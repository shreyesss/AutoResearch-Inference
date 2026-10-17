#!/usr/bin/env python3
"""Import completed seed-1042 AIPerf evidence without starting a server.

This is a provisional development measurement, not a matched evaluator cell,
load curve, SLA capacity estimate, or sealed-test result.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inference_autoresearch.benchmark.adaptive import _native_sla_records, _stat
from inference_autoresearch.benchmark.aiperf import _jsonl
from inference_autoresearch.evaluation.sla import assess_observed_point, validate_policy
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import sha256_file, verify_scenario


SCENARIO = "qwen-ops-mixed-development-1042-v1"
NATIVE_FILES = ("profile_export_aiperf.json", "profile_export_raw.jsonl", "profile_export.jsonl")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def inspect_trial(directory: Path, *, kind: str, manifest: dict[str, Any],
                  verified: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Check native accounting and exact frozen bodies before scoring latency."""
    paths = {name: directory / name for name in NATIVE_FILES}
    if not all(path.is_file() for path in paths.values()):
        raise ValueError(f"Missing native AIPerf export in {directory}")
    summary = _read(paths[NATIVE_FILES[0]])
    raw = _jsonl(paths[NATIVE_FILES[1]])
    measured = _jsonl(paths[NATIVE_FILES[2]])
    planned = verified["planned"]
    count = len(planned)
    phase = next((row for row in summary.get("input_config", {}).get("phases", [])
                  if row.get("name") == "profiling"), {})
    expected_type = "poisson" if kind == "source_capture" else "fixed_schedule"
    if (summary.get("is_complete") is not True or phase.get("type") != expected_type
            or phase.get("requests") != count or len(raw) != count
            or len(measured) != count or any(row.get("status") != 200 for row in raw)):
        raise ValueError(f"Incomplete or mismatched {kind} AIPerf trial")
    if kind == "source_capture":
        if not math.isclose(phase.get("rate", float("nan")), 0.1, rel_tol=1e-9):
            raise ValueError("Source capture is not the frozen 0.1-rps generation")
    else:
        datasets = summary.get("input_config", {}).get("datasets", [])
        if not any(row.get("type") == "file" and
                   Path(row.get("path", "")).resolve() == verified["payload_path"].resolve()
                   for row in datasets):
            raise ValueError("Replay did not use the frozen payload")
    expected = {(row["text"], row["output_length"]): row for row in planned}
    if len(expected) != count:
        raise ValueError("Frozen request bodies are ambiguous")
    by_native_id = {row.get("metadata", {}).get("x_request_id"): row for row in measured}
    if len(by_native_id) != count or None in by_native_id:
        raise ValueError("Native metric IDs are missing or duplicated")
    for native in raw:
        payload = native.get("payload") or {}
        messages = payload.get("messages") or []
        if len(messages) != 1 or messages[0].get("role") != "user":
            raise ValueError("Native request is not a single user turn")
        expected_row = expected.get((messages[0].get("content"), payload.get("max_completion_tokens")))
        if expected_row is None or payload.get("model") != manifest["model_id"]:
            raise ValueError("Native request body or model differs from frozen corpus")
        if any(payload.get(key) != value for key, value in expected_row["extra"].items()):
            raise ValueError("Native output controls differ from frozen corpus")
        native_id = native.get("metadata", {}).get("x_request_id")
        metrics = by_native_id.get(native_id, {}).get("metrics", {})
        if metrics.get("usage_completion_tokens", {}).get("value") != expected_row["output_length"]:
            raise ValueError("Native completion did not reach frozen output cap")
    records = _native_sla_records(raw, measured, planned)
    if len(records) != count or any(row["terminal_state"] != "completed" for row in records):
        raise ValueError("Frozen requests have missing or unsuccessful records")
    assessment = assess_observed_point(records, policy, verified["request_classes"])
    classes = {}
    for name, result in assessment["classes"].items():
        diag = result["diagnostic_percentiles_ms"]
        classes[name] = {
            "n": result["planned"], "ttft_p50_ms": diag["ttft"]["p50"],
            "ttft_p90_ms": diag["ttft"]["p90"],
            "tpot_p50_ms": diag["tpot"]["p50"],
            "tpot_p90_ms": diag["tpot"]["p90"],
            "ttft_deadline_breaches": result["ttft_deadline_breaches"],
            "tpot_deadline_breaches": result["tpot_deadline_breaches"],
            "observed_feasible": result["observed_feasible"],
            "reason_codes": result["reason_codes"]}
    return {"status": "valid", "kind": kind, "n": count,
            "offered_rps": phase.get("rate") if kind == "source_capture"
                           else manifest["offered_rps"],
            "observed_request_rps": _stat(summary, "request_throughput"),
            "output_tokens_per_s": _stat(summary, "output_token_throughput"),
            "observed_feasible": assessment["observed_feasible"],
            "classes": classes, "assessment": assessment,
            "native_artifacts": {name: {"path": str(path), "sha256": sha256_file(path)}
                                 for name, path in paths.items()}}


def import_b0(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / "configs/workloads/ops-frozen" / f"{SCENARIO}.json"
    policy_path = root / "configs/sla-policy-v3.json"
    manifest, policy = _read(manifest_path), _read(policy_path)
    validate_policy(policy)
    if (manifest.get("scenario_id") != SCENARIO or manifest.get("n_planned") != 240
            or manifest.get("seeds", {}).get("content") != 1042
            or manifest.get("seeds", {}).get("arrivals") != 1042):
        raise ValueError("Unexpected seed-1042 frozen scenario")
    verified = verify_scenario(manifest, root=root, require_validated=False)
    if verified.get("request_classes") is None:
        raise ValueError("Frozen request-class sidecar is absent")
    source_dir = root / ".artifacts/v3-independent-capture" / SCENARIO
    replay_dir = root / ".artifacts/v2-independent-validation/development_replication" / SCENARIO
    validation_path = replay_dir.parent / "validation-report.json"
    validation = _read(validation_path)
    validation_row = validation.get("scenarios", {}).get(SCENARIO, {})
    if (validation.get("schema_version") != "v2-independent-validation-v1"
            or validation_row.get("status") != "validated"
            or validation_row.get("planned") != 240
            or validation_row.get("http_200") != 240
            or validation_row.get("asset_sha256") != sha256_file(verified["payload_path"])
            or not all(validation_row.get(key) is True for key in
                       ("payload_match", "output_caps_realized", "schedule_match"))
            or validation_row.get("raw_sha256") != sha256_file(replay_dir / NATIVE_FILES[1])
            or validation_row.get("records_sha256") != sha256_file(replay_dir / NATIVE_FILES[2])):
        raise ValueError("Independent fixed-replay validation receipt is missing or changed")
    source_plan, source_status, replay_exit = (_read(source_dir / "plan.json"),
                                                _read(source_dir / "status.json"),
                                                _read(replay_dir / "exit.json"))
    if (source_plan.get("cell") != SCENARIO or source_plan.get("request_count") != 240
            or source_plan.get("random_seed") != 1042
            or source_status.get("aiperf_exit_code") != 0
            or replay_exit.get("exit_code") != 0):
        raise ValueError("Source capture or replay process did not complete as pinned")
    source = inspect_trial(source_dir / "aiperf/mixed", kind="source_capture",
                           manifest=manifest, verified=verified, policy=policy)
    replay = inspect_trial(replay_dir, kind="fixed_replay",
                           manifest=manifest, verified=verified, policy=policy)
    # Resolve the stock launch identity without starting a server.
    campaign = _read(root / "configs/campaign-v2.json")
    pinned = PinnedEnvironment(root / campaign["model"]["local_path"])
    baseline_config_id = resolve_config({}, pinned).config_id
    report = {"schema_version": "fast-pilot-b0-observed-v1", "status": "observed_b0",
              "claim": "provisional_development_b0_only",
              "capacity_confirmed": False, "sealed_test": False,
              "matched_evaluator_b0_receipt": False,
              "created_at_utc": datetime.now(UTC).isoformat(),
              "scenario_id": SCENARIO, "policy_id": policy["policy_id"],
              "policy_sha256": sha256_file(policy_path),
              "baseline_config_id": baseline_config_id,
              "input_artifacts": {
                  "manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path)},
                  "payload": {"path": str(verified["payload_path"]),
                              "sha256": sha256_file(verified["payload_path"])},
                  "class_sidecar": {"path": str(root / manifest["request_class_path"]),
                                    "sha256": manifest["request_class_sha256"]},
                  "policy": {"path": str(policy_path), "sha256": sha256_file(policy_path)},
                  "source_plan": {"path": str(source_dir / "plan.json"),
                                  "sha256": sha256_file(source_dir / "plan.json")},
                  "source_status": {"path": str(source_dir / "status.json"),
                                    "sha256": sha256_file(source_dir / "status.json")},
                  "replay_exit": {"path": str(replay_dir / "exit.json"),
                                  "sha256": sha256_file(replay_dir / "exit.json")},
                  "replay_validation": {"path": str(validation_path),
                                        "sha256": sha256_file(validation_path)}},
              "source_capture": source, "fixed_replay": replay}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite B0 import: {output}")
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    temporary.replace(output)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(".artifacts/fast-pilot-v4/b0-observed.json"))
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else args.root / args.output
    report = import_b0(args.root, output)
    print(json.dumps({"status": "imported", "path": str(output),
                      "source_feasible": report["source_capture"]["observed_feasible"],
                      "replay_feasible": report["fixed_replay"]["observed_feasible"]}, indent=2))


if __name__ == "__main__":
    main()

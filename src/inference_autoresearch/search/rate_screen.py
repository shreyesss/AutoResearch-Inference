"""One rate-matched Poisson triage cell at a B0-profiled development rate.

This deliberately does not claim exact arrival pairing or an SLA result. The
fixed 36 request bodies are reused, while AIPerf generates arrivals from the
same pinned rate and seed for B0 and every candidate.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.benchmark.adaptive import _native_sla_records, _stat
from inference_autoresearch.benchmark.aiperf import _jsonl
from inference_autoresearch.benchmark.sla_profiler import (
    SLAProfileSpec, assess_rate_trial, build_rate_argv,
)
from inference_autoresearch.contracts import CandidateProposal, EvaluationResult
from inference_autoresearch.runtime.config import resolve_config
from inference_autoresearch.workloads.registry import sha256_file, verify_scenario


class RateScreenError(RuntimeError):
    pass


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RateScreenError(f"expected JSON object: {path}")
    return value


def _output_caps_realized(raw: list[dict[str, Any]], measured: list[dict[str, Any]]) -> bool:
    by_id = {row.get("metadata", {}).get("x_request_id"): row for row in measured}
    if len(by_id) != len(measured):
        return False
    for row in raw:
        native_id = row.get("metadata", {}).get("x_request_id")
        expected = row.get("payload", {}).get("max_completion_tokens")
        metric = by_id.get(native_id, {}).get("metrics", {})
        actual = metric.get("usage_completion_tokens", {}).get("value")
        if type(expected) is not int or type(actual) is not int or actual != expected:
            return False
    return True


def select_screen_rate(study: dict[str, Any], root: Path, screen: Any) -> dict[str, Any]:
    """Choose one auditable diagnostic rate from a SHA-pinned B0 SLA curve."""
    root = Path(root).resolve()
    runs = study.get("baseline_adaptive_run_paths")
    if not isinstance(runs, list) or len(runs) != 1:
        raise RateScreenError("expected exactly one pinned B0 SLA profile")
    source_name = runs[0].get("source_path")
    source_hash = runs[0].get("source_sha256")
    if not isinstance(source_name, str) or Path(source_name).is_absolute():
        raise RateScreenError("B0 profile path must be project-relative")
    source = (root / source_name).resolve()
    if (not source.is_relative_to(root / ".artifacts/autoresearch-codebase")
            or not source.is_file() or source.name != "sla-profile-points.json"
            or sha256_file(source) != source_hash):
        raise RateScreenError("pinned B0 profile is missing or changed")
    profile = _read(source)
    policy_path = (root / study["policy"]["path"]).resolve()
    if (not policy_path.is_relative_to(root) or not policy_path.is_file()
            or sha256_file(policy_path) != study["policy"]["sha256"]):
        raise RateScreenError("approved SLA policy changed")
    policy_id = _read(policy_path)["policy_id"]
    manifest = screen.metadata["manifest"]
    if (profile.get("schema_version") != "sla-profile-points-v1"
            or profile.get("capacity_confirmed") is not False
            or profile.get("screen_scenario_id") != screen.scenario_id
            or profile.get("policy_id") != policy_id
            or profile.get("policy_sha256") != study["policy"]["sha256"]
            or screen.expected_count != 36):
        raise RateScreenError("B0 profile differs from approved policy or screen")
    checked = verify_scenario(manifest, root=root, require_validated=True)
    seed = profile.get("spec", {}).get("seed")
    if type(seed) is not int or seed < 0:
        raise RateScreenError("B0 profiler seed is missing")
    valid: list[tuple[int, dict[str, Any]]] = []
    for index, point in enumerate(profile.get("points", [])):
        screen_trial, qualified = point.get("screen"), point.get("qualified")
        rate = point.get("rate_rps")
        if (not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0
                or not isinstance(screen_trial, dict) or screen_trial.get("status") != "valid"
                or not isinstance(qualified, dict) or qualified.get("status") != "valid"
                or not isinstance(qualified.get("assessment"), dict)
                or qualified["assessment"].get("policy_id") != policy_id
                or point.get("arrival_seed") != seed + round(rate * 1_000_000)):
            continue
        artifacts = screen_trial.get("artifacts") or {}
        for key in ("summary", "raw", "records"):
            ref = artifacts.get(key)
            if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
                raise RateScreenError("selected B0 point lacks native screen evidence")
            path = Path(ref["path"]).resolve()
            if (not path.is_relative_to(source.parent.parent) or not path.is_file()
                    or sha256_file(path) != ref.get("sha256")):
                raise RateScreenError("B0 screen native artifact is missing or changed")
        valid.append((index, point))
    if not valid:
        raise RateScreenError("B0 profile has no valid class-assessed rate and screen")
    feasible = [(index, point) for index, point in valid
                if point["qualified"]["assessment"].get("observed_feasible") is True]
    if feasible:
        index, chosen = max(feasible, key=lambda item: (item[1]["rate_rps"], -item[0]))
        reason = "highest_observed_feasible_b0_rate"
    else:
        index, chosen = min(valid, key=lambda item: (item[1]["rate_rps"], item[0]))
        reason = "lowest_valid_b0_rate_baseline_infeasible_exploration"
    return {"schema_version": "rate-screen-lock-v1",
            "claim": "rate_matched_stochastic_36_request_triage_only",
            "exact_arrival_pairing": False, "capacity_confirmed": False,
            "selection_reason": reason, "selected_rate_rps": chosen["rate_rps"],
            "source_point_index": index, "source_profile_path": source_name,
            "source_profile_sha256": source_hash,
            "b0_profile_screen_artifacts": chosen["screen"]["artifacts"],
            "screen_scenario_id": screen.scenario_id,
            "screen_manifest_sha256": sha256_file(Path(screen.path)),
            "screen_payload_sha256": sha256_file(checked["payload_path"]),
            "arrival_pattern": "poisson", "arrival_seed": chosen["arrival_seed"],
            "client_concurrency_cap": profile["spec"]["client_concurrency_cap"]}


def run_rate_screen(engine: Any, candidate: CandidateProposal, scenario: Any,
                    rate_lock: dict[str, Any], ledger: Any, campaign_id: str,
                    artifact_root: Path) -> EvaluationResult:
    """Run one fresh pinned server and retain full AIPerf screen evidence."""
    if (rate_lock.get("schema_version") != "rate-screen-lock-v1"
            or rate_lock.get("screen_scenario_id") != scenario.scenario_id
            or sha256_file(Path(scenario.path)) != rate_lock.get("screen_manifest_sha256")
            or sha256_file(Path(scenario.metadata["asset"])) != rate_lock.get("screen_payload_sha256")):
        raise RateScreenError("rate screen input differs from pinned lock")
    source = (Path(scenario.metadata["registry_root"])
              / rate_lock["source_profile_path"]).resolve()
    if not source.is_file() or sha256_file(source) != rate_lock["source_profile_sha256"]:
        raise RateScreenError("B0 profile changed after rate selection")
    rate = rate_lock["selected_rate_rps"]
    seed = rate_lock["arrival_seed"] - round(rate * 1_000_000)
    spec = SLAProfileSpec(initial_rate_rps=rate, min_rate_rps=rate,
                          max_rate_rps=max(rate * 2, rate + 0.001),
                          client_concurrency_cap=rate_lock["client_concurrency_cap"], seed=seed)
    engine.benchmark.preflight_tokenizer(scenario)
    resolved = resolve_config(candidate.parameters, engine._pinned(), engine._domain())
    evaluation_id = "eval-" + uuid.uuid4().hex
    evaluation_dir = Path(artifact_root) / evaluation_id
    cell_dir = evaluation_dir / f"cell-01-{scenario.scenario_id}"
    aiperf_dir = cell_dir / "aiperf"
    aiperf_dir.mkdir(parents=True, exist_ok=False)
    (evaluation_dir / "proposal.json").write_text(json.dumps(asdict(candidate), indent=2) + "\n")
    (evaluation_dir / "resolved-config.json").write_text(json.dumps(asdict(resolved), indent=2, default=str) + "\n")
    (evaluation_dir / "evaluation-policy.json").write_text(json.dumps({
        "protocol_id": "rate-matched-poisson-triage-v1", "stage": "triage",
        "claim": rate_lock["claim"], "rate_lock_sha256": hashlib.sha256(
            json.dumps(rate_lock, sort_keys=True).encode()).hexdigest(),
        "exact_arrival_pairing": False}, indent=2) + "\n")
    handle = None
    started = time.monotonic()
    phases: dict[str, float] = {}
    try:
        phase = time.monotonic()
        handle = engine.runtime.start(resolved, cell_dir / "server")
        phases["server_start_s"] = time.monotonic() - phase
        phase = time.monotonic()
        engine.benchmark.prepare(handle, scenario, cell_dir / "warmup")
        phases["warmup_s"] = time.monotonic() - phase
        argv = build_rate_argv(engine.benchmark, handle, scenario, rate=rate,
                               spec=spec, output_dir=aiperf_dir)
        (aiperf_dir / "aiperf-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        timeout = math.ceil((scenario.expected_count + 4 * math.sqrt(scenario.expected_count)) / rate) + 390
        phase = time.monotonic()
        with (aiperf_dir / "aiperf-console.log").open("w") as console:
            try:
                process = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                         env=engine.benchmark._offline_env(),
                                         timeout=timeout, check=False)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                exit_code = -1
        phases["benchmark_s"] = time.monotonic() - phase
        (aiperf_dir / "aiperf-exit.json").write_text(json.dumps({"exit_code": exit_code}) + "\n")
        trial = assess_rate_trial(aiperf_dir, scenario, None, rate=rate,
                                  process_exit_code=exit_code, spec=spec)
        native_summary = _read(aiperf_dir / "profile_export_aiperf.json") if trial["status"] == "valid" else {}
        metrics = {"output_tokens_per_s": _stat(native_summary, "output_token_throughput"),
                   "ttft_p50_ms": _stat(native_summary, "time_to_first_token", "p50"),
                   "ttft_p90_ms": _stat(native_summary, "time_to_first_token", "p90"),
                   "ttft_p99_ms": _stat(native_summary, "time_to_first_token", "p99"),
                   "tpot_p50_ms": _stat(native_summary, "inter_token_latency", "p50"),
                   "tpot_p90_ms": _stat(native_summary, "inter_token_latency", "p90"),
                   "tpot_p99_ms": _stat(native_summary, "inter_token_latency", "p99"),
                   "dispatch_lag_p99_ms": trial["dispatch_lag_p99_ms"]}
        reasons = list(trial["reason_codes"])
        native_raw = _jsonl(aiperf_dir / "profile_export_raw.jsonl") if trial["status"] == "valid" else []
        native_measured = _jsonl(aiperf_dir / "profile_export.jsonl") if trial["status"] == "valid" else []
        if trial["status"] == "valid" and not _output_caps_realized(native_raw, native_measured):
            reasons.append("wrong_output_length")
        if trial["status"] == "valid" and any(metrics[name] is None for name in (
                "output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms", "ttft_p99_ms",
                "tpot_p50_ms", "tpot_p90_ms", "tpot_p99_ms")):
            reasons.append("missing_primary_metric")
        status = "valid" if not reasons else "measurement_failed"
        if status == "valid":
            manifest = scenario.metadata["manifest"]
            checked = verify_scenario(manifest, root=Path(scenario.metadata["registry_root"]))
            records = _native_sla_records(native_raw, native_measured, checked["planned"])
            with (aiperf_dir / "normalized-requests.jsonl").open("w") as stream:
                for record in records:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")
        counts = {"planned": scenario.expected_count, "dispatched": trial["dispatched"],
                  "completed": trial["completed"],
                  "not_dispatched": max(0, scenario.expected_count - trial["dispatched"]),
                  "failed": max(0, trial["dispatched"] - trial["completed"]),
                  "timed_out": 0, "canceled": 0, "censored": 0}
        cell_id = f"{evaluation_id}:{scenario.scenario_id}:1"
        cell = {"cell_id": cell_id, "scenario_id": scenario.scenario_id,
                "config_id": resolved.config_id, "status": status,
                "behavior": "normal" if status == "valid" else "unknown",
                "evidence_grade": "provisional" if status == "valid" else "ineligible",
                "counts": counts, "metrics": metrics,
                "artifacts": {"raw_requests": str(aiperf_dir / "normalized-requests.jsonl"),
                              "aiperf_export": str(aiperf_dir / "profile_export_aiperf.json"),
                              "raw_native": str(aiperf_dir / "profile_export_raw.jsonl"),
                              "metrics_native": str(aiperf_dir / "profile_export.jsonl")},
                "diagnostics": {"rate_screen_lock": rate_lock,
                                "realized_rate_rps": trial["realized_rate_rps"],
                                "class_metrics": trial["class_metrics"],
                                "claim": rate_lock["claim"]},
                "reason_codes": reasons}
        (cell_dir / "cell-result.json").write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n")
        (cell_dir / "controller-validation.json").write_text(json.dumps({
            "frontier_eligible": status == "valid", "reason_codes": reasons,
            "claim": rate_lock["claim"]}, indent=2) + "\n")
        ledger.append(campaign_id, "cell", cell_id, cell | {
            "stage": "triage", "offered_load": rate, "load_unit": "requests_per_s",
            "cache_protocol": scenario.cache_protocol,
            "measurement_protocol": "rate-matched-poisson-triage-v1",
            "is_baseline": not candidate.parameters})
        result = EvaluationResult(evaluation_id, resolved.config_id, "triage", [cell_id],
                                  "valid" if status == "valid" else "failed",
                                  failure_reasons=reasons)
        (evaluation_dir / "evaluation-result.json").write_text(json.dumps(asdict(result), indent=2) + "\n")
        return result
    finally:
        if handle is not None:
            engine.runtime.stop(handle)
        (cell_dir / "timing.json").write_text(json.dumps({
            "stage": "triage", "protocol_id": "rate-matched-poisson-triage-v1",
            "phases": phases, "total_wall_s": time.monotonic() - started}, indent=2) + "\n")

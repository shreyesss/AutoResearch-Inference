#!/usr/bin/env python3
"""Three matched 32-request operator points for B0 and at most two finalists.

`check` is GPU-free and read-only. `run` uses one shared GPU lease and writes
every native AIPerf export. The short curves diagnose operator tradeoffs;
they are neither SLA attainment nor independently confirmed capacity.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import random
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inference_autoresearch.benchmark.aiperf import AIPerfAdapter, _jsonl
from inference_autoresearch.benchmark.sla_profiler import SLAProfileSpec, assess_rate_trial, build_rate_argv
from inference_autoresearch.contracts import ScenarioManifest
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.runtime.docker import DockerRuntimeManager
from inference_autoresearch.search.rate_screen import _output_caps_realized
from inference_autoresearch.workloads.registry import sha256_file, verify_scenario


CAMPAIGN_ID = "qwen38-27b-fast-pilot-v4"
SCENARIO_ID = "qwen-ops-mixed-development-1042-v1"
CURVE_SCENARIO_ID = "qwen-ops-mixed-development-1042-curve32-v4"
RATES_RPS = (0.2, 0.4, 0.8)
SEED = 41042
SAMPLING_SEED = 321042
CLASS_QUOTAS = {"chat": 8, "agent": 8, "code": 8, "document": 8}
ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / ".artifacts/fast-pilot-v4"
OUTPUT = PILOT / "operator-curve-32x3"


class FollowupError(RuntimeError):
    pass


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise FollowupError(f"Expected JSON object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")
    temporary.replace(path)


def controller_aiperf_executable() -> Path:
    """Use the AIPerf installed in the executing controller environment."""
    found = shutil.which("aiperf")
    if not found:
        raise FollowupError("AIPerf is absent from the controller PATH")
    path = Path(found).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise FollowupError(f"Controller AIPerf is not executable: {path}")
    return path


def pinned_ref(root: Path, entry: dict[str, Any], *, label: str) -> Path:
    name, expected = entry.get("path"), entry.get("sha256")
    if not isinstance(name, str) or not isinstance(expected, str) or Path(name).is_absolute():
        raise FollowupError(f"Invalid {label} artifact reference")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file() or sha256_file(path) != expected:
        raise FollowupError(f"Changed or missing {label} artifact")
    return path


def selected_cases(root: Path, shortlist: dict[str, Any], ledger_path: Path,
                   pinned: PinnedEnvironment, domain: dict[str, list[object]]) -> list[dict[str, Any]]:
    """Resolve exact selected configs against source files and append-only ledger."""
    selected = shortlist.get("selected_proposals")
    ids = shortlist.get("selected_cell_ids")
    if (shortlist.get("capacity_confirmed") is not False
            or shortlist.get("further_evaluation_required") is not True
            or not isinstance(selected, list) or not 1 <= len(selected) <= 2
            or not isinstance(ids, list) or len(ids) != len(selected)
            or set(ids) != {item.get("cell_id") for item in selected}):
        raise FollowupError("Pilot shortlist is absent, empty or not a two-finalist provisional selection")
    if not ledger_path.is_file():
        raise FollowupError("Pilot ledger is absent")
    with sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT kind,entity_id,payload_json FROM events "
                          "WHERE campaign_id=? AND kind IN ('proposal','pilot_screen_decision')",
                          (CAMPAIGN_ID,)).fetchall()
    proposals = {entity: json.loads(payload) for kind, entity, payload in rows if kind == "proposal"}
    decisions = {entity: json.loads(payload) for kind, entity, payload in rows
                 if kind == "pilot_screen_decision"}
    cases = []
    seen_config_ids: set[str] = set()
    for entry in selected:
        proposal_id, config_id, parameters, cell_id = (entry.get("proposal_id"),
                                                       entry.get("config_id"),
                                                       entry.get("parameters"),
                                                       entry.get("cell_id"))
        if (not isinstance(proposal_id, str) or not isinstance(config_id, str)
                or not isinstance(parameters, dict) or not isinstance(cell_id, str)
                or config_id in seen_config_ids):
            raise FollowupError("Selected proposal identity is invalid or duplicated")
        seen_config_ids.add(config_id)
        proposal_path = pinned_ref(root, {"path": entry.get("proposal_path"),
                                          "sha256": entry.get("proposal_sha256")},
                                   label="normalized proposal")
        cell_path = pinned_ref(root, {"path": entry.get("cell_result_path"),
                                      "sha256": entry.get("cell_result_sha256")},
                               label="pilot CellResult")
        proposal_file, cell = read(proposal_path), read(cell_path)
        event, decision = proposals.get(proposal_id, {}), decisions.get(proposal_id, {})
        if (proposal_file.get("proposal_id") != proposal_id
                or proposal_file.get("parameters") != parameters
                or event.get("proposal", {}).get("parameters") != parameters
                or event.get("config_id") != config_id
                or decision.get("cell_id") != cell_id
                or decision.get("promote_to_shortlist") is not True
                or cell.get("cell_id") != cell_id or cell.get("config_id") != config_id
                or cell.get("status") != "valid"):
            raise FollowupError(f"Pilot evidence differs for {proposal_id}")
        resolved = resolve_config(parameters, pinned, domain)
        if resolved.config_id != config_id:
            raise FollowupError(f"Selected config ID differs from resolver for {proposal_id}")
        cases.append({"label": proposal_id, "config_id": config_id,
                      "parameters": parameters, "pilot_cell_id": cell_id,
                      "proposal_sha256": sha256_file(proposal_path),
                      "pilot_cell_sha256": sha256_file(cell_path)})
    return cases


def preflight(root: Path = ROOT, pilot: Path = PILOT) -> dict[str, Any]:
    """Validate pinned pilot selection and replay receipt without GPU or writes."""
    root, pilot = root.resolve(), pilot.resolve()
    shortlist_path, lock_path = pilot / "provisional-finalists.json", pilot / "pilot-campaign-lock.json"
    b0_path, status_path = pilot / "b0-observed.json", pilot / "run-status.json"
    campaign_path, domain_path, policy_path = (root / "configs/campaign-sla-serving-v3c.json",
                                                root / "configs/search-domain-v3c.json",
                                                root / "configs/sla-policy-v3.json")
    for path in (shortlist_path, lock_path, b0_path, status_path,
                 campaign_path, domain_path, policy_path):
        if not path.is_file():
            raise FollowupError(f"Required pilot input missing: {path}")
    shortlist, lock, b0, status = map(read, (shortlist_path, lock_path, b0_path, status_path))
    if (status.get("status") != "complete" or lock.get("campaign_id") != CAMPAIGN_ID
            or lock.get("b0_sha256") != sha256_file(b0_path)
            or lock.get("policy_sha256") != sha256_file(policy_path)
            or lock.get("domain_sha256") != sha256_file(domain_path)
            or lock.get("campaign_source_sha256") != sha256_file(campaign_path)
            or b0.get("status") != "observed_b0"
            or b0.get("capacity_confirmed") is not False
            or b0.get("policy_sha256") != lock["policy_sha256"]
            or b0.get("scenario_id") != SCENARIO_ID):
        raise FollowupError("Pilot completion or B0 source pins differ")
    source_path = Path(b0["input_artifacts"]["manifest"]["path"]).resolve()
    # The importer stores absolute native paths; verify each by its digest.
    for label, entry in b0["input_artifacts"].items():
        path = Path(entry["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256_file(path) != entry["sha256"]:
            raise FollowupError(f"B0 {label} pin changed")
    for trial in (b0["source_capture"], b0["fixed_replay"]):
        for entry in trial["native_artifacts"].values():
            path = Path(entry["path"]).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha256_file(path) != entry["sha256"]:
                raise FollowupError("B0 native export changed")
    manifest = read(source_path)
    checked = verify_scenario(manifest, root=root, require_validated=False)
    if (manifest.get("scenario_id") != SCENARIO_ID or manifest.get("n_planned") != 240
            or checked["request_classes"] is None
            or sha256_file(checked["payload_path"]) != b0["input_artifacts"]["payload"]["sha256"]):
        raise FollowupError("1042 frozen corpus changed")
    validation = read(Path(b0["input_artifacts"]["replay_validation"]["path"]))
    row = validation.get("scenarios", {}).get(SCENARIO_ID, {})
    if (row.get("status") != "validated" or row.get("schedule_match") is not True
            or row.get("payload_match") is not True or row.get("http_200") != 240):
        raise FollowupError("1042 replay validation no longer supports staged input")
    campaign, raw_domain = read(campaign_path), read(domain_path)
    model, runtime = campaign["model"], campaign["runtime"]
    pinned = PinnedEnvironment(root / model["local_path"], image=runtime["image"],
                               model_name=model["id"], model_revision=model["revision"],
                               max_model_len=model["max_model_len"],
                               tensor_parallel_size=model["tensor_parallel_size"],
                               dtype=model["dtype"], gpu_uuid=runtime["gpu_uuid"])
    domain = {name: list(spec["values"]) for name, spec in raw_domain["parameters"].items()
              if spec.get("active") is not False}
    baseline = resolve_config({}, pinned, domain)
    if baseline.config_id != b0.get("baseline_config_id"):
        raise FollowupError("B0 config identity differs")
    cases = selected_cases(root, shortlist, pilot / "ledger.sqlite", pinned, domain)
    policy = read(policy_path)
    if set(policy.get("classes", {})) != set(CLASS_QUOTAS):
        raise FollowupError("Curve class labels differ from approved research policy")
    selection = stratified_rows(checked["planned"], checked["request_classes"])
    return {"status": "ready_for_exploratory_operator_curve", "capacity_confirmed": False,
            "rates_rps": RATES_RPS, "seed": SEED,
            "class_quotas": CLASS_QUOTAS, "sampling_seed": SAMPLING_SEED,
            "selected_ids_sha256": selection["ids_sha256"],
            "shortlist_sha256": sha256_file(shortlist_path),
            "pilot_lock_sha256": sha256_file(lock_path),
            "b0_sha256": sha256_file(b0_path),
            "policy_sha256": sha256_file(policy_path),
            "source_manifest_sha256": sha256_file(source_path),
            "source_card_sha256": sha256_file(root / manifest["workload_card_path"]),
            "source_payload_sha256": sha256_file(checked["payload_path"]),
            "cases": [{"label": "B0", "config_id": baseline.config_id,
                       "parameters": {}, "pilot_cell_id": None}, *cases],
            "source_manifest": manifest, "policy": policy,
            "pinned": pinned, "domain": domain}


def stratified_rows(planned: list[dict[str, Any]],
                    request_classes: dict[str, str]) -> dict[str, Any]:
    """Draw fixed class quotas without replacement, retaining source order."""
    pools = {name: [row["session_id"] for row in planned
                    if request_classes[row["session_id"]] == name] for name in CLASS_QUOTAS}
    rng = random.Random(SAMPLING_SEED)
    chosen: set[str] = set()
    for name, quota in CLASS_QUOTAS.items():
        if len(pools[name]) < quota:
            raise FollowupError(f"Source lacks {quota} {name} requests")
        chosen.update(rng.sample(pools[name], quota))
    rows = [dict(row) for row in planned if row["session_id"] in chosen]
    if len(rows) != 32 or len({row["session_id"] for row in rows}) != 32:
        raise FollowupError("Stratified selection is incomplete or duplicated")
    origin = rows[0]["timestamp"]
    for row in rows:
        row["timestamp"] -= origin
    ids = [row["session_id"] for row in rows]
    return {"rows": rows, "ids": ids,
            "ids_sha256": hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()}


def staged_scenario(root: Path, output: Path, prepared: dict[str, Any]) -> ScenarioManifest:
    """Stage one 32-body diagnostic corpus; leave source 240 evidence intact."""
    original = prepared["source_manifest"]
    input_dir = output / "input"
    input_dir.mkdir(parents=True, exist_ok=False)
    source = verify_scenario(original, root=root, require_validated=False)
    chosen = stratified_rows(source["planned"], source["request_classes"])
    if chosen["ids_sha256"] != prepared["selected_ids_sha256"]:
        raise FollowupError("Deterministic 32-request selection changed")
    payload_path = input_dir / "1042-curve-32.jsonl"
    with payload_path.open("w") as stream:
        for row in chosen["rows"]:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    class_path = input_dir / "1042-curve-32.classes.json"
    write(class_path, {"schema_version": "ops-request-classes-v1",
                       "scenario_id": CURVE_SCENARIO_ID,
                       "classes_by_session_id": {key: source["request_classes"][key]
                                                 for key in chosen["ids"]}})
    source_card = read(root / original["workload_card_path"])
    source_schedule_rps = 31000 / chosen["rows"][-1]["timestamp"]
    card = source_card | {"card_id": CURVE_SCENARIO_ID, "readiness": "validated",
                          "shape_counts": CLASS_QUOTAS,
                          "configured_average_rps": None,
                          "frozen_schedule_average_rps": source_schedule_rps,
                          "source_arrival": {"pattern": "subset_of_1042_frozen_source",
                                             "rate_rps": source_schedule_rps},
                          "evaluation_arrival": {"pattern": "poisson", "rates_rps": RATES_RPS,
                                                 "base_seed": SEED},
                          "limitations": ["Same-source exploratory subset, not independent test or SLA sample.",
                                          "Stored timestamps are source-order metadata; AIPerf replaces arrivals."]}
    card_path = input_dir / "1042.card.json"
    write(card_path, card)
    manifest = original | {"scenario_id": CURVE_SCENARIO_ID,
                           "readiness": "validated", "n_planned": 32,
                           "payload_path": str(payload_path.relative_to(root)),
                           "schedule_path": str(payload_path.relative_to(root)),
                           "payload_sha256": sha256_file(payload_path),
                           "schedule_sha256": sha256_file(payload_path),
                           "request_class_path": str(class_path.relative_to(root)),
                           "request_class_sha256": sha256_file(class_path),
                           "workload_card_path": str(card_path.relative_to(root)),
                           "workload_card_sha256": sha256_file(card_path),
                           "shape_counts": CLASS_QUOTAS,
                           "seeds": {"arrivals": SEED,
                                     "content": 1042, "prefix": 0},
                           "offered_load": source_schedule_rps, "offered_rps": source_schedule_rps,
                           "dispatch_duration_s": chosen["rows"][-1]["timestamp"] / 1000,
                           "notes": "32-body same-source diagnostic; AIPerf Poisson rates replace arrivals. No SLA or independent test."}
    manifest_path = input_dir / "1042.manifest.json"
    write(manifest_path, manifest)
    checked = verify_scenario(manifest, root=root, require_validated=True)
    if len(checked["planned"]) != 32 or {name: list(checked["request_classes"].values()).count(name)
                                          for name in CLASS_QUOTAS} != CLASS_QUOTAS:
        raise FollowupError("Derived 32 manifest did not retain class quotas")
    write(input_dir / "selection-receipt.json", {
        "schema_version": "v4-operator-curve-32-v1", "source_scenario_id": SCENARIO_ID,
        "derived_scenario_id": CURVE_SCENARIO_ID, "sampling_seed": SAMPLING_SEED,
        "class_quotas": CLASS_QUOTAS, "selected_ids_sha256": chosen["ids_sha256"],
        "selected_ids": chosen["ids"], "source_manifest_sha256": prepared["source_manifest_sha256"],
        "source_payload_sha256": prepared["source_payload_sha256"],
        "derived_manifest_sha256": sha256_file(manifest_path),
        "derived_payload_sha256": sha256_file(payload_path),
        "derived_card_sha256": sha256_file(card_path),
        "derived_class_sidecar_sha256": sha256_file(class_path),
        "claim": "same_source_exploratory_operator_curve_only"})
    return ScenarioManifest(scenario_id=CURVE_SCENARIO_ID, workload_id=manifest["workload_name"],
                            path=manifest_path, group_id=manifest["workload_group_id"],
                            offered_load=source_schedule_rps, load_unit="requests_per_s",
                            expected_count=32, output_policy="forced_length",
                            traffic_mode="independent_open_loop", history_mode="single_turn",
                            cache_protocol="cold_stream",
                            metadata={"manifest": manifest, "asset": str(checked["payload_path"]),
                                      "registry_root": str(root),
                                      "request_classes": checked["request_classes"]})


def class_rows(trial: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for name, value in trial.get("class_metrics", {}).items():
        rows[name] = {"n_dispatched": value.get("n_dispatched"),
                      "ttft_eligible": value.get("ttft_eligible"),
                      "tpot_eligible": value.get("tpot_eligible"),
                      "ttft_p50_ms": value.get("ttft_p50_ms"),
                      "ttft_p90_ms": value.get("ttft_p90_ms"),
                      "tpot_p50_ms": value.get("tpot_p50_ms"),
                      "tpot_p90_ms": value.get("tpot_p90_ms")}
    return rows


def diagnostic_reasons(trial: dict[str, Any]) -> list[str]:
    """Reject incomplete traffic and missing latency; never score SLA targets."""
    reasons = list(trial.get("reason_codes", []))
    if trial.get("status") != "valid":
        reasons.append("invalid_aiperf_trial")
    classes = class_rows(trial)
    if set(classes) != set(CLASS_QUOTAS):
        reasons.append("class_coverage_mismatch")
    for name, quota in CLASS_QUOTAS.items():
        row = classes.get(name, {})
        if any(row.get(key) != quota for key in ("n_dispatched", "ttft_eligible", "tpot_eligible")):
            reasons.append(f"{name}_latency_or_count_missing")
        if any(not isinstance(row.get(key), (int, float)) or not math.isfinite(row[key])
               for key in ("ttft_p50_ms", "ttft_p90_ms", "tpot_p50_ms", "tpot_p90_ms")):
            reasons.append(f"{name}_percentile_missing")
    native = trial.get("native_summary_metrics", {})
    if any(not isinstance(native.get(key), (int, float)) or not math.isfinite(native[key])
           for key in ("output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms",
                       "tpot_p50_ms", "tpot_p90_ms")):
        reasons.append("aggregate_metric_missing")
    return sorted(set(reasons))


def compare_points(points: list[dict[str, Any]]) -> dict[str, Any]:
    if len(points) < len(RATES_RPS) or any(point["trial"]["status"] != "valid" for point in points):
        raise FollowupError("Operator curve has missing or invalid trials")
    by_label: dict[str, dict[float, dict[str, Any]]] = {}
    for point in points:
        by_label.setdefault(point["label"], {})[point["rate_rps"]] = point
    if any(set(group) != set(RATES_RPS) for group in by_label.values()) or "B0" not in by_label:
        raise FollowupError("Every configuration needs the same three offered rates")
    comparisons = []
    for label, rate_map in by_label.items():
        if label == "B0":
            continue
        for rate in RATES_RPS:
            point, baseline = rate_map[rate], by_label["B0"][rate]
            classes, base = class_rows(point["trial"]), class_rows(baseline["trial"])
            if set(classes) != set(base):
                raise FollowupError("Finalist class evidence differs from B0")
            deltas = {name: {metric + "_delta_ms": classes[name][metric] - base[name][metric]
                             for metric in ("ttft_p50_ms", "ttft_p90_ms", "tpot_p50_ms", "tpot_p90_ms")}
                      for name in base}
            numerator = point["trial"]["native_summary_metrics"]["output_tokens_per_s"]
            denominator = baseline["trial"]["native_summary_metrics"]["output_tokens_per_s"]
            comparisons.append({"label": label, "config_id": point["config_id"],
                                "rate_rps": rate, "class_latency_deltas_vs_b0": deltas,
                                "output_tokens_per_s_ratio_vs_b0": numerator / denominator
                                if numerator is not None and denominator else None})
    return {"claim": "same_source_32_request_operator_curves_only",
            "capacity_confirmed": False, "independent_test": False, "sla_assessed": False,
            "rates_rps": RATES_RPS, "requests_per_rate": 32, "class_quotas": CLASS_QUOTAS,
            "points": points, "comparisons": comparisons}


def plot_operator_points(output: Path, points: list[dict[str, Any]]) -> dict[str, str]:
    """Descriptive three-rate curves; no SLA boundary or confidence claim."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = list(dict.fromkeys(point["label"] for point in points))
    figure, axes = plt.subplots(3, 1, figsize=(9, 11), sharex=True)
    for label in labels:
        ordered = sorted((point for point in points if point["label"] == label),
                         key=lambda row: row["rate_rps"])
        for axis, metric in zip(axes, ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms")):
            axis.plot(RATES_RPS, [point["trial"]["native_summary_metrics"][metric]
                                      for point in ordered], marker="o", label=label)
    for axis, metric in zip(axes, ("Output tokens/s", "Overall TTFT p90 ms", "Overall TPOT p90 ms")):
        axis.set_ylabel(metric)
        axis.grid(True, alpha=0.3)
        axis.legend()
    axes[0].set_title("Observed operator curves, 32 requests/rate; exploratory")
    axes[2].set_xlabel("Offered requests/s")
    figure.tight_layout()
    path = output / "operator-curves.svg"
    figure.savefig(path)
    plt.close(figure)
    class_figure, class_axes = plt.subplots(4, 2, figsize=(13, 13), sharex=True)
    for row_index, name in enumerate(CLASS_QUOTAS):
        for column_index, metric in enumerate(("ttft", "tpot")):
            axis = class_axes[row_index, column_index]
            for label in labels:
                ordered = sorted((point for point in points if point["label"] == label),
                                 key=lambda row: row["rate_rps"])
                for percentile, style in (("p50", "--"), ("p90", "-")):
                    key = f"{metric}_{percentile}_ms"
                    axis.plot(RATES_RPS, [class_rows(point["trial"])[name][key]
                                              for point in ordered], marker="o", linestyle=style,
                              label=f"{label} {percentile}")
            axis.set_ylabel(f"{name} {metric.upper()} ms")
            axis.grid(True, alpha=0.3)
            axis.legend(fontsize="small")
    class_axes[-1, 0].set_xlabel("Offered requests/s")
    class_axes[-1, 1].set_xlabel("Offered requests/s")
    class_figure.suptitle("Per-class observed p50/p90; 8 requests/class/rate")
    class_figure.tight_layout()
    class_path = output / "per-class-curves.svg"
    class_figure.savefig(class_path)
    plt.close(class_figure)
    scatter, scatter_axis = plt.subplots(figsize=(9, 6))
    for point in points:
        metrics = point["trial"]["native_summary_metrics"]
        scatter_axis.scatter(metrics["ttft_p90_ms"], metrics["output_tokens_per_s"],
                             label=f"{point['label']} @ {point['rate_rps']:g}")
    scatter_axis.set_xlabel("Overall TTFT p90 ms")
    scatter_axis.set_ylabel("Output tokens/s")
    scatter_axis.set_title("Observed throughput/latency points; no confirmed Pareto frontier")
    scatter_axis.grid(True, alpha=0.3)
    scatter_axis.legend(fontsize="small")
    scatter.tight_layout()
    scatter_path = output / "throughput-latency-points.svg"
    scatter.savefig(scatter_path)
    plt.close(scatter)
    return {"operator_curves_svg": str(path), "per_class_curves_svg": str(class_path),
            "throughput_latency_svg": str(scatter_path)}


def run(root: Path = ROOT, pilot: Path = PILOT, output: Path = OUTPUT) -> dict[str, Any]:
    prepared = preflight(root, pilot)
    root, output = root.resolve(), output.resolve()
    guard_path = root / ".artifacts/gpu-locks" / "v4-operator-curve-process.lock"
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    with guard_path.open("a+") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if output.exists():
            raise FollowupError(f"Followup output already exists: {output}")
        if subprocess.run(["docker", "container", "inspect", "iar-b0"],
                          capture_output=True, check=False).returncode == 0:
            raise FollowupError("Shared B0 server still exists")
        active = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                                 "--format=csv,noheader,nounits"], capture_output=True,
                                text=True, check=True, timeout=15).stdout.strip()
        if active:
            raise FollowupError("GPU compute process exists")
        output.mkdir(parents=True, exist_ok=False)
        lock = {key: prepared[key] for key in ("shortlist_sha256", "pilot_lock_sha256",
                                               "b0_sha256", "policy_sha256",
                                               "source_manifest_sha256", "source_card_sha256",
                                               "source_payload_sha256")}
        lock.update({"schema_version": "fast-operator-curve-32x3-v1",
                     "rates_rps": RATES_RPS, "requests_per_rate": 32,
                     "arrival_pattern": "poisson", "base_seed": SEED,
                     "claim": "same_source_32_request_operator_curves_no_sla_or_capacity",
                     "selected_ids_sha256": prepared["selected_ids_sha256"],
                     "capacity_confirmed": False})
        write(output / "run-lock.json", lock)
        scenario = staged_scenario(root, output, prepared)
        lock["derived_input_receipt_sha256"] = sha256_file(output / "input/selection-receipt.json")
        write(output / "run-lock.json", lock)
        adapter = AIPerfAdapter(aiperf_executable=controller_aiperf_executable(),
                                tokenizer_path=prepared["pinned"].model_dir,
                                tokenizer_cache_dir=root / ".artifacts/aiperf-hf-cache")
        adapter.preflight_tokenizer(scenario)
        gpu_lock = Path(os.environ.get("IAR_GPU_LOCK_PATH", str(root / ".artifacts/gpu-locks" /
                            f"{prepared['pinned'].gpu_uuid}.lock")))
        runtime = DockerRuntimeManager(prepared["pinned"], gpu_lock)
        spec = SLAProfileSpec(initial_rate_rps=RATES_RPS[0], min_rate_rps=RATES_RPS[0],
                              max_rate_rps=RATES_RPS[-1], seed=SEED,
                              min_realized_rate_fraction=0.5,
                              client_concurrency_cap=256)
        points = []
        state = {"status": "running", "active": None, "completed": [],
                 "capacity_confirmed": False, "independent_test": False}
        write(output / "run-status.json", state)
        try:
            for ordinal, case in enumerate(prepared["cases"], 1):
                # The proposal and source inputs are rechecked before each GPU cell.
                fresh = preflight(root, pilot)
                if ([row["config_id"] for row in fresh["cases"]]
                        != [row["config_id"] for row in prepared["cases"]]
                        or any(fresh[key] != prepared[key] for key in lock if key in fresh)):
                    raise FollowupError("Pilot selection or frozen inputs changed during followup")
                state["active"] = case["label"]
                write(output / "run-status.json", state)
                config = resolve_config(case["parameters"], prepared["pinned"], prepared["domain"])
                cell = output / f"cell-{ordinal:02d}-{config.config_id}"
                cell.mkdir(parents=True, exist_ok=False)
                write(cell / "resolved-config.json", asdict(config))
                handle = None
                try:
                    handle = runtime.start(config, cell / "server")
                    adapter.prepare(handle, scenario, cell / "warmup")
                    for rate in RATES_RPS:
                        native = cell / f"rate-{rate:g}" / "aiperf"
                        native.mkdir(parents=True)
                        argv = build_rate_argv(adapter, handle, scenario, rate=rate,
                                               spec=spec, output_dir=native)
                        write(native / "aiperf-argv.json", {"argv": argv})
                        timeout = math.ceil((scenario.expected_count + 4 * math.sqrt(scenario.expected_count))
                                            / rate) + 390
                        with (native / "aiperf-console.log").open("w") as console:
                            try:
                                result = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                                        env=adapter._offline_env(), timeout=timeout,
                                                        check=False)
                                exit_code = result.returncode
                            except subprocess.TimeoutExpired:
                                exit_code = -1
                        write(native / "aiperf-exit.json", {"exit_code": exit_code})
                        trial = assess_rate_trial(native, scenario, None,
                                                  rate=rate, process_exit_code=exit_code, spec=spec)
                        if trial["status"] == "valid" and not _output_caps_realized(
                                _jsonl(native / "profile_export_raw.jsonl"),
                                _jsonl(native / "profile_export.jsonl")):
                            trial["status"] = "invalid"
                            trial["reason_codes"].append("wrong_output_length")
                        reasons = diagnostic_reasons(trial)
                        if reasons:
                            trial["status"] = "invalid"
                            trial["reason_codes"] = reasons
                        trial["class_p50_p90"] = class_rows(trial)
                        write(native.parent / "rate-trial.json", trial)
                        points.append({"label": case["label"], "config_id": config.config_id,
                                       "parameters": case["parameters"], "rate_rps": rate,
                                       "arrival_seed": SEED + round(rate * 1_000_000),
                                       "trial": trial,
                                       "trial_path": str(native.parent / "rate-trial.json")})
                        write(output / "all-points.json", {"capacity_confirmed": False,
                                                           "sla_assessed": False,
                                                           "rates_rps": RATES_RPS, "points": points})
                        state["active_rate_rps"] = rate
                        write(output / "run-status.json", state)
                        if trial["status"] != "valid":
                            raise FollowupError(f"Invalid traffic/accounting for {case['label']} "
                                                f"at {rate} req/s: {trial['reason_codes']}")
                    state["completed"].append(case["label"])
                    state["active"] = None
                    state["active_rate_rps"] = None
                    write(output / "run-status.json", state)
                finally:
                    if handle is not None:
                        runtime.stop(handle)
            report = compare_points(points)
            report["plots"] = plot_operator_points(output, points)
            write(output / "matched-comparison.json", report)
            fields = ["label", "config_id", "rate_rps", "offered_rps", "realized_rps",
                      "output_tokens_per_s", "dispatch_lag_p99_ms", "failures", "class",
                      "n_dispatched", "ttft_eligible", "tpot_eligible", "ttft_p50_ms",
                      "ttft_p90_ms", "tpot_p50_ms", "tpot_p90_ms"]
            with (output / "class-points.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for point in points:
                    for name, row in class_rows(point["trial"]).items():
                        writer.writerow({"label": point["label"], "config_id": point["config_id"],
                                         "rate_rps": point["rate_rps"],
                                         "offered_rps": point["trial"]["rate_rps"],
                                         "realized_rps": point["trial"]["realized_rate_rps"],
                                         "output_tokens_per_s": point["trial"]["native_summary_metrics"]
                                         ["output_tokens_per_s"],
                                         "dispatch_lag_p99_ms": point["trial"]["dispatch_lag_p99_ms"],
                                         "failures": point["trial"]["dispatched"] - point["trial"]["completed"],
                                         "class": name, **{key: row[key] for key in fields if key in row}})
            aggregate_fields = ["label", "config_id", "offered_rps", "realized_rps",
                                "output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms",
                                "tpot_p50_ms", "tpot_p90_ms", "dispatch_lag_p99_ms",
                                "planned", "dispatched", "completed", "failures", "status"]
            with (output / "operator-points.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=aggregate_fields)
                writer.writeheader()
                for point in points:
                    trial = point["trial"]
                    writer.writerow({"label": point["label"], "config_id": point["config_id"],
                                     "offered_rps": point["rate_rps"],
                                     "realized_rps": trial["realized_rate_rps"],
                                     "dispatch_lag_p99_ms": trial["dispatch_lag_p99_ms"],
                                     "planned": trial["planned"],
                                     "dispatched": trial["dispatched"],
                                     "completed": trial["completed"],
                                     "failures": trial["dispatched"] - trial["completed"],
                                     "status": trial["status"],
                                     **{key: trial["native_summary_metrics"].get(key) for key in
                                        ("output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms",
                                         "tpot_p50_ms", "tpot_p90_ms")}})
            state.update({"status": "complete", "capacity_confirmed": False})
            write(output / "run-status.json", state)
            return report
        except Exception as exc:
            state.update({"status": "blocked", "error": f"{type(exc).__name__}: {exc}"})
            write(output / "run-status.json", state)
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "run"))
    args = parser.parse_args()
    if args.action == "check":
        result = preflight()
        print(json.dumps({"status": result["status"], "rates_rps": RATES_RPS,
                          "requests_per_rate": 32,
                          "cases": [row["label"] for row in result["cases"]],
                          "capacity_confirmed": False}, indent=2))
        return 0
    result = run()
    print(json.dumps({"status": "complete", "requests_per_configuration": 96,
                      "matched_comparison": str(OUTPUT / "matched-comparison.json"),
                      "points": len(result["points"]), "capacity_confirmed": False,
                      "sla_assessed": False,
                      "independent_test": False}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V4 operator curve blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

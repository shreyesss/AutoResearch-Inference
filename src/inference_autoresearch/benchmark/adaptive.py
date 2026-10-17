"""AIPerf 0.13 rate search over evaluator-owned, frozen OPS inputs.

This is a separate exploratory load experiment on an already running server.
The ordinary matched server comparison still uses fixed-schedule replay.
"""

from __future__ import annotations

import json
import hashlib
import math
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from inference_autoresearch.contracts import ScenarioManifest, ServerHandle
from inference_autoresearch.evaluation.sla import SLAContractError, assess_observed_point, validate_policy
from inference_autoresearch.workloads.registry import WorkloadError, sha256_file, verify_scenario
from .aiperf import AIPerfAdapter, _jsonl, _percentile, _scenario_root


@dataclass(frozen=True)
class AdaptiveLoadSpec:
    request_count: int
    repeats: int
    iterations: int
    min_rate_rps: float
    max_rate_rps: float
    client_concurrency_cap: int = 256
    seed: int = 42
    planner: str = "bayesian"
    benchmark_duration_s: float = 600
    grace_period_s: float = 180
    max_dispatch_lag_ms: float = 20
    min_realized_rate_fraction: float = 0.5

    @classmethod
    def from_protocol(cls, protocol: dict[str, Any]) -> "AdaptiveLoadSpec":
        stage = protocol["stages"]["adaptive_exploration"]
        return cls(request_count=stage["request_count"], repeats=stage["repeats"],
                   iterations=stage["iterations"], min_rate_rps=stage["min_rate_rps"],
                   max_rate_rps=stage["max_rate_rps"],
                   client_concurrency_cap=stage["client_concurrency_cap"])

    def validate(self, scenario: ScenarioManifest) -> None:
        if scenario.traffic_mode != "independent_open_loop" or scenario.history_mode != "single_turn":
            raise WorkloadError("Adaptive rate search needs a frozen independent single-turn corpus")
        if self.request_count != scenario.expected_count or self.request_count < 2:
            raise WorkloadError("Every adaptive point must use the full frozen corpus exactly once")
        if not (1 <= self.repeats <= 10 and 2 <= self.iterations <= 200):
            raise WorkloadError("Invalid adaptive repeat/iteration budget")
        if (not all(math.isfinite(x) for x in (self.min_rate_rps, self.max_rate_rps,
                                               self.benchmark_duration_s, self.grace_period_s))
                or not 0 < self.min_rate_rps < self.max_rate_rps
                or self.benchmark_duration_s < (self.request_count - 1) / self.min_rate_rps + 10
                or self.grace_period_s < 0):
            raise WorkloadError("Adaptive duration does not cover the slowest sampled rate")
        if self.client_concurrency_cap < self.request_count:
            raise WorkloadError("Adaptive client concurrency cap could throttle offered load")
        if self.planner not in ("bayesian", "monotonic_sla", "smooth_isotonic"):
            raise WorkloadError("Unrecognized adaptive planner")
        if self.planner != "bayesian":
            raise WorkloadError("SLA-boundary planners need declared application SLOs")


def build_adaptive_argv(adapter: AIPerfAdapter, server: ServerHandle,
                        scenario: ScenarioManifest, spec: AdaptiveLoadSpec,
                        output_dir: Path) -> list[str]:
    spec.validate(scenario)
    if not adapter.aiperf_executable.is_file():
        raise WorkloadError("Pinned AIPerf executable is absent")
    manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
    checked = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=True)
    adapter._ensure_offline_snapshot(manifest)
    parsed = urlparse(server.base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
        raise WorkloadError("Server base_url must be a bare HTTP origin")
    # --no-fixed-schedule keeps the exact frozen bodies while AIPerf supplies
    # new arrival times at each proposed rate. Do not compare this with the
    # original timestamped scenario as an exact-schedule matched cell.
    return [str(adapter.aiperf_executable), "profile",
            "--model", manifest["model_id"], "--endpoint-type", "chat",
            "--endpoint", "/v1/chat/completions", "--streaming",
            "--url", parsed.netloc, "--tokenizer", manifest["model_id"],
            "--tokenizer-revision", manifest["tokenizer_revision"],
            "--apply-chat-template", "--use-server-token-count", "--per-chunk-usage",
            "--custom-dataset-type", "single-turn", "--input-file", str(checked["payload_path"]),
            "--no-fixed-schedule", "--dataset-sampling-strategy", "sequential",
            "--request-rate", str((spec.min_rate_rps + spec.max_rate_rps) / 2),
            "--request-rate-mode", "constant", "--concurrency", str(spec.client_concurrency_cap),
            "--request-count", str(spec.request_count), "--num-profile-runs", str(spec.repeats),
            "--benchmark-duration", str(spec.benchmark_duration_s),
            "--benchmark-grace-period", str(spec.grace_period_s),
            "--search-space", f"rate:{spec.min_rate_rps},{spec.max_rate_rps}:real",
            "--search-metric", "output_token_throughput", "--search-direction", "maximize",
            "--search-max-iterations", str(spec.iterations),
            "--search-initial-points", str(min(spec.iterations, 2)),
            "--search-planner", spec.planner, "--search-random-seed", str(spec.seed),
            "--random-seed", str(spec.seed), "--export-level", "raw", "--export-http-trace",
            "--output-artifact-dir", str(output_dir)]


def _stat(summary: dict[str, Any], name: str, statistic: str = "avg") -> float | None:
    value = summary.get(name, {})
    result = value.get(statistic) if isinstance(value, dict) else None
    if isinstance(result, (int, float)) and math.isfinite(result):
        return float(result)
    return None


def _request_key(text: str, output_length: int) -> tuple[str, int]:
    return text, output_length


def _shape(row: dict[str, Any]) -> str:
    """Labels for this pinned engineered OPS36 corpus, not production classes."""
    output_length = row["output_length"]
    if output_length == 256:
        return "chat_shape"
    if output_length == 512:
        return "document_shape"
    if output_length == 1024 and len(row["text"]) < 20000:
        return "code_shape"
    if output_length == 1024:
        return "agent_shape"
    return "unclassified_shape"


def _classify_trial(raw: list[dict[str, Any]], measured: list[dict[str, Any]],
                    planned: list[dict[str, Any]],
                    request_classes: dict[str, str] | None = None) -> tuple[bool, dict[str, Any]]:
    expected = Counter(_request_key(row["text"], row["output_length"]) for row in planned)
    if request_classes is not None and set(request_classes) != {row["session_id"] for row in planned}:
        raise WorkloadError("Verified request classes do not cover the frozen corpus")
    labels = {_request_key(row["text"], row["output_length"]):
              request_classes[row["session_id"]] if request_classes is not None else _shape(row)
              for row in planned}
    actual = Counter()
    by_request_id = {row.get("metadata", {}).get("x_request_id"): row
                     for row in measured}
    values: dict[str, dict[str, list[float]]] = {}
    counts: Counter[str] = Counter()
    for native in raw:
        payload = native.get("payload") or {}
        messages = payload.get("messages") or []
        if len(messages) != 1 or messages[0].get("role") != "user":
            return False, {}
        content = messages[0].get("content")
        output_length = payload.get("max_completion_tokens")
        if not isinstance(content, str) or type(output_length) is not int:
            return False, {}
        key = _request_key(content, output_length)
        actual[key] += 1
        label = labels.get(key, "unclassified_shape")
        counts[label] += 1
        metric_row = by_request_id.get(native.get("metadata", {}).get("x_request_id"), {})
        for native_name, short_name in (("time_to_first_token", "ttft"),
                                        ("inter_token_latency", "tpot"),
                                        ("request_latency", "e2e")):
            value = metric_row.get("metrics", {}).get(native_name, {}).get("value")
            if isinstance(value, (int, float)) and math.isfinite(value):
                values.setdefault(label, {}).setdefault(short_name, []).append(float(value))
    classes = {}
    for label in sorted(counts):
        classes[label] = {"n_dispatched": counts[label]}
        for metric in ("ttft", "tpot", "e2e"):
            samples = values.get(label, {}).get(metric, [])
            classes[label][f"{metric}_eligible"] = len(samples)
            for percentile, q in (("p50", .5), ("p90", .9), ("p95", .95), ("p99", .99)):
                classes[label][f"{metric}_{percentile}_ms"] = _percentile(samples, q)
    return actual == expected, classes


def normalize_search_history(output_dir: Path, *, config_id: str, scenario_id: str,
                             spec: AdaptiveLoadSpec,
                             scenario: ScenarioManifest | None = None) -> dict[str, Any]:
    """Expose each iteration and trial, including missing exports and invalid runs."""
    output_dir = Path(output_dir)
    source = output_dir / "search_history.json"
    if not source.is_file():
        raise WorkloadError(f"AIPerf search history missing: {source}")
    history = json.loads(source.read_text())
    native_config = history.get("config", {})
    spaces = native_config.get("search_space", [])
    expected_space = any(
        item.get("path") == "phases.profiling.rate"
        and math.isclose(item.get("lo", float("nan")), spec.min_rate_rps)
        and math.isclose(item.get("hi", float("nan")), spec.max_rate_rps)
        for item in spaces if isinstance(item, dict))
    if (native_config.get("max_iterations") != spec.iterations or not expected_space):
        raise WorkloadError("Native adaptive search space/budget differs from protocol")
    planned = None
    request_classes = None
    if scenario is not None:
        manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
        verified = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=True)
        planned = verified["planned"]
        request_classes = verified.get("request_classes")
    points: list[dict[str, Any]] = []
    for iteration in history.get("iterations", []):
        index = iteration["iteration_idx"]
        rate = iteration.get("variation_values", {}).get("phases.profiling.rate")
        if not isinstance(rate, (int, float)) or not math.isfinite(rate):
            raise WorkloadError(f"Iteration {index} has no finite offered rate")
        for repeat in range(1, spec.repeats + 1):
            trial = output_dir / f"search_iter_{index:04d}" / "profile_runs" / f"run_{repeat:04d}"
            summary_path = trial / "profile_export_aiperf.json"
            raw_path = trial / "profile_export_raw.jsonl"
            records_path = trial / "profile_export.jsonl"
            summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}
            raw = _jsonl(raw_path)
            metric_records = _jsonl(records_path)
            input_match, class_metrics = (_classify_trial(raw, metric_records, planned,
                                                           request_classes=request_classes)
                                          if planned is not None else (None, {}))
            starts = sorted(row["start_perf_ns"] for row in raw
                            if isinstance(row.get("start_perf_ns"), (int, float)))
            realized = ((len(starts) - 1) / ((starts[-1] - starts[0]) / 1e9)
                        if len(starts) >= 2 and starts[-1] > starts[0] else None)
            completed = sum(row.get("status") == 200 for row in raw)
            dispatched = len(raw)
            reasons = []
            if not summary or not raw_path.is_file() or not records_path.is_file():
                reasons.append("missing_native_export")
            if summary.get("is_complete") is not True:
                reasons.append("aiperf_incomplete")
            native_input = summary.get("input_config", {})
            phases = native_input.get("phases", [])
            phase = next((item for item in phases if item.get("name") == "profiling"), {})
            if (phase.get("requests") != spec.request_count
                    or phase.get("type") != "constant"
                    or not isinstance(phase.get("rate"), (int, float))
                    or not math.isclose(phase["rate"], rate, rel_tol=1e-9)):
                reasons.append("native_phase_mismatch")
            if not isinstance(phase.get("concurrency"), int) or phase["concurrency"] < spec.request_count:
                reasons.append("client_concurrency_binding")
            if scenario is not None:
                datasets = native_input.get("datasets", [])
                source_path = Path(scenario.metadata["asset"]).resolve()
                if not any(item.get("type") == "file"
                           and Path(item.get("path", "")).resolve() == source_path
                           and item.get("entries") == spec.request_count
                           for item in datasets):
                    reasons.append("native_corpus_mismatch")
            if dispatched != spec.request_count or completed != spec.request_count:
                reasons.append("request_accounting")
            if len(metric_records) != dispatched:
                reasons.append("missing_metric_records")
            if input_match is False:
                reasons.append("frozen_input_mismatch")
            if realized is None or realized < spec.min_realized_rate_fraction * rate:
                reasons.append("client_dispatch_shortfall")
            lag = _stat(summary, "credit_to_start_latency", "p99")
            if lag is None or lag > spec.max_dispatch_lag_ms:
                reasons.append("client_dispatch_lag")
            metrics = {
                "output_tokens_per_s": _stat(summary, "output_token_throughput"),
                "request_per_s": _stat(summary, "request_throughput"),
                "ttft_p50_ms": _stat(summary, "time_to_first_token", "p50"),
                "ttft_p90_ms": _stat(summary, "time_to_first_token", "p90"),
                "ttft_p95_ms": _stat(summary, "time_to_first_token", "p95"),
                "ttft_p99_ms": _stat(summary, "time_to_first_token", "p99"),
                "tpot_p50_ms": _stat(summary, "inter_token_latency", "p50"),
                "tpot_p90_ms": _stat(summary, "inter_token_latency", "p90"),
                "tpot_p95_ms": _stat(summary, "inter_token_latency", "p95"),
                "tpot_p99_ms": _stat(summary, "inter_token_latency", "p99"),
                "e2e_p50_ms": _stat(summary, "request_latency", "p50"),
                "e2e_p90_ms": _stat(summary, "request_latency", "p90"),
                "e2e_p95_ms": _stat(summary, "request_latency", "p95"),
                "e2e_p99_ms": _stat(summary, "request_latency", "p99"),
                "dispatch_lag_p99_ms": lag,
            }
            if any(metrics[key] is None for key in ("output_tokens_per_s", "ttft_p50_ms",
                                                     "tpot_p50_ms")):
                reasons.append("missing_primary_metric")
            points.append({
                "point_id": f"{config_id}:iter-{index:04d}:run-{repeat:04d}",
                "config_id": config_id, "scenario_id": scenario_id,
                "iteration_idx": index, "trial_index": repeat,
                "configured_rate": float(rate), "realized_rate": realized,
                "planner_feasible": iteration.get("feasible"),
                "objective_values": iteration.get("objective_values", []),
                "status": "valid" if not reasons else "invalid",
                "reason_codes": sorted(set(reasons)),
                "counts": {"planned": spec.request_count, "dispatched": dispatched,
                           "not_dispatched_or_missing_export": max(0, spec.request_count - dispatched),
                           "completed": completed, "failed": dispatched - completed,
                           "censored": None,
                           "metric_records": len(metric_records),
                           "ttft_eligible": int(_stat(summary, "time_to_first_token", "count") or 0),
                           "tpot_eligible": int(_stat(summary, "inter_token_latency", "count") or 0)},
                "metrics": metrics,
                "class_metrics": class_metrics,
                "class_label_policy": ("frozen_class_sidecar_v1" if request_classes is not None else
                                       "engineered_ops36_shape_v1" if planned is not None else None),
                "artifacts": {"summary": str(summary_path), "raw": str(raw_path),
                              "records": str(records_path)},
                "sample_count_policy": "constant_within_sweep",
            })
    payload = {
        "protocol_id": "ops-mixed-v2-adaptive-exploration",
        "config_id": config_id, "scenario_id": scenario_id,
        "sampling": {"request_count_per_trial": spec.request_count,
                     "repeats_per_iteration": spec.repeats,
                     "max_iterations": spec.iterations},
        "claim": "exploratory_load_curve_only",
        "native_history": str(source), "native_history_sha256": sha256_file(source),
        "convergence_reason": history.get("convergence_reason"),
        "planner_config": history.get("config"),
        "points": points,
    }
    target = output_dir / "normalized-search-points.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def run_adaptive(server: ServerHandle, scenario: ScenarioManifest, spec: AdaptiveLoadSpec,
                 output_dir: Path, adapter: AIPerfAdapter, *,
                 preparation_receipt: Path) -> dict[str, Any]:
    """Run on an already prepared server; caller owns the GPU lease and cleanup."""
    output_dir = Path(output_dir)
    receipt_path = Path(preparation_receipt)
    if not receipt_path.is_file():
        raise WorkloadError("Adaptive trial needs a disjoint warmup receipt")
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("version") != "preparation-receipt-v1"
            or receipt.get("server_id") != server.server_id
            or receipt.get("config_id") != server.config_id
            or receipt.get("scenario_id") != scenario.scenario_id):
        raise WorkloadError("Adaptive warmup receipt does not match server and scenario")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise WorkloadError(f"Refusing to overwrite adaptive artifacts: {output_dir}")
    argv = build_adaptive_argv(adapter, server, scenario, spec, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "aiperf-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
    timeout = int(spec.iterations * spec.repeats *
                  (spec.benchmark_duration_s + spec.grace_period_s + 90))
    with (output_dir / "aiperf-console.log").open("w") as console:
        try:
            process = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                     env=adapter._offline_env(), timeout=timeout, check=False)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            exit_code = -1
    (output_dir / "aiperf-exit.json").write_text(json.dumps({"exit_code": exit_code}) + "\n")
    result = normalize_search_history(output_dir, config_id=server.config_id,
                                      scenario_id=scenario.scenario_id, spec=spec,
                                      scenario=scenario)
    result["process_exit_code"] = exit_code
    result["preparation_receipt"] = str(receipt_path)
    from inference_autoresearch.search.report import export_adaptive_points
    result["report_artifacts"] = export_adaptive_points(result["points"], output_dir / "report")
    return result


def _native_sla_records(raw: list[dict[str, Any]], measured: list[dict[str, Any]],
                        planned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Join AIPerf's generated IDs to frozen workload IDs by exact request body.

    The frozen OPS corpus has unique (text, output cap) pairs. Refuse any
    ambiguous, unknown, or duplicate body instead of assigning a class from
    token length or a possibly incomplete AIPerf summary.
    """
    expected = {_request_key(row["text"], row["output_length"]): row["session_id"]
                for row in planned}
    if len(expected) != len(planned):
        raise SLAContractError("frozen workload has ambiguous request bodies")
    by_native_id: dict[str, dict[str, Any]] = {}
    for row in measured:
        native_id = row.get("metadata", {}).get("x_request_id")
        if not isinstance(native_id, str) or not native_id or native_id in by_native_id:
            raise SLAContractError("native metrics need unique request IDs")
        by_native_id[native_id] = row
    joined = {row["session_id"]: {"request_id": row["session_id"],
                                  "terminal_state": "missing"} for row in planned}
    seen_native: set[str] = set()
    seen_frozen: set[str] = set()
    for row in raw:
        payload = row.get("payload") or {}
        messages = payload.get("messages") or []
        if (len(messages) != 1 or messages[0].get("role") != "user"
                or not isinstance(messages[0].get("content"), str)
                or type(payload.get("max_completion_tokens")) is not int):
            raise SLAContractError("native request body does not match single-turn corpus")
        key = _request_key(messages[0]["content"], payload["max_completion_tokens"])
        frozen_id = expected.get(key)
        native_id = row.get("metadata", {}).get("x_request_id")
        if frozen_id is None or frozen_id in seen_frozen:
            raise SLAContractError("native request body is unknown or duplicated")
        if not isinstance(native_id, str) or not native_id or native_id in seen_native:
            raise SLAContractError("native request ID is absent or duplicated")
        seen_frozen.add(frozen_id)
        seen_native.add(native_id)
        metrics = by_native_id.get(native_id, {}).get("metrics", {})
        def metric(name: str) -> float | None:
            item = metrics.get(name, {})
            value = item.get("value") if isinstance(item, dict) and item.get("unit") == "ms" else None
            return float(value) if type(value) in (int, float) and math.isfinite(value) else None
        joined[frozen_id] = {"request_id": frozen_id,
                             "terminal_state": "completed" if row.get("status") == 200
                             and not row.get("metadata", {}).get("was_cancelled") else "failed",
                             "ttft_ms": metric("time_to_first_token"),
                             "tpot_ms": metric("inter_token_latency")}
    if set(by_native_id) != seen_native:
        raise SLAContractError("native metric records do not exactly match dispatched requests")
    return list(joined.values())


def assess_adaptive_sla(output_dir: Path, scenario: ScenarioManifest,
                        policy: dict[str, Any]) -> dict[str, Any]:
    """Assess every existing adaptive trial offline; never select a capacity rate."""
    validate_policy(policy)
    output_dir = Path(output_dir)
    normalized_path = output_dir / "normalized-search-points.json"
    history = json.loads(normalized_path.read_text())
    if (history.get("scenario_id") != scenario.scenario_id
            or history.get("claim") != "exploratory_load_curve_only"
            or not isinstance(history.get("points"), list)):
        raise SLAContractError("adaptive history identity or claim differs from frozen scenario")
    manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
    verified = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=True)
    planned = verified["planned"]
    if manifest.get("request_class_path") and verified.get("request_classes") is None:
        raise SLAContractError("frozen class sidecar was not verified")
    explicit_classes = verified.get("request_classes")
    if explicit_classes is not None:
        if (not isinstance(explicit_classes, dict)
                or set(explicit_classes) != {row["session_id"] for row in planned}):
            raise SLAContractError("class sidecar does not exactly cover frozen workload IDs")
        class_by_id = explicit_classes
        class_label_policy = "frozen_class_sidecar_v1"
        class_label_source = str(scenario.metadata.get("request_class_path")
                                 or manifest.get("request_class_path"))
    elif scenario.scenario_id == "qwen-ops-mixed-reference-v1":
        class_by_id = {row["session_id"]: _shape(row).removesuffix("_shape") for row in planned}
        class_label_policy = "engineered_ops36_shape_v1"
        class_label_source = "frozen exact request body/output cap; OPS36 shape rule"
    else:
        raise SLAContractError("SLA assessment requires a frozen request-class sidecar")
    if set(class_by_id.values()) != set(policy["classes"]):
        raise SLAContractError("SLA classes do not match frozen workload class labels")
    results = []
    seen_trials: set[tuple[int, int]] = set()
    for point in history["points"]:
        assessed = {"point_id": point.get("point_id"),
                    "configured_rate": point.get("configured_rate"),
                    "realized_rate": point.get("realized_rate"),
                    "native_status": point.get("status"),
                    "observed_feasible": False, "reason_codes": [],
                    "assessment": None}
        index, repeat = point.get("iteration_idx"), point.get("trial_index")
        if type(index) is not int or type(repeat) is not int or index < 0 or repeat < 1:
            assessed["reason_codes"].append("missing_trial_identity")
        elif (index, repeat) in seen_trials:
            assessed["reason_codes"].append("duplicate_trial_identity")
        else:
            seen_trials.add((index, repeat))
            trial = output_dir / f"search_iter_{index:04d}" / "profile_runs" / f"run_{repeat:04d}"
            raw_path = trial / "profile_export_raw.jsonl"
            records_path = trial / "profile_export.jsonl"
            assessed["native_artifacts"] = {
                "raw": {"path": str(raw_path), "sha256": sha256_file(raw_path)}
                if raw_path.is_file() else None,
                "metrics": {"path": str(records_path), "sha256": sha256_file(records_path)}
                if records_path.is_file() else None,
            }
            try:
                if not raw_path.is_file() or not records_path.is_file():
                    raise SLAContractError("native raw or metric export is missing")
                native = _native_sla_records(_jsonl(raw_path), _jsonl(records_path), planned)
                assessment = assess_observed_point(native, policy, class_by_id)
                assessed["assessment"] = assessment
                assessed["observed_feasible"] = assessment["observed_feasible"]
                assessed["reason_codes"] = sorted({reason for row in assessment["classes"].values()
                                                   for reason in row["reason_codes"]})
            except (OSError, ValueError, SLAContractError) as exc:
                assessed["reason_codes"].append("native_class_records_unassessable")
                assessed["detail"] = str(exc)
        if point.get("status") != "valid":
            assessed["observed_feasible"] = False
            assessed["reason_codes"].append("adaptive_trial_invalid")
        assessed["reason_codes"] = sorted(set(assessed["reason_codes"]))
        results.append(assessed)
    return {"schema_version": "adaptive-sla-assessment-v1",
            "policy_id": policy["policy_id"],
            "policy_sha256": hashlib.sha256(json.dumps(policy, sort_keys=True,
                                                         separators=(",", ":")).encode()).hexdigest(),
            "scenario_id": scenario.scenario_id,
            "config_id": history.get("config_id"),
            "class_label_policy": class_label_policy,
            "class_label_source": class_label_source,
            "source": str(normalized_path), "source_sha256": sha256_file(normalized_path),
            "claim": "observed_adaptive_points_only_no_confirmed_capacity",
            "capacity_confirmed": False,
            "point_count": len(results), "observed_feasible_point_count": sum(
                item["observed_feasible"] for item in results),
            "points": results}

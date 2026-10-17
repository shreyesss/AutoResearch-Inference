"""Class-aware, sequential AIPerf rate profiling on a qualified OPS workload.

AIPerf generates and measures each offered rate. The outer boundary planner
uses the frozen per-class policy because AIPerf 0.13 cannot enforce it. A
36-request screen checks transport only; every SLA decision uses all 240
requests in the qualified development corpus. Results are observed points,
never independent capacity confirmation.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from inference_autoresearch.contracts import ScenarioManifest, ServerHandle
from inference_autoresearch.evaluation.sla import assess_observed_point, validate_policy
from inference_autoresearch.workloads.registry import WorkloadError, sha256_file, verify_scenario

from .adaptive import _classify_trial, _native_sla_records, _stat
from .aiperf import AIPerfAdapter, _jsonl, _scenario_root


@dataclass(frozen=True)
class SLAProfileSpec:
    initial_rate_rps: float = 0.2
    min_rate_rps: float = 0.1
    max_rate_rps: float = 1.6
    multiplier: float = 2.0
    max_qualified_points: int = 6
    relative_bracket_tolerance: float = 0.1
    client_concurrency_cap: int = 256
    grace_period_s: float = 180.0
    max_dispatch_lag_p99_ms: float = 20.0
    min_realized_rate_fraction: float = 0.75
    seed: int = 42

    def validate(self, screen: ScenarioManifest, development: ScenarioManifest,
                 policy: dict[str, Any]) -> dict[str, Any]:
        validate_policy(policy)
        if screen.expected_count != 36 or development.expected_count != 240:
            raise WorkloadError("SLA profiler requires 36-request screen and qualified 240-request development corpus")
        if (screen.scenario_id == development.scenario_id
                or screen.traffic_mode != "independent_open_loop"
                or development.traffic_mode != "independent_open_loop"):
            raise WorkloadError("SLA profiler needs distinct independent screen and development workloads")
        if (not all(math.isfinite(value) for value in (
                self.initial_rate_rps, self.min_rate_rps, self.max_rate_rps, self.multiplier,
                self.relative_bracket_tolerance, self.grace_period_s,
                self.max_dispatch_lag_p99_ms, self.min_realized_rate_fraction))
                or not 0 < self.min_rate_rps <= self.initial_rate_rps < self.max_rate_rps
                or self.multiplier <= 1
                or not 0 < self.relative_bracket_tolerance < 1
                or self.grace_period_s < 0
                or self.max_dispatch_lag_p99_ms <= 0
                or not 0 < self.min_realized_rate_fraction <= 1
                or not 1 <= self.max_qualified_points <= 30
                or self.client_concurrency_cap < 240):
            raise WorkloadError("Invalid bounded SLA profile search budget")
        manifest = development.metadata.get("manifest") or json.loads(Path(development.path).read_text())
        verified = verify_scenario(manifest, root=_scenario_root(development), require_validated=True)
        classes = verified["request_classes"]
        if not classes or set(classes.values()) != set(policy["classes"]):
            raise WorkloadError("Qualified development corpus needs exact class sidecar matching policy")
        if any(list(classes.values()).count(name) < spec["min_eligible_requests"]
               for name, spec in policy["classes"].items()):
            raise WorkloadError("Development class quota is below the SLA policy minimum")
        screen_manifest = screen.metadata.get("manifest") or json.loads(Path(screen.path).read_text())
        verify_scenario(screen_manifest, root=_scenario_root(screen), require_validated=True)
        return verified


def build_rate_argv(adapter: AIPerfAdapter, server: ServerHandle,
                    scenario: ScenarioManifest, *, rate: float, spec: SLAProfileSpec,
                    output_dir: Path) -> list[str]:
    if not math.isfinite(rate) or rate <= 0:
        raise WorkloadError("Offered rate must be positive and finite")
    if not adapter.aiperf_executable.is_file():
        raise WorkloadError("Pinned AIPerf executable is absent")
    manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
    checked = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=True)
    adapter._ensure_offline_snapshot(manifest)
    parsed = urlparse(server.base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
        raise WorkloadError("Server base_url must be a bare HTTP origin")
    # A Poisson trace can take longer than N/rate. The request cap stops a
    # completed run; the duration is a generous dispatch ceiling, not a fixed
    # time tax on each successful trial.
    duration_s = math.ceil((scenario.expected_count + 4 * math.sqrt(scenario.expected_count)) / rate) + 30
    return [str(adapter.aiperf_executable), "profile",
            "--model", manifest["model_id"], "--endpoint-type", "chat",
            "--endpoint", "/v1/chat/completions", "--streaming",
            "--url", parsed.netloc, "--tokenizer", manifest["model_id"],
            "--tokenizer-revision", manifest["tokenizer_revision"],
            "--apply-chat-template", "--use-server-token-count", "--per-chunk-usage",
            "--custom-dataset-type", "single-turn", "--input-file", str(checked["payload_path"]),
            "--no-fixed-schedule", "--dataset-sampling-strategy", "sequential",
            "--request-rate", str(rate), "--arrival-pattern", "poisson",
            "--concurrency", str(spec.client_concurrency_cap),
            "--request-count", str(scenario.expected_count),
            "--benchmark-duration", str(duration_s),
            "--benchmark-grace-period", str(spec.grace_period_s),
            "--random-seed", str(spec.seed + round(rate * 1_000_000)),
            "--export-level", "raw", "--export-http-trace",
            "--output-artifact-dir", str(output_dir)]


def assess_rate_trial(output_dir: Path, scenario: ScenarioManifest, policy: dict[str, Any] | None,
                      *, rate: float, process_exit_code: int, spec: SLAProfileSpec) -> dict[str, Any]:
    """Fail closed on accounting, transport, dispatch, and per-class SLA evidence."""
    output_dir = Path(output_dir)
    manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
    checked = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=True)
    planned = checked["planned"]
    paths = {"summary": output_dir / "profile_export_aiperf.json",
             "raw": output_dir / "profile_export_raw.jsonl",
             "records": output_dir / "profile_export.jsonl",
             "server_metrics": output_dir / "server_metrics_export.json"}
    artifacts = {name: {"path": str(path), "sha256": sha256_file(path)} if path.is_file() else None
                 for name, path in paths.items()}
    reasons: list[str] = []
    if process_exit_code:
        reasons.append("aiperf_process_failure")
    if not all(paths[name].is_file() for name in ("summary", "raw", "records")):
        reasons.append("missing_native_export")
    try:
        summary = json.loads(paths["summary"].read_text()) if paths["summary"].is_file() else {}
        raw = _jsonl(paths["raw"])
        measured = _jsonl(paths["records"])
    except (OSError, ValueError, WorkloadError) as exc:
        reasons.append("invalid_native_export")
        summary, raw, measured = {}, [], []
        export_detail = str(exc)
    else:
        export_detail = None
    if summary.get("is_complete") is not True:
        reasons.append("aiperf_incomplete")
    phase = next((item for item in summary.get("input_config", {}).get("phases", [])
                  if item.get("name") == "profiling"), {})
    if (phase.get("requests") != scenario.expected_count or phase.get("type") != "poisson"
            or type(phase.get("rate")) not in (int, float)
            or not math.isclose(phase["rate"], rate, rel_tol=1e-9)):
        reasons.append("native_phase_mismatch")
    if type(phase.get("concurrency")) is not int or phase["concurrency"] < scenario.expected_count:
        reasons.append("client_concurrency_binding")
    datasets = summary.get("input_config", {}).get("datasets", [])
    if not any(item.get("type") == "file"
               and Path(item.get("path", "")).resolve() == checked["payload_path"].resolve()
               for item in datasets):
        reasons.append("native_corpus_mismatch")
    try:
        input_match, class_metrics = _classify_trial(raw, measured, planned,
                                                     request_classes=checked["request_classes"])
    except (KeyError, TypeError, ValueError) as exc:
        input_match, class_metrics = False, {}
        reasons.append("frozen_input_unassessable")
        export_detail = str(exc)
    if not input_match:
        reasons.append("frozen_input_mismatch")
    if len(raw) != scenario.expected_count or sum(row.get("status") == 200 for row in raw) != scenario.expected_count:
        reasons.append("request_accounting")
    if len(measured) != len(raw):
        reasons.append("missing_metric_records")
    starts = sorted(row["start_perf_ns"] for row in raw
                    if type(row.get("start_perf_ns")) in (int, float))
    realized = ((len(starts) - 1) / ((starts[-1] - starts[0]) / 1e9)
                if len(starts) >= 2 and starts[-1] > starts[0] else None)
    if realized is None or realized < spec.min_realized_rate_fraction * rate:
        reasons.append("client_dispatch_shortfall")
    lag = _stat(summary, "credit_to_start_latency", "p99")
    if lag is None or lag > spec.max_dispatch_lag_p99_ms:
        reasons.append("client_dispatch_lag")
    assessment = None
    if policy is not None:
        if checked["request_classes"] is None:
            reasons.append("class_sidecar_missing")
        else:
            try:
                native = _native_sla_records(raw, measured, planned)
                assessment = assess_observed_point(native, policy, checked["request_classes"])
            except (ValueError, KeyError, TypeError, WorkloadError) as exc:
                reasons.append("native_class_records_unassessable")
                export_detail = str(exc)
    valid = not reasons
    return {"rate_rps": rate, "realized_rate_rps": realized,
            "stage": "qualified_development" if policy is not None else "transport_screen",
            "scenario_id": scenario.scenario_id, "planned": scenario.expected_count,
            "dispatched": len(raw), "completed": sum(row.get("status") == 200 for row in raw),
            "status": "valid" if valid else "invalid", "reason_codes": sorted(set(reasons)),
            "detail": export_detail, "process_exit_code": process_exit_code,
            "dispatch_lag_p99_ms": lag, "native_summary_metrics": {
                "request_per_s": _stat(summary, "request_throughput"),
                "output_tokens_per_s": _stat(summary, "output_token_throughput"),
                "ttft_p50_ms": _stat(summary, "time_to_first_token", "p50"),
                "ttft_p90_ms": _stat(summary, "time_to_first_token", "p90"),
                "tpot_p50_ms": _stat(summary, "inter_token_latency", "p50"),
                "tpot_p90_ms": _stat(summary, "inter_token_latency", "p90")},
            "class_metrics": class_metrics, "assessment": assessment,
            "observed_feasible": bool(valid and assessment and assessment["observed_feasible"]),
            "artifacts": artifacts}


def next_rate(points: list[dict[str, Any]], spec: SLAProfileSpec) -> float | None:
    """Expand to a bracket, then bisect; invalid evidence never defines an SLA boundary."""
    qualified = [point for point in points if point.get("qualified")]
    if points and len(qualified) != len(points):
        return None
    if len(qualified) >= spec.max_qualified_points:
        return None
    if not qualified:
        return spec.initial_rate_rps
    valid = [point for point in qualified if point["qualified"]["status"] == "valid"]
    if len(valid) != len(qualified):
        return None
    feasible = [point["rate_rps"] for point in valid if point["qualified"]["observed_feasible"]]
    infeasible = [point["rate_rps"] for point in valid if not point["qualified"]["observed_feasible"]]
    if not feasible:
        smallest = min(point["rate_rps"] for point in valid)
        if smallest <= spec.min_rate_rps * (1 + 1e-9):
            return None
        candidate = max(smallest / spec.multiplier, spec.min_rate_rps)
        return round(candidate, 8)
    low = max(feasible)
    higher_failures = [rate for rate in infeasible if rate > low]
    if higher_failures:
        high = min(higher_failures)
        if (high - low) / low <= spec.relative_bracket_tolerance:
            return None
        return round((low + high) / 2, 8)
    candidate = min(low * spec.multiplier, spec.max_rate_rps)
    return round(candidate, 8) if candidate > low * (1 + 1e-9) else None


def profile_stop_reason(points: list[dict[str, Any]], spec: SLAProfileSpec) -> str:
    if not points:
        return "no_point_scheduled"
    if any((point.get("screen") or {}).get("status") == "invalid"
           or (point.get("qualified") or {}).get("status") == "invalid"
           for point in points):
        return "invalid_trial_requires_investigation"
    qualified = [point for point in points if point.get("qualified")]
    if len(qualified) >= spec.max_qualified_points:
        return "qualified_point_budget_exhausted"
    feasible = [point["rate_rps"] for point in qualified if point["qualified"]["observed_feasible"]]
    if not feasible:
        return "baseline_infeasible_or_lower_bound_reached"
    low = max(feasible)
    higher_failures = [point["rate_rps"] for point in qualified
                       if not point["qualified"]["observed_feasible"]
                       and point["rate_rps"] > low]
    if higher_failures:
        return "bracket_tolerance_reached"
    if low >= spec.max_rate_rps * (1 - 1e-9):
        return "maximum_rate_reached_without_boundary"
    return "planner_stopped_without_boundary"


def run_sla_profile(server: ServerHandle, screen: ScenarioManifest,
                    development: ScenarioManifest, policy: dict[str, Any], spec: SLAProfileSpec,
                    output_dir: Path, adapter: AIPerfAdapter, *,
                    preparation_receipt: Path, policy_source_path: Path) -> dict[str, Any]:
    """Measure one prepared server; persist each point before deciding the next rate."""
    spec.validate(screen, development, policy)
    receipt = json.loads(Path(preparation_receipt).read_text())
    if (receipt.get("version") != "preparation-receipt-v1"
            or receipt.get("server_id") != server.server_id
            or receipt.get("config_id") != server.config_id
            or receipt.get("scenario_id") != development.scenario_id):
        raise WorkloadError("SLA profile warmup receipt does not match prepared server and development scenario")
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise WorkloadError(f"Refusing to overwrite SLA profile artifacts: {output_dir}")
    output_dir.mkdir(parents=True)
    policy_source_path = Path(policy_source_path)
    if json.loads(policy_source_path.read_text()) != policy:
        raise WorkloadError("Approved policy source differs from loaded SLA policy")
    protocol = {"schema_version": "sla-profile-points-v1",
                "claim": "observed_development_points_no_confirmed_capacity",
                "capacity_confirmed": False, "config_id": server.config_id,
                "screen_scenario_id": screen.scenario_id,
                "development_scenario_id": development.scenario_id,
                "policy_id": policy["policy_id"],
                "policy_sha256": sha256_file(policy_source_path),
                "spec": asdict(spec), "points": []}
    # Copy exact bytes so the policy hash matches the approved study pin.
    shutil.copyfile(policy_source_path, output_dir / "sla-policy.json")
    (output_dir / "profile-protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    while True:
        rate = next_rate(protocol["points"], spec)
        if rate is None:
            break
        point: dict[str, Any] = {"rate_rps": rate,
                                 "arrival_pattern": "poisson",
                                 "arrival_seed": spec.seed + round(rate * 1_000_000),
                                 "screen": None, "qualified": None}
        protocol["points"].append(point)
        for stage, scenario in (("screen", screen), ("qualified", development)):
            directory = output_dir / f"point-{len(protocol['points']):02d}-{rate:g}" / stage
            argv = build_rate_argv(adapter, server, scenario, rate=rate, spec=spec,
                                   output_dir=directory)
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "aiperf-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
            timeout = (math.ceil((scenario.expected_count + 4 * math.sqrt(scenario.expected_count)) / rate)
                       + math.ceil(spec.grace_period_s) + 210)
            with (directory / "aiperf-console.log").open("w") as console:
                try:
                    process = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                             env=adapter._offline_env(), timeout=timeout, check=False)
                    exit_code = process.returncode
                except subprocess.TimeoutExpired:
                    exit_code = -1
            point[stage] = assess_rate_trial(directory, scenario,
                                             policy if stage == "qualified" else None,
                                             rate=rate, process_exit_code=exit_code, spec=spec)
            point[stage]["directory"] = str(directory)
            (output_dir / "sla-profile-points.json").write_text(
                json.dumps(protocol, indent=2, sort_keys=True) + "\n")
            if point[stage]["status"] != "valid":
                break
    protocol["stop_reason"] = profile_stop_reason(protocol["points"], spec)
    (output_dir / "sla-profile-points.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    return protocol

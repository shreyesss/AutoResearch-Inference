"""Pinned AIPerf 0.13 single-turn replay adapter and lossless request accounting.

The benchmark engine owns scheduling and HTTP; this adapter only verifies frozen
inputs, launches an allowlisted argv, and normalizes the native exports. It never
accepts benchmark flags or workload paths from candidate proposals.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from inference_autoresearch.contracts import CellResult, MeasurementPolicy, ScenarioManifest, ServerHandle
from inference_autoresearch.workloads.registry import WorkloadError, sha256_file, verify_scenario


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _scenario_root(scenario: ScenarioManifest | dict[str, Any]) -> Path:
    metadata = _field(scenario, "metadata", {}) or {}
    if metadata.get("registry_root"):
        return Path(metadata["registry_root"])
    manifest_path = _field(scenario, "path")
    if manifest_path:
        path = Path(manifest_path).resolve()
        if path.parent.name == "workloads" and path.parent.parent.name == "configs":
            return path.parents[2]
    raise WorkloadError("Scenario needs an explicit registry_root or a registered manifest path")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        with path.open() as stream:
            return [json.loads(line) for line in stream if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkloadError(f"Invalid AIPerf export {path}: {exc}") from exc


def _metric(row: dict[str, Any] | None, key: str) -> float | int | None:
    item = (row or {}).get("metrics", {}).get(key)
    value = item.get("value") if isinstance(item, dict) else None
    return value if isinstance(value, (int, float)) and math.isfinite(value) else None


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    point = (len(values) - 1) * q
    low, high = math.floor(point), math.ceil(point)
    if low == high:
        return values[low]
    return values[low] * (high - point) + values[high] * (point - low)


def _one_by_id(rows: list[dict[str, Any]], key: str) -> tuple[dict[str, dict[str, Any]], bool]:
    result: dict[str, dict[str, Any]] = {}
    duplicate = False
    for row in rows:
        request_id = row.get("metadata", {}).get(key)
        if not isinstance(request_id, str) or not request_id or request_id in result:
            duplicate = True
        else:
            result[request_id] = row
    return result, duplicate


def _planned_key(row: dict[str, Any], dependent: bool) -> str:
    if dependent:
        return f"{row['session_id'].replace(':', '_')}#{row['round_index']}"
    return row["session_id"]


def _raw_key(row: dict[str, Any], dependent: bool) -> str | None:
    meta = row.get("metadata", {})
    session = meta.get("conversation_id")
    if not isinstance(session, str):
        return None
    return f"{session}#{meta.get('turn_index')}" if dependent else session


def _source_offsets(rows: list[dict[str, Any]]) -> list[float | None]:
    stamps = []
    for row in rows:
        values = [event.get("timestamp") for event in row.get("timing_events", [])
                  if event.get("event_type") in ("user_message", "tool_result") and event.get("timestamp")]
        stamps.append(datetime.fromisoformat(max(values).replace("Z", "+00:00")) if values else None)
    first = next((stamp for stamp in stamps if stamp is not None), None)
    return [(stamp - first).total_seconds() * 1000 if stamp is not None and first is not None else None
            for stamp in stamps]


def _server_gauges(path: Path) -> dict[str, float | None]:
    gauges: dict[str, float | None] = {"queue_max": None, "kv_cache_usage_max": None,
                                      "prefix_cache_hits": None, "prefix_cache_queries": None,
                                      "achieved_cache_hit_fraction": None,
                                      "mtp_accepted_tokens": None, "mtp_draft_tokens": None,
                                      "mtp_acceptance_fraction": None}
    if not path.is_file():
        return gauges
    try:
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(line for line in stream if line.strip() and not line.startswith("#")))
    except (OSError, csv.Error):
        return gauges
    for row in rows:
        name = row.get("Metric", "")
        if name == "vllm:num_requests_waiting" and row.get("max"):
            gauges["queue_max"] = float(row["max"])
        elif name == "vllm:kv_cache_usage_perc" and row.get("max"):
            gauges["kv_cache_usage_max"] = float(row["max"])
        elif name == "vllm:prefix_cache_hits" and row.get("avg"):
            gauges["prefix_cache_hits"] = float(row["avg"])
        elif name == "vllm:prefix_cache_queries" and row.get("avg"):
            gauges["prefix_cache_queries"] = float(row["avg"])
        elif name == "vllm:spec_decode_num_accepted_tokens" and row.get("avg"):
            gauges["mtp_accepted_tokens"] = float(row["avg"])
        elif name == "vllm:spec_decode_num_draft_tokens" and row.get("avg"):
            gauges["mtp_draft_tokens"] = float(row["avg"])
    if gauges["prefix_cache_hits"] is not None and gauges["prefix_cache_queries"]:
        gauges["achieved_cache_hit_fraction"] = gauges["prefix_cache_hits"] / gauges["prefix_cache_queries"]
    if gauges["mtp_accepted_tokens"] is not None and gauges["mtp_draft_tokens"]:
        gauges["mtp_acceptance_fraction"] = gauges["mtp_accepted_tokens"] / gauges["mtp_draft_tokens"]
    return gauges


def normalize_exports(scenario: ScenarioManifest | dict[str, Any], artifact_dir: Path,
                      *, config_id: str, run_id: str, stage: str = "pilot",
                      replicate: int = 1, output_dir: Path | None = None,
                      max_schedule_lag_ms: float = 20.0) -> CellResult:
    """Account for every planned request and derive one provisional cell result.

    Missing AIPerf rows become explicit `not_dispatched` records. A response with
    absent metrics is failed/ineligible, never a zero-latency success. `request_id`
    is the frozen session ID; `aiperf_request_id` preserves the native UUID.
    """
    artifact_dir = Path(artifact_dir)
    output_dir = Path(output_dir or artifact_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = _field(scenario, "metadata", {}).get("manifest") if not isinstance(scenario, dict) else scenario.get("manifest")
    if manifest is None:
        path = _field(scenario, "path")
        manifest = json.loads(Path(path).read_text()) if path else scenario
    checked = verify_scenario(manifest, root=_scenario_root(scenario),
                              require_validated=(stage != "pilot"))
    planned = checked["planned"]
    dependent = manifest["traffic_mode"] == "dependent_sessions"
    source_offsets = _source_offsets(planned) if dependent else [None] * len(planned)
    raw_path = artifact_dir / "profile_export_raw.jsonl"
    metrics_path = artifact_dir / "profile_export.jsonl"
    summary_path = artifact_dir / "profile_export_aiperf.json"
    raw = _jsonl(raw_path)
    measured = _jsonl(metrics_path)
    actual: dict[str, dict[str, Any]] = {}
    raw_duplicates = False
    for item in raw:
        key = _raw_key(item, dependent)
        if key is None or key in actual:
            raw_duplicates = True
        else:
            actual[key] = item
    raw_lines = {_raw_key(item, dependent): i
                 for i, item in enumerate(raw, start=1)}
    metric_rows, metric_duplicates = _one_by_id(measured, "x_request_id")
    reasons: set[str] = set()
    if raw_duplicates or metric_duplicates:
        reasons.add("request_accounting")
    if set(actual) - {_planned_key(row, dependent) for row in planned}:
        reasons.add("request_accounting")
    if len(metric_rows) != len(measured) or len(raw) != len(actual):
        reasons.add("request_accounting")
    summary = {}
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text())
        except (OSError, json.JSONDecodeError):
            reasons.add("invalid_aiperf_export")
    if summary.get("is_complete") is not True:
        reasons.add("incomplete_aiperf_export")
    if summary.get("aiperf_version") not in (None, "0.13.0"):
        reasons.add("unsupported_aiperf_version")
    first_start = min((r.get("metadata", {}).get("request_start_ns") for r in raw
                       if isinstance(r.get("metadata", {}).get("request_start_ns"), int)), default=None)
    first_credit = min((r.get("metadata", {}).get("credit_issued_ns") for r in raw
                        if isinstance(r.get("metadata", {}).get("credit_issued_ns"), int)), default=None)
    records: list[dict[str, Any]] = []
    ttfts: list[float] = []
    tpots: list[float] = []
    scheduled_ttfts: list[float] = []
    lags: list[float] = []
    schedule_errors: list[float] = []
    starts: list[int] = []
    ends: list[int] = []
    counts = {"planned": len(planned), "dispatched": 0, "not_dispatched": 0,
              "completed": 0, "failed": 0, "timed_out": 0, "canceled": 0,
              "censored": 0, "tpot_eligible": 0, "successful_completion_tokens": 0}
    for index, row in enumerate(planned):
        planned_id = _planned_key(row, dependent)
        native = actual.get(planned_id)
        base = {"request_id": planned_id, "session_id": row["session_id"],
                "turn_index": row.get("round_index", 0),
                "scenario_id": manifest["scenario_id"], "configuration_id": config_id,
                "run_id": run_id, "stage": stage, "replicate": replicate, "planned_index": index,
                "scheduled_arrival_ms": row.get("timestamp") if not dependent else None,
                "source_submission_offset_ms": source_offsets[index],
                "aiperf_request_id": None,
                "actual_dispatch_ns": None, "first_relevant_token_ns": None,
                "first_token_timestamp_source": "aiperf_ttft_offset_estimate",
                "final_relevant_token_ns": None, "terminal_ns": None,
                "ttft_ms": None, "tpot_ms": None,
                "dispatch_lag_ms": None, "input_tokens": None,
                "completion_tokens": None, "reasoning_tokens": None,
                "counting_source": "server_usage", "http_status": None,
                "terminal_state": "not_dispatched", "error": None,
                "raw_record_line": None}
        if native is None:
            counts["not_dispatched"] += 1
            reasons.add("request_accounting")
            records.append(base)
            continue
        counts["dispatched"] += 1
        meta = native.get("metadata", {})
        native_id = meta.get("x_request_id")
        metric = metric_rows.get(native_id)
        start = meta.get("request_start_ns")
        end = meta.get("request_end_ns")
        status = native.get("status")
        base.update({"aiperf_request_id": native_id, "actual_dispatch_ns": start,
                     "terminal_ns": end, "http_status": status,
                     "raw_record_line": raw_lines.get(planned_id)})
        if isinstance(start, int):
            starts.append(start)
        if isinstance(end, int):
            ends.append(end)
        credit = meta.get("credit_issued_ns")
        if isinstance(start, int) and isinstance(credit, int) and first_credit is not None:
            lag = (start - credit) / 1e6
            schedule_error = ((credit - first_credit) / 1e6 - row["timestamp"]
                              if not dependent else None)
            base["dispatch_lag_ms"] = lag
            base["fixed_schedule_error_ms"] = schedule_error
            lags.append(lag)
            if schedule_error is not None:
                schedule_errors.append(schedule_error)
        if meta.get("was_cancelled"):
            base["terminal_state"] = "canceled"
            base["error"] = "AIPerf marked request canceled"
            counts["canceled"] += 1
            reasons.add("unexpected_cancellation")
            records.append(base)
            continue
        if not isinstance(end, int):
            base["terminal_state"] = "censored"
            base["error"] = "No terminal timestamp in AIPerf raw record"
            counts["censored"] += 1
            reasons.add("timeout_censoring")
            records.append(base)
            continue
        if status != 200:
            timeout = status in (408, 504) or "timeout" in str(native.get("error", "")).lower()
            base["terminal_state"] = "timed_out" if timeout else "failed"
            base["error"] = str(native.get("error") or f"HTTP {status}")
            counts["timed_out" if timeout else "failed"] += 1
            reasons.add("timeout_censoring" if timeout else "invalid_response")
            records.append(base)
            continue
        if metric is None:
            base["terminal_state"] = "failed"
            base["error"] = "Missing per-request AIPerf metric export"
            counts["failed"] += 1
            reasons.add("request_accounting")
            records.append(base)
            continue
        ttft = _metric(metric, "time_to_first_token")
        tpot = _metric(metric, "inter_token_latency")
        latency = _metric(metric, "request_latency")
        prompt = _metric(metric, "usage_prompt_tokens")
        completion = _metric(metric, "usage_completion_tokens")
        reasoning = _metric(metric, "usage_reasoning_tokens")
        base.update({"ttft_ms": ttft, "tpot_ms": tpot, "input_tokens": prompt,
                     "completion_tokens": completion, "reasoning_tokens": reasoning})
        if isinstance(start, int) and ttft is not None:
            base["first_relevant_token_ns"] = start + round(ttft * 1e6)
        payload = native.get("payload", {})
        if dependent:
            output_cap = (row.get("output_tokens") or 0) + (row.get("reasoning_output_tokens") or 0)
            roles = [message.get("role") for message in payload.get("messages", [])]
            payload_ok = (payload.get("max_completion_tokens") == output_cap
                          and roles and roles[0] == "user"
                          and meta.get("turn_index") == row["round_index"])
            output_ok = isinstance(completion, (int, float)) and 0 < completion <= output_cap
        else:
            output_cap = row["output_length"]
            expected_extra = row.get("extra", {})
            payload_ok = (payload.get("messages") == [{"role": "user", "content": row["text"]}]
                          and payload.get("max_completion_tokens") == output_cap
                          and all(payload.get(key) == value for key, value in expected_extra.items()))
            output_ok = completion == output_cap
        valid_numbers = all(value is not None for value in (ttft, latency, prompt, completion))
        if not payload_ok:
            reasons.add("input_mismatch")
        if not valid_numbers:
            reasons.add("missing_required_metric")
        if not output_ok:
            reasons.add("wrong_output_length")
        if valid_numbers and completion > 1:
            if tpot is None or abs(tpot - (latency - ttft) / (completion - 1)) > 1e-4:
                reasons.add("token_counting_mismatch")
        if not payload_ok or not valid_numbers or not output_ok:
            base["terminal_state"] = "failed"
            base["error"] = "Invalid payload, missing metric, or wrong output length"
            counts["failed"] += 1
        else:
            base["terminal_state"] = "completed"
            counts["completed"] += 1
            counts["successful_completion_tokens"] += int(completion)
            ttfts.append(float(ttft))
            if tpot is not None and completion > 1:
                tpots.append(float(tpot))
                counts["tpot_eligible"] += 1
            if not dependent and first_credit is not None and isinstance(start, int):
                scheduled_ttfts.append(ttft + (start - first_credit) / 1e6 - row["timestamp"])
        records.append(base)
    if len(metric_rows) != counts["dispatched"]:
        reasons.add("request_accounting")
    if (lags and max(lags) > max_schedule_lag_ms) or (schedule_errors and max(abs(value) for value in schedule_errors) > max_schedule_lag_ms):
        reasons.add("client_lag")
    elapsed = (max(ends) - first_start) / 1e9 if ends and first_start is not None else None
    dispatch_duration = (max(starts) - first_start) / 1e9 if starts and first_start is not None else 0.0
    drain = max(0.0, elapsed - dispatch_duration) if elapsed is not None else 0.0
    metrics = {"output_tokens_per_s": counts["successful_completion_tokens"] / elapsed if elapsed else None,
               "ttft_p50_ms": _percentile(ttfts, .5), "ttft_p90_ms": _percentile(ttfts, .9),
               "ttft_p99_ms": _percentile(ttfts, .99),
               "tpot_p50_ms": _percentile(tpots, .5), "tpot_p90_ms": _percentile(tpots, .9),
               "tpot_p99_ms": _percentile(tpots, .99),
               "scheduled_ttft_p99_ms": _percentile(scheduled_ttfts, .99),
               "dispatch_lag_p99_ms": _percentile(lags, .99)}
    gauges = _server_gauges(artifact_dir / "server_metrics_export.csv")
    if any(reason in reasons for reason in ("invalid_response", "wrong_output_length", "input_mismatch", "unexpected_cancellation")):
        status = "functional_failed"
    elif reasons:
        status = "measurement_failed" if counts["dispatched"] == counts["planned"] else "incomplete"
    else:
        status = "valid"
    normalized_path = output_dir / "normalized-requests.jsonl"
    with normalized_path.open("w") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    artifact_hashes = {name: sha256_file(path) for name, path in (
        ("raw", raw_path), ("metrics", metrics_path), ("summary", summary_path)) if path.is_file()}
    cell_id = f"{run_id}:{manifest['scenario_id']}:{replicate}"
    result = CellResult(
        cell_id=cell_id, scenario_id=manifest["scenario_id"], config_id=config_id,
        status=status, behavior="unknown", evidence_grade="provisional" if status == "valid" else "ineligible",
        counts=counts, metrics=metrics,
        artifacts={"raw_requests": str(normalized_path), "aiperf_export": str(summary_path),
                   "raw_native": str(raw_path), "metrics_native": str(metrics_path)},
        diagnostics={"windows": {"dispatch_duration_s": dispatch_duration,
                                  "drain_duration_s": drain, "effective_duration_s": elapsed},
                     "server_gauges": gauges, "artifact_sha256": artifact_hashes,
                     "token_counting_mode": "server_usage_completion_includes_reasoning_once",
                     "planned_schedule_sha256": manifest["schedule_sha256"],
                     "max_absolute_schedule_error_ms": max((abs(x) for x in schedule_errors), default=None)},
        reason_codes=sorted(reasons),
    )
    class_summary_path = output_dir / "workload-class-summaries.json"
    class_summary_path.write_text(json.dumps({manifest["workload_name"]: {
        "counts": counts, "ttft_p50_ms": metrics["ttft_p50_ms"],
        "ttft_p90_ms": metrics["ttft_p90_ms"],
        "ttft_p99_ms": metrics["ttft_p99_ms"], "tpot_p50_ms": metrics["tpot_p50_ms"],
        "tpot_p90_ms": metrics["tpot_p90_ms"],
        "tpot_p99_ms": metrics["tpot_p99_ms"]}}, indent=2, sort_keys=True) + "\n")
    if stage == "triage":
        # Triage is an internal fast gate; the frozen v0.2 wire schema admits
        # pilot/screen/expanded/confirm only. Keep a clearly native result.
        (output_dir / "triage-native-result.json").write_text(
            json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    else:
        wire = _wire_cell_result(result, manifest=manifest, run_id=run_id, stage=stage,
                                 replicate=replicate, artifact_dir=artifact_dir,
                                 class_summary_path=class_summary_path)
        (output_dir / "cell-result.json").write_text(json.dumps(wire, indent=2, sort_keys=True) + "\n")
    return result


def _wire_cell_result(result: CellResult, *, manifest: dict[str, Any], run_id: str,
                      stage: str, replicate: int, artifact_dir: Path,
                      class_summary_path: Path) -> dict[str, Any]:
    gauges = result.diagnostics["server_gauges"]
    evidence = []
    for observation, value, unit in (
        ("queue_max", gauges["queue_max"], "requests"),
        ("kv_cache_usage_max", gauges["kv_cache_usage_max"], "fraction"),
        ("prefix_cache_hits", gauges["prefix_cache_hits"], "tokens"),
        ("prefix_cache_queries", gauges["prefix_cache_queries"], "tokens"),
        ("mtp_acceptance_fraction", gauges["mtp_acceptance_fraction"], "fraction"),
    ):
        evidence.append({"observation": observation, "value": value, "unit": unit,
                         "availability": "measured" if value is not None else "not_collected",
                         "reason": None if value is not None else "Counter absent from AIPerf server metrics export",
                         "artifact_id": str(artifact_dir / "server_metrics_export.csv") if value is not None else None})
    return {
        "schema_version": "0.2", "example_only": False, "backend": "real",
        "run_id": run_id, "configuration_id": result.config_id,
        "scenario_id": result.scenario_id, "workload_group_id": manifest["workload_group_id"],
        "protocol_id": manifest["protocol_id"], "stage": stage, "replicate": replicate,
        "status": result.status, "behavior": result.behavior,
        "evidence_grade": result.evidence_grade, "reason_codes": result.reason_codes,
        "metrics": result.metrics, "counts": result.counts,
        "windows": {key: value if value is not None else 0.0
                    for key, value in result.diagnostics["windows"].items()},
        "diagnostics": {"achieved_cache_hit_fraction": gauges["achieved_cache_hit_fraction"],
                        "graph_fallback": None,
                        "mtp_acceptance_fraction": gauges["mtp_acceptance_fraction"],
                        "sustainable": None,
                        "token_counting_mode": result.diagnostics["token_counting_mode"]},
        "artifacts": {"raw_requests": result.artifacts["raw_requests"],
                      "server_log": str(artifact_dir / "server.log") if (artifact_dir / "server.log").exists() else "",
                      "aiperf_export": result.artifacts["aiperf_export"],
                      "telemetry": str(artifact_dir / "server_metrics_export.csv") if (artifact_dir / "server_metrics_export.csv").exists() else "",
                      "workload_class_summaries": str(class_summary_path),
                      "realized_stream": result.artifacts["raw_requests"]},
        "notes": "Single diagnostic cell. p99 is an observed sample quantile; sustainable capacity and production representativeness are unconfirmed. Empty artifact paths mean unavailable.",
        "mechanism_evidence": evidence,
    }


class AIPerfAdapter:
    """Run a validated frozen scenario with native AIPerf profile."""

    PINNED_TOKENIZER_SHA256 = "0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3"

    def __init__(self, *, aiperf_executable: Path | None = None,
                 tokenizer_path: Path | None = None,
                 tokenizer_cache_dir: Path | None = None):
        self.aiperf_executable = Path(aiperf_executable or os.environ.get("IAR_AIPERF")
                                      or shutil.which("aiperf") or ".venv/bin/aiperf")
        self.tokenizer_path = Path(tokenizer_path or os.environ.get("IAR_TOKENIZER_PATH")
                                   or ".artifacts/models/Qwen3.8-27B")
        self.tokenizer_cache_dir = Path(tokenizer_cache_dir or os.environ.get("IAR_TOKENIZER_CACHE")
                                        or self.tokenizer_path.resolve().parents[1] / "aiperf-hf-cache")

    def _verify_tokenizer(self, manifest: dict[str, Any]) -> None:
        if not (self.tokenizer_path / "tokenizer.json").is_file():
            raise WorkloadError(f"Pinned tokenizer unavailable: {self.tokenizer_path}")
        if sha256_file(self.tokenizer_path / "tokenizer.json") != self.PINNED_TOKENIZER_SHA256:
            raise WorkloadError("Pinned tokenizer.json SHA256 mismatch")
        if manifest.get("model_id") != "Qwen/Qwen3.8-27B" or manifest.get("tokenizer_revision") != "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0":
            raise WorkloadError("Adapter tokenizer model/revision differs from pinned Qwen campaign")
        config_path = self.tokenizer_path / "tokenizer_config.json"
        if not config_path.is_file():
            raise WorkloadError("Pinned tokenizer_config.json unavailable")
        try:
            template = json.loads(config_path.read_text())["chat_template"]
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise WorkloadError("Cannot verify pinned chat template") from exc
        digest = hashlib.sha256(template.encode()).hexdigest()
        if digest != manifest["template_hash"]:
            raise WorkloadError("Chat template differs from frozen scenario pin")

    def _snapshot_path(self, manifest: dict[str, Any]) -> Path:
        repo_key = manifest["model_id"].replace("/", "--")
        return self.tokenizer_cache_dir / f"models--{repo_key}" / "snapshots" / manifest["tokenizer_revision"]

    def _ensure_offline_snapshot(self, manifest: dict[str, Any]) -> Path:
        """Bind the HF offline cache key to exactly the verified local model."""
        self._verify_tokenizer(manifest)
        model_dir = self.tokenizer_path.resolve()
        snapshot = self._snapshot_path(manifest)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        if snapshot.is_symlink():
            if snapshot.resolve() != model_dir:
                raise WorkloadError(f"Pinned tokenizer cache points to another model: {snapshot}")
        elif snapshot.exists():
            raise WorkloadError(f"Pinned tokenizer cache snapshot is not a symlink: {snapshot}")
        else:
            snapshot.symlink_to(model_dir, target_is_directory=True)
        if sha256_file(snapshot / "tokenizer.json") != self.PINNED_TOKENIZER_SHA256:
            raise WorkloadError("Offline snapshot tokenizer hash differs from local pin")
        return snapshot

    def _offline_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HF_HUB_CACHE"] = str(self.tokenizer_cache_dir.resolve())
        env["HF_HUB_OFFLINE"] = "1"
        env["TRANSFORMERS_OFFLINE"] = "1"
        return env

    def preflight_tokenizer(self, scenario: ScenarioManifest) -> dict[str, Any]:
        """Load through AIPerf 0.13 itself, offline, before acquiring a GPU."""
        manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
        verify_scenario(manifest, root=_scenario_root(scenario), require_validated=False)
        if not self.aiperf_executable.is_file() or not os.access(self.aiperf_executable, os.X_OK):
            raise WorkloadError(f"AIPerf executable unavailable: {self.aiperf_executable}")
        snapshot = self._ensure_offline_snapshot(manifest)
        with self.aiperf_executable.open() as entrypoint:
            shebang = entrypoint.readline().strip()
        if not shebang.startswith("#!/"):
            raise WorkloadError("AIPerf executable has no absolute Python interpreter shebang")
        interpreter = Path(shebang[2:].split()[0])
        if not interpreter.is_file():
            raise WorkloadError(f"AIPerf interpreter unavailable: {interpreter}")
        code = (
            "import importlib.metadata,json,sys; "
            "from aiperf.common.tokenizer import Tokenizer; "
            "version=importlib.metadata.version('aiperf'); "
            "assert version=='0.13.0',f'Unsupported AIPerf {version}'; "
            "Tokenizer.from_pretrained(sys.argv[1],revision=sys.argv[2]); "
            "print(json.dumps({'aiperf_version':version,'loaded':True}))"
        )
        completed = subprocess.run([str(interpreter), "-c", code, manifest["model_id"],
                                    manifest["tokenizer_revision"]],
                                   env=self._offline_env(), capture_output=True, text=True,
                                   timeout=45, check=False)
        if completed.returncode != 0:
            raise WorkloadError(f"AIPerf offline tokenizer preflight failed: {completed.stderr[-1500:]}")
        loaded = json.loads(completed.stdout.strip().splitlines()[-1])
        return {"status": "verified", "model_id": manifest["model_id"],
                "revision": manifest["tokenizer_revision"], "template_hash": manifest["template_hash"],
                "tokenizer_sha256": self.PINNED_TOKENIZER_SHA256,
                "snapshot": str(snapshot), "snapshot_resolves_to": str(self.tokenizer_path.resolve()),
                "aiperf_version": loaded["aiperf_version"], "loaded": loaded["loaded"],
                "network_mode": "offline"}

    def build_argv(self, server: ServerHandle, scenario: ScenarioManifest,
                   policy: MeasurementPolicy, output_dir: Path) -> list[str]:
        if not self.aiperf_executable.is_file() or not os.access(self.aiperf_executable, os.X_OK):
            raise WorkloadError(f"AIPerf executable unavailable: {self.aiperf_executable}")
        manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
        self._ensure_offline_snapshot(manifest)
        checked = verify_scenario(manifest, root=_scenario_root(scenario),
                                  require_validated=(policy.stage != "pilot"))
        if policy.cache_protocol != manifest["cache_protocol"]:
            raise WorkloadError("Measurement cache protocol differs from frozen scenario")
        parsed = urlparse(server.base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
            raise WorkloadError("Server base_url must be a bare HTTP origin")
        benchmark_duration = float(policy.metadata.get("benchmark_duration_s", 70))
        grace = float(policy.metadata.get("benchmark_grace_period_s", 60))
        if not math.isfinite(benchmark_duration) or not math.isfinite(grace) or benchmark_duration <= 0 or grace < 0:
            raise WorkloadError("Invalid benchmark duration/grace")
        schedule_duration = checked["schedule_duration_s"]
        if schedule_duration is not None and benchmark_duration < schedule_duration + 5:
            raise WorkloadError("Benchmark duration would truncate the frozen schedule")
        if policy.deadline_s < benchmark_duration + grace + 10:
            raise WorkloadError("Process deadline would truncate the benchmark or grace period")
        loader = "tracelab" if manifest["traffic_mode"] == "dependent_sessions" else "single-turn"
        argv = [str(self.aiperf_executable), "profile",
                "--model", manifest["model_id"], "--endpoint-type", "chat",
                "--endpoint", "/v1/chat/completions", "--streaming",
                "--url", parsed.netloc, "--tokenizer", manifest["model_id"],
                "--tokenizer-revision", manifest["tokenizer_revision"],
                "--apply-chat-template", "--use-server-token-count", "--per-chunk-usage",
                "--export-level", "raw", "--export-http-trace",
                "--benchmark-duration", str(benchmark_duration),
                "--benchmark-grace-period", str(grace),
                "--custom-dataset-type", loader, "--input-file", str(checked["payload_path"]),
                "--fixed-schedule", "--fixed-schedule-auto-offset",
                "--request-count", str(manifest["n_planned"]), "--random-seed", "42",
                "--output-artifact-dir", str(output_dir)]
        if loader == "tracelab":
            argv.extend(["--extra-inputs", json.dumps({"chat_template_kwargs": {"enable_thinking": False},
                                                          "temperature": 0}, separators=(",", ":"))])
        return argv

    def prepare(self, server: ServerHandle, scenario: ScenarioManifest,
                output_dir: Path, *, timeout_s: float = 120) -> dict[str, Any]:
        """Run the frozen disjoint warmup and issue a machine-checkable receipt."""
        output_dir = Path(output_dir)
        if output_dir.exists() and any(output_dir.iterdir()):
            raise WorkloadError(f"Refusing to overwrite preparation artifacts: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
        checked = verify_scenario(manifest, root=_scenario_root(scenario), require_validated=False)
        prep = json.loads(checked["preparation_path"].read_text())
        warm = prep.get("warmup", {})
        if prep.get("cache_protocol") != "cold_stream" or warm.get("kind") != "disjoint_native_synthetic":
            raise WorkloadError("Unsupported or missing frozen preparation policy")
        if not self.aiperf_executable.is_file() or not os.access(self.aiperf_executable, os.X_OK):
            raise WorkloadError(f"AIPerf executable unavailable: {self.aiperf_executable}")
        self._ensure_offline_snapshot(manifest)
        parsed = urlparse(server.base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
            raise WorkloadError("Server base_url must be a bare HTTP origin")
        count = int(warm["request_count"])
        output_tokens = int(warm["output_tokens"])
        argv = [str(self.aiperf_executable), "profile", "--model", manifest["model_id"],
                "--endpoint-type", "chat", "--endpoint", "/v1/chat/completions",
                "--streaming", "--url", parsed.netloc, "--tokenizer", manifest["model_id"],
                "--tokenizer-revision", manifest["tokenizer_revision"],
                "--apply-chat-template", "--use-server-token-count", "--per-chunk-usage",
                "--export-level", "raw", "--export-http-trace",
                "--benchmark-duration", "70", "--benchmark-grace-period", "60",
                "--prompt-input-tokens-mean", str(warm["input_tokens_target"]),
                "--prompt-input-tokens-stddev", "0", "--prompt-output-tokens-mean", str(output_tokens),
                "--prompt-output-tokens-stddev", "0",
                "--extra-inputs", json.dumps({"chat_template_kwargs": {"enable_thinking": False},
                                              "temperature": 0, "ignore_eos": True,
                                              "min_tokens": output_tokens}, separators=(",", ":")),
                "--request-rate", "0.2", "--request-rate-mode", "constant",
                "--concurrency", "256", "--request-count", str(count),
                "--random-seed", str(warm["seed"]), "--output-artifact-dir", str(output_dir)]
        (output_dir / "aiperf-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        env = self._offline_env()
        with (output_dir / "aiperf-console.log").open("w") as console:
            completed = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                       timeout=timeout_s, env=env, check=False)
        raw = _jsonl(output_dir / "profile_export_raw.jsonl")
        summary_path = output_dir / "profile_export_aiperf.json"
        summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}
        if completed.returncode != 0 or len(raw) != count or any(r.get("status") != 200 for r in raw) or summary.get("is_complete") is not True:
            raise WorkloadError("Frozen disjoint warmup failed; inspect preparation artifacts")
        receipt = {"version": "preparation-receipt-v1", "server_id": server.server_id,
                   "config_id": server.config_id, "scenario_id": scenario.scenario_id,
                   "cache_protocol": manifest["cache_protocol"], "request_count": count,
                   "raw_sha256": sha256_file(output_dir / "profile_export_raw.jsonl"),
                   "preparation_policy_sha256": sha256_file(checked["preparation_path"])}
        (output_dir / "preparation-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return receipt

    def run_cell(self, server: ServerHandle, scenario: ScenarioManifest,
                 policy: MeasurementPolicy, output_dir: Path) -> CellResult:
        receipt_path = policy.metadata.get("preparation_receipt")
        if not receipt_path:
            raise WorkloadError("A validated preparation receipt is required before measurement")
        receipt = json.loads(Path(receipt_path).read_text())
        manifest = scenario.metadata.get("manifest") or json.loads(Path(scenario.path).read_text())
        checked = verify_scenario(manifest, root=_scenario_root(scenario),
                                  require_validated=(policy.stage != "pilot"))
        if (receipt.get("version") != "preparation-receipt-v1"
                or receipt.get("server_id") != server.server_id
                or receipt.get("config_id") != server.config_id
                or receipt.get("scenario_id") != scenario.scenario_id
                or receipt.get("cache_protocol") != manifest["cache_protocol"]
                or receipt.get("preparation_policy_sha256") != sha256_file(checked["preparation_path"])):
            raise WorkloadError("Preparation receipt does not match this server/scenario/policy")
        output_dir = Path(output_dir)
        if output_dir.exists() and any(output_dir.iterdir()):
            raise WorkloadError(f"Refusing to overwrite cell artifacts: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        argv = self.build_argv(server, scenario, policy, output_dir)
        (output_dir / "aiperf-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        env = self._offline_env()
        with (output_dir / "aiperf-console.log").open("w") as console:
            try:
                completed = subprocess.run(argv, stdout=console, stderr=subprocess.STDOUT,
                                           timeout=policy.deadline_s, env=env, check=False)
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                exit_code = -1
        (output_dir / "aiperf-exit.json").write_text(json.dumps({"exit_code": exit_code}) + "\n")
        result = normalize_exports(
            scenario, output_dir, config_id=server.config_id,
            run_id=str(policy.metadata.get("run_id", "run")), stage=policy.stage,
            replicate=policy.replicate, output_dir=output_dir,
            max_schedule_lag_ms=float(policy.metadata.get("max_schedule_lag_ms", 20)))
        if exit_code != 0 and result.status == "valid":
            result = CellResult(**{**asdict(result), "status": "measurement_failed",
                                   "evidence_grade": "ineligible",
                                   "reason_codes": sorted(set(result.reason_codes + ["aiperf_process_failure"]))})
            (output_dir / "cell-result.json").write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
        return result

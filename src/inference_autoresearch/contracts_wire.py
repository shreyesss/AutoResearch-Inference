"""Explicit v0.2 CellResult wire export; internal DTO remains intentionally lean."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from inference_autoresearch.contracts import CellResult, MeasurementPolicy, ScenarioManifest


METRICS = ("output_tokens_per_s", "ttft_p50_ms", "ttft_p99_ms", "tpot_p50_ms",
           "tpot_p99_ms", "scheduled_ttft_p99_ms", "dispatch_lag_p99_ms")
COUNTS = ("planned", "dispatched", "not_dispatched", "completed", "failed", "timed_out",
          "canceled", "censored", "tpot_eligible", "successful_completion_tokens")
WINDOWS = ("dispatch_duration_s", "drain_duration_s", "effective_duration_s")


def _mechanism(observation: str, value: Any, unit: str | None, artifact: str | None) -> dict[str, Any]:
    measured = isinstance(value, (int, float)) and math.isfinite(value)
    return {"observation": observation, "value": value if measured else None,
            "unit": unit, "availability": "measured" if measured else "not_collected",
            "reason": None if measured else "Counter not present in this cell export",
            "artifact_id": artifact if measured else None}


def cell_result_wire(cell: CellResult, scenario: ScenarioManifest, policy: MeasurementPolicy,
                     server_artifact_dir: Path, *, backend: str = "real") -> dict[str, Any]:
    """Map measured cell fields to the handoff schema without inventing missing counters."""
    if cell.scenario_id != scenario.scenario_id:
        raise ValueError("cell/scenario identity mismatch")
    if backend not in ("real", "mock"):
        raise ValueError("backend must be real or mock")
    windows = cell.diagnostics.get("windows", {})
    if any(not isinstance(windows.get(k), (int, float)) or not math.isfinite(windows[k])
           or windows[k] < 0 for k in WINDOWS):
        raise ValueError("cell lacks measured nonnegative time windows")
    if any(k not in cell.counts for k in COUNTS):
        raise ValueError("cell lacks complete request accounting")
    gauges = cell.diagnostics.get("server_gauges", {})
    server_artifact_dir = Path(server_artifact_dir)
    telemetry = server_artifact_dir / "telemetry.jsonl"
    server_log = server_artifact_dir / "startup.log"
    metric_artifact = str(telemetry) if telemetry.is_file() else None
    raw_requests = cell.artifacts.get("raw_requests", "not_collected")
    data = {
        "schema_version": "0.2", "example_only": backend == "mock", "backend": backend,
        "run_id": str(policy.metadata.get("run_id", cell.cell_id.split(":")[0])),
        "configuration_id": cell.config_id, "scenario_id": cell.scenario_id,
        "workload_group_id": scenario.group_id,
        "protocol_id": str(policy.metadata.get("protocol_id", "unknown")),
        "stage": policy.stage, "replicate": policy.replicate,
        "status": cell.status, "behavior": cell.behavior,
        "evidence_grade": cell.evidence_grade, "reason_codes": list(cell.reason_codes),
        "metrics": {key: cell.metrics.get(key) for key in METRICS},
        "counts": {key: cell.counts[key] for key in COUNTS},
        "windows": {key: windows[key] for key in WINDOWS},
        "diagnostics": {
            "achieved_cache_hit_fraction": None,
            "graph_fallback": None,
            "mtp_acceptance_fraction": gauges.get("mtp_acceptance_fraction"),
            "sustainable": None,
            "token_counting_mode": str(cell.diagnostics.get("token_counting_mode", "unknown")),
        },
        "artifacts": {
            "raw_requests": raw_requests,
            "server_log": str(server_log) if server_log.is_file() else "not_collected",
            "aiperf_export": cell.artifacts.get("aiperf_export", "not_collected"),
            "telemetry": str(telemetry) if telemetry.is_file() else "not_collected",
            "workload_class_summaries": cell.artifacts.get("workload_class_summaries", "not_collected"),
            "realized_stream": cell.artifacts.get("realized_stream", raw_requests),
        },
        "notes": "Single-cell provisional measurement. Null counters were not established; see raw artifacts.",
        "mechanism_evidence": [
            _mechanism("queue_max", gauges.get("queue_max"), "requests", metric_artifact),
            _mechanism("kv_cache_usage_max", gauges.get("kv_cache_usage_max"), "fraction", metric_artifact),
            _mechanism("prefix_cache_hits", gauges.get("prefix_cache_hits"), "requests", metric_artifact),
            _mechanism("mtp_acceptance_fraction", gauges.get("mtp_acceptance_fraction"), "fraction", metric_artifact),
        ],
    }
    return data


def export_cell_result(cell: CellResult, scenario: ScenarioManifest, policy: MeasurementPolicy,
                       server_artifact_dir: Path, output_path: Path,
                       schema_path: Path | None = None, *, backend: str = "real") -> Path:
    if schema_path is None:
        root = Path(os.environ.get("IAR_REPO_ROOT", Path.cwd()))
        schema_path = root / "inference-autoresearch-handoff/contracts/cell-result.schema.json"
    schema = json.loads(Path(schema_path).read_text())
    data = cell_result_wire(cell, scenario, policy, server_artifact_dir, backend=backend)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        raise ValueError(f"CellResult v0.2 wire validation failed: {errors[0].message}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(output_path)
    return output_path

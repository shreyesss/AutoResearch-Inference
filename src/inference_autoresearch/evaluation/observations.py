"""State exactly which proposer-requested diagnostics a measured cell supplies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def observation_receipt(requested: list[str], resolved: dict[str, Any],
                        cell_dir: Path) -> dict[str, Any]:
    """Describe existing evidence; never imply that an extra profile ran."""
    result_path = cell_dir / "cell-result.json"
    cell = json.loads(result_path.read_text()) if result_path.is_file() else {}
    gauges = cell.get("diagnostics", {}).get("server_gauges", {})
    metrics_path = cell_dir / "aiperf/server_metrics_export.csv"
    log_path = cell_dir / "server/server.log"
    observations: dict[str, dict[str, Any]] = {}
    for name in requested:
        if name == "resolved_config":
            observations[name] = {"status": "available", "path": "../resolved-config.json",
                                  "effective_settings": resolved.get("effective_settings", {})}
        elif name == "queue_batch_summary":
            observations[name] = {"status": "partial", "queue_max": gauges.get("queue_max"),
                                  "raw_server_metrics": "aiperf/server_metrics_export.csv" if metrics_path.is_file() else None,
                                  "limitation": "No structured per-step batch composition is exported."}
        elif name == "token_budget_summary":
            observations[name] = {"status": "partial",
                                  "max_num_batched_tokens": resolved.get("effective_settings", {}).get("max_num_batched_tokens"),
                                  "raw_server_metrics": "aiperf/server_metrics_export.csv" if metrics_path.is_file() else None,
                                  "limitation": "Actual per-request prefill chunk sizes are not exported; the iteration-token histogram is not a chunk trace."}
        elif name == "cache_memory_summary":
            observations[name] = {"status": "available" if gauges else "unavailable",
                                  "kv_cache_usage_max": gauges.get("kv_cache_usage_max"),
                                  "achieved_cache_hit_fraction": gauges.get("achieved_cache_hit_fraction"),
                                  "raw_server_metrics": "aiperf/server_metrics_export.csv" if metrics_path.is_file() else None}
        elif name == "speculation_summary":
            observations[name] = {"status": "not_applicable" if resolved.get("effective_settings", {}).get("mtp_draft_tokens") == 0 else "partial",
                                  "mtp_accepted_tokens": gauges.get("mtp_accepted_tokens"),
                                  "mtp_draft_tokens": gauges.get("mtp_draft_tokens"),
                                  "mtp_acceptance_fraction": gauges.get("mtp_acceptance_fraction")}
        elif name == "graph_summary":
            observations[name] = {"status": "raw_log_only" if log_path.is_file() else "unavailable",
                                  "raw_server_log": "server/server.log" if log_path.is_file() else None,
                                  "limitation": "No structured graph-coverage or compilation-event summary is exported."}
        elif name == "targeted_profile":
            observations[name] = {"status": "not_executed",
                                  "limitation": "The controller does not run an extra GPU profile for this request."}
        else:
            observations[name] = {"status": "unsupported"}
    return {"schema_version": "observation-receipt-v1", "requested": requested,
            "observations": observations, "extra_gpu_traffic_executed": False}

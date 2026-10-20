#!/usr/bin/env python3
"""Normalize AIPerf artifacts into a stable manual-comparison score."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

METRIC_ALIASES = {
    "ttft": ("time_to_first_token", "ttft"),
    "itl": ("inter_token_latency", "time_per_output_token", "tpot"),
    "request_latency": ("request_latency", "e2e_latency"),
    "request_throughput": ("request_throughput",),
    "output_token_throughput": ("output_token_throughput",),
    "goodput": ("goodput",),
    "good_request_fraction": ("good_request_fraction",),
    "request_count": ("request_count",),
    "error_count": ("error_request_count", "request_error_count"),
    "replay_lag": ("replay_sched_lag", "replay_schedule_lag"),
    "replay_degraded": ("replay_sched_degraded",),
    "cache_hit_share": (
        "kv_cache_hit_rate",
        "prefix_cache_hit_rate",
        "input_token_cache_hit_rate",
    ),
    "input_sequence_length": ("input_sequence_length",),
    "context_overflow_count": ("context_overflow_count",),
}


class AnalysisError(RuntimeError):
    """Raised when AIPerf artifacts cannot support a valid score."""


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AnalysisError(f"{path} must contain a mapping")
    return value


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def metrics_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    metrics = payload.get("metrics")
    return metrics if isinstance(metrics, Mapping) else payload


def metric_item(
    metrics: Mapping[str, Any], aliases: Sequence[str]
) -> Mapping[str, Any] | None:
    for name in aliases:
        value = metrics.get(name)
        if isinstance(value, Mapping):
            return value
        for key, candidate in metrics.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized == name and isinstance(candidate, Mapping):
                return candidate
    return None


def metric_value(
    metrics: Mapping[str, Any],
    aliases: Sequence[str],
    statistic: str,
) -> float | None:
    for alias in aliases:
        flattened = metrics.get(f"{alias}_{statistic}")
        if isinstance(flattened, Mapping):
            for key in (statistic, "avg", "mean", "value"):
                value = finite(flattened.get(key))
                if value is not None:
                    return value
        value = finite(flattened)
        if value is not None:
            return value
    item = metric_item(metrics, aliases)
    if item is None:
        return None
    combined = item.get("combined")
    if isinstance(combined, Mapping):
        value = finite(combined.get(statistic))
        if value is not None:
            return value
    value = finite(item.get(statistic))
    if value is not None:
        return value
    if statistic == "avg":
        return finite(item.get("mean"))
    if statistic == "mean":
        return finite(item.get("avg"))
    return None


def find_export(artifact_root: Path) -> Path:
    aggregate = sorted(
        artifact_root.rglob("profile_export_aiperf_aggregate.json")
    )
    if aggregate:
        return aggregate[-1]
    exports = sorted(artifact_root.rglob("profile_export_aiperf.json"))
    if not exports:
        raise AnalysisError(f"no AIPerf profile export found under {artifact_root}")
    return exports[-1]


def slo_for(
    campaign: Mapping[str, Any], category: str
) -> dict[str, float]:
    base = dict((campaign.get("slo") or {}).get("default") or {})
    override = (campaign.get("slo") or {}).get(category) or {}
    base.update(override)
    return {key: float(value) for key, value in base.items()}


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def record_metric(record: Mapping[str, Any], name: str) -> Any:
    metrics = record.get("metrics")
    if not isinstance(metrics, Mapping):
        return None
    item = metrics.get(name)
    return item.get("value") if isinstance(item, Mapping) else None


def profiling_records(artifact_root: Path) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    for path in sorted(artifact_root.rglob("profile_export.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                metadata = record.get("metadata")
                if (
                    isinstance(metadata, Mapping)
                    and metadata.get("benchmark_phase") not in {None, "profiling"}
                ):
                    continue
                records.append(record)
    return records


def is_fixed_schedule(workload: Mapping[str, Any]) -> bool:
    dataset = workload.get("dataset") or {}
    timing = workload.get("timing") or {}
    return bool(
        dataset.get("kind") == "mooncake_trace"
        or timing.get("mode") == "fixed_schedule"
    )


def output_speed_sla_report(
    records: Sequence[Mapping[str, Any]],
    campaign: Mapping[str, Any],
    workload: Mapping[str, Any],
) -> dict[str, Any]:
    policy = campaign.get("output_speed_sla") or {}
    minimum_output_tokens = int(policy.get("minimum_output_tokens", 50))
    minimum_speed = float(policy.get("minimum_tokens_per_second", 30))
    minimum_attainment = float(policy.get("minimum_attainment_fraction", 0.95))
    category = str(workload.get("category") or "default")
    thresholds = slo_for(campaign, category)

    rows: list[dict[str, float | None]] = []
    for record in records:
        itl = finite(record_metric(record, "inter_token_latency"))
        rows.append(
            {
                "output_tokens": finite(
                    record_metric(record, "output_sequence_length")
                ),
                "itl_ms": itl,
                "speed": 1000.0 / itl if itl is not None and itl > 0 else None,
                "ttft_ms": finite(record_metric(record, "time_to_first_token")),
                "request_latency_ms": finite(
                    record_metric(record, "request_latency")
                ),
            }
        )

    tiers = policy.get("tiers") or {}

    def summarize(selected: Sequence[Mapping[str, float | None]]) -> dict[str, Any]:
        speeds = [
            value
            for row in selected
            if (value := finite(row.get("speed"))) is not None
        ]
        itls = [
            value
            for row in selected
            if (value := finite(row.get("itl_ms"))) is not None
        ]
        passing = sum(value >= minimum_speed for value in speeds)
        denominator = len(selected)
        p50_speed = percentile(speeds, 0.50)
        p10_speed = percentile(speeds, 0.10)
        highest_tier = None
        for name, requirements in tiers.items():
            required_p50 = float(requirements["p50_tokens_per_second"])
            required_p10 = float(requirements["p10_tokens_per_second"])
            if (
                p50_speed is not None
                and p10_speed is not None
                and p50_speed >= required_p50
                and p10_speed >= required_p10
            ):
                highest_tier = str(name)
        attainment = passing / denominator if denominator else None
        return {
            "requests": denominator,
            "measured_requests": len(speeds),
            "speed_p50_tokens_per_second": p50_speed,
            "speed_p10_tokens_per_second": p10_speed,
            "speed_attainment_fraction": attainment,
            "itl_p50_ms": percentile(itls, 0.50),
            "itl_p90_ms": percentile(itls, 0.90),
            "itl_p95_ms": percentile(itls, 0.95),
            "itl_p99_ms": percentile(itls, 0.99),
            "meets_minimum_speed_sla": bool(
                attainment is not None and attainment >= minimum_attainment
            ),
            "highest_output_speed_tier": highest_tier,
        }

    sufficiently_long = [
        row
        for row in rows
        if (
            (output_tokens := finite(row.get("output_tokens"))) is not None
            and output_tokens >= minimum_output_tokens
        )
    ]
    qualified = 0
    for row in rows:
        output_tokens = finite(row.get("output_tokens"))
        ttft = finite(row.get("ttft_ms"))
        latency = finite(row.get("request_latency_ms"))
        if (
            output_tokens is None
            or ttft is None
            or latency is None
            or ttft > thresholds["ttft_ms"]
            or latency > thresholds["request_latency_ms"]
        ):
            continue
        if output_tokens >= minimum_output_tokens:
            speed = finite(row.get("speed"))
            if speed is None or speed < minimum_speed:
                continue
        qualified += 1

    return {
        "minimum_output_tokens": minimum_output_tokens,
        "minimum_tokens_per_second": minimum_speed,
        "minimum_attainment_fraction": minimum_attainment,
        "whole_trace": summarize(rows),
        "sufficiently_long_outputs": summarize(sufficiently_long),
        "length_aware_good_request_fraction": (
            qualified / len(rows) if rows else None
        ),
    }


def cache_hit_report(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    prompt_tokens = 0.0
    cached_tokens = 0.0
    reported_requests = 0
    for record in records:
        prompt = finite(record_metric(record, "usage_prompt_tokens"))
        cached = finite(
            record_metric(record, "usage_prompt_cache_read_tokens")
        )
        if prompt is None or cached is None or prompt < 0 or cached < 0:
            continue
        reported_requests += 1
        prompt_tokens += prompt
        cached_tokens += cached
    requests = len(records)
    return {
        "requests": requests,
        "reported_requests": reported_requests,
        "reporting_coverage": (
            reported_requests / requests if requests else None
        ),
        "prompt_tokens": prompt_tokens,
        "cached_prompt_tokens": cached_tokens,
        "cache_hit_share": (
            cached_tokens / prompt_tokens if prompt_tokens > 0 else None
        ),
    }


def classify_record(
    record: Mapping[str, Any], workload: Mapping[str, Any]
) -> str:
    category = str(workload.get("category") or "default")
    pairs = (workload.get("dataset") or {}).get("pairs") or []
    if not pairs:
        return category
    input_tokens = finite(record_metric(record, "input_sequence_length"))
    output_tokens = finite(record_metric(record, "output_sequence_length"))
    if input_tokens is None or output_tokens is None:
        return "unknown"
    return str(
        min(
            pairs,
            key=lambda item: abs(
                math.log(max(input_tokens, 1) / max(float(item["input"]), 1))
            )
            + abs(
                math.log(max(output_tokens, 1) / max(float(item["output"]), 1))
            ),
        )["category"]
    )


def cohort_metrics(
    artifact_root: Path,
    workload: Mapping[str, Any],
    campaign: Mapping[str, Any],
    *,
    length_aware_output_speed: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    grouped: dict[str, dict[str, list[float]]] = {}
    for record in profiling_records(artifact_root):
        category = classify_record(record, workload)
        target = grouped.setdefault(
            category,
            {"ttft": [], "itl": [], "latency": [], "max_chunk_gap": []},
        )
        for source_name, target_name in (
            ("time_to_first_token", "ttft"),
            ("inter_token_latency", "itl"),
            ("request_latency", "latency"),
        ):
            value = finite(record_metric(record, source_name))
            if value is not None:
                target[target_name].append(value)
        chunks = record_metric(record, "inter_chunk_latency")
        if isinstance(chunks, list):
            finite_chunks = [
                value
                for item in chunks
                if (value := finite(item)) is not None
            ]
            if finite_chunks:
                target["max_chunk_gap"].append(max(finite_chunks))
    output: dict[str, Any] = {}
    failures: list[str] = []
    minimum_samples = int((campaign.get("hard_gates") or {}).get("minimum_requests", 1))
    for category, metrics in sorted(grouped.items()):
        count = len(metrics["ttft"])
        thresholds = slo_for(campaign, category)
        summary = {
            "requests": count,
            "ttft_p99_ms": percentile(metrics["ttft"], 0.99),
            "inter_token_latency_p99_ms": percentile(metrics["itl"], 0.99),
            "request_latency_p99_ms": percentile(metrics["latency"], 0.99),
            "maximum_stream_gap_p99_ms": percentile(
                metrics["max_chunk_gap"], 0.99
            ),
        }
        output[category] = summary
        if category == "unknown":
            failures.append("mixed workload contains unclassified records")
            continue
        if count < minimum_samples:
            failures.append(
                f"category {category}: requests {count} < {minimum_samples}"
            )
        for field, threshold_key in (
            ("ttft_p99_ms", "ttft_ms"),
            ("inter_token_latency_p99_ms", "inter_token_latency_ms"),
            ("request_latency_p99_ms", "request_latency_ms"),
        ):
            if length_aware_output_speed and field == "inter_token_latency_p99_ms":
                continue
            value = summary[field]
            if value is not None and value > thresholds[threshold_key]:
                failures.append(
                    f"category {category}: {field} {value:.3f} ms > "
                    f"{thresholds[threshold_key]:.3f} ms"
                )
    return output, failures


def analyze(
    *,
    export_path: Path,
    campaign: Mapping[str, Any],
    workload: Mapping[str, Any],
    candidate: str,
    phase: str,
    node_cost_per_hour: float,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AnalysisError(f"{export_path} must contain an object")
    metrics = metrics_payload(payload)
    category = str(workload.get("category") or "default")
    thresholds = slo_for(campaign, category)
    gates = campaign.get("hard_gates") or {}

    ttft = {
        stat: metric_value(metrics, METRIC_ALIASES["ttft"], stat)
        for stat in ("p50", "p90", "p95", "p99")
    }
    itl = {
        stat: metric_value(metrics, METRIC_ALIASES["itl"], stat)
        for stat in ("p50", "p90", "p95", "p99")
    }
    request_latency = {
        stat: metric_value(
            metrics, METRIC_ALIASES["request_latency"], stat
        )
        for stat in ("p50", "p90", "p95", "p99")
    }
    request_count = (
        metric_value(metrics, METRIC_ALIASES["request_count"], "avg")
        or metric_value(metrics, METRIC_ALIASES["request_count"], "value")
        or 0.0
    )
    error_count = (
        metric_value(metrics, METRIC_ALIASES["error_count"], "avg")
        or metric_value(metrics, METRIC_ALIASES["error_count"], "value")
        or 0.0
    )
    attempts = request_count + error_count
    completion_ratio = request_count / attempts if attempts else 0.0
    error_rate = error_count / attempts if attempts else 1.0
    good_fraction = metric_value(
        metrics, METRIC_ALIASES["good_request_fraction"], "avg"
    )
    goodput = metric_value(metrics, METRIC_ALIASES["goodput"], "avg")
    request_throughput = metric_value(
        metrics, METRIC_ALIASES["request_throughput"], "avg"
    )
    output_throughput = metric_value(
        metrics, METRIC_ALIASES["output_token_throughput"], "avg"
    )
    replay_lag_p99 = metric_value(
        metrics, METRIC_ALIASES["replay_lag"], "p99"
    )
    replay_degraded = metric_value(
        metrics, METRIC_ALIASES["replay_degraded"], "avg"
    )
    context_overflow = (
        metric_value(
            metrics, METRIC_ALIASES["context_overflow_count"], "avg"
        )
        or 0.0
    )
    metadata = payload.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    length_aware_output_speed = bool(
        (workload.get("dataset") or {}).get("kind") == "mooncake_trace"
    )
    records: list[Mapping[str, Any]] = []
    speed_report = None
    record_cache_report = None
    if artifact_root is not None:
        records = profiling_records(artifact_root)
        speed_report = output_speed_sla_report(records, campaign, workload)
        record_cache_report = cache_hit_report(records)
    aggregate_cache_hit_share = metric_value(
        metrics, METRIC_ALIASES["cache_hit_share"], "avg"
    )
    cache_hit_share = aggregate_cache_hit_share
    if cache_hit_share is None and record_cache_report is not None:
        cache_hit_share = finite(record_cache_report.get("cache_hit_share"))
    qualified_good_fraction = (
        finite(speed_report.get("length_aware_good_request_fraction"))
        if length_aware_output_speed and speed_report is not None
        else good_fraction
    )
    qualified_goodput = goodput
    if length_aware_output_speed:
        qualified_goodput = (
            request_throughput * qualified_good_fraction
            if request_throughput is not None
            and qualified_good_fraction is not None
            else None
        )

    failures: list[str] = []
    is_complete = payload.get("is_complete")
    if gates.get("require_complete_artifact", True) and is_complete is False:
        failures.append(
            f"incomplete artifact: {payload.get('incomplete_reason') or 'unknown'}"
        )
    if metadata.get("submission_valid") is False:
        failures.append(
            "AIPerf scenario invalid: "
            + ", ".join(
                map(str, metadata.get("submission_invalid_reasons") or [])
            )
        )
    if attempts < float(gates.get("minimum_requests", 1)):
        failures.append(
            f"requests {attempts:.0f} < {float(gates['minimum_requests']):.0f}"
        )
    if completion_ratio < float(gates.get("minimum_completion_ratio", 0)):
        failures.append(
            f"completion ratio {completion_ratio:.4f} below gate"
        )
    if error_rate > float(gates.get("maximum_error_rate", 1)):
        failures.append(f"error rate {error_rate:.4f} above gate")
    if (
        qualified_good_fraction is not None
        and qualified_good_fraction
        < float(gates.get("minimum_good_request_fraction", 0))
    ):
        failures.append(
            f"good request fraction {qualified_good_fraction:.4f} below gate"
        )
    if qualified_good_fraction is None:
        failures.append("good request fraction is unavailable")
    if qualified_goodput is None:
        failures.append("SLO goodput is unavailable")
    if length_aware_output_speed:
        if speed_report is None:
            failures.append("length-aware output speed metrics are unavailable")
        else:
            long_output = speed_report["sufficiently_long_outputs"]
            minimum_samples = int(gates.get("minimum_requests", 1))
            if int(long_output["requests"]) < minimum_samples:
                failures.append(
                    "sufficiently long output requests "
                    f"{long_output['requests']} < {minimum_samples}"
                )
            if not long_output["meets_minimum_speed_sla"]:
                attainment = finite(long_output["speed_attainment_fraction"])
                minimum = float(
                    speed_report["minimum_attainment_fraction"]
                )
                failures.append(
                    "long-output speed attainment "
                    f"{(attainment or 0):.4f} below {minimum:.4f}"
                )
    fixed_schedule = is_fixed_schedule(workload)
    if (
        fixed_schedule
        and gates.get("reject_replay_degraded", True)
        and replay_degraded is None
    ):
        failures.append("fixed-schedule replay degradation metric is unavailable")
    if (
        gates.get("reject_replay_degraded", True)
        and replay_degraded is not None
        and replay_degraded >= 0.5
    ):
        failures.append("fixed-schedule replay was degraded")
    maximum_lag = float(
        gates.get("maximum_replay_schedule_lag_p99_ms", math.inf)
    )
    if fixed_schedule and replay_lag_p99 is None:
        failures.append("replay schedule lag p99 is unavailable")
    if replay_lag_p99 is not None and replay_lag_p99 > maximum_lag:
        failures.append(
            f"replay schedule lag p99 {replay_lag_p99:.3f} ms > "
            f"{maximum_lag:.3f} ms"
        )
    if context_overflow > 0:
        failures.append(f"context overflow count {context_overflow:.0f}")
    input_sequence_length = metric_value(
        metrics, METRIC_ALIASES["input_sequence_length"], "avg"
    )
    if gates.get("require_server_token_usage", True) and input_sequence_length is None:
        failures.append("server token usage is unavailable")

    if ttft["p99"] is not None and ttft["p99"] > thresholds["ttft_ms"]:
        failures.append(
            f"TTFT p99 {ttft['p99']:.3f} ms > {thresholds['ttft_ms']:.3f} ms"
        )
    if (
        not length_aware_output_speed
        and itl["p99"] is not None
        and itl["p99"] > thresholds["inter_token_latency_ms"]
    ):
        failures.append(
            f"ITL p99 {itl['p99']:.3f} ms > "
            f"{thresholds['inter_token_latency_ms']:.3f} ms"
        )
    if (
        request_latency["p99"] is not None
        and request_latency["p99"] > thresholds["request_latency_ms"]
    ):
        failures.append(
            f"request latency p99 {request_latency['p99']:.3f} ms > "
            f"{thresholds['request_latency_ms']:.3f} ms"
        )

    cost_per_good_request = (
        node_cost_per_hour / (qualified_goodput * 3600)
        if qualified_goodput is not None and qualified_goodput > 0
        else None
    )
    cohorts: dict[str, Any] = {}
    if artifact_root is not None:
        cohorts, cohort_failures = cohort_metrics(
            artifact_root,
            workload,
            campaign,
            length_aware_output_speed=length_aware_output_speed,
        )
        failures.extend(cohort_failures)
    return {
        "schema_version": 1,
        "candidate": candidate,
        "suite": workload.get("suite"),
        "workload": workload.get("name"),
        "category": category,
        "phase": phase,
        "eligible": not failures,
        "hard_gate_failures": failures,
        "source_export": str(export_path),
        "thresholds": thresholds,
        "metrics": {
            "attempted_requests": attempts,
            "completion_ratio": completion_ratio,
            "error_rate": error_rate,
            "good_request_fraction": qualified_good_fraction,
            "slo_goodput_rps": qualified_goodput,
            "aiperf_good_request_fraction": good_fraction,
            "aiperf_slo_goodput_rps": goodput,
            "request_throughput_rps": request_throughput,
            "output_token_throughput": output_throughput,
            "ttft_ms": ttft,
            "inter_token_latency_ms": itl,
            "request_latency_ms": request_latency,
            "replay_schedule_lag_p99_ms": replay_lag_p99,
            "replay_degraded": replay_degraded,
            "context_overflow_count": context_overflow,
            "cache_hit_share": cache_hit_share,
            "cache_reporting": record_cache_report,
            "input_sequence_length_avg": input_sequence_length,
            "node_cost_per_hour": node_cost_per_hour,
            "cost_per_good_request": cost_per_good_request,
            "output_speed_sla": speed_report,
        },
        "metadata": dict(metadata),
        "cohorts": cohorts,
    }


def write_score(score: Mapping[str, Any], output: Path) -> None:
    output.write_text(
        json.dumps(score, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metrics = score["metrics"]
    speed_sla = metrics.get("output_speed_sla") or {}
    whole_speed = speed_sla.get("whole_trace") or {}
    long_speed = speed_sla.get("sufficiently_long_outputs") or {}
    row = {
        "candidate": score["candidate"],
        "suite": score["suite"],
        "workload": score["workload"],
        "phase": score["phase"],
        "eligible": score["eligible"],
        "failures": "; ".join(score["hard_gate_failures"]),
        "slo_goodput_rps": metrics.get("slo_goodput_rps"),
        "request_throughput_rps": metrics.get("request_throughput_rps"),
        "output_token_throughput": metrics.get("output_token_throughput"),
        "ttft_p99_ms": metrics["ttft_ms"].get("p99"),
        "itl_p99_ms": metrics["inter_token_latency_ms"].get("p99"),
        "request_latency_p99_ms": metrics["request_latency_ms"].get("p99"),
        "error_rate": metrics.get("error_rate"),
        "good_request_fraction": metrics.get("good_request_fraction"),
        "cache_hit_share": metrics.get("cache_hit_share"),
        "cache_reporting_coverage": (
            (metrics.get("cache_reporting") or {}).get("reporting_coverage")
        ),
        "whole_speed_p50_tps": whole_speed.get(
            "speed_p50_tokens_per_second"
        ),
        "whole_speed_p10_tps": whole_speed.get(
            "speed_p10_tokens_per_second"
        ),
        "whole_speed_tier": whole_speed.get("highest_output_speed_tier"),
        "long_output_speed_p50_tps": long_speed.get(
            "speed_p50_tokens_per_second"
        ),
        "long_output_speed_p10_tps": long_speed.get(
            "speed_p10_tokens_per_second"
        ),
        "long_output_speed_tier": long_speed.get(
            "highest_output_speed_tier"
        ),
        "replay_schedule_lag_p99_ms": metrics.get(
            "replay_schedule_lag_p99_ms"
        ),
        "cost_per_good_request": metrics.get("cost_per_good_request"),
    }
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--workload-config", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument(
        "--phase",
        choices=("discovery", "confirmation", "final"),
        required=True,
    )
    parser.add_argument("--node-cost-per-hour", type=float, default=36.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    campaign = load_yaml(args.campaign)
    workload = load_yaml(args.workload_config)
    export_path = find_export(args.artifact_root)
    score = analyze(
        export_path=export_path,
        campaign=campaign,
        workload=workload,
        candidate=args.candidate,
        phase=args.phase,
        node_cost_per_hour=args.node_cost_per_hour,
        artifact_root=args.artifact_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_score(score, args.output)
    print(json.dumps(score, indent=2, sort_keys=True))
    return 0 if score["eligible"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AnalysisError, OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"error: {exc}") from exc

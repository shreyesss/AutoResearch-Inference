#!/usr/bin/env python3
"""Collect immutable archive evidence and new latency-campaign analyses."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


COUNTER = re.compile(
    r"^vllm:prefix_cache_(hits|queries)_total\{[^}]*\}\s+([0-9.eE+-]+)"
)
PROM_VALUE = re.compile(
    r"^([A-Za-z_:][A-Za-z0-9_:]*)(?:\{[^}]*\})?\s+([0-9.eE+-]+)$"
)


class CollectionError(RuntimeError):
    """Raised when campaign metadata or result artifacts are malformed."""


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def read_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise CollectionError(f"{path} must contain a JSON object")
    return loaded


def read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise CollectionError(f"{path} must contain a YAML object")
    return loaded


def nested_metric(
    source: Mapping[str, Any],
    metric: str,
    percentile: str,
) -> float | None:
    value = source.get(metric)
    if not isinstance(value, Mapping):
        return None
    return finite(value.get(percentile))


def counter_totals(path: Path) -> dict[str, float]:
    totals = {"hits": 0.0, "queries": 0.0}
    if not path.is_file():
        return totals
    lines = path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()
    prefer_prefill = any(
        line.startswith("# source ") and ":8001/metrics" in line
        for line in lines
    )
    include = not prefer_prefill
    for line in lines:
        if line.startswith("# source "):
            include = not prefer_prefill or ":8001/metrics" in line
            continue
        if not include:
            continue
        match = COUNTER.match(line)
        if match:
            totals[match.group(1)] += float(match.group(2))
    return totals


def cache_share(path: Path) -> float | None:
    before = counter_totals(path / "metrics-before.txt")
    after = counter_totals(path / "metrics-after.txt")
    if not (path / "metrics-after.txt").is_file():
        return None
    queries = after["queries"] - before["queries"]
    return (after["hits"] - before["hits"]) / queries if queries > 0 else None


def pd_metric_deltas(path: Path) -> dict[str, float]:
    def values(metric_path: Path) -> dict[str, float]:
        result: dict[str, float] = defaultdict(float)
        if not metric_path.is_file():
            return result
        for line in metric_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            match = PROM_VALUE.match(line)
            if not match:
                continue
            name = match.group(1)
            lowered = name.lower()
            if not any(
                token in lowered
                for token in (
                    "nixl",
                    "kv_transfer",
                    "remote_prefill",
                    "kv_load",
                )
            ):
                continue
            result[name] += float(match.group(2))
        return result

    before = values(path / "metrics-before.txt")
    after = values(path / "metrics-after.txt")
    return {
        name: value - before.get(name, 0.0)
        for name, value in after.items()
        if value - before.get(name, 0.0) != 0
    }


def ancestor_json(path: Path, name: str, stop: Path) -> dict[str, Any] | None:
    current = path
    while current != stop and stop in current.parents:
        candidate = current / name
        if candidate.is_file():
            return read_json(candidate)
        current = current.parent
    candidate = stop / name
    return read_json(candidate) if candidate.is_file() else None


def status_for(
    path: Path, stop: Path, *, default_status: str = "incomplete"
) -> str:
    status = ancestor_json(path, "status.json", stop)
    if status and isinstance(status.get("status"), str):
        return str(status["status"])
    if ancestor_json(path, "stopped.json", stop) is not None:
        return "partial"
    lowered = str(path).lower()
    if "invalid" in lowered:
        return "invalid"
    if "aborted" in lowered:
        return "aborted"
    if "partial" in lowered or "stopped" in lowered:
        return "partial"
    return default_status


def workload_label(path: Path) -> str:
    for candidate in (
        "default-mix",
        "cache-sweep",
        "agent-session",
        "production-mix-32k",
        "offline-throughput-extended",
        "offline-throughput",
    ):
        if candidate in path.parts or candidate in str(path):
            return candidate
    return path.parent.name


def base_point(
    *,
    summary: Mapping[str, Any],
    label: str,
    experiment_id: str,
    evidence_class: str,
    source: Path,
    profile: str | None,
    status: str,
    cache_hit_share: float | None,
    include_in_slo_frontier: bool,
    tier: str | None,
    tier_pass: bool | None,
    legacy_reference: bool = False,
    slo_goodput_rps: float | None = None,
    scope: str = "overall",
    category: str | None = None,
    pass_phase: str | None = None,
    repetition: int | None = None,
    target_cacheable_fraction: float | None = None,
    decision_grade: bool = False,
) -> dict[str, Any]:
    completed = finite(summary.get("completed")) or 0.0
    input_total = finite(summary.get("input_tokens"))
    output_total = finite(summary.get("output_tokens"))
    request_rps = finite(summary.get("request_rps"))
    tasks_per_hour = request_rps * 3600 if request_rps is not None else None
    source_text = str(source).lower()
    if "remote" in source_text or "gateway" in source_text:
        request_path = "remote-gateway"
    elif "direct" in source_text:
        request_path = "direct-backend"
    else:
        request_path = "local-router"
    if "production-trace" in source_text or "/trace/" in source_text:
        provenance = "trace"
    elif evidence_class.startswith("reused_"):
        provenance = "reused-synthetic"
    else:
        provenance = "synthetic"
    if cache_hit_share is None:
        cache_regime = "unknown"
    elif cache_hit_share < 0.02:
        cache_regime = "uncached"
    else:
        cache_regime = "cache-active"
    arm = None
    if "arms" in source.parts:
        index = source.parts.index("arms")
        if index + 1 < len(source.parts):
            arm = source.parts[index + 1]
    transfer_deltas = pd_metric_deltas(source)
    transfer_failures = sum(
        value
        for name, value in transfer_deltas.items()
        if any(
            token in name.lower()
            for token in ("fail", "error", "recompute")
        )
    )
    return {
        "experiment_id": experiment_id,
        "label": label,
        "status": status,
        "evidence_class": evidence_class,
        "profile": profile,
        "arm": arm,
        "workload": summary.get("active_workload") or workload_label(source),
        "scope": scope,
        "category": category,
        "pass_phase": pass_phase,
        "repetition": repetition,
        "target_cacheable_fraction": target_cacheable_fraction,
        "decision_grade": decision_grade,
        "provenance": provenance,
        "request_path": request_path,
        "client": (
            f"{summary.get('shards')} processes"
            if summary.get("sharded") is True
            else "1 process"
        ),
        "mode": summary.get("mode"),
        "configured_concurrency": summary.get("configured_concurrency"),
        "configured_request_rate": summary.get("configured_request_rate"),
        "offered_request_rps": summary.get("offered_request_rps"),
        "request_rps": request_rps,
        "tasks_per_hour": tasks_per_hour,
        "slo_goodput_rps": slo_goodput_rps,
        "completion_ratio": summary.get("completion_ratio"),
        "error_rate": summary.get("error_rate"),
        "queue_slope_ms_per_s": summary.get("queue_slope_ms_per_s"),
        "concurrency_bound": summary.get("concurrency_bound"),
        "ttft_p50_ms": nested_metric(summary, "ttft_ms", "p50"),
        "ttft_p95_ms": nested_metric(summary, "ttft_ms", "p95"),
        "ttft_p99_ms": nested_metric(summary, "ttft_ms", "p99"),
        "tpot_p50_ms": nested_metric(summary, "tpot_ms", "p50"),
        "tpot_p95_ms": nested_metric(summary, "tpot_ms", "p95"),
        "tpot_p99_ms": nested_metric(summary, "tpot_ms", "p99"),
        "e2e_p50_ms": nested_metric(summary, "e2e_ms", "p50"),
        "e2e_p95_ms": nested_metric(summary, "e2e_ms", "p95"),
        "e2e_p99_ms": nested_metric(summary, "e2e_ms", "p99"),
        "stream_gap_p95_ms": nested_metric(summary, "stream_gap_ms", "p95"),
        "stream_gap_p99_ms": nested_metric(summary, "stream_gap_ms", "p99"),
        "mean_input_tokens": (
            input_total / completed
            if input_total is not None and completed > 0
            else summary.get("mean_input_tokens")
            or summary.get("mean_prompt_tokens")
        ),
        "mean_output_tokens": (
            output_total / completed
            if output_total is not None and completed > 0
            else summary.get("mean_output_tokens")
        ),
        "cache_hit_share": cache_hit_share,
        "cache_regime": cache_regime,
        "dspark_acceptance": summary.get("dspark_acceptance"),
        "engine_waiting_max": summary.get("engine_waiting_max"),
        "pd_transfer_failures": transfer_failures or None,
        "pd_metric_deltas": (
            json.dumps(transfer_deltas, sort_keys=True)
            if transfer_deltas
            else None
        ),
        "tier": tier,
        "tier_pass": tier_pass,
        "legacy_reference": legacy_reference,
        "include_in_slo_frontier": (
            include_in_slo_frontier
            and status == "complete"
            and summary.get("mode") == "open"
            and tier_pass is True
        ),
        "source": str(source),
    }


def legacy_pass_map(run_root: Path) -> dict[str, bool]:
    path = run_root / "default-mix/capacity/capacity_summary.json"
    if not path.is_file():
        return {}
    capacity = read_json(path)
    mapping: dict[str, bool] = {}
    references = capacity.get("run_references") or []
    if isinstance(references, list):
        for reference in references:
            if isinstance(reference, Mapping) and isinstance(
                reference.get("id"), str
            ):
                mapping[str(reference["id"])] = reference.get("pass") is True
    return mapping


def collect_existing(
    campaign: Mapping[str, Any], archive_root: Path
) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    evidence_items = campaign.get("existing_evidence") or []
    if not isinstance(evidence_items, list):
        raise CollectionError("existing_evidence must be a list")
    for evidence in evidence_items:
        if not isinstance(evidence, Mapping):
            continue
        relative = evidence.get("relative_path")
        if not isinstance(relative, str):
            continue
        root = archive_root / relative
        if not root.is_dir():
            continue
        pass_map = legacy_pass_map(root)
        fixed_cache = finite(evidence.get("cache_hit_share"))
        for summary_path in sorted(root.rglob("summary.json")):
            if "telemetry" in summary_path.parts:
                continue
            try:
                summary = read_json(summary_path)
            except (OSError, json.JSONDecodeError, CollectionError):
                continue
            trial = summary_path.parent
            run_pass = pass_map.get(trial.name)
            is_capacity = "capacity" in summary_path.parts
            tier = "legacy-p95" if is_capacity and pass_map else None
            measured_cache = cache_share(trial)
            if measured_cache is None:
                measured_cache = fixed_cache
            points.append(
                base_point(
                    summary=summary,
                    label=str(evidence.get("label") or evidence.get("id")),
                    experiment_id=str(evidence.get("id") or "existing"),
                    evidence_class=str(
                        evidence.get("evidence_class") or "reused"
                    ),
                    source=trial,
                    profile=(
                        str(evidence["profile"])
                        if evidence.get("profile") is not None
                        else None
                    ),
                    status=status_for(
                        trial, root, default_status="complete"
                    ),
                    cache_hit_share=measured_cache,
                    # Archive gates are p95-only and cannot satisfy the new
                    # repeated, per-class p99 frontier contract.
                    include_in_slo_frontier=False,
                    tier=tier,
                    tier_pass=run_pass,
                    legacy_reference=bool(
                        evidence.get("include_as_legacy_reference")
                    ),
                )
            )
    return points


def experiment_id_for(path: Path, live_root: Path) -> str:
    try:
        relative = path.relative_to(live_root)
    except ValueError:
        return "LAT-UNKNOWN"
    return relative.parts[0] if relative.parts else "LAT-UNKNOWN"


def apply_manifest_labels(
    point: dict[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    experiments = manifest.get("experiments") or []
    if not isinstance(experiments, list):
        experiments = []
    names = {str(value) for value in experiments}
    if "lat-prefix-off" in names:
        point["cache_regime"] = "disabled"
    elif "lat-prefix-on" in names:
        point["cache_regime"] = "enabled-unmeasured"
    if "lat-dspark-k2" in names:
        point["dspark_config"] = "k2"
    elif "lat-dspark-k5" in names:
        point["dspark_config"] = "k5"
    else:
        point["dspark_config"] = "off"
    return point


def apply_repeat_command(
    point: dict[str, Any], trial: Path, live_root: Path
) -> dict[str, Any]:
    if (
        point.get("pass_phase") == "discovery"
        and point.get("mode") == "open"
        and point.get("scope") == "overall"
        and point.get("tier") == "balanced"
        and point.get("target_cacheable_fraction") is not None
        and point.get("configured_request_rate") is not None
    ):
        relative = trial.relative_to(live_root)
        if len(relative.parts) >= 2:
            run_root = live_root / relative.parts[0] / relative.parts[1]
            cache = round(
                float(point["target_cacheable_fraction"]) * 100
            )
            rate = float(point["configured_request_rate"])
            point["repeat_command"] = (
                "bash ops_latency/run_repeat_selected.sh "
                f"--run-root {run_root} "
                f"--point {point['workload']}:{cache}:{rate:g}"
            )
    return point


def repeated_boundary_passes(
    *,
    trial: Path,
    tier: str | None,
    analysis_summary: Mapping[str, Any],
    live_root: Path,
) -> bool:
    if tier is None or "boundary" not in trial.parts:
        return False
    search = ancestor_json(
        trial, "latency_search_summary.json", live_root
    )
    if not search:
        return False
    highest = search.get("highest_passing")
    if not isinstance(highest, Mapping):
        return False
    value = highest.get(tier)
    if not isinstance(value, Mapping):
        return False
    expected = finite(value.get("load_point"))
    configured = finite(analysis_summary.get("configured_request_rate"))
    return (
        expected is not None
        and configured is not None
        and math.isclose(expected, configured, rel_tol=1e-9, abs_tol=1e-9)
    )


def active_case_metadata(path: Path) -> tuple[str | None, float | None]:
    pattern = re.compile(r"^(chat|code|agent|mix)-f(0|25|50|75)$")
    for part in path.parts:
        match = pattern.match(part)
        if match:
            return match.group(1), int(match.group(2)) / 100.0
    return None, None


def run_reference_metadata(
    trial: Path, live_root: Path
) -> tuple[str | None, int | None]:
    search = ancestor_json(
        trial, "latency_search_summary.json", live_root
    )
    if not search:
        return None, None
    references = search.get("run_references") or []
    for reference in references:
        if isinstance(reference, Mapping) and reference.get("id") == trial.name:
            phase = reference.get("pass_phase") or search.get("pass_phase")
            repetition = reference.get("repetition")
            return (
                str(phase) if isinstance(phase, str) else None,
                int(repetition)
                if isinstance(repetition, int)
                and not isinstance(repetition, bool)
                else None,
            )
    return None, None


def collect_live(live_root: Path) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    if not live_root.is_dir():
        return points
    for analysis_path in sorted(live_root.rglob("latency_analysis.json")):
        summary_path = analysis_path.with_name("summary.json")
        if not summary_path.is_file():
            continue
        analysis = read_json(analysis_path)
        summary = read_json(summary_path)
        trial = analysis_path.parent
        manifest = ancestor_json(trial, "manifest.json", live_root) or {}
        experiment_id = str(
            manifest.get("experiment_id")
            or experiment_id_for(trial, live_root)
        )
        profile = (
            str(manifest["profile"]) if manifest.get("profile") else None
        )
        status = status_for(trial, live_root)
        active_workload, target_cacheable_fraction = active_case_metadata(
            trial
        )
        pass_phase, repetition = run_reference_metadata(trial, live_root)
        overall = analysis.get("overall")
        if not isinstance(overall, Mapping):
            continue
        combined = dict(summary)
        if active_workload is not None:
            combined["active_workload"] = active_workload
        for metric in (
            "ttft_ms",
            "tpot_ms",
            "e2e_ms",
            "stream_gap_ms",
        ):
            if isinstance(overall.get(metric), Mapping):
                combined[metric] = overall[metric]
        for key in (
            "scheduled",
            "completed",
            "failed",
            "completion_ratio",
            "error_rate",
            "mean_input_tokens",
            "mean_output_tokens",
        ):
            if key in overall:
                combined[key] = overall[key]

        tiers = analysis.get("slo_tiers") or {}
        if not isinstance(tiers, Mapping) or not tiers:
            tiers = {None: {"pass": None, "slo_goodput_rps": None}}
        for tier_name, tier_result in tiers.items():
            tier_mapping = (
                tier_result if isinstance(tier_result, Mapping) else {}
            )
            points.append(
                apply_repeat_command(
                    apply_manifest_labels(
                        base_point(
                        summary=combined,
                        label=f"{experiment_id} {trial.parent.name}",
                        experiment_id=experiment_id,
                        evidence_class="measured_latency_campaign",
                        source=trial,
                        profile=profile,
                        status=status,
                        cache_hit_share=cache_share(trial),
                        include_in_slo_frontier=repeated_boundary_passes(
                            trial=trial,
                            tier=(
                                str(tier_name)
                                if tier_name is not None
                                else None
                            ),
                            analysis_summary=analysis,
                            live_root=live_root,
                        ),
                        tier=(
                            str(tier_name)
                            if tier_name is not None
                            else None
                        ),
                        tier_pass=(
                            tier_mapping.get("pass")
                            if isinstance(tier_mapping.get("pass"), bool)
                            else None
                        ),
                        slo_goodput_rps=finite(
                            tier_mapping.get("slo_goodput_rps")
                        ),
                        pass_phase=pass_phase,
                        repetition=repetition,
                        target_cacheable_fraction=target_cacheable_fraction,
                        ),
                        manifest,
                    ),
                    trial,
                    live_root,
                )
            )

        categories = analysis.get("by_category") or {}
        if isinstance(categories, Mapping):
            for category, group in categories.items():
                if not isinstance(group, Mapping):
                    continue
                category_summary = dict(summary)
                category_summary.update(group)
                points.append(
                    apply_repeat_command(
                        apply_manifest_labels(
                            base_point(
                            summary=category_summary,
                            label=f"{experiment_id} {trial.parent.name}",
                            experiment_id=experiment_id,
                            evidence_class="measured_latency_campaign",
                            source=trial,
                            profile=profile,
                            status=status,
                            cache_hit_share=cache_share(trial),
                            include_in_slo_frontier=False,
                            tier=None,
                            tier_pass=None,
                            scope="category",
                            category=str(category),
                            pass_phase=pass_phase,
                            repetition=repetition,
                            target_cacheable_fraction=target_cacheable_fraction,
                            ),
                            manifest,
                        ),
                        trial,
                        live_root,
                    )
                )
    return points


def confirmed_three_run_points(
    points: Sequence[Mapping[str, Any]],
    *,
    cache_tolerance: float,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for point in points:
        if (
            point.get("evidence_class") != "measured_latency_campaign"
            or point.get("scope") != "overall"
            or point.get("mode") != "open"
            or point.get("tier") is None
            or point.get("configured_request_rate") is None
        ):
            continue
        key = (
            point.get("experiment_id"),
            point.get("profile"),
            point.get("arm"),
            point.get("workload"),
            point.get("target_cacheable_fraction"),
            point.get("tier"),
            float(point["configured_request_rate"]),
        )
        groups[key].append(point)

    confirmed: list[dict[str, Any]] = []
    latency_fields = (
        "ttft_p50_ms",
        "ttft_p95_ms",
        "ttft_p99_ms",
        "tpot_p50_ms",
        "tpot_p95_ms",
        "tpot_p99_ms",
        "e2e_p50_ms",
        "e2e_p95_ms",
        "e2e_p99_ms",
        "stream_gap_p95_ms",
        "stream_gap_p99_ms",
        "queue_slope_ms_per_s",
        "error_rate",
    )
    for values in groups.values():
        by_repetition = {
            int(point["repetition"]): point
            for point in values
            if isinstance(point.get("repetition"), int)
            and point.get("tier_pass") is True
            and point.get("status") == "complete"
        }
        if set(by_repetition) < {1, 2, 3}:
            continue
        selected = [by_repetition[index] for index in (1, 2, 3)]
        if selected[0].get("pass_phase") != "discovery" or any(
            point.get("pass_phase") != "confirm" for point in selected[1:]
        ):
            continue
        target = finite(selected[0].get("target_cacheable_fraction"))
        hits = [
            finite(point.get("cache_hit_share")) for point in selected
        ]
        normalized_hits = [
            0.0 if target == 0.0 and value is None else value
            for value in hits
        ]
        if (
            target is not None
            and (
                any(value is None for value in normalized_hits)
                or any(
                    abs(float(value) - target) > cache_tolerance
                    for value in normalized_hits
                    if value is not None
                )
            )
        ):
            continue
        aggregate = dict(selected[0])
        aggregate.update(
            {
                "label": f"{selected[0]['label']} · 3-run confirmed",
                "evidence_class": "confirmed_three_run",
                "pass_phase": "confirm",
                "repetition": None,
                "repetition_count": 3,
                "decision_grade": True,
                "include_in_slo_frontier": True,
                "request_rps": min(
                    float(point["request_rps"]) for point in selected
                ),
                "slo_goodput_rps": min(
                    float(point["slo_goodput_rps"]) for point in selected
                ),
                "completion_ratio": min(
                    float(point["completion_ratio"]) for point in selected
                ),
                "cache_hit_share": (
                    sum(float(value) for value in normalized_hits)
                    / len(normalized_hits)
                    if normalized_hits
                    else None
                ),
                "source": ";".join(str(point["source"]) for point in selected),
            }
        )
        aggregate["tasks_per_hour"] = aggregate["request_rps"] * 3600
        for field in latency_fields:
            candidates = [
                finite(point.get(field)) for point in selected
            ]
            present = [value for value in candidates if value is not None]
            aggregate[field] = max(present) if present else None
        confirmed.append(aggregate)
    return confirmed


def mark_pareto_frontier(
    points: Sequence[dict[str, Any]],
    dimensions: Sequence[str] = (
        "ttft_p99_ms",
        "tpot_p99_ms",
        "slo_goodput_rps",
    ),
) -> None:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        if point.get("decision_grade") is True:
            groups[
                (
                    point.get("workload"),
                    point.get("target_cacheable_fraction"),
                    point.get("tier"),
                )
            ].append(point)
    for values in groups.values():
        for candidate in values:
            candidate["pareto_frontier"] = False
            candidate_values = {
                dimension: finite(candidate.get(dimension))
                for dimension in dimensions
            }
            if any(value is None for value in candidate_values.values()):
                candidate["include_in_slo_frontier"] = False
                continue
            dominated = False
            for other in values:
                if other is candidate:
                    continue
                other_values = {
                    dimension: finite(other.get(dimension))
                    for dimension in dimensions
                }
                if any(value is None for value in other_values.values()):
                    continue
                no_worse = True
                strictly_better = False
                for dimension in dimensions:
                    candidate_value = float(candidate_values[dimension])
                    other_value = float(other_values[dimension])
                    maximize = any(
                        token in dimension
                        for token in ("goodput", "throughput", "request_rps")
                    )
                    if maximize:
                        no_worse &= other_value >= candidate_value
                        strictly_better |= other_value > candidate_value
                    else:
                        no_worse &= other_value <= candidate_value
                        strictly_better |= other_value < candidate_value
                if no_worse and strictly_better:
                    dominated = True
                    break
            candidate["pareto_frontier"] = not dominated
            candidate["include_in_slo_frontier"] = not dominated


def collect(
    *,
    campaign_path: Path,
    archive_root: Path,
    live_root: Path,
) -> dict[str, Any]:
    campaign = read_yaml(campaign_path)
    points = collect_existing(campaign, archive_root)
    live_points = collect_live(live_root)
    points.extend(live_points)
    tolerance = float(
        (campaign.get("active_protocol") or {}).get(
            "cache_match_tolerance", 0.10
        )
    )
    confirmed = confirmed_three_run_points(
        live_points, cache_tolerance=tolerance
    )
    points.extend(confirmed)
    dimensions = tuple(
        str(value)
        for value in (campaign.get("active_protocol") or {}).get(
            "pareto_dimensions",
            ["ttft_p99_ms", "tpot_p99_ms", "slo_goodput_rps"],
        )
    )
    mark_pareto_frontier(confirmed, dimensions)
    gpu_count = int(campaign.get("gpu_count", 8))
    gpu_price = float(campaign.get("gpu_price_per_hour", 4.5))
    for point in points:
        tasks_per_hour = finite(point.get("tasks_per_hour"))
        point["cost_per_million_tasks"] = (
            gpu_count * gpu_price / tasks_per_hour * 1_000_000
            if tasks_per_hour is not None and tasks_per_hour > 0
            else None
        )
    return {
        "schema_version": 1,
        "campaign": campaign,
        "archive_root": str(archive_root),
        "live_root": str(live_root),
        "points": points,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = collect(
        campaign_path=args.campaign.expanduser().resolve(),
        archive_root=args.archive_root.expanduser().resolve(),
        live_root=args.live_root.expanduser().resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{len(result['points'])} points -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

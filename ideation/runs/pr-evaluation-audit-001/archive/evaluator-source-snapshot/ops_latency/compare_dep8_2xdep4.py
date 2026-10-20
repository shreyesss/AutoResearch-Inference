#!/usr/bin/env python3
"""Collect and select the paired DEP8 versus 2xDEP4 latency experiment.

All work happens after load generation. The module is shared by the resumable
runner and the HTML report so selection cannot drift from presentation.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

try:
    from ops_latency.report.collect_results import cache_share
except ModuleNotFoundError:  # Direct script execution from ops_latency/.
    from report.collect_results import cache_share


REQUEST_COUNTER = re.compile(
    r'^vllm:request_success_total\{[^}]*\}\s+([0-9.eE+-]+)$'
)
ROUTER_COUNTER = re.compile(
    r'^dsv41_router_requests_total\{kind="requests_backend_([0-9]+)"\}'
    r"\s+([0-9.eE+-]+)$"
)
RUN_ID = re.compile(r"closed-c(?P<concurrency>[0-9]+)-rep(?P<repetition>[0-9]+)")
METRICS = (
    "request_rps",
    "output_tokens_per_s",
    "completion_ratio",
    "error_rate",
    "ttft_p50_ms",
    "ttft_p95_ms",
    "ttft_p99_ms",
    "tpot_p50_ms",
    "tpot_p95_ms",
    "tpot_p99_ms",
    "e2e_p50_ms",
    "e2e_p95_ms",
    "e2e_p99_ms",
    "median_output_tokens_per_second_per_user",
    "cache_hit_share",
)
DELTA_METRICS = (
    "request_rps",
    "output_tokens_per_s",
    "ttft_p50_ms",
    "ttft_p95_ms",
    "ttft_p99_ms",
    "tpot_p50_ms",
    "tpot_p95_ms",
    "tpot_p99_ms",
    "e2e_p50_ms",
    "e2e_p95_ms",
    "e2e_p99_ms",
)


class ComparisonError(RuntimeError):
    """Raised when paired comparison evidence is missing or malformed."""


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def read_mapping(path: Path) -> dict[str, Any]:
    try:
        if path.suffix in {".yaml", ".yml"}:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ComparisonError(f"cannot read {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ComparisonError(f"{path} must contain an object")
    return loaded


def comparison_contract(campaign: Mapping[str, Any]) -> dict[str, Any]:
    contract = campaign.get("dep8_vs_2xdep4")
    if not isinstance(contract, dict):
        raise ComparisonError("campaign is missing dep8_vs_2xdep4")
    return contract


def arm_definitions(contract: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw = contract.get("arms")
    if not isinstance(raw, Mapping):
        raise ComparisonError("comparison contract is missing arms")
    result: dict[str, dict[str, Any]] = {}
    for name in ("dep8", "dep4_api2", "dep4_api4"):
        value = raw.get(name)
        if not isinstance(value, dict):
            raise ComparisonError(f"comparison arm {name} is missing")
        result[name] = value
    seq = raw.get("dep4_seq80")
    if not isinstance(seq, Mapping):
        raise ComparisonError("comparison arm dep4_seq80 is missing")
    result["dep4_api2_seq80"] = {
        "experiment_id": seq["experiment_id_api2"],
        "profile": seq["profile"],
        "experiment_flags": seq["experiment_flags_api2"],
    }
    result["dep4_api4_seq80"] = {
        "experiment_id": seq["experiment_id_api4"],
        "profile": seq["profile"],
        "experiment_flags": seq["experiment_flags_api4"],
    }
    return result


def source_counter_totals(path: Path) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    if not path.is_file():
        return {}
    source = "unknown"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# source "):
            source = line.removeprefix("# source ").strip()
            continue
        match = REQUEST_COUNTER.match(line)
        if match:
            totals[source] += float(match.group(1))
    return dict(totals)


def backend_balance(run_dir: Path) -> dict[str, Any]:
    before = source_counter_totals(run_dir / "metrics-before.txt")
    after = source_counter_totals(run_dir / "metrics-after.txt")
    deltas = {
        source: max(0.0, value - before.get(source, 0.0))
        for source, value in after.items()
    }
    total = sum(deltas.values())
    shares = {
        source: value / total
        for source, value in sorted(deltas.items())
        if total > 0
    }
    values = list(deltas.values())
    return {
        "completed_request_deltas": deltas,
        "shares": shares,
        "max_to_min_ratio": (
            max(values) / min(values)
            if len(values) > 1 and min(values) > 0
            else None
        ),
        "observed_backends": len(values),
        "all_observed_backends_active": bool(values)
        and all(value > 0 for value in values),
        "zero_traffic_backends": sorted(
            source for source, value in deltas.items() if value <= 0
        ),
    }


def router_balance(run_dir: Path) -> dict[str, Any] | None:
    def values(path: Path) -> dict[str, float]:
        result: dict[str, float] = defaultdict(float)
        if not path.is_file():
            return {}
        for line in path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            match = ROUTER_COUNTER.match(line)
            if match:
                result[f"backend_{match.group(1)}"] += float(match.group(2))
        return dict(result)

    before = values(run_dir / "metrics-before.txt")
    after = values(run_dir / "metrics-after.txt")
    if not after:
        return None
    deltas = {
        backend: max(0.0, value - before.get(backend, 0.0))
        for backend, value in after.items()
    }
    total = sum(deltas.values())
    shares = {
        backend: value / total
        for backend, value in sorted(deltas.items())
        if total > 0
    }
    values_list = list(deltas.values())
    return {
        "request_deltas": deltas,
        "shares": shares,
        "max_to_min_ratio": (
            max(values_list) / min(values_list)
            if len(values_list) > 1 and min(values_list) > 0
            else None
        ),
        "observed_backends": len(values_list),
        "all_observed_backends_active": bool(values_list)
        and all(value > 0 for value in values_list),
        "zero_traffic_backends": sorted(
            backend for backend, value in deltas.items() if value <= 0
        ),
    }


def dataset_digest(
    run_root: Path, case: str, concurrency: int, run_id: str
) -> str | None:
    manifest = (
        run_root
        / "trial-datasets"
        / "cells"
        / case
        / f"c{concurrency}"
        / "dataset-sha256.txt"
    )
    if not manifest.is_file():
        return None
    target = f"{run_id}.jsonl"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and Path(parts[1]).name == target:
            return parts[0]
    return None


def warmup_digest(run_root: Path, case: str) -> str | None:
    manifest = (
        run_root
        / "trial-datasets"
        / "cells"
        / case
        / "warmup-sha256.txt"
    )
    if not manifest.is_file():
        return None
    parts = manifest.read_text(encoding="utf-8").split()
    return parts[0] if parts else None


def qualify(
    point: Mapping[str, Any], selection: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    checks = (
        ("completion_ratio", ">=", "minimum_completion_ratio"),
        ("error_rate", "<=", "maximum_error_rate"),
        ("ttft_p50_ms", "<=", "ttft_p50_ms"),
        ("ttft_p99_ms", "<=", "ttft_p99_ms"),
        (
            "median_output_tokens_per_second_per_user",
            ">=",
            "minimum_median_output_tokens_per_second_per_user",
        ),
    )
    for metric, operator, threshold_name in checks:
        value = finite(point.get(metric))
        threshold = finite(selection.get(threshold_name))
        if value is None or threshold is None:
            failures.append(f"{metric}:missing")
        elif operator == ">=" and value < threshold:
            failures.append(f"{metric}:{value:.6g}<{threshold:.6g}")
        elif operator == "<=" and value > threshold:
            failures.append(f"{metric}:{value:.6g}>{threshold:.6g}")
    cache_value = finite(point.get("cache_hit_share"))
    cache_target = finite(selection.get("target_cache_hit_share"))
    cache_tolerance = finite(selection.get("cache_hit_tolerance"))
    if (
        cache_value is None
        or cache_target is None
        or cache_tolerance is None
    ):
        failures.append("cache_hit_share:missing")
    elif abs(cache_value - cache_target) > cache_tolerance:
        failures.append(
            "cache_hit_share:"
            f"{cache_value:.6g} outside {cache_target:.6g}±{cache_tolerance:.6g}"
        )
    if str(point.get("arm", "")).startswith("dep4_"):
        backend = point.get("backend_balance")
        router = point.get("router_balance")
        if (
            not isinstance(backend, Mapping)
            or backend.get("observed_backends") != 2
            or backend.get("all_observed_backends_active") is not True
        ):
            failures.append("backend_balance:not-two-active-backends")
        if (
            not isinstance(router, Mapping)
            or router.get("observed_backends") != 2
            or router.get("all_observed_backends_active") is not True
        ):
            failures.append("router_balance:not-two-active-backends")
    return not failures, failures


def point_from_summary(
    *,
    arm: str,
    experiment_id: str,
    run_root: Path,
    summary_path: Path,
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    summary = read_mapping(summary_path)
    run_dir = summary_path.parent
    match = RUN_ID.fullmatch(run_dir.name)
    if match is None:
        raise ComparisonError(f"unexpected comparison run directory: {run_dir}")
    concurrency = int(match.group("concurrency"))
    repetition = int(match.group("repetition"))
    scheduled = finite(summary.get("scheduled"))
    completed = finite(summary.get("completed"))
    tpot_p50 = finite((summary.get("tpot_ms") or {}).get("p50"))
    point: dict[str, Any] = {
        "arm": arm,
        "experiment_id": experiment_id,
        "run_root": str(run_root),
        "source": str(run_dir),
        "phase": (read_mapping(run_root / "configuration.json").get("phase") or "discovery"),
        "concurrency": concurrency,
        "repetition": repetition,
        "request_rps": finite(summary.get("request_rps")),
        "output_tokens_per_s": finite(
            summary.get("output_tps") or summary.get("output_tokens_per_s")
        ),
        "completion_ratio": (
            completed / scheduled
            if completed is not None and scheduled is not None and scheduled > 0
            else None
        ),
        "error_rate": finite(summary.get("error_rate")),
        "ttft_p50_ms": finite((summary.get("ttft_ms") or {}).get("p50")),
        "ttft_p95_ms": finite((summary.get("ttft_ms") or {}).get("p95")),
        "ttft_p99_ms": finite((summary.get("ttft_ms") or {}).get("p99")),
        "tpot_p50_ms": tpot_p50,
        "tpot_p95_ms": finite((summary.get("tpot_ms") or {}).get("p95")),
        "tpot_p99_ms": finite((summary.get("tpot_ms") or {}).get("p99")),
        "e2e_p50_ms": finite((summary.get("e2e_ms") or {}).get("p50")),
        "e2e_p95_ms": finite((summary.get("e2e_ms") or {}).get("p95")),
        "e2e_p99_ms": finite((summary.get("e2e_ms") or {}).get("p99")),
        "median_output_tokens_per_second_per_user": (
            1000.0 / tpot_p50 if tpot_p50 is not None and tpot_p50 > 0 else None
        ),
        "cache_hit_share": cache_share(run_dir),
        "backend_balance": backend_balance(run_dir),
        "router_balance": router_balance(run_dir),
        "dataset_sha256": dataset_digest(
            run_root, "agent-f75", concurrency, run_dir.name
        ),
        "warmup_dataset_sha256": warmup_digest(run_root, "agent-f75"),
    }
    point["qualifies"], point["qualification_failures"] = qualify(point, selection)
    return point


def valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def run_matches_contract(
    *,
    run_root: Path,
    definition: Mapping[str, Any],
    campaign: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> bool:
    config_path = run_root / "configuration.json"
    manifest_path = run_root / "manifest.json"
    if not config_path.is_file() or not manifest_path.is_file():
        return False
    config = read_mapping(config_path)
    manifest = read_mapping(manifest_path)
    protocol = contract.get("protocol") or {}
    workload = contract.get("workload") or {}
    expected_concurrencies = [
        int(value) for value in protocol.get("concurrencies") or []
    ]
    expected_concurrency_text = " ".join(map(str, expected_concurrencies))
    expected_flags = [str(value) for value in definition["experiment_flags"]]
    expected_flags_text = " ".join(expected_flags)
    phase = config.get("phase") or "discovery"
    if phase == "discovery":
        repetitions = int(protocol.get("discovery_repetitions") or 0)
        repetition_start = 1
        concurrency_match = (
            config.get("concurrencies") == expected_concurrency_text
        )
    elif phase == "confirm":
        repetitions = int(protocol.get("confirmation_repetitions") or 0)
        repetition_start = 2
        try:
            configured = [
                int(value)
                for value in str(config.get("concurrencies") or "").split()
            ]
        except ValueError:
            return False
        concurrency_match = (
            len(configured) == 1
            and configured[0] in expected_concurrencies
        )
    else:
        return False
    workload_suffix = str(workload.get("file") or "")
    config_workload = str(config.get("workload") or "")
    router_contract = (
        (campaign.get("vllm_router") or {}).get("aggregated_tp4_frontend")
        or {}
    )
    router_manifest = manifest.get("aggregated_router_config") or {}
    code_hashes = manifest.get("code_sha256") or {}
    required_hashes = (
        "experiment_definitions",
        "loadgen",
        "loadgen_shards",
        "latency_search",
        "serve_recipe",
        "serve_pd_recipe",
        "local_router",
        "sweep_runner",
        "comparison_analyzer",
        "comparison_runner",
    )
    return (
        config.get("kind") == "closed_loop_concurrency_sweep"
        and config.get("profile") == definition["profile"]
        and config.get("experiment_flags") == expected_flags_text
        and config.get("cases") == workload.get("case")
        and concurrency_match
        and config.get("search") == "fixed"
        and config_workload.endswith(workload_suffix)
        and config.get("loadgen_shards") == protocol.get("client_shards")
        and config.get("duration_s") == protocol.get("measured_s")
        and config.get("warmup_s") == protocol.get("warmup_s")
        and config.get("repetitions") == repetitions
        and config.get("repetition_start") == repetition_start
        and config.get("dataset_seed_namespace")
        == f"{protocol.get('dataset_seed_namespace')}-{phase}"
        and config.get("disable_early_stop") == 1
        and manifest.get("experiment_id") == definition["experiment_id"]
        and manifest.get("profile") == definition["profile"]
        and manifest.get("experiments") == expected_flags
        and str(manifest.get("workload") or "").endswith(workload_suffix)
        and valid_sha256(manifest.get("campaign_sha256"))
        and valid_sha256(manifest.get("profile_sha256"))
        and valid_sha256(manifest.get("workload_sha256"))
        and all(valid_sha256(code_hashes.get(name)) for name in required_hashes)
        and router_manifest.get("load_factor")
        == router_contract.get("sticky_load_factor")
        and router_manifest.get("connection_limit")
        == router_contract.get("connection_limit")
        and router_manifest.get("retry_connection_errors")
        == bool(router_contract.get("retry_connection_errors"))
    )


def latest_points(
    results_root: Path,
    definitions: Mapping[str, Mapping[str, Any]],
    campaign: Mapping[str, Any],
    contract: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, int], tuple[str, dict[str, Any]]] = {}
    for arm, definition in definitions.items():
        experiment_id = str(definition["experiment_id"])
        experiment_root = results_root / experiment_id
        if not experiment_root.is_dir():
            continue
        for run_root in sorted(experiment_root.iterdir()):
            status_path = run_root / "status.json"
            config_path = run_root / "configuration.json"
            if not status_path.is_file() or not config_path.is_file():
                continue
            if read_mapping(status_path).get("status") != "complete":
                continue
            if not run_matches_contract(
                run_root=run_root,
                definition=definition,
                campaign=campaign,
                contract=contract,
            ):
                continue
            for summary_path in run_root.glob(
                "cells/agent-f75/c*/runs/closed-c*-rep*/summary.json"
            ):
                point = point_from_summary(
                    arm=arm,
                    experiment_id=experiment_id,
                    run_root=run_root,
                    summary_path=summary_path,
                    selection=selection,
                )
                key = (arm, int(point["concurrency"]), int(point["repetition"]))
                stamp = run_root.name
                if key not in by_key or stamp > by_key[key][0]:
                    by_key[key] = (stamp, point)
    return sorted(
        (item[1] for item in by_key.values()),
        key=lambda item: (item["arm"], item["concurrency"], item["repetition"]),
    )


def median(values: Iterable[float | None]) -> float | None:
    numeric = [value for value in values if value is not None]
    return statistics.median(numeric) if numeric else None


def aggregate_points(points: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for point in points:
        grouped[(str(point["arm"]), int(point["concurrency"]))].append(point)
    aggregates: list[dict[str, Any]] = []
    for (arm, concurrency), observations in sorted(grouped.items()):
        result: dict[str, Any] = {
            "arm": arm,
            "experiment_id": observations[0]["experiment_id"],
            "concurrency": concurrency,
            "observations": len(observations),
            "repetitions": sorted(int(item["repetition"]) for item in observations),
            "all_observations_qualify": all(
                item.get("qualifies") is True for item in observations
            ),
            "confirmed": len(observations) >= 3
            and all(item.get("qualifies") is True for item in observations),
            "sources": [item["source"] for item in observations],
        }
        for metric in METRICS:
            result[metric] = median(finite(item.get(metric)) for item in observations)
        result["qualifies"] = result["all_observations_qualify"]
        balances = [
            item["backend_balance"]["max_to_min_ratio"]
            for item in observations
            if item["backend_balance"]["max_to_min_ratio"] is not None
        ]
        result["backend_max_to_min_ratio"] = median(balances)
        result["all_backends_active"] = all(
            item["backend_balance"]["all_observed_backends_active"] is True
            for item in observations
        )
        result["zero_traffic_backends"] = sorted(
            {
                name
                for item in observations
                for name in item["backend_balance"]["zero_traffic_backends"]
            }
        )
        backend_names = sorted(
            {
                name
                for item in observations
                for name in item["backend_balance"]["shares"]
            }
        )
        result["backend_shares"] = {
            name: median(
                finite(item["backend_balance"]["shares"].get(name))
                for item in observations
            )
            for name in backend_names
        }
        router_observations = [
            item["router_balance"]
            for item in observations
            if item["router_balance"] is not None
        ]
        result["router_max_to_min_ratio"] = median(
            finite(item.get("max_to_min_ratio"))
            for item in router_observations
        )
        result["all_router_backends_active"] = (
            all(
                item["all_observed_backends_active"] is True
                for item in router_observations
            )
            if router_observations
            else None
        )
        result["zero_traffic_router_backends"] = sorted(
            {
                name
                for item in router_observations
                for name in item["zero_traffic_backends"]
            }
        )
        router_names = sorted(
            {
                name
                for item in router_observations
                for name in item["shares"]
            }
        )
        result["router_shares"] = {
            name: median(
                finite(item["shares"].get(name))
                for item in router_observations
            )
            for name in router_names
        }
        aggregates.append(result)
    return aggregates


def best_qualifying(
    aggregates: Sequence[Mapping[str, Any]], arms: set[str]
) -> dict[str, Any] | None:
    eligible = [
        dict(point)
        for point in aggregates
        if point["arm"] in arms
        and point.get("qualifies") is True
        and finite(point.get("request_rps")) is not None
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda point: (
            -float(point["request_rps"]),
            float(point.get("tpot_p50_ms") or math.inf),
            float(point.get("e2e_p50_ms") or math.inf),
        ),
    )


def matching_aggregate(
    aggregates: Sequence[Mapping[str, Any]],
    selected: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if selected is None:
        return None
    for point in aggregates:
        if (
            point["arm"] == selected["arm"]
            and point["concurrency"] == selected["concurrency"]
        ):
            return dict(point)
    return None


def relative_deltas(
    dep4: Mapping[str, Any] | None,
    dep8: Mapping[str, Any] | None,
) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for metric in DELTA_METRICS:
        dep4_value = finite(dep4.get(metric)) if dep4 is not None else None
        dep8_value = finite(dep8.get(metric)) if dep8 is not None else None
        result[f"{metric}_delta_fraction"] = (
            (dep4_value - dep8_value) / dep8_value
            if dep4_value is not None
            and dep8_value is not None
            and dep8_value != 0
            else None
        )
    return result


def same_concurrency_comparisons(
    aggregates: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    dep8 = {
        int(point["concurrency"]): point
        for point in aggregates
        if point["arm"] == "dep8"
    }
    rows: list[dict[str, Any]] = []
    for point in aggregates:
        if not str(point["arm"]).startswith("dep4_"):
            continue
        reference = dep8.get(int(point["concurrency"]))
        target = finite(selection.get("target_cache_hit_share"))
        tolerance = finite(selection.get("cache_hit_tolerance"))
        dep4_cache = finite(point.get("cache_hit_share"))
        dep8_cache = (
            finite(reference.get("cache_hit_share"))
            if reference is not None
            else None
        )
        cache_comparable = (
            target is not None
            and tolerance is not None
            and dep4_cache is not None
            and dep8_cache is not None
            and abs(dep4_cache - target) <= tolerance
            and abs(dep8_cache - target) <= tolerance
        )
        rows.append(
            {
                "dep4_arm": point["arm"],
                "concurrency": point["concurrency"],
                "dep4_qualifies": point["qualifies"],
                "dep8_qualifies": (
                    reference.get("qualifies") if reference is not None else None
                ),
                "cache_comparable": cache_comparable,
                **relative_deltas(
                    point if cache_comparable else None,
                    reference if cache_comparable else None,
                ),
            }
        )
    return rows


def dataset_pairing(
    points: Sequence[Mapping[str, Any]],
    definitions: Mapping[str, Mapping[str, Any]],
    expected_concurrencies: Sequence[int],
) -> dict[str, Any]:
    by_run: dict[tuple[int, int, str], dict[str, str]] = defaultdict(dict)
    for point in points:
        digest = point.get("dataset_sha256")
        if isinstance(digest, str):
            by_run[
                (
                    int(point["concurrency"]),
                    int(point["repetition"]),
                    str(point["phase"]),
                )
            ][
                str(point["arm"])
            ] = digest
    discovery_by_arm: dict[str, dict[str, Any]] = {}
    warmups: dict[tuple[str, str], str] = {}
    for point in points:
        digest = point.get("warmup_dataset_sha256")
        if isinstance(digest, str):
            warmups[(str(point["arm"]), str(point["phase"]))] = digest
    for arm in definitions:
        if not arm.startswith("dep4_"):
            continue
        comparisons: list[dict[str, Any]] = []
        for concurrency in expected_concurrencies:
            values = by_run.get((int(concurrency), 1, "discovery"), {})
            dep8_digest = values.get("dep8")
            dep4_digest = values.get(arm)
            comparisons.append(
                {
                    "concurrency": concurrency,
                    "dep4_arm": arm,
                    "complete": dep8_digest is not None
                    and dep4_digest is not None,
                    "matches_dep8": dep8_digest is not None
                    and dep4_digest is not None
                    and dep4_digest == dep8_digest,
                    "dep8_sha256": dep8_digest,
                    "dep4_sha256": dep4_digest,
                }
            )
        measured = any(item["dep4_sha256"] is not None for item in comparisons)
        dep8_warmup = warmups.get(("dep8", "discovery"))
        dep4_warmup = warmups.get((arm, "discovery"))
        warmup_complete_and_match = (
            dep8_warmup is not None
            and dep4_warmup is not None
            and dep8_warmup == dep4_warmup
        )
        discovery_by_arm[arm] = {
            "measured": measured,
            "comparisons": comparisons,
            "complete": all(item["complete"] for item in comparisons),
            "complete_and_match": all(
                item["complete"] and item["matches_dep8"]
                for item in comparisons
            )
            and warmup_complete_and_match,
            "warmup_complete_and_match": warmup_complete_and_match,
            "dep8_warmup_sha256": dep8_warmup,
            "dep4_warmup_sha256": dep4_warmup,
        }
    confirmation_comparisons: list[dict[str, Any]] = []
    for (concurrency, repetition, phase), values in sorted(by_run.items()):
        if phase != "confirm" or repetition < 2 or "dep8" not in values:
            continue
        for arm, digest in values.items():
            if arm == "dep8":
                continue
            confirmation_comparisons.append(
                {
                    "concurrency": concurrency,
                    "repetition": repetition,
                    "dep4_arm": arm,
                    "matches_dep8": digest == values["dep8"],
                    "dep8_sha256": values["dep8"],
                    "dep4_sha256": digest,
                }
            )
    measured_statuses = [
        status for status in discovery_by_arm.values() if status["measured"]
    ]
    confirmation_warmup_by_arm: dict[str, dict[str, Any]] = {}
    dep8_confirmation_warmup = warmups.get(("dep8", "confirm"))
    for arm in definitions:
        if not arm.startswith("dep4_"):
            continue
        dep4_confirmation_warmup = warmups.get((arm, "confirm"))
        measured = dep4_confirmation_warmup is not None
        confirmation_warmup_by_arm[arm] = {
            "measured": measured,
            "complete_and_match": (
                measured
                and dep8_confirmation_warmup is not None
                and dep4_confirmation_warmup == dep8_confirmation_warmup
            ),
            "dep8_warmup_sha256": dep8_confirmation_warmup,
            "dep4_warmup_sha256": dep4_confirmation_warmup,
        }
    return {
        "discovery_by_arm": discovery_by_arm,
        "all_measured_discovery_arms_complete_and_match": bool(
            measured_statuses
        )
        and all(item["complete_and_match"] for item in measured_statuses),
        "confirmation_same_concurrency_comparisons": confirmation_comparisons,
        "confirmation_warmup_by_arm": confirmation_warmup_by_arm,
        "all_available_confirmation_pairs_match": all(
            item["matches_dep8"] for item in confirmation_comparisons
        ),
    }


def build_comparison(campaign_path: Path, results_root: Path) -> dict[str, Any]:
    campaign = read_mapping(campaign_path)
    contract = comparison_contract(campaign)
    definitions = arm_definitions(contract)
    selection = contract.get("selection")
    if not isinstance(selection, Mapping):
        raise ComparisonError("comparison selection contract is missing")
    points = latest_points(
        results_root, definitions, campaign, contract, selection
    )
    aggregates = aggregate_points(points)
    discovery_points = [
        point
        for point in points
        if point["phase"] == "discovery" and point["repetition"] == 1
    ]
    discovery_aggregates = aggregate_points(discovery_points)
    api_winner = best_qualifying(
        discovery_aggregates, {"dep4_api2", "dep4_api4"}
    )
    selected_api = str(api_winner["arm"]) if api_winner else None
    seq80_arm = (
        f"{selected_api}_seq80" if selected_api in {"dep4_api2", "dep4_api4"} else None
    )
    dep4_arms = {"dep4_api2", "dep4_api4"}
    if seq80_arm:
        dep4_arms.add(seq80_arm)
    discovery_dep4_winner = best_qualifying(discovery_aggregates, dep4_arms)
    discovery_dep8_winner = best_qualifying(discovery_aggregates, {"dep8"})
    dep4_winner = matching_aggregate(aggregates, discovery_dep4_winner)
    dep8_winner = matching_aggregate(aggregates, discovery_dep8_winner)
    expected_concurrencies = [
        int(value)
        for value in (contract.get("protocol") or {}).get("concurrencies") or []
    ]
    pairing = dataset_pairing(points, definitions, expected_concurrencies)
    selected_pairing = (
        (pairing.get("discovery_by_arm") or {}).get(
            str(discovery_dep4_winner["arm"])
        )
        if discovery_dep4_winner is not None
        else None
    )
    selected_confirmation_warmup_pairing = (
        (pairing.get("confirmation_warmup_by_arm") or {}).get(
            str(discovery_dep4_winner["arm"])
        )
        if discovery_dep4_winner is not None
        else None
    )
    return {
        "schema_version": 1,
        "campaign": str(campaign_path.resolve()),
        "results_root": str(results_root.resolve()),
        "contract": contract,
        "arm_definitions": definitions,
        "points": points,
        "aggregates": aggregates,
        "discovery_aggregates": discovery_aggregates,
        "dataset_pairing": pairing,
        "selected_dataset_pairing": selected_pairing,
        "selected_confirmation_warmup_pairing": (
            selected_confirmation_warmup_pairing
        ),
        "same_concurrency_deltas": same_concurrency_comparisons(
            discovery_aggregates, selection
        ),
        "selected_api_arm": selected_api,
        "selected_seq80_arm": seq80_arm,
        "selected_seq80_definition": (
            definitions.get(seq80_arm) if seq80_arm else None
        ),
        "discovery_selected_dep4_point": discovery_dep4_winner,
        "discovery_selected_dep8_point": discovery_dep8_winner,
        "selected_dep4_point": dep4_winner,
        "selected_dep8_point": dep8_winner,
        "selected_operating_point_deltas": relative_deltas(
            dep4_winner, dep8_winner
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--require-stage",
        choices=["api", "final"],
        help="Fail unless the stage has a qualifying selection.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_comparison(args.campaign, args.results_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    pairing_by_arm = result["dataset_pairing"]["discovery_by_arm"]
    if args.require_stage == "api" and (
        result["selected_api_arm"] is None
        or not pairing_by_arm["dep4_api2"]["complete_and_match"]
        or not pairing_by_arm["dep4_api4"]["complete_and_match"]
    ):
        raise ComparisonError(
            "API stage lacks a qualifying point or complete paired datasets"
        )
    if args.require_stage == "final" and (
        result["selected_dep4_point"] is None
        or result["selected_dep8_point"] is None
        or not (result.get("selected_dataset_pairing") or {}).get(
            "complete_and_match"
        )
    ):
        raise ComparisonError(
            "final selection or selected-arm dataset pairing is incomplete"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ComparisonError as exc:
        raise SystemExit(f"comparison error: {exc}") from exc

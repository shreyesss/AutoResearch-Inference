#!/usr/bin/env python3
"""Prepare deterministic median, burst, and cache-heavy Mooncake trace windows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import urllib.request
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAMPAIGN = ROOT / "ops_aiperf/campaign.yaml"
INPUT_BINS = (0, 512, 2048, 8192, 32768, 131072, math.inf)
OUTPUT_BINS = (0, 64, 256, 512, 1024, 2048, math.inf)


class MooncakeError(RuntimeError):
    """Raised when source or subset data is invalid."""


@dataclass(frozen=True)
class TraceRow:
    timestamp_ms: float
    input_length: int
    output_length: int
    hash_ids: tuple[str, ...]
    value: dict[str, Any]


@dataclass(frozen=True)
class Window:
    start_ms: float
    end_ms: float
    rows: tuple[TraceRow, ...]
    rps: float
    peak_1s: int
    peak_10s: int
    repeated_block_share: float
    length_distance: float
    median_score: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_campaign(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise MooncakeError(f"{path} must contain a mapping")
    return loaded


def integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MooncakeError(f"{field} must be a non-negative integer")
    return value


def load_trace(path: Path) -> list[TraceRow]:
    rows: list[TraceRow] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MooncakeError(
                    f"{path}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise MooncakeError(f"{path}:{line_number}: row must be an object")
            timestamp = value.get("timestamp")
            if (
                isinstance(timestamp, bool)
                or not isinstance(timestamp, (int, float))
                or not math.isfinite(float(timestamp))
            ):
                raise MooncakeError(
                    f"{path}:{line_number}: timestamp must be finite milliseconds"
                )
            hash_values = value.get("hash_ids") or []
            if not isinstance(hash_values, list):
                raise MooncakeError(f"{path}:{line_number}: hash_ids must be a list")
            rows.append(
                TraceRow(
                    timestamp_ms=float(timestamp),
                    input_length=integer(value.get("input_length"), "input_length"),
                    output_length=integer(value.get("output_length"), "output_length"),
                    hash_ids=tuple(str(item) for item in hash_values),
                    value=value,
                )
            )
    if not rows:
        raise MooncakeError(f"{path} contains no rows")
    rows.sort(key=lambda item: item.timestamp_ms)
    if rows[0].timestamp_ms < 0:
        raise MooncakeError("timestamps must be non-negative")
    return rows


def bin_index(value: int, bins: Sequence[float]) -> int:
    for index, upper in enumerate(bins[1:]):
        if value < upper:
            return index
    return len(bins) - 2


def length_histogram(rows: Sequence[TraceRow]) -> list[float]:
    cells = (len(INPUT_BINS) - 1) * (len(OUTPUT_BINS) - 1)
    counts = [0] * cells
    for row in rows:
        input_bin = bin_index(row.input_length, INPUT_BINS)
        output_bin = bin_index(row.output_length, OUTPUT_BINS)
        counts[input_bin * (len(OUTPUT_BINS) - 1) + output_bin] += 1
    total = max(1, len(rows))
    return [count / total for count in counts]


def total_variation(left: Sequence[float], right: Sequence[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(left, right, strict=True))


def peak_bucket_count(
    rows: Sequence[TraceRow], start_ms: float, bucket_ms: int
) -> int:
    counts: Counter[int] = Counter(
        int((row.timestamp_ms - start_ms) // bucket_ms) for row in rows
    )
    return max(counts.values(), default=0)


def repeated_block_share(rows: Sequence[TraceRow]) -> float:
    seen: set[str] = set()
    repeated = 0
    total = 0
    for row in rows:
        for block in row.hash_ids:
            total += 1
            if block in seen:
                repeated += 1
            seen.add(block)
    return repeated / total if total else 0.0


def candidate_windows(
    rows: Sequence[TraceRow],
    *,
    duration_s: int,
    minimum_requests: int,
    step_s: int = 60,
) -> list[Window]:
    duration_ms = duration_s * 1000
    start = math.floor(rows[0].timestamp_ms / (step_s * 1000)) * step_s * 1000
    final_start = rows[-1].timestamp_ms - duration_ms
    if final_start < start:
        raise MooncakeError("trace is shorter than the requested subset duration")
    boundaries: list[tuple[float, float, tuple[TraceRow, ...]]] = []
    left = 0
    right = 0
    current = start
    while current <= final_start:
        end = current + duration_ms
        while left < len(rows) and rows[left].timestamp_ms < current:
            left += 1
        right = max(right, left)
        while right < len(rows) and rows[right].timestamp_ms < end:
            right += 1
        selected = tuple(rows[left:right])
        if len(selected) >= minimum_requests:
            boundaries.append((current, end, selected))
        current += step_s * 1000
    if len(boundaries) < 3:
        raise MooncakeError(
            "fewer than three candidate windows meet the minimum request count"
        )

    rates = [len(selected) / duration_s for _, _, selected in boundaries]
    median_rate = statistics.median(rates)
    full_histogram = length_histogram(rows)
    windows: list[Window] = []
    for (window_start, window_end, selected), rate in zip(
        boundaries, rates, strict=True
    ):
        distance = total_variation(
            length_histogram(selected), full_histogram
        )
        rate_distance = abs(
            math.log((rate + 1e-12) / (median_rate + 1e-12))
        )
        windows.append(
            Window(
                start_ms=window_start,
                end_ms=window_end,
                rows=selected,
                rps=rate,
                peak_1s=peak_bucket_count(selected, window_start, 1000),
                peak_10s=peak_bucket_count(selected, window_start, 10000),
                repeated_block_share=repeated_block_share(selected),
                length_distance=distance,
                median_score=rate_distance + distance,
            )
        )
    return windows


def overlaps(left: Window, right: Window) -> bool:
    return left.start_ms < right.end_ms and right.start_ms < left.end_ms


def select_windows(windows: Sequence[Window]) -> dict[str, Window]:
    burst = max(
        windows,
        key=lambda item: (item.peak_1s, item.peak_10s, item.rps, -item.start_ms),
    )
    cache_candidates = [item for item in windows if not overlaps(item, burst)]
    if not cache_candidates:
        raise MooncakeError("cannot select a non-overlapping cache-heavy window")
    cache = max(
        cache_candidates,
        key=lambda item: (
            item.repeated_block_share,
            item.rps,
            -item.start_ms,
        ),
    )
    median_candidates = [
        item
        for item in windows
        if not overlaps(item, burst) and not overlaps(item, cache)
    ]
    if not median_candidates:
        raise MooncakeError("cannot select a non-overlapping median window")
    median = min(
        median_candidates,
        key=lambda item: (item.median_score, item.start_ms),
    )
    return {"median": median, "burst": burst, "cache-heavy": cache}


def percentile(values: Sequence[int], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def window_summary(window: Window) -> dict[str, Any]:
    inputs = [row.input_length for row in window.rows]
    outputs = [row.output_length for row in window.rows]
    return {
        "source_start_ms": window.start_ms,
        "source_end_ms": window.end_ms,
        "requests": len(window.rows),
        "request_rps": window.rps,
        "peak_requests_1s": window.peak_1s,
        "peak_requests_10s": window.peak_10s,
        "repeated_block_share": window.repeated_block_share,
        "length_distribution_distance": window.length_distance,
        "median_selection_score": window.median_score,
        "input_tokens": {
            "p50": percentile(inputs, 0.50),
            "p90": percentile(inputs, 0.90),
            "p99": percentile(inputs, 0.99),
            "mean": sum(inputs) / len(inputs),
        },
        "output_tokens": {
            "p50": percentile(outputs, 0.50),
            "p90": percentile(outputs, 0.90),
            "p99": percentile(outputs, 0.99),
            "mean": sum(outputs) / len(outputs),
        },
    }


def write_subset(path: Path, window: Window) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in window.rows:
            value = dict(row.value)
            value["timestamp"] = row.timestamp_ms - window.start_ms
            handle.write(json.dumps(value, separators=(",", ":")) + "\n")
    os.replace(temporary, path)


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open(
        "wb"
    ) as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
    os.replace(temporary, output)


def prepare(
    *,
    source: Path,
    output_root: Path,
    source_url: str,
    expected_sha256: str | None,
    duration_s: int,
    minimum_requests: int,
) -> dict[str, Any]:
    actual_source_sha256 = sha256_file(source)
    if expected_sha256 and actual_source_sha256 != expected_sha256:
        raise MooncakeError(
            f"source SHA256 {actual_source_sha256} != expected {expected_sha256}"
        )
    rows = load_trace(source)
    selected = select_windows(
        candidate_windows(
            rows,
            duration_s=duration_s,
            minimum_requests=minimum_requests,
        )
    )
    manifests: dict[str, Any] = {}
    subset_root = output_root / "subsets"
    for name, window in selected.items():
        subset_path = subset_root / f"{name}.jsonl"
        write_subset(subset_path, window)
        manifest = {
            "schema_version": 1,
            "name": name,
            "source_url": source_url,
            "source_sha256": actual_source_sha256,
            "subset_path": str(subset_path),
            "subset_sha256": sha256_file(subset_path),
            "window_duration_s": duration_s,
            **window_summary(window),
        }
        (subset_root / f"{name}.manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifests[name] = manifest
    index = {
        "schema_version": 1,
        "source_url": source_url,
        "source_path": str(source),
        "source_sha256": actual_source_sha256,
        "source_rows": len(rows),
        "window_duration_s": duration_s,
        "minimum_requests": minimum_requests,
        "subsets": manifests,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--window-duration", type=int)
    parser.add_argument("--minimum-requests", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    campaign = read_campaign(args.campaign.expanduser().resolve())
    config = campaign["production"]["mooncake"]
    data_root = (
        args.data_root
        or Path(
            os.environ.get(
                "AIPERF_DATA_ROOT",
                os.environ.get("MODEL_STORAGE_ROOT", "/models/deepseek-v4.1-flash")
                + "/datasets/aiperf",
            )
        )
    ).expanduser().resolve()
    output_root = data_root / "mooncake"
    source = (
        args.source.expanduser().resolve()
        if args.source
        else output_root / "source/mooncake_trace.jsonl"
    )
    if args.force_download and source.exists():
        source.unlink()
    if not source.is_file():
        if not args.download:
            raise MooncakeError(
                f"missing {source}; pass --download or provide --source"
            )
        download(str(config["source_url"]), source)
    index = prepare(
        source=source,
        output_root=output_root,
        source_url=str(config["source_url"]),
        expected_sha256=(
            None if args.source else str(config["source_sha256"])
        ),
        duration_s=int(
            args.window_duration or config["window_duration_s"]
        ),
        minimum_requests=int(
            args.minimum_requests or config["minimum_requests"]
        ),
    )
    print(json.dumps(index, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MooncakeError, OSError, KeyError, ValueError) as exc:
        raise SystemExit(f"error: {exc}") from exc

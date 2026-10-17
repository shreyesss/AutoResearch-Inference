#!/usr/bin/env python3
"""Derive Qwen-context-compatible Mooncake windows from pinned ops_aiperf subsets.

The source rows and their timestamps are otherwise unchanged. This is a derived
cohort and must never be reported as the original Mooncake window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def peak(rows: list[dict], bucket_ms: int) -> int:
    buckets = Counter(int(row["timestamp"] // bucket_ms) for row in rows)
    return max(buckets.values(), default=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--max-context-length", type=int, default=40960)
    parser.add_argument("--headroom-tokens", type=int, default=256)
    args = parser.parse_args()
    if args.max_context_length <= args.headroom_tokens or args.headroom_tokens < 0:
        parser.error("context length must exceed non-negative headroom")

    source_root = args.source_root.resolve() / "mooncake"
    output_root = args.output_root.resolve() / "mooncake"
    source_manifest = json.loads((source_root / "manifest.json").read_text())
    output_subsets = output_root / "subsets"
    output_subsets.mkdir(parents=True, exist_ok=True)
    budget = args.max_context_length - args.headroom_tokens
    result = {
        "schema_version": 1,
        "cohort": "qwen-context-filtered-mooncake",
        "source_manifest_sha256": sha256(source_root / "manifest.json"),
        "source_sha256": source_manifest["source_sha256"],
        "max_context_length": args.max_context_length,
        "headroom_tokens": args.headroom_tokens,
        "recorded_input_plus_output_budget": budget,
        "timestamp_policy": "preserve source offsets exactly; no rate scaling",
        "filter": "drop row only when recorded input_length + output_length exceeds budget",
        "subsets": {},
    }
    for name in ("median", "burst", "cache-heavy"):
        source = source_root / "subsets" / f"{name}.jsonl"
        expected = source_manifest["subsets"][name]["subset_sha256"]
        actual = sha256(source)
        if actual != expected:
            raise ValueError(f"{source}: SHA256 {actual} != expected {expected}")
        kept_lines: list[str] = []
        kept_rows: list[dict] = []
        dropped: list[dict] = []
        for number, line in enumerate(source.read_text().splitlines(), 1):
            row = json.loads(line)
            recorded_total = row["input_length"] + row["output_length"]
            if recorded_total > budget:
                dropped.append({
                    "source_row": number,
                    "timestamp_ms": row["timestamp"],
                    "input_length": row["input_length"],
                    "output_length": row["output_length"],
                    "reason": "recorded_context_exceeds_budget",
                })
            else:
                kept_lines.append(line)
                kept_rows.append(row)
        destination = output_subsets / f"{name}.jsonl"
        destination.write_text("\n".join(kept_lines) + "\n")
        source_count = source_manifest["subsets"][name]["requests"]
        if len(kept_rows) + len(dropped) != source_count:
            raise ValueError(f"{name}: row count differs from source manifest")
        result["subsets"][name] = {
            "source_subset_sha256": actual,
            "filtered_subset_sha256": sha256(destination),
            "source_requests": source_count,
            "kept_requests": len(kept_rows),
            "dropped_requests": len(dropped),
            "dropped_fraction": len(dropped) / source_count,
            "source_rps": source_manifest["subsets"][name]["request_rps"],
            "filtered_rps_over_600s": len(kept_rows) / 600,
            "source_peak_1s": source_manifest["subsets"][name]["peak_requests_1s"],
            "filtered_peak_1s": peak(kept_rows, 1000),
            "source_peak_10s": source_manifest["subsets"][name]["peak_requests_10s"],
            "filtered_peak_10s": peak(kept_rows, 10000),
            "max_recorded_input_plus_output": max(
                row["input_length"] + row["output_length"] for row in kept_rows
            ),
            "dropped": dropped,
        }
    (output_root / "qualification.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({name: {
        key: value for key, value in item.items() if key != "dropped"
    } for name, item in result["subsets"].items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

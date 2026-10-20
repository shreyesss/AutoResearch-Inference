#!/usr/bin/env python3
"""Prepare generated latency datasets for affinity and one-token warmup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def prepare(record: dict[str, Any], *, warmup: bool) -> dict[str, Any]:
    metadata = record.get("_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("request is missing _metadata")
    actual_isl = int(metadata.get("actual_isl") or 0)
    prefix_tokens = int(metadata.get("actual_prefix_tokens") or 0)
    metadata["target_cacheable_fraction"] = (
        prefix_tokens / actual_isl if actual_isl > 0 else 0.0
    )
    prefix_key = metadata.get("prefix_key")
    if isinstance(prefix_key, str) and prefix_key.startswith(("zipf-", "hot-")):
        case_name = str(metadata.get("case") or "case")
        affinity = f"cache-{case_name}-{prefix_key}"
        headers = record.setdefault("_headers", {})
        if not isinstance(headers, dict):
            raise ValueError("_headers must be an object")
        headers["X-Session-ID"] = affinity
        metadata["session_id"] = affinity
        metadata["X-Session-ID"] = affinity
        metadata["cache_affinity"] = "prefix-key"
    else:
        metadata["cache_affinity"] = "unique-request"
    if warmup:
        record["max_tokens"] = 1
        record["min_tokens"] = 1
        record["ignore_eos"] = True
        metadata["max_tokens"] = 1
        metadata["min_tokens"] = 1
        metadata["ignore_eos"] = True
        metadata["evidence_class"] = "cache_warmup_not_measured"
    else:
        metadata["evidence_class"] = "latency_topology_measurement"
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.input.open(encoding="utf-8") as source, args.output.open(
        "w", encoding="utf-8"
    ) as destination:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number}: request must be an object")
            destination.write(
                json.dumps(
                    prepare(value, warmup=args.warmup),
                    separators=(",", ":"),
                )
                + "\n"
            )
            count += 1
    if count == 0:
        raise ValueError("input dataset is empty")
    print(f"{count} requests -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

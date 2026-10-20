#!/usr/bin/env python3
"""Query one active or deferred experiment from the campaign manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--deferred", action="store_true")
    args = parser.parse_args()
    payload = yaml.safe_load(args.campaign.read_text(encoding="utf-8"))
    key = "deferred_experiments" if args.deferred else "experiments"
    for experiment in payload.get(key, []):
        if experiment.get("id") == args.id:
            result = dict(experiment)
            if not args.deferred:
                result["protocol"] = payload.get("active_protocol", {})
            print(json.dumps(result, sort_keys=True))
            return 0
    raise SystemExit(f"unknown {key} ID: {args.id}")


if __name__ == "__main__":
    raise SystemExit(main())

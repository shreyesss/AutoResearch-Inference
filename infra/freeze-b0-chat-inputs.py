#!/usr/bin/env python3
"""Freeze measured Qwen chat prompts into native AIPerf fixed-schedule JSONL."""

import hashlib
import json
from pathlib import Path

from aiperf.dataset.loader.models import SingleTurn


ROOT = Path(".artifacts/b0-load-curve")
TARGET = Path("infra/workloads")
CELLS = {"r256": (2.56, 154), "r32": (3.2, 192)}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    assets = {}
    for cell, (rate, count) in CELLS.items():
        raw_path = ROOT / cell / "profile_export_raw.jsonl"
        raws = [json.loads(line) for line in raw_path.read_text().splitlines() if line]
        raws.sort(key=lambda row: row["metadata"]["credit_issued_ns"])
        if len(raws) != count or any(row["status"] != 200 for row in raws):
            raise RuntimeError(f"{cell}: incomplete measured source")
        path = TARGET / f"b0-chat-{cell}.jsonl"
        with path.open("w") as handle:
            for index, raw in enumerate(raws):
                payload = raw["payload"]
                if (len(payload["messages"]) != 1 or payload["messages"][0]["role"] != "user"
                    or payload.get("max_completion_tokens") != 256 or payload.get("min_tokens") != 256
                    or payload.get("ignore_eos") is not True
                    or payload.get("temperature") != 0
                    or payload.get("chat_template_kwargs") != {"enable_thinking": False}):
                    raise RuntimeError(f"{cell}: unexpected source request body")
                record = {
                    "session_id": f"b0-{cell}-{index:04d}",
                    "timestamp": round(index * 1000 / rate, 3),
                    "text": payload["messages"][0]["content"],
                    "output_length": 256,
                    "extra": {
                        "chat_template_kwargs": {"enable_thinking": False},
                        "temperature": 0,
                        "ignore_eos": True,
                        "min_tokens": 256,
                    },
                }
                SingleTurn.model_validate(record)
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        assets[cell] = {
            "path": str(path), "sha256": sha256(path), "rows": count,
            "fixed_schedule_rate_rps": rate,
            "last_timestamp_ms": round((count - 1) * 1000 / rate, 3),
            "source_raw_sha256": sha256(raw_path),
            "format": "AIPerf single_turn JSONL with millisecond timestamps and independent sessions",
        }
    manifest = {
        "version": "b0-frozen-inputs-v1",
        "status": "schema-valid immutable inputs; see separate live replay validation record",
        "aiperf_version": "0.13.0", "model": "Qwen/Qwen3.8-27B",
        "assets": assets,
    }
    Path("infra/b0-frozen-inputs-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({name: {"rows": item["rows"], "sha256": item["sha256"]} for name, item in assets.items()}))


if __name__ == "__main__":
    main()

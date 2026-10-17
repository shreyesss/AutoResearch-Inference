#!/usr/bin/env python3
"""Fetch or verify the exact Qwen checkpoint used by the serving campaign.

This is an explicit bootstrap step, never run implicitly by an evaluator. It
does not print authentication tokens or change the campaign's model identity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MODEL = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
REQUIRED = ("config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json")


def verify(folder: Path) -> dict[str, object]:
    if not folder.is_dir():
        raise ValueError(f"model directory does not exist: {folder}")
    missing = [name for name in REQUIRED if not (folder / name).is_file()]
    if missing:
        raise ValueError(f"missing model files: {missing}")
    shards = sorted(folder.glob("*.safetensors"))
    if len(shards) != 18 or any(path.stat().st_size <= 0 for path in shards):
        raise ValueError(f"expected 18 nonempty safetensors shards; found {len(shards)}")
    index = json.loads((folder / "model.safetensors.index.json").read_text())
    indexed = set(index.get("weight_map", {}).values())
    if indexed != {path.name for path in shards}:
        raise ValueError("safetensors index and downloaded shards disagree")
    return {
        "model": MODEL,
        "revision": REVISION,
        "directory": str(folder.resolve()),
        "shards": [{"name": path.name, "bytes": path.stat().st_size} for path in shards],
        "total_shard_bytes": sum(path.stat().st_size for path in shards),
        "verification": "all indexed shards present and nonempty; content hashes supplied by pinned Hub snapshot",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".artifacts/models/Qwen3.8-27B"))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if not args.check_only:
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise SystemExit("Install huggingface_hub before downloading the model") from exc
        snapshot_download(
            repo_id=MODEL,
            revision=REVISION,
            local_dir=output,
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model", "*.tiktoken", "*.py"],
        )
    receipt = verify(output)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

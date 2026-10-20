#!/usr/bin/env python3
"""Patch AIPerf 0.13.0 workers to accept an offline local tokenizer path."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    spec = importlib.util.find_spec("aiperf.common.tokenizer")
    if spec is None or spec.origin is None:
        raise SystemExit("AIPerf tokenizer module is unavailable")
    target = Path(spec.origin)
    text = target.read_text(encoding="utf-8")
    marker = "local_path = Path(name).expanduser()"
    if marker in text:
        print(f"AIPerf local-tokenizer patch already present: {target}")
        return

    needle = '''        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError
'''
    replacement = '''        from pathlib import Path

        local_path = Path(name).expanduser()
        if local_path.is_dir():
            return str(local_path.resolve())

        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError
'''
    if needle not in text:
        raise SystemExit(
            f"unsupported AIPerf tokenizer implementation; patch marker missing in {target}"
        )
    target.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
    print(f"Patched AIPerf offline local-tokenizer support: {target}")


if __name__ == "__main__":
    main()

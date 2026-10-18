#!/usr/bin/env python3
"""Make the already persisted Codex JSONL events readable during the v4 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / ".artifacts/fast-pilot-v4"
PROPOSALS = PILOT / "proposals"


def _indented(value: object) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, indent=2, sort_keys=True)
    return "\n".join("    " + line for line in value.splitlines()) or "    (empty)"


def _atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content)
    temporary.replace(path)


def render_attempt(attempt: Path) -> dict[str, object] | None:
    source = attempt / "codex.events.jsonl"
    if not source.is_file():
        return None
    raw = source.read_bytes()
    receipt_path = attempt / "proposer-receipt.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
    lines = [f"# {attempt.name}: Codex visible trace", "",
             "This renders the saved Codex CLI event stream. The original JSONL is the complete ",
             "machine-readable record of exposed messages and tool events. Internal model reasoning ",
             "is not exposed by Codex CLI. This attempt uses a fresh, ephemeral Codex process.", "",
             f"- Model: `{receipt.get('model', 'unknown')}`",
             f"- Receipt status: `{receipt.get('status', 'unknown')}`",
             f"- Source SHA-256: `{hashlib.sha256(raw).hexdigest()}`", ""]
    event_count = 0
    thread_id = None
    for line_number, raw_line in enumerate(raw.splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            # A currently running Codex process may still be writing its last line.
            if line_number == len(raw.splitlines()):
                break
            raise
        event_count += 1
        kind = event.get("type", "unknown")
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        lines.extend([f"## {event_count}. {kind}" +
                      (f" · {item.get('type')}" if item.get("type") else ""), ""])
        if item.get("type") == "agent_message":
            lines.extend([str(item.get("text", "")), ""])
        elif item.get("type") == "command_execution":
            lines.extend(["Command:", "", _indented(item.get("command", "")), "",
                          f"Exit code: `{item.get('exit_code')}` · status: `{item.get('status')}`",
                          "", "Output:", "", _indented(item.get("aggregated_output", "")), ""])
        else:
            lines.extend([_indented(event), ""])
    trace = attempt / "codex.trace.md"
    _atomic(trace, "\n".join(lines) + "\n")
    proposal = attempt / "proposal.normalized.json"
    return {"attempt": attempt.name, "thread_id": thread_id,
            "receipt_status": receipt.get("status"), "event_count": event_count,
            "raw_events": str(source.relative_to(ROOT)),
            "readable_trace": str(trace.relative_to(ROOT)),
            "notes": str((attempt / "workspace/notes.md").relative_to(ROOT))
                     if (attempt / "workspace/notes.md").is_file() else None,
            "proposal": str(proposal.relative_to(ROOT)) if proposal.is_file() else None,
            "raw_sha256": hashlib.sha256(raw).hexdigest()}


def render_all() -> dict[str, object]:
    attempts = []
    for path in sorted(PROPOSALS.glob("attempt-*")):
        if path.is_dir():
            rendered = render_attempt(path)
            if rendered is not None:
                attempts.append(rendered)
    result = {"updated_at_utc": datetime.now(UTC).isoformat(),
              "session_model": "fresh_ephemeral_codex_process_per_proposal_with_filesystem_memory",
              "attempts": attempts}
    _atomic(PILOT / "agent-trace-index.json", json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    while True:
        result = render_all()
        print(f"rendered {len(result['attempts'])} attempts", flush=True)
        status_file = PILOT / "run-status.json"
        if not args.watch or (status_file.is_file() and
                              json.loads(status_file.read_text()).get("status") in {"complete", "blocked"}):
            return
        time.sleep(15)


if __name__ == "__main__":
    main()

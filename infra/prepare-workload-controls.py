#!/usr/bin/env python3
"""Freeze three small native AIPerf workload assets for control inspection."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(".artifacts/workload-controls")
QUAL = Path(".artifacts/dataset-qualification")
SOURCE_AUDIT = Path("infra/qualification-source-audit.json")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-trace", required=True, type=Path)
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    audit = json.loads(SOURCE_AUDIT.read_text())
    if sha256(QUAL / "tracelab-search.jsonl") != audit["tracelab"]["search"]["file_sha256"]:
        raise RuntimeError("TraceLab search file differs from frozen audit")
    if sha256(QUAL / "specbench-replay.jsonl") != audit["specbench"]["replay"]["sha256"]:
        raise RuntimeError("SpecBench replay file differs from frozen audit")
    trace_rows = read_jsonl(QUAL / "tracelab-search.jsonl")
    session_ids = {s["session_id"] for s in audit["tracelab"]["search"]["sessions"]
                   if s["rows"] == 4 and max(s["output_tokens"]) <= 128}
    candidates = [s for s in audit["tracelab"]["search"]["sessions"] if s["session_id"] in session_ids]
    chosen = min(candidates, key=lambda s: (s["peak_context"], s["session_id"]))
    selected = [row for row in trace_rows if row["session_id"] == chosen["session_id"]]
    if [row["round_index"] for row in selected] != [0, 1, 2, 3]:
        raise RuntimeError("Chosen TraceLab session is incomplete")
    trace_path = ROOT / "tracelab-four-turn.jsonl"
    trace_path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in selected))
    # Preserve JSONL row bytes for the native generator. AIPerf hashes the file
    # to scope synthesized block text, so the byte hash is part of the asset.
    moon_rows = read_jsonl(args.generated_trace)
    if len(moon_rows) != 18 or len({r["session_id"] for r in moon_rows}) != 6:
        raise RuntimeError("Expected six complete three-turn Mooncake sessions")
    if any(rows != 3 for rows in __import__("collections").Counter(r["session_id"] for r in moon_rows).values()):
        raise RuntimeError("Mooncake turn count differs from configuration")
    moon_path = ROOT / "mooncake-six-sessions.jsonl"
    moon_path.write_bytes(args.generated_trace.read_bytes())
    spec_path = ROOT / "specbench-five.jsonl"
    spec_path.write_bytes((QUAL / "specbench-replay.jsonl").read_bytes())
    def input_times(rows):
        stamps = []
        for row in rows:
            events = [e["timestamp"] for e in row.get("timing_events", [])
                      if e.get("event_type") in ("user_message", "tool_result") and e.get("timestamp")]
            stamps.append(max(events))
        from datetime import datetime
        values = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in stamps]
        return [round((x - values[0]).total_seconds() * 1000, 3) for x in values]
    groups = {}
    for row in moon_rows:
        groups.setdefault(row["session_id"], []).append(row)
    target_prompt_lengths = {}
    for sid, rows in groups.items():
        cumulative = rows[0]["input_length"]
        planned = [cumulative]
        for previous, row in zip(rows, rows[1:]):
            cumulative += previous["output_length"] + row["input_length"]
            planned.append(cumulative)
        target_prompt_lengths[sid] = planned
    manifest = {
        "version": "workload-controls-v1",
        "source_audit_sha256": sha256(SOURCE_AUDIT),
        "roles": {
            "tracelab_recorded_session": {
                "asset": str(trace_path), "sha256": sha256(trace_path),
                "source_session_id": chosen["session_id"], "rounds": 4,
                "source_input_tokens": [r["input_tokens_total"] for r in selected],
                "source_output_tokens_plus_reasoning": [(r.get("output_tokens") or 0) + (r.get("reasoning_output_tokens") or 0) for r in selected],
                "source_submission_offsets_ms": input_times(selected),
                "timing_scope": "within-session only; native loader zeros each session's first timestamp",
            },
            "mooncake_burst_diagnostic": {
                "asset": str(moon_path), "sha256": sha256(moon_path),
                "config": "infra/control-agentic-config.json", "config_sha256": sha256(Path("infra/control-agentic-config.json")),
                "seed": 42, "sessions": 6, "turns": 18, "block_size": 64,
                "first_turn_timestamp_ms": [rows[0]["timestamp"] for rows in groups.values()],
                "group_ids": [rows[0]["group_id"] for rows in groups.values()],
                "incremental_input_tokens": {sid: [row["input_length"] for row in rows] for sid, rows in groups.items()},
                "planned_cumulative_prompt_tokens": target_prompt_lengths,
                "requested_output_tokens": [row["output_length"] for row in moon_rows],
                "continuation_delays_ms": [row["delay"] for row in moon_rows if "delay" in row],
                "timing_scope": "all first turns at zero; response-relative continuation delays; synthetic assumptions",
            },
            "specbench_semantic": {
                "asset": str(spec_path), "sha256": sha256(spec_path),
                "source_question_ids": audit["specbench"]["replay"]["question_ids"],
                "requests": 5, "timing_scope": "one request/s diagnostic pacing; source has no arrival data",
            },
        },
        "load_status": "content/topology frozen for control inspection; ordinary/busy load pending B0 calibration",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"manifest": str(ROOT / "manifest.json"), "trace_session": chosen["session_id"], "mooncake_rows": len(moon_rows)}))


if __name__ == "__main__":
    main()

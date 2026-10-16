#!/usr/bin/env python3
"""Compare frozen M3 inputs with actual AIPerf request and usage exports."""

import hashlib
import json
from pathlib import Path

ROOT = Path(".artifacts/dataset-qualification")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def records(name):
    folder = ROOT / name
    raw = [json.loads(line) for line in (folder / "profile_export_raw.jsonl").open()]
    metrics = [json.loads(line) for line in (folder / "profile_export.jsonl").open()]
    by_id = {row["metadata"]["x_request_id"]: row for row in metrics}
    assert len(raw) == len(metrics) == len(by_id)
    return sorted([(r, by_id[r["metadata"]["x_request_id"]]) for r in raw],
                  key=lambda pair: pair[0]["metadata"]["request_start_ns"])


def measure(raw, metrics):
    m = raw["metadata"]
    values = metrics["metrics"]
    def metric(name):
        return values.get(name, {}).get("value")
    finish_reasons = []
    for group in raw["responses"]:
        for packet in group.get("packets", []):
            if packet.get("name") != "data" or packet.get("value") == "[DONE]":
                continue
            try:
                chunk = json.loads(packet["value"])
            except (TypeError, json.JSONDecodeError):
                continue
            finish_reasons.extend(choice["finish_reason"] for choice in chunk.get("choices", []) if choice.get("finish_reason"))
    return {
        "session_id": m["conversation_id"], "turn_index": m["turn_index"],
        "http_status": raw["status"], "stream": raw["payload"].get("stream"),
        "stream_chunk_groups": len(raw["responses"]),
        "prompt_tokens": metric("usage_prompt_tokens"),
        "completion_tokens": metric("usage_completion_tokens"),
        "finish_reason": finish_reasons[-1] if finish_reasons else None,
        "max_completion_tokens": raw["payload"].get("max_completion_tokens"),
        "message_roles": [x["role"] for x in raw["payload"]["messages"]],
        "request_start_ns": m["request_start_ns"],
        "request_end_ns": m["request_end_ns"],
    }


def main():
    audit = json.loads((ROOT / "source-audit.json").read_text())
    spec_inputs = [json.loads(line) for line in (ROOT / "specbench-replay.jsonl").open()]
    spec_records = records("specbench-replay")
    spec = []
    for expected, (raw, metrics) in zip(spec_inputs, spec_records, strict=True):
        actual = measure(raw, metrics)
        actual["source_question_id"] = int(expected["session_id"].split(":")[1])
        actual["exact_prompt_text"] = raw["payload"]["messages"] == [{"role": "user", "content": expected["text"]}]
        spec.append(actual)
    source_rows = [json.loads(line) for line in (ROOT / "tracelab-replay.jsonl").open()]
    trace_records = records("tracelab-replay")
    trace = []
    for expected, (raw, metrics) in zip(source_rows, trace_records, strict=True):
        actual = measure(raw, metrics)
        actual["source_session_id"] = expected["session_id"]
        actual["source_round_index"] = expected["round_index"]
        actual["source_input_tokens"] = expected["input_tokens_total"]
        actual["source_output_tokens_plus_reasoning"] = (expected.get("output_tokens") or 0) + (expected.get("reasoning_output_tokens") or 0)
        actual["prompt_token_delta_vs_source"] = actual["prompt_tokens"] - actual["source_input_tokens"]
        actual["source_text_status"] = "reconstructed by native TraceLab loader; original text absent"
        assert actual["turn_index"] == expected["round_index"]
        assert actual["session_id"] == expected["session_id"].replace(":", "_"), actual["session_id"]
        trace.append(actual)
    assert all(r["http_status"] == 200 and r["stream"] and r["stream_chunk_groups"] > 1 and r["prompt_tokens"] is not None and r["completion_tokens"] is not None for r in spec + trace)
    assert all(r["exact_prompt_text"] and r["max_completion_tokens"] == 128 for r in spec)
    assert [r["turn_index"] for r in trace] == list(range(len(trace)))
    assert trace[0]["session_id"] == trace[1]["session_id"]
    assert len(trace[1]["message_roles"]) > len(trace[0]["message_roles"])
    source_submissions = []
    for row in source_rows:
        stamps = [event["timestamp"] for event in row["timing_events"] if event.get("event_type") in ("user_message", "tool_result") and event.get("timestamp")]
        source_submissions.append(max(stamps))
    from datetime import datetime
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in source_submissions]
    gap_source = (times[1] - times[0]).total_seconds() * 1000
    gap_target = (trace[1]["request_start_ns"] - trace[0]["request_start_ns"]) / 1e6
    after_previous_end = (trace[1]["request_start_ns"] - trace[0]["request_end_ns"]) / 1e6
    result = {
        "status": "transport_validated",
        "scope": "five selected semantic first turns plus one two-turn TraceLab search session; no held-out replay, SLA, capacity, or production-representativeness claim",
        "source_audit_version": audit["version"],
        "source_audit_sha256": sha256(ROOT / "source-audit.json"),
        "raw_export_sha256": {name: sha256(ROOT / name / "profile_export_raw.jsonl") for name in ("specbench-replay", "tracelab-replay")},
        "metrics_export_sha256": {name: sha256(ROOT / name / "profile_export.jsonl") for name in ("specbench-replay", "tracelab-replay")},
        "semantic": spec, "tracelab": trace,
        "tracelab_timing": {"source_submission_gap_ms": gap_source, "actual_request_start_gap_ms": gap_target, "actual_next_start_after_previous_end_ms": after_previous_end, "fixed_schedule_note": "Dependencies can delay requests beyond source absolute schedule when target response duration differs."},
    }
    (ROOT / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "semantic_requests": len(spec), "trace_requests": len(trace), "source_gap_ms": gap_source, "target_gap_ms": gap_target}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Inspect intended versus actual inputs for native AIPerf control packs."""

import hashlib
import itertools
import json
import os
from pathlib import Path


ROOT = Path(".artifacts/workload-controls")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def exports(name):
    raw_path = ROOT / name / "profile_export_raw.jsonl"
    metric_path = ROOT / name / "profile_export.jsonl"
    raws = jsonl(raw_path)
    metrics = {r["metadata"]["x_request_id"]: r for r in jsonl(metric_path)}
    if len(raws) != len(metrics):
        raise RuntimeError(f"{name}: raw/metrics request count differs")
    return raws, metrics, {"raw_sha256": sha256(raw_path), "metric_sha256": sha256(metric_path)}


def observed(raw, metrics):
    m = raw["metadata"]
    values = metrics[m["x_request_id"]]["metrics"]
    def metric(key):
        return values.get(key, {}).get("value")
    finish = []
    for group in raw["responses"]:
        for packet in group.get("packets", []):
            if packet.get("name") == "data" and packet.get("value") != "[DONE]":
                try:
                    chunk = json.loads(packet["value"])
                except (ValueError, TypeError):
                    continue
                finish.extend(c["finish_reason"] for c in chunk.get("choices", []) if c.get("finish_reason"))
    return {
        "session_id": m["conversation_id"], "turn_index": m["turn_index"],
        "status": raw["status"], "stream": raw["payload"].get("stream"),
        "stream_groups": len(raw["responses"]),
        "message_roles": [item["role"] for item in raw["payload"]["messages"]],
        "max_completion_tokens": raw["payload"].get("max_completion_tokens"),
        "prompt_tokens": metric("usage_prompt_tokens"),
        "completion_tokens": metric("usage_completion_tokens"),
        "finish_reason": finish[-1] if finish else None,
        "request_start_ns": m["request_start_ns"],
        "request_end_ns": m["request_end_ns"],
    }


def main():
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    roles = manifest["roles"]
    for item in roles.values():
        if sha256(Path(item["asset"])) != item["sha256"]:
            raise RuntimeError(f"Frozen asset changed: {item['asset']}")
    trace_rows = jsonl(Path(roles["tracelab_recorded_session"]["asset"]))
    moon_rows = jsonl(Path(roles["mooncake_burst_diagnostic"]["asset"]))
    t_raw, t_metric, t_hashes = exports("tracelab-four-turn")
    m_raw, m_metric, m_hashes = exports("mooncake-six-sessions")
    if len(t_raw) != 4 or len(m_raw) != 18:
        raise RuntimeError("Incomplete replay request export")
    trace = sorted([observed(r, t_metric) for r in t_raw], key=lambda x: x["turn_index"])
    for expected, actual in zip(trace_rows, trace, strict=True):
        assert actual["session_id"] == expected["session_id"].replace(":", "_")
        assert actual["turn_index"] == expected["round_index"]
        assert actual["max_completion_tokens"] == (expected.get("output_tokens") or 0) + (expected.get("reasoning_output_tokens") or 0)
        actual["source_input_tokens"] = expected["input_tokens_total"]
        actual["source_prefix_tokens"] = expected.get("prefix_tokens")
        actual["source_prompt_delta"] = actual["prompt_tokens"] - actual["source_input_tokens"]
    source_offsets = roles["tracelab_recorded_session"]["source_submission_offsets_ms"]
    actual_offsets = [(r["request_start_ns"] - trace[0]["request_start_ns"]) / 1e6 for r in trace]
    trace_timing = [
        {"turn": i, "source_offset_ms": source_offsets[i], "actual_offset_ms": round(actual_offsets[i], 3),
         "actual_minus_source_ms": round(actual_offsets[i] - source_offsets[i], 3),
         "actual_after_previous_response_ms": round((trace[i]["request_start_ns"] - trace[i-1]["request_end_ns"]) / 1e6, 3) if i else None}
        for i in range(len(trace))
    ]
    index = {}
    for raw in m_raw:
        item = observed(raw, m_metric)
        index[(item["session_id"], item["turn_index"])] = item
    moon = []
    per_session = {}
    for expected in moon_rows:
        sid = expected["session_id"]
        turn = len(per_session.setdefault(sid, []))
        actual = index[(sid, turn)]
        assert actual["max_completion_tokens"] == expected["output_length"]
        actual["source_incremental_input_tokens"] = expected["input_length"]
        actual["planned_cumulative_prompt_tokens"] = roles["mooncake_burst_diagnostic"]["planned_cumulative_prompt_tokens"][sid][turn]
        actual["prompt_token_delta_vs_plan"] = actual["prompt_tokens"] - actual["planned_cumulative_prompt_tokens"]
        actual["source_delay_ms"] = expected.get("delay")
        if turn:
            prev = per_session[sid][-1]
            actual["actual_after_previous_response_ms"] = round((actual["request_start_ns"] - prev["request_end_ns"]) / 1e6, 3)
            actual["delay_error_ms"] = round(actual["actual_after_previous_response_ms"] - expected["delay"], 3)
            actual["realized_prompt_growth_tokens"] = actual["prompt_tokens"] - prev["prompt_tokens"]
        per_session[sid].append(actual)
        moon.append(actual)
    first_starts = [items[0]["request_start_ns"] for items in per_session.values()]
    first_rows = [rows[0] for _, group in itertools.groupby(moon_rows, key=lambda r: r["session_id"]) for rows in [list(group)]]
    same, different = [], []
    same_text, different_text = [], []
    first_content = {r["metadata"]["conversation_id"]: r["payload"]["messages"][0]["content"]
                     for r in m_raw if r["metadata"]["turn_index"] == 0}
    for a, b in itertools.combinations(first_rows, 2):
        n = 0
        for x, y in zip(a["hash_ids"], b["hash_ids"]):
            if x != y:
                break
            n += 1
        is_same = a["group_id"] == b["group_id"]
        (same if is_same else different).append(n)
        text_chars = len(os.path.commonprefix([first_content[a["session_id"]], first_content[b["session_id"]]]))
        (same_text if is_same else different_text).append(text_chars)
    assert same and different and min(same) > max(different)
    assert same_text and different_text and min(same_text) > max(different_text)
    all_requests = trace + moon
    assert all(r["status"] == 200 and r["stream"] and r["stream_groups"] > 1 and r["prompt_tokens"] is not None and r["completion_tokens"] is not None for r in all_requests)
    assert all(len(items) == 3 and [r["turn_index"] for r in items] == [0, 1, 2] for items in per_session.values())
    assert all(r["actual_after_previous_response_ms"] >= 0 for r in moon if r["turn_index"])
    prior = json.loads(Path("infra/qualification-validation.json").read_text())
    assert len(prior["semantic"]) == 5 and all(r["exact_prompt_text"] and r["http_status"] == 200 for r in prior["semantic"])
    assert sha256(Path(roles["specbench_semantic"]["asset"])) == manifest["roles"]["specbench_semantic"]["sha256"]
    result = {
        "version": "workload-controls-v1", "status": "transport_validated",
        "scope": "Recorded one-session timing and synthetic concurrent burst; no production mix, SLA, capacity or vLLM parameter comparison",
        "manifest_sha256": sha256(manifest_path),
        "semantic_reused_prior_validation": {"source": "infra/qualification-validation.json", "sha256": sha256(Path("infra/qualification-validation.json")), "requests": 5},
        "tracelab": {"request_count": len(trace), "exports": t_hashes, "requests": trace, "timing": trace_timing},
        "mooncake": {"request_count": len(moon), "exports": m_hashes, "requests": moon,
                     "first_start_spread_ms": round((max(first_starts) - min(first_starts)) / 1e6, 3),
                     "same_group_shared_first_blocks": same,
                     "different_group_shared_first_blocks": different,
                     "same_group_shared_first_chars": same_text,
                     "different_group_shared_first_chars": different_text},
    }
    (ROOT / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "trace_requests": len(trace), "mooncake_requests": len(moon), "first_start_spread_ms": result["mooncake"]["first_start_spread_ms"]}))


if __name__ == "__main__":
    main()

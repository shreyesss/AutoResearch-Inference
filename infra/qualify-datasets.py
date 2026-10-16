#!/usr/bin/env python3
"""Freeze small, source-backed AIPerf qualification inputs without a new runner."""

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def percentile(values, percent):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * percent / 100))]


def summary(values):
    return {"count": len(values), "p50": percentile(values, 50), "p90": percentile(values, 90), "p99": percentile(values, 99), "max": max(values) if values else None}


def event_time(row):
    candidates = [dt.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
                  for e in row.get("timing_events") or []
                  if e.get("event_type") in ("user_message", "tool_result") and e.get("timestamp")]
    return max(candidates) if candidates else None


def stable_rank(namespace, item):
    return hashlib.sha256(f"iar-m3-v1:{namespace}:{item}".encode()).hexdigest()


def specbench(source, target):
    rows = [json.loads(line) for line in source.read_text().splitlines() if line]
    by_category = collections.defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
    assert len(rows) == 480 and len({r["question_id"] for r in rows}) == 480
    search, evaluation = [], []
    for category, records in sorted(by_category.items()):
        ordered = sorted(records, key=lambda x: stable_rank(category, x["question_id"]))
        n_eval = len(ordered) // 5
        evaluation.extend(ordered[:n_eval])
        search.extend(ordered[n_eval:])
    search.sort(key=lambda x: x["question_id"])
    evaluation.sort(key=lambda x: x["question_id"])
    assert len(search) == 384 and len(evaluation) == 96
    assert not ({r["turns"][0] for r in search} & {r["turns"][0] for r in evaluation})
    selection = [next(r for r in search if r["category"] == c) for c in ("writing", "coding", "summarization", "rag", "math_reasoning")]
    def save_inputs(name, records):
        path = target / name
        with path.open("w") as out:
            for row in records:
                out.write(json.dumps({"text": row["turns"][0], "session_id": f"specbench:{row['question_id']}", "output_length": 128}, ensure_ascii=False) + "\n")
        return {"path": str(path), "sha256": digest(path), "question_ids": [r["question_id"] for r in records]}
    return {
        "source_sha256": digest(source), "source_rows": len(rows),
        "source_fields": sorted({key for row in rows for key in row}),
        "missing_required_fields": {key: sum(key not in row for row in rows) for key in ("question_id", "category", "turns")},
        "source_categories": {c: len(v) for c, v in sorted(by_category.items())},
        "source_turn_counts": dict(collections.Counter(len(r["turns"]) for r in rows)),
        "selection_rule": "Within each category, SHA256(iar-m3-v1:category:question_id) order; first 20% eval; remaining search. First source turn only; 128-token natural-EOS ceiling for target replay.",
        "search": save_inputs("specbench-search.jsonl", search),
        "evaluation": save_inputs("specbench-eval.jsonl", evaluation),
        "replay": save_inputs("specbench-replay.jsonl", selection),
        "missing_source_fields": ["output tokens", "arrival timestamps", "session think/tool delays", "target tokenizer counts"],
    }


def tracelab(source, target):
    sessions = {}
    row_count = 0
    joint = []
    input_lengths, output_lengths, prefix_ratios = [], [], []
    arrivals = {1: collections.Counter(), 10: collections.Counter(), 60: collections.Counter()}
    groups = collections.Counter()
    fields = collections.Counter()
    nulls = collections.Counter()
    prior_session = None
    for line in gzip.open(source, "rt"):
        row = json.loads(line)
        row_count += 1
        fields.update(row.keys())
        nulls.update(key for key, value in row.items() if value is None)
        sid = row["session_id"]
        if sid != prior_session:
            groups[sid] += 1
            prior_session = sid
        first = event_time(row)
        inp, out = int(row.get("input_tokens_total") or 0), int(row.get("output_tokens") or 0)
        input_lengths.append(inp); output_lengths.append(out)
        joint.append((inp, out))
        if inp:
            prefix_ratios.append(round((row.get("prefix_tokens") or 0) / inp, 3))
        if first:
            stamp = int(first.timestamp())
            for width in arrivals:
                arrivals[width][stamp // width] += 1
        info = sessions.setdefault(sid, {"session_id": sid, "user": row.get("user"), "project": row.get("project"), "provider": row.get("provider"), "rows": 0, "first": None, "last": None, "peak_context": 0, "rounds": [], "tool_rows": 0, "input_lengths": [], "output_lengths": [], "prefix_ratios": [], "timestamps": []})
        info["rows"] += 1
        info["peak_context"] = max(info["peak_context"], inp + out + int(row.get("reasoning_output_tokens") or 0))
        info["rounds"].append(row.get("round_index"))
        info["tool_rows"] += bool(row.get("tools"))
        info["input_lengths"].append(inp)
        info["output_lengths"].append(out)
        if inp:
            info["prefix_ratios"].append(round((row.get("prefix_tokens") or 0) / inp, 3))
        if first:
            info["timestamps"].append(first)
            info["first"] = min(info["first"], first) if info["first"] else first
            info["last"] = max(info["last"], first) if info["last"] else first
    invalid = [s for s, n in groups.items() if n > 1]
    eligible = []
    for info in sessions.values():
        if info["session_id"] in invalid or not (2 <= info["rows"] <= 5) or info["peak_context"] > 16384:
            continue
        if info["rounds"] != list(range(info["rows"])) or len(info["timestamps"]) != info["rows"]:
            continue
        gaps = [(b-a).total_seconds() for a,b in zip(info["timestamps"], info["timestamps"][1:])]
        if all(0 <= gap <= 30 for gap in gaps):
            eligible.append(info)
    # A fixed date boundary and user exclusion preserve time and identity separation.
    eligible.sort(key=lambda x: (x["first"], x["session_id"]))
    cutoff = dt.datetime(2026, 4, 1, tzinfo=dt.timezone.utc)
    search = [s for s in eligible if s["last"] < cutoff]
    search_users = {s["user"] for s in search}
    evaluation = [s for s in eligible if s["first"] >= cutoff and s["user"] not in search_users]
    if not search or not evaluation:
        raise RuntimeError("No time-separated, user-disjoint TraceLab split under bounded criteria")
    assert not ({s["user"] for s in search} & {s["user"] for s in evaluation})
    assert not ({s["project"] for s in search if s["project"]} & {s["project"] for s in evaluation if s["project"]})
    replay = min((s for s in search if s["peak_context"] <= 6000), key=lambda s: (s["peak_context"], s["first"]))
    chosen = {s["session_id"] for s in search + evaluation}
    files = {"search": target / "tracelab-search.jsonl", "evaluation": target / "tracelab-eval.jsonl", "replay": target / "tracelab-replay.jsonl"}
    handles = {k: path.open("w") for k, path in files.items()}
    try:
        for line in gzip.open(source, "rt"):
            sid = json.loads(line)["session_id"]
            if sid in chosen:
                handles["evaluation" if sid in {s["session_id"] for s in evaluation} else "search"].write(line)
                if sid == replay["session_id"]:
                    handles["replay"].write(line)
    finally:
        for handle in handles.values():
            handle.close()
    def slim(info):
        return {"session_id": info["session_id"], "user": info["user"], "project": info["project"], "provider": info["provider"], "rows": info["rows"], "first": info["first"].isoformat(), "last": info["last"].isoformat(), "peak_context": info["peak_context"], "tool_rows": info["tool_rows"], "input_tokens": info["input_lengths"], "output_tokens": info["output_lengths"], "prefix_ratio": info["prefix_ratios"]}
    def selected_stats(entries):
        inputs = [v for s in entries for v in s["input_lengths"]]
        outputs = [v for s in entries for v in s["output_lengths"]]
        gaps = [round((b-a).total_seconds(), 3) for s in entries for a,b in zip(s["timestamps"], s["timestamps"][1:])]
        growth = [b-a for s in entries for a,b in zip(s["input_lengths"], s["input_lengths"][1:])]
        return {"input_tokens": summary(inputs), "output_tokens": summary(outputs), "submission_gap_seconds": summary(gaps), "input_growth_tokens": summary(growth), "tool_rounds": sum(s["tool_rows"] for s in entries), "prefix_ratio": summary([v for s in entries for v in s["prefix_ratios"]]), "users": len({s["user"] for s in entries}), "non_null_projects": len({s["project"] for s in entries if s["project"]})}
    return {
        "source_sha256": digest(source), "source_rows": row_count, "source_session_count": len(sessions),
        "source_field_presence": dict(sorted(fields.items())),
        "source_field_nulls": dict(sorted(nulls.items())),
        "source_noncontiguous_session_ids": len(invalid),
        "source_session_turns": summary([s["rows"] for s in sessions.values()]),
        "source_tool_rounds": sum(s["tool_rows"] for s in sessions.values()),
        "source_joint_input_output_tokens": {"input": summary(input_lengths), "output": summary(output_lengths), "joint_shape_counts": {"short_input_le_2048": sum(i <= 2048 for i, _ in joint), "mid_input_2049_8192": sum(2048 < i <= 8192 for i, _ in joint), "long_input_gt_8192": sum(i > 8192 for i, _ in joint), "ongoing_decode_output_ge_256": sum(o >= 256 for _, o in joint)}},
        "source_prefix_ratio": summary(prefix_ratios),
        "source_occupied_window_arrivals": {f"{width}s": summary(list(counts.values())) for width, counts in arrivals.items()},
        "eligibility": "Complete contiguous sessions, 2-5 rounds indexed 0..n-1, peak source input+output+reasoning <=16384, every round has a dated explicit user/tool input event, each latest-input submission gap 0..30s; source timings include provider latency.",
        "eligible_sessions": len(eligible), "eligible_users": len({s["user"] for s in eligible}),
        "selection_rule": "Search sessions end before 2026-04-01 UTC. Evaluation sessions start on/after the boundary and have users absent from search. Other eligible sessions are excluded. Replay picks the search session with smallest peak context <=6000.",
        "search": {"sessions": [slim(s) for s in search], "file_sha256": digest(files["search"]), "rows": sum(s["rows"] for s in search), "statistics": selected_stats(search)},
        "evaluation": {"sessions": [slim(s) for s in evaluation], "file_sha256": digest(files["evaluation"]), "rows": sum(s["rows"] for s in evaluation), "statistics": selected_stats(evaluation)},
        "replay": {"session": slim(replay), "file_sha256": digest(files["replay"]), "rows": replay["rows"]},
        "missing_source_fields": ["original prompt/response text", "Qwen tokenization", "exact Qwen KV identity", "true human think time separate from provider service"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path(".artifacts/capability-spike"))
    parser.add_argument("--output-dir", type=Path, default=Path(".artifacts/dataset-qualification"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    expected = {
        "spec_bench_question.jsonl": "4b6d33e79484f9841c487ee87d1cf6aa8c6066f61d5d482ff09e5a007fafdf04",
        "syfi_coding_trace.jsonl.gz": "9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b",
    }
    for name, sha in expected.items():
        actual = digest(args.source_dir / name)
        if actual != sha:
            raise RuntimeError(f"{name}: SHA-256 {actual} differs from pinned {sha}")
    spec = specbench(args.source_dir / "spec_bench_question.jsonl", args.output_dir)
    trace = tracelab(args.source_dir / "syfi_coding_trace.jsonl.gz", args.output_dir)
    result = {"version": "m3-v1", "specbench": spec, "tracelab": trace}
    write_json(args.output_dir / "source-audit.json", result)
    print(json.dumps({"audit": str(args.output_dir / "source-audit.json"), "specbench_search": len(spec["search"]["question_ids"]), "specbench_eval": len(spec["evaluation"]["question_ids"]), "tracelab_search_rows": trace["search"]["rows"], "tracelab_eval_rows": trace["evaluation"]["rows"]}))


if __name__ == "__main__":
    main()

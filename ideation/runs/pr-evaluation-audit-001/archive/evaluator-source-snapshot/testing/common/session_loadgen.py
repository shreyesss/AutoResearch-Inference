#!/usr/bin/env python3
"""Closed-loop multi-turn session load for agent-style prefix-cache reuse.

Each of --concurrency workers runs one session at a time. A session starts
from a first-turn request in --dataset, then for every later turn appends the
model's actual reply and a fresh, unique tool-output message, and sends the
whole conversation again only after the previous turn finished. That is the
access pattern of long-horizon agents: every turn re-sends a growing history
whose earlier part is already in the server's prefix cache.

Only turns that complete inside [--warmup, --duration] count toward rates, so
the result reflects steady state rather than the all-turn-1 start. No new turn
starts after --duration; in-flight turns are drained and excluded.

Cached prompt tokens per turn come from usage.prompt_tokens_details, which
vLLM fills when started with --enable-prompt-tokens-details.

With --dp-ranks N, every turn of a session carries X-data-parallel-rank
(session number mod N), so a data-parallel server keeps the whole session on
one engine and its prefix cache. Without it, vLLM balances each turn by load
and later turns usually land on a rank that never saw the history.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import random
import time
from pathlib import Path
from typing import Any

import httpx

WORDS = (
    "result value table field record index status update request response error "
    "metric latency buffer cache vector matrix batch stream window offset parser "
    "config module service handler queue worker thread memory region shard "
    "partition schema column filter reduce merge branch commit revision artifact"
).split()


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def stats(values: list[float]) -> dict[str, float | None]:
    return {
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "mean": sum(values) / len(values) if values else None,
    }


def tool_text(tokens: int, seed: str) -> str:
    rng = random.Random(seed)
    words = [rng.choice(WORDS) + str(rng.randrange(1000)) for _ in range(int(tokens / 2.2))]
    return "Tool output:\n" + " ".join(words)


class Session:
    def __init__(self, args: argparse.Namespace, items: list[dict[str, Any]]) -> None:
        self.args = args
        self.items = items
        self.next_item = 0
        self.records: list[dict[str, Any]] = []
        self.sessions_completed: list[float] = []
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(args.timeout, connect=60.0),
            limits=httpx.Limits(max_connections=None, max_keepalive_connections=None),
        )
        self.endpoint = args.base_url.rstrip("/") + "/chat/completions"
        self.start = 0.0

    def elapsed(self) -> float:
        return time.monotonic() - self.start

    async def turn(
        self, body: dict[str, Any], session_id: str, turn_index: int, headers: dict[str, str]
    ) -> tuple[dict[str, Any], str]:
        record: dict[str, Any] = {"session": session_id, "turn": turn_index, "start_s": self.elapsed()}
        content: list[str] = []
        first = None
        usage: dict[str, Any] = {}
        error = None
        try:
            async with self.client.stream(
                "POST", self.endpoint, json=body, headers=headers
            ) as response:
                if response.status_code != 200:
                    error = f"http_{response.status_code}"
                    await response.aread()
                else:
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        payload = json.loads(data)
                        if payload.get("usage"):
                            usage = payload["usage"]
                        for choice in payload.get("choices") or []:
                            delta = choice.get("delta") or {}
                            text = delta.get("content") or ""
                            if (text or delta.get("reasoning_content")) and first is None:
                                first = self.elapsed()
                            if text:
                                content.append(text)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            error = type(exc).__name__
        record["end_s"] = self.elapsed()
        record["error"] = error
        record["ttft_s"] = None if first is None else first - record["start_s"]
        record["prompt_tokens"] = usage.get("prompt_tokens")
        record["completion_tokens"] = usage.get("completion_tokens")
        details = usage.get("prompt_tokens_details") or {}
        record["cached_tokens"] = details.get("cached_tokens")
        return record, "".join(content)

    async def worker(self, worker_id: int) -> None:
        args = self.args
        while self.elapsed() < args.duration:
            item = self.items[self.next_item % len(self.items)]
            session_number = self.next_item
            self.next_item += 1
            session_id = f"sess-{args.seed}-{session_number:07d}"
            body = copy.deepcopy(item)
            for key in ("_headers", "_metadata"):
                body.pop(key, None)
            body.pop("tools", None)
            body.pop("tool_choice", None)
            body["model"] = args.model
            body["stream"] = True
            body["stream_options"] = {"include_usage": True}
            headers = {"X-Session-ID": session_id}
            if args.dp_ranks:
                headers["X-data-parallel-rank"] = str(session_number % args.dp_ranks)
            previous_prompt = None
            for turn_index in range(args.turns):
                if self.elapsed() >= args.duration:
                    return
                record, reply = await self.turn(body, session_id, turn_index, headers)
                record["previous_prompt_tokens"] = previous_prompt
                self.records.append(record)
                if record["error"] is not None:
                    break
                previous_prompt = record["prompt_tokens"]
                body["messages"].append({"role": "assistant", "content": reply or "(no text)"})
                body["messages"].append(
                    {
                        "role": "user",
                        "content": tool_text(args.tool_tokens, f"{session_id}:{turn_index}")
                        + "\nContinue the task using this output.",
                    }
                )
            else:
                self.sessions_completed.append(self.elapsed())

    async def run(self) -> None:
        self.start = time.monotonic()
        await asyncio.gather(*(self.worker(index) for index in range(self.args.concurrency)))
        await self.client.aclose()


def summarize(args: argparse.Namespace, runner: Session, wall_s: float) -> dict[str, Any]:
    window = args.duration - args.warmup
    inside = [
        r for r in runner.records
        if args.warmup <= r["end_s"] <= args.duration
    ]
    ok = [r for r in inside if r["error"] is None]
    errors = [r for r in inside if r["error"] is not None]
    prompt = sum(r["prompt_tokens"] or 0 for r in ok)
    output = sum(r["completion_tokens"] or 0 for r in ok)
    cached = [r for r in ok if r["cached_tokens"] is not None]
    by_turn: dict[int, dict[str, float]] = {}
    for turn in sorted({r["turn"] for r in ok}):
        rows = [r for r in ok if r["turn"] == turn]
        prompt_turn = sum(r["prompt_tokens"] or 0 for r in rows)
        reported = [r for r in rows if r["cached_tokens"] is not None]
        cached_turn = sum(r["cached_tokens"] for r in reported)
        reported_prompt = sum(r["prompt_tokens"] or 0 for r in reported)
        ideal = sum(r["previous_prompt_tokens"] or 0 for r in rows)
        by_turn[turn] = {
            "requests": len(rows),
            "mean_prompt_tokens": prompt_turn / len(rows),
            "cached_share": cached_turn / reported_prompt if reported_prompt else None,
            "ideal_cached_share": ideal / prompt_turn if prompt_turn else None,
        }
    e2e = [r["end_s"] - r["start_s"] for r in ok]
    ttft = [r["ttft_s"] for r in ok if r["ttft_s"] is not None]
    tpot = [
        (r["end_s"] - r["start_s"] - r["ttft_s"]) / (r["completion_tokens"] - 1) * 1000
        for r in ok
        if r["ttft_s"] is not None and (r["completion_tokens"] or 0) > 1
    ]
    sessions = [t for t in runner.sessions_completed if args.warmup <= t <= args.duration]
    ideal_total = sum(r["previous_prompt_tokens"] or 0 for r in ok)
    return {
        "schema_version": 1,
        "mode": "session",
        "concurrency": args.concurrency,
        "dp_ranks": args.dp_ranks,
        "turns_per_session": args.turns,
        "tool_tokens_per_turn": args.tool_tokens,
        "duration_s": args.duration,
        "warmup_s": args.warmup,
        "wall_s": wall_s,
        "completed": len(ok),
        "errors": len(errors),
        "error_rate": len(errors) / len(inside) if inside else None,
        "request_rps": len(ok) / window,
        "sessions_completed": len(sessions),
        "sessions_per_hr": len(sessions) / window * 3600,
        "input_tps": prompt / window,
        "output_tps": output / window,
        "mean_prompt_tokens": prompt / len(ok) if ok else None,
        "mean_output_tokens": output / len(ok) if ok else None,
        "cached_share": (
            sum(r["cached_tokens"] for r in cached) / sum(r["prompt_tokens"] or 0 for r in cached)
            if cached else None
        ),
        "ideal_cached_share": ideal_total / prompt if prompt else None,
        "by_turn": by_turn,
        "ttft_ms": {k: (v * 1000 if v is not None else None) for k, v in stats(ttft).items()},
        "e2e_ms": {k: (v * 1000 if v is not None else None) for k, v in stats(e2e).items()},
        "tpot_ms": stats(tpot),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--tool-tokens", type=int, default=1500)
    parser.add_argument("--duration", type=float, default=900)
    parser.add_argument("--warmup", type=float, default=300)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--dp-ranks", type=int, default=0,
        help="pin each session to one data-parallel rank (0 = let the server balance)",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.warmup < args.duration:
        parser.error("--warmup must be in [0, --duration)")

    items = [json.loads(line) for line in args.dataset.open()]
    runner = Session(args, items)
    began = time.monotonic()
    asyncio.run(runner.run())
    summary = summarize(args, runner, time.monotonic() - began)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "requests.jsonl").open("w") as handle:
        for record in runner.records:
            handle.write(json.dumps(record) + "\n")
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in (
        "request_rps", "sessions_per_hr", "cached_share", "ideal_cached_share", "error_rate"
    )}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

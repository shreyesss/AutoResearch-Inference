"""Root-only bounded rank control and prospectively rank-pinned lifecycle.

Preserves service_lifecycle.py and its failed unpinned receipt. No service changes.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.parse import urlparse

from service_lifecycle import drain_values, parse_metrics, session_for


FINISH_REASONS = {"stop", "length", "abort", "error", "repetition"}


def success_values(backends, model):
    result = {}
    for replica, rows in enumerate(backends):
        found = {}
        for name, labels, value in rows:
            if name != "vllm:request_success_total":
                continue
            engine, reason = labels.get("engine"), labels.get("finished_reason")
            if (labels.get("model_name") != model or engine not in {"0", "1", "2", "3"}
                    or reason not in FINISH_REASONS or (engine, reason) in found
                    or not math.isfinite(value) or value < 0 or not value.is_integer()):
                raise ValueError("unexpected, duplicate, or invalid engine success counter")
            if engine != "0" and value != 0:
                raise AssertionError("terminal traffic on never-routed rank")
            found[engine, reason] = int(value)
        # Lazy absent series remain unknown. Routing/fresh ownership and the
        # independent delta gate distinguish unused ranks; no missing-as-zero.
        result[str(replica)] = {str(rank): {reason: found.get((str(rank), reason))
                               for reason in sorted(FINISH_REASONS)} for rank in range(4)}
    if set(result) != {"0", "1"}:
        raise ValueError("exactly two replicas required")
    return result


def counter_delta(before, after, *, expected, unused_rank):
    if before is None or after is None:
        if not unused_rank or expected != 0 or any(x not in (None, 0) for x in (before, after)):
            raise AssertionError("missing required terminal counter or unexpected unused-rank activity")
        return None
    delta = after - before
    if delta != expected:
        raise AssertionError(f"terminal counter delta {delta} != {expected}")
    return delta


def attest_delta(before, after, replica, rank, finish_reason=None):
    if rank != 0 or finish_reason not in FINISH_REASONS:
        raise AssertionError("native traffic adapter permits terminal requests only on rank0")
    return {str(r): {str(e): {reason: counter_delta(before[str(r)][str(e)][reason],
        after[str(r)][str(e)][reason], expected=int((r, e, reason) == (replica, rank, finish_reason)),
        unused_rank=e != 0) for reason in sorted(FINISH_REASONS)} for e in range(4)} for r in range(2)}


def generated(record):
    return (record["content"], record["reasoning"], record["usage"]["completion_tokens"], record["finish_reason"])


def reference_prompt(replica):
    return f"C03 isolated correctness marker REPLICA_{replica}. Reply with exactly the word READY."


async def run_control(h, receipt):
    for replica in range(2):
        for rank in (0, 2):
            pair = [await h.request(replica, rank, f"control-replica-{replica}-rank-{rank}-repeat-{i}",
                                    reference_prompt(replica), 64) for i in range(2)]
            receipt["pairs"].append({"replica": replica, "internal_rank": rank,
                "request_labels": [r["label"] for r in pair],
                "status": "pass" if generated(pair[0]) == generated(pair[1]) else "fail_exact_repeatability"})
    receipt["status"] = "pass" if all(p["status"] == "pass" for p in receipt["pairs"]) else "fail_exact_repeatability"


class Harness:
    def __init__(self, args, receipt, client):
        self.args, self.receipt, self.client = args, receipt, client
        self.urls = [args.base_url, *args.backend_urls]
        self.observations = args.output.with_suffix(".observations")
        self.observations.mkdir(exist_ok=False)
        self.snapshot_count = 0

    async def get_text(self, url):
        async with self.client.get(url) as response:
            if response.status != 200:
                raise AssertionError(f"read-only endpoint {url} returned {response.status}")
            return await response.text()

    async def snapshot(self, *, initial=False):
        text = await asyncio.wait_for(asyncio.gather(*(self.get_text(url + "/metrics") for url in self.urls)), 10)
        observation = {"time_unix_s": time.time(), "files": []}
        index = self.snapshot_count
        self.snapshot_count += 1
        for role, content in zip(("router", "replica-0", "replica-1"), text):
            path = self.observations / f"{index:04d}-{role}.txt"
            path.write_text(content)
            observation["files"].append({"role": role, "path": str(path),
                                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        self.receipt["observations"].append(observation)
        rows = [parse_metrics(s) for s in text]
        from native_metrics import validate_observed_metrics
        validate_observed_metrics(rows[0], rows[1:], self.args.model)
        if initial:
            from native_metrics import initial_values
            values = initial_values(rows[0], rows[1:], self.args.model)
        else:
            values = drain_values(rows[0], rows[1:])
            if set(values["request_counts"]) != {"0", "1"}:
                raise ValueError("missing router request counters")
        values["success_counts"] = success_values(rows[1:], self.args.model)
        values["observation_index"] = index
        return values

    async def drain(self, label):
        samples = []
        record = {"label": label, "status": "running", "samples": samples}
        self.receipt["drains"].append(record)
        deadline, consecutive = time.monotonic() + 60, 0
        try:
            while time.monotonic() < deadline:
                values = await asyncio.wait_for(self.snapshot(), min(10, deadline - time.monotonic()))
                samples.append(dict(time_unix_s=time.time(), **values))
                consecutive = consecutive + 1 if values["zero"] else 0
                if consecutive == 3:
                    record["status"] = "pass"
                    return values
                await asyncio.sleep(min(1, max(0, deadline - time.monotonic())))
            raise AssertionError(f"{label}: serving did not drain within60s")
        except Exception as exc:
            record.update(status="fail", error=f"{type(exc).__name__}: {exc}")
            raise

    async def request(self, replica, rank, label, prompt, limit, cancel=False):
        before = await self.snapshot()
        if not before["zero"]:
            raise AssertionError("new request attempted before strict idle state")
        session_id = session_for(replica)
        body = {"model": self.args.model, "messages": [{"role": "user", "content": prompt}],
                "stream": True, "stream_options": {"include_usage": True}, "temperature": 0,
                "seed": 731, "max_completion_tokens": limit, "ignore_eos": False}
        headers = {"X-Session-ID": session_id, "X-data-parallel-rank": str(rank)}
        record = {"replica": replica, "requested_internal_rank": rank, "label": label,
                  "session_id": session_id, "headers": headers, "body": body,
                  "started_unix_s": time.time(), "content": "", "reasoning": "", "events": [],
                  "cancelled": False, "finish_reason": None, "usage": None,
                  "before_observation_index": before["observation_index"]}
        self.receipt["requests"].append(record)
        async with self.client.post(self.args.base_url + "/v1/chat/completions", json=body, headers=headers) as response:
            record["http_status"] = response.status
            if response.status != 200:
                record["error_body"] = await response.text()
                raise AssertionError(f"{label}:HTTP{response.status}")
            data_lines, response_id, done = [], None, False
            async for raw in response.content:
                line = raw.decode("utf-8").rstrip("\r\n")
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                    continue
                if line or not data_lines:
                    continue
                data, data_lines = "\n".join(data_lines), []
                if data == "[DONE]":
                    done = True
                    break
                event = json.loads(data)
                record["events"].append(event)
                if event.get("id"):
                    if response_id is None:
                        response_id = event["id"]
                    elif event["id"] != response_id:
                        raise AssertionError("cross-request response ID within SSE stream")
                if event.get("usage"):
                    record["usage"] = event["usage"]
                for choice in event.get("choices", []):
                    if choice.get("index", 0) != 0:
                        raise AssertionError("unexpected completion choice")
                    delta = choice.get("delta", {})
                    record["content"] += delta.get("content") or ""
                    record["reasoning"] += delta.get("reasoning") or delta.get("reasoning_content") or ""
                    if choice.get("finish_reason") is not None:
                        record["finish_reason"] = choice["finish_reason"]
                if cancel and (record["content"] or record["reasoning"]) and record["finish_reason"] is None:
                    record["cancelled"], record["closed_unix_s"] = True, time.time()
                    response.close()
                    break
            record["response_id"], record["done_marker"] = response_id, done
        record["ended_unix_s"] = time.time()
        if cancel:
            if not record["cancelled"]:
                raise AssertionError("cancellation did not close an unfinished content-producing request")
        elif (not done or not response_id or record["finish_reason"] not in ("stop", "length")
              or not (record["content"] or record["reasoning"]) or not record["usage"]
              or record["usage"].get("completion_tokens", 0) <= 0):
            raise AssertionError(f"{label}: incomplete/malformed successful completion")
        after = await self.drain(label + "-drain")
        record["after_observation_index"] = after["observation_index"]
        router_delta = {str(r): after["request_counts"][str(r)] - before["request_counts"][str(r)] for r in range(2)}
        record["observed_router_request_deltas"] = router_delta
        if router_delta != {str(r): int(r == replica) for r in range(2)}:
            raise AssertionError(f"unexpected replica routing/concurrent traffic: {router_delta}")
        record["observed_engine_success_deltas"] = attest_delta(
            before["success_counts"], after["success_counts"], replica, rank,
            None if cancel else record["finish_reason"])
        record["attested_internal_rank"] = rank
        return record


async def run(args, receipt):
    import aiohttp
    if args.mode == "control" and args.arm != "A":
        raise ValueError("this bounded baseline control is authorized only for A")
    urls = [args.base_url, *args.backend_urls]
    if any(urlparse(u).hostname not in ("127.0.0.1", "localhost") or urlparse(u).scheme != "http" for u in urls):
        raise ValueError("this fixture is restricted to the authorized local node")
    if len(args.backend_urls) != 2 or len(set(args.backend_urls)) != 2:
        raise ValueError("exactly two distinct attested backend URLs are required")
    receipt["identity_receipt"] = {"path": str(args.identity),
        "sha256": hashlib.sha256(args.identity.read_bytes()).hexdigest(),
        "scope": "external root runtime-attestation linkage; worker identities not revalidated by this client"}
    if args.mode == "lifecycle":
        if args.rank_control is None:
            raise ValueError("pinned lifecycle requires the approved baseline rank-control receipt")
        control = json.loads(args.rank_control.read_text())
        if (control.get("status") != "pass" or control.get("mode") != "control" or control.get("arm") != "A"
                or len(control.get("requests", [])) != 8 or len(control.get("pairs", [])) != 4
                or any(p.get("status") != "pass" for p in control["pairs"])):
            raise ValueError("baseline rank control did not establish exact within-rank repeatability")
        receipt["baseline_rank_control"] = {"path": str(args.rank_control),
            "sha256": hashlib.sha256(args.rank_control.read_bytes()).hexdigest()}
    timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        h = Harness(args, receipt, client)
        health = json.loads(await h.get_text(args.base_url + "/health"))
        if health.get("backends") != args.backend_urls:
            raise AssertionError("router backend identity differs from attested order")
        receipt["router_health"] = health
        await h.drain("initial")
        if args.mode == "control":
            await run_control(h, receipt)
        else:
            for replica in range(2):
                prompt = reference_prompt(replica)
                reference = await h.request(replica, 0, "reference-before", prompt, 64)
                await h.request(replica, 0, "cancel-in-flight",
                    f"C03 cancellation marker REPLICA_{replica}. Write a detailed numbered list of1000different integers and explain each entry.", 4096, True)
                recovery = await h.request(replica, 0, "reference-after-cancel", prompt, 64)
                if generated(reference) != generated(recovery):
                    raise AssertionError("exact reference changed after cancellation; no tolerance")
                natural = await h.request(replica, 0, "natural-stop",
                    f"C03 natural stop marker REPLICA_{replica}. Answer only OK and finish.", 512)
                wake = await h.request(replica, 0, "reference-after-finished-wake", prompt, 64)
                if generated(reference) != generated(wake):
                    raise AssertionError("exact reference changed after finished-request drain/wake")
                receipt["replicas"].append({"replica": replica, "internal_rank": 0,
                    "cancel_and_observable_recovery": "pass", "finished_request_drain_and_wake": "pass",
                    "natural_stop": "observed" if natural["finish_reason"] == "stop" else "inconclusive_at512",
                    "exact_eos_token_id_observed": False})
            receipt["status"] = "pass" if all(r["natural_stop"] == "observed" for r in receipt["replicas"]) else "inconclusive_natural_stop"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--backend-urls", nargs=2, default=["http://127.0.0.1:8100", "http://127.0.0.1:8101"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--arm", choices=("A", "B"), required=True)
    parser.add_argument("--mode", choices=("control", "lifecycle"), required=True)
    parser.add_argument("--rank-control", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(".observations").exists():
        raise SystemExit("refusing to overwrite rank fixture evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "arm": args.arm, "mode": args.mode, "status": "running",
               "requests": [], "drains": [], "replicas": [], "pairs": [], "observations": [],
               "candidate_correctness_qualified": False,
               "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "scope": "bounded exact within-rank repeatability or rank0 observable lifecycle recovery; not all KV cells"}
    try:
        asyncio.run(run(args, receipt))
    except Exception as exc:
        receipt.update(status="fail", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        args.output.write_text(json.dumps(receipt, indent=2) + "\n")

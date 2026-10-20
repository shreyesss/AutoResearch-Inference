"""Corrected common-version root-run singleton-token integration.

Requires fresh exclusive root identity and eight restored native receipts.
The original ten requests plus six fixed all-rank primers initialize metrics; missing samples stay unknown.
Frontend cancellation is attested by one live snapshot, zero terminal-counter
changes and a separate mandatory root-collected abort-log acceptance gate.
"""
from __future__ import annotations
import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse

from service_rank_control import FINISH_REASONS, Harness, session_for, counter_delta


TOKEN_IDS = (671, 2581, 3967, 10059, 678)
CAPS = (17, 19, 23, 29, 31)
EOS_ID = 1
TOKENIZER_SHA256 = "c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b"
CONFIG_SHA256 = "8be45ce0476004a3f529fd896115a4a2e800a129ad2d3ec05b16050f52e21879"


def row_token(replica, row):
    return TOKEN_IDS[(row + replica) % len(TOKEN_IDS)]


def completion_body(model, replica, row):
    return {"model": model, "prompt": f"C03 controlled integration REPLICA_{replica} ROW_{row}.",
            "stream": True, "stream_options": {"include_usage": True},
            "return_token_ids": True, "temperature": 1.0, "top_p": 1.0, "top_k": 0,
            "seed": 731, "watermarking": True, "ignore_eos": True, "min_tokens": 0,
            "max_tokens": CAPS[row], "allowed_token_ids": [row_token(replica, row)]}


def validate_completion(record, token_id, cap, *, eos=False, cancel=False):
    """One independent expected-ID checker used by runtime and negative controls."""
    ids = record.get("token_ids")
    if (record.get("http_status") != 200 or not record.get("response_id")
            or not isinstance(ids, list) or any(type(x) is not int for x in ids)):
        raise AssertionError("invalid response identity or returned token IDs")
    if cancel:
        if (not record.get("cancelled") or record.get("finish_reason") is not None
                or record.get("done_marker") or not ids or len(ids) >= cap
                or ids != [token_id] * len(ids)):
            raise AssertionError("cancelled request lacks a valid nonempty unfinished singleton prefix")
        return
    expected_count = 1 if eos else cap
    expected_finish = "stop" if eos else "length"
    usage_count = (record.get("usage") or {}).get("completion_tokens")
    if (ids != [token_id] * expected_count or record.get("finish_reason") != expected_finish
            or not record.get("done_marker") or record.get("cancelled")
            or type(usage_count) is not int or usage_count != expected_count):
        raise AssertionError("committed IDs/count/usage/terminal reason differ from independent singleton oracle")
    if not eos:
        spec = (record.get("metrics") or {}).get("speculative_decoding")
        if (not isinstance(spec, dict) or type(spec.get("num_spec_tokens")) is not int
                or spec["num_spec_tokens"] != 5 or type(spec.get("num_spec_steps")) is not int
                or spec["num_spec_steps"] <= 0):
            raise AssertionError("completed controlled stream lacks active five-token speculative decoding evidence")


def attest_counts(before, after, replica, count, reason):
    """Batch-level observation prevents concurrent requests racing individual counters."""
    if reason == "frontend_cancel" and count != 1:
        raise AssertionError("frontend cancellation group must contain exactly one request")
    deltas = {}
    for r in range(2):
        deltas[str(r)] = {}
        for rank in range(4):
            deltas[str(r)][str(rank)] = {}
            for finish in sorted(FINISH_REASONS):
                expected = count if (reason != "frontend_cancel" and r == replica and rank == 0 and finish == reason) else 0
                deltas[str(r)][str(rank)][finish] = counter_delta(
                    before["success_counts"][str(r)][str(rank)][finish],
                    after["success_counts"][str(r)][str(rank)][finish],
                    expected=expected, unused_rank=False)
    router = {str(r): after["request_counts"][str(r)] - before["request_counts"][str(r)] for r in range(2)}
    if router != {str(r): count if r == replica else 0 for r in range(2)}:
        raise AssertionError(f"router request delta mismatch: {router}")
    return {"engine_success_deltas": deltas, "router_request_deltas": router}


def cancel_engine_witness(snapshot, replica):
    """Zero target running may be a stale gauge; never call that an attested rank."""
    witness = "missing"
    for r in range(2):
        for metric in ("vllm:num_requests_running", "vllm:num_requests_waiting"):
            values = snapshot["engines"][f"{r}:{metric}"]
            expected = {str(rank): 0 for rank in range(4)}
            if r == replica and metric.endswith("running"):
                target = values.get("0")
                if target not in (0, 1):
                    raise AssertionError("cancellation target running gauge outside {0,1}")
                expected["0"] = target
                if target == 1:
                    witness = "observed"
            if values != expected:
                raise AssertionError(f"live cancellation engine activity mismatch: {r}/{metric}")
    return witness


def validate_live_cancel_rank(snapshot, replica):
    """Exactly one snapshot while the nonterminal singleton stream is still open."""
    if snapshot["router"] != {str(r): int(r == replica) for r in range(2)}:
        raise AssertionError("live cancellation router identity/in-flight mismatch")
    return cancel_engine_witness(snapshot, replica)


class ControlledHarness(Harness):
    async def completion(self, replica, label, body, token_id, cap, *, eos=False, cancel=False, internal_rank=0):
        session = session_for(replica)
        headers = {"X-Session-ID": session, "X-data-parallel-rank": str(internal_rank)}
        record = {"replica": replica, "requested_internal_rank": internal_rank, "label": label,
                  "body": copy.deepcopy(body), "headers": headers, "session_id": session,
                  "started_unix_s": time.time(), "events": [], "token_ids": [], "text": "",
                  "prompt_token_ids": None, "response_id": None, "finish_reason": None,
                  "stop_reason": None, "usage": None, "metrics": None,
                  "cancelled": False, "done_marker": False}
        self.receipt["requests"].append(record)
        try:
            async with self.client.post(self.args.base_url + "/v1/completions", json=body, headers=headers) as response:
                record["http_status"] = response.status
                if response.status != 200:
                    record["error_body"] = await response.text()
                    raise AssertionError(f"{label}: HTTP{response.status}")
                data_lines = []
                async for raw in response.content:
                    line = raw.decode("utf-8").rstrip("\r\n")
                    if line.startswith("data:"):
                        data_lines.append(line[5:].strip())
                        continue
                    if line or not data_lines:
                        continue
                    data, data_lines = "\n".join(data_lines), []
                    if data == "[DONE]":
                        record["done_marker"] = True
                        break
                    event = json.loads(data)
                    record["events"].append(event)
                    if event.get("object") != "text_completion" or event.get("model") != self.args.model:
                        raise AssertionError("unexpected SSE object/model")
                    rid = event.get("id")
                    if not rid or (record["response_id"] is not None and rid != record["response_id"]):
                        raise AssertionError("missing/changing SSE response ID")
                    record["response_id"] = rid
                    if event.get("usage"):
                        record["usage"] = event["usage"]
                    if event.get("metrics") is not None:
                        if record["metrics"] is not None or not isinstance(event["metrics"], dict):
                            raise AssertionError("duplicate/malformed per-request metrics")
                        record["metrics"] = event["metrics"]
                    choices = event.get("choices", [])
                    if len(choices) > 1:
                        raise AssertionError("unexpected completion choices")
                    for choice in choices:
                        if choice.get("index") != 0:
                            raise AssertionError("unexpected completion choice index")
                        ids = choice.get("token_ids")
                        if not isinstance(ids, list) or any(type(x) is not int for x in ids):
                            raise AssertionError("missing/malformed returned token ID delta")
                        if record["finish_reason"] is not None and ids:
                            raise AssertionError("generated token IDs after terminal completion")
                        prompt_ids = choice.get("prompt_token_ids")
                        if prompt_ids is not None:
                            if (record["prompt_token_ids"] is not None or not isinstance(prompt_ids, list)
                                    or not prompt_ids or any(type(x) is not int for x in prompt_ids)):
                                raise AssertionError("duplicate/malformed returned prompt token IDs")
                            record["prompt_token_ids"] = prompt_ids
                        record["token_ids"].extend(ids)
                        record["text"] += choice.get("text") or ""
                        if choice.get("finish_reason") is not None:
                            if record["finish_reason"] is not None:
                                raise AssertionError("duplicate terminal completion")
                            record["finish_reason"] = choice["finish_reason"]
                            record["stop_reason"] = choice.get("stop_reason")
                    if cancel and record["token_ids"] and record["finish_reason"] is None:
                        if record["token_ids"] != [token_id] * len(record["token_ids"]) or len(record["token_ids"]) >= cap:
                            raise AssertionError("invalid singleton prefix before live cancellation observation")
                        # One bounded ordinary scrape, no polling or retry. The
                        # stream remains open until this actual-rank check passes.
                        live = await self.snapshot()
                        record["live_cancel_observation_index"] = live["observation_index"]
                        record["live_cancel_gauges"] = {"router": live["router"], "engines": live["engines"]}
                        witness = validate_live_cancel_rank(live, replica)
                        record["live_rank_witness"] = witness
                        record["attested_live_cancel_rank"] = 0 if witness == "observed" else None
                        record["cancelled"] = True
                        record["closed_unix_s"] = time.time()
                        response.close()
                        break
            if record["prompt_token_ids"] is None:
                raise AssertionError("completion omitted the requested prompt IDs")
            validate_completion(record, token_id, cap, eos=eos, cancel=cancel)
            record["independent_token_oracle"] = "pass"
            return record
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            record["ended_unix_s"] = time.time()

    async def group(self, replica, label, calls, count, reason):
        before = await self.snapshot()
        if not before["zero"]:
            raise AssertionError("request group attempted before strict idle state")
        record = {"replica": replica, "internal_rank": 0, "label": label,
                  "before_observation_index": before["observation_index"], "status": "running"}
        self.receipt["groups"].append(record)
        # Every member is awaited, even if one fails; no orphaned tasks or retries.
        results = await asyncio.gather(*(self.completion(replica, **call) for call in calls), return_exceptions=True)
        after = await self.drain(label + "-drain")
        record["after_observation_index"] = after["observation_index"]
        record.update(attest_counts(before, after, replica, count, reason))
        failures = [f"{type(x).__name__}: {x}" for x in results if isinstance(x, BaseException)]
        if failures:
            record.update(status="fail", errors=failures)
            raise AssertionError(f"{label}: request oracle failure: {failures}")
        ids = [x["response_id"] for x in results]
        earlier = [r["response_id"] for r in self.receipt["requests"] if r not in results]
        if len(ids) != len(set(ids)) or set(ids).intersection(earlier):
            raise AssertionError("response ID reused across requests")
        record.update(status="pass", response_ids=ids)
        if reason == "frontend_cancel":
            request = results[0]
            positive_indices = []
            if request["live_rank_witness"] == "observed":
                positive_indices.append(request["live_cancel_observation_index"])
            for sample in self.receipt["drains"][-1]["samples"]:
                if sample.get("status") == "not_ready":
                    continue
                if cancel_engine_witness(sample, replica) == "observed":
                    positive_indices.append(sample["observation_index"])
            record["status"] = "pending_external_abort_acceptance"
            record["terminal_counter_scope"] = "frontend disconnect path; all40 deltas must be zero, not a cancellation-rank measure"
            self.receipt["external_abort_acceptance"]["requests"].append({
                "replica": replica, "live_attested_internal_rank": request["attested_live_cancel_rank"],
                "live_rank_witness": request["live_rank_witness"],
                "positive_rank_observation_indices": positive_indices,
                "rank_acceptance": "positive_metric_witness" if positive_indices else "pending_positive_external_log_witness",
                "response_id": request["response_id"], "external_request_prefix": request["response_id"] + "-0",
                "started_unix_s": request["started_unix_s"], "closed_unix_s": request["closed_unix_s"],
                "drain_completed_unix_s": self.receipt["drains"][-1]["samples"][-1]["time_unix_s"],
                "live_observation_index": request["live_cancel_observation_index"],
                "identity_receipt_sha256": self.receipt["identity_receipt"]["sha256"]})
        return results


def file_receipt(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


async def run(args, receipt):
    import aiohttp
    urls = [args.base_url, *args.backend_urls]
    if any(urlparse(url).hostname not in ("127.0.0.1", "localhost") or urlparse(url).scheme != "http" for url in urls):
        raise ValueError("fixture restricted to the authorized local node")
    if len(args.backend_urls) != 2 or len(set(args.backend_urls)) != 2:
        raise ValueError("exactly two distinct attested backend URLs required")
    receipt["identity_receipt"] = dict(file_receipt(args.identity),
        scope="external root runtime/source/process attestation linkage; client verifies endpoint and counter identities")
    identity = json.loads(args.identity.read_text())
    if (identity.get("arm") != args.arm or identity.get("run_id") != args.run_id
            or identity.get("fresh_exclusive_service") is not True
            or identity.get("no_prior_client_requests") is not True):
        raise AssertionError("fresh exclusive root ownership/no-prior-client identity is absent")
    receipt["native_receipts"] = []
    for replica in range(2):
        for rank in range(4):
            path = args.native_observations / f"replica{replica}" / f"rank{rank}.json"
            native = json.loads(path.read_text())
            if (native.get("arm") != args.arm or native.get("run_id") != args.run_id
                    or native.get("replica") != replica or native.get("rank") != rank
                    or native.get("status") != "passed" or native.get("restored") is not True
                    or native.get("native_oracle_passed") is not True
                    or native.get("capture_attestation_passed") is not True
                    or native.get("timed_samples") != 960):
                raise AssertionError("native startup prerequisite failed")
            receipt["native_receipts"].append(file_receipt(path))
    receipt["tokenizer_snapshot"] = file_receipt(args.tokenizer_json)
    receipt["model_config"] = file_receipt(args.model_config)
    if receipt["tokenizer_snapshot"]["sha256"] != TOKENIZER_SHA256 or receipt["model_config"]["sha256"] != CONFIG_SHA256:
        raise ValueError("tokenizer/model config differs from frozen token-oracle inventory")
    if json.loads(args.model_config.read_text()).get("eos_token_id") != EOS_ID:
        raise ValueError("model EOS differs from frozen ID")
    timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        h = ControlledHarness(args, receipt, client)
        health = json.loads(await h.get_text(args.base_url + "/health"))
        if health.get("backends") != args.backend_urls:
            raise AssertionError("router backend identity differs from attested order")
        receipt["router_health"] = health
        # The fixed first five per replica initialize lazy metrics without extra
        # traffic. Initial absence is retained as unknown under fresh ownership.
        initial = await h.snapshot(initial=True)
        receipt["initial_observation"] = initial
        bodies_by_replica = [[completion_body(args.model, replica, row) for row in range(5)] for replica in range(2)]
        calls = [(replica, row) for replica in range(2) for row in range(5)]
        results = await asyncio.gather(*(h.completion(replica,
            label=f"replica-{replica}-row-{row}", body=bodies_by_replica[replica][row],
            token_id=row_token(replica, row), cap=CAPS[row]) for replica, row in calls), return_exceptions=True)
        initial_failures = [f"{type(x).__name__}: {x}" for x in results if isinstance(x, BaseException)]
        if initial_failures:
            raise AssertionError(f"initial ten token fixtures failed: {initial_failures}")
        # Mostrecent scheduler gauges require one actual scheduler-stat record
        # per engine. These six fixed primers preserve the original ten fixtures.
        primer_calls = [(replica, rank) for replica in range(2) for rank in (1, 2, 3)]
        primer_results = await asyncio.gather(*(h.completion(replica,
            label=f"replica-{replica}-rank-{rank}-metric-primer",
            body=copy.deepcopy(bodies_by_replica[replica][rank]),
            token_id=row_token(replica, rank), cap=CAPS[rank], internal_rank=rank)
            for replica, rank in primer_calls), return_exceptions=True)
        receipt["metric_primers"] = [{"replica": replica, "rank": rank,
            "label": f"replica-{replica}-rank-{rank}-metric-primer"}
            for replica, rank in primer_calls]
        after = await h.drain("initial-sixteen-requests-drain")
        from native_metrics import attest_initial_counts
        receipt["initial_counts"] = attest_initial_counts(after)
        failures = [f"{type(x).__name__}: {x}" for x in primer_results if isinstance(x, BaseException)]
        if failures:
            raise AssertionError(f"metric primer token fixtures failed: {failures}")
        receipt["groups"].append({"label": "initial-ten-concurrent", "status": "pass",
            "before_observation_index": initial["observation_index"],
            "after_observation_index": after["observation_index"],
            "response_ids": [x["response_id"] for x in results]})
        for replica in range(2):
            bodies = bodies_by_replica[replica]
            batch = results[replica*5:(replica+1)*5]
            cancel_body = copy.deepcopy(bodies[1])
            cancel_body.update(prompt=f"C03 controlled cancellation REPLICA_{replica}.", max_tokens=4096)
            await h.group(replica, f"replica-{replica}-cancel", [{
                "label": f"replica-{replica}-cancel", "body": cancel_body,
                "token_id": row_token(replica, 1), "cap": 4096, "cancel": True}], 1, "frontend_cancel")
            recovery = (await h.group(replica, f"replica-{replica}-recovery", [{
                "label": f"replica-{replica}-reference-after-cancel", "body": copy.deepcopy(bodies[0]),
                "token_id": row_token(replica, 0), "cap": CAPS[0]}], 1, "length"))[0]
            if recovery["body"] != batch[0]["body"] or recovery["prompt_token_ids"] != batch[0]["prompt_token_ids"]:
                raise AssertionError("reference replay body/prompt IDs changed")
            eos_body = copy.deepcopy(bodies[0])
            eos_body.update(prompt=f"C03 controlled EOS REPLICA_{replica}.", allowed_token_ids=[EOS_ID],
                            ignore_eos=False, min_tokens=0, max_tokens=8)
            await h.group(replica, f"replica-{replica}-eos", [{
                "label": f"replica-{replica}-eos", "body": eos_body,
                "token_id": EOS_ID, "cap": 8, "eos": True}], 1, "stop")
            wake = (await h.group(replica, f"replica-{replica}-wake", [{
                "label": f"replica-{replica}-reference-after-eos", "body": copy.deepcopy(bodies[1]),
                "token_id": row_token(replica, 1), "cap": CAPS[1]}], 1, "length"))[0]
            if wake["body"] != batch[1]["body"] or wake["prompt_token_ids"] != batch[1]["prompt_token_ids"]:
                raise AssertionError("wake reference body/prompt IDs changed")
            natural = await h.request(replica, 0, f"replica-{replica}-natural-stop",
                f"C03 natural stop marker REPLICA_{replica}. Answer only OK and finish.", 512)
            receipt["replicas"].append({"replica": replica, "internal_rank": 0,
                "controlled_committed_token_ownership": "pass", "cancel_abort_drain_recovery": "pending_external_abort_acceptance",
                "forced_eos_exact_id_and_wake": "pass",
                "unconstrained_natural_stop": "observed" if natural["finish_reason"] == "stop" else "inconclusive_at512"})
    if len(receipt["requests"]) != 26:
        raise AssertionError("fixed request inventory differs from twenty-six")
    all_ids = [r["response_id"] for r in receipt["requests"]]
    if len(all_ids) != len(set(all_ids)):
        raise AssertionError("response ID reused across controlled and unconstrained requests")
    receipt["scoped_observable_checks"] = "pass"
    receipt["status"] = "pending_external_abort_acceptance" if all(r["unconstrained_natural_stop"] == "observed" for r in receipt["replicas"]) else "inconclusive_natural_stop"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--backend-urls", nargs=2, default=["http://127.0.0.1:8100", "http://127.0.0.1:8101"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--native-observations", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tokenizer-json", type=Path, required=True)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--arm", choices=("A", "B"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(".observations").exists():
        raise SystemExit("refusing to overwrite integration evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "arm": args.arm, "status": "running", "requests": [],
               "drains": [], "replicas": [], "groups": [], "observations": [],
               "version": "c25-native-all-rank-primer-v2", "run_id": args.run_id,
               "external_abort_acceptance": {"status": "pending", "requests": [],
                   "required_evidence": "root-collected immutable per-attested-container logs: unique Added request responseID-0-internal, exact internal-ID Aborted request(s), external Request responseID-0 aborted; same API process, ordered within request/drain window allowing log second precision; positive DP0 running witness required in saved live/drain snapshots or same-container Received-counts logs during sole-request interval; none means inconclusive without rerun; independent designer acceptance required"},
               "candidate_correctness_qualified": False,
               "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "dependencies": [file_receipt(Path(__file__).with_name(name))
                                for name in ("service_rank_control.py", "service_lifecycle.py", "native_metrics.py")],
               "scope": "controlled committed token ownership, real cancellation/abort/drain, EOS stop and wake; no unconstrained equivalence, physical KV slot reuse or full KV/draft-row correctness"}
    try:
        asyncio.run(run(args, receipt))
    except Exception as exc:
        receipt.update(status="fail", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        args.output.write_text(json.dumps(receipt, indent=2) + "\n")

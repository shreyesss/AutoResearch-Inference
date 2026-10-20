#!/usr/bin/env python3
"""Engine-agnostic async load generator for OpenAI chat-completions SSE APIs."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import math
import os
import random
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

try:
    import httpx
except ImportError:
    print(
        "error: httpx is required; install requirements-tools.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


QUEUE_FLAT_LIMIT_MS_PER_S = 1.0


class LoadgenError(RuntimeError):
    """Raised for invalid inputs or an unrecoverable harness failure."""


@dataclass(frozen=True)
class DatasetItem:
    body: dict[str, Any]
    metadata: dict[str, Any]
    session_id: str | None
    dataset_index: int


@dataclass(frozen=True)
class Schedule:
    request_id: int
    item: DatasetItem
    scheduled_mono: float


@dataclass
class Activity:
    active: int = 0
    peak: int = 0
    cap_wait_count: int = 0


@dataclass(frozen=True)
class RunClock:
    mono_start: float
    wall_start: datetime

    def iso_at(self, monotonic_value: float | None) -> str | None:
        if monotonic_value is None:
            return None
        wall = self.wall_start + timedelta(seconds=monotonic_value - self.mono_start)
        return wall.isoformat().replace("+00:00", "Z")


def sanitize_error(value: str, limit: int = 600) -> str:
    compact = " ".join(value.split())
    compact = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", compact)
    compact = re.sub(
        r'(?i)(api[_-]?key|token|authorization)(["\s:=]+)[^,\s"}]+',
        r"\1\2[REDACTED]",
        compact,
    )
    return compact[:limit]


def validate_base_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise LoadgenError("--base-url must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise LoadgenError("--base-url must not contain credentials")
    if parsed.query or parsed.fragment:
        raise LoadgenError("--base-url must not contain a query string or fragment")
    clean_path = parsed.path.rstrip("/")
    public_base = urlunsplit((parsed.scheme, parsed.netloc, clean_path, "", ""))
    if clean_path.endswith("/chat/completions"):
        endpoint = public_base
    elif clean_path.endswith("/v1"):
        endpoint = public_base + "/chat/completions"
    else:
        endpoint = public_base + "/v1/chat/completions"
    return public_base, endpoint


def header_value(headers: Mapping[str, Any], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name.lower():
            if not isinstance(value, str) or not value:
                raise LoadgenError(f"{name} must be a non-empty string")
            return value
    return None


def load_dataset(path: Path) -> list[DatasetItem]:
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError as exc:
        raise LoadgenError(f"cannot open dataset {path}: {exc}") from exc

    items: list[DatasetItem] = []
    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LoadgenError(
                    f"{path}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(raw, dict):
                raise LoadgenError(f"{path}:{line_number}: record must be an object")

            if isinstance(raw.get("body"), dict):
                body = copy.deepcopy(cast(dict[str, Any], raw["body"]))
                metadata_raw = raw.get("metadata", raw.get("_metadata", {}))
                headers_raw = raw.get("headers", raw.get("_headers", {}))
            else:
                body = {
                    key: copy.deepcopy(value)
                    for key, value in raw.items()
                    if key not in {"_headers", "_metadata", "headers"}
                }
                metadata_raw = raw.get("_metadata", {})
                headers_raw = raw.get("_headers", raw.get("headers", {}))

            if not isinstance(metadata_raw, dict):
                raise LoadgenError(
                    f"{path}:{line_number}: workload metadata must be an object"
                )
            if not isinstance(headers_raw, dict):
                raise LoadgenError(
                    f"{path}:{line_number}: helper headers must be an object"
                )
            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                raise LoadgenError(
                    f"{path}:{line_number}: body.messages must be a non-empty list"
                )
            session_id = header_value(headers_raw, "X-Session-ID")
            if session_id is None:
                session_id = header_value(metadata_raw, "X-Session-ID")
            if session_id is None:
                metadata_session = metadata_raw.get("session_id")
                if isinstance(metadata_session, str) and metadata_session:
                    session_id = metadata_session
            items.append(
                DatasetItem(
                    body=body,
                    metadata=copy.deepcopy(metadata_raw),
                    session_id=session_id,
                    dataset_index=len(items),
                )
            )
    if not items:
        raise LoadgenError(f"dataset {path} contains no requests")
    return items


def usage_tokens(payload: Mapping[str, Any]) -> tuple[int | None, int | None]:
    usage = payload.get("usage")
    if not isinstance(usage, Mapping):
        return None, None

    def integer(*keys: str) -> int | None:
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return value
        return None

    return integer("prompt_tokens", "input_tokens"), integer(
        "completion_tokens", "output_tokens"
    )


def payload_has_token(payload: Mapping[str, Any]) -> bool:
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return False
    for choice in choices:
        if not isinstance(choice, Mapping):
            continue
        candidate = choice.get("delta", choice.get("message", {}))
        if not isinstance(candidate, Mapping):
            continue
        for key in ("content", "reasoning_content", "reasoning", "text"):
            value = candidate.get(key)
            if isinstance(value, str) and value:
                return True
        tool_calls = candidate.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            return True
        function_call = candidate.get("function_call")
        if isinstance(function_call, Mapping) and function_call:
            return True
    return False


def server_error(payload: Mapping[str, Any]) -> str | None:
    error = payload.get("error")
    if error is None:
        return None
    if isinstance(error, Mapping):
        message = error.get("message")
        if isinstance(message, str):
            return sanitize_error(message)
    return sanitize_error(json.dumps(error, ensure_ascii=False))


def fallback_input_tokens(metadata: Mapping[str, Any]) -> int:
    for key in ("actual_isl", "input_tokens", "target_isl"):
        value = metadata.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return 0


async def issue_request(
    schedule: Schedule,
    *,
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    mode: str,
    semaphore: asyncio.Semaphore,
    activity: Activity,
    clock: RunClock,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    waiting_for_cap = semaphore.locked()
    if mode == "open" and waiting_for_cap:
        activity.cap_wait_count += 1
    await semaphore.acquire()
    started_mono = loop.time()
    activity.active += 1
    activity.peak = max(activity.peak, activity.active)

    first_token_mono: float | None = None
    previous_chunk_mono: float | None = None
    completed_mono: float
    itl_ms: list[float] = []
    token_chunks = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    status: int | None = None
    error_type: str | None = None
    error_message: str | None = None

    body = copy.deepcopy(schedule.item.body)
    body["model"] = model
    body["stream"] = True
    stream_options = body.get("stream_options", {})
    if not isinstance(stream_options, dict):
        stream_options = {}
    stream_options["include_usage"] = True
    body["stream_options"] = stream_options
    headers: dict[str, str] = {}
    if schedule.item.session_id:
        headers["X-Session-ID"] = schedule.item.session_id

    def observe_payload(payload: Mapping[str, Any]) -> None:
        nonlocal first_token_mono
        nonlocal previous_chunk_mono
        nonlocal token_chunks
        nonlocal input_tokens
        nonlocal output_tokens
        nonlocal error_type
        nonlocal error_message

        prompt_count, completion_count = usage_tokens(payload)
        if prompt_count is not None:
            input_tokens = prompt_count
        if completion_count is not None:
            output_tokens = completion_count
        payload_error = server_error(payload)
        if payload_error is not None:
            error_type = "server_error"
            error_message = payload_error
            return
        if payload_has_token(payload):
            now = loop.time()
            if first_token_mono is None:
                first_token_mono = now
            elif previous_chunk_mono is not None:
                itl_ms.append((now - previous_chunk_mono) * 1000.0)
            previous_chunk_mono = now
            token_chunks += 1

    try:
        async with client.stream(
            "POST", endpoint, json=body, headers=headers
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                raw_error = await response.aread()
                error_type = "http_error"
                error_message = sanitize_error(
                    raw_error.decode("utf-8", errors="replace")
                    or f"HTTP status {status}"
                )
            elif "text/event-stream" not in response.headers.get(
                "content-type", ""
            ).lower():
                raw_response = await response.aread()
                try:
                    payload = json.loads(raw_response)
                except json.JSONDecodeError as exc:
                    error_type = "invalid_json_response"
                    error_message = sanitize_error(str(exc))
                else:
                    if not isinstance(payload, dict):
                        error_type = "invalid_json_response"
                        error_message = "response JSON was not an object"
                    else:
                        observe_payload(payload)
            else:
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError as exc:
                        error_type = "invalid_sse_json"
                        error_message = sanitize_error(str(exc))
                        break
                    if not isinstance(payload, dict):
                        error_type = "invalid_sse_payload"
                        error_message = "SSE data was not a JSON object"
                        break
                    observe_payload(payload)
                    if error_type is not None:
                        break
    except httpx.TimeoutException as exc:
        error_type = "timeout"
        error_message = sanitize_error(str(exc) or "request timed out")
    except httpx.RequestError as exc:
        error_type = "transport_error"
        error_message = sanitize_error(str(exc))
    except Exception as exc:  # keep one malformed request from losing the run
        error_type = "client_error"
        error_message = sanitize_error(f"{type(exc).__name__}: {exc}")
    finally:
        completed_mono = loop.time()
        activity.active -= 1
        semaphore.release()

    if error_type is None and first_token_mono is None:
        error_type = "empty_response"
        error_message = "successful response contained no output token event"
    if input_tokens is None:
        input_tokens = fallback_input_tokens(schedule.item.metadata)
        input_usage_source = "workload_metadata"
    else:
        input_usage_source = "server"
    if output_tokens is None:
        output_tokens = token_chunks
        output_usage_source = "chunk_count_estimate"
    else:
        output_usage_source = "server"

    queue_delay_ms = (started_mono - schedule.scheduled_mono) * 1000.0
    ttft_ms = (
        (first_token_mono - started_mono) * 1000.0
        if first_token_mono is not None
        else None
    )
    e2e_ms = (completed_mono - started_mono) * 1000.0
    if first_token_mono is not None and output_tokens > 1:
        tpot_ms = (
            (completed_mono - first_token_mono) * 1000.0 / (output_tokens - 1)
        )
    elif itl_ms:
        tpot_ms = sum(itl_ms) / len(itl_ms)
    else:
        tpot_ms = None
    success = error_type is None and status is not None and 200 <= status < 300
    requested_max_tokens = schedule.item.metadata.get("max_tokens")
    requested_min_tokens = schedule.item.metadata.get("min_tokens")
    ignore_eos = schedule.item.metadata.get("ignore_eos") is True

    return {
        "request_id": schedule.request_id,
        "dataset_index": schedule.item.dataset_index,
        "mode": mode,
        "session_id": schedule.item.session_id,
        "scheduled_at": clock.iso_at(schedule.scheduled_mono),
        "started_at": clock.iso_at(started_mono),
        "first_token_at": clock.iso_at(first_token_mono),
        "completed_at": clock.iso_at(completed_mono),
        "scheduled_offset_s": schedule.scheduled_mono - clock.mono_start,
        "queue_delay_ms": queue_delay_ms,
        "ttft_ms": ttft_ms,
        "tpot_ms": tpot_ms,
        "e2e_ms": e2e_ms,
        "itl_ms": itl_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "requested_max_tokens": requested_max_tokens,
        "requested_min_tokens": requested_min_tokens,
        "ignore_eos": ignore_eos,
        "input_usage_source": input_usage_source,
        "output_usage_source": output_usage_source,
        "http_status": status,
        "success": success,
        "error_type": error_type,
        "error": error_message,
        "workload": schedule.item.metadata,
    }


async def run_closed_loop(
    *,
    items: Sequence[DatasetItem],
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    concurrency: int,
    duration: float,
    max_requests: int,
    semaphore: asyncio.Semaphore,
    activity: Activity,
    clock: RunClock,
) -> tuple[list[dict[str, Any]], float]:
    loop = asyncio.get_running_loop()
    outcomes: list[dict[str, Any]] = []
    next_request_id = 0
    last_scheduled = clock.mono_start

    def reserve() -> Schedule | None:
        nonlocal next_request_id, last_scheduled
        now = loop.time()
        if duration > 0 and now - clock.mono_start >= duration:
            return None
        if max_requests > 0 and next_request_id >= max_requests:
            return None
        request_id = next_request_id
        next_request_id += 1
        last_scheduled = now
        return Schedule(
            request_id=request_id,
            item=items[request_id % len(items)],
            scheduled_mono=now,
        )

    async def worker() -> None:
        while True:
            schedule = reserve()
            if schedule is None:
                return
            outcomes.append(
                await issue_request(
                    schedule,
                    client=client,
                    endpoint=endpoint,
                    model=model,
                    mode="closed",
                    semaphore=semaphore,
                    activity=activity,
                    clock=clock,
                )
            )

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    scheduling_end = (
        min(clock.mono_start + duration, loop.time())
        if duration > 0 and (max_requests <= 0 or next_request_id < max_requests)
        else last_scheduled
    )
    return outcomes, scheduling_end


async def run_open_loop(
    *,
    items: Sequence[DatasetItem],
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    concurrency: int,
    request_rate: float,
    duration: float,
    max_requests: int,
    seed: int,
    semaphore: asyncio.Semaphore,
    activity: Activity,
    clock: RunClock,
) -> tuple[list[dict[str, Any]], float]:
    loop = asyncio.get_running_loop()
    random_source = random.Random(seed)
    tasks: list[asyncio.Task[dict[str, Any]]] = []
    arrival = clock.mono_start
    request_id = 0
    ended_by_duration = False

    while max_requests <= 0 or request_id < max_requests:
        if request_id > 0:
            arrival += random_source.expovariate(request_rate)
        if duration > 0 and arrival - clock.mono_start >= duration:
            ended_by_duration = True
            break
        delay = arrival - loop.time()
        if delay > 0:
            await asyncio.sleep(delay)
        schedule = Schedule(
            request_id=request_id,
            item=items[request_id % len(items)],
            scheduled_mono=arrival,
        )
        tasks.append(
            asyncio.create_task(
                issue_request(
                    schedule,
                    client=client,
                    endpoint=endpoint,
                    model=model,
                    mode="open",
                    semaphore=semaphore,
                    activity=activity,
                    clock=clock,
                )
            )
        )
        request_id += 1
        await asyncio.sleep(0)

    if ended_by_duration:
        deadline = clock.mono_start + duration
        if deadline > loop.time():
            await asyncio.sleep(deadline - loop.time())
        scheduling_end = deadline
    else:
        scheduling_end = loop.time()
    outcomes = await asyncio.gather(*tasks) if tasks else []
    return outcomes, scheduling_end


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def metric_summary(values: Sequence[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "mean": sum(values) / len(values) if values else None,
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
    }


def linear_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((value - x_mean) ** 2 for value in xs)
    if denominator <= 0:
        return 0.0
    return sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(xs, ys, strict=True)
    ) / denominator


def build_summary(
    *,
    outcomes: Sequence[Mapping[str, Any]],
    mode: str,
    base_url: str,
    model: str,
    concurrency: int,
    request_rate: float,
    requested_duration: float,
    run_duration: float,
    scheduling_duration: float,
    activity: Activity,
    dataset_size: int,
) -> dict[str, Any]:
    successful = [item for item in outcomes if item.get("success") is True]
    failed = [item for item in outcomes if item.get("success") is not True]
    scheduled = len(outcomes)
    completed = len(successful)
    safe_run_duration = max(run_duration, 1e-9)
    safe_scheduling_duration = max(scheduling_duration, 1e-9)

    def successful_values(key: str) -> list[float]:
        return [
            float(value)
            for item in successful
            if isinstance((value := item.get(key)), (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        ]

    queue_values = [
        float(value)
        for item in outcomes
        if isinstance((value := item.get("queue_delay_ms")), (int, float))
        and not isinstance(value, bool)
    ]
    scheduled_offsets = [
        float(item["scheduled_offset_s"])
        for item in outcomes
        if isinstance(item.get("scheduled_offset_s"), (int, float))
        and isinstance(item.get("queue_delay_ms"), (int, float))
    ]
    queue_for_slope = [
        float(item["queue_delay_ms"])
        for item in outcomes
        if isinstance(item.get("scheduled_offset_s"), (int, float))
        and isinstance(item.get("queue_delay_ms"), (int, float))
    ]
    queue_slope = linear_slope(scheduled_offsets, queue_for_slope)
    input_total = sum(
        int(item.get("input_tokens", 0))
        for item in successful
        if isinstance(item.get("input_tokens"), int)
    )
    output_total = sum(
        int(item.get("output_tokens", 0))
        for item in successful
        if isinstance(item.get("output_tokens"), int)
    )
    requested_output_values = [
        int(value)
        for item in successful
        if isinstance((value := item.get("requested_max_tokens")), int)
        and not isinstance(value, bool)
        and value > 0
    ]
    observed_output_values = [
        int(value)
        for item in successful
        if isinstance((value := item.get("output_tokens")), int)
        and not isinstance(value, bool)
        and value >= 0
    ]
    fixed_output = [
        item
        for item in successful
        if item.get("ignore_eos") is True
        or (
            isinstance(item.get("requested_min_tokens"), int)
            and item.get("requested_min_tokens") == item.get("requested_max_tokens")
        )
    ]
    fixed_output_shortfalls = [
        item
        for item in fixed_output
        if not isinstance(item.get("output_tokens"), int)
        or int(item["output_tokens"])
        < int(item.get("requested_min_tokens") or item.get("requested_max_tokens") or 0)
    ]
    server_output_usage = sum(
        1 for item in successful if item.get("output_usage_source") == "server"
    )
    status_counts = Counter(
        str(item.get("http_status"))
        if item.get("http_status") is not None
        else "transport_error"
        for item in outcomes
    )
    error_counts = Counter(
        str(item.get("error_type") or "unknown") for item in failed
    )
    concurrency_bound = mode == "open" and activity.cap_wait_count > 0
    client_limited = (
        mode == "closed"
        and scheduled >= concurrency
        and activity.peak < concurrency
    )
    return {
        "schema_version": 1,
        "mode": mode,
        "base_url": base_url,
        "model": model,
        "dataset_requests": dataset_size,
        "configured_concurrency": concurrency,
        "configured_request_rate": request_rate if mode == "open" else None,
        "requested_duration_s": requested_duration,
        "run_duration_s": run_duration,
        "scheduling_duration_s": scheduling_duration,
        "scheduled": scheduled,
        "completed": completed,
        "failed": len(failed),
        "completion_ratio": completed / scheduled if scheduled else 0.0,
        "error_rate": len(failed) / scheduled if scheduled else 0.0,
        "request_rps": completed / safe_run_duration,
        "offered_request_rps": scheduled / safe_scheduling_duration,
        "input_tokens": input_total,
        "output_tokens": output_total,
        "input_tps": input_total / safe_run_duration,
        "output_tps": output_total / safe_run_duration,
        "mean_requested_output_tokens": (
            sum(requested_output_values) / len(requested_output_values)
            if requested_output_values
            else None
        ),
        "mean_output_tokens": (
            sum(observed_output_values) / len(observed_output_values)
            if observed_output_values
            else None
        ),
        "fixed_output_requests": len(fixed_output),
        "fixed_output_shortfalls": len(fixed_output_shortfalls),
        "osl_shortfall_rate": (
            len(fixed_output_shortfalls) / len(fixed_output)
            if fixed_output
            else None
        ),
        "server_output_usage_fraction": (
            server_output_usage / completed if completed else 0.0
        ),
        "ttft_ms": metric_summary(successful_values("ttft_ms")),
        "tpot_ms": metric_summary(successful_values("tpot_ms")),
        "e2e_ms": metric_summary(successful_values("e2e_ms")),
        "queue_delay_ms": metric_summary(queue_values),
        "queue_slope_ms_per_s": queue_slope,
        "queue_flat": queue_slope <= QUEUE_FLAT_LIMIT_MS_PER_S,
        "queue_flat_limit_ms_per_s": QUEUE_FLAT_LIMIT_MS_PER_S,
        "concurrency_bound": concurrency_bound,
        "client_limited": client_limited,
        "semaphore_wait_count": activity.cap_wait_count,
        "peak_in_flight": activity.peak,
        "http_status_counts": dict(sorted(status_counts.items())),
        "error_counts": dict(sorted(error_counts.items())),
    }


async def run(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dataset_path = args.dataset.expanduser().resolve()
    items = load_dataset(dataset_path)
    public_base_url, endpoint = validate_base_url(args.base_url)
    loop = asyncio.get_running_loop()
    mono_start = loop.time()
    clock = RunClock(mono_start=mono_start, wall_start=datetime.now(UTC))
    activity = Activity()
    semaphore = asyncio.Semaphore(args.concurrency)
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=min(args.concurrency, 256),
        keepalive_expiry=30.0,
    )
    default_headers: dict[str, str] = {"Accept": "text/event-stream"}
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        default_headers["Authorization"] = f"Bearer {api_key}"
    timeout = httpx.Timeout(args.timeout)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        headers=default_headers,
        follow_redirects=False,
    ) as client:
        if args.mode == "closed":
            outcomes, scheduling_end = await run_closed_loop(
                items=items,
                client=client,
                endpoint=endpoint,
                model=args.model,
                concurrency=args.concurrency,
                duration=args.duration,
                max_requests=args.max_requests,
                semaphore=semaphore,
                activity=activity,
                clock=clock,
            )
        else:
            outcomes, scheduling_end = await run_open_loop(
                items=items,
                client=client,
                endpoint=endpoint,
                model=args.model,
                concurrency=args.concurrency,
                request_rate=args.request_rate,
                duration=args.duration,
                max_requests=args.max_requests,
                seed=args.seed,
                semaphore=semaphore,
                activity=activity,
                clock=clock,
            )
    run_end = loop.time()
    outcomes.sort(key=lambda item: int(item["request_id"]))
    summary = build_summary(
        outcomes=outcomes,
        mode=args.mode,
        base_url=public_base_url,
        model=args.model,
        concurrency=args.concurrency,
        request_rate=args.request_rate,
        requested_duration=args.duration,
        run_duration=run_end - mono_start,
        scheduling_duration=max(0.0, scheduling_end - mono_start),
        activity=activity,
        dataset_size=len(items),
    )
    summary["started_at"] = clock.iso_at(mono_start)
    summary["completed_at"] = clock.iso_at(run_end)
    return outcomes, summary


def write_results(
    output_dir: Path,
    outcomes: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        if not output_dir.is_dir():
            raise LoadgenError(f"output path {output_dir} is not a directory")
        requests_path = output_dir / "requests.jsonl"
        with requests_path.open("w", encoding="utf-8") as handle:
            for outcome in outcomes:
                json.dump(outcome, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
        with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except OSError as exc:
        raise LoadgenError(f"cannot write results under {output_dir}: {exc}") from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run closed-loop or Poisson open-loop chat-completion load."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", choices=("closed", "open"), required=True)
    parser.add_argument("--concurrency", type=int, default=64)
    parser.add_argument("--request-rate", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args(argv)
    if args.concurrency <= 0:
        parser.error("--concurrency must be positive")
    if not math.isfinite(args.request_rate) or args.request_rate <= 0:
        parser.error("--request-rate must be positive and finite")
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error("--duration must be non-negative and finite")
    if args.max_requests < 0:
        parser.error("--max-requests must be non-negative")
    if args.duration == 0 and args.max_requests == 0:
        parser.error("at least one of --duration or --max-requests must set a limit")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    outcomes, summary = asyncio.run(run(args))
    write_results(args.output_dir.expanduser().resolve(), outcomes, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if int(summary["failed"]) == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LoadgenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        sys.exit(130)

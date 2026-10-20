#!/usr/bin/env python3
"""Open streaming requests, stop after first content, and record cancellation."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import time
from pathlib import Path
from typing import Any

import httpx


def load_requests(path: Path, count: int) -> list[dict[str, Any]]:
    requests = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                continue
            item.pop("_metadata", None)
            item.pop("_headers", None)
            item["stream"] = True
            requests.append(item)
            if len(requests) >= count:
                break
    if not requests:
        raise RuntimeError("dataset contains no requests")
    return requests


async def cancel_one(
    *,
    client: httpx.AsyncClient,
    endpoint: str,
    body: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    started = time.monotonic()
    first_content = None
    error = None
    status = None
    try:
        async with semaphore:
            async with client.stream("POST", endpoint, json=body) as response:
                status = response.status_code
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:") and line[5:].strip() not in {
                        "",
                        "[DONE]",
                    }:
                        first_content = time.monotonic()
                        break
                # Leaving this context closes the stream before completion.
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    completed = time.monotonic()
    return {
        "http_status": status,
        "first_content_ms": (
            (first_content - started) * 1000
            if first_content is not None
            else None
        ),
        "closed_after_ms": (completed - started) * 1000,
        "cancelled_after_content": first_content is not None and error is None,
        "error": error,
    }


async def execute(args: argparse.Namespace) -> dict[str, Any]:
    bodies = load_requests(args.dataset, args.requests)
    endpoint = args.base_url.rstrip("/") + "/chat/completions"
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    semaphore = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient(timeout=args.timeout, limits=limits) as client:
        results = await asyncio.gather(
            *(
                cancel_one(
                    client=client,
                    endpoint=endpoint,
                    body=copy.deepcopy(body),
                    semaphore=semaphore,
                )
                for body in bodies
            )
        )
    cancelled = sum(
        result["cancelled_after_content"] is True for result in results
    )
    return {
        "schema_version": 1,
        "requested": len(bodies),
        "concurrency": args.concurrency,
        "cancelled_after_content": cancelled,
        "errors": len(bodies) - cancelled,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--requests", type=int, default=64)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0:
        parser.error("--requests and --concurrency must be positive")
    result = asyncio.run(execute(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: result[key] for key in result if key != "results"}))
    return 0 if result["cancelled_after_content"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import math
import os
from collections import Counter

from aiohttp import (
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TCPConnector,
    web,
)

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class Router:
    def __init__(self, backends: list[str]) -> None:
        if not backends:
            raise ValueError("at least one backend is required")
        self.backends = [value.rstrip("/") for value in backends]
        self.round_robin = itertools.cycle(range(len(backends)))
        self.counts: Counter[str] = Counter()
        self.in_flight = [0 for _ in backends]
        load_factor = os.environ.get("DSV41_ROUTER_LOAD_FACTOR", "").strip()
        self.load_factor = float(load_factor) if load_factor else None
        if self.load_factor is not None and self.load_factor < 1.0:
            raise ValueError("DSV41_ROUTER_LOAD_FACTOR must be at least 1.0")
        self.connection_limit = int(
            os.environ.get("DSV41_ROUTER_CONNECTION_LIMIT", "100")
        )
        if self.connection_limit < 0:
            raise ValueError("DSV41_ROUTER_CONNECTION_LIMIT cannot be negative")
        self.retry_connection_errors = (
            os.environ.get("DSV41_ROUTER_RETRY_CONNECTION_ERRORS", "0") == "1"
        )
        self.session: ClientSession | None = None

    async def start(self, _: web.Application) -> None:
        connector = TCPConnector(
            limit=self.connection_limit,
            enable_cleanup_closed=True,
        )
        self.session = ClientSession(
            timeout=ClientTimeout(total=None, connect=30),
            connector=connector,
        )

    async def stop(self, _: web.Application) -> None:
        if self.session:
            await self.session.close()

    def select(self, request: web.Request) -> tuple[int, str]:
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            digest = hashlib.sha256(session_id.encode()).digest()
            home = int.from_bytes(digest[:8], "big") % len(self.backends)
            if self.load_factor is not None and len(self.backends) > 1:
                # Consistent hashing with bounded loads. Keep affinity while
                # the home rank is below load_factor × node-average active
                # requests, then spill to the least-loaded rank. Including
                # the request being assigned gives a usable bound at startup.
                average = max(
                    1.0,
                    (sum(self.in_flight) + 1) / len(self.backends),
                )
                bound = math.ceil(self.load_factor * average)
                if self.in_flight[home] >= bound:
                    index = min(
                        range(len(self.backends)),
                        key=lambda candidate: (
                            self.in_flight[candidate],
                            (candidate - home) % len(self.backends),
                        ),
                    )
                    if index != home:
                        return index, "sticky_bounded"
            return home, "sticky"
        return next(self.round_robin), "round_robin"

    def reserve(self, request: web.Request) -> tuple[int, str]:
        """Select and reserve a backend without yielding the event loop."""
        index, policy = self.select(request)
        self.in_flight[index] += 1
        return index, policy

    def release(self, index: int) -> None:
        if self.in_flight[index] <= 0:
            raise RuntimeError(f"backend {index} has no in-flight reservation")
        self.in_flight[index] -= 1

    async def upstream_request(
        self,
        method: str,
        target: str,
        body: bytes,
        headers: dict[str, str],
    ) -> ClientResponse:
        if self.session is None:
            raise web.HTTPServiceUnavailable(text="router not ready")
        attempts = 2 if self.retry_connection_errors else 1
        for attempt in range(attempts):
            try:
                return await self.session.request(
                    method,
                    target,
                    data=body,
                    headers=headers,
                )
            except ClientConnectorError:
                if attempt + 1 >= attempts:
                    raise
                self.counts["upstream_connection_retries"] += 1
        raise RuntimeError("unreachable connection-retry state")

    async def proxy(self, request: web.Request) -> web.StreamResponse:
        if self.session is None:
            raise web.HTTPServiceUnavailable(text="router not ready")
        index, policy = self.reserve(request)
        backend = self.backends[index]
        target = f"{backend}{request.rel_url}"
        try:
            body = await request.read()
            headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in HOP_BY_HOP and key.lower() != "host"
            }
            self.counts[f"requests_backend_{index}"] += 1
            self.counts[f"requests_policy_{policy}"] += 1
            upstream = await self.upstream_request(
                request.method,
                target,
                body,
                headers,
            )
            try:
                response_headers = {
                    key: value
                    for key, value in upstream.headers.items()
                    if key.lower() not in HOP_BY_HOP
                }
                response = web.StreamResponse(
                    status=upstream.status, headers=response_headers
                )
                await response.prepare(request)
                async for chunk in upstream.content.iter_any():
                    await response.write(chunk)
                await response.write_eof()
                if upstream.status >= 400:
                    self.counts[f"errors_backend_{index}"] += 1
                return response
            finally:
                upstream.release()
        except Exception as exc:
            self.counts[f"errors_backend_{index}"] += 1
            raise web.HTTPBadGateway(text=str(exc)) from exc
        finally:
            self.release(index)

    async def health(self, _: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ok",
                "backends": self.backends,
                "in_flight": self.in_flight,
                "load_factor": self.load_factor,
                "connection_limit": self.connection_limit,
                "retry_connection_errors": self.retry_connection_errors,
            }
        )

    async def metrics(self, _: web.Request) -> web.Response:
        lines = [
            "# TYPE dsv41_router_requests_total counter",
            *(
                f'dsv41_router_requests_total{{kind="{key}"}} {value}'
                for key, value in sorted(self.counts.items())
            ),
            "# TYPE dsv41_router_in_flight gauge",
            *(
                f'dsv41_router_in_flight{{backend="{index}"}} {value}'
                for index, value in enumerate(self.in_flight)
            ),
        ]
        return web.Response(text="\n".join(lines) + "\n", content_type="text/plain")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--backends", nargs="+", required=True)
    args = parser.parse_args()

    router = Router(args.backends)
    app = web.Application(client_max_size=256 * 1024**2)
    app.on_startup.append(router.start)
    app.on_cleanup.append(router.stop)
    app.router.add_get("/health", router.health)
    app.router.add_get("/metrics", router.metrics)
    app.router.add_route("*", "/{path:.*}", router.proxy)
    web.run_app(app, host=args.host, port=args.port, handle_signals=True)


if __name__ == "__main__":
    main()

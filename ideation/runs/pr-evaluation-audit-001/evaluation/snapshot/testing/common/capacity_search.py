#!/usr/bin/env python3
"""Two-stage closed/open-loop capacity search using the native load generator."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

SCREEN_RATIOS = (0.10, 0.25, 0.50, 0.70, 0.85, 0.95, 1.05)
MIN_COMPLETION_RATIO = 0.995
MIN_GAIN = 0.03
BISECTION_WIDTH = 0.05


class SearchError(RuntimeError):
    """Raised for invalid search input or an unrecoverable subprocess failure."""


def finite_number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SearchError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise SearchError(f"{field} must be finite and at least {minimum}")
    return result


def parse_concurrencies(value: str) -> list[int]:
    values: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            concurrency = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"invalid concurrency {raw!r}"
            ) from exc
        if concurrency <= 0:
            raise argparse.ArgumentTypeError("concurrencies must be positive")
        values.append(concurrency)
    if not values:
        raise argparse.ArgumentTypeError("at least one concurrency is required")
    if values != sorted(set(values)):
        raise argparse.ArgumentTypeError(
            "concurrencies must be unique and increasing"
        )
    return values


def sanitize_process_error(value: str, limit: int = 500) -> str:
    return " ".join(value.split())[:limit]


def nested_number(
    summary: Mapping[str, Any], group: str, key: str
) -> float | None:
    value = summary.get(group)
    if not isinstance(value, Mapping):
        return None
    metric = value.get(key)
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        result = float(metric)
        return result if math.isfinite(result) else None
    return None


def scalar_number(summary: Mapping[str, Any], key: str) -> float | None:
    value = summary.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) else None
    return None


class CapacitySearch:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.results = args.results.expanduser().resolve()
        self.runs_dir = self.results / "runs"
        self.loadgen = Path(__file__).with_name("loadgen.py").resolve()
        self.run_references: list[dict[str, Any]] = []
        self.run_summaries: dict[str, dict[str, Any]] = {}
        self.observations: dict[float, list[dict[str, Any]]] = {}
        self.run_counter = 0
        self.stage_a_refs: list[dict[str, Any]] = []
        self.stage_b_refs: list[dict[str, Any]] = []
        self.throughput_refs: list[dict[str, Any]] = []

    def _classify(
        self, summary: Mapping[str, Any], *, open_loop: bool
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        completion = scalar_number(summary, "completion_ratio")
        error_rate = scalar_number(summary, "error_rate")
        ttft_p95 = nested_number(summary, "ttft_ms", "p95")
        tpot_p95 = nested_number(summary, "tpot_ms", "p95")
        output_tokens = scalar_number(summary, "output_tokens") or 0.0
        completed = scalar_number(summary, "completed") or 0.0

        if completion is None or completion < MIN_COMPLETION_RATIO:
            reasons.append(
                f"completion ratio {completion!r} is below {MIN_COMPLETION_RATIO}"
            )
        if error_rate is None or error_rate > self.args.slo_error_rate:
            reasons.append(
                f"error rate {error_rate!r} exceeds {self.args.slo_error_rate}"
            )
        if ttft_p95 is None or ttft_p95 > self.args.slo_ttft_p95_ms:
            reasons.append(
                f"TTFT p95 {ttft_p95!r} ms exceeds "
                f"{self.args.slo_ttft_p95_ms} ms"
            )
        # One-token prefill probes have no meaningful TPOT sample.
        if output_tokens > completed and (
            tpot_p95 is None or tpot_p95 > self.args.slo_tpot_p95_ms
        ):
            reasons.append(
                f"TPOT p95 {tpot_p95!r} ms exceeds "
                f"{self.args.slo_tpot_p95_ms} ms"
            )
        if open_loop:
            queue_slope = scalar_number(summary, "queue_slope_ms_per_s")
            if queue_slope is None or queue_slope > self.args.queue_slope_ms_per_s:
                reasons.append(
                    f"queue slope {queue_slope!r} ms/s exceeds "
                    f"{self.args.queue_slope_ms_per_s} ms/s"
                )
            if summary.get("concurrency_bound") is True:
                reasons.append("open-loop safety semaphore was binding")
        return not reasons, reasons

    def _latency_evidence(self, summary: Mapping[str, Any]) -> dict[str, Any]:
        ttft_p95 = nested_number(summary, "ttft_ms", "p95")
        tpot_p95 = nested_number(summary, "tpot_ms", "p95")
        e2e_p95 = nested_number(summary, "e2e_ms", "p95")
        would_fail: list[str] = []
        if ttft_p95 is None or ttft_p95 > self.args.slo_ttft_p95_ms:
            would_fail.append("ttft_p95")
        output_tokens = scalar_number(summary, "output_tokens") or 0.0
        completed = scalar_number(summary, "completed") or 0.0
        if output_tokens > completed and (
            tpot_p95 is None or tpot_p95 > self.args.slo_tpot_p95_ms
        ):
            would_fail.append("tpot_p95")
        return {
            "ttft_p95_ms": ttft_p95,
            "tpot_p95_ms": tpot_p95,
            "e2e_p95_ms": e2e_p95,
            "would_fail_slo": would_fail,
        }

    def _classify_offline(
        self, summary: Mapping[str, Any]
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        completion = scalar_number(summary, "completion_ratio")
        error_rate = scalar_number(summary, "error_rate")
        output_tps = scalar_number(summary, "output_tps")
        fixed_output_requests = scalar_number(summary, "fixed_output_requests")
        shortfall_rate = scalar_number(summary, "osl_shortfall_rate")
        server_usage_fraction = scalar_number(
            summary, "server_output_usage_fraction"
        )
        if (
            completion is None
            or completion < self.args.minimum_completion_ratio
        ):
            reasons.append(
                f"completion ratio {completion!r} is below "
                f"{self.args.minimum_completion_ratio}"
            )
        if error_rate is None or error_rate > self.args.maximum_error_rate:
            reasons.append(
                f"error rate {error_rate!r} exceeds "
                f"{self.args.maximum_error_rate}"
            )
        if output_tps is None or output_tps <= 0:
            reasons.append("run reported no positive output token throughput")
        if fixed_output_requests is None or fixed_output_requests <= 0:
            reasons.append("offline throughput requires fixed-output requests")
        if (
            shortfall_rate is None
            or shortfall_rate > self.args.maximum_osl_shortfall_rate
        ):
            reasons.append(
                f"OSL shortfall rate {shortfall_rate!r} exceeds "
                f"{self.args.maximum_osl_shortfall_rate}"
            )
        if (
            server_usage_fraction is None
            or server_usage_fraction < self.args.minimum_server_usage_fraction
        ):
            reasons.append(
                f"server output usage fraction {server_usage_fraction!r} is below "
                f"{self.args.minimum_server_usage_fraction}"
            )
        if summary.get("client_limited") is True:
            reasons.append("closed-loop client did not sustain configured concurrency")
        return not reasons, reasons

    def _run_once(
        self,
        *,
        stage: str,
        mode: str,
        duration: float,
        concurrency: int,
        request_rate: float | None = None,
        repetition: int = 1,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        self.run_counter += 1
        rate_label = (
            f"-r{request_rate:.4f}".replace(".", "_")
            if request_rate is not None
            else ""
        )
        run_id = (
            f"{self.run_counter:03d}-stage-{stage.lower()}-{mode}"
            f"-c{concurrency}{rate_label}-rep{repetition}"
        )
        output_dir = self.runs_dir / run_id
        command = [
            sys.executable,
            str(self.loadgen),
            "--dataset",
            str(self.args.dataset.expanduser().resolve()),
            "--base-url",
            self.args.base_url,
            "--model",
            self.args.model,
            "--mode",
            mode,
            "--concurrency",
            str(concurrency),
            "--duration",
            str(duration),
            "--max-requests",
            str(self.args.max_requests),
            "--output-dir",
            str(output_dir),
            "--timeout",
            str(self.args.timeout),
            "--seed",
            str(self.args.seed + self.run_counter),
        ]
        if request_rate is not None:
            command.extend(["--request-rate", f"{request_rate:.9g}"])

        process_error: str | None = None
        return_code: int | None = None
        try:
            completed_process = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=max(120.0, duration + 2.0 * self.args.timeout + 90.0),
            )
            return_code = completed_process.returncode
            if return_code not in {0, 1}:
                process_error = sanitize_process_error(
                    completed_process.stderr or completed_process.stdout
                )
        except subprocess.TimeoutExpired:
            process_error = "load generator subprocess exceeded its safety timeout"
        except OSError as exc:
            process_error = sanitize_process_error(str(exc))

        summary_path = output_dir / "summary.json"
        summary: dict[str, Any] | None = None
        if process_error is None:
            try:
                loaded = json.loads(summary_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("summary root is not an object")
                summary = cast(dict[str, Any], loaded)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                process_error = f"cannot read run summary: {sanitize_process_error(str(exc))}"

        if summary is None:
            passed = False
            reasons = [process_error or "load generator did not produce a summary"]
            latency_evidence = None
        else:
            latency_evidence = self._latency_evidence(summary)
            if self.args.search_mode == "offline-throughput":
                passed, reasons = self._classify_offline(summary)
            else:
                passed, reasons = self._classify(
                    summary, open_loop=mode == "open"
                )
        reference: dict[str, Any] = {
            "id": run_id,
            "stage": stage,
            "mode": mode,
            "concurrency": concurrency,
            "request_rate": request_rate,
            "duration_s": duration,
            "repetition": repetition,
            "output_dir": str(output_dir.relative_to(self.results)),
            "summary": str(summary_path.relative_to(self.results)),
            "return_code": return_code,
            "valid": summary is not None,
            "pass": passed,
            "reasons": reasons,
            "request_rps": None
            if summary is None
            else scalar_number(summary, "request_rps"),
            "output_tps": None
            if summary is None
            else scalar_number(summary, "output_tps"),
            "latency_evidence": latency_evidence,
        }
        self.run_references.append(reference)
        if stage == "A":
            self.stage_a_refs.append(reference)
        elif stage == "B":
            self.stage_b_refs.append(reference)
        else:
            self.throughput_refs.append(reference)
        if summary is not None:
            self.run_summaries[run_id] = summary
        return reference, summary

    def stage_a(self) -> tuple[float, int | None, str]:
        previous_rps: float | None = None
        consecutive_low_gains = 0
        peak_rps = 0.0
        max_slo_concurrency: int | None = None
        stop_reason = "exhausted configured concurrencies"
        duration = self.args.closed_duration or self.args.screen_duration

        for concurrency in self.args.closed_concurrencies:
            reference, summary = self._run_once(
                stage="A",
                mode="closed",
                duration=duration,
                concurrency=concurrency,
            )
            if summary is None or not reference["pass"]:
                stop_reason = f"run {reference['id']} failed its validity/SLO checks"
                break
            request_rps = scalar_number(summary, "request_rps")
            if request_rps is None or request_rps <= 0:
                stop_reason = f"run {reference['id']} reported no positive throughput"
                break
            peak_rps = max(peak_rps, request_rps)
            max_slo_concurrency = concurrency
            if previous_rps is not None:
                gain = (request_rps - previous_rps) / previous_rps
                reference["throughput_gain"] = gain
                if gain < MIN_GAIN:
                    consecutive_low_gains += 1
                else:
                    consecutive_low_gains = 0
                if consecutive_low_gains >= 2:
                    stop_reason = "throughput gain stayed below 3% for two steps"
                    break
            previous_rps = request_rps
        return peak_rps, max_slo_concurrency, stop_reason

    def stage_offline_throughput(
        self,
    ) -> tuple[float | None, int | None, str]:
        previous_tps: float | None = None
        consecutive_low_gains = 0
        peak_tps: float | None = None
        peak_concurrency: int | None = None
        stop_reason = "exhausted configured offline concurrencies"
        duration = self.args.closed_duration or self.args.screen_duration

        for concurrency in self.args.offline_concurrencies:
            reference, summary = self._run_once(
                stage="T",
                mode="closed",
                duration=duration,
                concurrency=concurrency,
            )
            if summary is None or reference["pass"] is not True:
                stop_reason = (
                    f"run {reference['id']} failed offline validity checks"
                )
                break
            output_tps = scalar_number(summary, "output_tps")
            if output_tps is None or output_tps <= 0:
                stop_reason = (
                    f"run {reference['id']} reported no positive output TPS"
                )
                break
            if peak_tps is None or output_tps > peak_tps:
                peak_tps = output_tps
                peak_concurrency = concurrency
            if previous_tps is not None:
                gain = (output_tps - previous_tps) / previous_tps
                reference["throughput_gain"] = gain
                if gain < MIN_GAIN:
                    consecutive_low_gains += 1
                else:
                    consecutive_low_gains = 0
                if consecutive_low_gains >= 2:
                    stop_reason = (
                        "output TPS gain stayed below 3% for two steps"
                    )
                    break
            previous_tps = output_tps
        return peak_tps, peak_concurrency, stop_reason

    def _record_rate(
        self, rate: float, *, duration: float, repetition: int = 1
    ) -> dict[str, Any]:
        normalized = round(rate, 6)
        reference, _ = self._run_once(
            stage="B",
            mode="open",
            duration=duration,
            concurrency=self.args.open_concurrency,
            request_rate=normalized,
            repetition=repetition,
        )
        self.observations.setdefault(normalized, []).append(reference)
        return reference

    def _rate_passes(self, rate: float) -> bool:
        runs = self.observations.get(round(rate, 6), [])
        return bool(runs) and all(run["pass"] is True for run in runs)

    def stage_b(self, peak_rps: float) -> tuple[float | None, list[dict[str, Any]]]:
        screen_duration = self.args.open_duration or self.args.screen_duration
        initial_rates = sorted(
            {round(peak_rps * ratio, 6) for ratio in SCREEN_RATIOS if peak_rps * ratio > 0}
        )
        for rate in initial_rates:
            self._record_rate(rate, duration=screen_duration)

        passing = sorted(rate for rate in self.observations if self._rate_passes(rate))
        # Search below the first screen point if even 10% of closed-loop peak fails.
        probe = min(initial_rates)
        for _ in range(6):
            if passing:
                break
            probe = round(probe / 2.0, 6)
            if probe <= 0:
                break
            self._record_rate(probe, duration=screen_duration)
            passing = sorted(
                rate for rate in self.observations if self._rate_passes(rate)
            )
        if not passing:
            return None, []

        low = max(passing)
        failing_above = sorted(
            rate
            for rate in self.observations
            if rate > low and not self._rate_passes(rate)
        )
        # Usually 105% brackets the peak. Expand conservatively if it does not.
        expansion = max(self.observations)
        for _ in range(5):
            if failing_above:
                break
            expansion = round(expansion * 1.25, 6)
            self._record_rate(expansion, duration=screen_duration)
            if self._rate_passes(expansion):
                low = expansion
            else:
                failing_above = [expansion]
        if not failing_above:
            return None, []
        high = min(rate for rate in failing_above if rate > low)

        for _ in range(16):
            if (high - low) / max(low, 1e-9) <= BISECTION_WIDTH:
                break
            midpoint = round((low + high) / 2.0, 6)
            if midpoint in self.observations:
                break
            self._record_rate(midpoint, duration=screen_duration)
            if self._rate_passes(midpoint):
                low = midpoint
            else:
                high = midpoint

        boundary_duration = self.args.boundary_duration
        candidates = sorted(
            (
                rate
                for rate in self.observations
                if rate <= low and self._rate_passes(rate)
            ),
            reverse=True,
        )
        for candidate in candidates:
            boundary_runs: list[dict[str, Any]] = []
            for repetition in range(1, self.args.repetitions + 1):
                reference = self._record_rate(
                    candidate,
                    duration=boundary_duration,
                    repetition=repetition,
                )
                boundary_runs.append(reference)
                if reference["pass"] is not True:
                    break
            if len(boundary_runs) == self.args.repetitions and all(
                run["pass"] is True for run in boundary_runs
            ):
                return candidate, boundary_runs
        return None, []

    def mean_boundary_e2e(self, references: Sequence[Mapping[str, Any]]) -> float | None:
        weighted_total = 0.0
        completed_total = 0.0
        for reference in references:
            run_id = reference.get("id")
            if not isinstance(run_id, str):
                continue
            summary = self.run_summaries.get(run_id)
            if summary is None:
                continue
            mean = nested_number(summary, "e2e_ms", "mean")
            completed = scalar_number(summary, "completed")
            if mean is None or completed is None or completed <= 0:
                continue
            weighted_total += mean * completed
            completed_total += completed
        return weighted_total / completed_total if completed_total else None

    def execute(self) -> tuple[dict[str, Any], int]:
        self.results.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        if self.args.search_mode == "offline-throughput":
            peak_tps, peak_concurrency, stop_reason = (
                self.stage_offline_throughput()
            )
            result: dict[str, Any] = {
                "schema_version": 1,
                "search_mode": "offline-throughput",
                "evidence_class": "non_slo_offline_throughput",
                "created_at": datetime.now(UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "dataset": str(self.args.dataset.expanduser().resolve()),
                "base_url": self.args.base_url,
                "model": self.args.model,
                "objective": "output_tps",
                "peak_output_tps": peak_tps,
                "peak_concurrency": peak_concurrency,
                "stop_reason": stop_reason,
                "validity": {
                    "minimum_completion_ratio": self.args.minimum_completion_ratio,
                    "maximum_error_rate": self.args.maximum_error_rate,
                    "maximum_osl_shortfall_rate": (
                        self.args.maximum_osl_shortfall_rate
                    ),
                    "minimum_server_usage_fraction": (
                        self.args.minimum_server_usage_fraction
                    ),
                },
                "runs": [reference["id"] for reference in self.throughput_refs],
                "run_references": self.throughput_refs,
            }
            latency = {
                "schema_version": 1,
                "search_mode": "offline-throughput",
                "capacity_publishable": False,
                "note": (
                    "Latency is recorded for diagnosis only and did not gate "
                    "the offline throughput search."
                ),
                "comparison_slo": {
                    "ttft_p95_ms": self.args.slo_ttft_p95_ms,
                    "tpot_p95_ms": self.args.slo_tpot_p95_ms,
                },
                "runs": [
                    {
                        "id": reference["id"],
                        "concurrency": reference["concurrency"],
                        "output_tps": reference["output_tps"],
                        "latency_evidence": reference["latency_evidence"],
                    }
                    for reference in self.throughput_refs
                ],
            }
            (self.results / "throughput_summary.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (self.results / "non_capacity_evidence.json").write_text(
                json.dumps(latency, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return result, 0 if peak_tps is not None else 1

        peak_rps, max_slo_concurrency, stage_a_stop = self.stage_a()

        boundary_references: list[dict[str, Any]] = []
        highest_passing_rps: float | None = None
        if peak_rps > 0:
            highest_passing_rps, boundary_references = self.stage_b(peak_rps)
        mean_e2e_ms = self.mean_boundary_e2e(boundary_references)
        operational_rps = (
            0.8 * highest_passing_rps
            if highest_passing_rps is not None
            else None
        )
        estimated_users = (
            highest_passing_rps
            * (mean_e2e_ms / 1000.0 + self.args.think_time)
            if highest_passing_rps is not None and mean_e2e_ms is not None
            else None
        )
        result: dict[str, Any] = {
            "schema_version": 1,
            "search_mode": "slo-capacity",
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "dataset": str(self.args.dataset.expanduser().resolve()),
            "base_url": self.args.base_url,
            "model": self.args.model,
            "slo": {
                "minimum_completion_ratio": MIN_COMPLETION_RATIO,
                "maximum_error_rate": self.args.slo_error_rate,
                "ttft_p95_ms": self.args.slo_ttft_p95_ms,
                "tpot_p95_ms": self.args.slo_tpot_p95_ms,
                "maximum_queue_slope_ms_per_s": self.args.queue_slope_ms_per_s,
            },
            "peak_closed_loop_rps": peak_rps,
            "highest_passing_rps": highest_passing_rps,
            "operational_rps": operational_rps,
            "operational_rps_80_percent": operational_rps,
            "max_slo_concurrency": max_slo_concurrency,
            "mean_e2e_ms": mean_e2e_ms,
            "think_time_s": self.args.think_time,
            "estimated_users": estimated_users,
            "stage_a": {
                "stop_reason": stage_a_stop,
                "runs": [reference["id"] for reference in self.stage_a_refs],
            },
            "stage_b": {
                "screen_ratios": list(SCREEN_RATIOS),
                "bisect_relative_width": BISECTION_WIDTH,
                "boundary_repetitions": self.args.repetitions,
                "boundary_runs": [
                    reference["id"] for reference in boundary_references
                ],
                "runs": [reference["id"] for reference in self.stage_b_refs],
            },
            "run_references": self.run_references,
        }
        output = self.results / "capacity_summary.json"
        output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result, 0 if highest_passing_rps is not None else 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find SLO-qualified capacity or a closed-loop offline output-TPS peak."
        ),
        epilog=(
            "Defaults are short screening runs. SLO capacity uses a closed/open "
            "two-stage search; offline throughput uses only the closed-loop "
            "concurrency ladder and never establishes sustainable capacity."
        ),
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument(
        "--search-mode",
        choices=["slo-capacity", "offline-throughput"],
        default="slo-capacity",
    )
    parser.add_argument("--slo-ttft-p95-ms", type=float, default=2000.0)
    parser.add_argument("--slo-tpot-p95-ms", type=float, default=50.0)
    parser.add_argument("--slo-error-rate", type=float, default=0.005)
    parser.add_argument("--minimum-completion-ratio", type=float, default=0.995)
    parser.add_argument("--maximum-error-rate", type=float, default=0.005)
    parser.add_argument(
        "--maximum-osl-shortfall-rate", type=float, default=0.01
    )
    parser.add_argument(
        "--minimum-server-usage-fraction", type=float, default=0.99
    )
    parser.add_argument(
        "--think-time",
        type=float,
        default=0.0,
        help="mean user think time in seconds for the concurrency estimate",
    )
    parser.add_argument(
        "--closed-concurrencies",
        type=parse_concurrencies,
        default=parse_concurrencies("1,2,4,8,16,32,64,128,256"),
    )
    parser.add_argument(
        "--offline-concurrencies",
        type=parse_concurrencies,
        default=parse_concurrencies("1,2,4,8,16,32,64,128,256,512"),
    )
    parser.add_argument("--screen-duration", type=float, default=30.0)
    parser.add_argument(
        "--closed-duration",
        type=float,
        help="override screening duration for Stage A",
    )
    parser.add_argument(
        "--open-duration",
        type=float,
        help="override screening duration for initial/bisection Stage B runs",
    )
    parser.add_argument("--boundary-duration", type=float, default=30.0)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--open-concurrency",
        type=int,
        default=4096,
        help="safety cap; a run fails classification if this cap binds",
    )
    parser.add_argument("--queue-slope-ms-per-s", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args(argv)

    for field in (
        "slo_ttft_p95_ms",
        "slo_tpot_p95_ms",
        "think_time",
        "screen_duration",
        "boundary_duration",
        "queue_slope_ms_per_s",
        "timeout",
    ):
        value = getattr(args, field)
        if not math.isfinite(value) or value < 0:
            parser.error(f"--{field.replace('_', '-')} must be finite and non-negative")
    for field in ("closed_duration", "open_duration"):
        value = getattr(args, field)
        if value is not None and (not math.isfinite(value) or value <= 0):
            parser.error(f"--{field.replace('_', '-')} must be positive and finite")
    if args.slo_ttft_p95_ms <= 0 or args.slo_tpot_p95_ms <= 0:
        parser.error("latency SLOs must be positive")
    if not 0 <= args.slo_error_rate <= 1:
        parser.error("--slo-error-rate must be a fraction between 0 and 1")
    for field in (
        "minimum_completion_ratio",
        "maximum_error_rate",
        "maximum_osl_shortfall_rate",
        "minimum_server_usage_fraction",
    ):
        value = getattr(args, field)
        if not 0 <= value <= 1:
            parser.error(
                f"--{field.replace('_', '-')} must be a fraction between 0 and 1"
            )
    if args.screen_duration <= 0 or args.boundary_duration <= 0:
        parser.error("durations must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")
    if args.open_concurrency <= 0:
        parser.error("--open-concurrency must be positive")
    if args.max_requests < 0:
        parser.error("--max-requests must be non-negative")
    parsed = urlsplit(args.base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        parser.error("--base-url must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        parser.error("--base-url must not contain credentials")
    if parsed.query or parsed.fragment:
        parser.error("--base-url must not contain a query string or fragment")
    if not args.dataset.expanduser().is_file():
        parser.error("--dataset must name an existing JSONL file")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    search = CapacitySearch(args)
    try:
        result, exit_code = search.execute()
    except OSError as exc:
        raise SearchError(f"cannot create capacity results: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        sys.exit(130)

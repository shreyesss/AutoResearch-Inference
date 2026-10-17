"""Deterministic authority boundary for one frozen vLLM/AIPerf evaluation."""

from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import (CandidateProposal, CellResult, EvaluationResult,
                                               MeasurementPolicy, ScenarioManifest)
from inference_autoresearch.contracts_wire import export_cell_result
from inference_autoresearch.runtime.config import BASELINE, PinnedEnvironment, resolve_config


class EvaluationError(RuntimeError):
    pass


def _save(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(path)


@contextmanager
def _timed(phases: dict[str, float], name: str):
    """Record elapsed wall time even when a phase raises."""
    start = time.monotonic()
    try:
        yield
    finally:
        phases[name] = round(time.monotonic() - start, 6)


def _validate_cell(cell: CellResult, expected: int, config_id: str, scenario_id: str) -> list[str]:
    reasons: list[str] = []
    if cell.config_id != config_id or cell.scenario_id != scenario_id:
        reasons.append("identity_mismatch")
    counts = cell.counts
    required = ("planned", "dispatched", "not_dispatched", "completed", "failed", "timed_out",
                "canceled", "censored", "tpot_eligible", "successful_completion_tokens")
    if any(key not in counts or type(counts[key]) is not int or counts[key] < 0 for key in required):
        return reasons + ["request_accounting"]
    if counts["planned"] != expected or counts["planned"] != counts["dispatched"] + counts["not_dispatched"]:
        reasons.append("request_accounting")
    if counts["dispatched"] != sum(counts[k] for k in ("completed", "failed", "timed_out", "canceled")):
        reasons.append("request_accounting")
    if counts["censored"] or counts["failed"] or counts["timed_out"] or counts["canceled"] or counts["not_dispatched"]:
        reasons.append("incomplete_or_failed_requests")
    if cell.status == "valid" and any(cell.metrics.get(k) is None for k in
                                       ("output_tokens_per_s", "ttft_p50_ms", "ttft_p99_ms", "tpot_p50_ms", "tpot_p99_ms")):
        reasons.append("missing_primary_metric")
    if cell.behavior == "overload":
        reasons.append("overload")
    return sorted(set(reasons))


def classify_behavior(cell: CellResult) -> CellResult:
    """Assign only defensible finite-run behavior; unknown stays ineligible.

    Clean completion and low client lag are required. A small transient queue
    is admissible only when at most three requests wait and post-send drain is at
    most 10% of dispatch time. This rule is fixed before the four-task B0 and
    admits natural long-prefill contention without accepting sustained backlog.
    Neither case proves capacity beyond this measured window.
    """
    gauges = cell.diagnostics.get("server_gauges", {})
    queue = gauges.get("queue_max")
    lag = cell.metrics.get("dispatch_lag_p99_ms")
    windows = cell.diagnostics.get("windows", {})
    drain = windows.get("drain_duration_s")
    dispatch = windows.get("dispatch_duration_s")
    if queue == 0 and cell.status == "valid" and lag is not None and lag <= 20:
        return replace(cell, behavior="normal", diagnostics=cell.diagnostics | {
            "behavior_admission": "zero_server_queue"})
    if (cell.status == "valid" and isinstance(queue, (int, float)) and 0 < queue <= 3
            and isinstance(dispatch, (int, float)) and dispatch > 0
            and isinstance(drain, (int, float)) and 0 <= drain <= 0.10 * dispatch
            and lag is not None and lag <= 20):
        return replace(cell, behavior="normal", diagnostics=cell.diagnostics | {
            "behavior_admission": "bounded_transient_queue",
            "behavior_thresholds": {"queue_max": 3, "max_drain_fraction": 0.10}})
    if isinstance(queue, (int, float)) and queue > 0 and isinstance(drain, (int, float)) and isinstance(dispatch, (int, float)) and drain > max(30, dispatch / 3):
        return replace(cell, behavior="overload")
    return replace(cell, behavior="unknown")


def measurement_limits(scenario: ScenarioManifest) -> dict[str, float]:
    """Give the entire frozen schedule time to dispatch, plus bounded drain time.

    The ordinary 60-second fixtures retain their existing 70/60/180-second
    benchmark/grace/process limits. Longer OPS schedules get a window derived
    from the verified last timestamp rather than a hardcoded 70-second cut-off.
    """
    duration = scenario.metadata.get("schedule_duration_s", 60.0)
    if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
        raise EvaluationError("Scenario has no valid verified schedule duration")
    benchmark = max(70, math.ceil(duration) + 10)
    grace = 60 if duration <= 60 else min(180, max(60, math.ceil(duration)))
    deadline = max(180, benchmark + grace + 30)
    return {"schedule_duration_s": float(duration), "benchmark_duration_s": float(benchmark),
            "benchmark_grace_period_s": float(grace), "deadline_s": float(deadline)}


class EvaluationEngine:
    """Proposal settings are the only caller-controlled variable.

    Registry, policy, model, image, schedule, server process, and GPU lock are
    evaluator-owned. Each cold_stream cell gets a fresh server, then its own
    disjoint preparation traffic. This is protocol `fresh-server-cell-v1` and
    is not pooled with the historical shared-server manual runs.
    """

    def __init__(self, campaign: dict[str, Any], registry: Any, runtime: Any, benchmark: Any,
                 artifact_root: Path, ledger: Any):
        self.campaign = campaign
        self.registry = registry
        self.runtime = runtime
        self.benchmark = benchmark
        self.artifact_root = Path(artifact_root)
        self.ledger = ledger
        self.campaign_id = campaign["campaign_id"]

    def _scenario(self, scenario_id: str) -> ScenarioManifest:
        if hasattr(self.registry, "load"):
            scenario = self.registry.load(scenario_id)
        else:
            scenario = self.registry[scenario_id]
        if not isinstance(scenario, ScenarioManifest):
            raise EvaluationError("registry must return validated ScenarioManifest objects")
        if scenario.cache_protocol != "cold_stream":
            raise EvaluationError("cache preparation protocol is not implemented for this scenario")
        if scenario.traffic_mode != "independent_open_loop" or scenario.history_mode != "single_turn":
            raise EvaluationError("this evaluator only supports frozen independent replay")
        return scenario

    def _domain(self) -> dict[str, list[object]]:
        raw = self.campaign.get("domain")
        if raw is not None:
            return {key: list(value) for key, value in raw.items()}
        path = self.campaign.get("search_domain_path")
        if not path:
            raise EvaluationError("frozen search domain missing")
        source = Path(path)
        if not source.is_absolute():
            source = Path(self.campaign.get("project_root", Path.cwd())) / source
        values = json.loads(source.read_text())["parameters"]
        return {key: list(spec["values"]) for key, spec in values.items()}

    def _pinned(self) -> PinnedEnvironment:
        model = self.campaign["model"]
        runtime = self.campaign["runtime"]
        baseline = self.campaign["baseline"]
        if {key: baseline.get(key) for key in BASELINE} != BASELINE or baseline.get("reasoning_parser") != "qwen3":
            raise EvaluationError("campaign B0 does not match the measured resolved baseline")
        local = Path(self.campaign.get("model_dir", model["local_path"]))
        if not local.is_absolute():
            local = Path(self.campaign.get("project_root", Path.cwd())) / local
        return PinnedEnvironment(local, image=runtime["image"], model_name=model["id"],
                                 model_revision=model["revision"], max_model_len=model["max_model_len"],
                                 tensor_parallel_size=model["tensor_parallel_size"], dtype=model["dtype"],
                                 gpu_uuid=runtime["gpu_uuid"])

    def _append(self, kind: str, entity_id: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            self.ledger.append(self.campaign_id, kind, entity_id, data)

    def evaluate(self, candidate: CandidateProposal, scenario_ids: list[str], stage: str) -> EvaluationResult:
        evaluation_start = time.monotonic()
        if stage not in ("pilot", "triage", "screen", "expanded", "confirm"):
            raise EvaluationError("unknown evaluation stage")
        protocol_id = "fresh-server-triage-v1" if stage == "triage" else "fresh-server-cell-v1"
        if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
            raise EvaluationError("provide distinct frozen scenario IDs")
        # Resolve all read-only inputs before touching the GPU.
        scenarios = [self._scenario(identifier) for identifier in scenario_ids]
        limits = {scenario.scenario_id: measurement_limits(scenario) for scenario in scenarios}
        resolved = resolve_config(candidate.parameters, self._pinned(), self._domain())
        preflight_start = time.monotonic()
        if self.campaign.get("backend", "real") == "real":
            preflight = getattr(self.benchmark, "preflight_tokenizer", None)
            if preflight is None:
                raise EvaluationError("real adapter must preflight the exact offline tokenizer loader")
            for scenario in scenarios:
                preflight(scenario)
        preflight_s = round(time.monotonic() - preflight_start, 6)
        evaluation_id = "eval-" + uuid.uuid4().hex
        output_dir = self.artifact_root / self.campaign_id / evaluation_id
        output_dir.mkdir(parents=True, exist_ok=False)
        _save(output_dir / "proposal.json", asdict(candidate))
        _save(output_dir / "resolved-config.json", asdict(resolved))
        _save(output_dir / "evaluation-policy.json", {
            "protocol_id": protocol_id, "stage": stage,
            "scenario_ids": scenario_ids, "cache_policy": "fresh vLLM process per measured cell; disjoint warmup",
            "measurement_limits_by_scenario": limits,
        })
        self._append("evaluation_transition", evaluation_id, {"state": "validated", "config_id": resolved.config_id})
        self._append("resolved_config", resolved.config_id, asdict(resolved) | {
            "proposal_id": candidate.proposal_id, "overrides": candidate.parameters,
            "is_baseline": not candidate.parameters,
        })
        cell_ids: list[str] = []
        failures: list[str] = []
        cell_timings: list[dict[str, Any]] = []
        for ordinal, scenario in enumerate(scenarios, 1):
            cell_dir = output_dir / f"cell-{ordinal:02d}-{scenario.scenario_id}"
            cell_dir.mkdir()
            handle = None
            cell_start = time.monotonic()
            phases: dict[str, float] = {}
            cell_failure: str | None = None
            self._append("evaluation_transition", evaluation_id,
                         {"state": "starting", "scenario_id": scenario.scenario_id, "ordinal": ordinal})
            try:
                with _timed(phases, "server_start_s"):
                    handle = self.runtime.start(resolved, cell_dir / "server")
                self._append("evaluation_transition", evaluation_id,
                             {"state": "warming", "scenario_id": scenario.scenario_id})
                with _timed(phases, "warmup_s"):
                    receipt = self.benchmark.prepare(handle, scenario, cell_dir / "warmup")
                receipt_path = cell_dir / "warmup" / "preparation-receipt.json"
                if not isinstance(receipt, dict) or not receipt_path.is_file():
                    raise EvaluationError("benchmark preparation did not produce a receipt")
                cell_limits = limits[scenario.scenario_id]
                policy = MeasurementPolicy(stage=stage, replicate=1,
                                           window_s=cell_limits["schedule_duration_s"],
                                           deadline_s=cell_limits["deadline_s"],
                                           min_eligible=0, cache_protocol=scenario.cache_protocol,
                                           metadata={"run_id": evaluation_id,
                                                     "preparation_receipt": str(receipt_path),
                                                     "benchmark_duration_s": cell_limits["benchmark_duration_s"],
                                                     "benchmark_grace_period_s": cell_limits["benchmark_grace_period_s"],
                                                     "protocol_id": protocol_id})
                self._append("evaluation_transition", evaluation_id,
                             {"state": "measuring", "scenario_id": scenario.scenario_id})
                with _timed(phases, "benchmark_s"):
                    cell = self.benchmark.run_cell(handle, scenario, policy, cell_dir / "aiperf")
                if not isinstance(cell, CellResult):
                    raise EvaluationError("benchmark adapter returned an invalid CellResult")
                with _timed(phases, "result_processing_s"):
                    cell = classify_behavior(cell)
                    _save(cell_dir / "cell-result.json", asdict(cell))
                    if self.campaign.get("backend", "real") == "real" and stage != "triage":
                        export_cell_result(cell, scenario, policy, cell_dir / "server",
                                           cell_dir / "cell-result-v02.json")
                    elif self.campaign.get("backend", "real") == "real":
                        _save(cell_dir / "wire-export-status.json", {
                            "status": "unavailable_for_triage",
                            "reason": "frozen cell-result v0.2 schema excludes the triage stage",
                            "native_cell_result": str(cell_dir / "cell-result.json"),
                        })
                    reasons = _validate_cell(cell, scenario.expected_count, resolved.config_id, scenario.scenario_id)
                    _save(cell_dir / "controller-validation.json", {"reason_codes": reasons,
                           "frontier_eligible": cell.status == "valid" and cell.behavior == "normal" and not reasons})
                    if reasons or cell.status != "valid":
                        failures.extend(f"{scenario.scenario_id}:{reason}" for reason in (reasons or cell.reason_codes or [cell.status]))
                    cell_ids.append(cell.cell_id)
                    self._append("cell", cell.cell_id, asdict(cell) | {
                        "controller_validation": reasons, "stage": stage,
                        "offered_load": scenario.offered_load, "load_unit": scenario.load_unit,
                        "cache_protocol": scenario.cache_protocol,
                        "measurement_protocol": protocol_id,
                        "workload_group_id": scenario.group_id,
                        "is_baseline": not candidate.parameters,
                    })
            except Exception as exc:
                reason = f"{scenario.scenario_id}:{type(exc).__name__}:{exc}"
                cell_failure = reason
                failures.append(reason)
                _save(cell_dir / "failure.json", {"reason": reason, "state": "functional_or_measurement_failed"})
                self._append("evaluation_transition", evaluation_id,
                             {"state": "failed", "scenario_id": scenario.scenario_id, "reason": reason})
            finally:
                if handle is not None:
                    self._append("evaluation_transition", evaluation_id,
                                 {"state": "draining", "scenario_id": scenario.scenario_id})
                    try:
                        with _timed(phases, "server_stop_s"):
                            self.runtime.stop(handle)
                    except Exception as exc:
                        cell_failure = f"{scenario.scenario_id}:cleanup:{exc}"
                        failures.append(cell_failure)
                timing = {"scenario_id": scenario.scenario_id, "stage": stage,
                          "protocol_id": protocol_id, "ordinal": ordinal,
                          "status": "failed" if cell_failure or failures else "completed",
                          "failure": cell_failure, "phases": phases,
                          "total_wall_s": round(time.monotonic() - cell_start, 6)}
                _save(cell_dir / "timing.json", timing)
                self._append("cell_timing", f"{evaluation_id}:{ordinal}", timing)
                cell_timings.append(timing)
            if failures:
                break
        status = "valid" if len(cell_ids) == len(scenarios) and not failures else "failed"
        result = EvaluationResult(evaluation_id, resolved.config_id, stage, cell_ids,
                                  status, failures, {"directory": str(output_dir),
                                                     "protocol_id": protocol_id,
                                                     "elapsed_s": f"{time.monotonic() - evaluation_start:.3f}",
                                                     "timings": str(output_dir / "evaluation-timings.json")})
        _save(output_dir / "evaluation-timings.json", {
            "evaluation_id": evaluation_id, "protocol_id": protocol_id,
            "stage": stage, "preflight_s": preflight_s,
            "cells": cell_timings,
            "total_wall_s": round(time.monotonic() - evaluation_start, 6),
        })
        _save(output_dir / "evaluation-result.json", asdict(result))
        self._append("evaluation", evaluation_id, asdict(result))
        return result

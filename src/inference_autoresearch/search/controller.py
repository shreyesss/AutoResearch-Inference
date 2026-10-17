"""Bounded proposal/evaluate loop with a hard real-search qualification gate."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CampaignResult, CandidateProposal, ProposalContext, Proposer
from inference_autoresearch.storage import Ledger
from .domain import Domain, config_identity, scientific_campaign_hash, sha
from .report import export, export_history, pareto_front, eligible, OBJECTIVES


class SearchGateError(RuntimeError):
    pass


def qualification_ok(campaign: dict[str, Any], domain: Domain, campaign_path: Path,
                     backend: str, ledger: Ledger | None = None, registry: Any = None,
                     artifact_root: Path | None = None) -> dict[str, Any]:
    if backend != "real":
        return {"search_allowed": True, "label": "mock_only"}
    path_value = campaign.get("real_search_qualification_path")
    if not path_value:
        raise SearchGateError("real autonomous search requires a qualification report; pilot evaluate remains available")
    path = Path(path_value)
    if not path.is_absolute():
        path = campaign_path.parent.parent / path if campaign_path.parent.name == "configs" else campaign_path.parent / path
    if not path.is_file():
        raise SearchGateError(f"qualification report missing: {path}")
    qualification = json.loads(path.read_text())
    if qualification.get("search_allowed") is not True or qualification.get("backend") != "real":
        raise SearchGateError("qualification does not authorize real search")
    if qualification.get("source") != "iar qualify":
        raise SearchGateError("qualification report was not produced by iar qualify")
    if qualification.get("campaign_hash") != scientific_campaign_hash(campaign) or qualification.get("domain_hash") != domain.digest:
        raise SearchGateError("qualification does not match frozen campaign/domain hashes")
    if qualification.get("qualification_requirements_hash") != sha(
            campaign.get("qualification_requirements", {})):
        raise SearchGateError("qualification requirements changed since report generation")
    required = ("provenance_validated", "traffic_validated", "baseline_characterized", "sensitivity_qualified")
    if any(qualification.get(key) is not True for key in required):
        raise SearchGateError("qualification lacks workload/B0/sensitivity evidence")
    if not qualification.get("evidence_ids"):
        raise SearchGateError("qualification has no evidence IDs")
    if ledger is not None and registry is not None and artifact_root is not None:
        from .qualification import assess
        fresh = assess(campaign, domain, ledger, registry, artifact_root, backend="real")
        if not fresh["search_allowed"] or any(fresh[key] != qualification.get(key) for key in
            ("campaign_hash", "domain_hash", "qualification_requirements_hash",
             "provenance_validated", "traffic_validated",
             "baseline_characterized", "sensitivity_qualified", "evidence_ids")):
            raise SearchGateError("qualification no longer matches current machine evidence")
    return qualification


class SearchController:
    def __init__(self, campaign: dict[str, Any], campaign_path: Path, domain: Domain,
                 proposer: Proposer, evaluator: Any, ledger: Ledger, artifact_root: Path,
                 backend: str, evidence_refs: list[dict[str, Any]] | None = None):
        self.campaign = campaign
        self.campaign_path = campaign_path
        self.domain = domain
        self.proposer = proposer
        self.evaluator = evaluator
        self.ledger = ledger
        self.artifact_root = artifact_root
        self.backend = backend
        self.evidence_refs = evidence_refs or []

    def run(self, max_proposals: int | None = None, resume: bool = False) -> CampaignResult:
        qualification = qualification_ok(self.campaign, self.domain, self.campaign_path, self.backend,
                                         self.ledger, getattr(self.evaluator, "registry", None),
                                         self.artifact_root)
        campaign_id = self.campaign["campaign_id"]
        budget = self.campaign.get("search_budget", {})
        cap = min(int(max_proposals or budget.get("max_distinct_proposals", 12)),
                  int(budget.get("max_distinct_proposals", 12)))
        if cap < 1:
            raise ValueError("search requires positive proposal budget")
        wall_limit = float(budget.get("wall_seconds", 21600))
        start = time.monotonic()
        campaign_digest = scientific_campaign_hash(self.campaign)
        self.ledger.claim(campaign_id, "campaign_lock", "frozen", campaign_digest,
                          {"campaign_hash": campaign_digest, "domain_hash": self.domain.digest,
                           "backend": self.backend})
        existing = self.ledger.events(campaign_id, "proposal")
        if existing and not resume:
            raise ValueError("campaign already has proposals; pass --resume")
        proposed = len(existing)
        tested = len(self.ledger.events(campaign_id, "search_evaluation"))
        seen_ids = {event["payload"].get("config_id") for event in existing}
        if resume and hasattr(self.proposer, "index"):
            self.proposer.index = proposed
        # Search starts with a measured B0 under its own exact screen protocol.
        # Historical shared-server/manual B0 cells do not satisfy this gate.
        baseline_id = config_identity(self.campaign, self.campaign["baseline"])
        baseline_cells = [e["payload"] for e in self.ledger.events(campaign_id, "cell")
                          if e["payload"].get("config_id") == baseline_id
                          and e["payload"].get("stage") == "screen"
                          and e["payload"].get("measurement_protocol") in
                          ("fresh-server-cell-v1", "mock-frozen-v1")]
        have_scenarios = {cell["scenario_id"] for cell in baseline_cells if eligible(cell)}
        missing = set(self.campaign["screen_scenario_ids"]) - have_scenarios
        if missing:
            b0 = CandidateProposal(proposal_id="B0-screen", parameters={}, experiment_kind="exploration",
                hypothesis="Screen-protocol reference at fixed offered loads",
                expected_tradeoff="reference", predictions=[{"observation": "primary metrics",
                    "expected_change": "reference", "scope": "frozen screen scenarios"}],
                falsification_condition="baseline request accounting or environment validation fails")
            self.ledger.append(campaign_id, "baseline_required", "B0-screen",
                               {"missing_scenarios": sorted(missing), "config_id": baseline_id})
            baseline_result = self.evaluator.evaluate(b0, self.campaign["screen_scenario_ids"], "screen")
            self.ledger.append(campaign_id, "search_baseline", baseline_result.evaluation_id,
                               asdict(baseline_result))
            if baseline_result.status != "valid":
                raise SearchGateError("screen B0 failed; inspect baseline evaluation before candidate search")
            baseline_cells = [e["payload"] for e in self.ledger.events(campaign_id, "cell")
                              if e["payload"].get("config_id") == baseline_id
                              and e["payload"].get("stage") == "screen"]
            have_scenarios = {cell["scenario_id"] for cell in baseline_cells if eligible(cell)}
            if set(self.campaign["screen_scenario_ids"]) - have_scenarios:
                raise SearchGateError("screen B0 missing eligible cells on common scenarios")
        stop_reason = "proposal_budget"
        while proposed < cap:
            if time.monotonic() - start >= wall_limit:
                stop_reason = "wall_budget"
                break
            recent = [event["payload"] for event in self.ledger.events(campaign_id, "cell")][-80:]
            front = _scoped_fronts(recent)
            feedback = [event["payload"] for event in self.ledger.events(campaign_id, "feedback")][-12:]
            context = ProposalContext(
                campaign_id=campaign_id,
                mission="Find compatible Pareto tradeoffs in pinned vLLM serving settings",
                domain=self.domain.raw,
                baseline=self.campaign["baseline"], frontier=front,
                recent_results=feedback + recent[-12:], evidence_refs=self.evidence_refs,
                remaining_budget={"distinct_proposals": cap - proposed,
                                  "wall_seconds": max(0, wall_limit - (time.monotonic() - start))},
                qualification=qualification,
            )
            try:
                proposal: CandidateProposal = self.proposer.propose(context)
                effective = self.domain.effective(self.campaign["baseline"], proposal.parameters)
                config_id = config_identity(self.campaign, effective)
                if config_id in seen_ids:
                    self.ledger.append(campaign_id, "proposal_rejected", proposal.proposal_id,
                                       {"reason": "equivalent_config", "config_id": config_id,
                                        "proposal": asdict(proposal)})
                    stop_reason = "duplicate_config"
                    break
                self.ledger.claim(campaign_id, "proposal", proposal.proposal_id,
                                  sha(asdict(proposal)), {"proposal": asdict(proposal),
                                                          "config_id": config_id, "effective": effective,
                                                          "label": self.backend})
                seen_ids.add(config_id)
                proposed += 1
                self.ledger.append(campaign_id, "lifecycle", proposal.proposal_id,
                                   {"state": "validated", "config_id": config_id})
                result = self.evaluator.evaluate(proposal, self.campaign["screen_scenario_ids"], "screen")
                self.ledger.append(campaign_id, "search_evaluation", result.evaluation_id,
                                   asdict(result) | {"proposal_id": proposal.proposal_id})
                candidate_cells = [e["payload"] for e in self.ledger.events(campaign_id, "cell")
                                   if e["payload"].get("cell_id") in result.cell_ids]
                self.ledger.append(campaign_id, "feedback", proposal.proposal_id,
                                   _feedback(proposal, result, candidate_cells, baseline_cells))
                tested += 1
            except Exception as exc:
                self.ledger.append(campaign_id, "search_error", f"attempt-{proposed+1}",
                                   {"error_type": type(exc).__name__, "reason": str(exc)})
                stop_reason = "proposal_or_evaluation_error"
                break
        paths = export([e["payload"] for e in self.ledger.events(campaign_id, "cell")],
                       self.artifact_root / "report")
        paths.update(export_history(self.ledger, campaign_id, self.artifact_root / "report"))
        if stop_reason == "proposal_budget":
            stop_reason = "screen_budget_confirmation_pending"
        result = CampaignResult(campaign_id, stop_reason, tested, proposed, paths)
        self.ledger.append(campaign_id, "search_stop", campaign_id, asdict(result))
        return result


def _scope(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(k, "")) for k in
                 ("scenario_id", "offered_load", "load_unit", "cache_protocol", "stage", "measurement_protocol"))


def _scoped_fronts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_scope(row), []).append(row)
    return [{"scope": key, "cells": pareto_front(members)} for key, members in groups.items()]


def _feedback(proposal: CandidateProposal, result: Any, cells: list[dict[str, Any]],
              baseline_cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_scope = {_scope(row): row for row in baseline_cells if eligible(row)}
    comparisons = []
    for cell in cells:
        baseline = by_scope.get(_scope(cell))
        deltas = {metric: cell.get("metrics", {}).get(metric) - baseline["metrics"][metric]
                  for metric in OBJECTIVES if baseline and isinstance(cell.get("metrics", {}).get(metric), (int, float))
                  and isinstance(baseline["metrics"].get(metric), (int, float))}
        comparisons.append({"scenario_id": cell.get("scenario_id"), "scope": _scope(cell),
                            "baseline_cell_id": baseline.get("cell_id") if baseline else None,
                            "candidate_cell_id": cell.get("cell_id"), "validity": cell.get("status"),
                            "behavior": cell.get("behavior"), "metric_delta": deltas,
                            "reason_codes": cell.get("reason_codes", [])})
    return {"proposal_id": proposal.proposal_id, "evaluation_id": result.evaluation_id,
            "status": result.status, "comparisons": comparisons,
            "prediction_status": "unresolved_pending_confirmation",
            "evidence_grade": "provisional", "failure_reasons": result.failure_reasons}

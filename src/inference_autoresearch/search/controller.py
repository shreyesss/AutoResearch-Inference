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
from .report import export, export_history, export_suite_front, pareto_front, eligible, dominates, OBJECTIVES


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
    fixed_four = campaign.get("qualification_requirements", {}).get("mode") == "fixed-four-v1"
    required = ("provenance_validated", "traffic_validated", "baseline_characterized")
    if fixed_four:
        if (qualification.get("qualification_mode") != "fixed-four-v1" or
                qualification.get("qualification_grade") != "exploratory_four_task" or
                qualification.get("sensitivity_qualified") is not False):
            raise SearchGateError("four-task qualification grade or sensitivity claim is invalid")
    else:
        required += ("sensitivity_qualified",)
    if any(qualification.get(key) is not True for key in required):
        raise SearchGateError("qualification lacks required workload/B0 evidence")
    if not qualification.get("evidence_ids"):
        raise SearchGateError("qualification has no evidence IDs")
    if ledger is not None and registry is not None and artifact_root is not None:
        from .qualification import assess
        fresh = assess(campaign, domain, ledger, registry, artifact_root, backend="real")
        if not fresh["search_allowed"] or any(fresh.get(key) != qualification.get(key) for key in
            ("campaign_hash", "domain_hash", "qualification_requirements_hash",
             "qualification_mode", "qualification_grade",
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
        triage_id = self.campaign.get("triage_scenario_id")
        fixed_four = self.campaign.get("qualification_requirements", {}).get("mode") == "fixed-four-v1"
        if fixed_four and triage_id is not None:
            raise SearchGateError("four-task search evaluates every task; triage is disallowed")
        if triage_id is not None and (not isinstance(triage_id, str)
                                      or triage_id not in self.campaign["screen_scenario_ids"]):
            raise ValueError("triage_scenario_id must be one frozen screen scenario")
        triage_policy = self.campaign.get("triage_promotion_policy", "valid")
        if triage_policy not in ("valid", "not_point_dominated_by_matched_b0"):
            raise ValueError("unknown triage_promotion_policy")
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
        baseline_id = config_identity(self.campaign, self.campaign["baseline"])
        seen_ids.add(baseline_id)
        # The triage and two-load screen have independent matched B0 cells.
        # A prior pilot or a manual shared-server cell cannot satisfy either.
        def ensure_baseline(stage: str, scenario_ids: list[str]) -> list[dict[str, Any]]:
            protocol = "fresh-server-triage-v1" if stage == "triage" else "fresh-server-cell-v1"
            def matching_cells() -> list[dict[str, Any]]:
                return [event["payload"] for event in self.ledger.events(campaign_id, "cell")
                        if event["payload"].get("config_id") == baseline_id
                        and event["payload"].get("stage") == stage
                        and event["payload"].get("measurement_protocol") in
                        (protocol, "mock-frozen-v1")
                        and (not fixed_four or event["payload"].get("is_baseline") is True)]
            cells = matching_cells()
            missing = set(scenario_ids) - {cell["scenario_id"] for cell in cells if eligible(cell)}
            if missing:
                b0 = CandidateProposal(proposal_id=f"B0-{stage}", parameters={},
                    experiment_kind="exploration", hypothesis=f"{stage} reference at fixed offered loads",
                    expected_tradeoff="reference", predictions=[{"observation": "primary metrics",
                        "expected_change": "reference", "scope": f"frozen {stage} scenarios"}],
                    falsification_condition="baseline request accounting or environment validation fails")
                self.ledger.append(campaign_id, "baseline_required", f"B0-{stage}",
                                   {"missing_scenarios": sorted(missing), "config_id": baseline_id,
                                    "stage": stage, "protocol_id": protocol})
                baseline_result = self.evaluator.evaluate(b0, scenario_ids, stage)
                self.ledger.append(campaign_id, "search_baseline", baseline_result.evaluation_id,
                                   asdict(baseline_result))
                if baseline_result.status != "valid":
                    raise SearchGateError(f"{stage} B0 failed; inspect baseline evaluation before candidate search")
                cells = matching_cells()
                if set(scenario_ids) - {cell["scenario_id"] for cell in cells if eligible(cell)}:
                    raise SearchGateError(f"{stage} B0 missing eligible cells on common scenarios")
            return cells

        triage_baseline = ensure_baseline("triage", [triage_id]) if triage_id else []
        baseline_cells = [] if triage_id else ensure_baseline("screen", self.campaign["screen_scenario_ids"])
        stop_reason = "proposal_budget"
        while proposed < cap:
            if time.monotonic() - start >= wall_limit:
                stop_reason = "wall_budget"
                break
            heldout_ids = set(self.campaign.get("heldout_scenario_ids", []))
            recent = [event["payload"] for event in self.ledger.events(campaign_id, "cell")
                      if event["payload"].get("scenario_id") not in heldout_ids
                      and "heldout" not in str(event["payload"].get("stage", "")).lower()]
            front = _scoped_fronts(recent)
            if fixed_four:
                suite_paths = export_suite_front(recent, self.campaign["screen_scenario_ids"],
                                                 self.artifact_root / "report")
                suite = json.loads(Path(suite_paths["suite_front_json"]).read_text())
                front.append({"scope": "fixed_four_suite", "objectives": suite["objectives"],
                              "scopes": suite["scopes"]})
            feedback = [event["payload"] for event in self.ledger.events(campaign_id, "feedback")][-12:]
            context = ProposalContext(
                campaign_id=campaign_id,
                mission="Find compatible Pareto tradeoffs in pinned vLLM serving settings",
                domain=self.domain.raw,
                baseline=self.campaign["baseline"], frontier=front,
                recent_results=baseline_cells + feedback + recent[-12:], evidence_refs=self.evidence_refs,
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
                if triage_id:
                    triage_result = self.evaluator.evaluate(proposal, [triage_id], "triage")
                    self.ledger.append(campaign_id, "search_triage_evaluation", triage_result.evaluation_id,
                                       asdict(triage_result) | {"proposal_id": proposal.proposal_id})
                    triage_cells = [e["payload"] for e in self.ledger.events(campaign_id, "cell")
                                    if e["payload"].get("cell_id") in triage_result.cell_ids]
                    triage_feedback = _feedback(proposal, triage_result, triage_cells, triage_baseline)
                    triage_feedback["stage"] = "triage"
                    self.ledger.append(campaign_id, "feedback", proposal.proposal_id, triage_feedback)
                    reference = next((row for row in reversed(triage_baseline)
                                      if row["scenario_id"] == triage_id and eligible(row)), None)
                    candidate_row = next((row for row in triage_cells
                                          if row.get("scenario_id") == triage_id), None)
                    if triage_result.status != "valid" or candidate_row is None or not eligible(candidate_row):
                        decision = "invalid"
                    elif reference is None:
                        raise SearchGateError("matched triage B0 disappeared before promotion decision")
                    elif triage_policy == "not_point_dominated_by_matched_b0" and dominates(reference, candidate_row):
                        decision = "dominated_by_matched_b0"
                    else:
                        decision = "promote_to_two_load_screen"
                    self.ledger.append(campaign_id, "triage_decision", proposal.proposal_id,
                                       {"decision": decision, "triage_evaluation_id": triage_result.evaluation_id,
                                        "candidate_cell_id": candidate_row.get("cell_id") if candidate_row else None,
                                        "baseline_cell_id": reference.get("cell_id") if reference else None,
                                        "policy": triage_policy, "evidence_grade": "provisional",
                                        "limitation": "one load and one window; point dominance can be noise or hide gains at other loads"})
                    if decision != "promote_to_two_load_screen":
                        continue
                    baseline_cells = ensure_baseline("screen", self.campaign["screen_scenario_ids"])
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
        export_kwargs = {"screen_scenario_ids": self.campaign["screen_scenario_ids"]} if fixed_four else {}
        paths = export([e["payload"] for e in self.ledger.events(campaign_id, "cell")],
                       self.artifact_root / "report", **export_kwargs)
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

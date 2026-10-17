"""Explicit CPU-only fake for contract integration; never real evidence."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal, CellResult, EvaluationResult
from inference_autoresearch.search.domain import Domain, config_identity, sha


class MockEvaluator:
    def __init__(self, campaign: dict[str, Any], registry: Any, domain: Domain,
                 artifact_root: Path, ledger: Any):
        self.campaign, self.registry, self.domain = campaign, registry, domain
        self.artifact_root, self.ledger = artifact_root, ledger

    def evaluate(self, candidate: CandidateProposal, scenario_ids: list[str], stage: str) -> EvaluationResult:
        effective = self.domain.effective(self.campaign["baseline"], candidate.parameters)
        config_id = config_identity(self.campaign, effective)
        evaluation_id = "mock-eval-" + sha({"proposal": candidate.proposal_id, "stage": stage,
                                              "scenarios": scenario_ids})[:16]
        cell_ids = []
        for scenario_id in scenario_ids:
            scenario = self.registry.load(scenario_id)
            count = scenario.expected_count
            cell_id = evaluation_id + ":" + scenario_id
            cell_ids.append(cell_id)
            # Fixed synthetic numbers exist only to test accounting, grouping and plots.
            depth = int(effective.get("mtp_draft_tokens", 0))
            load = float(scenario.offered_load or 0)
            cell = CellResult(
                cell_id=cell_id, scenario_id=scenario_id, config_id=config_id,
                status="valid", behavior="normal", evidence_grade="provisional",
                counts={"planned": count, "dispatched": count, "not_dispatched": 0,
                        "completed": count, "failed": 0, "timed_out": 0, "canceled": 0,
                        "censored": 0, "tpot_eligible": count, "successful_completion_tokens": count * 256},
                metrics={"output_tokens_per_s": round(load * 215 + depth * 12, 2),
                         "ttft_p50_ms": 185 + depth * 8, "ttft_p99_ms": 215 + depth * 10,
                         "tpot_p50_ms": 60 - min(depth, 3) * 8,
                         "tpot_p99_ms": 65 - min(depth, 3) * 8},
                diagnostics={"mock": True}, artifacts={},
            )
            self.ledger.append(self.campaign["campaign_id"], "cell", cell_id,
                               asdict(cell) | {"stage": stage, "offered_load": scenario.offered_load,
                                               "load_unit": scenario.load_unit,
                                               "cache_protocol": scenario.cache_protocol,
                                               "measurement_protocol": "mock-frozen-v1",
                                               "workload_group_id": scenario.group_id,
                                               "is_baseline": candidate.parameters == {}, "mock": True})
        result = EvaluationResult(evaluation_id, config_id, stage, cell_ids, "valid",
                                  artifacts={"mock": "true"})
        self.ledger.append(self.campaign["campaign_id"], "evaluation", evaluation_id,
                           asdict(result) | {"mock": True})
        return result

"""The optional one-load triage cannot masquerade as a two-load screen."""

import json
from dataclasses import asdict
from pathlib import Path

from inference_autoresearch.contracts import CandidateProposal, CellResult, EvaluationResult
from inference_autoresearch.search.controller import SearchController
from inference_autoresearch.search.domain import Domain, config_identity
from inference_autoresearch.storage import Ledger


ROOT = Path(__file__).resolve().parents[2]


class ThreeProposals:
    def __init__(self):
        self.index = 0

    def propose(self, context):
        self.index += 1
        return CandidateProposal(f"p{self.index}", {"max_num_seqs": (64, 128, 256)[self.index - 1]})


class StageEvaluator:
    def __init__(self, campaign, ledger):
        self.campaign, self.ledger = campaign, ledger
        self.calls = []

    def evaluate(self, candidate, scenario_ids, stage):
        self.calls.append((candidate.proposal_id, stage, tuple(scenario_ids)))
        config_id = config_identity(self.campaign,
                                    self.campaign["baseline"] | candidate.parameters)
        evaluation_id = f"eval-{candidate.proposal_id}-{stage}"
        cell_ids = []
        for scenario_id in scenario_ids:
            cell_id = f"{evaluation_id}:{scenario_id}"
            cell_ids.append(cell_id)
            if candidate.proposal_id == "p1" and stage == "triage":
                status, behavior, metrics = "failed", "unknown", {}
            elif candidate.proposal_id == "p2" and stage == "triage":
                status, behavior, metrics = "valid", "normal", {
                    "output_tokens_per_s": 90, "ttft_p99_ms": 230, "tpot_p99_ms": 65}
            elif candidate.proposal_id == "p3" and stage == "triage":
                status, behavior, metrics = "valid", "normal", {
                    "output_tokens_per_s": 110, "ttft_p99_ms": 220, "tpot_p99_ms": 45}
            else:
                status, behavior, metrics = "valid", "normal", {
                    "output_tokens_per_s": 100, "ttft_p99_ms": 200, "tpot_p99_ms": 60}
            cell = CellResult(cell_id, scenario_id, config_id, status, behavior=behavior,
                              counts={"planned": 2, "dispatched": 2, "completed": 2,
                                      "not_dispatched": 0, "failed": 0, "timed_out": 0,
                                      "canceled": 0, "censored": 0}, metrics=metrics)
            self.ledger.append(self.campaign["campaign_id"], "cell", cell_id, asdict(cell) | {
                "stage": stage, "offered_load": 2.56 if scenario_id == "lo" else 3.2,
                "load_unit": "requests_per_s", "cache_protocol": "cold_stream",
                "measurement_protocol": "fresh-server-triage-v1" if stage == "triage" else "fresh-server-cell-v1",
            })
        return EvaluationResult(evaluation_id, config_id, stage, cell_ids,
                                "failed" if candidate.proposal_id == "p1" and stage == "triage" else "valid")


def test_opt_in_triage_runs_matched_b0_and_only_promoted_full_screen(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign.json").read_text())
    campaign.update(campaign_id="triage-test", triage_scenario_id="lo",
                    triage_promotion_policy="not_point_dominated_by_matched_b0",
                    screen_scenario_ids=["lo", "hi"])
    domain = Domain.load(ROOT / "configs/search-domain.json")
    ledger = Ledger(tmp_path / "ledger.sqlite3")
    evaluator = StageEvaluator(campaign, ledger)
    controller = SearchController(campaign, ROOT / "configs/campaign.json", domain,
                                  ThreeProposals(), evaluator, ledger, tmp_path, "mock")
    outcome = controller.run(max_proposals=3)
    assert evaluator.calls == [
        ("B0-triage", "triage", ("lo",)),
        ("p1", "triage", ("lo",)),
        ("p2", "triage", ("lo",)),
        ("p3", "triage", ("lo",)),
        ("B0-screen", "screen", ("lo", "hi")),
        ("p3", "screen", ("lo", "hi")),
    ]
    decisions = [event["payload"]["decision"] for event in ledger.events("triage-test", "triage_decision")]
    assert decisions == ["invalid", "dominated_by_matched_b0", "promote_to_two_load_screen"]
    assert len(ledger.events("triage-test", "search_triage_evaluation")) == 3
    assert len(ledger.events("triage-test", "search_evaluation")) == 1
    assert outcome.tested_count == 1


def test_default_triage_promotes_valid_point_dominated_cell(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign.json").read_text())
    campaign.update(campaign_id="safe-triage-test", triage_scenario_id="lo",
                    screen_scenario_ids=["lo", "hi"])
    domain = Domain.load(ROOT / "configs/search-domain.json")
    ledger = Ledger(tmp_path / "ledger.sqlite3")
    evaluator = StageEvaluator(campaign, ledger)
    proposer = ThreeProposals()
    proposer.index = 1  # The next candidate is p2: point-dominated at the triage load.
    controller = SearchController(campaign, ROOT / "configs/campaign.json", domain,
                                  proposer, evaluator, ledger, tmp_path, "mock")
    controller.run(max_proposals=1)
    assert ("p2", "screen", ("lo", "hi")) in evaluator.calls
    decision = ledger.events("safe-triage-test", "triage_decision")[0]["payload"]
    assert decision["decision"] == "promote_to_two_load_screen"
    assert decision["policy"] == "valid"


def test_triage_id_must_be_in_frozen_screen(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign.json").read_text())
    campaign.update(campaign_id="bad-triage-test", triage_scenario_id="unfrozen")
    ledger = Ledger(tmp_path / "ledger.sqlite3")
    controller = SearchController(campaign, ROOT / "configs/campaign.json",
                                  Domain.load(ROOT / "configs/search-domain.json"),
                                  ThreeProposals(), StageEvaluator(campaign, ledger), ledger,
                                  tmp_path, "mock")
    try:
        controller.run(max_proposals=1)
    except ValueError as exc:
        assert "triage_scenario_id" in str(exc)
    else:
        raise AssertionError("unfrozen triage scenario must fail before GPU work")


def test_heldout_cells_never_enter_proposer_context(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign.json").read_text())
    campaign.update(campaign_id="heldout-context-test", screen_scenario_ids=["lo"],
                    heldout_scenario_ids=["hidden"])
    ledger = Ledger(tmp_path / "ledger.sqlite3")
    ledger.append("heldout-context-test", "cell", "hidden-cell", {
        "cell_id": "hidden-cell", "scenario_id": "hidden", "stage": "confirm",
        "status": "valid", "metrics": {"output_tokens_per_s": 9999}})

    class CaptureProposer:
        context = None

        def propose(self, context):
            self.context = context
            return CandidateProposal("visible-proposal", {"max_num_seqs": 128})

    proposer = CaptureProposer()
    controller = SearchController(campaign, ROOT / "configs/campaign.json",
                                  Domain.load(ROOT / "configs/search-domain.json"),
                                  proposer, StageEvaluator(campaign, ledger), ledger, tmp_path, "mock")
    controller.run(max_proposals=1)
    assert proposer.context is not None
    assert all(row.get("scenario_id") != "hidden" for row in proposer.context.recent_results)
    assert all(row.get("scenario_id") != "hidden" for scope in proposer.context.frontier
               for row in scope["cells"])

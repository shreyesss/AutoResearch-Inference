"""CPU-only checks that the overnight v2 path stays bounded and resumable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

optuna = pytest.importorskip("optuna")

from inference_autoresearch.search.controller import SearchController
from inference_autoresearch.search.domain import Domain
from inference_autoresearch.search.domain import config_identity
from inference_autoresearch.search.mock import MockEvaluator
from inference_autoresearch.search.optimizer import OptunaProposer
from inference_autoresearch.search.qualification import assess
from inference_autoresearch.storage import Ledger
from inference_autoresearch.workloads.registry import ScenarioRegistry


ROOT = Path(__file__).resolve().parents[2]


def _setup(tmp_path: Path):
    campaign_path = ROOT / "configs/campaign-v2.json"
    campaign = json.loads(campaign_path.read_text())
    domain = Domain.load(ROOT / campaign["search_domain_path"])
    registry = ScenarioRegistry(ROOT / campaign["workload_registry"], root=ROOT)
    artifact_root = tmp_path / "mock"
    ledger = Ledger(artifact_root / "ledger.sqlite3")
    evaluator = MockEvaluator(campaign, registry, domain, artifact_root, ledger)
    proposer = OptunaProposer(campaign, domain, artifact_root, ledger, "mock")
    return campaign_path, campaign, domain, registry, artifact_root, ledger, evaluator, proposer


def test_v2_optuna_search_uses_only_one_mixed_cell_and_resumes(tmp_path: Path):
    path, campaign, domain, _registry, root, ledger, evaluator, proposer = _setup(tmp_path)
    controller = SearchController(campaign, path, domain, proposer, evaluator,
                                  ledger, root, "mock")
    assert isinstance(proposer.study.sampler, optuna.samplers.TPESampler)
    result = controller.run(max_proposals=2)
    assert result.proposed_count == result.tested_count == 2
    cells = [row["payload"] for row in ledger.events(campaign["campaign_id"], "cell")]
    assert len(cells) == 3  # one B0, one mixed screen per proposal
    assert {row["stage"] for row in cells} == {"triage"}
    assert {row["scenario_id"] for row in cells} == {"qwen-ops-mixed-reference-v1"}
    proposals = [row["payload"]["proposal"] for row in
                 ledger.events(campaign["campaign_id"], "proposal")]
    assert all("enable_prefix_caching" not in row["parameters"] and
               "mtp_draft_tokens" not in row["parameters"] for row in proposals)
    study = optuna.load_study(study_name=campaign["campaign_id"],
                              storage=f"sqlite:///{root / 'optimizer/optuna.sqlite3'}")
    assert len([trial for trial in study.trials if trial.state.is_finished()]) >= 2
    assert len([trial for trial in study.trials if trial.state == optuna.trial.TrialState.COMPLETE]) == 2

    resumed = OptunaProposer(campaign, domain, root, ledger, "mock")
    next_result = SearchController(campaign, path, domain, resumed, evaluator,
                                   ledger, root, "mock").run(max_proposals=3, resume=True)
    assert next_result.proposed_count == next_result.tested_count == 3
    assert len(ledger.events(campaign["campaign_id"], "cell")) == 4


def test_v2_qualification_requires_matched_triage_b0(tmp_path: Path):
    _path, campaign, domain, registry, root, ledger, _evaluator, _proposer = _setup(tmp_path)
    before = assess(campaign, domain, ledger, registry, root, backend="real")
    assert not before["search_allowed"]
    scenario = registry.load("qwen-ops-mixed-reference-v1")
    count = scenario.expected_count
    ledger.append(campaign["campaign_id"], "cell", "test-b0", {
        "cell_id": "test-b0", "scenario_id": scenario.scenario_id,
        "config_id": config_identity(campaign, campaign["baseline"]),
        "is_baseline": True, "stage": "triage",
        "measurement_protocol": "fresh-server-triage-v1",
        "offered_load": scenario.offered_load, "load_unit": scenario.load_unit,
        "cache_protocol": scenario.cache_protocol,
        "status": "valid", "behavior": "normal", "evidence_grade": "provisional",
        "counts": {"planned": count, "dispatched": count, "completed": count,
                   "not_dispatched": 0, "failed": 0, "timed_out": 0,
                   "canceled": 0, "censored": 0},
        "metrics": {"output_tokens_per_s": 55.0, "ttft_p99_ms": 9000.0,
                    "tpot_p99_ms": 65.0},
    })
    after = assess(campaign, domain, ledger, registry, root, backend="real")
    assert after["search_allowed"]
    assert after["qualification_grade"] == "exploratory_fast_gate"

import json
import fcntl
from pathlib import Path
from types import SimpleNamespace

import pytest

from inference_autoresearch.search.domain import Domain
from inference_autoresearch.contracts import CandidateProposal
from inference_autoresearch.search.proposer import CodexProposer
from inference_autoresearch.search.sla_controller import (
    SLASearchError, SLAServingController, screen_viability, select_screen_finalists,
)


ROOT = Path(__file__).resolve().parents[2]


def _screen(cell_id, throughput, ttft, tpot, *, status="valid"):
    return {"cell_id": cell_id, "scenario_id": "mixed", "offered_load": .1,
            "load_unit": "requests_per_s", "cache_protocol": "cold_stream",
            "stage": "triage", "measurement_protocol": "fresh-server-triage-v1",
            "status": status, "behavior": "normal",
            "counts": {"planned": 36, "dispatched": 36, "completed": 36,
                       "not_dispatched": 0, "failed": 0, "timed_out": 0,
                       "canceled": 0, "censored": 0},
            "metrics": {"output_tokens_per_s": throughput, "ttft_p50_ms": ttft * .6,
                        "ttft_p90_ms": ttft, "tpot_p50_ms": tpot * .8,
                        "tpot_p90_ms": tpot, "ttft_p99_ms": ttft * 1.1,
                        "tpot_p99_ms": tpot * 1.1}}


def test_v3_screen_rejects_only_invalid_or_predeclared_large_regressions():
    b0 = _screen("b0", 100, 1000, 50)
    rule = {"min_throughput_fraction_of_b0": .5,
            "max_ttft_p90_multiplier_of_b0": 2,
            "max_tpot_p90_multiplier_of_b0": 2}
    assert screen_viability(_screen("near", 80, 1500, 80), b0, rule)["promote_to_shortlist"]
    bad = screen_viability(_screen("bad", 30, 2200, 120), b0, rule)
    assert set(bad["reason_codes"]) == {
        "large_regression_output_tokens_per_s", "large_regression_ttft_p90_ms",
        "large_regression_tpot_p90_ms"}
    invalid = screen_viability(_screen("invalid", 100, 1000, 50, status="invalid"), b0, rule)
    assert invalid["reason_codes"] == ["screen_invalid_or_incomplete"]


def test_v3_shortlist_keeps_all_viable_but_selects_complementary_provisional_finalists():
    rows = [_screen("a", 100, 1000, 50) | {"screen_promoted": True},
            _screen("b", 120, 1100, 45) | {"screen_promoted": True},
            _screen("dominated", 80, 1500, 60) | {"screen_promoted": True},
            _screen("rejected", 200, 800, 30) | {"screen_promoted": False}]
    shortlist = select_screen_finalists(rows, 2)
    assert shortlist["selected_cell_ids"] == ["b", "a"]
    assert shortlist["nondominated_cell_ids"] == ["b", "a"]
    assert shortlist["all_viable_cell_ids"] == ["a", "b", "dominated"]
    assert shortlist["evidence_grade"] == "provisional_36_request_screen"
    assert "optimum" in shortlist["limitation"]
    assert [item["reason"] for item in shortlist["selection_rationale"]] == [
        "highest_screen_output_tokens_per_s", "lowest_balanced_relative_screen_p50_p90_latency_among_remaining"]
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3c.json").read_text())
    assert campaign["sla_search"]["max_finalists"] == campaign["search_budget"]["max_expanded_finalists"] == 2
    assert campaign["search_budget"]["max_distinct_proposals"] == 8


def test_v3_preflight_refuses_missing_approved_study_before_evaluator(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3c.json").read_text())
    campaign["sla_study_path"] = "missing-study.json"
    campaign_path = tmp_path / "configs/campaign-sla-serving-v3c.json"
    campaign_path.parent.mkdir()
    campaign_path.write_text(json.dumps(campaign))
    domain = Domain.load(ROOT / "configs/search-domain-v2.json")
    proposer = CodexProposer(domain, tmp_path / "artifacts",
                             sla_study_path=tmp_path / "missing-study.json")

    class Registry:
        def list(self):
            return campaign["screen_scenario_ids"] + campaign["development_scenario_ids"]

    class NeverEvaluate:
        def evaluate(self, *args, **kwargs):
            raise AssertionError("preflight must not launch a server")

    controller = SLAServingController(campaign, campaign_path, domain, Registry(),
                                      proposer, NeverEvaluate(), None, tmp_path / "artifacts")
    with pytest.raises(SLASearchError, match="approved active SLA study is absent"):
        controller.run()


def test_v3_cli_has_explicit_gpu_free_preflight_and_real_codex_command():
    from inference_autoresearch.cli import build_parser

    args = build_parser().parse_args(["sla-search", "--backend", "real",
                                "--campaign", "configs/campaign-sla-serving-v3c.json", "--check"])
    assert args.command == "sla-search" and args.check is True
    assert args.backend == "real"


def test_v3_search_refuses_concurrent_process_before_gpu_or_agent(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3c.json").read_text())
    domain = Domain.load(ROOT / "configs/search-domain-v2.json")
    campaign_path = tmp_path / "configs/campaign.json"
    campaign_path.parent.mkdir()
    campaign_path.write_text(json.dumps(campaign))
    proposer = CodexProposer(domain, tmp_path / "artifacts", sla_study_path=tmp_path / "absent.json")
    controller = SLAServingController(campaign, campaign_path, domain, None,
                                      proposer, None, None, tmp_path / "artifacts")
    lock_path = tmp_path / "artifacts/search-process.lock"
    lock_path.parent.mkdir()
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with pytest.raises(SLASearchError, match="another v3 SLA search process"):
            controller.run()


def test_all_proposals_receive_only_prior_short_screen_feedback_before_finalist_evaluations(tmp_path, monkeypatch):
    import inference_autoresearch.search.sla_controller as module

    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3c.json").read_text())
    campaign["search_budget"]["max_distinct_proposals"] = 2
    campaign["sla_search"]["max_finalists"] = 2
    campaign["sla_study_path"] = ".artifacts/v3-independent-capture/active.json"
    campaign_path = tmp_path / "configs/campaign.json"
    campaign_path.parent.mkdir()
    campaign_path.write_text(json.dumps(campaign))
    study_path = tmp_path / campaign["sla_study_path"]
    study_path.parent.mkdir(parents=True)
    study_path.write_text("{}")
    rate_lock = {"schema_version": "rate-screen-lock-v1", "claim": "rate_matched_stochastic_36_request_triage_only",
                 "selected_rate_rps": .2}
    lock_path = tmp_path / "artifacts/screen-rate-lock.json"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps(rate_lock))
    audit = tmp_path / ".artifacts/v3-independent-capture/development-input-audit.json"
    audit.write_text("{}")
    domain = Domain.load(ROOT / "configs/search-domain-v2.json")
    calls = []
    contexts = []
    cells = {}
    baseline = _screen("b0-screen", 100, 1000, 50)
    cells[baseline["cell_id"]] = baseline

    class Proposer:
        def propose(self, context):
            contexts.append(context)
            number = len(contexts)
            return CandidateProposal(proposal_id=f"candidate-{number}",
                parameters={"max_num_batched_tokens": (4096 if number == 1 else 16384)},
                experiment_kind="exploration", hypothesis="Test scheduler token budget")

    class Evaluator:
        def evaluate(self, proposal, scenarios, stage):
            calls.append((proposal.proposal_id, stage))
            if proposal.proposal_id == "B0-sla-screen":
                return SimpleNamespace(cell_ids=[baseline["cell_id"]], status="valid")
            produced = []
            for scenario in scenarios:
                cell_id = f"{proposal.proposal_id}-{scenario}"
                cell = _screen(cell_id, 90, 1100, 55) | {
                    "scenario_id": scenario, "config_id": proposal.proposal_id, "stage": stage}
                cells[cell_id] = cell
                produced.append(cell_id)
            return SimpleNamespace(cell_ids=produced, status="valid")

    class Ledger:
        def claim(self, *args):
            pass
        def events(self, *args):
            return []
        def append(self, *args):
            pass

    monkeypatch.setattr(module, "load_split_plan", lambda *args, **kwargs: {})
    monkeypatch.setattr(module, "audit_confirmation_pairs", lambda *args, **kwargs: {})
    curve_calls = []
    monkeypatch.setattr(module, "export_sla_curves", lambda sources, output: (
        curve_calls.append((sources, output)) or {"point_count": 2}))
    controller = SLAServingController(campaign, campaign_path, domain, None,
        Proposer(), Evaluator(), Ledger(), tmp_path / "artifacts")
    controller.preflight = lambda: (
        {"policy": {"sha256": "p"}, "baseline_adaptive_run_paths": [],
         "adaptive_development": {"baseline_cell_sha256_by_path": {}},
         "capacity_confirmation": {"split_plan_path": "split.json"}},
        {}, [{"cell_id": "b0-dev-1042"}, {"cell_id": "b0-dev-1043"}])
    controller._cells = lambda ids: [cells[cell_id] for cell_id in ids]
    controller._screen_evaluate = lambda proposal, screen_id, lock: (
        controller.evaluator.evaluate(proposal, [screen_id], "triage"))
    controller._assess_cell = lambda cell, policy: {
        "cell_id": cell["cell_id"], "observed_feasible": True}
    profile_source = tmp_path / ".artifacts/autoresearch-codebase/profile/sla-profile-points.json"
    profile_source.parent.mkdir(parents=True)
    profile_source.write_text("{}")
    controller._profile_finalist = lambda proposal, study_path: {
        "process_exit_code": 0, "timed_out": False,
        "result": {"status": "observed", "artifacts": {"all_points": str(profile_source)}}}

    controller.run()

    assert calls == [
        ("B0-sla-screen", "triage"),
        ("candidate-1", "triage"), ("candidate-2", "triage"),
        ("candidate-1", "expanded"), ("candidate-2", "expanded")]
    assert len(contexts) == 2
    assert not [cell for cell in contexts[1].recent_results if cell.get("stage") == "expanded"]
    assert {cell["cell_id"] for cell in contexts[1].recent_results} == {
        "b0-screen", "candidate-1-qwen-ops-mixed-reference-v1"}
    assert contexts[1].recent_results[-1]["sla_screen_decision"]["promote_to_shortlist"] is True
    assert len(curve_calls) == 1
    assert curve_calls[0][0] == [profile_source, profile_source]

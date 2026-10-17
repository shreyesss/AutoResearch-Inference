import json
import fcntl
from pathlib import Path

import pytest

from inference_autoresearch.search.domain import Domain
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
            "metrics": {"output_tokens_per_s": throughput, "ttft_p90_ms": ttft,
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


def test_v3_shortlist_promotes_all_viable_and_reports_provisional_pareto():
    rows = [_screen("a", 100, 1000, 50) | {"screen_promoted": True},
            _screen("b", 120, 1100, 45) | {"screen_promoted": True},
            _screen("dominated", 80, 1500, 60) | {"screen_promoted": True},
            _screen("rejected", 200, 800, 30) | {"screen_promoted": False}]
    shortlist = select_screen_finalists(rows, 4)
    assert shortlist["selected_cell_ids"] == ["b", "a", "dominated"]
    assert shortlist["nondominated_cell_ids"] == ["b", "a"]
    assert shortlist["all_viable_cell_ids"] == ["a", "b", "dominated"]
    assert shortlist["evidence_grade"] == "provisional_36_request_screen"
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3.json").read_text())
    assert campaign["sla_search"]["max_finalists"] == campaign["search_budget"]["max_distinct_proposals"]


def test_v3_preflight_refuses_missing_approved_study_before_evaluator(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3.json").read_text())
    campaign["sla_study_path"] = "missing-study.json"
    campaign_path = tmp_path / "configs/campaign-sla-serving-v3.json"
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
                                "--campaign", "configs/campaign-sla-serving-v3.json", "--check"])
    assert args.command == "sla-search" and args.check is True
    assert args.backend == "real"


def test_v3_search_refuses_concurrent_process_before_gpu_or_agent(tmp_path):
    campaign = json.loads((ROOT / "configs/campaign-sla-serving-v3.json").read_text())
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

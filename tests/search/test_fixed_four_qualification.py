"""Four-task exploratory search needs actual matched B0 evidence for every task."""

import json
import hashlib
from types import SimpleNamespace

import pytest

from inference_autoresearch.search import qualification as module
from inference_autoresearch.search.controller import SearchGateError, qualification_ok
from inference_autoresearch.search.domain import Domain, scientific_campaign_hash, sha


IDS = module.FIXED_FOUR_SCENARIOS


class Registry:
    def __init__(self, root):
        self.root = root
        self.missing = set()

    def load(self, scenario_id):
        if scenario_id in self.missing:
            raise ValueError("not registered")
        return SimpleNamespace(
            offered_load=0.5, load_unit="requests_per_s", cache_protocol="cold_stream",
            expected_count=16,
            scenario_id=scenario_id,
            metadata={"manifest": {"readiness": "validated",
                                   "traffic_mode": "independent_open_loop",
                                   "workload_card_path": f"{scenario_id}.card.json",
                                   "payload_sha256": f"sha-{scenario_id}"}})


class Ledger:
    def __init__(self, rows):
        self.rows = rows

    def events(self, campaign_id, kind):
        assert kind == "cell"
        return [{"payload": row} for row in self.rows]


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "config_identity", lambda *args: "B0", raising=False)
    # _assess_fixed_four imports this dynamically from domain.
    monkeypatch.setattr("inference_autoresearch.search.domain.config_identity", lambda *args: "B0")
    campaign = {
        "campaign_id": "four-test", "screen_scenario_ids": list(IDS),
        "baseline": {}, "qualification_requirements": {"mode": "fixed-four-v1"},
    }
    validation = {"schema_version": "ops4-frozen-validation-v1", "scenarios": {
        scenario_id: {"status": "validated", "planned": 16, "http_200": 16,
                      "payload_match": True, "output_caps_realized": True,
                      "schedule_match": True, "asset_sha256": f"sha-{scenario_id}",
                      "raw_sha256": "raw", "records_sha256": "records"}
        for scenario_id in IDS}}
    encoded = json.dumps(validation).encode()
    (tmp_path / "validation.json").write_bytes(encoded)
    report_hash = hashlib.sha256(encoded).hexdigest()
    for scenario_id in IDS:
        (tmp_path / f"{scenario_id}.card.json").write_text(json.dumps({
            "validation_report_path": "validation.json",
            "validation_report_sha256": report_hash}))
    rows = [{
        "cell_id": f"cell-{scenario_id}", "scenario_id": scenario_id,
        "config_id": "B0", "is_baseline": True, "stage": "screen",
        "measurement_protocol": "fresh-server-cell-v1",
        "offered_load": 0.5, "load_unit": "requests_per_s",
        "cache_protocol": "cold_stream", "status": "valid", "behavior": "normal",
        "counts": {"planned": 16, "dispatched": 16, "completed": 16,
                   "not_dispatched": 0, "failed": 0, "timed_out": 0,
                   "canceled": 0, "censored": 0},
        "metrics": {"output_tokens_per_s": 100.0,
                    "ttft_p99_ms": 200.0, "tpot_p99_ms": 50.0},
    } for scenario_id in IDS]
    return campaign, Registry(tmp_path), Ledger(rows), Domain({"parameters": {}})


def assess(setup, tmp_path):
    campaign, registry, ledger, domain = setup
    return module.assess(campaign, domain, ledger, registry, tmp_path)


def test_four_complete_registered_screen_b0_cells_allow_exploratory_search(setup, tmp_path):
    report = assess(setup, tmp_path)
    assert report["search_allowed"] is True
    assert report["qualification_grade"] == "exploratory_four_task"
    assert report["sensitivity_qualified"] is False
    assert len([x for x in report["evidence_ids"] if x.startswith("baseline_cell:")]) == 4


@pytest.mark.parametrize("field,value", [
    ("config_id", "other-config"), ("is_baseline", False),
    ("stage", "pilot"), ("measurement_protocol", "shared-server-v1"),
    ("offered_load", 1.0), ("mock", True),
])
def test_rejects_unmatched_or_nonfresh_b0(setup, tmp_path, field, value):
    setup[2].rows[0][field] = value
    report = assess(setup, tmp_path)
    assert report["search_allowed"] is False
    assert f"eligible_matched_screen_b0_missing:{IDS[0]}" in report["blocked_reasons"]


def test_rejects_missing_request_or_input_or_suite_member(setup, tmp_path):
    setup[2].rows[1]["counts"]["completed"] = 15
    assert assess(setup, tmp_path)["search_allowed"] is False
    setup[2].rows[1]["counts"]["completed"] = 16
    setup[1].missing.add(IDS[2])
    assert assess(setup, tmp_path)["search_allowed"] is False
    setup[1].missing.clear()
    setup[0]["screen_scenario_ids"] = list(IDS[:3])
    assert "fixed_four_screen_suite_mismatch" in assess(setup, tmp_path)["blocked_reasons"]


def test_rejects_changed_or_failed_independent_validation(setup, tmp_path):
    card_path = tmp_path / f"{IDS[0]}.card.json"
    card = json.loads(card_path.read_text())
    card["validation_report_sha256"] = "0" * 64
    card_path.write_text(json.dumps(card))
    report = assess(setup, tmp_path)
    assert report["search_allowed"] is False
    assert any(reason.startswith(f"screen_scenario_unqualified:{IDS[0]}") for reason in report["blocked_reasons"])


def test_triage_and_heldout_are_not_four_task_search(setup, tmp_path):
    setup[0]["triage_scenario_id"] = IDS[0]
    assert "fixed_four_triage_disallowed" in assess(setup, tmp_path)["blocked_reasons"]
    setup[0].pop("triage_scenario_id")
    setup[0]["heldout_scenario_ids"] = [IDS[3]]
    assert "fixed_four_heldout_scenarios_disallowed" in assess(setup, tmp_path)["blocked_reasons"]


def test_controller_rechecks_live_four_task_evidence(setup, tmp_path):
    campaign, registry, ledger, domain = setup
    report_path = tmp_path / "qualification.json"
    campaign["real_search_qualification_path"] = str(report_path)
    report_path.write_text(json.dumps(assess(setup, tmp_path)))
    assert qualification_ok(campaign, domain, tmp_path / "campaign.json", "real",
                            ledger, registry, tmp_path)["search_allowed"] is True
    ledger.rows[3]["status"] = "failed"
    with pytest.raises(SearchGateError, match="machine evidence"):
        qualification_ok(campaign, domain, tmp_path / "campaign.json", "real",
                         ledger, registry, tmp_path)


def test_controller_rejects_false_sensitivity_claim(setup, tmp_path):
    campaign, registry, ledger, domain = setup
    report = assess(setup, tmp_path)
    report["sensitivity_qualified"] = True
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(report))
    campaign["real_search_qualification_path"] = str(path)
    with pytest.raises(SearchGateError, match="sensitivity claim"):
        qualification_ok(campaign, domain, tmp_path / "campaign.json", "real",
                         ledger, registry, tmp_path)


def test_legacy_qualification_without_four_task_fields_still_rechecks(setup, tmp_path, monkeypatch):
    campaign, registry, ledger, domain = setup
    campaign["qualification_requirements"] = {}
    report = {
        "search_allowed": True, "backend": "real", "source": "iar qualify",
        "campaign_hash": scientific_campaign_hash(campaign), "domain_hash": domain.digest,
        "qualification_requirements_hash": sha({}),
        "provenance_validated": True, "traffic_validated": True,
        "baseline_characterized": True, "sensitivity_qualified": True,
        "evidence_ids": ["legacy-evidence"],
    }
    path = tmp_path / "legacy-report.json"
    path.write_text(json.dumps(report))
    campaign["real_search_qualification_path"] = str(path)
    monkeypatch.setattr(module, "assess", lambda *args, **kwargs: report)
    assert qualification_ok(campaign, domain, tmp_path / "campaign.json", "real",
                            ledger, registry, tmp_path) == report

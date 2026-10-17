import json

from inference_autoresearch.evaluation.sensitivity import build_sensitivity_report, lock_pilot_plan
from inference_autoresearch.search.domain import Domain
from inference_autoresearch.storage.ledger import Ledger


def test_matched_scope_only_and_no_automatic_gate(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite")
    base = {"scenario_id": "short", "workload_group_id": "chat", "offered_load": 3.2,
            "load_unit": "requests_per_s", "cache_protocol": "cold_stream",
            "measurement_protocol": "fresh-server-cell-v1", "stage": "pilot",
            "status": "valid", "behavior": "normal", "controller_validation": [],
            "counts": {"planned": 200, "completed": 200},
            "metrics": {"output_tokens_per_s": 690, "ttft_p99_ms": 225, "tpot_p99_ms": 64}}
    ledger.append("c", "cell", "b0", base | {"cell_id": "b0", "config_id": "b0", "is_baseline": True})
    cand = base | {"cell_id": "mtp", "config_id": "mtp", "is_baseline": False,
                   "metrics": {"output_tokens_per_s": 750, "ttft_p99_ms": 260, "tpot_p99_ms": 33}}
    ledger.append("c", "cell", "mtp", cand)
    ledger.append("c", "cell", "other", cand | {"cell_id": "other", "stage": "confirm"})
    report = build_sensitivity_report({"campaign_id": "c", "domain": {}}, ledger, tmp_path / "report.json")
    assert report["sensitivity_qualified"] is False
    assert len(report["contrasts"]) == 1
    assert report["contrasts"][0]["classification"] == "inconclusive_single_window"
    assert report["contrasts"][0]["effects"]["tpot_p99_ms"]["absolute_delta"] == -31
    assert len(report["excluded"]) == 1


def test_predeclared_repeated_mechanism_can_qualify_sensitivity(tmp_path):
    domain_path = tmp_path / "domain.json"
    domain_path.write_text(json.dumps({"parameters": {"mtp_draft_tokens": {"baseline": 0, "values": [0, 1]},
                                                     "max_num_seqs": {"baseline": 512, "values": [64, 512]}}}))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"schema_version": "pilot-plan-v1", "campaign_id": "c",
                                     "domain_hash": Domain.load(domain_path).digest,
                                     "protocol_id": "fresh-server-cell-v1", "stage": "pilot",
                                     "min_matched_repeats": 2,
                                     "contrasts": [
                                         {"contrast_id": "mtp", "role": "mechanism",
                                          "candidate_overrides": {"mtp_draft_tokens": 1},
                                          "scenario_ids": ["short"],
                                          "required_binding_observation": "mtp_acceptance_fraction"},
                                         {"contrast_id": "cap64", "role": "negative_control",
                                          "candidate_overrides": {"max_num_seqs": 64},
                                          "scenario_ids": ["short"], "expected_flat": True,
                                          "expected_observation": {"name": "queue_max", "equals": 0}},
                                     ]}))
    campaign = {"campaign_id": "c", "search_domain_path": str(domain_path),
                "qualification_requirements": {"pilot_plan_path": str(plan_path)}}
    ledger = Ledger(tmp_path / "ledger.sqlite")
    lock_pilot_plan(campaign, ledger)
    for config_id, overrides in (("mtp", {"mtp_draft_tokens": 1}), ("cap64", {"max_num_seqs": 64})):
        ledger.append("c", "resolved_config", config_id, {"overrides": overrides})
    common = {"scenario_id": "short", "workload_group_id": "chat", "offered_load": 3.2,
              "load_unit": "requests_per_s", "cache_protocol": "cold_stream",
              "measurement_protocol": "fresh-server-cell-v1", "stage": "pilot",
              "status": "valid", "behavior": "normal", "controller_validation": [],
              "counts": {"planned": 200, "completed": 200}}
    for idx in range(2):
        for config_id, is_baseline, output, ttft, tpot, gauge in (
            ("b0", True, 690 + idx, 225 + idx, 64 + idx, {"queue_max": 0}),
            ("mtp", False, 740 + idx, 235 + idx, 35 + idx,
             {"queue_max": 0, "mtp_acceptance_fraction": .8}),
            ("cap64", False, 690 + idx, 225 + idx, 64 + idx, {"queue_max": 0}),
        ):
            cell_id = f"{config_id}-{idx}"
            ledger.append("c", "cell", cell_id, common | {"cell_id": cell_id,
                          "config_id": config_id, "is_baseline": is_baseline,
                          "metrics": {"output_tokens_per_s": output, "ttft_p99_ms": ttft,
                                      "tpot_p99_ms": tpot},
                          "diagnostics": {"server_gauges": gauge}})
    report = build_sensitivity_report(campaign, ledger, tmp_path / "report.json")
    assert report["sensitivity_qualified"] is True
    assert all(item["qualified"] for item in report["plan_checks"])

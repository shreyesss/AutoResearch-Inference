import csv
import json
from pathlib import Path

import pytest

from inference_autoresearch.search.report import export, export_suite_front


SCENARIOS = ["chat", "mixed", "agent", "burst"]


def cell(config, scenario, *, throughput=100, ttft=200, tpot=50,
         protocol="fresh-server-cell-v1", stage="screen", load=2.0,
         status="valid", baseline=False, suffix=""):
    return {"cell_id": f"{config}-{scenario}{suffix}", "config_id": config,
            "scenario_id": scenario, "stage": stage, "measurement_protocol": protocol,
            "offered_load": load, "load_unit": "requests_per_s",
            "cache_protocol": "cold_stream", "status": status, "behavior": "normal",
            "is_baseline": baseline,
            "counts": {"planned": 10, "dispatched": 10, "completed": 10,
                       "not_dispatched": 0, "failed": 0, "timed_out": 0,
                       "canceled": 0, "censored": 0},
            "metrics": {"output_tokens_per_s": throughput, "ttft_p99_ms": ttft,
                        "tpot_p99_ms": tpot}}


def suite(tmp_path, rows):
    paths = export(rows, tmp_path, screen_scenario_ids=SCENARIOS)
    return json.loads(Path(paths["suite_front_json"]).read_text()), list(
        csv.DictReader(Path(paths["suite_front_csv"]).open()))


def test_complete_four_task_front_keeps_tradeoff_and_reports_dominance(tmp_path):
    rows = [cell("B0", s, baseline=True) for s in SCENARIOS]
    rows += [cell("better", s, throughput=110, ttft=180, tpot=45) for s in SCENARIOS]
    rows += [cell("tradeoff", s, throughput=120, ttft=210, tpot=40) for s in SCENARIOS]
    result, flat = suite(tmp_path, rows)
    assert len(result["objectives"]) == 12
    scope = result["scopes"][0]
    assert set(scope["front_config_ids"]) == {"better", "tradeoff"}
    by_id = {r["config_id"]: r for r in scope["configurations"]}
    assert by_id["B0"]["is_baseline"] is True
    assert by_id["B0"]["status"] == "dominated"
    assert by_id["B0"]["dominated_by"] == ["better"]
    assert by_id["tradeoff"]["status"] == "frontier"
    assert {r["config_id"] for r in flat} == {"B0", "better", "tradeoff"}
    assert flat[0]["chat.output_tokens_per_s"] != ""


def test_partial_failed_duplicate_and_incompatible_cells_never_enter_front(tmp_path):
    rows = [cell("B0", s, baseline=True) for s in SCENARIOS]
    rows += [cell("partial", s, throughput=500, ttft=1, tpot=1) for s in SCENARIOS[:3]]
    rows += [cell("failed", s, throughput=500, ttft=1, tpot=1,
                  status="functional_failed" if s == "burst" else "valid") for s in SCENARIOS]
    rows += [cell("duplicate", s, throughput=500, ttft=1, tpot=1) for s in SCENARIOS]
    rows += [cell("duplicate", "chat", throughput=500, ttft=1, tpot=1, suffix="-again")]
    rows += [cell("wrong-load", s, throughput=500, ttft=1, tpot=1,
                  load=3.0 if s == "mixed" else 2.0) for s in SCENARIOS]
    rows += [cell("triage-only", "chat", stage="triage", throughput=1000)]
    result, _ = suite(tmp_path, rows)
    scope = result["scopes"][0]
    assert scope["front_config_ids"] == ["B0"]
    by_id = {r["config_id"]: r for r in scope["configurations"]}
    assert "burst:missing_screen_cell" in by_id["partial"]["reason_codes"]
    assert "burst:no_eligible_cell" in by_id["failed"]["reason_codes"]
    assert "chat:duplicate_eligible_cells" in by_id["duplicate"]["reason_codes"]
    assert "mixed:incompatible_load_or_cache" in by_id["wrong-load"]["reason_codes"]
    assert "chat:missing_screen_cell" in by_id["triage-only"]["reason_codes"]
    assert all(by_id[c]["status"] == "incomplete" for c in
               ("partial", "failed", "duplicate", "wrong-load", "triage-only"))


def test_protocol_scopes_do_not_mix_and_nan_is_ineligible(tmp_path):
    rows = [cell("B0", s, baseline=True) for s in SCENARIOS]
    rows += [cell("other-protocol", s, protocol="mock-frozen-v1",
                  throughput=200) for s in SCENARIOS]
    rows += [cell("bad-number", s, throughput=float("nan") if s == "chat" else 300)
             for s in SCENARIOS]
    result, _ = suite(tmp_path, rows)
    scopes = {s["measurement_protocol"]: s for s in result["scopes"]}
    assert scopes["fresh-server-cell-v1"]["front_config_ids"] == ["B0"]
    assert scopes["mock-frozen-v1"]["front_config_ids"] == ["other-protocol"]
    configs = {c["config_id"]: c for c in scopes["fresh-server-cell-v1"]["configurations"]}
    assert "chat:no_eligible_cell" in configs["bad-number"]["reason_codes"]
    assert configs["other-protocol"]["status"] == "incomplete"


def test_one_task_regression_preserves_baseline_on_suite_front(tmp_path):
    rows = [cell("B0", s, baseline=True) for s in SCENARIOS]
    rows += [cell("three-gains", s, throughput=120,
                  ttft=250 if s == "burst" else 180, tpot=45) for s in SCENARIOS]
    result, _ = suite(tmp_path, rows)
    assert set(result["scopes"][0]["front_config_ids"]) == {"B0", "three-gains"}


def test_suite_export_demands_exactly_four_distinct_tasks(tmp_path):
    with pytest.raises(ValueError, match="four distinct"):
        export_suite_front([], ["a", "b", "c", "c"], tmp_path)


def test_triage_only_still_exports_incomplete_configuration(tmp_path):
    result, _ = suite(tmp_path, [cell("attempt", "chat", stage="triage")])
    row = result["scopes"][0]["configurations"][0]
    assert row["config_id"] == "attempt"
    assert row["status"] == "incomplete"
    assert "chat:missing_screen_cell" in row["reason_codes"]

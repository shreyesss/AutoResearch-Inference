import copy
import math

import pytest

from ideation.controls import expand_query, prescreen
from ideation.discovery import load_config
from pathlib import Path


def record():
    return {"target": {"benchmark": "agent-75", "metric": "amortized_time_per_output_token", "min_relative_gain": 0.01},
            "baseline_iteration": {"value": 10, "unit": "ms"},
            "component_savings": {"low": 45, "high": 83, "unit": "us"},
            "calls_per_iteration": 1, "exposed_fraction": {"low": 0.5, "high": 1},
            "progress": {"baseline_tokens": 4, "candidate_tokens": 4},
            "evidence": [{"source": "component-run-25", "scope": "component"}],
            "next_cheapest_falsifier": "CPU: check actual sampler path and complete-iteration call count from pinned code."}


def test_small_component_gain_does_not_become_service_gain():
    result = prescreen(record())
    assert result["estimates"]["saved_iteration_us"] == {"low": 22.5, "high": 83}
    assert result["target_relative_gain"]["high"] == pytest.approx(.0083)
    assert result["decision"] == "reject"
    assert result["validated"] is False
    assert result["evidence"][0]["scope"] == "component"


def test_accepted_progress_loss_can_overwhelm_faster_iteration():
    value = record()
    value["progress"]["candidate_tokens"] = 3
    assert prescreen(value)["target_relative_gain"]["high"] < 0


def test_no_guess_of_accepted_tokens_from_rollout_length():
    value = record()
    value["progress"] = {"baseline_tokens": 4, "rollout_length": 5}
    result = prescreen(value)
    assert result["target_relative_gain"] is None
    assert "candidate_amortized_us_per_token" not in result["estimates"]
    assert result["decision"] == "advance_diagnostic"
    assert any("candidate_tokens" in x for x in result["unknowns"])


def test_tail_metric_not_qualified_by_mean_iteration_arithmetic():
    value = record()
    value["target"]["metric"] = "p99_ITL"
    result = prescreen(value)
    assert result["target_relative_gain"] is None
    value["tail_guards"] = [{"name": "p99 ITL no regression", "passed": False}]
    assert prescreen(value)["decision"] == "reject"


def test_task_threshold_optional_and_unknown_exposure_not_assumed():
    value = record()
    del value["target"]["min_relative_gain"]
    assert prescreen(value)["decision"] == "advance_diagnostic"
    del value["exposed_fraction"]
    assert prescreen(value)["estimates"] == {}
    del value["next_cheapest_falsifier"]
    assert prescreen(value)["decision"] == "defer"


@pytest.mark.parametrize("field,value", [("calls_per_iteration", math.nan), ("calls_per_iteration", True), ("calls_per_iteration", -1), ("calls_per_iteration", math.inf)])
def test_invalid_numbers(field, value):
    item = record()
    item[field] = value
    with pytest.raises(ValueError):
        prescreen(item)


@pytest.mark.parametrize("unit", ["ns", "milliseconds", "tokens", None])
def test_reject_ambiguous_units(unit):
    item = record()
    item["component_savings"]["unit"] = unit
    with pytest.raises(ValueError):
        prescreen(item)


def test_inconsistent_units_or_call_count_cannot_be_silently_clamped():
    item = record()
    item["component_savings"]["unit"] = "ms"
    with pytest.raises(ValueError, match="whole iteration"):
        prescreen(item)


def test_negative_savings_and_overlap_bounds_ordered_correctly():
    item = record()
    item["component_savings"] = {"low": -83, "high": -45, "unit": "us"}
    result = prescreen(item)
    assert result["estimates"]["saved_iteration_us"] == {"low": -83, "high": -22.5}


def test_queries_match_real_taxonomy_and_are_bounded():
    config = load_config(Path(__file__).parents[1] / "config/discovery.json")
    result = expand_query("H200 speculative decoding KV cache latency", config, "2026-09-01", "2026-10-22")
    assert result["matched_families"]
    assert len(result["queries"]) <= 8
    assert result["limits"]["network_calls"] == 0
    assert "to_publication_date:2026-10-21" in result["queries"][0]["openalex"]["filter"]
    assert "202610212359" in result["queries"][0]["arxiv"]["search_query"]
    assert result["queries"][0]["local"]["before"] == "2026-10-22"


def test_unrelated_domain_not_forced_to_inference():
    config = {"families": [{"id": "spec", "terms": ["speculative decoding", "MTP"]}]}
    result = expand_query("membrane desalination fouling", config)
    assert not result["matched_families"]
    assert all("MTP" not in q["terms"] for q in result["queries"])
    assert result["queries"][0]["terms"] == ["membrane desalination fouling"]


def test_date_errors_and_fts_injection_safe():
    with pytest.raises(ValueError):
        expand_query("topic", {}, "2026-10-22", "2026-10-01")
    result = expand_query('test " OR title:secret', {})
    assert result["queries"][0]["local"]["query"] == '"test   OR title:secret"'


@pytest.mark.parametrize("field", ["baseline_tokens", "candidate_tokens"])
@pytest.mark.parametrize("bad", [0, -1, True, float("nan"), float("inf")])
def test_invalid_accepted_progress(field, bad):
    item = record()
    item["progress"][field] = bad
    with pytest.raises(ValueError):
        prescreen(item)


def test_overflow_not_emitted_as_invalid_json():
    item = record()
    item["baseline_iteration"]["value"] = 1e308
    with pytest.raises(ValueError):
        prescreen(item)


def test_input_preserved_without_mutation():
    item = record()
    original = copy.deepcopy(item)
    result = prescreen(item)
    result["input"]["target"]["benchmark"] = "other"
    assert item == original


def test_local_recipes_execute_against_actual_fts_and_date_filters(tmp_path):
    from ideation.store import Store
    store = Store(tmp_path / "corpus.sqlite")
    for key, updated in [("old", "2026-09-01"), ("recent", "2026-10-21"), ("end", "2026-10-22")]:
        store.put({"id": key, "source": "github", "kind": "pr", "url": "https://example.test/" + key,
                   "title": "Speculative decoding regression", "body": "Draft acceptance and throughput", "updated_at": updated})
    plans = expand_query("speculative decoding", {"families": [{"id": "spec", "terms": ["speculative decoding"]}]}, "2026-10-01", "2026-10-22")
    for recipe in plans["queries"]:
        rows = store.search(**recipe["local"])
        assert all(row["id"] == "recent" for row in rows)
    assert store.search(**plans["queries"][0]["local"])[0]["id"] == "recent"
    for recipe in expand_query('test " OR title:secret', {})["queries"]:
        assert store.search(**recipe["local"]) == []
    store.db.close()

import csv
import json

import pytest

from inference_autoresearch.search.sla_curve_report import export_sla_curves


def _qualified(rate, *, tokens, ttft, tpot, feasible=True):
    classes = {}
    for name in ("chat", "agent", "code", "document"):
        classes[name] = {
            "planned": 60, "completed": 60, "ttft_eligible": 60,
            "tpot_eligible": 60, "observed_feasible": feasible,
            "reason_codes": [] if feasible else ["ttft_deadline_exceeded"],
            "diagnostic_percentiles_ms": {
                "ttft": {"p50": ttft / 2, "p90": ttft},
                "tpot": {"p50": tpot / 2, "p90": tpot},
            },
        }
    return {
        "status": "valid", "reason_codes": [], "planned": 240,
        "completed": 240, "realized_rate_rps": rate * .98,
        "observed_feasible": feasible,
        "native_summary_metrics": {
            "output_tokens_per_s": tokens, "ttft_p50_ms": ttft / 2,
            "ttft_p90_ms": ttft, "tpot_p50_ms": tpot / 2,
            "tpot_p90_ms": tpot,
        },
        "assessment": {"classes": classes, "observed_feasible": feasible},
    }


def _profile(config_id, points):
    return {
        "schema_version": "sla-profile-points-v1",
        "claim": "observed_development_points_no_confirmed_capacity",
        "capacity_confirmed": False, "config_id": config_id,
        "policy_id": "research-v3", "policy_sha256": "same-policy-hash",
        "development_scenario_id": "dev-1042", "points": points,
    }


def _point(rate, qualified):
    return {"rate_rps": rate, "arrival_seed": 42 + round(rate * 1_000_000),
            "screen": {"status": "valid", "reason_codes": []},
            "qualified": qualified}


def test_report_preserves_every_point_and_class_curve_without_capacity_claim(tmp_path):
    source = tmp_path / "profile.json"
    source.write_text(json.dumps(_profile("b0", [
        _point(.2, _qualified(.2, tokens=100, ttft=900, tpot=60)),
        _point(.3, _qualified(.3, tokens=130, ttft=800, tpot=50)),
        _point(.4, _qualified(.4, tokens=160, ttft=1200, tpot=65, feasible=False)),
        {"rate_rps": .5, "arrival_seed": 500042,
         "screen": {"status": "invalid", "reason_codes": ["client_dispatch_lag"]},
         "qualified": None},
    ])))
    result = export_sla_curves([source], tmp_path / "report")
    report = json.loads((tmp_path / "report/sla-curves.json").read_text())
    assert result["point_count"] == 4
    assert result["class_point_count"] == 12
    assert report["claim"] == "observed_in_sample_points_only_no_confirmed_capacity_or_frontier"
    assert report["provisional_nondominated_point_ids"] == [
        "profile-01-point-02", "profile-01-point-03"]
    assert report["observed_feasible_point_ids"] == [
        "profile-01-point-01", "profile-01-point-02"]
    with (tmp_path / "report/sla-curve-points.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert rows[-1]["qualified_status"] == "not_run"
    assert rows[-1]["reason_codes"] == '["client_dispatch_lag"]'
    with (tmp_path / "report/sla-curve-class-points.csv").open(newline="") as handle:
        classes = list(csv.DictReader(handle))
    chat = next(row for row in classes if row["point_id"] == "profile-01-point-02"
                and row["class"] == "chat")
    assert chat["ttft_p50_ms"] == "400.0"
    assert chat["ttft_p90_ms"] == "800.0"
    assert chat["tpot_p90_ms"] == "50.0"
    for name in ("load-curves.svg", "class-curves.svg", "throughput-latency.svg"):
        assert (tmp_path / "report" / name).is_file()


def test_multiple_profiles_require_same_policy_and_corpus(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(_profile("b0", [_point(.2, _qualified(.2, tokens=100,
                                                                     ttft=900, tpot=60))])))
    altered = _profile("candidate", [_point(.2, _qualified(.2, tokens=110,
                                                            ttft=890, tpot=59))])
    altered["development_scenario_id"] = "different-dev"
    second.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="same policy and development corpus"):
        export_sla_curves([first, second], tmp_path / "report")
    altered["development_scenario_id"] = "dev-1042"
    second.write_text(json.dumps(altered))
    report = export_sla_curves([first, second], tmp_path / "report")
    assert report["point_count"] == 2
    data = json.loads((tmp_path / "report/sla-curves.json").read_text())
    assert data["provisional_nondominated_point_ids"] == ["profile-02-point-01"]

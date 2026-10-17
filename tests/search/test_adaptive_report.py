import csv
import hashlib
import json
from pathlib import Path

from inference_autoresearch.search.report import export_adaptive_points
from inference_autoresearch.contracts import ProposalContext
from inference_autoresearch.search.proposer import _stage_measurements


def test_adaptive_report_keeps_invalid_and_repeated_trials(tmp_path):
    points = [
        {"point_id": "rate-1-repeat-1", "config_id": "B0", "scenario_id": "mixed",
         "iteration_idx": 1, "trial_index": 1, "configured_rate": 0.1,
         "realized_rate": 0.099, "status": "valid", "planner_feasible": None,
         "counts": {"planned": 100, "dispatched": 100, "completed": 100,
                    "failed": 0, "censored": 0},
         "metrics": {"ttft_p50_ms": 400, "ttft_p90_ms": 900,
                     "ttft_p99_ms": 1200, "output_tokens_per_s": 55},
         "reason_codes": [], "artifacts": {"raw": "trial-1/raw.jsonl"}},
        {"point_id": "rate-1-repeat-2", "config_id": "B0", "scenario_id": "mixed",
         "iteration_idx": 1, "trial_index": 2, "configured_rate": 0.1,
         "realized_rate": 0.06, "status": "invalid_dispatch", "planner_feasible": False,
         "counts": {"planned": 100, "dispatched": 60, "completed": 60,
                    "failed": 0, "censored": 40},
         "metrics": {"ttft_p50_ms": 300, "output_tokens_per_s": 42},
         "reason_codes": ["client_throttled"], "artifacts": {"raw": "trial-2/raw.jsonl"}},
    ]
    paths = export_adaptive_points(points, tmp_path)
    archived = json.loads(Path(paths["adaptive_points_json"]).read_text())
    assert archived["points"] == points
    with Path(paths["adaptive_points_csv"]).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[1]["status"] == "invalid_dispatch"
    assert rows[1]["reason_codes"] == '["client_throttled"]'
    assert rows[1]["ttft_p99_ms"] == ""


def test_agent_stages_adaptive_history_without_a_cell_raw_export(tmp_path):
    root = tmp_path / "campaign"
    adaptive = root / "capacity" / "normalized-search-points.json"
    adaptive.parent.mkdir(parents=True)
    adaptive.write_text(json.dumps({"claim": "exploratory_load_curve_only", "config_id": "B0",
                                    "scenario_id": "mixed",
                                    "points": [{"point_id": "one", "status": "invalid"}]}) + "\n")
    visible = {"cell_id": "capacity-1", "stage": "capacity", "scenario_id": "mixed",
               "config_id": "B0",
               "artifacts": {"normalized_search_points": str(adaptive)}}
    hidden = dict(visible, cell_id="test-1", stage="sealed-test")
    context = ProposalContext("c", "research", {}, {}, [], [visible, hidden], [], {}, {})
    packet = _stage_measurements(context, root, tmp_path / "attempt")
    assert [row["cell_id"] for row in packet["cells"]] == ["capacity-1"]
    staged = tmp_path / "attempt" / packet["cells"][0]["files"][0]["path"]
    assert staged.read_bytes() == adaptive.read_bytes()
    assert packet["cells"][0]["omitted"] == [{"reason": "no_raw_artifact_reference"}]


def test_agent_indexes_all_visible_adaptive_trials_as_exploratory(tmp_path):
    root = tmp_path / "campaign"
    visible = []
    for config_id in ("B0", "finalist"):
        folder = root / "adaptive" / config_id / "aiperf"
        folder.mkdir(parents=True)
        points = [
            {"point_id": f"{config_id}:1", "configured_rate": 0.1,
             "realized_rate": 0.099, "status": "valid", "counts": {"completed": 36},
             "metrics": {"ttft_p90_ms": 1000, "output_tokens_per_s": 55}},
            {"point_id": f"{config_id}:2", "configured_rate": 0.2,
             "realized_rate": 0.07, "status": "invalid", "reason_codes": ["client_dispatch_shortfall"],
             "counts": {"completed": 22}, "metrics": {"ttft_p90_ms": 500}},
        ]
        normalized = folder / "normalized-search-points.json"
        normalized.write_text(json.dumps({"claim": "exploratory_load_curve_only",
                                          "config_id": config_id, "scenario_id": "mixed",
                                          "points": points}) + "\n")
        sla_dir = folder.parent / "sla-assessments"
        sla_dir.mkdir()
        (sla_dir / "policy-valid.json").write_text(json.dumps({
            "schema_version": "adaptive-sla-assessment-v1",
            "policy_id": "declared-slo", "policy_sha256": "a" * 64,
            "claim": "observed_adaptive_points_only_no_confirmed_capacity",
            "capacity_confirmed": False, "config_id": config_id, "scenario_id": "mixed",
            "source": str(normalized.resolve()),
            "source_sha256": hashlib.sha256(normalized.read_bytes()).hexdigest(),
            "point_count": 2, "observed_feasible_point_count": 0, "points": [],
        }))
        (sla_dir / "policy-mismatch.json").write_text(json.dumps({
            "schema_version": "adaptive-sla-assessment-v1",
            "claim": "observed_adaptive_points_only_no_confirmed_capacity",
            "capacity_confirmed": False, "config_id": "other", "scenario_id": "mixed",
            "source": str(normalized.resolve()),
            "source_sha256": hashlib.sha256(normalized.read_bytes()).hexdigest(),
        }))
        report = folder / "report" / "adaptive-points.csv"
        report.parent.mkdir()
        report.write_text("point_id,status\n")
        visible.append({"cell_id": f"adaptive-{config_id}", "stage": "capacity",
                        "scenario_id": "mixed", "config_id": config_id,
                        "artifacts": {"normalized_search_points": str(normalized),
                                      "adaptive_points_csv": str(report)}})
    context = ProposalContext("c", "research", {}, {}, [],
                              visible + [dict(visible[0], cell_id="hidden", stage="sealed_test")],
                              [], {}, {})
    run_dir = tmp_path / "attempt"
    packet = _stage_measurements(context, root, run_dir)
    index = json.loads((run_dir / "evaluation-index.json").read_text())
    assert len(packet["adaptive_studies"]) == len(index["adaptive_studies"]) == 2
    for study, cell in zip(index["adaptive_studies"], index["cells"]):
        assert study["claim"] == "exploratory_load_curve_only"
        assert study["capacity_confirmed"] is False
        assert [point["status"] for point in study["points"]] == ["valid", "invalid"]
        assert study["points"][1]["reason_codes"] == ["client_dispatch_shortfall"]
        assert study["points"][0]["metrics"]["ttft_p90_ms"] == 1000
        assert (run_dir / study["source"]["path"]).is_file()
        assert any(item["path"].endswith("adaptive-points.csv") for item in cell["files"])
        assert len(study["sla_assessments"]) == 1
        sla = study["sla_assessments"][0]
        assert sla["policy_id"] == "declared-slo" and sla["capacity_confirmed"] is False
        assert (run_dir / sla["source"]["path"]).is_file()
        assert any(item["reason"] == "sla_assessment_provenance_mismatch"
                   for item in cell["omitted"])


def test_agent_does_not_index_adaptive_history_with_mismatched_identity(tmp_path):
    root = tmp_path / "campaign"
    adaptive = root / "adaptive" / "normalized-search-points.json"
    adaptive.parent.mkdir(parents=True)
    adaptive.write_text(json.dumps({"claim": "exploratory_load_curve_only", "config_id": "wrong",
                                    "scenario_id": "mixed", "points": [{"status": "valid"}]}) + "\n")
    cell = {"cell_id": "adaptive-B0", "stage": "capacity", "config_id": "B0",
            "scenario_id": "mixed", "artifacts": {"normalized_search_points": str(adaptive)}}
    context = ProposalContext("c", "research", {}, {}, [], [cell], [], {}, {})
    packet = _stage_measurements(context, root, tmp_path / "attempt")
    assert packet["adaptive_studies"] == []
    assert {item["reason"] for item in packet["cells"][0]["omitted"]} >= {
        "adaptive_history_identity_or_claim_mismatch"}

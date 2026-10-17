import csv
import hashlib
import json
from pathlib import Path

from inference_autoresearch.search.report import export_adaptive_points, export_sla_profile_class_points
from inference_autoresearch.contracts import ProposalContext
from inference_autoresearch.search.proposer import _stage_measurements
from inference_autoresearch.search.proposer import _stage_sla_study, ProposerError
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
import pytest


def test_adaptive_report_keeps_invalid_and_repeated_trials(tmp_path):
    points = [
        {"point_id": "rate-1-repeat-1", "config_id": "B0", "scenario_id": "mixed",
         "iteration_idx": 1, "trial_index": 1, "configured_rate": 0.1,
         "realized_rate": 0.099, "status": "valid", "planner_feasible": None,
         "counts": {"planned": 100, "dispatched": 100, "completed": 100,
                    "failed": 0, "censored": 0},
         "metrics": {"ttft_p50_ms": 400, "ttft_p90_ms": 900,
                     "ttft_p99_ms": 1200, "output_tokens_per_s": 55},
         "class_label_policy": "frozen_class_sidecar_v1",
         "class_metrics": {"chat": {"n_dispatched": 40, "ttft_eligible": 40,
                                    "tpot_eligible": 40, "ttft_p50_ms": 300,
                                    "ttft_p90_ms": 700, "tpot_p90_ms": 40},
                           "document": {"n_dispatched": 60, "ttft_eligible": 60,
                                        "tpot_eligible": 60, "ttft_p90_ms": 1300,
                                        "tpot_p90_ms": 55}},
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
    with Path(paths["adaptive_class_points_csv"]).open(newline="") as handle:
        classes = list(csv.DictReader(handle))
    assert [(row["class_label"], row["ttft_p90_ms"]) for row in classes] == [
        ("chat", "700"), ("document", "1300")]
    assert all(row["class_label_policy"] == "frozen_class_sidecar_v1" for row in classes)


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


def test_v3_agent_stages_approved_policy_and_class_assessed_b0_before_proposal(tmp_path):
    root = tmp_path
    (root / "configs").mkdir()
    (root / "configs/source.json").write_text(json.dumps({"model": {"local_path": "models/qwen"}}))
    policy = {"schema_version": "0.1", "policy_id": "research-v3", "confidence_level": .95,
              "classes": {name: {"percentile": "p90", "ttft_ms": 1500, "tpot_ms": 70,
                                 "max_error_fraction": 0, "min_eligible_requests": 30}
                          for name in ("chat", "agent", "code", "document")}}
    policy_path = root / "configs/policy.json"
    policy_path.write_text(json.dumps(policy))
    policy_digest = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    baseline_id = resolve_config({}, PinnedEnvironment(root / "models/qwen")).config_id
    profile_path = root / "artifacts/dev/sla-profile-points.json"
    profile_path.parent.mkdir(parents=True)
    raw = root / "artifacts/dev/native.jsonl"
    raw.write_text('{"request_id":"one"}\n')
    profile = {"schema_version": "sla-profile-points-v1",
               "claim": "observed_development_points_no_confirmed_capacity",
               "capacity_confirmed": False, "config_id": baseline_id,
               "development_scenario_id": "dev-1042", "policy_id": "research-v3",
               "policy_sha256": policy_digest,
               "points": [{"rate_rps": .1, "qualified": {"status": "valid",
                           "artifacts": {"raw": {"path": str(raw),
                                                 "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}},
                           "assessment": {"policy_id": "research-v3",
                                          "classes": {name: {"observed_feasible": True}
                                                      for name in policy["classes"]}}}}]}
    profile_path.write_text(json.dumps(profile))
    study = {"schema_version": "sla-study-scaffold-v1", "claim": "not_runnable_until_qualified",
             "source_campaign_path": "configs/source.json",
             "adaptive_development": {"scenario_id": "dev-1042"},
             "policy": {"path": "configs/policy.json", "agent_evidence_source": "configs/policy.json",
                        "sha256": policy_digest, "approval_status": "approved", "approved_by": "user"},
             "baseline_adaptive_run_paths": [{"source_path": "artifacts/dev/sla-profile-points.json",
                                               "source_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest()}]}
    study_path = root / "configs/study.json"
    study_path.write_text(json.dumps(study))
    run_dir = root / "attempt"
    packet = _stage_sla_study(study_path, run_dir, root=root)
    assert packet["capacity_confirmed"] is False
    assert packet["policy_sha256"] == policy_digest
    assert packet["baseline_adaptive_studies"][0]["class_assessed_point_count"] == 1
    native = packet["baseline_adaptive_studies"][0]["native_artifacts"][0]
    assert (run_dir / native["staged"]["path"]).read_bytes() == raw.read_bytes()
    assert json.loads((run_dir / packet["policy_path"]).read_text()) == policy
    assert json.loads((run_dir / "sla-study-index.json").read_text()) == packet
    policy_path.write_text(json.dumps(policy | {"policy_id": "changed"}))
    with pytest.raises(ProposerError, match="missing or changed"):
        _stage_sla_study(study_path, root / "attempt2", root=root)


def test_v3_class_profile_export_keeps_classes_and_denominators(tmp_path):
    profile = {"schema_version": "sla-profile-points-v1",
               "points": [{"rate_rps": .2, "qualified": {"status": "valid",
                           "assessment": {"classes": {
                               "chat": {"planned": 35, "completed": 35, "ttft_eligible": 35,
                                        "tpot_eligible": 35, "observed_feasible": True,
                                        "diagnostic_percentiles_ms": {
                                            "ttft": {"p50": 500, "p90": 800, "p95": 900, "p99": 1000},
                                            "tpot": {"p50": 35, "p90": 45, "p95": 50, "p99": 60}}},
                               "document": {"planned": 40, "completed": 39, "ttft_eligible": 39,
                                            "tpot_eligible": 39, "observed_feasible": False,
                                            "reason_codes": ["error_fraction_exceeded"],
                                            "diagnostic_percentiles_ms": {
                                                "ttft": {"p90": 13000},
                                                "tpot": {"p90": 50}}}}}}}]}
    paths = export_sla_profile_class_points(profile, tmp_path)
    with Path(paths["sla_profile_class_points_csv"]).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["class"], row["planned"], row["ttft_p90_ms"]) for row in rows] == [
        ("chat", "35", "800"), ("document", "40", "13000")]
    assert rows[1]["reason_codes"] == '["error_fraction_exceeded"]'


def test_agent_indexes_visible_candidate_v3_profile_without_capacity_claim(tmp_path):
    root = tmp_path / "campaign"
    source = root / "sla-profile/run/aiperf/sla-profile-points.json"
    source.parent.mkdir(parents=True)
    native = source.parent / "trial/raw.jsonl"
    native.parent.mkdir()
    native.write_text('{"request_id":"one"}\n')
    profile = {"schema_version": "sla-profile-points-v1",
               "claim": "observed_development_points_no_confirmed_capacity",
               "capacity_confirmed": False, "config_id": "candidate", "development_scenario_id": "dev",
               "policy_id": "research-v3", "policy_sha256": "a" * 64,
               "points": [{"rate_rps": .3, "screen": {"status": "valid"},
                           "qualified": {"status": "invalid", "reason_codes": ["ttft_deadline_exceeded"]}}]}
    profile["points"][0]["qualified"]["artifacts"] = {
        "raw": {"path": str(native), "sha256": hashlib.sha256(native.read_bytes()).hexdigest()}}
    source.write_text(json.dumps(profile))
    row = {"cell_id": "candidate-profile", "stage": "sla_profile", "scenario_id": "dev",
           "config_id": "candidate", "artifacts": {"sla_profile_points": str(source)}}
    context = ProposalContext("c", "research", {}, {}, [], [row], [], {}, {})
    packet = _stage_measurements(context, root, tmp_path / "attempt")
    assert len(packet["adaptive_studies"]) == 1
    indexed = packet["adaptive_studies"][0]
    assert indexed["capacity_confirmed"] is False
    assert indexed["policy_sha256"] == "a" * 64
    assert indexed["points"][0]["qualified"]["reason_codes"] == ["ttft_deadline_exceeded"]
    native_link = next(item for item in packet["cells"][0]["files"]
                       if item["path"].endswith("raw.jsonl"))
    assert (tmp_path / "attempt" / native_link["path"]).read_bytes() == native.read_bytes()

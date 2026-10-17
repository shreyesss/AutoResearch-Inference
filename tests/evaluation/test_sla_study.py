import json
from pathlib import Path

import pytest

from inference_autoresearch.evaluation import sla_study
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import sha256_file


def test_unlaunched_v3_template_accepts_policy_but_blocks_on_development_and_b0():
    result = sla_study.audit_sla_study(
        Path("configs/sla-study-v3.template.json"), root=Path.cwd())
    assert result["status"] == "blocked"
    assert result["capacity_confirmed"] is False
    assert result["screen_request_count"] == 36
    assert result["adaptive_request_count_per_point"] == 240
    assert result["policy_sha256"] == sha256_file(Path("configs/sla-policy-v3.json"))
    assert "application_sla_policy_not_approved" not in result["blockers"]
    assert "development_manifest_missing_or_unpinned" in result["blockers"]
    assert "development_b0_cells_missing" in result["blockers"]


def _write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def _qualified_fixture(tmp_path, monkeypatch, *, document_count=60):
    root = tmp_path
    source = _write(root, "configs/campaign-v2.json", {
        "campaign_id": "qwen38-27b-eval-v2",
        "model": {"local_path": ".artifacts/models/Qwen3.8-27B"},
    })
    screen = _write(root, "configs/workloads/screen.json", {
        "scenario_id": "qwen-ops-mixed-reference-v1", "payload_sha256": "screen-payload"})
    sidecar = _write(root, "configs/workloads/development.classes.json", {"classes": True})
    development = _write(root, "configs/workloads/development.json", {
        "scenario_id": "qwen-ops-mixed-development-1042-v1",
        "suite_role": "development", "n_planned": 240,
        "payload_sha256": "different-payload", "schedule_sha256": "schedule-hash",
        "request_class_path": "configs/workloads/development.classes.json",
        "request_class_sha256": sha256_file(sidecar),
    })
    approved_policy = json.loads(Path("configs/sla-policy-proposed.json").read_text())
    approved_policy["policy_id"] = "test-approved-sla-v1"
    policy = _write(root, "configs/policy.json", approved_policy)
    raw = _write(root, ".artifacts/requests.json", [])
    baseline_id = resolve_config({}, PinnedEnvironment(root / ".artifacts/models/Qwen3.8-27B")).config_id
    cell = _write(root, ".artifacts/b0-cell.json", {
        "scenario_id": "qwen-ops-mixed-development-1042-v1",
        "config_id": baseline_id, "status": "valid", "behavior": "normal", "cell_id": "b0:dev:1",
        "counts": {"planned": 240, "dispatched": 240, "completed": 240,
                   "failed": 0, "timed_out": 0, "canceled": 0, "censored": 0,
                   "not_dispatched": 0},
        "diagnostics": {"planned_schedule_sha256": "schedule-hash"},
        "artifacts": {"raw_requests": str(raw)},
    })
    study = {
        "schema_version": "sla-study-scaffold-v1", "campaign_id": "future-sla",
        "claim": "not_runnable_until_qualified", "source_campaign_path": str(source.relative_to(root)),
        "screen": {"scenario_id": "qwen-ops-mixed-reference-v1",
                   "manifest_path": str(screen.relative_to(root)),
                   "manifest_sha256": sha256_file(screen), "request_count": 36,
                   "claim": "large_regression_screen_only"},
        "adaptive_development": {
            "scenario_id": "qwen-ops-mixed-development-1042-v1",
            "manifest_path": str(development.relative_to(root)),
            "manifest_sha256": sha256_file(development),
            "request_class_path": str(sidecar.relative_to(root)),
            "request_class_sha256": sha256_file(sidecar),
            "request_count_per_point": 240, "baseline_cell_paths": [str(cell.relative_to(root))],
            "minimum_baseline_cells": 1, "claim": "observed_class_slo_points_only"},
        "policy": {"path": str(policy.relative_to(root)), "sha256": sha256_file(policy),
                   "approval_status": "approved", "approved_by": "test owner",
                   "agent_evidence_source": str(policy.relative_to(root))},
        "capacity_confirmation": {"required": True,
                                  "split_plan_path": "configs/evaluation-splits-v3.json"},
    }
    study_path = _write(root, "configs/study.json", study)
    classes = ["chat"] * 60 + ["agent"] * 60 + ["code"] * (120 - document_count) + ["document"] * document_count
    def fake_verify(manifest, **_kwargs):
        if manifest["scenario_id"] == "qwen-ops-mixed-reference-v1":
            return {"planned": [{"text": f"screen-{i}", "timestamp": i} for i in range(36)]}
        return {"planned": [{"text": f"development-{i}", "timestamp": i} for i in range(240)],
                "request_classes": {f"id-{i}": name for i, name in enumerate(classes)}}
    monkeypatch.setattr(sla_study, "verify_scenario", fake_verify)
    monkeypatch.setattr(sla_study, "load_split_plan", lambda *_args, **_kwargs: {
        "source_manifest_sha256": sha256_file(screen),
        "generation": {"request_count_per_window": 240},
        "stages": {"development_replication": {"windows": [
            {"scenario_id": "qwen-ops-mixed-development-1042-v1"}]}}})
    return root, study_path


def test_ready_means_inputs_only_not_capacity(tmp_path, monkeypatch):
    root, study = _qualified_fixture(tmp_path, monkeypatch)
    result = sla_study.audit_sla_study(study, root=root)
    assert result["status"] == "inputs_ready_for_new_campaign"
    assert result["blockers"] == []
    assert result["capacity_confirmed"] is False
    assert result["agent_policy_evidence_path"] == "configs/policy.json"


def test_class_minimum_is_per_adaptive_point(tmp_path, monkeypatch):
    root, study = _qualified_fixture(tmp_path, monkeypatch, document_count=29)
    result = sla_study.audit_sla_study(study, root=root)
    assert "development_class_sample_count_below_policy_minimum" in result["blockers"]


def test_same_screen_cannot_be_adaptive_development(tmp_path, monkeypatch):
    root, study_path = _qualified_fixture(tmp_path, monkeypatch)
    study = json.loads(study_path.read_text())
    study["adaptive_development"]["scenario_id"] = study["screen"]["scenario_id"]
    study_path.write_text(json.dumps(study))
    with pytest.raises(sla_study.SLAStudyError, match="distinct 240-request"):
        sla_study.audit_sla_study(study_path, root=root)


def test_approved_marker_does_not_accept_proposed_policy_id(tmp_path, monkeypatch):
    root, study_path = _qualified_fixture(tmp_path, monkeypatch)
    policy = root / "configs/policy.json"
    data = json.loads(policy.read_text())
    data["policy_id"] = "proposed-research-slo"
    policy.write_text(json.dumps(data))
    study = json.loads(study_path.read_text())
    study["policy"]["sha256"] = sha256_file(policy)
    study_path.write_text(json.dumps(study))
    result = sla_study.audit_sla_study(study_path, root=root)
    assert "sla_policy_id_still_proposed" in result["blockers"]

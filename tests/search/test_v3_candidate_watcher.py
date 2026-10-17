"""GPU-free checks for the one-shot v3 candidate search watcher."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "infra/run_v3_candidate_search.py"
SPEC = importlib.util.spec_from_file_location("v3_candidate_watcher", SCRIPT)
assert SPEC and SPEC.loader
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


def _json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return watcher.sha(path)


def _evidence(tmp_path: Path) -> tuple[dict, dict, dict]:
    policy_path = "configs/sla-policy-v3.json"
    policy = {"policy_id": "research-v3", "classes": {"chat": {}, "agent": {},
                                                         "code": {}, "document": {}}}
    policy_sha = _json(tmp_path / policy_path, policy)
    source_path = ".artifacts/runs/sla-profile-points.json"
    profile = {"schema_version": "sla-profile-points-v1",
               "claim": "observed_development_points_no_confirmed_capacity",
               "capacity_confirmed": False, "config_id": "B0",
               "development_scenario_id": "dev-1042",
               "policy_id": policy["policy_id"], "policy_sha256": policy_sha,
               "points": [{"rate_rps": 0.2, "qualified": {"status": "valid",
                           "assessment": {"policy_id": policy["policy_id"],
                                          "classes": {name: {} for name in policy["classes"]}}}}]}
    source_sha = _json(tmp_path / source_path, profile)
    cells = [".artifacts/cells/dev-1042/cell-result.json",
             ".artifacts/cells/dev-1043/cell-result.json"]
    cell_sha = {cell: _json(tmp_path / cell, {"cell_id": str(i)})
                for i, cell in enumerate(cells)}
    study = {"policy": {"approval_status": "approved", "path": policy_path,
                        "sha256": policy_sha},
             "baseline_adaptive_run_paths": [{"source_path": source_path,
                                              "source_sha256": source_sha}],
             "adaptive_development": {
                 "scenario_id": "dev-1042", "baseline_cell_paths": [cells[0]],
                 "matched_baseline_replication_cell_paths": [cells[1]],
                 "baseline_cell_sha256_by_path": cell_sha}}
    study_path = tmp_path / ".artifacts/v3-independent-capture/sla-study-activated.json"
    study_sha = _json(study_path, study)
    receipt = {"status": "observed_b0_profile", "capacity_confirmed": False,
               "study_path": str(study_path), "study_sha256": study_sha,
               "source": study["baseline_adaptive_run_paths"][0]}
    b0 = {"status": "matched_evaluator_b0_valid", "sla_capacity_confirmed": False,
          "baseline_config_id": "B0"}
    return receipt, study, b0


def test_watcher_requires_valid_four_class_profile_and_two_pinned_b0_cells(tmp_path):
    receipt, study, b0 = _evidence(tmp_path)
    result = watcher.validate_profile_evidence(tmp_path, receipt, study, b0)
    assert result["valid_class_assessed_point_count"] == 1
    assert result["matched_b0_cell_count"] == 2
    assert result["capacity_confirmed"] is False
    path = tmp_path / study["adaptive_development"]["matched_baseline_replication_cell_paths"][0]
    path.write_text("changed")
    with pytest.raises(ValueError, match="CellResult missing or changed"):
        watcher.validate_profile_evidence(tmp_path, receipt, study, b0)


def test_watcher_rejects_invalid_profile_even_with_receipt(tmp_path):
    receipt, study, b0 = _evidence(tmp_path)
    profile_path = tmp_path / study["baseline_adaptive_run_paths"][0]["source_path"]
    profile = json.loads(profile_path.read_text())
    del profile["points"][0]["qualified"]["assessment"]["classes"]["document"]
    digest = _json(profile_path, profile)
    study["baseline_adaptive_run_paths"][0]["source_sha256"] = digest
    receipt["source"]["source_sha256"] = digest
    receipt["study_sha256"] = _json(
        tmp_path / ".artifacts/v3-independent-capture/sla-study-activated.json", study)
    with pytest.raises(ValueError, match="no valid four-class point"):
        watcher.validate_profile_evidence(tmp_path, receipt, study, b0)


def test_watcher_records_preflight_failure_and_refuses_rerun(tmp_path, monkeypatch):
    root = tmp_path / ".artifacts/v3-independent-capture"
    monkeypatch.setattr(watcher, "INPUT_ROOT", root)
    monkeypatch.setattr(watcher, "STATUS", root / "candidate-search-status.json")
    monkeypatch.setattr(watcher, "wait_for_profile", lambda *_: {"study_sha256": "pin"})
    monkeypatch.setattr(watcher, "no_prior_proposals", lambda: None)
    monkeypatch.setattr(watcher, "controller_runtime_pin", lambda: {"image_id": "pin"})
    monkeypatch.setattr(watcher, "run_command", lambda *_args, **_kwargs: (1, "", False))
    monkeypatch.setattr(watcher, "idle_gpu", lambda: pytest.fail("GPU gate reached"))
    with pytest.raises(RuntimeError, match="preflight failed"):
        watcher.run_waiter(60)
    status = json.loads(watcher.STATUS.read_text())
    assert status["status"] == "blocked"
    assert status["stage"] == "blocked"
    assert status["sealed_test_touched"] is False
    with pytest.raises(RuntimeError, match="existing candidate search status"):
        watcher.run_waiter(60)


def test_controller_preflight_and_search_share_docker_runtime(tmp_path, monkeypatch):
    root = tmp_path / ".artifacts/v3-independent-capture"
    pin = {"image_id": "sha256:current"}
    seen: list[list[str]] = []
    monkeypatch.setattr(watcher, "INPUT_ROOT", root)
    monkeypatch.setattr(watcher, "STATUS", root / "status.json")
    monkeypatch.setattr(watcher, "wait_for_profile", lambda *_: {
        "study_sha256": "study", "policy_sha256": "policy"})
    monkeypatch.setattr(watcher, "no_prior_proposals", lambda: None)
    monkeypatch.setattr(watcher, "controller_runtime_pin", lambda: pin)
    monkeypatch.setattr(watcher, "idle_gpu", lambda: None)

    def fake_run(argv, *_args, **_kwargs):
        seen.append(argv)
        if "--check" in argv:
            return 0, json.dumps({"status": "ready", "study_sha256": "study",
                                  "policy_sha256": "policy", "capacity_confirmed": False}), False
        return 0, json.dumps({"campaign_id": watcher.CAMPAIGN_ID,
                              "status": "development_screen_complete",
                              "capacity_confirmed": False}), False

    monkeypatch.setattr(watcher, "run_command", fake_run)
    result = watcher.run_waiter(60)
    assert result["status"] == "development_search_observed"
    assert len(seen) == 2
    assert seen[0][0:5] == seen[1][0:5] == [
        "docker", "exec", "-w", str(watcher.ROOT), watcher.CONTROLLER_CONTAINER]
    assert seen[0][-1] == "--check" and seen[1] == seen[0][:-1]


def test_controller_pin_rejects_rebuilt_image_mismatch(monkeypatch):
    class Result:
        def __init__(self, stdout):
            self.stdout = stdout

    def fake_run(argv, **_kwargs):
        if argv[:2] == ["docker", "inspect"]:
            return Result(json.dumps([{"State": {"Running": True},
                                       "Image": "sha256:old", "Config": {"Image": watcher.CONTROLLER_IMAGE},
                                       "Mounts": []}]))
        if argv[:3] == ["docker", "image", "inspect"]:
            return Result(json.dumps([{"Id": "sha256:new"}]))
        pytest.fail("stale image should be rejected before Docker exec")

    monkeypatch.setattr(watcher.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="container, current image"):
        watcher.controller_runtime_pin()


def test_watcher_blocks_when_profiler_disappears_without_receipt(tmp_path, monkeypatch):
    root = tmp_path / ".artifacts/v3-independent-capture"
    root.mkdir(parents=True)
    (root / "b0-sla-profile-argv.json").write_text("{}")
    monkeypatch.setattr(watcher, "INPUT_ROOT", root)
    monkeypatch.setattr(watcher, "PROFILE_INVALID", root / "invalid.json")
    monkeypatch.setattr(watcher, "PROFILE_RECEIPT", root / "receipt.json")
    monkeypatch.setattr(watcher, "STATUS", root / "status.json")
    monkeypatch.setattr(watcher, "session_active", lambda _name: False)
    ticks = iter([0, 1, 2, 64, 65])
    monkeypatch.setattr(watcher.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(watcher.time, "sleep", lambda _seconds: None)
    with pytest.raises(RuntimeError, match="exited without a validated receipt"):
        watcher.wait_for_profile(120, {"events": []})

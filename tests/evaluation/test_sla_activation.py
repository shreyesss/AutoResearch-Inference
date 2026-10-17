import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "activate_v3_sla_study", ROOT / "infra/activate_v3_sla_study.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_study_activation_requires_exact_matched_b0_receipt(tmp_path):
    scenario = "qwen-ops-mixed-development-1042-v1"
    repeat = "qwen-ops-mixed-development-1043-v1"
    manifest_path = tmp_path / "configs/dev.json"
    classes_path = tmp_path / "configs/dev.classes.json"
    manifest_path.parent.mkdir()
    classes_path.write_text('{"request_classes":{}}')
    manifest_path.write_text(json.dumps({"scenario_id": scenario, "readiness": "validated",
                                         "suite_role": "development", "n_planned": 240,
                                         "request_class_path": "configs/dev.classes.json",
                                         "request_class_sha256": _sha(classes_path)}))
    template = {"schema_version": "sla-study-scaffold-v1",
                "claim": "not_runnable_until_qualified",
                "policy": {"sha256": "a" * 64},
                "adaptive_development": {"scenario_id": scenario,
                                         "manifest_path": "configs/dev.json",
                                         "request_class_path": "configs/dev.classes.json"}}
    cells = {}
    for name in (scenario, repeat):
        folder = tmp_path / "artifacts" / name
        folder.mkdir(parents=True)
        raw = folder / "raw.jsonl"
        raw.write_text('{"request_id":"one"}\n')
        cell_path = folder / "cell-result.json"
        cell = {"scenario_id": name, "cell_id": f"B0:{name}", "config_id": "B0",
                "status": "valid", "behavior": "normal",
                "counts": {"planned": 240, "dispatched": 240, "completed": 240,
                           "failed": 0, "timed_out": 0, "canceled": 0,
                           "censored": 0, "not_dispatched": 0},
                "artifacts": {"raw_requests": str(raw)}}
        cell_path.write_text(json.dumps(cell))
        cells[name] = {"path": str(cell_path.relative_to(tmp_path)), "sha256": _sha(cell_path),
                       "raw_requests_path": str(raw.relative_to(tmp_path)),
                       "raw_requests_sha256": _sha(raw), "cell_id": cell["cell_id"]}
    receipt = {"schema_version": "matched-evaluator-b0-receipt-v1",
               "status": "matched_evaluator_b0_valid", "campaign_id": "qwen38-27b-sla-b0-v3",
               "policy_sha256": "a" * 64, "baseline_config_id": "B0",
               "sla_capacity_confirmed": False, "cells": cells}
    study = module.build_activated_study(tmp_path, template, receipt)
    assert study["adaptive_development"]["baseline_cell_paths"] == [cells[scenario]["path"]]
    assert study["adaptive_development"]["matched_baseline_replication_cell_paths"] == [cells[repeat]["path"]]
    assert study["adaptive_development"]["manifest_sha256"] == _sha(manifest_path)
    assert study["adaptive_development"]["baseline_cell_sha256_by_path"][cells[scenario]["path"]] == cells[scenario]["sha256"]
    assert study["adaptive_development"]["baseline_raw_sha256_by_path"][cells[repeat]["path"]] == cells[repeat]["raw_requests_sha256"]
    assert study["baseline_adaptive_run_paths"] == []
    (tmp_path / cells[repeat]["raw_requests_path"]).write_text("changed\n")
    with pytest.raises(ValueError, match="changed or became ineligible"):
        module.build_activated_study(tmp_path, template, receipt)

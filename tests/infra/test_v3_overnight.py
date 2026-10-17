"""The overnight launcher must stop before spending GPU time on bad inputs."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "infra/run_v3_development_overnight.py"


def load_module():
    spec = importlib.util.spec_from_file_location("v3_overnight", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = load_module()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "ARTIFACTS", tmp_path / "artifacts")
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    scenario = "qwen-ops-mixed-development-1042-v1"
    cell = module.ARTIFACTS / scenario
    (cell / "aiperf/mixed").mkdir(parents=True)
    module.ASSETS.mkdir()
    split = {"source_sha256": "source", "generation": {
        "request_count_per_window": 240, "dataset_entries": 960, "request_rate_rps": 0.1},
        "qualification": {"minimum_class_requests_per_window": 30}}
    def write(path: Path, value: dict):
        path.write_text(json.dumps(value))
    write(cell / "plan.json", {"cell": scenario, "workload": "mixed",
          "random_seed": 1042, "source_sha256": "source", "request_count": 240,
          "effective_dataset_entries": 960, "offered_rps": 0.1})
    write(cell / "status.json", {"aiperf_exit_code": 0})
    write(cell / "aiperf/mixed/summary.json", {"status": "complete",
          "request_count": 240, "http_200": 240, "statuses": [200], "raw_sha256": "raw"})
    write(module.ARTIFACTS / f"{scenario}.freeze.json", {
        "scenario_id": scenario, "rows": 240, "asset_sha256": "payload"})
    write(module.ASSETS / f"{scenario}.json", {"readiness": "prepared",
          "suite_role": "development", "payload_sha256": "payload",
          "seeds": {"arrivals": 1042, "content": 1042},
          "request_class_sha256": "classes"})
    labels = (["chat"] * 80 + ["agent"] * 60 + ["code"] * 60 + ["document"] * 40)
    monkeypatch.setattr(module, "verify_scenario", lambda *args, **kwargs: {
        "request_classes": {str(i): label for i, label in enumerate(labels)}})
    return module, scenario, split, cell, labels


def test_capture_passes_only_with_full_accounting_and_class_quota(tmp_path, monkeypatch):
    module, scenario, split, _, _ = fixture(tmp_path, monkeypatch)
    result = module.inspect_capture(scenario, 1042, split)
    assert result["class_counts"] == {"chat": 80, "agent": 60, "code": 60, "document": 40}
    assert result["sla_capacity_confirmed"] is False
    assert result["evaluator_b0_cell"] is None


def test_capture_stops_on_failure_or_undersampled_class(tmp_path, monkeypatch):
    module, scenario, split, cell, labels = fixture(tmp_path, monkeypatch)
    status_path = cell / "status.json"
    status_path.write_text(json.dumps({"aiperf_exit_code": 1}))
    with pytest.raises(ValueError, match="incomplete or has failures"):
        module.inspect_capture(scenario, 1042, split)
    status_path.write_text(json.dumps({"aiperf_exit_code": 0}))
    labels[-11:] = ["chat"] * 11
    with pytest.raises(ValueError, match="lacks 30 requests"):
        module.inspect_capture(scenario, 1042, split)

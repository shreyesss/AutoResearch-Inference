"""Matched B0 receipts require complete evaluator CellResults, not replay reports."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "infra/run_v3_matched_b0.py"


def module():
    spec = importlib.util.spec_from_file_location("v3_matched_b0", SCRIPT)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_static_config_is_pinned_to_stock_development_inputs():
    _, _, _, expected = module().static_config()
    assert expected["config_id"] == "cfg-8d0de585f89598b2160f"
    assert expected["ids"] == ["qwen-ops-mixed-development-1042-v1",
                               "qwen-ops-mixed-development-1043-v1"]


def test_cell_receipt_rejects_failed_or_mismatched_window(tmp_path, monkeypatch):
    b0 = module()
    monkeypatch.setattr(b0, "ROOT", tmp_path)
    monkeypatch.setattr(b0, "OUT_ROOT", tmp_path / "b0")
    directory = b0.OUT_ROOT / "campaign" / "eval-1"
    ids = ["dev-1042", "dev-1043"]
    prepared = {"baseline_config_id": "cfg-b0", "scenario_ids": ids,
                "campaign_id": "b0", "campaign_sha256": "campaign",
                "protocol_sha256": "protocol", "policy_sha256": "policy",
                "input_audit_sha256": "audit"}
    for ordinal, name in enumerate(ids, 1):
        manifest = tmp_path / "configs/workloads/ops-frozen" / f"{name}.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"schedule_sha256": f"schedule-{name}"}))
        cell_dir = directory / f"cell-{ordinal:02d}-{name}"
        cell_dir.mkdir(parents=True)
        raw = cell_dir / "raw.jsonl"
        raw.write_text("{}\n")
        cell = {"cell_id": f"cell-{name}", "scenario_id": name, "config_id": "cfg-b0",
                "status": "valid", "behavior": "normal",
                "counts": {"planned": 240, "dispatched": 240, "completed": 240,
                           "failed": 0, "timed_out": 0, "canceled": 0, "censored": 0,
                           "not_dispatched": 0},
                "diagnostics": {"planned_schedule_sha256": f"schedule-{name}"},
                "metrics": {"output_tokens_per_s": 40.0, "ttft_p90_ms": 1000.0,
                            "tpot_p90_ms": 50.0},
                "artifacts": {"raw_requests": str(raw)}}
        (cell_dir / "cell-result.json").write_text(json.dumps(cell))
    cli_result = {"status": "valid", "config_id": "cfg-b0",
                  "artifacts": {"directory": str(directory)}}
    receipt = b0.validate_result(prepared, cli_result)
    assert set(receipt["cells"]) == set(ids)
    assert receipt["sla_capacity_confirmed"] is False
    bad_path = directory / "cell-02-dev-1043/cell-result.json"
    bad = json.loads(bad_path.read_text())
    bad["counts"]["failed"] = 1
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="incomplete or mismatched"):
        b0.validate_result(prepared, cli_result)

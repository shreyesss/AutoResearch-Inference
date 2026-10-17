"""The 240-request followup admits only hash-pinned pilot selections."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import sha256_file


SCRIPT = Path(__file__).resolve().parents[2] / "infra/run_fast_finalists_v4.py"
SPEC = importlib.util.spec_from_file_location("run_fast_finalists_v4", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _selection(root: Path) -> tuple[dict, Path, PinnedEnvironment, dict]:
    domain = {"max_num_batched_tokens": [4096, 8192]}
    pinned = PinnedEnvironment(root / "model")
    parameters = {"max_num_batched_tokens": 4096}
    config_id = resolve_config(parameters, pinned, domain).config_id
    proposal = {"proposal_id": "candidate-1", "parameters": parameters}
    cell = {"cell_id": "eval-one:qwen-ops-mixed-reference-v1:1",
            "config_id": config_id, "status": "valid"}
    proposal_path, cell_path = root / "proposal.json", root / "cell.json"
    proposal_path.write_text(json.dumps(proposal))
    cell_path.write_text(json.dumps(cell))
    ledger = root / "ledger.sqlite"
    with sqlite3.connect(ledger) as db:
        db.execute("CREATE TABLE events(campaign_id TEXT, kind TEXT, entity_id TEXT, payload_json TEXT)")
        for kind, payload in (("proposal", {"proposal": proposal, "config_id": config_id}),
                              ("pilot_screen_decision", {"cell_id": cell["cell_id"],
                                                          "promote_to_shortlist": True})):
            db.execute("INSERT INTO events VALUES(?,?,?,?)",
                       (MODULE.CAMPAIGN_ID, kind, proposal["proposal_id"], json.dumps(payload)))
    selected = {"proposal_id": proposal["proposal_id"], "config_id": config_id,
                "parameters": parameters, "cell_id": cell["cell_id"],
                "proposal_path": proposal_path.name, "proposal_sha256": sha256_file(proposal_path),
                "cell_result_path": cell_path.name, "cell_result_sha256": sha256_file(cell_path)}
    shortlist = {"capacity_confirmed": False, "further_evaluation_required": True,
                 "selected_cell_ids": [cell["cell_id"]], "selected_proposals": [selected]}
    return shortlist, ledger, pinned, domain


def test_selected_config_must_match_pinned_proposal_cell_and_ledger(tmp_path: Path) -> None:
    shortlist, ledger, pinned, domain = _selection(tmp_path)
    rows = MODULE.selected_cases(tmp_path, shortlist, ledger, pinned, domain)
    assert rows[0]["config_id"] == shortlist["selected_proposals"][0]["config_id"]
    assert rows[0]["parameters"] == {"max_num_batched_tokens": 4096}
    (tmp_path / "proposal.json").write_text('{"proposal_id":"candidate-1","parameters":{}}')
    with pytest.raises(MODULE.FollowupError, match="Changed or missing"):
        MODULE.selected_cases(tmp_path, shortlist, ledger, pinned, domain)


def test_uses_controller_aiperf_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "aiperf"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: str(executable))
    assert MODULE.controller_aiperf_executable() == executable.resolve()
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: None)
    with pytest.raises(MODULE.FollowupError, match="absent from the controller PATH"):
        MODULE.controller_aiperf_executable()


def test_matched_comparison_retains_class_p90_direction(tmp_path: Path) -> None:
    def point(label: str, p90: float, throughput: float) -> dict:
        classes = {"chat": {"planned": 40, "ttft_deadline_breaches": 0,
                            "tpot_deadline_breaches": 0, "observed_feasible": True,
                            "reason_codes": [], "diagnostic_percentiles_ms": {
                                "ttft": {"p50": p90 / 2, "p90": p90},
                                "tpot": {"p50": 20, "p90": 30}}}}
        return {"label": label, "config_id": label, "trial": {
            "status": "valid", "observed_feasible": True, "assessment": {"classes": classes},
            "native_summary_metrics": {"output_tokens_per_s": throughput}}}
    points = [point("B0", 100, 50), point("candidate", 80, 60)]
    result = MODULE.compare_points(points)
    assert result["capacity_confirmed"] is False
    assert result["comparisons"][0]["class_latency_deltas_vs_b0"]["chat"]["ttft_p90_ms_delta_ms"] == -20
    assert result["comparisons"][0]["output_tokens_per_s_ratio_vs_b0"] == 1.2
    assert Path(MODULE.plot_operator_points(tmp_path, points)["per_class_svg"]).is_file()

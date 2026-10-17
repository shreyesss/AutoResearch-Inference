from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from inference_autoresearch.search.fast_pilot import (
    BASE_SEED, RATE_RPS, export_screen_points, preflight, rate_lock,
)


ROOT = Path(__file__).resolve().parents[2]


def test_fixed_rate_lock_uses_real_b0_report_and_records_actual_aiperf_seed():
    report = ROOT / ".artifacts/fast-pilot-v4/b0-observed.json"
    if not report.exists():
        return
    prepared = preflight(ROOT, report.parent)
    lock = rate_lock(prepared, ROOT)
    assert lock["selected_rate_rps"] == RATE_RPS
    assert lock["base_seed"] == BASE_SEED
    assert lock["arrival_seed"] == BASE_SEED + round(RATE_RPS * 1_000_000)
    assert lock["source_profile_path"] == ".artifacts/fast-pilot-v4/b0-observed.json"
    assert lock["claim"] == "fixed_rate_matched_36_request_exploratory_triage_only"
    assert lock["capacity_confirmed"] is False


def test_export_retains_invalid_candidate_and_provisional_frontier(tmp_path: Path):
    def cell(name: str, status: str, throughput: float):
        return {"cell_id": name, "config_id": name, "status": status,
                "reason_codes": [] if status == "valid" else ["server_start_failed"],
                "metrics": {"output_tokens_per_s": throughput,
                            "ttft_p50_ms": 100, "ttft_p90_ms": 200,
                            "tpot_p50_ms": 30, "tpot_p90_ms": 40}}
    baseline = cell("b0", "valid", 100)
    rows = [{"proposal": SimpleNamespace(proposal_id="better"),
             "cell": cell("good", "valid", 120),
             "decision": {"promote_to_shortlist": True}},
            {"proposal": SimpleNamespace(proposal_id="failed"),
             "cell": cell("bad", "measurement_failed", 0),
             "decision": {"promote_to_shortlist": False}}]
    exported = export_screen_points(tmp_path, baseline, rows)
    data = json.loads(Path(exported["json"]).read_text())
    assert [row["label"] for row in data["points"]] == ["B0", "better", "failed"]
    assert data["capacity_confirmed"] is False
    frontier = json.loads(Path(exported["frontier"]).read_text())
    assert frontier["cell_ids"] == ["good"]
    assert Path(exported["csv"]).is_file()
    assert Path(exported["scatter_svg"]).is_file()

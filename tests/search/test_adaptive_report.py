import csv
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
    adaptive.write_text('{"points":[{"point_id":"one","status":"invalid"}]}\n')
    visible = {"cell_id": "capacity-1", "stage": "capacity", "scenario_id": "mixed",
               "artifacts": {"normalized_search_points": str(adaptive)}}
    hidden = dict(visible, cell_id="test-1", stage="sealed-test")
    context = ProposalContext("c", "research", {}, {}, [], [visible, hidden], [], {}, {})
    packet = _stage_measurements(context, root, tmp_path / "attempt")
    assert [row["cell_id"] for row in packet["cells"]] == ["capacity-1"]
    staged = tmp_path / "attempt" / packet["cells"][0]["files"][0]["path"]
    assert staged.read_bytes() == adaptive.read_bytes()
    assert packet["cells"][0]["omitted"] == [{"reason": "no_raw_artifact_reference"}]

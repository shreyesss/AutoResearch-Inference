"""Inspection should expose the full run trail without altering experiment events."""

from __future__ import annotations

import json
from pathlib import Path

from inference_autoresearch.storage.inspection import build_inspection, write_inspection
from inference_autoresearch.storage.ledger import Ledger


def test_inspection_links_cells_logs_and_feedback(tmp_path: Path) -> None:
    campaign_id = "inspect-campaign"
    root = tmp_path / campaign_id / "real"
    ledger = Ledger(root / "ledger.sqlite3")
    run = root / campaign_id / "eval-one"
    server = run / "cell-01-chat" / "server"
    server.mkdir(parents=True)
    (server / "server.log").write_text("example log\n")
    (server / "telemetry.jsonl").write_text("{}\n")
    attempt = root / "proposals" / "attempt-0001"
    (attempt / "workspace").mkdir(parents=True)
    (attempt / "proposer-receipt.json").write_text('{"status":"validated"}\n')
    (attempt / "workspace" / "notes.md").write_text("Measured decode tradeoff.\n")
    ledger.append(campaign_id, "proposal", "proposal-one", {
        "config_id": "cfg-one", "proposal": {"hypothesis": "Speculation improves decode"}})
    ledger.append(campaign_id, "evaluation_transition", "eval-one", {"state": "measuring"})
    ledger.append(campaign_id, "cell", "cell-one", {
        "scenario_id": "chat", "status": "valid", "behavior": "normal",
        "counts": {"planned": 3, "completed": 3},
        "metrics": {"output_tokens_per_s": 10, "ttft_p99_ms": 20, "tpot_p99_ms": 30},
        "artifacts": {"raw_requests": str(run / "cell-01-chat" / "normalized-requests.jsonl")}})
    ledger.append(campaign_id, "evaluation", "eval-one", {
        "config_id": "cfg-one", "stage": "screen", "status": "valid", "cell_ids": ["cell-one"],
        "artifacts": {"directory": str(run), "elapsed_s": "12.0"}})
    ledger.append(campaign_id, "feedback", "proposal-one", {"status": "valid"})
    before = len(ledger.events(campaign_id))

    result = write_inspection(ledger, campaign_id, root, "real")
    assert len(ledger.events(campaign_id)) == before
    assert result["event_count"] == 5
    assert result["evaluation_count"] == 1
    assert result["attempt_count"] == 1
    data = json.loads(Path(result["index_json"]).read_text())
    assert data["evaluations"][0]["cells"][0]["metrics"]["output_tokens_per_s"] == 10
    assert f"{campaign_id}/eval-one/cell-01-chat/server/server.log" in data["evaluations"][0]["files"]
    assert data["proposals"][0]["feedback"]["status"] == "valid"
    assert data["attempts"][0]["status"] == "validated"
    assert "proposals/attempt-0001/workspace/notes.md" in data["attempts"][0]["files"]
    assert "measuring" in Path(result["index_markdown"]).read_text()


def test_inspection_never_walks_external_ledger_directory(tmp_path: Path) -> None:
    root = tmp_path / "campaign" / "real"
    ledger = Ledger(root / "ledger.sqlite3")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("private")
    ledger.append("campaign", "evaluation", "eval-two", {
        "config_id": "cfg-two", "stage": "screen", "status": "failed",
        "cell_ids": [], "artifacts": {"directory": str(outside)}})
    data = build_inspection(ledger, "campaign", root, "real")
    assert data["evaluations"][0]["files"] == []

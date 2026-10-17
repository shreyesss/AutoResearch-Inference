"""Regenerate a readable campaign index from the durable ledger and run files.

This is a view over evidence, never an additional source of experimental truth.
Large request streams and logs are linked rather than copied into the index.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from inference_autoresearch.storage.ledger import Ledger


def _within(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _path(root: Path, path: Path) -> str:
    return str(path.relative_to(root)) if _within(root, path) else str(path)


def _run_files(root: Path, directory: str | None) -> list[str]:
    if not directory:
        return []
    folder = Path(directory)
    if not folder.is_absolute():
        folder = root / folder
    # A ledger path must never cause inspection to walk outside the campaign.
    if not _within(root, folder) or not folder.is_dir():
        return []
    return sorted(_path(root, item) for item in folder.rglob("*") if item.is_file()
                  and not item.is_symlink())


def build_inspection(ledger: Ledger, campaign_id: str, root: Path,
                     backend: str) -> dict[str, Any]:
    """Return a bounded summary; the append-only ledger remains the full timeline."""
    root = Path(root).resolve()
    events = ledger.events(campaign_id)
    cells = {event["entity_id"]: event for event in events if event["kind"] == "cell"}
    feedback = {event["entity_id"]: event for event in events if event["kind"] == "feedback"}
    evaluations = []
    for event in events:
        if event["kind"] != "evaluation":
            continue
        payload = event["payload"]
        directory = payload.get("artifacts", {}).get("directory")
        cell_summaries = []
        for cell_id in payload.get("cell_ids", []):
            recorded = cells.get(cell_id)
            if recorded is None:
                cell_summaries.append({"cell_id": cell_id, "status": "missing_from_ledger"})
                continue
            cell = recorded["payload"]
            cell_summaries.append({
                "cell_id": cell_id, "scenario_id": cell.get("scenario_id"),
                "status": cell.get("status"), "behavior": cell.get("behavior"),
                "evidence_grade": cell.get("evidence_grade"),
                "counts": cell.get("counts", {}), "metrics": cell.get("metrics", {}),
                "reason_codes": cell.get("reason_codes", []),
                "artifacts": cell.get("artifacts", {}),
            })
        evaluations.append({
            "evaluation_id": event["entity_id"], "utc": event["utc"],
            "config_id": payload.get("config_id"), "stage": payload.get("stage"),
            "status": payload.get("status"), "failure_reasons": payload.get("failure_reasons", []),
            "elapsed_s": payload.get("artifacts", {}).get("elapsed_s"),
            "directory": _path(root, Path(directory)) if directory else None,
            "files": _run_files(root, directory), "cells": cell_summaries,
        })
    proposals = []
    for event in events:
        if event["kind"] != "proposal":
            continue
        payload = event["payload"]
        proposal_id = event["entity_id"]
        proposals.append({
            "proposal_id": proposal_id, "utc": event["utc"],
            "config_id": payload.get("config_id"),
            "proposal": payload.get("proposal"), "effective": payload.get("effective"),
            "feedback": feedback.get(proposal_id, {}).get("payload"),
        })
    attempts = []
    proposal_root = root / "proposals"
    if proposal_root.is_dir() and not proposal_root.is_symlink():
        for folder in sorted(proposal_root.glob("attempt-[0-9][0-9][0-9][0-9]")):
            if not folder.is_dir() or folder.is_symlink() or not _within(root, folder):
                continue
            receipt_path = folder / "proposer-receipt.json"
            try:
                receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
            except (OSError, ValueError):
                receipt = {"status": "unreadable_receipt"}
            important = ("proposer-receipt.json", "codex.events.jsonl", "codex.stderr.txt",
                         "proposal.final.json", "proposal.normalized.json", "research-index.json",
                         "measurements-index.json", "evaluation-index.json", "retrieval-audit.json",
                         "workspace/notes.md")
            attempts.append({"attempt": folder.name, "status": receipt.get("status", "unknown"),
                             "directory": _path(root, folder),
                             "files": [_path(root, folder / name) for name in important
                                       if (folder / name).is_file() and not (folder / name).is_symlink()]})
    adaptive_studies = []
    for path in sorted(root.rglob("normalized-search-points.json")) if root.is_dir() else []:
        if (not path.is_file() or path.is_symlink() or not _within(root, path)
                or (root / "proposals") in path.parents):
            continue
        try:
            payload = json.loads(path.read_text())
            points = payload.get("points", [])
            if not isinstance(points, list):
                raise ValueError("points is not a list")
            native = Path(payload["native_history"]).resolve() if isinstance(
                payload.get("native_history"), str) else path.with_name("search_history.json")
            adaptive_studies.append({
                "path": _path(root, path), "native_history": _path(root, native)
                if _within(root, native) and native.is_file() else None,
                "point_count": len(points),
                "status_counts": dict(Counter(str(point.get("status")) for point in points
                                               if isinstance(point, dict))),
                "points": [{key: point.get(key) for key in
                            ("point_id", "config_id", "scenario_id", "iteration_idx", "trial_index",
                             "configured_rate", "realized_rate", "status", "reason_codes", "counts",
                             "metrics", "artifacts")}
                           for point in points if isinstance(point, dict)],
            })
        except (OSError, ValueError) as exc:
            adaptive_studies.append({"path": _path(root, path), "error": type(exc).__name__})
    timeline = [{"seq": event["seq"], "utc": event["utc"], "kind": event["kind"],
                 "entity_id": event["entity_id"],
                 "state": event["payload"].get("state"),
                 "reason": event["payload"].get("reason")}
                for event in events]
    return {"campaign_id": campaign_id, "backend": backend,
            "ledger": _path(root, ledger.path), "event_count": len(events),
            "timeline": timeline, "proposals": proposals, "attempts": attempts,
            "evaluations": evaluations, "adaptive_studies": adaptive_studies,
            "top_level_files": sorted(_path(root, item) for item in root.iterdir()
                                      if item.is_file() and not item.is_symlink()) if root.is_dir() else []}


def _markdown(data: dict[str, Any]) -> str:
    lines = [f"# Campaign {data['campaign_id']} ({data['backend']})", "",
             f"Ledger: `{data['ledger']}`; events: {data['event_count']}.", "",
             "This index is regenerated from the ledger and run files. It contains no inferred lessons.", "",
             "## Evaluations", ""]
    if not data["evaluations"]:
        lines.append("No evaluations recorded.")
    for item in data["evaluations"]:
        lines += [f"### {item['evaluation_id']}", "",
                  f"{item['utc']} · {item['stage']} · {item['status']} · config `{item['config_id']}`",
                  f"Elapsed: {item['elapsed_s'] or 'unavailable'} s; directory: `{item['directory'] or 'unavailable'}`.", ""]
        for cell in item["cells"]:
            metrics = cell.get("metrics", {})
            lines.append(f"- `{cell['cell_id']}` ({cell.get('scenario_id')}): {cell.get('status')}; "
                         f"output tok/s {metrics.get('output_tokens_per_s', '—')}, "
                         f"TTFT p50/p90 {metrics.get('ttft_p50_ms', '—')}/{metrics.get('ttft_p90_ms', '—')} ms, "
                         f"TTFT p99 {metrics.get('ttft_p99_ms', '—')} ms, "
                         f"TPOT p50/p90 {metrics.get('tpot_p50_ms', '—')}/{metrics.get('tpot_p90_ms', '—')} ms/token, "
                         f"TPOT p99 {metrics.get('tpot_p99_ms', '—')} ms.")
        if item["failure_reasons"]:
            lines.append(f"- Failures: {', '.join(item['failure_reasons'])}")
        lines += ["", "Files:", ""]
        lines.extend(f"- `{path}`" for path in item["files"])
        lines.append("")
    lines += ["## Proposals", ""]
    if not data["proposals"]:
        lines.append("No autonomous proposals recorded.")
    for item in data["proposals"]:
        proposal = item.get("proposal") or {}
        lines += [f"- `{item['proposal_id']}` → `{item['config_id']}`: "
                  f"{proposal.get('hypothesis', 'hypothesis unavailable')}; "
                  f"feedback {((item.get('feedback') or {}).get('status') or 'pending')}."]
    lines += ["", "## Codex research attempts", ""]
    if not data["attempts"]:
        lines.append("No proposer attempts recorded.")
    for item in data["attempts"]:
        lines.append(f"- `{item['attempt']}`: {item['status']}; `{item['directory']}`")
        lines.extend(f"  - `{path}`" for path in item["files"])
    lines += ["", "## Adaptive load studies", ""]
    if not data["adaptive_studies"]:
        lines.append("No normalized adaptive load studies recorded.")
    for study in data["adaptive_studies"]:
        lines.append(f"- `{study['path']}`: {study.get('point_count', 'unreadable')} trials; "
                     f"statuses {study.get('status_counts', {})}; native history "
                     f"`{study.get('native_history') or 'unavailable'}`.")
        for point in study.get("points", []):
            metrics = point.get("metrics") or {}
            lines.append(f"  - `{point.get('point_id')}`: configured/realized "
                         f"{point.get('configured_rate')}/{point.get('realized_rate')} requests/s; "
                         f"{point.get('status')}; output {metrics.get('output_tokens_per_s', '—')} tok/s; "
                         f"TTFT p50/p90/p99 "
                         f"{metrics.get('ttft_p50_ms', '—')}/{metrics.get('ttft_p90_ms', '—')}/"
                         f"{metrics.get('ttft_p99_ms', '—')} ms; reasons {point.get('reason_codes') or []}.")
    lines += ["", "## Timeline", ""]
    lines.extend(f"- {item['seq']} {item['utc']} {item['kind']} `{item['entity_id']}`"
                 + (f" · {item['state']}" if item['state'] else "")
                 + (f" · {item['reason']}" if item['reason'] else "") for item in data["timeline"])
    return "\n".join(lines) + "\n"


def write_inspection(ledger: Ledger, campaign_id: str, root: Path,
                     backend: str) -> dict[str, Any]:
    data = build_inspection(ledger, campaign_id, root, backend)
    target = Path(root) / "inspection"
    target.mkdir(parents=True, exist_ok=True)
    for name, content in (("index.json", json.dumps(data, indent=2, sort_keys=True) + "\n"),
                          ("INDEX.md", _markdown(data))):
        tmp = target / f".{name}.tmp"
        tmp.write_text(content)
        os.replace(tmp, target / name)
    return {"campaign_id": campaign_id, "backend": backend,
            "event_count": data["event_count"], "evaluation_count": len(data["evaluations"]),
            "proposal_count": len(data["proposals"]),
            "attempt_count": len(data["attempts"]),
            "adaptive_study_count": len(data["adaptive_studies"]),
            "index_json": str(target / "index.json"), "index_markdown": str(target / "INDEX.md"),
            "ledger": str(ledger.path)}

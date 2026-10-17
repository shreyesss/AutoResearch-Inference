#!/usr/bin/env python3
"""Independently replay and verify the four OPS synthetic inputs on Qwen B0.

Run after the source calibration queue has stopped. ``replay`` writes raw AIPerf
outputs and a tracked, content-addressed validation report. ``promote`` changes
prepared cards/manifests to validated only when that report passes all checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDS = ("qwen-ops-chat-low-v1", "qwen-ops-agent-low-v1",
       "qwen-ops-document-reference-v1", "qwen-ops-mixed-reference-v1")
ASSETS = ROOT / "configs/workloads/ops-frozen"
OUT = ROOT / ".artifacts/ops4-frozen-validation"
REPORT = ROOT / "infra/ops4-frozen-validation.json"
SCHEMA_VERSION = "ops4-frozen-validation-v1"
MODEL = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def asset_paths(scenario_id: str) -> tuple[Path, Path, Path]:
    if scenario_id not in IDS:
        raise ValueError(f"not in the selected frozen suite: {scenario_id}")
    return (ASSETS / f"{scenario_id}.jsonl", ASSETS / f"{scenario_id}.card.json",
            ASSETS / f"{scenario_id}.json")


def verify(scenario_id: str, target: Path) -> dict:
    asset, _, manifest_path = asset_paths(scenario_id)
    manifest = json.loads(manifest_path.read_text())
    planned = rows(asset)
    if sha(asset) != manifest["payload_sha256"] or len(planned) != manifest["n_planned"]:
        raise ValueError(f"{scenario_id}: frozen asset differs from manifest")
    summary = json.loads((target / "profile_export_aiperf.json").read_text())
    raw_path = target / "profile_export_raw.jsonl"
    records_path = target / "profile_export.jsonl"
    raw = rows(raw_path)
    records = rows(records_path)
    if summary.get("is_complete") is not True or len(raw) != len(records) or len(raw) != len(planned):
        raise ValueError(f"{scenario_id}: replay incomplete or request count mismatch")
    by_id = {item["metadata"]["conversation_id"]: item for item in raw}
    metrics = {item["metadata"]["x_request_id"]: item["metrics"] for item in records}
    if len(by_id) != len(planned) or len(metrics) != len(records):
        raise ValueError(f"{scenario_id}: duplicate replay IDs")
    prompt_min, prompt_max = math.inf, 0
    lags = []
    first_credit = min(item["metadata"]["credit_issued_ns"] for item in raw)
    for expected in planned:
        item = by_id.get(expected["session_id"])
        if item is None or item["status"] != 200:
            raise ValueError(f"{scenario_id}: missing or failed {expected['session_id']}")
        payload = item["payload"]
        if (payload.get("model") != MODEL or
            payload.get("messages") != [{"role": "user", "content": expected["text"]}] or
            payload.get("max_completion_tokens") != expected["output_length"] or
            any(payload.get(key) != value for key, value in expected["extra"].items())):
            raise ValueError(f"{scenario_id}: payload mismatch {expected['session_id']}")
        metric = metrics[item["metadata"]["x_request_id"]]
        completion = metric.get("usage_completion_tokens", {}).get("value")
        prompt = metric.get("usage_prompt_tokens", {}).get("value")
        if completion != expected["output_length"] or not isinstance(prompt, int):
            raise ValueError(f"{scenario_id}: output cap or prompt usage mismatch")
        prompt_min, prompt_max = min(prompt_min, prompt), max(prompt_max, prompt)
        credit = item["metadata"]["credit_issued_ns"]
        start = item["metadata"]["request_start_ns"]
        offset = (credit - first_credit) / 1e6
        if abs(offset - expected["timestamp"]) > 20:
            raise ValueError(f"{scenario_id}: fixed credit schedule drift above 20 ms")
        lag = (start - credit) / 1e6
        lags.append(lag)
    if max(lags) > 20:
        raise ValueError(f"{scenario_id}: client dispatch lag above 20 ms")
    return {"status": "validated", "planned": len(planned), "http_200": len(raw),
            "payload_match": True, "output_caps_realized": True, "schedule_match": True,
            "asset_sha256": sha(asset), "raw_sha256": sha(raw_path),
            "records_sha256": sha(records_path),
            "prompt_tokens_min_max": [prompt_min, prompt_max],
            "max_dispatch_lag_ms": max(lags),
            "artifact_path": str(target.relative_to(ROOT))}


def replay() -> None:
    subprocess.run(["curl", "--fail", "--silent", "--max-time", "3",
                    "http://127.0.0.1:8000/health"], check=True, stdout=subprocess.DEVNULL)
    cache = subprocess.run([str(ROOT / "infra/prepare-aiperf-tokenizer-cache.sh")],
                           check=True, capture_output=True, text=True).stdout.strip()
    env = os.environ | {"HF_HUB_CACHE": cache, "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1"}
    OUT.mkdir(parents=True, exist_ok=True)
    result = (json.loads(REPORT.read_text()) if REPORT.exists() else
              {"schema_version": SCHEMA_VERSION, "scenarios": {}})
    if result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("existing validation report has an unexpected schema")
    for scenario_id in IDS:
        asset, _, manifest_path = asset_paths(scenario_id)
        manifest = json.loads(manifest_path.read_text())
        if manifest["readiness"] != "prepared":
            raise ValueError(f"{scenario_id}: expected prepared manifest")
        if scenario_id in result["scenarios"]:
            verify(scenario_id, OUT / scenario_id)
            print(f"already validated {scenario_id}", flush=True)
            continue
        duration = math.ceil(rows(asset)[-1]["timestamp"] / 1000) + 10
        grace = min(300, max(180, duration))
        target = OUT / scenario_id
        target.mkdir()
        argv = [str(ROOT / ".venv/bin/aiperf"), "profile", "--model", MODEL,
                "--endpoint-type", "chat", "--endpoint", "/v1/chat/completions",
                "--streaming", "--url", "127.0.0.1:8000", "--tokenizer", MODEL,
                "--tokenizer-revision", REVISION, "--apply-chat-template",
                "--use-server-token-count", "--per-chunk-usage",
                "--custom-dataset-type", "single-turn", "--input-file", str(asset),
                "--fixed-schedule", "--fixed-schedule-auto-offset",
                "--benchmark-duration", str(duration), "--benchmark-grace-period", str(grace),
                "--export-level", "raw", "--export-http-trace",
                "--output-artifact-dir", str(target)]
        (target / "argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        with (target / "console.log").open("w") as stream:
            completed = subprocess.run(argv, cwd=ROOT, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, timeout=duration + grace + 120,
                                       check=False)
        (target / "exit.json").write_text(json.dumps({"exit_code": completed.returncode}) + "\n")
        if completed.returncode:
            raise RuntimeError(f"{scenario_id}: AIPerf exited {completed.returncode}; inspect {target}")
        result["scenarios"][scenario_id] = verify(scenario_id, target)
        print(f"validated {scenario_id}: {result['scenarios'][scenario_id]['planned']} requests", flush=True)
        pending = REPORT.with_suffix(".json.tmp")
        pending.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        pending.replace(REPORT)
    print(REPORT)


def promote() -> None:
    report = json.loads(REPORT.read_text())
    if report.get("schema_version") != SCHEMA_VERSION or set(report["scenarios"]) != set(IDS):
        raise ValueError("incomplete frozen validation report")
    for scenario_id in IDS:
        asset, card_path, manifest_path = asset_paths(scenario_id)
        entry = report["scenarios"][scenario_id]
        manifest = json.loads(manifest_path.read_text())
        if (entry["status"] != "validated" or entry["planned"] != manifest["n_planned"] or
            entry["http_200"] != entry["planned"] or entry["asset_sha256"] != sha(asset) or
            any(entry[key] is not True for key in
                ("payload_match", "output_caps_realized", "schedule_match"))):
            raise ValueError(f"{scenario_id}: validation evidence mismatch")
        if manifest["readiness"] != "prepared":
            raise ValueError(f"{scenario_id}: cannot re-promote")
    report_hash = sha(REPORT)
    for scenario_id in IDS:
        _, card_path, manifest_path = asset_paths(scenario_id)
        card = json.loads(card_path.read_text())
        manifest = json.loads(manifest_path.read_text())
        card["readiness"] = manifest["readiness"] = "validated"
        card["limitations"] = [item for item in card.get("limitations", [])
                               if "requires an independent fixed-schedule" not in item]
        card["validation_report_path"] = str(REPORT.relative_to(ROOT))
        card["validation_report_sha256"] = report_hash
        manifest["notes"] = "Independently fixed-schedule replay-validated on Qwen B0."
        card_path.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
        manifest["workload_card_sha256"] = sha(card_path)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"promoted {len(IDS)} validated scenarios; report sha256={report_hash}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("replay", "promote"))
    parser.add_argument("--split-plan", type=Path,
                        help="Use predeclared v2 independent windows instead of historical OPS4")
    parser.add_argument("--split-stage", choices=("development_replication", "sealed_test"),
                        help="Required with --split-plan; validate only this independent stage")
    parser.add_argument("--scenario",
                        help="Replay one predeclared split window first; promotion still requires the full stage")
    args = parser.parse_args()
    if args.split_plan:
        if not args.split_stage:
            parser.error("--split-stage is required with --split-plan")
        from inference_autoresearch.evaluation.split_v2 import load_split_plan
        split_plan = load_split_plan(args.split_plan, root=ROOT)
        IDS = tuple(row["scenario_id"] for row in split_plan["stages"][args.split_stage]["windows"])
        if args.scenario:
            if args.action != "replay":
                parser.error("--scenario is only valid for replay; promote requires the full stage")
            if args.scenario not in IDS:
                parser.error("--scenario must be a predeclared window in --split-stage")
            IDS = (args.scenario,)
        OUT = ROOT / ".artifacts/v2-independent-validation" / args.split_stage
        REPORT = OUT / "validation-report.json"
        SCHEMA_VERSION = "v2-independent-validation-v1"
    elif args.split_stage:
        parser.error("--split-stage requires --split-plan")
    elif args.scenario:
        parser.error("--scenario requires --split-plan and --split-stage")
    replay() if args.action == "replay" else promote()

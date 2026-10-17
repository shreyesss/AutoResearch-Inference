#!/usr/bin/env python3
"""Validate manual serving probes against frozen chat assets and B0 repeats."""

import csv
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(".artifacts/manual-serving-search-v1")
MANIFEST = Path("infra/b0-frozen-inputs-manifest.json")
BASELINE = Path("infra/sequence-cap-pilot-results.json")
CELL_RESULT = runpy.run_path("infra/analyze-sequence-cap-pilot.py")["cell_result"]
PHASES = ("mtp1a", "cap128a", "mtp3a", "b0check", "mtp1b", "mtp3b")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counters(path):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(
            line for line in stream if not line.startswith("#") and line.strip()))
    wanted = ("vllm:spec_decode_num_drafts", "vllm:spec_decode_num_draft_tokens",
              "vllm:spec_decode_num_accepted_tokens")
    found = {row["Metric"]: float(row["avg"]) for row in rows if row["Metric"] in wanted}
    drafts = found.get("vllm:spec_decode_num_draft_tokens", 0)
    accepted = found.get("vllm:spec_decode_num_accepted_tokens", 0)
    if drafts:
        found["acceptance_fraction"] = accepted / drafts
    return found


def nonempty_visible_responses(path):
    count = 0
    for line in path.read_text().splitlines():
        if not line:
            continue
        request = json.loads(line)
        content = []
        for response in request["responses"]:
            for packet in response["packets"]:
                if packet["name"] != "data" or packet["value"] == "[DONE]":
                    continue
                chunk = json.loads(packet["value"])
                for choice in chunk.get("choices") or []:
                    content.append(choice.get("delta", {}).get("content") or "")
        count += bool("".join(content).strip())
    return count


def main():
    manifest = json.loads(MANIFEST.read_text())
    baseline = json.loads(BASELINE.read_text())
    assert all(baseline["cells"][phase][cell]["valid_realization"]
               for phase in ("b0a", "b0b") for cell in ("r256", "r32"))
    output = {
        "version": "manual-serving-search-results-v1",
        "plan_sha256": sha256(Path("infra/manual-search-plan.json")),
        "manifest_sha256": sha256(MANIFEST),
        "baseline_results_sha256": sha256(BASELINE),
        "baseline_phases": ["b0a", "b0b"],
        "baseline_cells": {phase: baseline["cells"][phase] for phase in ("b0a", "b0b")},
        "phases": {},
    }
    for cell, entry in manifest["assets"].items():
        if sha256(Path(entry["path"])) != entry["sha256"]:
            raise RuntimeError(f"Frozen input asset changed: {cell}")
    for phase in PHASES:
        phase_dir = ROOT / phase
        argv_path = phase_dir / "server-argv.json"
        if not argv_path.exists():
            continue
        argv = json.loads(argv_path.read_text())
        cap = argv[argv.index("--max-num-seqs") + 1]
        expected_cap = "128" if phase == "cap128a" else "512"
        if cap != expected_cap:
            raise RuntimeError(f"{phase}: unexpected sequence cap {cap}")
        actual_mtp = None
        if "--speculative-config" in argv:
            actual_mtp = json.loads(argv[argv.index("--speculative-config") + 1])
        expected_depth = 1 if phase in ("mtp1a", "mtp1b") else 3 if phase in ("mtp3a", "mtp3b") else 0
        if ((actual_mtp or {}).get("num_speculative_tokens", 0) != expected_depth
            or (actual_mtp is not None and actual_mtp.get("method") != "mtp")):
            raise RuntimeError(f"{phase}: unexpected MTP config {actual_mtp}")
        record = {"max_num_seqs": int(cap), "mtp_depth": expected_depth, "cells": {}}
        for cell, entry in manifest["assets"].items():
            directory = phase_dir / cell
            if (directory / "profile_export_raw.jsonl").exists():
                result = CELL_RESULT(directory, Path(entry["path"]), entry["rows"])
                result["speculation_counters"] = counters(directory / "server_metrics_export.csv")
                result["nonempty_visible_responses"] = nonempty_visible_responses(
                    directory / "profile_export_raw.jsonl")
                if result["nonempty_visible_responses"] != entry["rows"]:
                    result["valid_realization"] = False
                    result["issues"].append("missing visible assistant content")
                record["cells"][cell] = result
        output["phases"][phase] = record
    target = Path("infra/manual-serving-search-results.json")
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    for phase, record in output["phases"].items():
        for cell, result in record["cells"].items():
            print(json.dumps({
                "phase": phase, "cell": cell, "valid": result["valid_realization"],
                "ttft_p50_p99": result["ttft_ms_p50_p99"],
                "tpot_p50_p99": result["tpot_ms_p50_p99"],
                "output_tokens_per_s": result["finite_run_output_tokens_per_s"],
                "waiting_max": result["server_gauges"].get("vllm:num_requests_waiting", {}).get("max"),
                "late_outstanding": [bin_["outstanding_at_end"] for bin_ in result["send_bin_10s"][-3:]],
                "speculation": result["speculation_counters"],
            }))


if __name__ == "__main__":
    main()

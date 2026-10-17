#!/usr/bin/env python3
"""Print reproducible AIPerf capture commands for independent v2 windows; no GPU work.

After the operator captures each source cell, freeze it with
freeze-ops-synthetic-cell.py --split development|sealed_test, then validate
its fixed-schedule replay before marking the card and manifest validated.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from inference_autoresearch.evaluation.split_v2 import load_split_plan


ROOT = Path(__file__).resolve().parents[1]


def _input_planner():
    path = ROOT / "infra/prepare-ops-synthetic-inputs.py"
    spec = importlib.util.spec_from_file_location("ops_input_planner", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.plan


def capture_plans(spec_path: Path, artifact_root: Path) -> list[dict]:
    split_plan = load_split_plan(spec_path, root=ROOT)
    generation = split_plan["generation"]
    plan_input = _input_planner()
    result = []
    for stage_name in ("development_replication", "sealed_test"):
        split = "development" if stage_name == "development_replication" else "sealed_test"
        for window in split_plan["stages"][stage_name]["windows"]:
            cell = artifact_root / window["scenario_id"]
            source = plan_input(
                "mixed", rate=generation["request_rate_rps"],
                count=generation["request_count_per_window"],
                duration=generation["benchmark_duration_s"],
                dataset_entries=generation["dataset_entries"],
                random_seed=window["seed"],
                artifact_dir=cell / "aiperf/mixed",
            )
            if source["source_sha256"] != split_plan["source_sha256"]:
                raise ValueError("OPS mixed source changed")
            result.append({"stage": stage_name, "scenario_id": window["scenario_id"],
                           "seed": window["seed"],
                           "runner_argv": [".venv/bin/python", "infra/run-ops-b0.py",
                                           "--workload", "mixed", "--rate", str(generation["request_rate_rps"]),
                                           "--count", str(generation["request_count_per_window"]),
                                           "--duration", str(generation["benchmark_duration_s"]),
                                           "--timeout", str(generation["benchmark_duration_s"] + 600),
                                           "--dataset-entries",
                                           str(generation["dataset_entries"]), "--random-seed",
                                           str(window["seed"]), "--root", str(artifact_root),
                                           "--cell", window["scenario_id"]],
                           "freeze_argv": [".venv/bin/python", "infra/freeze-ops-synthetic-cell.py",
                                           "--cell", str(cell), "--scenario-id", window["scenario_id"],
                                           "--split", split]})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=ROOT / "configs/evaluation-splits-v3.json")
    parser.add_argument("--artifact-root", type=Path,
                        default=ROOT / ".artifacts/v3-independent-capture")
    args = parser.parse_args()
    print(json.dumps(capture_plans(args.spec, args.artifact_root), indent=2))


if __name__ == "__main__":
    main()

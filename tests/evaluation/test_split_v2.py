import json
import subprocess
from pathlib import Path

import pytest

from inference_autoresearch.evaluation.split_v2 import (
    SplitError, audit_confirmation_pairs, audit_frozen_splits, load_split_plan,
    require_window_class_counts,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "configs/evaluation-splits-v3.json"


def test_independent_windows_are_predeclared_and_not_pretended_ready():
    plan = load_split_plan(SPEC, root=ROOT)
    assert [window["seed"] for stage in plan["stages"].values()
            for window in stage["windows"]] == [1042, 1043, 2042, 2043]
    assert plan["stages"]["sealed_test"]["proposer_visible"] is False
    with pytest.raises(SplitError, match="not captured"):
        audit_frozen_splits(plan, root=ROOT)


def test_seed_reuse_and_test_visibility_fail_closed(tmp_path):
    data = json.loads(SPEC.read_text())
    data["stages"]["sealed_test"]["windows"][0]["seed"] = 1042
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data))
    with pytest.raises(SplitError, match="unique and disjoint"):
        load_split_plan(path, root=ROOT)
    data["stages"]["sealed_test"]["windows"][0]["seed"] = 2042
    data["stages"]["sealed_test"]["proposer_visible"] = True
    path.write_text(json.dumps(data))
    with pytest.raises(SplitError, match="withheld"):
        load_split_plan(path, root=ROOT)


def test_confirmation_requires_matched_complete_normal_cells():
    plan = load_split_plan(SPEC, root=ROOT)
    expected = [window["scenario_id"] for window in plan["stages"]["development_replication"]["windows"]]
    audit = {"status": "input_audit_passed", "windows": [
        {"stage": "development_replication", "scenario_id": identifier} for identifier in expected]}

    def cell(identifier, config):
        return {"cell_id": f"{config}:{identifier}", "scenario_id": identifier,
                "config_id": config, "status": "valid", "behavior": "normal",
                "counts": {"planned": 240, "completed": 240, "failed": 0, "timed_out": 0,
                           "canceled": 0, "censored": 0, "not_dispatched": 0},
                "metrics": {"output_tokens_per_s": 55.0, "ttft_p90_ms": 5500.0,
                            "tpot_p90_ms": 58.0}}

    baseline = [cell(identifier, "b0") for identifier in expected]
    candidate = [cell(identifier, "candidate") for identifier in expected]
    result = audit_confirmation_pairs(plan, audit, "development_replication", baseline, candidate)
    assert result["status"] == "eligible_for_sla_scoring" and result["sla_claim"] is False
    candidate[0]["counts"]["completed"] = 239
    with pytest.raises(SplitError, match="Incomplete"):
        audit_confirmation_pairs(plan, audit, "development_replication", baseline, candidate)


def test_capture_plan_uses_separate_seeds_without_running_gpu(tmp_path):
    completed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "infra/plan-v3-independent-splits.py"),
         "--artifact-root", str(tmp_path / "capture")],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    commands = json.loads(completed.stdout)
    assert len(commands) == 4
    assert {item["seed"] for item in commands} == {1042, 1043, 2042, 2043}
    assert all(item["runner_argv"][item["runner_argv"].index("--count") + 1] == "240"
               for item in commands)
    assert not (tmp_path / "capture").exists()


def test_class_minimum_applies_to_each_window_not_pooled_stage():
    def labels(counts):
        return {f"request-{index}": shape
                for index, shape in enumerate(
                    shape for name, count in counts.items() for shape in [name] * count)}

    # Two such windows would have 58 documents pooled, but neither qualifies.
    too_few = labels({"chat": 110, "agent": 51, "code": 50, "document": 29})
    with pytest.raises(SplitError, match="Window lacks 30"):
        require_window_class_counts(too_few, expected_count=240, minimum=30)
    enough = labels({"chat": 109, "agent": 51, "code": 50, "document": 30})
    assert require_window_class_counts(enough, expected_count=240, minimum=30)["document"] == 30

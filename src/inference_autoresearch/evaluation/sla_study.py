"""Fail-closed readiness audit for a future class-aware SLA campaign.

This scaffold is deliberately not an `iar` campaign. Passing its audit means
the inputs may be wired into a new versioned campaign; it never reports an
SLA capacity or starts a benchmark.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inference_autoresearch.evaluation.sla import validate_policy
from inference_autoresearch.evaluation.split_v2 import SplitError, load_split_plan
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import WorkloadError, sha256_file, verify_scenario


class SLAStudyError(ValueError):
    pass


def _under(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise SLAStudyError("study paths must be nonempty and relative to the project root")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise SLAStudyError("study path escapes the project root")
    return path


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SLAStudyError(f"expected a JSON object: {path}")
    return value


def audit_sla_study(path: Path, *, root: Path) -> dict[str, Any]:
    """Return explicit blockers; never treat an absent artifact as qualified."""
    root = Path(root).resolve()
    study = _read_object(path)
    if study.get("schema_version") != "sla-study-scaffold-v1" or study.get("claim") != "not_runnable_until_qualified":
        raise SLAStudyError("unsupported SLA study scaffold")
    screen = study["screen"]
    development = study["adaptive_development"]
    policy_ref = study["policy"]
    if (screen.get("scenario_id") != "qwen-ops-mixed-reference-v1"
            or screen.get("request_count") != 36
            or screen.get("claim") != "large_regression_screen_only"):
        raise SLAStudyError("screen must remain the frozen 36-request regression check")
    if (development.get("scenario_id") == screen["scenario_id"]
            or development.get("manifest_path") == screen.get("manifest_path")
            or development.get("request_count_per_point") != 240
            or development.get("claim") != "observed_class_slo_points_only"):
        raise SLAStudyError("adaptive points require a distinct 240-request development scenario")
    if (policy_ref.get("agent_evidence_source") != policy_ref.get("path")
            or study.get("capacity_confirmation", {}).get("required") is not True):
        raise SLAStudyError("policy evidence path and independent confirmation are mandatory")
    if "proposed" in policy_ref["path"].lower():
        raise SLAStudyError("an approved, versioned policy file is required")
    source_campaign = _read_object(_under(root, study["source_campaign_path"]))
    if source_campaign.get("campaign_id") != "qwen38-27b-eval-v2":
        raise SLAStudyError("SLA scaffold must identify the pinned exploratory source campaign")
    pinned = PinnedEnvironment(_under(root, source_campaign["model"]["local_path"]))
    baseline_id = resolve_config({}, pinned).config_id
    blockers: list[str] = []
    split_ref = study["capacity_confirmation"]["split_plan_path"]
    try:
        split = load_split_plan(_under(root, split_ref), root=root)
        dev_ids = {row["scenario_id"] for row in split["stages"]["development_replication"]["windows"]}
        if (development["scenario_id"] not in dev_ids
                or split["generation"]["request_count_per_window"] != 240
                or split["source_manifest_sha256"] != screen["manifest_sha256"]):
            blockers.append("development_not_in_qualified_split_plan")
    except (OSError, ValueError, KeyError, SplitError):
        blockers.append("development_split_plan_missing_or_changed")

    screen_path = _under(root, screen["manifest_path"])
    verified_screen: dict[str, Any] | None = None
    if not screen_path.is_file() or sha256_file(screen_path) != screen.get("manifest_sha256"):
        blockers.append("screen_manifest_missing_or_changed")
    else:
        try:
            manifest = _read_object(screen_path)
            verified_screen = verify_scenario(manifest, root=root)
            if manifest.get("scenario_id") != screen["scenario_id"] or len(verified_screen["planned"]) != 36:
                blockers.append("screen_manifest_not_qualified_36")
        except (ValueError, KeyError, OSError, WorkloadError):
            blockers.append("screen_manifest_not_qualified_36")

    policy: dict[str, Any] | None = None
    policy_path = _under(root, policy_ref["path"])
    if (policy_ref.get("approval_status") != "approved"
            or not isinstance(policy_ref.get("approved_by"), str)
            or not policy_ref["approved_by"].strip()):
        blockers.append("application_sla_policy_not_approved")
    if (not isinstance(policy_ref.get("sha256"), str)
            or len(policy_ref["sha256"]) != 64
            or not policy_path.is_file()
            or sha256_file(policy_path) != policy_ref["sha256"]):
        blockers.append("sla_policy_hash_missing_or_changed")
    else:
        try:
            policy = _read_object(policy_path)
            validate_policy(policy)
            if "proposed" in policy["policy_id"].lower():
                blockers.append("sla_policy_id_still_proposed")
        except (ValueError, KeyError, OSError):
            blockers.append("sla_policy_invalid")

    development_path = _under(root, development["manifest_path"])
    class_path = _under(root, development["request_class_path"])
    verified_development: dict[str, Any] | None = None
    if (not isinstance(development.get("manifest_sha256"), str)
            or len(development["manifest_sha256"]) != 64
            or not development_path.is_file()
            or sha256_file(development_path) != development["manifest_sha256"]):
        blockers.append("development_manifest_missing_or_unpinned")
    elif (not isinstance(development.get("request_class_sha256"), str)
          or len(development["request_class_sha256"]) != 64
          or not class_path.is_file()
          or sha256_file(class_path) != development["request_class_sha256"]):
        blockers.append("development_class_sidecar_missing_or_unpinned")
    else:
        try:
            manifest = _read_object(development_path)
            if (manifest.get("scenario_id") != development["scenario_id"]
                    or manifest.get("suite_role") != "development"
                    or manifest.get("n_planned") != 240
                    or manifest.get("request_class_path") != development["request_class_path"]
                    or manifest.get("request_class_sha256") != development["request_class_sha256"]
                    or manifest.get("payload_sha256") == _read_object(screen_path).get("payload_sha256")):
                raise SLAStudyError("development manifest identity, sidecar, or content is wrong")
            verified_development = verify_scenario(manifest, root=root)
            if verified_development["request_classes"] is None:
                raise SLAStudyError("development request classes are absent")
            if verified_screen is not None:
                source_texts = {row["text"] for row in verified_screen["planned"]}
                development_texts = [row["text"] for row in verified_development["planned"]]
                if len(set(development_texts)) != len(development_texts) or source_texts.intersection(development_texts):
                    blockers.append("development_reuses_screen_content")
                if ([row["timestamp"] for row in verified_screen["planned"]]
                        == [row["timestamp"] for row in verified_development["planned"]]):
                    blockers.append("development_reuses_screen_arrivals")
            if policy is not None:
                counts = {name: list(verified_development["request_classes"].values()).count(name)
                          for name in policy["classes"]}
                if set(verified_development["request_classes"].values()) != set(policy["classes"]):
                    blockers.append("development_classes_do_not_match_policy")
                if any(counts[name] < policy["classes"][name]["min_eligible_requests"] for name in counts):
                    blockers.append("development_class_sample_count_below_policy_minimum")
        except (ValueError, KeyError, OSError, WorkloadError):
            blockers.append("development_manifest_or_sidecar_not_qualified")

    cell_paths = development.get("baseline_cell_paths")
    minimum = development.get("minimum_baseline_cells")
    if not isinstance(cell_paths, list) or type(minimum) is not int or minimum < 1 or len(cell_paths) < minimum:
        blockers.append("development_b0_cells_missing")
    elif verified_development is not None:
        seen_ids: set[str] = set()
        for cell_ref in cell_paths:
            cell_path = _under(root, cell_ref)
            try:
                cell = _read_object(cell_path)
                counts = cell["counts"]
                if (cell.get("scenario_id") != development["scenario_id"]
                        or cell.get("config_id") != baseline_id
                        or cell.get("status") != "valid" or cell.get("behavior") != "normal"
                        or cell.get("cell_id") in seen_ids
                        or counts.get("planned") != 240 or counts.get("dispatched") != 240
                        or counts.get("completed") != 240
                        or any(counts.get(key) != 0 for key in
                               ("failed", "timed_out", "canceled", "censored", "not_dispatched"))
                        or cell.get("diagnostics", {}).get("planned_schedule_sha256")
                           != _read_object(development_path)["schedule_sha256"]
                        or not Path(cell.get("artifacts", {}).get("raw_requests", "")).is_file()):
                    raise SLAStudyError("B0 cell is not complete on the pinned development traffic")
                seen_ids.add(cell["cell_id"])
            except (ValueError, KeyError, OSError, TypeError):
                blockers.append("development_b0_cell_not_qualified")
                break

    return {"study_id": study["campaign_id"],
            "status": "inputs_ready_for_new_campaign" if not blockers else "blocked",
            "blockers": sorted(set(blockers)),
            "screen_request_count": 36,
            "adaptive_request_count_per_point": 240,
            "adaptive_scenario_id": development["scenario_id"],
            "policy_sha256": policy_ref.get("sha256"),
            "agent_policy_evidence_path": policy_ref["agent_evidence_source"],
            "capacity_confirmed": False,
            "note": "Readiness only; AIPerf throughput-only selection is not an SLA capacity result."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("configs/sla-study-v3.template.json"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = audit_sla_study(args.study, root=args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] == "blocked":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Schema-bound Codex CLI proposal driver and explicitly labeled deterministic mock."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal, ProposalContext
from inference_autoresearch.evaluation.sla import validate_policy
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from .domain import Domain


class ProposerError(RuntimeError):
    pass


def _write_snapshot(path: Path, content: bytes) -> str:
    """Write a controller-owned research input and return its content digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ProposerError(f"research snapshot changed: {path}")
        return digest
    path.write_bytes(content)
    path.chmod(0o444)
    return digest


def _stage_previous_attempts(proposal_root: Path, run_dir: Path) -> list[dict[str, Any]]:
    """Copy bounded prior research artifacts; never mount old writable attempts."""
    history = []
    for previous in sorted(proposal_root.glob("attempt-[0-9][0-9][0-9][0-9]"))[-12:]:
        if previous == run_dir or not previous.is_dir() or previous.is_symlink():
            continue
        record = {"attempt": previous.name, "files": []}
        for relative in ("workspace/notes.md", "proposal.normalized.json", "proposer-receipt.json"):
            source = previous / relative
            if not source.is_file() or source.is_symlink():
                continue
            content = source.read_bytes()
            if len(content) > 65536:
                record["files"].append({"source": relative, "omitted": "over_64_kib"})
                continue
            target = run_dir / "history" / previous.name / Path(relative).name
            digest = _write_snapshot(target, content)
            record["files"].append({"path": str(target.relative_to(run_dir)), "sha256": digest,
                                    "bytes": len(content)})
        history.append(record)
    return history


_CELL_RESEARCH_FILES = (
    "cell-result.json", "cell-result-v02.json", "controller-validation.json", "timing.json",
    "aiperf/normalized-requests.jsonl", "aiperf/profile_export.jsonl",
    "aiperf/profile_export_aiperf.json", "aiperf/profile_export_aiperf.csv",
    "aiperf/server_metrics_export.csv", "aiperf/server_metrics_export.json",
    "aiperf/profile_export_console.txt", "aiperf/workload-class-summaries.json",
    "aiperf/aiperf-console.log", "aiperf/aiperf-argv.json", "aiperf/aiperf-exit.json",
    "server/server.log", "server/startup.log", "server/telemetry.jsonl",
    "server/requested-config.json", "server/resolved-startup.json", "server/hardware.json",
)
_EVALUATION_RESEARCH_FILES = (
    "resolved-config.json", "evaluation-result.json", "proposal.json", "evaluation-policy.json",
)
_ADAPTIVE_RESEARCH_BASENAMES = {
    "normalized-search-points.json", "search_history.json",
    "adaptive-points.json", "adaptive-points.csv", "sla-profile-points.json",
}


def _study_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ProposerError("SLA study references must be project-relative paths")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or any(
            marker in part.lower() for part in path.relative_to(root).parts
            for marker in ("sealed", "heldout", "test")):
        raise ProposerError("SLA study cannot stage paths outside development evidence")
    return path


def _checked_study_source(root: Path, relative: str, digest: str) -> Path:
    path = _study_file(root, relative)
    if (not isinstance(digest, str) or len(digest) != 64 or not path.is_file()
            or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
        raise ProposerError(f"SLA study source missing or changed: {relative}")
    return path


def _stage_matched_b0(study: dict[str, Any], root: Path, run_dir: Path,
                      baseline_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    development = study["adaptive_development"]
    manifest = _checked_study_source(root, development["manifest_path"],
                                     development.get("manifest_sha256"))
    classes = _checked_study_source(root, development["request_class_path"],
                                    development.get("request_class_sha256"))
    manifest_staged = run_dir / "sla-study" / "development-manifest.json"
    classes_staged = run_dir / "sla-study" / "development-classes.json"
    _write_snapshot(manifest_staged, manifest.read_bytes())
    _write_snapshot(classes_staged, classes.read_bytes())
    anchor = development.get("baseline_cell_paths")
    replication = development.get("matched_baseline_replication_cell_paths")
    if (not isinstance(anchor, list) or len(anchor) != 1
            or not isinstance(replication, list) or not replication):
        raise ProposerError("v3 agent requires matched B0 anchor and independent replication cells")
    cells = []
    for role, paths in (("development_anchor", anchor), ("development_replication", replication)):
        for position, relative in enumerate(paths):
            digest_expected = development.get("baseline_cell_sha256_by_path", {}).get(relative)
            raw_digest_expected = development.get("baseline_raw_sha256_by_path", {}).get(relative)
            source = _checked_study_source(root, relative, digest_expected)
            cell = json.loads(source.read_text())
            raw_source = Path(str(cell.get("artifacts", {}).get("raw_requests", ""))).resolve()
            if (not raw_source.is_relative_to(root) or not raw_source.is_file()
                    or raw_source.is_symlink() or not isinstance(raw_digest_expected, str)
                    or len(raw_digest_expected) != 64
                    or hashlib.sha256(raw_source.read_bytes()).hexdigest() != raw_digest_expected):
                raise ProposerError("matched B0 raw request evidence is missing or changed")
            counts = cell.get("counts", {})
            if (cell.get("config_id") != baseline_id
                    or cell.get("status") != "valid" or cell.get("behavior") != "normal"
                    or counts.get("planned") != 240 or counts.get("dispatched") != 240
                    or counts.get("completed") != 240
                    or any(counts.get(key) != 0 for key in
                           ("failed", "timed_out", "canceled", "censored", "not_dispatched"))
                    or (role == "development_anchor"
                        and cell.get("scenario_id") != development["scenario_id"])):
                raise ProposerError("matched B0 CellResult is not qualified")
            if raw_source.stat().st_size > 16 * 1024 * 1024:
                raise ProposerError("matched B0 raw request file exceeds 16 MiB staging limit")
            destination = run_dir / "sla-study" / "matched-b0" / f"{role}-{position:02d}"
            cell_staged = destination / "cell-result.json"
            raw_staged = destination / raw_source.name
            _write_snapshot(cell_staged, source.read_bytes())
            _write_snapshot(raw_staged, raw_source.read_bytes())
            cells.append({"role": role, "evidence_id": str(cell["cell_id"]),
                          "scenario_id": cell["scenario_id"], "config_id": baseline_id,
                          "metrics": cell.get("metrics", {}), "counts": counts,
                          "source": {"path": str(cell_staged.relative_to(run_dir)),
                                     "sha256": digest_expected},
                          "raw_requests": {"path": str(raw_staged.relative_to(run_dir)),
                                           "sha256": raw_digest_expected}})
    return cells, {"manifest": {"path": str(manifest_staged.relative_to(run_dir)),
                                "sha256": development["manifest_sha256"]},
                   "class_sidecar": {"path": str(classes_staged.relative_to(run_dir)),
                                     "sha256": development["request_class_sha256"]}}


def _stage_sla_study(study_path: Path, run_dir: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Stage approved policy and class-aware B0 trials before a v3 Codex proposal.

    This is deliberately a strict, explicit input. A missing assessment or an
    exploratory load point cannot silently become an SLA capacity claim.
    """
    study_path = study_path.resolve()
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    if not study_path.is_relative_to(root) or not study_path.is_file():
        raise ProposerError("SLA study must be an existing file under the project root")
    study_bytes = study_path.read_bytes()
    study = json.loads(study_bytes)
    if (study.get("schema_version") != "sla-study-scaffold-v1"
            or study.get("claim") != "not_runnable_until_qualified"):
        raise ProposerError("unsupported SLA study specification")
    policy_ref = study.get("policy", {})
    if (policy_ref.get("approval_status") != "approved"
            or not policy_ref.get("approved_by")
            or policy_ref.get("agent_evidence_source") != policy_ref.get("path")
            or "proposed" in str(policy_ref.get("path", "")).lower()):
        raise ProposerError("SLA policy is not approved for agent research")
    policy_path = _checked_study_source(root, policy_ref["path"], policy_ref.get("sha256"))
    policy = json.loads(policy_path.read_text())
    validate_policy(policy)
    if "proposed" in policy["policy_id"].lower():
        raise ProposerError("SLA policy ID remains proposed")
    development = study.get("adaptive_development", {})
    scenario_id = development.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ProposerError("SLA study lacks a development scenario")
    source_campaign = json.loads(_study_file(root, study["source_campaign_path"]).read_text())
    baseline_id = resolve_config({}, PinnedEnvironment(
        _study_file(root, source_campaign["model"]["local_path"]))).config_id
    runs = study.get("baseline_adaptive_run_paths")
    if not isinstance(runs, list) or not runs:
        raise ProposerError("SLA study needs at least one assessed B0 adaptive run before proposals")
    _write_snapshot(run_dir / "sla-study" / "study.json", study_bytes)
    policy_staged = run_dir / "sla-study" / "approved-policy.json"
    _write_snapshot(policy_staged, policy_path.read_bytes())
    matched_b0, development_inputs = _stage_matched_b0(study, root, run_dir, baseline_id)
    indexed = []
    for number, entry in enumerate(runs):
        if not isinstance(entry, dict):
            raise ProposerError("SLA adaptive run references must be objects")
        source = _checked_study_source(root, entry.get("source_path"), entry.get("source_sha256"))
        if source.name == "sla-profile-points.json":
            profile = json.loads(source.read_text())
            qualified = [point["qualified"] for point in profile.get("points", [])
                         if isinstance(point, dict) and isinstance(point.get("qualified"), dict)]
            class_assessments = [item["assessment"] for item in qualified
                                 if isinstance(item.get("assessment"), dict)]
            if (profile.get("schema_version") != "sla-profile-points-v1"
                    or profile.get("claim") != "observed_development_points_no_confirmed_capacity"
                    or profile.get("capacity_confirmed") is not False
                    or profile.get("config_id") != baseline_id
                    or profile.get("development_scenario_id") != scenario_id
                    or profile.get("policy_id") != policy["policy_id"]
                    or profile.get("policy_sha256") != policy_ref["sha256"]
                    or not isinstance(profile.get("points"), list) or not class_assessments
                    or any(item.get("policy_id") != policy["policy_id"]
                           or set(item.get("classes", {})) != set(policy["classes"])
                           for item in class_assessments)):
                raise ProposerError("B0 SLA profile is not class-assessed under the approved policy")
            staged = run_dir / "sla-study" / f"b0-adaptive-{number:02d}" / source.name
            _write_snapshot(staged, source.read_bytes())
            native_files = []
            remaining_bytes = 128 * 1024 * 1024
            for point_index, point in enumerate(profile["points"]):
                if not isinstance(point, dict):
                    continue
                for gate in ("screen", "qualified"):
                    gate_result = point.get(gate)
                    if not isinstance(gate_result, dict):
                        continue
                    artifacts = gate_result.get("artifacts") or {}
                    for label in ("summary", "raw", "records", "server_metrics"):
                        native = artifacts.get(label)
                        if not isinstance(native, dict):
                            continue
                        reference = {"point_index": point_index, "gate": gate,
                                     "label": label, "source": native}
                        path = Path(str(native.get("path", ""))).resolve()
                        digest = native.get("sha256")
                        if (not path.is_relative_to(source.parent.parent)
                                or not path.is_file() or path.is_symlink()
                                or path.stat().st_size > 16 * 1024 * 1024
                                or path.stat().st_size > remaining_bytes
                                or not isinstance(digest, str) or len(digest) != 64):
                            reference["omitted"] = "missing_outside_run_or_staging_budget"
                        else:
                            data = path.read_bytes()
                            if hashlib.sha256(data).hexdigest() != digest:
                                reference["omitted"] = "native_artifact_hash_mismatch"
                            else:
                                native_staged = staged.parent / "native" / f"point-{point_index:03d}" / gate / label / path.name
                                _write_snapshot(native_staged, data)
                                reference["staged"] = {"path": str(native_staged.relative_to(run_dir)),
                                                       "sha256": digest, "bytes": len(data)}
                                remaining_bytes -= len(data)
                        native_files.append(reference)
            indexed.append({"evidence_id": f"b0-adaptive-{number:02d}",
                            "config_id": baseline_id, "scenario_id": scenario_id,
                            "claim": profile["claim"], "capacity_confirmed": False,
                            "source": {"path": str(staged.relative_to(run_dir)),
                                       "sha256": entry["source_sha256"]},
                            "point_count": len(profile["points"]),
                            "class_assessed_point_count": len(class_assessments),
                            "native_artifacts": native_files,
                            "points": profile["points"]})
            continue
        assessment = _checked_study_source(root, entry.get("assessment_path"),
                                           entry.get("assessment_sha256"))
        if source.name != "normalized-search-points.json" or assessment.suffix != ".json":
            raise ProposerError("SLA adaptive references must name normalized points and JSON assessment")
        points = json.loads(source.read_text())
        report = json.loads(assessment.read_text())
        if (points.get("claim") != "exploratory_load_curve_only"
                or points.get("config_id") != baseline_id
                or points.get("scenario_id") != scenario_id
                or not isinstance(points.get("points"), list) or not points["points"]
                or report.get("schema_version") != "adaptive-sla-assessment-v1"
                or report.get("claim") != "observed_adaptive_points_only_no_confirmed_capacity"
                or report.get("capacity_confirmed") is not False
                or report.get("config_id") != baseline_id
                or report.get("scenario_id") != scenario_id
                or report.get("policy_id") != policy["policy_id"]
                or report.get("policy_sha256") != hashlib.sha256(json.dumps(policy, sort_keys=True,
                        separators=(",", ":")).encode()).hexdigest()
                or report.get("source_sha256") != entry["source_sha256"]
                or Path(str(report.get("source", ""))).resolve() != source):
            raise ProposerError("B0 adaptive evidence does not match approved policy and development scenario")
        folder = run_dir / "sla-study" / f"b0-adaptive-{number:02d}"
        points_staged = folder / "normalized-search-points.json"
        report_staged = folder / "sla-assessment.json"
        _write_snapshot(points_staged, source.read_bytes())
        _write_snapshot(report_staged, assessment.read_bytes())
        indexed.append({"evidence_id": f"b0-adaptive-{number:02d}",
                        "config_id": baseline_id, "scenario_id": scenario_id,
                        "claim": "observed_class_slo_points_only_no_confirmed_capacity",
                        "source": {"path": str(points_staged.relative_to(run_dir)),
                                   "sha256": entry["source_sha256"]},
                        "assessment": {"path": str(report_staged.relative_to(run_dir)),
                                       "sha256": entry["assessment_sha256"]},
                        "point_count": len(points["points"]),
                        "observed_feasible_point_count": report.get("observed_feasible_point_count"),
                        "points": [{key: point.get(key) for key in
                                    ("point_id", "configured_rate", "realized_rate", "status",
                                     "reason_codes", "counts", "metrics", "class_metrics",
                                     "class_label_policy")}
                                   for point in points["points"] if isinstance(point, dict)]})
    packet = {"schema_version": "agent-sla-evidence-v1",
              "study_sha256": hashlib.sha256(study_bytes).hexdigest(),
              "policy_id": policy["policy_id"], "policy_sha256": policy_ref["sha256"],
              "policy_path": str(policy_staged.relative_to(run_dir)),
              "target_type": "approved_research_target_not_product_sla",
              "development_inputs": development_inputs,
              "matched_b0_cells": matched_b0,
              "baseline_adaptive_studies": indexed, "capacity_confirmed": False,
              "limitation": "Adaptive observations alone do not confirm an SLA boundary; independent windows remain required."}
    _write_snapshot(run_dir / "sla-study-index.json", (json.dumps(packet, indent=2) + "\n").encode())
    return packet


def _adaptive_point_index(record: dict[str, Any], run_dir: Path) -> dict[str, Any] | None:
    """Make staged exploratory trials discoverable without claiming SLA capacity."""
    if record["stage"] not in ("capacity", "sla_profile"):
        return None
    source = next((item for item in record["files"]
                   if Path(item["path"]).name in
                   ("normalized-search-points.json", "sla-profile-points.json")), None)
    if source is None:
        return None
    try:
        payload = json.loads((run_dir / source["path"]).read_text())
    except (OSError, ValueError):
        record["omitted"].append({"artifact": "normalized_search_points",
                                  "reason": "unreadable_adaptive_history"})
        return None
    if Path(source["path"]).name == "sla-profile-points.json":
        if (not isinstance(payload, dict)
                or payload.get("schema_version") != "sla-profile-points-v1"
                or payload.get("claim") != "observed_development_points_no_confirmed_capacity"
                or payload.get("capacity_confirmed") is not False
                or payload.get("config_id") != record["config_id"]
                or payload.get("development_scenario_id") != record["scenario_id"]
                or not isinstance(payload.get("points"), list)):
            record["omitted"].append({"artifact": "sla_profile_points",
                                      "reason": "sla_profile_identity_or_claim_mismatch"})
            return None
        return {"cell_id": record["cell_id"], "config_id": record["config_id"],
                "scenario_id": record["scenario_id"], "claim": payload["claim"],
                "policy_id": payload.get("policy_id"), "policy_sha256": payload.get("policy_sha256"),
                "capacity_confirmed": False, "source": source,
                "point_count": len(payload["points"]), "points": payload["points"]}
    if (not isinstance(payload, dict) or not isinstance(payload.get("points"), list)
            or payload.get("claim") != "exploratory_load_curve_only"
            or payload.get("config_id") != record["config_id"]
            or payload.get("scenario_id") != record["scenario_id"]):
        record["omitted"].append({"artifact": "normalized_search_points",
                                  "reason": "adaptive_history_identity_or_claim_mismatch"})
        return None
    points = []
    for point in payload["points"]:
        if not isinstance(point, dict):
            continue
        points.append({key: point.get(key) for key in (
            "point_id", "iteration_idx", "trial_index", "configured_rate", "realized_rate",
            "status", "reason_codes", "counts", "metrics", "planner_feasible",
            "objective_values", "sample_count_policy", "class_metrics", "class_label_policy")})
    return {"cell_id": record["cell_id"], "config_id": record["config_id"],
            "scenario_id": record["scenario_id"], "claim": "exploratory_load_curve_only",
            "capacity_confirmed": False, "source": source, "point_count": len(points),
            "sla_assessments": record.get("sla_assessments", []),
            "points": points}


def _stage_adaptive_sla_reports(source: Path, record: dict[str, Any], run_dir: Path,
                                destination: Path, budget: int) -> int:
    """Stage only reports tied to this visible ledger cell and adaptive source."""
    if (source.name != "normalized-search-points.json" or source.parent.name != "aiperf"
            or not source.is_file()):
        return budget
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    folders = (source.parent.parent / "sla-assessments", source.parent / "sla-assessments")
    assessments = []
    for folder in folders:
        if not folder.is_dir() or folder.is_symlink():
            continue
        for report_path in sorted(folder.glob("policy-*.json"))[:16]:
            if not report_path.is_file() or report_path.is_symlink():
                continue
            if report_path.stat().st_size > 16 * 1024 * 1024:
                record["omitted"].append({"artifact": report_path.name,
                                          "reason": "file_over_16_mib"})
                continue
            try:
                report = json.loads(report_path.read_text())
            except (OSError, ValueError):
                record["omitted"].append({"artifact": report_path.name,
                                          "reason": "unreadable_sla_assessment"})
                continue
            if (not isinstance(report, dict)
                    or report.get("schema_version") != "adaptive-sla-assessment-v1"
                    or report.get("claim") != "observed_adaptive_points_only_no_confirmed_capacity"
                    or report.get("capacity_confirmed") is not False
                    or report.get("config_id") != record["config_id"]
                    or report.get("scenario_id") != record["scenario_id"]
                    or report.get("source_sha256") != source_digest
                    or Path(str(report.get("source", ""))).resolve() != source.resolve()):
                record["omitted"].append({"artifact": report_path.name,
                                          "reason": "sla_assessment_provenance_mismatch"})
                continue
            before = len(record["files"])
            budget = _copy_research_file(report_path, destination / "sla-assessments" / report_path.name,
                                         run_dir, record, budget)
            if len(record["files"]) == before:
                continue
            assessments.append({"policy_id": report.get("policy_id"),
                                "policy_sha256": report.get("policy_sha256"),
                                "claim": report["claim"], "capacity_confirmed": False,
                                "point_count": report.get("point_count"),
                                "observed_feasible_point_count": report.get("observed_feasible_point_count"),
                                "source": record["files"][-1]})
    if assessments:
        record["sla_assessments"] = assessments
    return budget


def _stage_sla_profile_native_files(source: Path, record: dict[str, Any], run_dir: Path,
                                    destination: Path, budget: int) -> int:
    """Keep raw trial links inspectable inside the isolated Codex container."""
    try:
        profile = json.loads(source.read_text())
    except (OSError, ValueError):
        return budget
    for number, point in enumerate(profile.get("points", [])):
        if not isinstance(point, dict):
            continue
        for gate in ("screen", "qualified"):
            details = point.get(gate)
            if not isinstance(details, dict):
                continue
            artifacts = details.get("artifacts") or {}
            for label in ("summary", "raw", "records", "server_metrics"):
                ref = artifacts.get(label)
                if not isinstance(ref, dict):
                    continue
                native = Path(str(ref.get("path", ""))).resolve()
                digest = ref.get("sha256")
                if (not native.is_relative_to(source.parent.parent) or not native.is_file()
                        or native.is_symlink() or not isinstance(digest, str)
                        or len(digest) != 64 or hashlib.sha256(native.read_bytes()).hexdigest() != digest):
                    record["omitted"].append({"artifact": f"{number}:{gate}:{label}",
                                              "reason": "native_sla_profile_artifact_missing_or_changed"})
                    continue
                budget = _copy_research_file(native,
                    destination / "native" / f"point-{number:03d}" / gate / label / native.name,
                    run_dir, record, budget)
    return budget


def _stage_measurements(context: ProposalContext, artifact_root: Path,
                        run_dir: Path) -> dict[str, Any]:
    """Expose only controller-recorded, non-heldout same-campaign run files."""
    root = artifact_root.resolve()
    rows = [row for row in context.recent_results if isinstance(row, dict)]
    for scope in context.frontier:
        if isinstance(scope, dict):
            rows.extend(row for row in scope.get("cells", []) if isinstance(row, dict))
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    adaptive_studies: list[dict[str, Any]] = []
    budget = 128 * 1024 * 1024
    for row in rows:
        cell_id = str(row.get("cell_id", ""))
        stage = str(row.get("stage", ""))
        if not cell_id or cell_id in seen or not stage or any(
                marker in stage.lower() for marker in ("heldout", "sealed", "test")):
            continue
        seen.add(cell_id)
        artifacts = row.get("artifacts") or {}
        if not isinstance(artifacts, dict):
            artifacts = {}
        record = {"cell_id": cell_id, "stage": stage, "scenario_id": row.get("scenario_id"),
                  "config_id": row.get("config_id"), "measurement_protocol": row.get("measurement_protocol"),
                  "offered_load": row.get("offered_load"), "load_unit": row.get("load_unit"),
                  "matched_baseline_cell_id": row.get("matched_baseline_cell_id"),
                  "evidence_grade": row.get("evidence_grade", "ungraded"),
                  "metrics": row.get("metrics", {}), "counts": row.get("counts", {}),
                  "status": row.get("status"), "behavior": row.get("behavior"),
                  "reason_codes": row.get("reason_codes", []),
                  "uncertainty": row.get("uncertainty", "unavailable"),
                  "files": [], "omitted": []}
        for label, artifact_path in artifacts.items():
            if not isinstance(artifact_path, str) or Path(artifact_path).name not in _ADAPTIVE_RESEARCH_BASENAMES:
                continue
            adaptive_source = Path(artifact_path).resolve()
            if not adaptive_source.is_relative_to(root):
                record["omitted"].append({"artifact": label, "reason": "adaptive_artifact_outside_campaign"})
                continue
            budget = _copy_research_file(adaptive_source,
                                         run_dir / "measurements" / "adaptive" / f"record-{len(records):04d}"
                                         / adaptive_source.name, run_dir, record, budget)
            if adaptive_source.name == "normalized-search-points.json":
                budget = _stage_adaptive_sla_reports(
                    adaptive_source, record, run_dir,
                    run_dir / "measurements" / "adaptive" / f"record-{len(records):04d}", budget)
            elif adaptive_source.name == "sla-profile-points.json":
                budget = _stage_sla_profile_native_files(
                    adaptive_source, record, run_dir,
                    run_dir / "measurements" / "adaptive" / f"record-{len(records):04d}", budget)
        adaptive_index = _adaptive_point_index(record, run_dir)
        if adaptive_index is not None:
            adaptive_studies.append(adaptive_index)
        reference = artifacts.get("raw_requests") or artifacts.get("aiperf_export")
        if not isinstance(reference, str):
            record["omitted"].append({"reason": "no_raw_artifact_reference"})
            records.append(record)
            continue
        source = Path(reference).resolve()
        if not source.is_relative_to(root):
            record["omitted"].append({"reason": "raw_artifact_outside_campaign"})
            records.append(record)
            continue
        cell_dir = next((part for part in source.parents if part.name.startswith("cell-")
                         and part.parent.name.startswith("eval-")), None)
        if cell_dir is None or not cell_dir.is_relative_to(root):
            record["omitted"].append({"reason": "raw_artifact_not_in_cell"})
            records.append(record)
            continue
        evaluation_dir = cell_dir.parent
        destination = run_dir / "measurements" / evaluation_dir.name / cell_dir.name
        for relative in _CELL_RESEARCH_FILES:
            source_file = cell_dir / relative
            budget = _copy_research_file(source_file, destination / relative, run_dir,
                                         record, budget)
        for relative in _EVALUATION_RESEARCH_FILES:
            source_file = evaluation_dir / relative
            budget = _copy_research_file(source_file,
                                         run_dir / "measurements" / evaluation_dir.name / relative,
                                         run_dir, record, budget)
        records.append(record)
    result = {"cells": records, "adaptive_studies": adaptive_studies,
              "file_size_limit_bytes": 16 * 1024 * 1024,
              "total_size_limit_bytes": 128 * 1024 * 1024,
              "scope": "controller-provided visible development cells; heldout/test excluded",
              "excluded": "Unlisted native raw exports, model weights and unrelated artifacts"}
    _write_snapshot(run_dir / "measurements-index.json", (json.dumps(result, indent=2) + "\n").encode())
    _write_snapshot(run_dir / "evaluation-index.json", (json.dumps({
        "schema_version": "evaluation-index-v1", "campaign_id": context.campaign_id,
        "cells": records, "adaptive_studies": adaptive_studies,
        "visible_cell_count": len(records),
        "note": "Controller-provided development evidence only; source files listed with SHA-256 in files."
    }, indent=2) + "\n").encode())
    return result


def _copy_research_file(source: Path, destination: Path, run_dir: Path,
                        record: dict[str, Any], budget: int) -> int:
    if not source.is_file() or source.is_symlink():
        return budget
    size = source.stat().st_size
    relative = str(destination.relative_to(run_dir))
    if size > 16 * 1024 * 1024:
        record["omitted"].append({"path": relative, "reason": "file_over_16_mib", "bytes": size})
        return budget
    if size > budget:
        record["omitted"].append({"path": relative, "reason": "total_128_mib_budget", "bytes": size})
        return budget
    content = source.read_bytes()
    if len(content) != size:
        record["omitted"].append({"path": relative, "reason": "changed_while_staging"})
        return budget
    already_staged = destination.exists()
    digest = _write_snapshot(destination, content)
    record["files"].append({"path": relative, "sha256": digest, "bytes": size})
    return budget if already_staged else budget - size


def parse_proposal(raw: dict[str, Any], domain: Domain, allowed_evidence_ids: set[str]) -> CandidateProposal:
    from jsonschema import Draft202012Validator
    errors = sorted(Draft202012Validator(domain.proposal_schema()).iter_errors(raw), key=lambda x: list(x.path))
    if errors:
        raise ProposerError(f"proposal schema violation: {errors[0].message}")
    if raw.get("schema_version") != "0.2":
        raise ProposerError("proposal schema_version must be 0.2")
    allowed_keys = set(domain.proposal_schema()["properties"])
    if set(raw) != allowed_keys:
        raise ProposerError(f"proposal fields differ from contract: {sorted(set(raw) ^ allowed_keys)}")
    domain.validate(raw["parameters"])
    if not raw["proposal_id"] or not raw["falsification_condition"] or not raw["predictions"]:
        raise ProposerError("proposal ID, falsification and predictions are required")
    if not set(raw["evidence_ids"]).issubset(allowed_evidence_ids):
        raise ProposerError("proposal cites evidence outside allowlist")
    return CandidateProposal(
        proposal_id=raw["proposal_id"], parameters=raw["parameters"],
        parent_configuration_ids=raw["parent_configuration_ids"], hypothesis=raw["hypothesis"],
        expected_tradeoff=raw["expected_tradeoff"], evidence_ids=raw["evidence_ids"],
        experiment_kind=raw["experiment_kind"], predictions=raw["predictions"],
        falsification_condition=raw["falsification_condition"],
        requested_observations=raw["requested_observations"],
    )


def parse_codex_output(raw: dict[str, Any], domain: Domain,
                       allowed_evidence_ids: set[str]) -> CandidateProposal:
    """Validate strict model output, then normalize nullable overrides to v0.2."""
    from jsonschema import Draft202012Validator
    errors = sorted(Draft202012Validator(domain.codex_output_schema()).iter_errors(raw),
                    key=lambda x: list(x.path))
    if errors:
        raise ProposerError(f"Codex output schema violation: {errors[0].message}")
    sparse = dict(raw)
    sparse["parameters"] = {key: value for key, value in raw["parameters"].items()
                            if value is not None}
    return parse_proposal(sparse, domain, allowed_evidence_ids)


class CodexProposer:
    def __init__(self, domain: Domain, artifact_root: Path, timeout_s: int = 180,
                 skill_path: Path | None = None, cli: str = "codex",
                 expected_version: str | None = None, model: str | None = None,
                 reasoning_effort: str | None = None, web_search: str = "disabled",
                 sla_study_path: Path | None = None):
        self.domain = domain
        self.artifact_root = Path(artifact_root)
        self.timeout_s = timeout_s
        self.skill_path = Path(skill_path) if skill_path else Path(__file__).resolve().parents[3] / "agent" / "SKILL.md"
        self.cli = cli
        self.expected_version = expected_version
        if model is not None and (not model or any(c.isspace() for c in model)):
            raise ValueError("proposer model must be one nonempty model ID")
        if reasoning_effort not in (None, "low", "medium", "high", "xhigh", "max", "ultra"):
            raise ValueError("unsupported proposer reasoning effort")
        if web_search not in ("disabled", "cached", "indexed", "live"):
            raise ValueError("unsupported proposer web-search mode")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.web_search = web_search
        self.sla_study_path = Path(sla_study_path) if sla_study_path is not None else None

    def propose(self, context: ProposalContext) -> CandidateProposal:
        binary = shutil.which(self.cli)
        if binary is None:
            raise ProposerError("Codex CLI unavailable; no fallback proposer")
        # Codex's own shell sandbox is unavailable inside the nested proposer.
        # The full-access mode below is safe only when the Docker wrapper is the
        # executable. Refuse a host Codex binary in the default real path.
        if self.cli == "codex":
            with open(binary, "rb") as executable:
                marker = executable.read(2048)
            if b"IAR_ISOLATED_CODEX_WRAPPER=1" not in marker:
                raise ProposerError("real Codex proposer requires the isolated Docker wrapper")
        env_keys = ("HOME", "CODEX_HOME", "PATH", "LANG", "LC_ALL", "HTTPS_PROXY", "HTTP_PROXY",
                    "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "IAR_REPO_ROOT",
                    "IAR_CODEX_HOME", "IAR_PROPOSER_IMAGE")
        env = {key: os.environ[key] for key in env_keys if key in os.environ}
        version = subprocess.run([binary, "--version"], capture_output=True, text=True,
                                 timeout=10, check=False, env=env)
        if version.returncode or "codex-cli" not in version.stdout:
            raise ProposerError(f"Codex CLI version check failed: {version.stderr[:300]}")
        if self.expected_version and self.expected_version not in version.stdout:
            raise ProposerError("Codex CLI version differs from campaign pin")
        auth = subprocess.run([binary, "login", "status"], capture_output=True, text=True,
                              timeout=15, check=False, env=env)
        if auth.returncode:
            raise ProposerError("Codex CLI authentication unavailable; no fallback proposer")
        proposal_root = self.artifact_root / "proposals"
        previous = [int(path.name.split("-")[-1]) for path in proposal_root.glob("attempt-*")
                    if path.name.split("-")[-1].isdigit()]
        run_dir = proposal_root / f"attempt-{max(previous, default=0) + 1:04d}"
        run_dir.mkdir(parents=True, exist_ok=False)
        workspace = run_dir / "workspace"
        workspace.mkdir(mode=0o777)
        workspace.chmod(0o777)
        schema_file = run_dir / "proposal.schema.json"
        final_file = run_dir / "proposal.final.json"
        event_file = run_dir / "codex.events.jsonl"
        stderr_file = run_dir / "codex.stderr.txt"
        input_file = run_dir / "context.json"
        _write_snapshot(schema_file, (json.dumps(self.domain.codex_output_schema(), indent=2) + "\n").encode())
        skill = self.skill_path.read_text()
        reference = self.skill_path.with_name("reference.md").read_text()
        _write_snapshot(run_dir / "SKILL.md", skill.encode())
        _write_snapshot(run_dir / "reference.md", reference.encode())
        retrieval_audit = []
        staged_refs = []
        evidence_dir = run_dir / "evidence"
        evidence_dir.mkdir()
        for ref in context.evidence_refs:
            path = Path(ref.get("snapshot_path", ""))
            if not path.is_file():
                continue
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != ref.get("sha256"):
                raise ProposerError(f"evidence changed: {ref.get('evidence_id')}")
            evidence_id = str(ref["evidence_id"])
            if not evidence_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in evidence_id):
                raise ProposerError("unsafe evidence ID")
            staged = evidence_dir / f"{evidence_id}.txt"
            _write_snapshot(staged, data)
            staged_refs.append({"evidence_id": ref["evidence_id"], "source_sha256": ref["sha256"],
                                "path": str(staged.relative_to(run_dir)), "bytes": len(data)})
            retrieval_audit.append({"evidence_id": ref["evidence_id"], "bytes": len(data),
                                    "sha256": ref["sha256"], "path": str(staged.relative_to(run_dir))})
        context_payload = asdict(context)
        context_payload["evidence_refs"] = staged_refs
        _write_snapshot(input_file, (json.dumps(context_payload, indent=2, default=str) + "\n").encode())
        _write_snapshot(run_dir / "retrieval-audit.json", (json.dumps(retrieval_audit, indent=2) + "\n").encode())
        (run_dir / "history").mkdir()
        history = _stage_previous_attempts(proposal_root, run_dir)
        measurements = _stage_measurements(context, self.artifact_root, run_dir)
        sla_evidence = (_stage_sla_study(self.sla_study_path, run_dir)
                        if self.sla_study_path is not None else None)
        research_index = {
            "current": {"skill": "../SKILL.md", "reference": "../reference.md",
                        "context": "../context.json", "evidence": "../evidence/",
                        "schema": "../proposal.schema.json",
                        "measurements": "../measurements-index.json",
                        "evaluation": "../evaluation-index.json"},
            "previous_attempts": history,
            "measurement_cells": len(measurements["cells"]),
            "adaptive_studies": len(measurements["adaptive_studies"]),
            "adaptive_points": sum(item["point_count"] for item in measurements["adaptive_studies"]),
            "writable_notes": "notes.md",
            "authority": "Only parameter proposals; the controller owns traffic and evaluation.",
        }
        if sla_evidence is not None:
            research_index["sla_evidence"] = "../sla-study-index.json"
            research_index["sla_policy_id"] = sla_evidence["policy_id"]
            research_index["sla_policy_sha256"] = sla_evidence["policy_sha256"]
            research_index["baseline_adaptive_studies"] = len(sla_evidence["baseline_adaptive_studies"])
            research_index["matched_b0_cells"] = len(sla_evidence["matched_b0_cells"])
        _write_snapshot(run_dir / "research-index.json", (json.dumps(research_index, indent=2) + "\n").encode())
        # The isolated proposer runs as uid 1000 while the controller may run as
        # root. Codex writes its last message itself, so pre-create only that
        # output as writable; keep the staged inputs and directory read-only to it.
        final_file.touch()
        final_file.chmod(0o666)
        prompt = ("You are the serving autoresearch proposer. First read ../SKILL.md and "
                  "../reference.md. Inspect ../research-index.json and ../context.json; open "
                  "the staged evidence under ../evidence/, prior notes under ../history/, "
                  "and scoped real-run files listed by ../evaluation-index.json and ../measurements-index.json. "
                  + ("Before proposing, read ../sla-study-index.json, its hash-checked approved research policy, "
                     "and B0 adaptive trial assessments. Treat all sampled rates as observations, not confirmed capacity. "
                     if sla_evidence is not None else "") +
                  "Use shell/file reads freely inside this isolated research container. "
                  "Write any durable reasoning for the next attempt to notes.md here. "
                  "Return exactly one JSON proposal matching ../proposal.schema.json. "
                  "The controller alone validates and evaluates it.")
        argv = [binary, "exec", "--sandbox", "danger-full-access", "--skip-git-repo-check",
                "--ignore-user-config", "--ephemeral", "--json"]
        if self.model:
            argv.extend(("--model", self.model))
        if self.reasoning_effort:
            argv.extend(("--config", f'model_reasoning_effort="{self.reasoning_effort}"'))
        argv.extend(("--config", f'web_search="{self.web_search}"', "--cd", str(workspace),
                     "--output-schema", str(schema_file), "--output-last-message", str(final_file), "-"))
        receipt_file = run_dir / "proposer-receipt.json"
        receipt = {"driver": "codex-cli", "version": version.stdout.strip(), "argv": argv,
                   "model": self.model, "reasoning_effort": self.reasoning_effort,
                   "web_search": self.web_search,
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "skill_sha256": hashlib.sha256(skill.encode()).hexdigest(),
                   "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
                   "schema_sha256": hashlib.sha256(schema_file.read_bytes()).hexdigest(),
                   "sandbox": "docker-isolated-research-workspace", "cwd": str(workspace),
                   "research_index": str(run_dir / "research-index.json"),
                   "staged_evidence_count": len(staged_refs),
                   "staged_measurement_cells": len(measurements["cells"]),
                   "staged_measurement_files": sum(len(cell["files"]) for cell in measurements["cells"]),
                   "staged_adaptive_studies": len(measurements["adaptive_studies"]),
                   "staged_adaptive_points": sum(item["point_count"] for item in measurements["adaptive_studies"]),
                   "sla_study_sha256": sla_evidence["study_sha256"] if sla_evidence else None,
                   "sla_policy_sha256": sla_evidence["policy_sha256"] if sla_evidence else None,
                   "staged_b0_adaptive_studies": len(sla_evidence["baseline_adaptive_studies"]) if sla_evidence else 0,
                   "previous_attempts": len(history),
                   "status": "started"}
        receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
        try:
            with event_file.open("w") as event_out, stderr_file.open("w") as err_out:
                process = subprocess.run(argv, input=prompt, stdout=event_out, stderr=err_out,
                                         text=True, timeout=self.timeout_s, check=False, env=env)
        except subprocess.TimeoutExpired as exc:
            receipt["status"] = "timeout"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex proposer timed out after {self.timeout_s}s; events={event_file}") from exc
        receipt["exit_code"] = process.returncode
        if process.returncode:
            receipt["status"] = "failed"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex proposer failed exit={process.returncode}; stderr={stderr_file}")
        if not final_file.exists() or not final_file.stat().st_size:
            receipt["status"] = "missing_final"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex returned no final JSON; events={event_file}")
        try:
            raw = json.loads(final_file.read_text())
        except (ValueError, OSError) as exc:
            receipt["status"] = "invalid_final_json"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex final response is not JSON: {final_file}") from exc
        # The qualification report's immutable scenario and B0 cell IDs are
        # exposed in context.json and backed by staged measurement files.
        # Accept those citations as well as the separately staged documents.
        allowed = {str(ref["evidence_id"]) for ref in staged_refs}
        allowed.update(item for item in context.qualification.get("evidence_ids", [])
                       if isinstance(item, str))
        allowed.update(item["cell_id"] for item in measurements["cells"]
                       if isinstance(item.get("cell_id"), str))
        if sla_evidence is not None:
            allowed.update(item["evidence_id"] for item in sla_evidence["matched_b0_cells"])
            allowed.update(item["evidence_id"] for item in sla_evidence["baseline_adaptive_studies"])
            allowed.update(str(point["point_id"])
                           for study in sla_evidence["baseline_adaptive_studies"]
                           for point in study["points"] if isinstance(point.get("point_id"), str))
        try:
            proposal = parse_codex_output(raw, self.domain, allowed)
        except (ProposerError, ValueError) as exc:
            receipt["status"] = "invalid_proposal"
            receipt["validation_error"] = str(exc)
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise
        normalized_file = run_dir / "proposal.normalized.json"
        normalized_tmp = run_dir / "proposal.normalized.json.tmp"
        normalized_bytes = (json.dumps(asdict(proposal), indent=2, sort_keys=True) + "\n").encode()
        normalized_tmp.write_bytes(normalized_bytes)
        os.replace(normalized_tmp, normalized_file)
        receipt["status"] = "validated"
        receipt["proposal_sha256"] = hashlib.sha256(final_file.read_bytes()).hexdigest()
        receipt["normalized_proposal_path"] = str(normalized_file)
        receipt["normalized_proposal_sha256"] = hashlib.sha256(normalized_bytes).hexdigest()
        receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
        return proposal


class MockProposer:
    """Deterministic contract test driver; never silently used for real search."""

    def __init__(self, domain: Domain):
        self.domain = domain
        self.index = 0

    def propose(self, context: ProposalContext) -> CandidateProposal:
        axes = self.domain.raw["parameters"]
        options = [(key, value) for key, spec in axes.items() if spec.get("active") is not False for value in spec["values"]
                   if value != spec["baseline"]]
        if self.index >= len(options):
            raise ProposerError("mock proposal domain exhausted")
        key, value = options[self.index]
        self.index += 1
        return CandidateProposal(
            proposal_id=f"mock-{self.index:03d}", parameters={key: value},
            experiment_kind="exploration", hypothesis=f"Exercise {key}={value} in mock mode",
            expected_tradeoff="Contract test only; no performance claim",
            predictions=[{"observation": key, "expected_change": "mock cell completes",
                          "scope": "mock evaluator"}],
            falsification_condition="Mock evaluator rejects the candidate",
        )

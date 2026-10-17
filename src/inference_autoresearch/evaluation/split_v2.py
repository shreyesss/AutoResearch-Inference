"""Predeclare independent OPS mixed confirmation windows and audit frozen assets.

This module never turns a plan into an SLA result. Each generated window must
first be captured from AIPerf and independently replay-qualified on the B0.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from inference_autoresearch.workloads.registry import verify_scenario, sha256_file


class SplitError(ValueError):
    pass


STAGES = ("development_replication", "sealed_test")


def require_window_class_counts(request_classes: dict[str, str], *,
                                expected_count: int, minimum: int) -> dict[str, int]:
    if len(request_classes) != expected_count:
        raise SplitError("Window request-class mapping is incomplete")
    counts = Counter(request_classes.values())
    if (set(counts) != {"chat", "agent", "code", "document"}
            or any(counts.get(shape, 0) < minimum
                   for shape in ("chat", "agent", "code", "document"))):
        raise SplitError(f"Window lacks {minimum} requests per OPS class")
    return dict(counts)


def load_split_plan(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    root = Path(root or Path.cwd()).resolve()
    plan = json.loads(Path(path).read_text())
    if plan.get("schema_version") != "evaluation-splits-v3":
        raise SplitError("Unsupported split plan")
    source = (root / plan["source_yaml"]).resolve()
    if (not source.is_relative_to(root) or not source.is_file()
            or sha256_file(source) != plan["source_sha256"]):
        raise SplitError("Synthetic source is absent or has changed")
    source_manifest = (root / plan["source_manifest"]).resolve()
    if (not source_manifest.is_relative_to(root) or not source_manifest.is_file()
            or sha256_file(source_manifest) != plan["source_manifest_sha256"]):
        raise SplitError("Screen manifest is absent or has changed")
    generation = plan["generation"]
    if generation["request_count_per_window"] < 240 or generation["request_rate_rps"] <= 0:
        raise SplitError("Independent windows need a positive rate and at least 240 requests")
    if plan["qualification"].get("minimum_class_requests_per_window") != 30:
        raise SplitError("Each window must require 30 requests per OPS class")
    if generation["dataset_entries"] < generation["request_count_per_window"]:
        raise SplitError("Dataset pool is smaller than a window")
    seen_ids: set[str] = set()
    seen_seeds: set[int] = {42}
    for stage_name in STAGES:
        stage = plan["stages"][stage_name]
        if stage.get("status") != "planned_not_captured" or len(stage.get("windows", [])) < 2:
            raise SplitError(f"{stage_name} requires two planned independent windows")
        if stage.get("proposer_visible") is not (stage_name == "development_replication"):
            raise SplitError("Sealed test must be withheld from the proposer")
        for window in stage["windows"]:
            identifier, seed = window["scenario_id"], window["seed"]
            if not isinstance(identifier, str) or not identifier or type(seed) is not int:
                raise SplitError("Window requires scenario ID and integer seed")
            if identifier in seen_ids or seed in seen_seeds:
                raise SplitError("Window scenario IDs and seeds must be unique and disjoint from B0")
            seen_ids.add(identifier)
            seen_seeds.add(seed)
    return plan


def audit_frozen_splits(plan: dict[str, Any], *, root: Path,
                        stage_name: str | None = None) -> dict[str, Any]:
    """Fail closed until the selected windows are live replay-validated.

    Assets use the same pinned manifest contract as the search screen. This
    audit catches content reuse and split/seed mistakes but cannot establish
    that traffic or SLO estimates are statistically reliable.
    """
    root = Path(root).resolve()
    if stage_name is not None and stage_name not in STAGES:
        raise SplitError(f"Unknown independent split stage: {stage_name}")
    source = json.loads((root / plan["source_manifest"]).read_text())
    source_rows = verify_scenario(source, root=root)["planned"]
    seen_hashes = {hashlib.sha256(row["text"].encode()).hexdigest() for row in source_rows}
    seen_schedules = {tuple(row["timestamp"] for row in source_rows)}
    checked: list[dict[str, Any]] = []
    # Development can be qualified before sealed test exists. Sealed test must
    # be compared against development to prove the final content split.
    selected_stages = ("development_replication",) if stage_name == "development_replication" else STAGES
    stage_shapes: dict[str, dict[str, int]] = {name: {} for name in selected_stages}
    window_shapes: dict[str, dict[str, int]] = {}
    for selected_stage in selected_stages:
        for window in plan["stages"][selected_stage]["windows"]:
            path = root / "configs/workloads/ops-frozen" / f"{window['scenario_id']}.json"
            if not path.is_file():
                raise SplitError(f"Independent window not captured: {window['scenario_id']}")
            manifest = json.loads(path.read_text())
            if manifest.get("scenario_id") != window["scenario_id"]:
                raise SplitError("Window scenario ID differs from frozen manifest")
            if manifest.get("readiness") != "validated":
                raise SplitError(f"Window lacks independent replay validation: {window['scenario_id']}")
            expected_split = "development" if selected_stage == "development_replication" else "sealed_test"
            if manifest.get("suite_role") != expected_split or manifest.get("source_manifest", {}).get("split") != expected_split:
                raise SplitError(f"Window has incorrect split: {window['scenario_id']}")
            if manifest.get("seeds", {}).get("content") != window["seed"] or manifest.get("seeds", {}).get("arrivals") != window["seed"]:
                raise SplitError(f"Window seed differs from predeclared seed: {window['scenario_id']}")
            if manifest.get("source_manifest", {}).get("revision_or_hash") != plan["source_sha256"]:
                raise SplitError("Window changed the source workload")
            if manifest.get("n_planned") != plan["generation"]["request_count_per_window"]:
                raise SplitError("Window request count differs from predeclared plan")
            verified = verify_scenario(manifest, root=root)
            rows = verified["planned"]
            request_classes = verified["request_classes"]
            if request_classes is None:
                raise SplitError(f"Window lacks explicit request classes: {window['scenario_id']}")
            minimum = plan["qualification"]["minimum_class_requests_per_window"]
            shapes = require_window_class_counts(
                request_classes, expected_count=manifest["n_planned"], minimum=minimum)
            window_shapes[window["scenario_id"]] = shapes
            stage_shapes[selected_stage].update({
                shape: stage_shapes[selected_stage].get(shape, 0) + count
                for shape, count in shapes.items()
            })
            schedule = tuple(row["timestamp"] for row in rows)
            if schedule in seen_schedules:
                raise SplitError(f"Window reuses an arrival schedule: {window['scenario_id']}")
            seen_schedules.add(schedule)
            hashes = [hashlib.sha256(row["text"].encode()).hexdigest() for row in rows]
            if len(set(hashes)) != len(hashes) or set(hashes) & seen_hashes:
                raise SplitError(f"Window reuses request content: {window['scenario_id']}")
            seen_hashes.update(hashes)
            checked.append({"stage": selected_stage, "scenario_id": window["scenario_id"],
                            "manifest_sha256": sha256_file(path), "request_count": len(rows),
                            "request_class_sha256": manifest["request_class_sha256"]})
    return {"status": "input_audit_passed", "windows": checked,
            "class_counts_by_stage": stage_shapes, "class_counts_by_window": window_shapes,
            "limitations": ["B0 and candidate runs remain required on each window.",
                            "No numeric SLA or uncertainty claim follows from asset validation."]}


def audit_confirmation_pairs(plan: dict[str, Any], input_audit: dict[str, Any],
                             stage_name: str, baseline_cells: list[dict[str, Any]],
                             candidate_cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Require one valid matched B0/candidate cell per independent window.

    This checks measurement completeness and pairing, not statistical power or
    SLA attainment. Those decisions belong to the scoring protocol.
    """
    if stage_name not in STAGES or input_audit.get("status") != "input_audit_passed":
        raise SplitError("Confirmation requires audited independent inputs")
    expected = {row["scenario_id"] for row in plan["stages"][stage_name]["windows"]}
    audited = {row["scenario_id"] for row in input_audit.get("windows", [])
               if row.get("stage") == stage_name}
    if expected != audited:
        raise SplitError("Confirmation stage assets are not completely audited")
    if ({row.get("scenario_id") for row in baseline_cells} != expected
            or {row.get("scenario_id") for row in candidate_cells} != expected
            or len(baseline_cells) != len(expected) or len(candidate_cells) != len(expected)):
        raise SplitError("A matched baseline/candidate cell is required for every window")
    baseline_by_id = {row["scenario_id"]: row for row in baseline_cells}
    candidate_by_id = {row["scenario_id"]: row for row in candidate_cells}
    baseline_configs = {row.get("config_id") for row in baseline_cells}
    candidate_configs = {row.get("config_id") for row in candidate_cells}
    if (len(baseline_configs) != 1 or len(candidate_configs) != 1
            or baseline_configs == candidate_configs or None in baseline_configs | candidate_configs):
        raise SplitError("Paired cells must use one B0 and one distinct candidate configuration")
    paired = []
    for window in plan["stages"][stage_name]["windows"]:
        scenario_id = window["scenario_id"]
        pair = (baseline_by_id[scenario_id], candidate_by_id[scenario_id])
        for cell in pair:
            counts = cell.get("counts", {})
            metrics = cell.get("metrics", {})
            if (cell.get("status") != "valid" or cell.get("behavior") != "normal"
                    or counts.get("planned") != plan["generation"]["request_count_per_window"]
                    or counts.get("completed") != counts.get("planned")
                    or any(counts.get(key) != 0 for key in ("failed", "timed_out", "canceled", "censored", "not_dispatched"))):
                raise SplitError(f"Incomplete or non-normal confirmation cell: {scenario_id}")
            for metric in ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms"):
                value = metrics.get(metric)
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    raise SplitError(f"Missing confirmation metric {metric}: {scenario_id}")
        paired.append({"scenario_id": scenario_id,
                       "baseline_cell_id": pair[0]["cell_id"],
                       "candidate_cell_id": pair[1]["cell_id"]})
    return {"status": "eligible_for_sla_scoring", "stage": stage_name, "pairs": paired,
            "sla_claim": False}

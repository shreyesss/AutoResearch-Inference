"""Conservative matched-load mechanism pilot summary from immutable ledger cells."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from inference_autoresearch.search.domain import Domain, scientific_campaign_hash


OBJECTIVES = ("output_tokens_per_s", "ttft_p99_ms", "tpot_p99_ms")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _scope(cell: dict[str, Any]) -> tuple[Any, ...]:
    return (cell.get("scenario_id"), cell.get("workload_group_id"), cell.get("offered_load"),
            cell.get("load_unit"), cell.get("cache_protocol"), cell.get("measurement_protocol"),
            cell.get("stage"))


def _eligible(cell: dict[str, Any]) -> bool:
    counts = cell.get("counts", {})
    return (cell.get("status") == "valid" and cell.get("behavior") == "normal"
            and not cell.get("controller_validation")
            and counts.get("planned", 0) > 0 and counts.get("completed") == counts.get("planned")
            and all(isinstance(cell.get("metrics", {}).get(key), (int, float))
                    and math.isfinite(cell["metrics"][key]) for key in OBJECTIVES))


def _unique_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["cell_id"]: row for row in rows}
    return list(by_id.values())


def lock_pilot_plan(campaign: dict[str, Any], ledger: Any) -> dict[str, Any]:
    """Lock a declared plan before the first pilot cell; refuse retrospective plans."""
    source = campaign.get("qualification_requirements", {}).get("pilot_plan_path")
    if not source:
        raise ValueError("campaign has no pilot_plan_path")
    path = Path(source)
    if not path.is_absolute():
        path = Path(campaign.get("project_root", Path.cwd())) / path
    raw = path.read_bytes()
    plan = json.loads(raw)
    if plan.get("schema_version") != "pilot-plan-v1" or plan.get("campaign_id") != campaign["campaign_id"]:
        raise ValueError("pilot plan version/campaign mismatch")
    domain_path = Path(campaign["search_domain_path"])
    if not domain_path.is_absolute():
        domain_path = Path(campaign.get("project_root", Path.cwd())) / domain_path
    if plan.get("domain_hash") != Domain.load(domain_path).digest or plan.get("protocol_id") != "fresh-server-cell-v1":
        raise ValueError("pilot plan domain/protocol mismatch")
    events = ledger.events(campaign["campaign_id"])
    if any(row["kind"] == "cell" and row["payload"].get("stage") == "pilot"
           and not row["payload"].get("is_baseline") for row in events):
        raise ValueError("candidate pilot cells already exist; a plan cannot be locked retrospectively")
    digest = hashlib.sha256(raw).hexdigest()
    locks = [row for row in events if row["kind"] == "pilot_plan_locked"]
    if locks:
        if len(locks) != 1 or locks[0]["payload"].get("sha256") != digest:
            raise ValueError("pilot plan changed after lock")
        return locks[0]["payload"]
    receipt = {"plan_id": plan.get("plan_id", digest[:16]), "sha256": digest,
               "path": str(path), "domain_hash": plan.get("domain_hash"),
               "protocol_id": plan.get("protocol_id")}
    ledger.append(campaign["campaign_id"], "pilot_plan_locked", receipt["plan_id"], receipt)
    return receipt


def _plan_gate(campaign: dict[str, Any], events: list[dict[str, Any]],
               cells: list[dict[str, Any]], configs: dict[str, dict[str, Any]],
               domain_hash: str) -> tuple[bool, list[str], list[dict[str, Any]]]:
    source = campaign.get("qualification_requirements", {}).get("pilot_plan_path")
    if not source:
        return False, ["pilot_plan_path_missing"], []
    path = Path(source)
    if not path.is_absolute():
        path = Path(campaign.get("project_root", Path.cwd())) / path
    try:
        raw = path.read_bytes()
        plan = json.loads(raw)
    except (OSError, ValueError):
        return False, ["pilot_plan_unreadable"], []
    reasons: list[str] = []
    if plan.get("schema_version") != "pilot-plan-v1" or plan.get("campaign_id") != campaign["campaign_id"]:
        reasons.append("pilot_plan_identity_mismatch")
    if plan.get("domain_hash") != domain_hash or plan.get("protocol_id") != "fresh-server-cell-v1":
        reasons.append("pilot_plan_domain_or_protocol_mismatch")
    lock = [row for row in events if row["kind"] == "pilot_plan_locked"]
    digest = hashlib.sha256(raw).hexdigest()
    first_pilot = min((row["seq"] for row in events if row["kind"] == "cell"
                       and row["payload"].get("stage") == "pilot"
                       and not row["payload"].get("is_baseline")), default=None)
    if len(lock) != 1 or lock[0]["payload"].get("sha256") != digest or (
            first_pilot is not None and lock[0]["seq"] >= first_pilot):
        reasons.append("pilot_plan_not_locked_before_measurement")
    repeats = plan.get("min_matched_repeats", 0)
    if type(repeats) is not int or repeats < 2:
        reasons.append("pilot_repeat_policy_inadequate")
        repeats = 2
    checks: list[dict[str, Any]] = []
    planned_contrasts = plan.get("contrasts", [])
    if not isinstance(planned_contrasts, list) or not any(item.get("role") == "mechanism" for item in planned_contrasts):
        reasons.append("mechanism_contrast_missing")
        planned_contrasts = []
    stage = plan.get("stage", "pilot")
    for item in planned_contrasts:
        contrast_id = item.get("contrast_id", "unnamed")
        overrides = item.get("candidate_overrides", {})
        role = item.get("role")
        scenario_ids = item.get("scenario_ids", [])
        if not isinstance(overrides, dict) or not scenario_ids or role not in ("mechanism", "negative_control"):
            reasons.append(f"{contrast_id}:invalid_plan_contrast")
            continue
        config_ids = [key for key, data in configs.items() if data.get("overrides") == overrides]
        if len(config_ids) != 1:
            reasons.append(f"{contrast_id}:resolved_candidate_missing_or_ambiguous")
            continue
        config_id = config_ids[0]
        for scenario_id in scenario_ids:
            scoped = [row for row in cells if row.get("scenario_id") == scenario_id
                      and row.get("stage") == stage
                      and row.get("measurement_protocol") == plan.get("protocol_id")]
            baseline = _unique_cells([row for row in scoped if row.get("is_baseline") and _eligible(row)])
            candidate = _unique_cells([row for row in scoped if row.get("config_id") == config_id and _eligible(row)])
            if len(baseline) < repeats or len(candidate) < repeats:
                reasons.append(f"{contrast_id}:{scenario_id}:insufficient_clean_matched_repeats")
                checks.append({"contrast_id": contrast_id, "scenario_id": scenario_id,
                               "baseline_repeats": len(baseline), "candidate_repeats": len(candidate),
                               "qualified": False})
                continue
            # Empirical separation exceeds observed B0 run-to-run range. This is
            # a mechanism sensitivity screen, not a confidence interval or p99 SLA.
            separated = {metric: (max(row["metrics"][metric] for row in baseline) <
                                  min(row["metrics"][metric] for row in candidate) or
                                  max(row["metrics"][metric] for row in candidate) <
                                  min(row["metrics"][metric] for row in baseline))
                         for metric in OBJECTIVES}
            binding_name = item.get("required_binding_observation")
            binding_values = [row.get("diagnostics", {}).get("server_gauges", {}).get(binding_name)
                              for row in candidate] if binding_name else []
            binding_measured = bool(binding_name and all(isinstance(v, (int, float)) and v > 0
                                                         for v in binding_values))
            if role == "mechanism" and not any(separated.values()):
                reasons.append(f"{contrast_id}:{scenario_id}:effect_not_separated_from_repeat_noise")
            if role == "mechanism" and not binding_measured:
                reasons.append(f"{contrast_id}:{scenario_id}:binding_diagnostic_missing_or_inactive")
            if role == "negative_control" and item.get("expected_flat") is True and any(separated.values()):
                reasons.append(f"{contrast_id}:{scenario_id}:negative_control_not_flat")
            expected_observation = item.get("expected_observation")
            if role == "negative_control" and expected_observation:
                name = expected_observation.get("name")
                target = expected_observation.get("equals")
                observed = [row.get("diagnostics", {}).get("server_gauges", {}).get(name)
                            for row in candidate]
                if target is None or any(value != target for value in observed):
                    reasons.append(f"{contrast_id}:{scenario_id}:negative_control_observation_mismatch")
            checks.append({"contrast_id": contrast_id, "scenario_id": scenario_id,
                           "role": role, "baseline_repeats": len(baseline),
                           "candidate_repeats": len(candidate), "separated_metrics": separated,
                           "binding_observation": binding_name, "binding_values": binding_values,
                           "expected_observation": expected_observation,
                           "baseline_cell_ids": [row["cell_id"] for row in baseline],
                           "candidate_cell_ids": [row["cell_id"] for row in candidate],
                           "qualified": not any(reason.startswith(f"{contrast_id}:{scenario_id}:") for reason in reasons)})
    return not reasons, reasons, checks


def build_sensitivity_report(campaign: dict[str, Any], ledger: Any, output_path: Path) -> dict[str, Any]:
    """Summarize repeats without promoting short screens to confirmed p99 evidence.

    Results group by exact scenario/load/cache/stage/protocol. A missing B0 or
    clean candidate becomes an explicit exclusion. Replicate ranges are empirical
    ranges, never confidence intervals. The report does not unlock search itself.
    """
    campaign_id = campaign["campaign_id"]
    events = ledger.events(campaign_id)
    cells = [row["payload"] for row in events if row["kind"] == "cell"]
    configs = {row["entity_id"]: row["payload"] for row in events if row["kind"] == "resolved_config"}
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for cell in cells:
        by_scope.setdefault(_scope(cell), []).append(cell)
    contrasts: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for scope, rows in sorted(by_scope.items(), key=lambda item: str(item[0])):
        baseline = _unique_cells([row for row in rows if row.get("is_baseline") and _eligible(row)])
        candidates = {row["config_id"] for row in rows if not row.get("is_baseline")}
        for config_id in sorted(candidates):
            candidate = _unique_cells([row for row in rows if row["config_id"] == config_id and _eligible(row)])
            if not baseline or not candidate:
                excluded.append({"scope": scope, "config_id": config_id,
                                 "reason": "missing_clean_matched_baseline_or_candidate"})
                continue
            effects: dict[str, Any] = {}
            for metric in OBJECTIVES:
                b = [row["metrics"][metric] for row in baseline]
                c = [row["metrics"][metric] for row in candidate]
                bmedian, cmedian = statistics.median(b), statistics.median(c)
                effects[metric] = {
                    "baseline_median": bmedian, "candidate_median": cmedian,
                    "absolute_delta": cmedian - bmedian,
                    "relative_delta": (cmedian - bmedian) / bmedian if bmedian else None,
                    "baseline_observed_range": [min(b), max(b)],
                    "candidate_observed_range": [min(c), max(c)],
                    "ranges_separated": max(b) < min(c) or max(c) < min(b),
                }
            repeats = min(len(baseline), len(candidate))
            label = "inconclusive_single_window"
            if repeats >= 2:
                label = "measured_sensitive_provisional" if any(
                    effects[metric]["ranges_separated"] for metric in OBJECTIVES
                ) else "flat_or_uncertain"
            contrasts.append({"scope": scope, "config_id": config_id,
                              "overrides": configs.get(config_id, {}).get("overrides", {}),
                              "baseline_cell_ids": [row["cell_id"] for row in baseline],
                              "candidate_cell_ids": [row["cell_id"] for row in candidate],
                              "baseline_repeats": len(baseline), "candidate_repeats": len(candidate),
                              "classification": label, "effects": effects})
    domain_path = campaign.get("search_domain_path")
    if campaign.get("domain") is not None:
        domain = campaign["domain"]
        domain_hash = _hash(domain)
    elif domain_path:
        path = Path(domain_path)
        root = Path(campaign.get("project_root", Path.cwd()))
        domain_file = path if path.is_absolute() else root / path
        domain = json.loads(domain_file.read_text())
        domain_hash = Domain.load(domain_file).digest
    else:
        domain = None
        domain_hash = _hash(None)
    plan_passed, plan_reasons, plan_checks = _plan_gate(campaign, events, cells, configs, domain_hash)
    backend = "mock" if any(row.get("diagnostics", {}).get("mock") for row in cells) else "real"
    sensitivity_qualified = plan_passed and backend == "real"
    core = {"version": "sensitivity-report-v1", "campaign_id": campaign_id,
            "campaign_hash": scientific_campaign_hash(campaign),
            "domain_hash": domain_hash, "backend": backend,
            "contrasts": contrasts, "excluded": excluded,
            "plan_checks": plan_checks, "plan_reasons": plan_reasons,
            "sensitivity_qualified": sensitivity_qualified,
            "qualification_reason": ("All predeclared pilot contrasts met the repeat, effect-separation and binding checks; source, traffic, semantic and tail qualification remain separate gates."
                                     if sensitivity_qualified else "; ".join(plan_reasons) or "backend is mock"),
            "limitations": ["Empirical replicate ranges are not confidence intervals.",
                            "Only exact matched scope is compared; no averaging across workloads or loads.",
                            "Short p99 screens cannot certify SLA tails or sustainable capacity."],
            "evidence_ids": [row["cell_id"] for row in cells]}
    core["report_id"] = "sens-" + _hash(core)[:20]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(core, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(output_path)
    return core

"""Conservative search qualification from immutable, scoped evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain import Domain, scientific_campaign_hash, sha
from .report import eligible


REQUIRED_FAMILIES = ("mixed", "session", "semantic")


def assess(campaign: dict[str, Any], domain: Domain, ledger: Any, registry: Any,
           artifact_root: Path, backend: str = "real",
           sensitivity_report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed. A real source-backed suite and repeated tails are required."""
    reasons: list[str] = []
    if backend != "real":
        reasons.append("mock_backend_not_qualifying")
    requirements = campaign.get("qualification_requirements", {})
    family_map = requirements.get("representative_scenarios", {})
    if not isinstance(family_map, dict):
        family_map = {}
    source_reports = requirements.get("source_report_paths", {})
    realization_reports = requirements.get("realization_report_paths", {})
    semantic_report = requirements.get("semantic_validation_report_path")
    provenance = True
    traffic = True
    evidence_ids: list[str] = []
    for family in REQUIRED_FAMILIES:
        scenario_id = family_map.get(family)
        if not scenario_id:
            reasons.append(f"representative_{family}_scenario_missing")
            provenance = traffic = False
            continue
        try:
            scenario = registry.load(scenario_id)
            if scenario.metadata["manifest"].get("suite_role") != "representative":
                reasons.append(f"{family}_scenario_not_representative")
                provenance = False
        except Exception as exc:
            reasons.append(f"{family}_scenario_unqualified:{type(exc).__name__}")
            provenance = traffic = False
            continue
        source_path = source_reports.get(family)
        if not _valid_report(source_path, expected_scenario=scenario_id):
            reasons.append(f"{family}_source_report_missing_or_unmatched")
            provenance = False
        else:
            evidence_ids.append(f"source:{family}:{scenario_id}")
        realization_path = realization_reports.get(family)
        if not _valid_report(realization_path, expected_scenario=scenario_id):
            reasons.append(f"{family}_traffic_realization_missing_or_unmatched")
            traffic = False
        else:
            evidence_ids.append(f"traffic:{family}:{scenario_id}")
    if not _valid_report(semantic_report):
        reasons.append("semantic_validation_missing")
        provenance = False
    else:
        evidence_ids.append("semantic_validation")
    cells = [event["payload"] for event in ledger.events(campaign["campaign_id"], "cell")]
    min_repeats = int(requirements.get("baseline_min_repeats", 3))
    min_eligible = int(requirements.get("baseline_min_eligible_per_scenario", 1000))
    baseline_ok = True
    for scenario_id in list(campaign["screen_scenario_ids"]) + list(family_map.values()):
        baseline = [row for row in cells if row.get("scenario_id") == scenario_id and
                    row.get("is_baseline") is True and row.get("measurement_protocol") ==
                    "fresh-server-cell-v1" and eligible(row)]
        n = sum(row.get("counts", {}).get("completed", 0) for row in baseline)
        if len(baseline) < min_repeats or n < min_eligible:
            reasons.append(f"baseline_repeats_or_tail_samples_insufficient:{scenario_id}")
            baseline_ok = False
    if baseline_ok:
        evidence_ids.append("baseline:repeated_matched")
    sensitivity_path = requirements.get("sensitivity_report_path") or str(artifact_root / "sensitivity-report.json")
    sensitivity = sensitivity_report or _read(sensitivity_path)
    sensitive = bool(sensitivity and sensitivity.get("sensitivity_qualified") is True and
                     sensitivity.get("backend") == "real" and
                     sensitivity.get("campaign_hash") == scientific_campaign_hash(campaign) and
                     sensitivity.get("domain_hash") == domain.digest)
    if not sensitive:
        reasons.append("reproducible_sensitivity_report_missing_or_unmatched")
    else:
        evidence_ids.append("sensitivity:repeated_effect")
    if not requirements.get("active_domain_capability_report_path") or not _valid_report(
            requirements.get("active_domain_capability_report_path")):
        reasons.append("active_domain_capability_report_missing")
        sensitive = False
    else:
        evidence_ids.append("active_domain_capabilities")
    allowed = backend == "real" and provenance and traffic and baseline_ok and sensitive and not reasons
    return {"schema_version": "qualification-v1", "backend": backend,
            "campaign_id": campaign["campaign_id"],
            "campaign_hash": scientific_campaign_hash(campaign), "domain_hash": domain.digest,
            "qualification_requirements_hash": sha(requirements),
            "provenance_validated": provenance, "traffic_validated": traffic,
            "baseline_characterized": baseline_ok, "sensitivity_qualified": sensitive,
            "search_allowed": allowed, "blocked_reasons": sorted(set(reasons)),
            "evidence_ids": evidence_ids, "source": "iar qualify", "report_root": str(artifact_root)}


def _read(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        raw = json.loads(Path(path).read_text())
        return raw if isinstance(raw, dict) else None
    except (OSError, ValueError):
        return None


def _valid_report(path: str | None, expected_scenario: str | None = None) -> bool:
    report = _read(path)
    return bool(report and report.get("backend") == "real" and report.get("status") in
                ("complete", "validated", "qualified") and report.get("evidence_ids") and
                (expected_scenario is None or report.get("scenario_id") == expected_scenario))

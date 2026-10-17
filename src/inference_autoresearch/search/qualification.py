"""Conservative search qualification from immutable, scoped evidence."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .domain import Domain, scientific_campaign_hash, sha
from .report import eligible


REQUIRED_FAMILIES = ("mixed", "session", "semantic")
FIXED_FOUR_MODE = "fixed-four-v1"
FIXED_FOUR_SCENARIOS = (
    "qwen-ops-chat-low-v1",
    "qwen-ops-agent-low-v1",
    "qwen-ops-document-reference-v1",
    "qwen-ops-mixed-reference-v1",
)


def assess(campaign: dict[str, Any], domain: Domain, ledger: Any, registry: Any,
           artifact_root: Path, backend: str = "real",
           sensitivity_report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed. A real source-backed suite and repeated tails are required."""
    if campaign.get("qualification_requirements", {}).get("mode") == FIXED_FOUR_MODE:
        return _assess_fixed_four(campaign, domain, ledger, registry, artifact_root, backend)
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


def _assess_fixed_four(campaign: dict[str, Any], domain: Domain, ledger: Any,
                       registry: Any, artifact_root: Path, backend: str) -> dict[str, Any]:
    """Exploratory four-task gate: validated inputs and one matched B0 per task.

    This grade deliberately makes no SLA, production, or sensitivity claim.
    The first agent proposal may be the first sensitivity experiment.
    """
    from .domain import config_identity

    requirements = campaign.get("qualification_requirements", {})
    reasons: list[str] = []
    evidence_ids: list[str] = []
    if backend != "real":
        reasons.append("mock_backend_not_qualifying")
    ids = campaign.get("screen_scenario_ids", [])
    suite_ok = (isinstance(ids, list) and len(ids) == 4 and
                set(ids) == set(FIXED_FOUR_SCENARIOS) and len(set(ids)) == 4)
    if not suite_ok:
        reasons.append("fixed_four_screen_suite_mismatch")
    if campaign.get("triage_scenario_id") is not None:
        reasons.append("fixed_four_triage_disallowed")
    if campaign.get("heldout_scenario_ids"):
        reasons.append("fixed_four_heldout_scenarios_disallowed")

    scenarios: dict[str, Any] = {}
    for scenario_id in FIXED_FOUR_SCENARIOS:
        try:
            scenario = registry.load(scenario_id)  # validated readiness and immutable asset checks
            manifest = scenario.metadata["manifest"]
            if (manifest.get("readiness") != "validated" or
                    manifest.get("traffic_mode") != "independent_open_loop"):
                raise ValueError("scenario is not a validated independent replay")
            report_hash = _frozen_validation_evidence(scenario, registry)
            scenarios[scenario_id] = scenario
            evidence_ids.append(f"scenario:{scenario_id}:{manifest['payload_sha256']}")
            evidence_ids.append(f"frozen_validation:{scenario_id}:{report_hash}")
        except (AttributeError, KeyError, OSError, ValueError, TypeError) as exc:
            reasons.append(f"screen_scenario_unqualified:{scenario_id}:{type(exc).__name__}")
    traffic_ok = suite_ok and len(scenarios) == 4

    baseline_ok = traffic_ok
    if traffic_ok and backend == "real":
        try:
            baseline_id = config_identity(campaign, campaign["baseline"])
            cells = [event["payload"] for event in ledger.events(campaign["campaign_id"], "cell")]
        except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
            reasons.append(f"baseline_evidence_unavailable:{type(exc).__name__}")
            baseline_ok = False
        else:
            for scenario_id in FIXED_FOUR_SCENARIOS:
                scenario = scenarios[scenario_id]
                matches = [row for row in cells if
                           row.get("scenario_id") == scenario_id and
                           row.get("config_id") == baseline_id and
                           row.get("is_baseline") is True and
                           row.get("stage") == "screen" and
                           row.get("measurement_protocol") == "fresh-server-cell-v1" and
                           row.get("offered_load") == scenario.offered_load and
                           row.get("load_unit") == scenario.load_unit and
                           row.get("cache_protocol") == scenario.cache_protocol and
                           row.get("counts", {}).get("planned") == scenario.expected_count and
                           not row.get("mock") and eligible(row)]
                if not matches:
                    reasons.append(f"eligible_matched_screen_b0_missing:{scenario_id}")
                    baseline_ok = False
                else:
                    evidence_ids.append(f"baseline_cell:{scenario_id}:{matches[-1]['cell_id']}")
    else:
        baseline_ok = False

    allowed = backend == "real" and traffic_ok and baseline_ok and not reasons
    return {"schema_version": "qualification-v1", "backend": backend,
            "campaign_id": campaign["campaign_id"],
            "campaign_hash": scientific_campaign_hash(campaign), "domain_hash": domain.digest,
            "qualification_requirements_hash": sha(requirements),
            "qualification_mode": FIXED_FOUR_MODE,
            "qualification_grade": "exploratory_four_task",
            "provenance_validated": traffic_ok, "traffic_validated": traffic_ok,
            "baseline_characterized": baseline_ok, "sensitivity_qualified": False,
            "search_allowed": allowed, "blocked_reasons": sorted(set(reasons)),
            "evidence_ids": evidence_ids, "source": "iar qualify", "report_root": str(artifact_root)}


def _frozen_validation_evidence(scenario: Any, registry: Any) -> str:
    """Require tracked independent replay proof tied to the exact frozen asset."""
    root = Path(registry.root).resolve()
    manifest = scenario.metadata["manifest"]

    def under_root(relative: str) -> Path:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("validation evidence path must be relative")
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("validation evidence path escapes registry root")
        return path

    card = json.loads(under_root(manifest["workload_card_path"]).read_text())
    report_path = under_root(card["validation_report_path"])
    report_bytes = report_path.read_bytes()
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    if report_hash != card["validation_report_sha256"]:
        raise ValueError("validation report hash differs from frozen card")
    report = json.loads(report_bytes)
    if report.get("schema_version") != "ops4-frozen-validation-v1":
        raise ValueError("wrong frozen validation schema")
    entry = report.get("scenarios", {}).get(scenario.scenario_id)
    if (not isinstance(entry, dict) or entry.get("status") != "validated" or
            entry.get("planned") != scenario.expected_count or
            entry.get("http_200") != scenario.expected_count or
            entry.get("payload_match") is not True or
            entry.get("output_caps_realized") is not True or
            entry.get("schedule_match") is not True or
            entry.get("asset_sha256") != manifest["payload_sha256"] or
            not entry.get("raw_sha256") or not entry.get("records_sha256")):
        raise ValueError("independent replay validation is absent or unmatched")
    return report_hash


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

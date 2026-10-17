"""Observed application-SLO checks over complete, class-labelled request records.

This module deliberately does not turn a short observed percentile into a
confidence bound or a confirmed capacity result. Confirmation is a separate
protocol decision over independent windows.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


class SLAContractError(ValueError):
    pass


_PERCENTILES = {"p50": 0.50, "p90": 0.90, "p95": 0.95, "p99": 0.99}


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def _binomial_cdf(k: int, n: int, probability: float) -> float:
    if probability <= 0:
        return 1.0
    if probability >= 1:
        return 0.0 if k < n else 1.0
    return sum(math.exp(math.lgamma(n + 1) - math.lgamma(j + 1)
                        - math.lgamma(n - j + 1) + j * math.log(probability)
                        + (n - j) * math.log1p(-probability))
               for j in range(k + 1))


def upper_violation_bound(violations: int, requests: int, confidence: float) -> float:
    """Exact one-sided binomial bound, conditional on independent requests."""
    if not (0 <= violations <= requests and requests > 0 and 0 < confidence < 1):
        raise SLAContractError("invalid violation count, request count, or confidence")
    if violations == requests:
        return 1.0
    lower, upper = 0.0, 1.0
    alpha = 1 - confidence
    for _ in range(65):
        middle = (lower + upper) / 2
        if _binomial_cdf(violations, requests, middle) > alpha:
            lower = middle
        else:
            upper = middle
    return (lower + upper) / 2


def validate_policy(policy: dict[str, Any]) -> None:
    """Require explicit, versioned deadlines; never infer them from B0."""
    if policy.get("schema_version") != "0.1" or not isinstance(policy.get("policy_id"), str) or not policy["policy_id"]:
        raise SLAContractError("SLA policy needs schema_version=0.1 and policy_id")
    confidence = policy.get("confidence_level")
    if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 < confidence < 1:
        raise SLAContractError("SLA policy needs confidence_level in (0, 1)")
    classes = policy.get("classes")
    if not isinstance(classes, dict) or not classes:
        raise SLAContractError("SLA policy needs at least one named request class")
    for name, spec in classes.items():
        if not isinstance(name, str) or not name or not isinstance(spec, dict):
            raise SLAContractError("invalid SLA class")
        if spec.get("percentile") not in _PERCENTILES:
            raise SLAContractError(f"{name}: unsupported percentile")
        for metric in ("ttft_ms", "tpot_ms"):
            value = spec.get(metric)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise SLAContractError(f"{name}: {metric} must be a positive deadline")
        errors = spec.get("max_error_fraction")
        if type(errors) not in (int, float) or not math.isfinite(errors) or not 0 <= errors <= 1:
            raise SLAContractError(f"{name}: max_error_fraction must be in [0, 1]")
        minimum = spec.get("min_eligible_requests")
        if type(minimum) is not int or minimum < 1:
            raise SLAContractError(f"{name}: min_eligible_requests must be positive")


def assess_observed_point(
    records: list[dict[str, Any]], policy: dict[str, Any],
    class_by_request_id: dict[str, str],
) -> dict[str, Any]:
    """Check one measured point, failing closed on absent or duplicate requests.

    ``class_by_request_id`` must come from the frozen workload manifest. The
    server's prompt-token count is not a substitute for an authoritative class
    label. The returned feasibility is observed only, not SLA certification.
    """
    validate_policy(policy)
    if not class_by_request_id or set(class_by_request_id.values()) != set(policy["classes"]):
        raise SLAContractError("policy classes must exactly match frozen workload classes")
    by_id: dict[str, dict[str, Any]] = {}
    for row in records:
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or request_id in by_id:
            raise SLAContractError("request records need distinct request IDs")
        by_id[request_id] = row
    if set(by_id) != set(class_by_request_id):
        raise SLAContractError("request records do not exactly match frozen workload IDs")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for request_id, name in class_by_request_id.items():
        groups[name].append(by_id[request_id])
    results: dict[str, Any] = {}
    for name, spec in policy["classes"].items():
        rows = groups[name]
        completed = [row for row in rows if row.get("terminal_state") == "completed"]
        ttfts = [float(row["ttft_ms"]) for row in completed
                 if type(row.get("ttft_ms")) in (int, float) and math.isfinite(row["ttft_ms"])]
        tpots = [float(row["tpot_ms"]) for row in completed
                 if type(row.get("tpot_ms")) in (int, float) and math.isfinite(row["tpot_ms"])]
        percentile = spec["percentile"]
        ttft = _percentile(ttfts, _PERCENTILES[percentile])
        tpot = _percentile(tpots, _PERCENTILES[percentile])
        error_fraction = (len(rows) - len(completed)) / len(rows)
        ttft_breaches = sum(row.get("terminal_state") != "completed"
                            or type(row.get("ttft_ms")) not in (int, float)
                            or not math.isfinite(row["ttft_ms"])
                            or row["ttft_ms"] > spec["ttft_ms"] for row in rows)
        tpot_breaches = sum(row.get("terminal_state") != "completed"
                            or type(row.get("tpot_ms")) not in (int, float)
                            or not math.isfinite(row["tpot_ms"])
                            or row["tpot_ms"] > spec["tpot_ms"] for row in rows)
        ttft_upper = upper_violation_bound(ttft_breaches, len(rows), policy["confidence_level"])
        tpot_upper = upper_violation_bound(tpot_breaches, len(rows), policy["confidence_level"])
        reasons = []
        if len(ttfts) < spec["min_eligible_requests"] or len(tpots) < spec["min_eligible_requests"]:
            reasons.append("insufficient_eligible_requests")
        if error_fraction > spec["max_error_fraction"]:
            reasons.append("error_fraction_exceeded")
        if ttft is not None and ttft > spec["ttft_ms"]:
            reasons.append("ttft_deadline_exceeded")
        if tpot is not None and tpot > spec["tpot_ms"]:
            reasons.append("tpot_deadline_exceeded")
        # A finite-sample percentile is a descriptive statistic. This extra
        # check asks whether the observed violation rate can support the
        # stated attainment fraction under an independent-request model.
        if ttft_upper > 1 - _PERCENTILES[percentile]:
            reasons.append("ttft_attainment_unconfirmed")
        if tpot_upper > 1 - _PERCENTILES[percentile]:
            reasons.append("tpot_attainment_unconfirmed")
        results[name] = {
            "planned": len(rows), "completed": len(completed),
            "ttft_eligible": len(ttfts), "tpot_eligible": len(tpots),
            "error_fraction": error_fraction, "percentile": percentile,
            "ttft_observed_ms": ttft, "tpot_observed_ms": tpot,
            "ttft_deadline_breaches": ttft_breaches,
            "tpot_deadline_breaches": tpot_breaches,
            "ttft_violation_upper_bound": ttft_upper,
            "tpot_violation_upper_bound": tpot_upper,
            "observed_feasible": not reasons, "reason_codes": reasons,
        }
    return {
        "policy_id": policy["policy_id"], "claim": "independent_request_point_only",
        "confidence_level": policy["confidence_level"],
        "observed_feasible": all(row["observed_feasible"] for row in results.values()),
        "classes": results,
    }

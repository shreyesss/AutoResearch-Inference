import pytest

from inference_autoresearch.evaluation.sla import (
    SLAContractError, assess_observed_point, upper_violation_bound, validate_policy,
)


def _policy():
    return {"schema_version": "0.1", "policy_id": "application-slo-v1",
            "confidence_level": 0.95,
            "classes": {"chat": {"percentile": "p90", "ttft_ms": 300,
                                 "tpot_ms": 50, "max_error_fraction": 0,
                                 "min_eligible_requests": 30}}}


def test_observed_sla_requires_complete_class_accounting_and_reports_denominators():
    rows = [{"request_id": "a", "terminal_state": "completed", "ttft_ms": 100,
             "tpot_ms": 30},
            {"request_id": "b", "terminal_state": "completed", "ttft_ms": 200,
             "tpot_ms": 40}]
    result = assess_observed_point(rows, _policy(), {"a": "chat", "b": "chat"})
    assert result["claim"] == "independent_request_point_only"
    assert result["observed_feasible"] is False
    assert "ttft_attainment_unconfirmed" in result["classes"]["chat"]["reason_codes"]
    assert result["classes"]["chat"]["ttft_observed_ms"] == pytest.approx(190)
    diagnostics = result["classes"]["chat"]["diagnostic_percentiles_ms"]
    assert diagnostics["ttft"]["p50"] == pytest.approx(150)
    assert diagnostics["ttft"]["p99"] == pytest.approx(199)
    assert diagnostics["tpot"]["p95"] == pytest.approx(39.5)
    assert result["classes"]["chat"]["ttft_eligible"] == 2
    with pytest.raises(SLAContractError, match="exactly match"):
        assess_observed_point(rows[:1], _policy(), {"a": "chat", "b": "chat"})


def test_observed_sla_fails_closed_on_errors_or_missing_metrics():
    rows = [{"request_id": "a", "terminal_state": "completed", "ttft_ms": 100,
             "tpot_ms": None},
            {"request_id": "b", "terminal_state": "failed", "ttft_ms": None,
             "tpot_ms": None}]
    result = assess_observed_point(rows, _policy(), {"a": "chat", "b": "chat"})
    assert result["observed_feasible"] is False
    assert set(result["classes"]["chat"]["reason_codes"]) == {
        "insufficient_eligible_requests", "error_fraction_exceeded",
        "ttft_attainment_unconfirmed", "tpot_attainment_unconfirmed"}


def test_policy_rejects_missing_or_invented_deadlines():
    policy = _policy()
    del policy["classes"]["chat"]["ttft_ms"]
    with pytest.raises(SLAContractError, match="positive deadline"):
        validate_policy(policy)


def test_exact_violation_bound_requires_enough_independent_requests():
    assert upper_violation_bound(0, 28, .95) > .10
    assert upper_violation_bound(0, 29, .95) < .10
    assert upper_violation_bound(1, 30, .95) > .10
    rows = [{"request_id": str(i), "terminal_state": "completed",
             "ttft_ms": 100, "tpot_ms": 30} for i in range(30)]
    result = assess_observed_point(rows, _policy(), {str(i): "chat" for i in range(30)})
    assert result["observed_feasible"] is True
    assert result["classes"]["chat"]["ttft_violation_upper_bound"] < .10

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from inference_autoresearch.search.rate_screen import (
    RateScreenError, _output_caps_realized, run_rate_screen, select_screen_rate,
)
from inference_autoresearch.contracts import CandidateProposal


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path, monkeypatch, *, feasible: bool = True):
    import inference_autoresearch.search.rate_screen as module

    policy_path = tmp_path / "configs/sla-policy-v3.json"
    policy_path.parent.mkdir()
    policy_path.write_text(json.dumps({"policy_id": "research-policy"}))
    payload = tmp_path / "configs/screen.jsonl"
    payload.write_text("frozen bodies\n")
    manifest_path = tmp_path / "configs/screen.json"
    manifest_path.write_text("{}")
    screen = SimpleNamespace(scenario_id="screen-36", expected_count=36,
                             path=manifest_path, metadata={"manifest": {}})
    monkeypatch.setattr(module, "verify_scenario", lambda *args, **kwargs: {"payload_path": payload})
    profile_dir = tmp_path / ".artifacts/autoresearch-codebase/run/sla-profile/r1/aiperf"
    profile_dir.mkdir(parents=True)
    native = {}
    for key in ("summary", "raw", "records"):
        path = profile_dir / f"{key}.txt"
        path.write_text(f"{key} evidence")
        native[key] = {"path": str(path), "sha256": _sha(path)}
    points = []
    for rate, passes in ((.1, feasible), (.2, feasible), (.4, False)):
        points.append({"rate_rps": rate, "arrival_seed": 42 + round(rate * 1_000_000),
                       "screen": {"status": "valid", "artifacts": native},
                       "qualified": {"status": "valid", "assessment": {
                           "policy_id": "research-policy", "observed_feasible": passes}}})
    profile_path = profile_dir / "sla-profile-points.json"
    profile_path.write_text(json.dumps({
        "schema_version": "sla-profile-points-v1", "capacity_confirmed": False,
        "screen_scenario_id": "screen-36", "policy_id": "research-policy",
        "policy_sha256": _sha(policy_path),
        "spec": {"seed": 42, "client_concurrency_cap": 256}, "points": points}))
    study = {"policy": {"path": "configs/sla-policy-v3.json", "sha256": _sha(policy_path)},
             "baseline_adaptive_run_paths": [{
                 "source_path": str(profile_path.relative_to(tmp_path)),
                 "source_sha256": _sha(profile_path)}]}
    return study, screen, profile_path, native


def test_selects_highest_valid_feasible_b0_rate_and_pins_inputs(tmp_path, monkeypatch):
    study, screen, _, native = _fixture(tmp_path, monkeypatch)
    lock = select_screen_rate(study, tmp_path, screen)
    assert lock["selected_rate_rps"] == .2
    assert lock["arrival_seed"] == 200042
    assert lock["selection_reason"] == "highest_observed_feasible_b0_rate"
    assert lock["screen_payload_sha256"] == _sha(tmp_path / "configs/screen.jsonl")
    assert lock["b0_profile_screen_artifacts"] == native
    assert lock["exact_arrival_pairing"] is False


def test_baseline_infeasible_uses_lowest_valid_rate_with_no_capacity_claim(tmp_path, monkeypatch):
    study, screen, _, _ = _fixture(tmp_path, monkeypatch, feasible=False)
    lock = select_screen_rate(study, tmp_path, screen)
    assert lock["selected_rate_rps"] == .1
    assert lock["selection_reason"] == "lowest_valid_b0_rate_baseline_infeasible_exploration"
    assert lock["capacity_confirmed"] is False


def test_changed_b0_evidence_blocks_rate_screen(tmp_path, monkeypatch):
    study, screen, profile, native = _fixture(tmp_path, monkeypatch)
    profile.write_text(profile.read_text() + " ")
    with pytest.raises(RateScreenError, match="missing or changed"):
        select_screen_rate(study, tmp_path, screen)
    study["baseline_adaptive_run_paths"][0]["source_sha256"] = _sha(profile)
    Path(native["raw"]["path"]).write_text("changed")
    with pytest.raises(RateScreenError, match="artifact is missing or changed"):
        select_screen_rate(study, tmp_path, screen)


def test_short_screen_rejects_output_cap_mismatch():
    raw = [{"metadata": {"x_request_id": "r1"},
            "payload": {"max_completion_tokens": 256}}]
    measured = [{"metadata": {"x_request_id": "r1"},
                 "metrics": {"usage_completion_tokens": {"value": 255}}}]
    assert not _output_caps_realized(raw, measured)
    measured[0]["metrics"]["usage_completion_tokens"]["value"] = 256
    assert _output_caps_realized(raw, measured)


def test_candidate_server_start_failure_is_recorded_and_does_not_abort(tmp_path, monkeypatch):
    import inference_autoresearch.search.rate_screen as module

    manifest = tmp_path / "screen.json"
    payload = tmp_path / "screen.jsonl"
    profile = tmp_path / "profile.json"
    for path in (manifest, payload, profile):
        path.write_text("frozen")
    screen = SimpleNamespace(scenario_id="screen-36", expected_count=36,
                             path=manifest, cache_protocol="cold_stream",
                             metadata={"asset": str(payload), "registry_root": str(tmp_path)})
    rate_lock = {"schema_version": "rate-screen-lock-v1",
                 "screen_scenario_id": screen.scenario_id,
                 "screen_manifest_sha256": _sha(manifest),
                 "screen_payload_sha256": _sha(payload),
                 "source_profile_path": profile.name,
                 "source_profile_sha256": _sha(profile),
                 "selected_rate_rps": 0.2, "arrival_seed": 200042,
                 "client_concurrency_cap": 256,
                 "claim": "rate_matched_stochastic_36_request_triage_only"}
    @dataclass
    class Resolved:
        config_id: str = "candidate-id"
    monkeypatch.setattr(module, "resolve_config", lambda *_: Resolved())
    class FailingRuntime:
        def start(self, *_):
            raise RuntimeError("server exited before readiness")
    class Ledger:
        def __init__(self):
            self.rows = []
        def append(self, *args):
            self.rows.append(args)
    ledger = Ledger()
    engine = SimpleNamespace(
        _pinned=lambda: None, _domain=lambda: None, runtime=FailingRuntime(),
        benchmark=SimpleNamespace(preflight_tokenizer=lambda *_: None))
    candidate = CandidateProposal("candidate-1", {"max_num_seqs": 64},
                                  "exploration", "Startup may fail")
    result = run_rate_screen(engine, candidate, screen, rate_lock, ledger,
                             "campaign", tmp_path / "evaluations")
    assert result.status == "failed"
    assert len(result.cell_ids) == 1
    cell = json.loads(next((tmp_path / "evaluations").glob("*/cell-*/cell-result.json")).read_text())
    assert cell["status"] == "measurement_failed"
    assert cell["counts"]["not_dispatched"] == 36
    assert cell["reason_codes"] == ["screen_exception_RuntimeError"]
    assert ledger.rows[0][1] == "cell"

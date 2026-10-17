import json
from pathlib import Path

from inference_autoresearch.contracts import CandidateProposal, CellResult, ScenarioManifest, ServerHandle
from inference_autoresearch.evaluation.engine import EvaluationEngine, classify_behavior
from inference_autoresearch.runtime.config import BASELINE, PINNED_IMAGE, PINNED_MODEL_REVISION


class FakeRuntime:
    def __init__(self):
        self.started = []
        self.stopped = []

    def start(self, config, output_dir):
        output_dir.mkdir(parents=True)
        handle = ServerHandle("fake-server", "http://127.0.0.1:8000", config.config_id)
        self.started.append(handle)
        return handle

    def stop(self, handle):
        self.stopped.append(handle)


class FakeBenchmark:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.policies = []

    def prepare(self, server, scenario, output_dir):
        output_dir.mkdir()
        receipt = {"server_id": server.server_id, "scenario_id": scenario.scenario_id}
        (output_dir / "preparation-receipt.json").write_text(json.dumps(receipt))
        return receipt

    def run_cell(self, server, scenario, policy, output_dir):
        assert Path(policy.metadata["preparation_receipt"]).is_file()
        self.policies.append(policy)
        if self.fail:
            raise RuntimeError("benchmark failed")
        return CellResult("cell-1", scenario.scenario_id, server.config_id, "valid",
                          counts={"planned": 2, "dispatched": 2, "not_dispatched": 0,
                                  "completed": 2, "failed": 0, "timed_out": 0, "canceled": 0,
                                  "censored": 0, "tpot_eligible": 2, "successful_completion_tokens": 512},
                          metrics={"output_tokens_per_s": 100., "ttft_p50_ms": 180.,
                                   "ttft_p99_ms": 210., "tpot_p50_ms": 50.,
                                   "tpot_p99_ms": 55., "dispatch_lag_p99_ms": 2.},
                          diagnostics={"server_gauges": {"queue_max": 0},
                                       "windows": {"dispatch_duration_s": 1., "drain_duration_s": 1.}})


def campaign(tmp_path):
    return {"campaign_id": "fake", "backend": "mock", "project_root": str(tmp_path),
            "model": {"id": "Qwen/Qwen3.8-27B", "revision": PINNED_MODEL_REVISION,
                      "local_path": "model", "max_model_len": 40960,
                      "tensor_parallel_size": 1, "dtype": "bfloat16"},
            "runtime": {"image": PINNED_IMAGE,
                        "gpu_uuid": "GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83"},
            "baseline": BASELINE | {"reasoning_parser": "qwen3"},
            "domain": {key: [value] for key, value in BASELINE.items()}}


def test_cleanup_and_accounting_in_fake_path(tmp_path):
    scenario = ScenarioManifest("short", expected_count=2)
    runtime = FakeRuntime()
    engine = EvaluationEngine(campaign(tmp_path), {"short": scenario}, runtime,
                              FakeBenchmark(), tmp_path / "runs", None)
    result = engine.evaluate(CandidateProposal("p0", {}), ["short"], "pilot")
    assert result.status == "valid"
    assert len(runtime.started) == len(runtime.stopped) == 1
    assert json.loads((Path(result.artifacts["directory"]) / "cell-01-short" / "controller-validation.json").read_text())["frontier_eligible"]
    timings = json.loads(Path(result.artifacts["timings"]).read_text())
    assert timings["protocol_id"] == "fresh-server-cell-v1"
    assert timings["cells"][0]["status"] == "completed"
    assert all(name in timings["cells"][0]["phases"] for name in
               ("server_start_s", "warmup_s", "benchmark_s", "result_processing_s", "server_stop_s"))


def test_engine_writes_truthful_requested_observation_receipt(tmp_path):
    scenario = ScenarioManifest("short", expected_count=2)
    engine = EvaluationEngine(campaign(tmp_path), {"short": scenario}, FakeRuntime(),
                              FakeBenchmark(), tmp_path / "runs", None)
    proposal = CandidateProposal("p1", {}, requested_observations=[
        "resolved_config", "token_budget_summary", "targeted_profile"])
    result = engine.evaluate(proposal, ["short"], "pilot")
    receipt = json.loads((Path(result.artifacts["directory"]) / "cell-01-short" /
                          "observation-receipt.json").read_text())
    assert receipt["observations"]["resolved_config"]["status"] == "available"
    assert receipt["observations"]["token_budget_summary"]["status"] == "partial"
    assert receipt["observations"]["targeted_profile"]["status"] == "not_executed"


def test_failure_still_stops_server(tmp_path):
    runtime = FakeRuntime()
    engine = EvaluationEngine(campaign(tmp_path), {"short": ScenarioManifest("short", expected_count=2)},
                              runtime, FakeBenchmark(fail=True), tmp_path / "runs", None)
    result = engine.evaluate(CandidateProposal("p0", {}), ["short"], "pilot")
    assert result.status == "failed" and "benchmark failed" in result.failure_reasons[0]
    assert len(runtime.stopped) == 1
    timings = json.loads(Path(result.artifacts["timings"]).read_text())
    assert timings["cells"][0]["status"] == "failed"
    assert "benchmark_s" in timings["cells"][0]["phases"]
    assert "server_stop_s" in timings["cells"][0]["phases"]


def test_triage_is_separate_stage_and_protocol(tmp_path):
    scenario = ScenarioManifest("short", expected_count=2)
    real_campaign = campaign(tmp_path) | {"backend": "real"}
    benchmark = FakeBenchmark()
    benchmark.preflight_tokenizer = lambda manifest: None
    engine = EvaluationEngine(real_campaign, {"short": scenario}, FakeRuntime(),
                              benchmark, tmp_path / "runs", None)
    result = engine.evaluate(CandidateProposal("p1", {}), ["short"], "triage")
    output = Path(result.artifacts["directory"])
    assert result.stage == "triage"
    assert result.artifacts["protocol_id"] == "fresh-server-triage-v1"
    assert json.loads((output / "evaluation-policy.json").read_text())["stage"] == "triage"
    assert json.loads((output / "evaluation-timings.json").read_text())["protocol_id"] == "fresh-server-triage-v1"
    status = json.loads((output / "cell-01-short" / "wire-export-status.json").read_text())
    assert status["status"] == "unavailable_for_triage"
    assert not (output / "cell-01-short" / "cell-result-v02.json").exists()


def test_behavior_requires_queue_evidence():
    cell = CellResult("c", "s", "cfg", "valid", counts={},
                      metrics={"dispatch_lag_p99_ms": 1}, diagnostics={"server_gauges": {"queue_max": None}})
    assert classify_behavior(cell).behavior == "unknown"


def test_bounded_transient_queue_admits_cold_mixed_but_not_backlog():
    cell = CellResult("c", "mixed", "cfg", "valid", counts={},
                      metrics={"dispatch_lag_p99_ms": 1.08},
                      diagnostics={"server_gauges": {"queue_max": 2},
                                   "windows": {"dispatch_duration_s": 362.19,
                                               "drain_duration_s": 23.63}})
    accepted = classify_behavior(cell)
    assert accepted.behavior == "normal"
    assert accepted.diagnostics["behavior_admission"] == "bounded_transient_queue"
    document = CellResult("c3", "document", "cfg", "valid", counts={},
                          metrics={"dispatch_lag_p99_ms": 1.12},
                          diagnostics={"server_gauges": {"queue_max": 3},
                                       "windows": {"dispatch_duration_s": 354.07,
                                                   "drain_duration_s": 27.49}})
    assert classify_behavior(document).behavior == "normal"
    backlog = CellResult("c2", "mixed", "cfg", "valid", counts={},
                         metrics={"dispatch_lag_p99_ms": 1.08},
                         diagnostics={"server_gauges": {"queue_max": 2},
                                      "windows": {"dispatch_duration_s": 181.10,
                                                  "drain_duration_s": 30.70}})
    assert classify_behavior(backlog).behavior == "unknown"
    excessive_queue = CellResult("c4", "mixed", "cfg", "valid", counts={},
                                 metrics={"dispatch_lag_p99_ms": 1.08},
                                 diagnostics={"server_gauges": {"queue_max": 4},
                                              "windows": {"dispatch_duration_s": 362.19,
                                                          "drain_duration_s": 23.63}})
    assert classify_behavior(excessive_queue).behavior == "unknown"


def test_long_frozen_schedule_gets_full_window_and_recorded_limits(tmp_path):
    scenario = ScenarioManifest("ops", expected_count=2,
                                metadata={"schedule_duration_s": 121.23})
    benchmark = FakeBenchmark()
    engine = EvaluationEngine(campaign(tmp_path), {"ops": scenario}, FakeRuntime(),
                              benchmark, tmp_path / "runs", None)
    result = engine.evaluate(CandidateProposal("p0", {}), ["ops"], "pilot")
    assert result.status == "valid"
    policy = benchmark.policies[0]
    assert policy.metadata["benchmark_duration_s"] == 132
    assert policy.metadata["benchmark_grace_period_s"] == 122
    assert policy.deadline_s == 284
    recorded = json.loads((Path(result.artifacts["directory"]) / "evaluation-policy.json").read_text())
    assert recorded["measurement_limits_by_scenario"]["ops"] == {
        "schedule_duration_s": 121.23, "benchmark_duration_s": 132.0,
        "benchmark_grace_period_s": 122.0, "deadline_s": 284.0,
    }


def test_short_schedule_retains_existing_limits(tmp_path):
    benchmark = FakeBenchmark()
    engine = EvaluationEngine(campaign(tmp_path),
                              {"short": ScenarioManifest("short", expected_count=2,
                                                         metadata={"schedule_duration_s": 59.765625})},
                              FakeRuntime(), benchmark, tmp_path / "runs", None)
    result = engine.evaluate(CandidateProposal("p0", {}), ["short"], "pilot")
    assert result.status == "valid"
    policy = benchmark.policies[0]
    assert policy.metadata["benchmark_duration_s"] == 70
    assert policy.metadata["benchmark_grace_period_s"] == 60
    assert policy.deadline_s == 180

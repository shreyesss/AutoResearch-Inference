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

    def prepare(self, server, scenario, output_dir):
        output_dir.mkdir()
        receipt = {"server_id": server.server_id, "scenario_id": scenario.scenario_id}
        (output_dir / "preparation-receipt.json").write_text(json.dumps(receipt))
        return receipt

    def run_cell(self, server, scenario, policy, output_dir):
        assert Path(policy.metadata["preparation_receipt"]).is_file()
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

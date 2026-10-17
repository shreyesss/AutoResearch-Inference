import json
from pathlib import Path

import pytest

from inference_autoresearch.benchmark.adaptive import (
    AdaptiveLoadSpec, _classify_trial, build_adaptive_argv, normalize_search_history,
)
from inference_autoresearch.benchmark.aiperf import AIPerfAdapter
from inference_autoresearch.contracts import ServerHandle
from inference_autoresearch.workloads.registry import ScenarioRegistry, WorkloadError, verify_scenario


def _spec():
    return AdaptiveLoadSpec(request_count=36, repeats=2, iterations=3,
                            min_rate_rps=.08, max_rate_rps=.2)


def test_adaptive_argv_uses_frozen_corpus_and_constant_count(monkeypatch):
    scenario = ScenarioRegistry(Path("configs/workloads/ops4-registry.json")).load(
        "qwen-ops-mixed-reference-v1")
    adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"))
    monkeypatch.setattr(adapter, "_ensure_offline_snapshot", lambda manifest: None)
    server = ServerHandle(server_id="b0", base_url="http://127.0.0.1:8000", config_id="b0")
    argv = build_adaptive_argv(adapter, server, scenario, _spec(), Path("/tmp/adaptive"))
    assert argv[argv.index("--request-count") + 1] == "36"
    assert argv[argv.index("--num-profile-runs") + 1] == "2"
    assert argv[argv.index("--search-space") + 1] == "rate:0.08,0.2:real"
    assert "--no-fixed-schedule" in argv
    assert "--fixed-schedule" not in argv
    assert argv[argv.index("--dataset-sampling-strategy") + 1] == "sequential"
    with pytest.raises(WorkloadError, match="full frozen corpus"):
        AdaptiveLoadSpec(request_count=12, repeats=1, iterations=2,
                         min_rate_rps=.08, max_rate_rps=.2).validate(scenario)


def test_known_twelve_request_smoke_is_rejected_by_dispatch_accounting(tmp_path):
    import shutil

    source = Path(".artifacts/aiperf-adaptive-ops4-spike")
    if not source.is_dir():
        pytest.skip("Saved AIPerf smoke unavailable")
    # Normalize the actual saved native exports without touching the GPU.
    shutil.copy2(source / "search_history.json", tmp_path / "search_history.json")
    for index in range(2):
        original = source / f"search_iter_{index:04d}" / "profile_runs" / "run_0001"
        target = tmp_path / f"search_iter_{index:04d}" / "profile_runs" / "run_0001"
        target.mkdir(parents=True)
        for name in ("profile_export_aiperf.json", "profile_export_raw.jsonl", "profile_export.jsonl"):
            shutil.copy2(original / name, target / name)
    result = normalize_search_history(tmp_path, config_id="b0", scenario_id="chat-smoke",
        spec=AdaptiveLoadSpec(request_count=12, repeats=1, iterations=2,
                              min_rate_rps=1.8, max_rate_rps=2.6,
                              benchmark_duration_s=70))
    assert len(result["points"]) == 2
    assert all(point["status"] == "invalid" for point in result["points"])
    assert "client_dispatch_shortfall" in result["points"][0]["reason_codes"]
    assert Path(result["native_history"]).is_file()


def test_missing_trial_remains_visible(tmp_path):
    history = {"config": {"max_iterations": 2,
                          "search_space": [{"path": "phases.profiling.rate",
                                            "lo": .08, "hi": .2}]},
               "iterations": [{"iteration_idx": 0,
               "variation_values": {"phases.profiling.rate": .1},
               "objective_values": [], "feasible": False}]}
    (tmp_path / "search_history.json").write_text(json.dumps(history))
    result = normalize_search_history(tmp_path, config_id="b0", scenario_id="mixed",
        spec=AdaptiveLoadSpec(request_count=36, repeats=1, iterations=2,
                              min_rate_rps=.08, max_rate_rps=.2))
    point = result["points"][0]
    assert point["status"] == "invalid"
    assert "missing_native_export" in point["reason_codes"]
    assert point["counts"]["planned"] == 36


def test_exact_mixed_corpus_classification_detects_missing_content():
    scenario = ScenarioRegistry(Path("configs/workloads/ops4-registry.json")).load(
        "qwen-ops-mixed-reference-v1")
    planned = verify_scenario(scenario.metadata["manifest"],
                              root=Path(scenario.metadata["registry_root"]))["planned"]
    raw = [{"metadata": {"x_request_id": str(index)},
            "payload": {"messages": [{"role": "user", "content": row["text"]}],
                        "max_completion_tokens": row["output_length"]}}
           for index, row in enumerate(planned)]
    measured = [{"metadata": {"x_request_id": str(index)},
                 "metrics": {"time_to_first_token": {"value": 100 + index},
                             "inter_token_latency": {"value": 50},
                             "request_latency": {"value": 1000}}}
                for index in range(len(planned))]
    matched, classes = _classify_trial(raw, measured, planned)
    assert matched
    assert {name: entry["n_dispatched"] for name, entry in classes.items()} == {
        "chat_shape": 17, "agent_shape": 8, "document_shape": 5, "code_shape": 6}
    assert classes["chat_shape"]["ttft_eligible"] == 17
    assert not _classify_trial(raw[:-1], measured[:-1], planned)[0]

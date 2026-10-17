import json
from dataclasses import replace
from pathlib import Path

import pytest

from inference_autoresearch.benchmark.aiperf import AIPerfAdapter
from inference_autoresearch.benchmark.sla_profiler import (
    SLAProfileSpec, assess_rate_trial, build_rate_argv, next_rate,
    profile_stop_reason,
)
from inference_autoresearch.contracts import ServerHandle
from inference_autoresearch.workloads.registry import ScenarioRegistry


def _screen():
    return ScenarioRegistry(Path("configs/workloads/ops4-registry.json")).load(
        "qwen-ops-mixed-reference-v1")


def _point(rate, feasible, status="valid"):
    return {"rate_rps": rate, "screen": {"status": "valid"},
            "qualified": {"status": status, "observed_feasible": feasible}}


def test_boundary_planner_expands_and_bisects_but_stops_on_invalid():
    spec = SLAProfileSpec(initial_rate_rps=.2, max_rate_rps=1.6)
    assert next_rate([], spec) == .2
    assert next_rate([_point(.2, True)], spec) == .4
    assert next_rate([_point(.2, True), _point(.4, False)], spec) == .3
    assert next_rate([_point(.2, True), _point(.4, False), _point(.3, True)], spec) == .35
    assert next_rate([_point(.2, False)], spec) == .1
    assert next_rate([_point(.2, False), _point(.1, False)], spec) is None
    assert profile_stop_reason([_point(.2, False), _point(.1, False)], spec) == "baseline_infeasible_or_lower_bound_reached"
    assert next_rate([_point(.2, True, "invalid")], spec) is None
    assert next_rate([{"rate_rps": .2, "screen": {"status": "invalid"},
                       "qualified": None}], spec) is None


def test_aiperf_rate_argv_keeps_exact_corpus_and_poisson_seed(monkeypatch, tmp_path):
    scenario = _screen()
    adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"))
    monkeypatch.setattr(adapter, "_ensure_offline_snapshot", lambda manifest: None)
    server = ServerHandle(server_id="b0", base_url="http://127.0.0.1:8000", config_id="b0")
    argv = build_rate_argv(adapter, server, scenario, rate=.2,
                           spec=SLAProfileSpec(), output_dir=tmp_path)
    assert argv[argv.index("--request-count") + 1] == "36"
    assert argv[argv.index("--arrival-pattern") + 1] == "poisson"
    assert argv[argv.index("--request-rate") + 1] == "0.2"
    assert argv[argv.index("--random-seed") + 1] == "200042"
    assert "--no-fixed-schedule" in argv
    assert argv[argv.index("--dataset-sampling-strategy") + 1] == "sequential"


def test_rate_trial_uses_exact_class_labels_and_fails_on_invalid_dispatch(monkeypatch, tmp_path):
    planned = [{"session_id": name, "text": f"unique {name}",
                "output_length": cap}
               for name, cap in (("chat", 256), ("agent", 1024),
                                 ("code", 1024), ("document", 512))]
    classes = {row["session_id"]: row["session_id"] for row in planned}
    scenario = replace(_screen(), scenario_id="qualified-four-test",
                       expected_count=4, metadata={"manifest": {"dummy": True},
                                                   "registry_root": str(tmp_path)})
    asset = tmp_path / "asset.jsonl"
    asset.write_text("\n".join(json.dumps(row) for row in planned) + "\n")
    monkeypatch.setattr("inference_autoresearch.benchmark.sla_profiler.verify_scenario",
                        lambda *args, **kwargs: {"planned": planned,
                                                  "payload_path": asset,
                                                  "request_classes": classes})
    summary = {"is_complete": True,
               "input_config": {"phases": [{"name": "profiling", "requests": 4,
                                            "type": "poisson", "rate": .2,
                                            "concurrency": 256}],
                                "datasets": [{"type": "file", "path": str(asset)}]},
               "credit_to_start_latency": {"p99": 1},
               "request_throughput": {"avg": .2},
               "output_token_throughput": {"avg": 100}}
    (tmp_path / "profile_export_aiperf.json").write_text(json.dumps(summary))
    raw = []
    measured = []
    for index, row in enumerate(planned):
        native_id = str(index)
        raw.append({"metadata": {"x_request_id": native_id}, "status": 200,
                    "start_perf_ns": 1_000_000_000 + index * 5_000_000_000,
                    "payload": {"messages": [{"role": "user", "content": row["text"]}],
                                "max_completion_tokens": row["output_length"]}})
        measured.append({"metadata": {"x_request_id": native_id},
                         "metrics": {"time_to_first_token": {"value": 100, "unit": "ms"},
                                     "inter_token_latency": {"value": 40, "unit": "ms"}}})
    raw_path = tmp_path / "profile_export_raw.jsonl"
    measured_path = tmp_path / "profile_export.jsonl"
    raw_path.write_text("\n".join(json.dumps(row) for row in raw) + "\n")
    measured_path.write_text("\n".join(json.dumps(row) for row in measured) + "\n")
    policy = {"schema_version": "0.1", "policy_id": "test", "confidence_level": .01,
              "classes": {name: {"percentile": "p90", "ttft_ms": 150,
                                 "tpot_ms": 70, "max_error_fraction": 0,
                                 "min_eligible_requests": 1} for name in classes}}
    result = assess_rate_trial(tmp_path, scenario, policy, rate=.2,
                               process_exit_code=0, spec=SLAProfileSpec())
    assert result["status"] == "valid"
    assert result["assessment"]["classes"]["code"]["planned"] == 1
    assert result["observed_feasible"]
    summary["credit_to_start_latency"]["p99"] = 21
    (tmp_path / "profile_export_aiperf.json").write_text(json.dumps(summary))
    invalid = assess_rate_trial(tmp_path, scenario, policy, rate=.2,
                                process_exit_code=0, spec=SLAProfileSpec())
    assert invalid["status"] == "invalid"
    assert not invalid["observed_feasible"]
    assert "client_dispatch_lag" in invalid["reason_codes"]


def test_sla_profiler_cli_has_qualified_entrypoint():
    from inference_autoresearch.cli import build_parser

    args = build_parser().parse_args(["sla-profile", "--backend", "real",
                                      "--campaign", "configs/campaign-v2.json",
                                      "--max-points", "3"])
    assert args.command == "sla-profile" and args.max_points == 3

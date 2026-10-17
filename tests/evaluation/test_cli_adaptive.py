import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from inference_autoresearch import cli
from inference_autoresearch.contracts import ResolvedServeConfig, ServerHandle
from inference_autoresearch.search.domain import Domain
from inference_autoresearch.storage import Ledger
from inference_autoresearch.workloads.registry import ScenarioRegistry


class FakeRuntime:
    def __init__(self):
        self.started = []
        self.stopped = []

    def start(self, config, output_dir):
        self.started.append(config)
        output_dir.mkdir(parents=True)
        return ServerHandle(server_id="server-one", base_url="http://127.0.0.1:8000",
                            config_id=config.config_id)

    def stop(self, handle):
        self.stopped.append(handle)


class FakeBenchmark:
    def preflight_tokenizer(self, scenario):
        return {"loaded": True}

    def prepare(self, handle, scenario, output_dir):
        output_dir.mkdir(parents=True)
        receipt = {"version": "preparation-receipt-v1", "server_id": handle.server_id,
                   "config_id": handle.config_id, "scenario_id": scenario.scenario_id}
        (output_dir / "preparation-receipt.json").write_text(json.dumps(receipt))
        return receipt


def _inputs(tmp_path):
    campaign_path = Path("configs/campaign-v2.json").resolve()
    campaign = json.loads(campaign_path.read_text())
    domain = Domain.load(Path("configs/search-domain-v2.json"))
    registry = ScenarioRegistry(Path("configs/workloads/ops4-registry.json"))
    artifact_root = tmp_path / "real"
    ledger = Ledger(artifact_root / "ledger.sqlite3")
    return campaign_path, campaign, domain, registry, artifact_root, ledger


def _fake_engine(runtime):
    return SimpleNamespace(runtime=runtime, benchmark=FakeBenchmark(),
                           _pinned=lambda: object(), _domain=lambda: {})


def test_adaptive_cli_records_all_points_and_stops_server(monkeypatch, tmp_path):
    campaign_path, campaign, domain, registry, artifact_root, ledger = _inputs(tmp_path)
    runtime = FakeRuntime()
    monkeypatch.setattr(cli, "_engine", lambda *args: _fake_engine(runtime))
    monkeypatch.setattr("inference_autoresearch.runtime.config.resolve_config",
                        lambda parameters, pinned, values: ResolvedServeConfig(
                            config_id="candidate" if parameters else "b0"))

    def fake_adaptive(handle, scenario, spec, output_dir, adapter, *, preparation_receipt):
        assert preparation_receipt.is_file()
        assert spec.request_count == 36 and spec.repeats == 2
        output_dir.mkdir(parents=True)
        (output_dir / "normalized-search-points.json").write_text('{"points":[]}')
        (output_dir / "search_history.json").write_text('{}')
        return {"protocol_id": "ops-mixed-v2-adaptive-exploration", "process_exit_code": 0,
                "points": [{"status": "valid", "configured_rate": .1},
                           {"status": "valid", "configured_rate": .15},
                           {"status": "invalid", "configured_rate": .2}],
                "report_artifacts": {}}

    monkeypatch.setattr("inference_autoresearch.benchmark.adaptive.run_adaptive", fake_adaptive)
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"parameters": {"max_num_batched_tokens": 4096}}))
    args = argparse.Namespace(backend="real", candidate=str(candidate))
    result = cli._run_adaptive_pilot(args, campaign, campaign_path, domain, registry,
                                     artifact_root, ledger)
    assert result["config_id"] == "candidate"
    assert result["point_count"] == 3 and result["valid_trial_count"] == 2
    assert result["valid_rate_count"] == 2
    assert len(runtime.started) == len(runtime.stopped) == 1
    cell = ledger.events(campaign["campaign_id"], "cell")[0]["payload"]
    assert cell["stage"] == "capacity" and cell["status"] == "exploratory"
    assert Path(cell["artifacts"]["normalized_search_points"]).is_file()


def test_adaptive_cli_failure_still_stops_server(monkeypatch, tmp_path):
    campaign_path, campaign, domain, registry, artifact_root, ledger = _inputs(tmp_path)
    runtime = FakeRuntime()
    monkeypatch.setattr(cli, "_engine", lambda *args: _fake_engine(runtime))
    monkeypatch.setattr("inference_autoresearch.runtime.config.resolve_config",
                        lambda *args: ResolvedServeConfig(config_id="b0"))
    monkeypatch.setattr("inference_autoresearch.benchmark.adaptive.run_adaptive",
                        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("AIPerf failed")))
    args = argparse.Namespace(backend="real", candidate=None)
    with pytest.raises(RuntimeError, match="AIPerf failed"):
        cli._run_adaptive_pilot(args, campaign, campaign_path, domain, registry,
                                artifact_root, ledger)
    assert len(runtime.started) == len(runtime.stopped) == 1
    assert ledger.events(campaign["campaign_id"], "adaptive_study")[0]["payload"]["status"] == "failed"


def test_adaptive_parser_exposes_candidate_override():
    args = cli.build_parser().parse_args(["adaptive", "--campaign", "configs/campaign-v2.json",
                                           "--backend", "real", "--candidate", "candidate.json"])
    assert args.command == "adaptive" and args.candidate == "candidate.json"


def test_adaptive_cli_cleanup_failure_is_recorded(monkeypatch, tmp_path):
    campaign_path, campaign, domain, registry, artifact_root, ledger = _inputs(tmp_path)
    runtime = FakeRuntime()
    runtime.stop = lambda handle: (_ for _ in ()).throw(RuntimeError("stop failed"))
    monkeypatch.setattr(cli, "_engine", lambda *args: _fake_engine(runtime))
    monkeypatch.setattr("inference_autoresearch.runtime.config.resolve_config",
                        lambda *args: ResolvedServeConfig(config_id="b0"))
    monkeypatch.setattr("inference_autoresearch.benchmark.adaptive.run_adaptive",
                        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("measure failed")))
    with pytest.raises(RuntimeError, match="measure failed"):
        cli._run_adaptive_pilot(argparse.Namespace(backend="real", candidate=None), campaign,
                                campaign_path, domain, registry, artifact_root, ledger)
    final = ledger.events(campaign["campaign_id"], "adaptive_transition")[-1]["payload"]
    assert final["state"] == "cleanup_failed" and final["cleanup_error"] == "stop failed"

import hashlib
import json
from pathlib import Path

import pytest

from inference_autoresearch.search.controller import SearchGateError, qualification_ok
from inference_autoresearch.search.domain import Domain, config_identity, scientific_campaign_hash
from inference_autoresearch.search.report import export, pareto_front
from inference_autoresearch.storage import Ledger


ROOT = Path(__file__).resolve().parents[2]


def test_domain_includes_baseline_and_excludes_unqualified_axes():
    campaign = json.loads((ROOT / "configs/campaign.json").read_text())
    domain = Domain.load(ROOT / "configs/search-domain.json")
    effective = domain.effective(campaign["baseline"], {})
    assert effective["max_num_seqs"] == 512
    assert config_identity(campaign, effective) == config_identity(campaign,
        domain.effective(campaign["baseline"], {"max_num_seqs": 512}))
    for axis, spec in domain.raw["parameters"].items():
        if spec.get("active") is False:
            with pytest.raises(ValueError, match="capability qualification"):
                domain.validate({axis: spec["values"][0]})
            assert axis not in domain.proposal_schema()["properties"]["parameters"]["properties"]


def test_real_search_gate_refuses_draft_even_when_mock_allowed():
    path = ROOT / "configs/campaign.json"
    campaign = json.loads(path.read_text())
    domain = Domain.load(ROOT / "configs/search-domain.json")
    with pytest.raises(SearchGateError, match="qualification"):
        qualification_ok(campaign, domain, path, "real")
    assert qualification_ok(campaign, domain, path, "mock")["label"] == "mock_only"
    amended = dict(campaign, status="qualified", real_search_qualification_path="some-report.json")
    assert scientific_campaign_hash(amended) == scientific_campaign_hash(campaign)


def test_ledger_immutable_identity_and_append_only_failures(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite3")
    assert ledger.claim("c", "proposal", "p1", "digest-1", {"status": "valid"})
    assert not ledger.claim("c", "proposal", "p1", "digest-1", {"status": "valid"})
    with pytest.raises(ValueError, match="changed"):
        ledger.claim("c", "proposal", "p1", "digest-2", {"status": "changed"})
    ledger.append("c", "evaluation", "failed", {"status": "failed"})
    assert len(ledger.events("c")) == 2


def test_front_only_clean_compatible_cells_and_failed_counts(tmp_path):
    def row(cid, throughput, ttft, tpot, *, status="valid", scenario="same"):
        return {"cell_id": cid, "scenario_id": scenario, "config_id": cid, "stage": "pilot",
                "offered_load": 3.2, "load_unit": "requests_per_s", "cache_protocol": "cold_stream",
                "measurement_protocol": "fresh-server-cell-v1", "status": status, "behavior": "normal",
                "counts": {"planned": 100, "dispatched": 100, "completed": 100,
                           "not_dispatched": 0, "failed": 0, "timed_out": 0,
                           "canceled": 0, "censored": 0},
                "metrics": {"output_tokens_per_s": throughput, "ttft_p99_ms": ttft,
                            "tpot_p99_ms": tpot}}
    rows = [row("b0", 100, 200, 60), row("tradeoff", 110, 220, 45),
            row("dominated", 90, 230, 65), row("failed", 200, 100, 20, status="functional_failed")]
    assert {r["cell_id"] for r in pareto_front(rows)} == {"b0", "tradeoff"}
    paths = export(rows + [row("other", 500, 1, 1, scenario="other")], tmp_path)
    fronts = json.loads(Path(paths["fronts_json"]).read_text())
    assert len(fronts) == 2
    summary = json.loads(Path(paths["summary_json"]).read_text())
    assert summary["status_counts"]["functional_failed"] == 1


def test_cli_failed_evaluation_returns_nonzero(monkeypatch, capsys):
    from inference_autoresearch import cli
    monkeypatch.setattr(cli, "run", lambda args: {"status": "failed", "failure_reasons": ["startup_oom"]})
    assert cli.main(["baseline", "--backend", "mock"]) == 2
    assert "startup_oom" in capsys.readouterr().out


def test_codex_driver_keeps_event_stream_separate_from_validated_proposal(tmp_path):
    from inference_autoresearch.contracts import ProposalContext
    from inference_autoresearch.search.proposer import CodexProposer
    fake = tmp_path / "codex"
    domain = Domain.load(ROOT / "configs/search-domain.json")
    strict_params = {name: None for name in domain.codex_output_schema()["properties"]["parameters"]["properties"]}
    strict_params["max_num_seqs"] = 128
    payload = {"schema_version": "0.2", "proposal_id": "p1",
               "parent_configuration_ids": [], "parameters": strict_params,
               "hypothesis": "Test cap headroom", "expected_tradeoff": "May queue",
               "evidence_ids": [], "experiment_kind": "hypothesis",
               "predictions": [{"observation": "queue", "expected_change": "increase",
                                "scope": "short-chat 3.2"}],
               "falsification_condition": "Queue remains zero", "requested_observations": []}
    fake.write_text("#!/usr/bin/env python3\n"
        "import json,sys,pathlib\n"
        "if sys.argv[1:] == ['--version']: print('codex-cli 0.test'); sys.exit(0)\n"
        "if sys.argv[1:] == ['login','status']: print('Logged in'); sys.exit(0)\n"
        "args=sys.argv[1:]; p=pathlib.Path(args[args.index('--output-last-message')+1]); "
        f"p.write_text({json.dumps(json.dumps(payload))}); print('{{\"type\":\"event\"}}')\n")
    fake.chmod(0o755)
    context = ProposalContext("c", "test", domain.raw, {}, [], [], [], {"distinct_proposals": 1},
                              {"search_allowed": True})
    proposal = CodexProposer(domain, tmp_path / "artifacts", cli=str(fake),
                              skill_path=ROOT / "agent/SKILL.md",
                              expected_version="0.test").propose(context)
    assert proposal.parameters == {"max_num_seqs": 128}
    attempt = tmp_path / "artifacts/proposals/attempt-0001"
    assert json.loads((attempt / "codex.events.jsonl").read_text())["type"] == "event"
    assert json.loads((attempt / "proposal.final.json").read_text())["proposal_id"] == "p1"
    receipt = json.loads((attempt / "proposer-receipt.json").read_text())
    normalized = attempt / "proposal.normalized.json"
    assert receipt["status"] == "validated"
    assert receipt["normalized_proposal_path"] == str(normalized)
    assert receipt["normalized_proposal_sha256"] == hashlib.sha256(normalized.read_bytes()).hexdigest()
    assert json.loads(normalized.read_text())["parameters"] == {"max_num_seqs": 128}


def test_codex_strict_schema_requires_all_typed_keys_and_normalizes_nulls():
    from jsonschema import Draft202012Validator
    from inference_autoresearch.search.proposer import parse_codex_output, ProposerError
    domain = Domain.load(ROOT / "configs/search-domain.json")
    schema = domain.codex_output_schema()
    assert schema["required"] == list(schema["properties"])
    params = schema["properties"]["parameters"]
    assert params["required"] == list(params["properties"])
    assert all("type" in field and "null" in field["type"] for field in params["properties"].values())
    assert all("type" in field for field in schema["properties"].values())
    raw = {"schema_version": "0.2", "proposal_id": "p2",
           "parent_configuration_ids": [], "parameters": {key: None for key in params["properties"]},
           "hypothesis": "One axis probe", "expected_tradeoff": "Unknown",
           "evidence_ids": [], "experiment_kind": "exploration",
           "predictions": [{"observation": "queue", "expected_change": "flat", "scope": "short chat"}],
           "falsification_condition": "Queue changes", "requested_observations": []}
    raw["parameters"]["max_num_seqs"] = 128
    Draft202012Validator.check_schema(schema)
    assert parse_codex_output(raw, domain, set()).parameters == {"max_num_seqs": 128}
    del raw["parameters"]["max_num_seqs"]
    with pytest.raises(ProposerError, match="schema violation"):
        parse_codex_output(raw, domain, set())


def test_cell_wire_export_validates_handoff_schema_without_invented_counters(tmp_path):
    from inference_autoresearch.contracts import CellResult, MeasurementPolicy, ScenarioManifest
    from inference_autoresearch.contracts_wire import export_cell_result
    cell = CellResult("run:scenario:1", "scenario", "cfg-1", "valid", behavior="normal",
        counts={"planned": 2, "dispatched": 2, "not_dispatched": 0, "completed": 2,
                "failed": 0, "timed_out": 0, "canceled": 0, "censored": 0,
                "tpot_eligible": 2, "successful_completion_tokens": 512},
        metrics={"output_tokens_per_s": 100, "ttft_p50_ms": 150, "ttft_p99_ms": 200,
                 "tpot_p50_ms": 20, "tpot_p99_ms": 30,
                 "scheduled_ttft_p99_ms": 201, "dispatch_lag_p99_ms": 1},
        diagnostics={"windows": {"dispatch_duration_s": 2, "drain_duration_s": 3,
                                   "effective_duration_s": 5}, "server_gauges": {"queue_max": 0},
                     "token_counting_mode": "server_usage"},
        artifacts={"raw_requests": "requests.jsonl", "aiperf_export": "profile.json"})
    scenario = ScenarioManifest("scenario", group_id="short-chat")
    policy = MeasurementPolicy("pilot", metadata={"run_id": "run", "protocol_id": "fresh-server-cell-v1"})
    path = export_cell_result(cell, scenario, policy, tmp_path, tmp_path / "cell-result-v02.json",
                               ROOT / "inference-autoresearch-handoff/contracts/cell-result.schema.json")
    exported = json.loads(path.read_text())
    assert exported["configuration_id"] == "cfg-1"
    assert exported["diagnostics"]["achieved_cache_hit_fraction"] is None
    assert exported["mechanism_evidence"][0]["value"] == 0

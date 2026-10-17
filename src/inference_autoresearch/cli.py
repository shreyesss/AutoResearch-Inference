"""Trusted campaign entrypoint. Proposal authority is separate from GPU authority."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal
from inference_autoresearch.search.controller import SearchController, qualification_ok
from inference_autoresearch.search.domain import Domain, scientific_campaign_hash, sha
from inference_autoresearch.search.evidence import EvidenceStore
from inference_autoresearch.search.mock import MockEvaluator
from inference_autoresearch.search.proposer import CodexProposer, MockProposer, parse_proposal
from inference_autoresearch.search.qualification import assess
from inference_autoresearch.search.report import export, export_history
from inference_autoresearch.storage import Ledger
from inference_autoresearch.storage.inspection import write_inspection
from inference_autoresearch.workloads.registry import ScenarioRegistry


def _file(path: str, campaign_path: Path) -> Path:
    given = Path(path)
    if given.is_absolute():
        return given
    project_root = campaign_path.parent.parent if campaign_path.parent.name == "configs" else campaign_path.parent
    candidates = [project_root / given, campaign_path.parent / given]
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def _load_campaign(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text())
    required = ("schema_version", "campaign_id", "model", "runtime", "baseline",
                "search_domain_path", "workload_registry", "screen_scenario_ids", "search_budget")
    if any(key not in raw for key in required):
        raise ValueError(f"campaign missing keys: {[k for k in required if k not in raw]}")
    if raw["schema_version"] != "0.1":
        raise ValueError("campaign schema version not supported")
    proposer = raw.get("proposer", {})
    if not isinstance(proposer, dict) or (proposer and not isinstance(proposer.get("model"), str)):
        raise ValueError("campaign proposer must declare a model ID")
    if proposer and proposer.get("web_search") not in ("disabled", "cached", "indexed", "live"):
        raise ValueError("campaign proposer must declare a supported web-search mode")
    return raw


def _lock(campaign: dict[str, Any], domain: Domain, root: Path) -> None:
    lock = {"campaign_hash": scientific_campaign_hash(campaign), "domain_hash": domain.digest,
            "campaign_id": campaign["campaign_id"]}
    root.mkdir(parents=True, exist_ok=True)
    path = root / "campaign.lock.json"
    if path.exists():
        previous = json.loads(path.read_text())
        legacy = {"campaign_hash": sha(campaign), "domain_hash": domain.digest,
                  "campaign_id": campaign["campaign_id"]}
        legacy_before_pilot_requirements = {
            "campaign_hash": sha({k: v for k, v in campaign.items() if k != "qualification_requirements"}),
            "domain_hash": domain.digest, "campaign_id": campaign["campaign_id"]}
        if previous in (legacy, legacy_before_pilot_requirements):
            migration = {"from": previous, "to": lock,
                         "reason": "Operational qualification path/plan added; frozen measurement fields unchanged"}
            (root / "campaign-lock-migration.json").write_text(json.dumps(migration, indent=2) + "\n")
            path.write_text(json.dumps(lock, indent=2) + "\n")
        elif previous != lock:
            raise ValueError("frozen campaign/domain changed; create a new campaign ID and output directory")
    else:
        path.write_text(json.dumps(lock, indent=2) + "\n")


def _candidate(path: Path, domain: Domain) -> CandidateProposal:
    raw = json.loads(path.read_text())
    if "schema_version" in raw:
        return parse_proposal(raw, domain, set(raw.get("evidence_ids", [])))
    if "parameters" not in raw:
        raise ValueError("candidate needs parameters")
    domain.validate(raw["parameters"])
    return CandidateProposal(proposal_id=raw.get("proposal_id", path.stem),
                             parameters=raw["parameters"], hypothesis=raw.get("hypothesis", "manual pilot"),
                             experiment_kind="exploration", expected_tradeoff=raw.get("expected_tradeoff", "unknown"),
                             predictions=raw.get("predictions", [{"observation": "primary metrics",
                               "expected_change": "unknown", "scope": "pilot"}]),
                             falsification_condition=raw.get("falsification_condition", "no measured effect"))


def _lock_pilot_plan(campaign: dict[str, Any], campaign_path: Path, ledger: Ledger,
                     backend: str, domain: Domain, candidate: CandidateProposal,
                     scenario_ids: list[str]) -> None:
    """Freeze a declared contrast before any real candidate pilot cell."""
    if backend == "mock":
        return
    plan_ref = campaign.get("qualification_requirements", {}).get("pilot_plan_path")
    if not plan_ref:
        raise ValueError("real pilot needs a predeclared pilot_plan_path")
    plan_path = _file(plan_ref, campaign_path)
    plan = json.loads(plan_path.read_text())
    if plan.get("campaign_id") != campaign["campaign_id"]:
        raise ValueError("pilot plan campaign ID differs")
    if plan.get("domain_hash") != domain.digest or plan.get("protocol_id") != "fresh-server-cell-v1":
        raise ValueError("pilot plan domain/protocol differs from frozen campaign")
    matching = [contrast for contrast in plan.get("contrasts", []) if
                contrast.get("candidate_overrides") == candidate.parameters and
                set(contrast.get("scenario_ids", [])) == set(scenario_ids)]
    if not matching:
        raise ValueError("real pilot candidate/scenarios are not a predeclared contrast")
    existing = ledger.events(campaign["campaign_id"], "cell")
    locks = ledger.events(campaign["campaign_id"], "pilot_plan_locked")
    if not locks and any(row["payload"].get("stage") == "pilot" and
                            not row["payload"].get("is_baseline") for row in existing):
        raise ValueError("candidate pilot cells predate a locked plan; version the campaign")
    measured = sum(1 for row in existing if row["payload"].get("stage") == "pilot")
    if measured + len(scenario_ids) > int(plan.get("budget", {}).get("max_pilot_cells", 0)):
        raise ValueError("pilot plan cell budget exhausted")
    from inference_autoresearch.evaluation.sensitivity import lock_pilot_plan
    lock_pilot_plan(campaign | {"project_root": str(campaign_path.parent.parent)}, ledger)


def _engine(backend: str, campaign: dict[str, Any], domain: Domain,
            registry: ScenarioRegistry, artifact_root: Path, ledger: Ledger, campaign_path: Path):
    if backend == "mock":
        return MockEvaluator(campaign, registry, domain, artifact_root, ledger)
    from inference_autoresearch.benchmark.aiperf import AIPerfAdapter
    from inference_autoresearch.evaluation.engine import EvaluationEngine
    from inference_autoresearch.runtime.config import PinnedEnvironment
    from inference_autoresearch.runtime.docker import DockerRuntimeManager
    model, runtime = campaign["model"], campaign["runtime"]
    pinned = PinnedEnvironment(model_dir=_file(model["local_path"], campaign_path).resolve(),
                               image=runtime["image"], model_name=model["id"],
                               model_revision=model["revision"], max_model_len=model["max_model_len"],
                               tensor_parallel_size=model["tensor_parallel_size"], dtype=model["dtype"],
                               gpu_uuid=runtime["gpu_uuid"])
    frozen = dict(campaign)
    frozen["domain"] = {key: spec["values"] for key, spec in domain.raw["parameters"].items()
                        if spec.get("active") is not False}
    frozen["model_dir"] = str(pinned.model_dir)
    project_root = campaign_path.parent.parent if campaign_path.parent.name == "configs" else campaign_path.parent
    lock_path = Path(os.environ.get("IAR_GPU_LOCK_PATH",
                    str(project_root / ".artifacts" / "gpu-locks" / f"{runtime['gpu_uuid']}.lock")))
    manager = DockerRuntimeManager(pinned, lock_path)
    aiperf_binary = Path(shutil.which("aiperf") or _file(".venv/bin/aiperf", campaign_path))
    benchmark = AIPerfAdapter(aiperf_executable=aiperf_binary,
                              tokenizer_path=pinned.model_dir,
                              tokenizer_cache_dir=project_root / ".artifacts" / "aiperf-hf-cache")
    return EvaluationEngine(frozen, registry, manager, benchmark, artifact_root, ledger)


def _print(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="iar", description="Pinned Qwen serving experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("doctor", "characterize", "prepare", "baseline", "pilot", "evaluate", "adaptive",
                    "sla-profile",
                    "assess-adaptive-sla",
                    "qualify", "search", "report", "inspect"):
        item = sub.add_parser(command)
        item.add_argument("--campaign", default="configs/campaign.json")
        item.add_argument("--backend", choices=("mock", "real"), default="mock")
        item.add_argument("--output-dir", default=".artifacts/autoresearch-codebase")
        if command in ("pilot", "evaluate"):
            item.add_argument("--candidate")
        if command == "adaptive":
            item.add_argument("--candidate", help="Optional typed v2 serving override; omitted uses B0.")
        if command == "sla-profile":
            item.add_argument("--study", default="configs/sla-study-v3.template.json")
            item.add_argument("--candidate", help="Optional typed serving override; omitted uses B0.")
            item.add_argument("--initial-rate-rps", type=float, default=0.2)
            item.add_argument("--min-rate-rps", type=float, default=0.1)
            item.add_argument("--max-rate-rps", type=float, default=1.6)
            item.add_argument("--max-points", type=int, default=6)
        if command == "assess-adaptive-sla":
            item.add_argument("--policy", required=True, help="Explicit versioned application SLA policy JSON.")
            item.add_argument("--adaptive-run", required=True,
                              help="Existing adaptive run directory (or its aiperf subdirectory).")
            item.add_argument("--scenario", required=True, help="Frozen registry scenario ID.")
            item.add_argument("--assessment-output", help="Optional output JSON path.")
        if command in ("baseline", "pilot", "evaluate"):
            item.add_argument("--scenario", action="append", dest="scenarios",
                              help="Evaluator registry ID; may be repeated. Defaults to campaign screens.")
        if command == "baseline":
            item.add_argument("--stage", choices=("pilot", "screen", "triage"), default=None,
                              help="Use screen for a matched search baseline; defaults to screen in fixed-four-v1.")
        if command == "evaluate":
            item.add_argument("--stage", choices=("pilot", "screen", "expanded", "confirm"), default="pilot")
        if command == "search":
            item.add_argument("--max-proposals", type=int)
            item.add_argument("--resume", action="store_true")
            item.add_argument("--proposer", choices=("codex", "mock", "optuna"))
            item.add_argument("--skill", default="agent/SKILL.md")
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    campaign_path = Path(args.campaign).resolve()
    campaign = _load_campaign(campaign_path)
    project_root = campaign_path.parent.parent if campaign_path.parent.name == "configs" else campaign_path.parent
    domain = Domain.load(_file(campaign["search_domain_path"], campaign_path))
    registry = ScenarioRegistry(_file(campaign["workload_registry"], campaign_path), root=project_root)
    if args.command == "assess-adaptive-sla":
        return _run_adaptive_sla_assessment(args, registry)
    artifact_root = Path(args.output_dir).resolve() / campaign["campaign_id"] / args.backend
    if args.command == "inspect" and not (artifact_root / "ledger.sqlite3").is_file():
        raise ValueError(f"no campaign ledger to inspect: {artifact_root / 'ledger.sqlite3'}")
    ledger = Ledger(artifact_root / "ledger.sqlite3")
    command = args.command
    if command == "inspect":
        return write_inspection(ledger, campaign["campaign_id"], artifact_root, args.backend)
    if command == "doctor":
        result: dict[str, Any] = {"campaign_id": campaign["campaign_id"], "backend": args.backend,
                 "campaign_hash": scientific_campaign_hash(campaign), "domain_hash": domain.digest,
                 "scenarios": registry.list(), "codex_cli": shutil.which("codex"),
                 "proposer_config": campaign.get("proposer"),
                 "aiperf": shutil.which("aiperf") or str(project_root / ".venv/bin/aiperf")}
        if args.backend == "real":
            engine = _engine("real", campaign, domain, registry, artifact_root, ledger, campaign_path)
            screen_ids = campaign.get("screen_scenario_ids", [])
            if not screen_ids:
                raise ValueError("campaign has no frozen screen scenarios for tokenizer preflight")
            result["tokenizer_preflight"] = engine.benchmark.preflight_tokenizer(registry.load(screen_ids[0]))
            result["hardware"] = engine.runtime.inspect_hardware()
            aiperf_path = Path(shutil.which("aiperf") or _file(".venv/bin/aiperf", campaign_path))
            version = subprocess.run([str(aiperf_path), "--version"], capture_output=True,
                                     text=True, timeout=15, check=False)
            if version.returncode or version.stdout.strip() != campaign["runtime"]["aiperf_version"]:
                raise ValueError("AIPerf version differs from campaign pin")
            result["aiperf_version"] = version.stdout.strip()
            codex = shutil.which("codex")
            if not codex:
                result["codex_status"] = "unavailable"
            else:
                seen = subprocess.run([codex, "--version"], capture_output=True,
                                      text=True, timeout=15, check=False)
                result["codex_status"] = "available" if seen.returncode == 0 else "unavailable"
                result["codex_version"] = seen.stdout.strip() if seen.returncode == 0 else None
                expected_codex = campaign["runtime"].get("codex_cli_version_observed")
                if seen.returncode == 0 and expected_codex and expected_codex not in seen.stdout:
                    raise ValueError("Codex CLI version differs from observed campaign pin")
                auth = subprocess.run([codex, "login", "status"], capture_output=True,
                                      text=True, timeout=15, check=False)
                result["codex_auth_status"] = "ready" if auth.returncode == 0 else "unavailable"
        else:
            result["status"] = "mock_preflight_only"
        return result
    if command in ("characterize", "prepare"):
        items = []
        for scenario_id in registry.list():
            try:
                scenario = registry.load(scenario_id, require_validated=False)
                readiness = scenario.metadata["manifest"].get("readiness")
                items.append({"scenario_id": scenario_id, "expected_count": scenario.expected_count,
                              "offered_load": scenario.offered_load, "manifest": str(scenario.path),
                              "role": scenario.metadata["manifest"].get("suite_role"),
                              "readiness": readiness,
                              "evaluator_ready": readiness == "validated" and
                                 scenario.traffic_mode == "independent_open_loop" and
                                 scenario.history_mode == "single_turn"})
            except Exception as exc:
                items.append({"scenario_id": scenario_id, "readiness": "blocked",
                              "evaluator_ready": False, "reason": f"{type(exc).__name__}: {exc}"})
        status = ("screen_assets_verified" if command == "prepare" and
                  all(item.get("evaluator_ready") for item in items if item["scenario_id"] in
                      campaign["screen_scenario_ids"]) else
                  "registered_source_inventory_only" if command == "characterize" else "screen_assets_blocked")
        result = {"status": status, "backend": args.backend, "scenarios": items,
                  "note": "See each scenario readiness and validation report for exact evaluator eligibility."}
        artifact_root.mkdir(parents=True, exist_ok=True)
        (artifact_root / f"{command}.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    if command == "report":
        rows = [event["payload"] for event in ledger.events(campaign["campaign_id"], "cell")]
        report_dir = artifact_root / "report"
        suite_ids = (campaign["screen_scenario_ids"] if
                     campaign.get("qualification_requirements", {}).get("mode") == "fixed-four-v1"
                     else None)
        artifacts = export(rows, report_dir, screen_scenario_ids=suite_ids)
        artifacts.update(export_history(ledger, campaign["campaign_id"], report_dir))
        return {"campaign_id": campaign["campaign_id"], "backend": args.backend,
                "cells": len(rows), "artifacts": artifacts}
    if command == "qualify":
        from inference_autoresearch.evaluation.sensitivity import build_sensitivity_report
        sensitivity_path = artifact_root / "sensitivity-report.json"
        sensitivity = build_sensitivity_report(campaign | {"project_root": str(project_root)},
                                               ledger, sensitivity_path)
        qualification = assess(campaign, domain, ledger, registry, artifact_root,
                               backend=args.backend, sensitivity_report=sensitivity)
        artifact_root.mkdir(parents=True, exist_ok=True)
        path = artifact_root / "qualification-report.json"
        path.write_text(json.dumps(qualification, indent=2, sort_keys=True) + "\n")
        return qualification | {"artifact_path": str(path), "sensitivity_path": str(sensitivity_path)}
    _lock(campaign, domain, artifact_root)
    if command == "search":
        qualification_ok(campaign, domain, campaign_path, args.backend,
                         ledger, registry, artifact_root)
        mode = args.proposer or ("codex" if args.backend == "real" else "mock")
        if args.backend == "real" and mode == "mock":
            raise ValueError("real autonomous search cannot use mock proposer")
        proposer_config = campaign.get("proposer", {})
        if mode == "mock":
            proposer = MockProposer(domain)
        elif mode == "optuna":
            from inference_autoresearch.search.optimizer import OptunaProposer
            proposer = OptunaProposer(campaign, domain, artifact_root, ledger, args.backend)
        else:
            proposer = CodexProposer(domain, artifact_root,
                     timeout_s=int(campaign["search_budget"].get("proposal_timeout_seconds", 180)),
                     skill_path=_file(args.skill, campaign_path),
                     expected_version=campaign["runtime"].get("codex_cli_version_observed"),
                     model=proposer_config.get("model"),
                     reasoning_effort=proposer_config.get("reasoning_effort"),
                     web_search=proposer_config.get("web_search", "disabled"))
        evidence_sources = campaign.get("evidence_sources")
        if evidence_sources is not None and (not isinstance(evidence_sources, dict)
                                             or not all(isinstance(k, str) and isinstance(v, str)
                                                        for k, v in evidence_sources.items())):
            raise ValueError("campaign evidence_sources must map evidence IDs to repository paths")
        evidence = EvidenceStore(project_root, artifact_root / "evidence",
                                 sources=evidence_sources).snapshot()
        engine = _engine(args.backend, campaign, domain, registry, artifact_root, ledger, campaign_path)
        controller = SearchController(campaign, campaign_path, domain, proposer, engine,
                                      ledger, artifact_root, args.backend, evidence)
        return asdict(controller.run(max_proposals=args.max_proposals, resume=args.resume))
    if command == "adaptive":
        return _run_adaptive_pilot(args, campaign, campaign_path, domain, registry,
                                   artifact_root, ledger)
    if command == "sla-profile":
        return _run_sla_profile(args, campaign, campaign_path, domain, registry,
                                artifact_root, ledger, project_root)
    engine = _engine(args.backend, campaign, domain, registry, artifact_root, ledger, campaign_path)
    scenario_ids = args.scenarios or campaign["screen_scenario_ids"]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("scenario IDs must be distinct")
    if command == "baseline":
        mode = campaign.get("qualification_requirements", {}).get("mode")
        stage = args.stage or ("triage" if mode == "fast-gate-v2" else
                               "screen" if mode == "fixed-four-v1" else "pilot")
        candidate = CandidateProposal(proposal_id="B0", parameters={}, experiment_kind="exploration",
                    hypothesis="Measure frozen resolved stock performance baseline",
                    expected_tradeoff="reference", predictions=[{"observation": "primary metrics",
                     "expected_change": "reference", "scope": "frozen campaign screen"}],
                    falsification_condition="request accounting or environment pin fails")
        result = engine.evaluate(candidate, scenario_ids, stage)
        return asdict(result) | {"backend": args.backend, "baseline": True}
    if command in ("evaluate", "pilot"):
        if args.candidate:
            candidate = _candidate(Path(args.candidate), domain)
        elif command == "pilot":
            candidate = CandidateProposal(proposal_id="pilot-mtp1", parameters={"mtp_draft_tokens": 1},
                 hypothesis="Speculation may improve decode at a TTFT cost", experiment_kind="hypothesis",
                 expected_tradeoff="decode versus TTFT", predictions=[{"observation": "TPOT",
                   "expected_change": "decrease", "scope": "short-chat fixed loads"}],
                 falsification_condition="No repeatable decode effect or semantic failure")
        else:
            raise ValueError("evaluate requires --candidate")
        domain.validate(candidate.parameters)
        stage = "pilot" if command == "pilot" else args.stage
        if stage == "pilot":
            _lock_pilot_plan(campaign, campaign_path, ledger, args.backend,
                             domain, candidate, scenario_ids)
        result = engine.evaluate(candidate, scenario_ids, stage)
        return asdict(result) | {"backend": args.backend}
    raise ValueError(f"unknown command {command}")


def _run_adaptive_pilot(args: argparse.Namespace, campaign: dict[str, Any],
                        campaign_path: Path, domain: Domain, registry: ScenarioRegistry,
                        artifact_root: Path, ledger: Ledger) -> dict[str, Any]:
    """Exploratory rate curve on one fresh pinned server; never an SLA claim."""
    if args.backend != "real" or campaign.get("qualification_requirements", {}).get("mode") != "fast-gate-v2":
        raise ValueError("iar adaptive requires the real fast-gate-v2 campaign")
    from inference_autoresearch.benchmark.adaptive import AdaptiveLoadSpec, run_adaptive
    from inference_autoresearch.evaluation.protocol_v2 import load_protocol, stage_invocation
    from inference_autoresearch.runtime.config import resolve_config

    protocol = load_protocol(_file(campaign["evaluation_protocol_path"], campaign_path), registry)
    stage = stage_invocation(protocol, "adaptive_exploration")
    scenario = registry.load(stage["scenario_id"])
    spec = AdaptiveLoadSpec.from_protocol(protocol)
    spec.validate(scenario)
    candidate = _candidate(Path(args.candidate), domain) if args.candidate else CandidateProposal(
        proposal_id="B0-adaptive", parameters={}, experiment_kind="exploration",
        hypothesis="Measure the exploratory B0 offered-rate curve")
    domain.validate(candidate.parameters)
    engine = _engine("real", campaign, domain, registry, artifact_root, ledger, campaign_path)
    engine.benchmark.preflight_tokenizer(scenario)
    resolved = resolve_config(candidate.parameters, engine._pinned(), engine._domain())
    run_id = "adaptive-" + uuid.uuid4().hex
    run_dir = artifact_root / "adaptive" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "proposal.json").write_text(json.dumps(asdict(candidate), indent=2, sort_keys=True) + "\n")
    (run_dir / "resolved-config.json").write_text(json.dumps(asdict(resolved), indent=2,
                                                           sort_keys=True, default=str) + "\n")
    (run_dir / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    ledger.append(campaign["campaign_id"], "adaptive_transition", run_id,
                  {"state": "validated", "config_id": resolved.config_id,
                   "scenario_id": scenario.scenario_id, "claim": "exploratory_load_curve_only"})
    started = time.monotonic()
    handle = None
    result: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None
    try:
        handle = engine.runtime.start(resolved, run_dir / "server")
        ledger.append(campaign["campaign_id"], "adaptive_transition", run_id,
                      {"state": "warming", "server_id": handle.server_id})
        engine.benchmark.prepare(handle, scenario, run_dir / "warmup")
        ledger.append(campaign["campaign_id"], "adaptive_transition", run_id,
                      {"state": "measuring", "sample_count_per_trial": spec.request_count,
                       "repeats_per_iteration": spec.repeats, "max_iterations": spec.iterations})
        result = run_adaptive(handle, scenario, spec, run_dir / "aiperf", engine.benchmark,
                              preparation_receipt=run_dir / "warmup" / "preparation-receipt.json")
        artifacts = {"normalized_search_points": str(run_dir / "aiperf" / "normalized-search-points.json"),
                     "native_search_history": str(run_dir / "aiperf" / "search_history.json"),
                     "aiperf_console": str(run_dir / "aiperf" / "aiperf-console.log"),
                     "server": str(run_dir / "server"),
                     **result.get("report_artifacts", {})}
        valid_trial_count = sum(row["status"] == "valid" for row in result["points"])
        valid_rate_count = len({row.get("configured_rate") for row in result["points"]
                                if row["status"] == "valid" and row.get("configured_rate") is not None})
        study_status = ("exploratory" if result["process_exit_code"] == 0 and valid_rate_count >= 2
                        else "invalid")
        cell = {"cell_id": run_id, "scenario_id": scenario.scenario_id,
                "config_id": resolved.config_id, "stage": "capacity",
                "status": study_status, "behavior": "unknown", "evidence_grade": "exploratory",
                "measurement_protocol": result["protocol_id"],
                "claim": "exploratory_load_curve_only", "is_baseline": not candidate.parameters,
                "counts": {}, "metrics": {}, "artifacts": artifacts,
                "reason_codes": ((["aiperf_process_failure"] if result["process_exit_code"] else [])
                                 + (["fewer_than_two_valid_rates"] if valid_rate_count < 2 else [])),
                "point_count": len(result["points"]),
                "valid_trial_count": valid_trial_count,
                "valid_rate_count": valid_rate_count}
        ledger.append(campaign["campaign_id"], "cell", run_id, cell)
        ledger.append(campaign["campaign_id"], "adaptive_study", run_id,
                      {"status": study_status, "cell_id": run_id, "artifacts": artifacts,
                       "point_count": cell["point_count"], "valid_trial_count": cell["valid_trial_count"],
                       "valid_rate_count": valid_rate_count})
        answer = {"run_id": run_id, "campaign_id": campaign["campaign_id"],
                  "config_id": resolved.config_id, "status": study_status,
                  "claim": "exploratory_load_curve_only", "point_count": cell["point_count"],
                  "valid_trial_count": cell["valid_trial_count"], "valid_rate_count": valid_rate_count,
                  "artifacts": artifacts}
    except Exception as exc:
        failure = {"status": "failed", "error_type": type(exc).__name__, "reason": str(exc),
                   "artifacts_dir": str(run_dir)}
        (run_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        ledger.append(campaign["campaign_id"], "adaptive_study", run_id, failure)
        raise
    finally:
        pending_error = sys.exc_info()[0] is not None
        cleanup_error = None
        if handle is not None:
            try:
                engine.runtime.stop(handle)
            except Exception as exc:
                cleanup_error = exc
        ledger.append(campaign["campaign_id"], "adaptive_transition", run_id,
                      {"state": "cleanup_failed" if cleanup_error else
                                "stopped" if handle is not None else "startup_failed",
                       "wall_seconds": round(time.monotonic() - started, 3),
                       "measurement_completed": result is not None,
                       "cleanup_error": str(cleanup_error) if cleanup_error else None})
        if cleanup_error and not pending_error:
            raise cleanup_error
    assert answer is not None
    return answer


def _run_adaptive_sla_assessment(args: argparse.Namespace,
                                 registry: ScenarioRegistry) -> dict[str, Any]:
    """Assess saved adaptive native trials offline; never launch a server."""
    from inference_autoresearch.benchmark.adaptive import assess_adaptive_sla
    from inference_autoresearch.evaluation.sla import validate_policy
    from inference_autoresearch.workloads.registry import sha256_file

    policy_path = Path(args.policy).resolve()
    policy = json.loads(policy_path.read_text())
    validate_policy(policy)
    scenario = registry.load(args.scenario)
    run_path = Path(args.adaptive_run).resolve()
    aiperf_dir = run_path if (run_path / "normalized-search-points.json").is_file() else run_path / "aiperf"
    assessment = assess_adaptive_sla(aiperf_dir, scenario, policy)
    assessment["policy_source"] = str(policy_path)
    assessment["policy_file_sha256"] = sha256_file(policy_path)
    default_path = run_path / "sla-assessments" / f"policy-{assessment['policy_sha256'][:12]}.json"
    output_path = Path(args.assessment_output).resolve() if args.assessment_output else default_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(assessment, indent=2, sort_keys=True) + "\n"
    if output_path.exists() and output_path.read_text() != serialized:
        raise ValueError(f"refusing to overwrite changed SLA assessment: {output_path}")
    if not output_path.exists():
        output_path.write_text(serialized)
    return {"status": "assessed", "assessment_path": str(output_path),
            "policy_id": policy["policy_id"], "point_count": assessment["point_count"],
            "observed_feasible_point_count": assessment["observed_feasible_point_count"],
            "claim": assessment["claim"], "capacity_confirmed": False}


def _run_sla_profile(args: argparse.Namespace, campaign: dict[str, Any],
                     campaign_path: Path, domain: Domain, registry: ScenarioRegistry,
                     artifact_root: Path, ledger: Ledger, project_root: Path) -> dict[str, Any]:
    """One fresh pinned server, class-aware external rate planner, raw AIPerf points."""
    from inference_autoresearch.benchmark.sla_profiler import SLAProfileSpec, run_sla_profile
    from inference_autoresearch.contracts import ScenarioManifest
    from inference_autoresearch.evaluation.sla_study import audit_sla_study
    from inference_autoresearch.runtime.config import resolve_config
    from inference_autoresearch.workloads.registry import verify_scenario

    if args.backend != "real" or campaign.get("campaign_id") != "qwen38-27b-eval-v2":
        raise ValueError("iar sla-profile requires --backend real --campaign configs/campaign-v2.json")
    study_path = _file(args.study, campaign_path).resolve()
    readiness = audit_sla_study(study_path, root=project_root)
    if readiness["status"] != "inputs_ready_for_new_campaign":
        raise ValueError(f"SLA study inputs are not qualified: {readiness['blockers']}")
    study = json.loads(study_path.read_text())
    if _file(study["source_campaign_path"], campaign_path).resolve() != campaign_path:
        raise ValueError("SLA study source campaign differs from requested campaign")
    screen = registry.load(study["screen"]["scenario_id"])
    development_ref = study["adaptive_development"]
    development_path = _file(development_ref["manifest_path"], campaign_path).resolve()
    development_manifest = json.loads(development_path.read_text())
    checked = verify_scenario(development_manifest, root=project_root, require_validated=True)
    development = ScenarioManifest(
        scenario_id=development_manifest["scenario_id"],
        workload_id=development_manifest["workload_name"], path=development_path,
        group_id=development_manifest["workload_group_id"],
        offered_load=development_manifest["offered_load"],
        load_unit=development_manifest["load_unit"],
        expected_count=development_manifest["n_planned"],
        output_policy=development_manifest["output_policy"],
        traffic_mode=development_manifest["traffic_mode"],
        history_mode=development_manifest["history_mode"],
        cache_protocol=development_manifest["cache_protocol"],
        metadata={"manifest": development_manifest, "asset": str(checked["payload_path"]),
                  "registry_root": str(project_root),
                  "request_classes": checked["request_classes"],
                  "request_class_path": str(checked["request_class_path"])})
    policy_path = _file(study["policy"]["path"], campaign_path).resolve()
    policy = json.loads(policy_path.read_text())
    spec = SLAProfileSpec(initial_rate_rps=args.initial_rate_rps,
                          min_rate_rps=args.min_rate_rps,
                          max_rate_rps=args.max_rate_rps,
                          max_qualified_points=args.max_points)
    spec.validate(screen, development, policy)
    candidate = _candidate(Path(args.candidate), domain) if args.candidate else CandidateProposal(
        proposal_id="B0-sla-profile", parameters={}, experiment_kind="exploration",
        hypothesis="Locate observed class-aware SLA boundary on qualified development traffic")
    domain.validate(candidate.parameters)
    engine = _engine("real", campaign, domain, registry, artifact_root, ledger, campaign_path)
    engine.benchmark.preflight_tokenizer(development)
    resolved = resolve_config(candidate.parameters, engine._pinned(), engine._domain())
    run_id = "sla-profile-" + uuid.uuid4().hex
    run_dir = artifact_root / "sla-profile" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "proposal.json").write_text(json.dumps(asdict(candidate), indent=2, sort_keys=True) + "\n")
    (run_dir / "resolved-config.json").write_text(json.dumps(asdict(resolved), indent=2,
                                                           sort_keys=True, default=str) + "\n")
    (run_dir / "study.json").write_text(json.dumps(study, indent=2, sort_keys=True) + "\n")
    ledger.append(campaign["campaign_id"], "sla_profile_transition", run_id,
                  {"state": "validated", "config_id": resolved.config_id,
                   "development_scenario_id": development.scenario_id,
                   "claim": "observed_development_points_no_confirmed_capacity"})
    started = time.monotonic()
    handle = None
    result: dict[str, Any] | None = None
    try:
        handle = engine.runtime.start(resolved, run_dir / "server")
        ledger.append(campaign["campaign_id"], "sla_profile_transition", run_id,
                      {"state": "warming", "server_id": handle.server_id})
        engine.benchmark.prepare(handle, development, run_dir / "warmup")
        ledger.append(campaign["campaign_id"], "sla_profile_transition", run_id,
                      {"state": "measuring", "screen_count": 36,
                       "qualified_count_per_point": 240,
                       "max_qualified_points": spec.max_qualified_points})
        result = run_sla_profile(handle, screen, development, policy, spec,
                                 run_dir / "aiperf", engine.benchmark,
                                 preparation_receipt=run_dir / "warmup" / "preparation-receipt.json",
                                 policy_source_path=policy_path)
        from inference_autoresearch.search.report import export_sla_profile_class_points
        class_report = export_sla_profile_class_points(result, run_dir / "report")
        point_path = run_dir / "aiperf" / "sla-profile-points.json"
        artifacts = {"all_points": str(point_path), "aiperf_dir": str(run_dir / "aiperf"),
                     "server": str(run_dir / "server"), "policy": str(policy_path),
                     "study": str(study_path), **class_report}
        valid = [point for point in result["points"]
                 if point["qualified"] and point["qualified"]["status"] == "valid"]
        ledger.append(campaign["campaign_id"], "sla_profile_study", run_id,
                      {"status": "observed" if valid else "invalid",
                       "config_id": resolved.config_id,
                       "claim": result["claim"], "capacity_confirmed": False,
                       "point_count": len(result["points"]),
                       "valid_qualified_point_count": len(valid), "artifacts": artifacts})
        return {"run_id": run_id, "status": "observed" if valid else "invalid",
                "claim": result["claim"], "capacity_confirmed": False,
                "point_count": len(result["points"]),
                "valid_qualified_point_count": len(valid), "artifacts": artifacts}
    except Exception as exc:
        failure = {"status": "failed", "error_type": type(exc).__name__,
                   "reason": str(exc), "artifacts_dir": str(run_dir)}
        (run_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        ledger.append(campaign["campaign_id"], "sla_profile_study", run_id, failure)
        raise
    finally:
        pending_error = sys.exc_info()[0] is not None
        cleanup_error = None
        if handle is not None:
            try:
                engine.runtime.stop(handle)
            except Exception as exc:
                cleanup_error = exc
        ledger.append(campaign["campaign_id"], "sla_profile_transition", run_id,
                      {"state": "cleanup_failed" if cleanup_error else
                                "stopped" if handle is not None else "startup_failed",
                       "wall_seconds": round(time.monotonic() - started, 3),
                       "measurement_completed": result is not None,
                       "cleanup_error": str(cleanup_error) if cleanup_error else None})
        if cleanup_error and not pending_error:
            raise cleanup_error


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
        _print(result)
        if args.command in ("baseline", "pilot", "evaluate") and result.get("status") != "valid":
            return 2
        if args.command == "adaptive" and result.get("status") != "exploratory":
            return 2
        if args.command == "prepare" and result.get("status") == "screen_assets_blocked":
            return 2
        if args.command == "search" and result.get("stop_reason") in (
                "proposal_or_evaluation_error", "duplicate_config"):
            return 2
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
        print(json.dumps({"status": "blocked", "error_type": type(exc).__name__, "reason": str(exc)}),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

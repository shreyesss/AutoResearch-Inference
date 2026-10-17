"""Trusted campaign entrypoint. Proposal authority is separate from GPU authority."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
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
    for command in ("doctor", "characterize", "prepare", "baseline", "pilot", "evaluate",
                    "qualify", "search", "report", "inspect"):
        item = sub.add_parser(command)
        item.add_argument("--campaign", default="configs/campaign.json")
        item.add_argument("--backend", choices=("mock", "real"), default="mock")
        item.add_argument("--output-dir", default=".artifacts/autoresearch-codebase")
        if command in ("pilot", "evaluate"):
            item.add_argument("--candidate")
        if command in ("baseline", "pilot", "evaluate"):
            item.add_argument("--scenario", action="append", dest="scenarios",
                              help="Evaluator registry ID; may be repeated. Defaults to campaign screens.")
        if command == "baseline":
            item.add_argument("--stage", choices=("pilot", "screen"), default=None,
                              help="Use screen for a matched search baseline; defaults to screen in fixed-four-v1.")
        if command == "evaluate":
            item.add_argument("--stage", choices=("pilot", "screen", "expanded", "confirm"), default="pilot")
        if command == "search":
            item.add_argument("--max-proposals", type=int)
            item.add_argument("--resume", action="store_true")
            item.add_argument("--proposer", choices=("codex", "mock"))
            item.add_argument("--skill", default="agent/SKILL.md")
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    campaign_path = Path(args.campaign).resolve()
    campaign = _load_campaign(campaign_path)
    project_root = campaign_path.parent.parent if campaign_path.parent.name == "configs" else campaign_path.parent
    domain = Domain.load(_file(campaign["search_domain_path"], campaign_path))
    registry = ScenarioRegistry(_file(campaign["workload_registry"], campaign_path), root=project_root)
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
        proposer = (MockProposer(domain) if mode == "mock" else CodexProposer(domain, artifact_root,
                     timeout_s=int(campaign["search_budget"].get("proposal_timeout_seconds", 180)),
                     skill_path=_file(args.skill, campaign_path),
                     expected_version=campaign["runtime"].get("codex_cli_version_observed"),
                     model=proposer_config.get("model"),
                     reasoning_effort=proposer_config.get("reasoning_effort"),
                     web_search=proposer_config.get("web_search", "disabled")))
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
    engine = _engine(args.backend, campaign, domain, registry, artifact_root, ledger, campaign_path)
    scenario_ids = args.scenarios or campaign["screen_scenario_ids"]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("scenario IDs must be distinct")
    if command == "baseline":
        stage = args.stage or ("screen" if campaign.get("qualification_requirements", {}).get("mode") == "fixed-four-v1"
                               else "pilot")
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
        _print(result)
        if args.command in ("baseline", "pilot", "evaluate") and result.get("status") != "valid":
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

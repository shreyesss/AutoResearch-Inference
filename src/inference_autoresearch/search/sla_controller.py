"""Bounded Codex proposal loop for the approved v3 research SLA.

Each proposal gets a 36-request gross-regression screen. Only the provisional
finalists selected after exploration receive matched independent development
cells and a class-aware profile. No sealed data is loaded and no observed rate
is called confirmed SLA capacity.
"""

from __future__ import annotations

import json
import hashlib
import fcntl
import math
import os
import shutil
import signal
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal, ProposalContext
from inference_autoresearch.evaluation.sla import assess_observed_point, validate_policy
from inference_autoresearch.evaluation.sla_study import audit_sla_study
from inference_autoresearch.evaluation.split_v2 import SplitError, audit_confirmation_pairs, load_split_plan
from inference_autoresearch.search.domain import Domain, config_identity
from inference_autoresearch.search.proposer import CodexProposer, _stage_sla_study
from inference_autoresearch.search.report import eligible


class SLASearchError(RuntimeError):
    pass


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SLASearchError(f"expected JSON object: {path}")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def screen_viability(candidate: dict[str, Any], baseline: dict[str, Any],
                     rule: dict[str, float]) -> dict[str, Any]:
    """Reject only invalid cells or predeclared, conspicuous regressions."""
    reasons = []
    if not eligible(candidate):
        reasons.append("screen_invalid_or_incomplete")
    if not eligible(baseline):
        raise SLASearchError("36-request matched B0 screen is ineligible")
    cm, bm = candidate.get("metrics", {}), baseline["metrics"]
    for key, threshold in (("output_tokens_per_s", "min_throughput_fraction_of_b0"),
                           ("ttft_p90_ms", "max_ttft_p90_multiplier_of_b0"),
                           ("tpot_p90_ms", "max_tpot_p90_multiplier_of_b0")):
        if (not isinstance(cm.get(key), (int, float)) or not math.isfinite(cm[key])
                or not isinstance(bm.get(key), (int, float)) or bm[key] <= 0):
            reasons.append(f"missing_{key}")
            continue
        ratio = cm[key] / bm[key]
        if (key == "output_tokens_per_s" and ratio < rule[threshold]) or (
                key != "output_tokens_per_s" and ratio > rule[threshold]):
            reasons.append(f"large_regression_{key}")
    return {"promote_to_shortlist": not reasons, "reason_codes": sorted(set(reasons)),
            "claim": "36_request_regression_screen_only",
            "limitation": "A 36-request percentile is noisy; this gate rejects only large effects."}


def select_screen_finalists(rows: list[dict[str, Any]], max_finalists: int) -> dict[str, Any]:
    if max_finalists < 1:
        raise ValueError("max_finalists must be positive")
    candidates = [row for row in rows if row.get("screen_promoted") is True]
    def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
        a, b = left["metrics"], right["metrics"]
        names = ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms")
        return (a[names[0]] >= b[names[0]]
                and all(a[name] <= b[name] for name in names[1:])
                and any(a[name] != b[name] for name in names))
    front = [row for row in candidates if not any(
        dominates(other, row) for other in candidates if other is not row)]
    ordered = sorted(front, key=lambda row: (-row["metrics"]["output_tokens_per_s"],
                                            row["metrics"]["ttft_p90_ms"],
                                            row["metrics"]["tpot_p90_ms"],
                                            row["cell_id"]))
    # The screen is too small to establish Pareto dominance. Sample opposing
    # throughput and latency directions so the expensive gate does not simply
    # select the highest observed throughput from a noisy 36-request run.
    selected: list[dict[str, Any]] = []
    rationale: list[dict[str, str]] = []
    if candidates:
        throughput = min(candidates, key=lambda row: (
            -row["metrics"]["output_tokens_per_s"], row["cell_id"]))
        selected.append(throughput)
        rationale.append({"cell_id": throughput["cell_id"], "reason": "highest_screen_output_tokens_per_s"})
    if len(selected) < max_finalists and len(candidates) > 1:
        remaining = [row for row in candidates if row not in selected]
        latency_fields = ("ttft_p50_ms", "ttft_p90_ms", "tpot_p50_ms", "tpot_p90_ms")
        if not all(all(isinstance(row["metrics"].get(name), (int, float))
                       and math.isfinite(row["metrics"][name]) and row["metrics"][name] > 0
                       for name in latency_fields) for row in candidates):
            raise SLASearchError("viable screen is missing positive p50/p90 latency diagnostics")
        minima = {name: min(row["metrics"][name] for row in candidates)
                  for name in latency_fields}
        latency = min(remaining, key=lambda row: (
            max(row["metrics"][name] / minima[name] for name in latency_fields),
            sum(row["metrics"][name] / minima[name] for name in latency_fields),
            row["cell_id"]))
        selected.append(latency)
        rationale.append({"cell_id": latency["cell_id"],
                          "reason": "lowest_balanced_relative_screen_p50_p90_latency_among_remaining"})
    # The current campaign admits at most two finalists. Retain a deterministic
    # fallback if this pure selector is used independently with a larger limit.
    if len(selected) < max_finalists:
        for row in sorted(candidates, key=lambda item: (
                -item["metrics"]["output_tokens_per_s"], item["cell_id"])):
            if row not in selected:
                selected.append(row)
                rationale.append({"cell_id": row["cell_id"], "reason": "remaining_screen_throughput_order"})
            if len(selected) == max_finalists:
                break
    return {"selected_cell_ids": [row["cell_id"] for row in selected],
            "selection_rationale": rationale,
            "nondominated_cell_ids": [row["cell_id"] for row in ordered],
            "all_viable_cell_ids": [row["cell_id"] for row in candidates],
            "rule": "provisional_throughput_and_latency_extremes_after_all_screens",
            "evidence_grade": "provisional_36_request_screen",
            "limitation": "These noisy screens cannot establish an optimum or eliminate unselected viable candidates."}


class SLAServingController:
    def __init__(self, campaign: dict[str, Any], campaign_path: Path, domain: Domain,
                 registry: Any, proposer: CodexProposer, evaluator: Any, ledger: Any,
                 artifact_root: Path, evidence_refs: list[dict[str, Any]] | None = None):
        self.campaign = campaign
        self.campaign_path = Path(campaign_path).resolve()
        self.root = self.campaign_path.parent.parent
        self.domain = domain
        self.registry = registry
        self.proposer = proposer
        self.evaluator = evaluator
        self.ledger = ledger
        self.artifact_root = Path(artifact_root)
        self.evidence_refs = evidence_refs or []

    def preflight(self) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        campaign = self.campaign
        study_path = (self.root / campaign["sla_study_path"]).resolve()
        if (campaign.get("campaign_id") != "qwen38-27b-sla-serving-v3c"
                or not isinstance(self.proposer, CodexProposer)
                or self.proposer.sla_study_path is None
                or self.proposer.sla_study_path.resolve() != study_path
                or campaign.get("qualification_requirements", {}).get("mode") != "sla-agent-v3"
                or campaign.get("screen_scenario_ids") != ["qwen-ops-mixed-reference-v1"]
                or campaign.get("development_scenario_ids") != [
                    "qwen-ops-mixed-development-1042-v1", "qwen-ops-mixed-development-1043-v1"]
                or campaign.get("heldout_scenario_ids")
                or set(self.registry.list()) != set(campaign["screen_scenario_ids"]
                                                     + campaign["development_scenario_ids"])):
            raise SLASearchError("v3 campaign, Codex proposer or development-only registry differs")
        search = campaign.get("sla_search", {})
        if (search.get("screen_promotion") != "complete_valid_normal_only"
                or search.get("screen_large_regression") != {
                    "min_throughput_fraction_of_b0": 0.5,
                    "max_ttft_p90_multiplier_of_b0": 2.0,
                    "max_tpot_p90_multiplier_of_b0": 2.0}
                or search.get("max_finalists") not in (1, 2)
                or search.get("max_finalists") != campaign.get("search_budget", {}).get("max_expanded_finalists")
                or search.get("profile_max_qualified_points") not in range(1, 7)
                or search.get("sealed_test") != "out_of_registry_and_not_run"):
            raise SLASearchError("v3 coarse screen, shortlist or sealed-test policy differs")
        if not study_path.is_file():
            raise SLASearchError("approved active SLA study is absent; no GPU work is authorized")
        study_before = hashlib.sha256(study_path.read_bytes()).hexdigest()
        status = audit_sla_study(study_path, root=self.root)
        if status["status"] != "inputs_ready_for_new_campaign":
            raise SLASearchError(f"v3 study is not ready: {status['blockers']}")
        study = _read(study_path)
        source_campaign = _read(self.root / study["source_campaign_path"])
        if any(campaign.get(key) != source_campaign.get(key)
               for key in ("model", "runtime", "baseline")):
            raise SLASearchError("v3 serving campaign differs from pinned B0 model, runtime or settings")
        for axis in ("enable_prefix_caching", "mtp_draft_tokens"):
            spec = self.domain.raw["parameters"].get(axis, {})
            if spec.get("active") is not False or len(spec.get("values", [])) != 1:
                raise SLASearchError(f"v3 domain exposes unqualified {axis} variation")
        # This also checks the approved policy, both hash-pinned B0 cells and
        # a class-assessed adaptive B0 profile before any server is launched.
        evidence = _stage_sla_study(study_path, self.artifact_root / "preflight")
        if hashlib.sha256(study_path.read_bytes()).hexdigest() != study_before:
            raise SLASearchError("active SLA study changed during preflight")
        binary = shutil.which(self.proposer.cli)
        if not binary:
            raise SLASearchError("Codex CLI is unavailable before GPU search startup")
        if self.proposer.cli == "codex" and b"IAR_ISOLATED_CODEX_WRAPPER=1" not in Path(binary).read_bytes()[:2048]:
            raise SLASearchError("v3 Codex proposer lacks the isolated Docker wrapper")
        version = subprocess.run([binary, "--version"], capture_output=True, text=True,
                                 timeout=10, check=False)
        auth = subprocess.run([binary, "login", "status"], capture_output=True, text=True,
                              timeout=15, check=False)
        if (version.returncode or "codex-cli" not in version.stdout or auth.returncode
                or (self.proposer.expected_version
                    and self.proposer.expected_version not in version.stdout)):
            raise SLASearchError("Codex CLI version or authentication is not ready before GPU search startup")
        policy = _read(self.root / study["policy"]["path"])
        validate_policy(policy)
        baseline = [
            _read(self.root / relative)
            for relative in (study["adaptive_development"]["baseline_cell_paths"]
                             + study["adaptive_development"]["matched_baseline_replication_cell_paths"])
        ]
        baseline_assessments = [self._assess_cell(cell, policy) for cell in baseline]
        _write(self.artifact_root / "preflight-result.json",
               {"status": "ready", "study_path": str(study_path),
                "study_sha256": study_before,
                "policy_sha256": status["policy_sha256"],
                "matched_b0_cell_ids": [row["cell_id"] for row in baseline],
                "matched_b0_class_assessments": baseline_assessments,
                "b0_profile_point_count": sum(row["point_count"] for row in evidence["baseline_adaptive_studies"]),
                "capacity_confirmed": False})
        self.ledger.append(campaign["campaign_id"], "sla_baseline_development_assessment",
                           "matched_b0", {"assessments": baseline_assessments,
                                          "capacity_confirmed": False})
        return study, policy, baseline

    def _cells(self, ids: list[str]) -> list[dict[str, Any]]:
        wanted = set(ids)
        return [event["payload"] for event in self.ledger.events(self.campaign["campaign_id"], "cell")
                if event["payload"].get("cell_id") in wanted]

    def _assess_cell(self, cell: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        if not eligible(cell):
            return {"cell_id": cell["cell_id"], "observed_feasible": False,
                    "reason_codes": ["cell_invalid_or_incomplete"], "assessment": None}
        scenario = self.registry.load(cell["scenario_id"])
        classes = scenario.metadata.get("request_classes")
        raw_path = Path(cell.get("artifacts", {}).get("raw_requests", ""))
        if not raw_path.is_file() or not classes:
            raise SLASearchError("qualified development cell lacks raw requests or class sidecar")
        records = [json.loads(line) for line in raw_path.read_text().splitlines() if line]
        assessment = assess_observed_point(records, policy, classes)
        result = {"cell_id": cell["cell_id"], "scenario_id": cell["scenario_id"],
                  "config_id": cell["config_id"], "observed_feasible": assessment["observed_feasible"],
                  "assessment": assessment, "raw_requests": str(raw_path),
                  "raw_requests_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                  "claim": "matched_development_point_only_no_confirmed_capacity"}
        return result

    def _profile_finalist(self, proposal: CandidateProposal, study_path: Path) -> dict[str, Any]:
        """Reuse the class-aware profiler only after both dev windows pass."""
        root = self.artifact_root / "sla-development" / proposal.proposal_id
        candidate_path = root / "candidate.json"
        _write(candidate_path, asdict(proposal))
        argv = [str(self.root / ".venv/bin/iar"), "sla-profile", "--backend", "real",
                "--campaign", str(self.campaign_path), "--study", str(study_path),
                "--candidate", str(candidate_path), "--max-points",
                str(self.campaign["sla_search"]["profile_max_qualified_points"])]
        _write(root / "profile-argv.json", {"argv": argv})
        process = subprocess.Popen(argv, cwd=self.root, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=28800)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = process.communicate()
        (root / "profile-console.log").write_text(stdout + stderr)
        try:
            result = json.loads(stdout)
        except ValueError:
            result = {}
        packet = {"proposal_id": proposal.proposal_id, "process_exit_code": process.returncode,
                  "timed_out": timed_out,
                  "result": result, "claim": "observed_development_points_no_confirmed_capacity",
                  "capacity_confirmed": False}
        _write(root / "profile-result.json", packet)
        self.ledger.append(self.campaign["campaign_id"], "sla_finalist_profile",
                           proposal.proposal_id, packet)
        return packet

    def run(self) -> dict[str, Any]:
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        lock_path = self.artifact_root / "search-process.lock"
        with lock_path.open("a+") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SLASearchError("another v3 SLA search process owns the campaign") from exc
            try:
                return self._run_locked()
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _run_locked(self) -> dict[str, Any]:
        study, policy, baseline_cells = self.preflight()
        campaign_id = self.campaign["campaign_id"]
        study_path = (self.root / self.campaign["sla_study_path"]).resolve()
        study_digest = hashlib.sha256(study_path.read_bytes()).hexdigest()
        study_lock = {"study_path": str(study_path), "study_sha256": study_digest,
                      "policy_sha256": study["policy"]["sha256"],
                      "baseline_profile_sha256": [item["source_sha256"]
                                                  for item in study["baseline_adaptive_run_paths"]],
                      "baseline_cell_sha256_by_path":
                          study["adaptive_development"]["baseline_cell_sha256_by_path"],
                      "capacity_confirmed": False}
        self.ledger.claim(campaign_id, "sla_study_lock", "frozen", study_digest, study_lock)
        def require_frozen_study() -> None:
            if hashlib.sha256(study_path.read_bytes()).hexdigest() != study_digest:
                raise SLASearchError("active SLA study changed during v3 search")
        if self.ledger.events(campaign_id, "proposal"):
            raise SLASearchError("v3 search already has proposals; inspect before starting another batch")
        budget = self.campaign["search_budget"]
        max_proposals = budget["max_distinct_proposals"]
        if not 1 <= max_proposals <= 8:
            raise SLASearchError("v3 proposal budget must be 1..8")
        screen_id = self.campaign["screen_scenario_ids"][0]
        dev_ids = self.campaign["development_scenario_ids"]
        baseline = CandidateProposal(proposal_id="B0-sla-screen", parameters={},
            experiment_kind="exploration", hypothesis="Matched short screen reference")
        screen_result = self.evaluator.evaluate(baseline, [screen_id], "triage")
        require_frozen_study()
        screen_b0 = self._cells(screen_result.cell_ids)
        if screen_result.status != "valid" or len(screen_b0) != 1 or not eligible(screen_b0[0]):
            raise SLASearchError("fresh 36-request B0 screen failed")
        self.ledger.append(campaign_id, "sla_screen_baseline", screen_b0[0]["cell_id"],
                           {"cell_id": screen_b0[0]["cell_id"], "claim": "regression_screen_only"})
        screened: list[dict[str, Any]] = []
        finalized: list[dict[str, Any]] = []
        profiles: list[dict[str, Any]] = []
        split = load_split_plan(self.root / study["capacity_confirmation"]["split_plan_path"], root=self.root)
        input_audit = _read(self.root / ".artifacts/v3-independent-capture/development-input-audit.json")
        proposed_ids: set[str] = {config_identity(self.campaign, self.campaign["baseline"])}
        started = time.monotonic()
        for attempt in range(max_proposals):
            require_frozen_study()
            if time.monotonic() - started >= budget["wall_seconds"]:
                break
            visible = [screen_b0[0], *[row["cell"] | {"sla_screen_decision": row["decision"]}
                                      for row in screened]]
            context = ProposalContext(
                campaign_id=campaign_id,
                mission="Explore serving settings using noisy short screens; seek better class-aware SLA-feasible rate after finalist validation",
                domain=self.domain.raw, baseline=self.campaign["baseline"], frontier=[],
                recent_results=visible, evidence_refs=self.evidence_refs,
                remaining_budget={"distinct_proposals": max_proposals-attempt,
                                  "wall_seconds": max(0, budget["wall_seconds"]-(time.monotonic()-started))},
                qualification={"search_allowed": True, "qualification_grade": "v3_research_sla",
                               "evidence_ids": [row["cell_id"] for row in baseline_cells]})
            proposal = self.proposer.propose(context)
            require_frozen_study()
            self.domain.validate(proposal.parameters)
            config_id = config_identity(self.campaign,
                                        self.domain.effective(self.campaign["baseline"], proposal.parameters))
            if config_id in proposed_ids:
                self.ledger.append(campaign_id, "sla_proposal_rejected", proposal.proposal_id,
                                   {"reason": "equivalent_configuration", "config_id": config_id})
                continue
            proposed_ids.add(config_id)
            self.ledger.append(campaign_id, "proposal", proposal.proposal_id,
                               {"proposal": asdict(proposal), "config_id": config_id,
                                "claim": "v3_research_proposal"})
            result = self.evaluator.evaluate(proposal, [screen_id], "triage")
            require_frozen_study()
            cells = self._cells(result.cell_ids)
            if len(cells) != 1:
                raise SLASearchError("candidate screen has no unique CellResult")
            decision = screen_viability(cells[0], screen_b0[0],
                self.campaign["sla_search"]["screen_large_regression"])
            self.ledger.append(campaign_id, "sla_screen_decision", proposal.proposal_id,
                               {"proposal_id": proposal.proposal_id, "config_id": config_id,
                                "cell_id": cells[0]["cell_id"], "baseline_cell_id": screen_b0[0]["cell_id"],
                                **decision})
            screened.append({"proposal": proposal, "cell": cells[0], "decision": decision})
        # Select only after all proposals have had a short screen. The full
        # screen table remains in the ledger and on disk, including rejected
        # and unselected viable configurations.
        rows = [row["cell"] | {"screen_promoted": row["decision"]["promote_to_shortlist"]}
                for row in screened]
        selection = select_screen_finalists(rows, self.campaign["sla_search"]["max_finalists"])
        self.ledger.append(campaign_id, "sla_screen_shortlist", campaign_id, selection)
        _write(self.artifact_root / "screen-shortlist.json", selection)
        selected = set(selection["selected_cell_ids"])
        for row in screened:
            if row["cell"]["cell_id"] not in selected:
                continue
            proposal = row["proposal"]
            require_frozen_study()
            development = self.evaluator.evaluate(proposal, dev_ids, "expanded")
            require_frozen_study()
            development_cells = self._cells(development.cell_ids)
            if len(development_cells) != len(dev_ids):
                raise SLASearchError("development evaluation lacks both independent CellResults")
            assessments = [self._assess_cell(cell, policy) for cell in development_cells]
            try:
                pair = audit_confirmation_pairs(split, input_audit, "development_replication",
                                                baseline_cells, development_cells)
                pairing_error = None
            except SplitError as exc:
                pair = None
                pairing_error = str(exc)
            report = {"proposal_id": proposal.proposal_id,
                      "configuration_id": development_cells[0]["config_id"],
                      "claim": "independent_development_observations_only_no_confirmed_capacity",
                      "capacity_confirmed": False, "matched_pairs": pair,
                      "pairing_error": pairing_error,
                      "assessments": assessments,
                      "both_windows_observed_feasible": pairing_error is None and all(
                          item["observed_feasible"] for item in assessments)}
            report_path = self.artifact_root / "sla-development" / proposal.proposal_id / "report.json"
            _write(report_path, report)
            self.ledger.append(campaign_id, "sla_development_report", proposal.proposal_id,
                               {"path": str(report_path), **report})
            finalized.append(report)
            if report["both_windows_observed_feasible"]:
                require_frozen_study()
                packet = self._profile_finalist(proposal, study_path)
                profiles.append(packet)
                result = packet.get("result") or {}
                source_name = (result.get("artifacts") or {}).get("all_points")
                if packet["process_exit_code"] == 0 and isinstance(source_name, str):
                    source = Path(source_name).resolve()
                    allowed_root = (self.root / ".artifacts/autoresearch-codebase").resolve()
                    if not source.is_file() or not source.is_relative_to(allowed_root):
                        raise SLASearchError("candidate SLA profile source is outside research artifacts")
        summary = {"campaign_id": campaign_id, "status": "sequential_development_search_complete",
                   "proposal_count": len(screened), "shortlisted": len(selected),
                   "all_viable_screen_cell_ids": selection["all_viable_cell_ids"],
                   "selection_evidence_grade": selection["evidence_grade"],
                   "development_reports": finalized, "finalist_profiles": profiles,
                   "capacity_confirmed": False,
                   "next_gate": "independently confirm a frozen fixed-rate boundary and then sealed test"}
        _write(self.artifact_root / "sla-search-summary.json", summary)
        return summary

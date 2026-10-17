"""Fast, explicitly exploratory serving search over matched 36-request screens.

This campaign reuses a separately audited B0 capture as research context.  It
does not infer a capacity boundary or run the independent development/test gates.
"""

from __future__ import annotations

import fcntl
import csv
import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inference_autoresearch.cli import _engine
from inference_autoresearch.contracts import CandidateProposal, ProposalContext
from inference_autoresearch.search.domain import Domain, config_identity
from inference_autoresearch.search.proposer import CodexProposer, ProposerError
from inference_autoresearch.search.rate_screen import run_rate_screen
from inference_autoresearch.search.report import eligible
from inference_autoresearch.search.sla_controller import screen_viability, select_screen_finalists
from inference_autoresearch.storage import Ledger
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import ScenarioRegistry, sha256_file, verify_scenario


CAMPAIGN_ID = "qwen38-27b-fast-pilot-v4"
SCREEN_ID = "qwen-ops-mixed-reference-v1"
RATE_RPS = 0.4
BASE_SEED = 41042
ATTEMPT_BUDGET = 8
MAX_FINALISTS = 2
REGRESSION_RULE = {"min_throughput_fraction_of_b0": 0.5,
                   "max_ttft_p90_multiplier_of_b0": 2.0,
                   "max_tpot_p90_multiplier_of_b0": 2.0}


class FastPilotError(RuntimeError):
    pass


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise FastPilotError(f"expected JSON object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")
    pending.replace(path)


def idle_gpu() -> None:
    if subprocess.run(["docker", "container", "inspect", "iar-b0"],
                      capture_output=True, check=False).returncode == 0:
        raise FastPilotError("B0 server still exists; pilot must wait for the shared GPU")
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                             "--format=csv,noheader,nounits"], capture_output=True,
                            text=True, check=True, timeout=15)
    if result.stdout.strip():
        raise FastPilotError("GPU compute process is active; refusing overlap")


def baseline_evidence_refs(report: dict[str, Any], report_path: Path,
                           root: Path) -> list[dict[str, str]]:
    """Stage compact native diagnostics, retaining source hashes for audit."""
    refs = [{"evidence_id": "b0-observed-v4", "snapshot_path": str(report_path),
             "sha256": sha256_file(report_path)}]
    for label, entry in (("policy", report.get("input_artifacts", {}).get("policy")),
                         ("class-sidecar", report.get("input_artifacts", {}).get("class_sidecar"))):
        if not isinstance(entry, dict):
            raise FastPilotError(f"B0 report lacks {label} provenance")
        source = Path(entry["path"]).resolve()
        if not source.is_file() or not source.is_relative_to(root) or sha256_file(source) != entry["sha256"]:
            raise FastPilotError(f"B0 {label} artifact changed")
        refs.append({"evidence_id": f"b0-{label}-v4", "snapshot_path": str(source),
                     "sha256": entry["sha256"]})
    for trial_name, trial in (("capture", report.get("source_capture")),
                              ("replay", report.get("fixed_replay"))):
        native = trial.get("native_artifacts") if isinstance(trial, dict) else None
        if not isinstance(native, dict):
            raise FastPilotError(f"B0 {trial_name} native artifacts absent")
        for source_name, suffix in (("profile_export_aiperf.json", "summary"),
                                    ("profile_export.jsonl", "request-metrics")):
            entry = native.get(source_name)
            if not isinstance(entry, dict):
                raise FastPilotError(f"B0 {trial_name} {source_name} absent")
            source = Path(entry["path"]).resolve()
            if (not source.is_file() or not source.is_relative_to(root)
                    or sha256_file(source) != entry["sha256"]):
                raise FastPilotError(f"B0 {trial_name} {source_name} changed")
            refs.append({"evidence_id": f"b0-{trial_name}-{suffix}-v4",
                         "snapshot_path": str(source), "sha256": entry["sha256"]})
        # Small server counter exports are useful for queue/KV hypotheses.
        counters = Path(native["profile_export_aiperf.json"]["path"]).parent / "server_metrics_export.csv"
        if counters.is_file() and counters.is_relative_to(root):
            refs.append({"evidence_id": f"b0-{trial_name}-server-metrics-v4",
                         "snapshot_path": str(counters), "sha256": sha256_file(counters)})
    return refs


def preflight(root: Path, out: Path) -> dict[str, Any]:
    """Read-only validation; safe while the existing B0 chain uses the GPU."""
    root, out = root.resolve(), out.resolve()
    source_path = root / "configs/campaign-sla-serving-v3c.json"
    domain_path = root / "configs/search-domain-v3c.json"
    policy_path = root / "configs/sla-policy-v3.json"
    b0_path = out / "b0-observed.json"
    if not all(path.is_file() for path in (source_path, domain_path, policy_path, b0_path)):
        raise FastPilotError("v4 source campaign/domain/policy or audited B0 report is absent")
    source, b0 = read(source_path), read(b0_path)
    domain = Domain.load(domain_path)
    pinned = PinnedEnvironment(root / source["model"]["local_path"])
    baseline_id = resolve_config({}, pinned).config_id
    if (source.get("proposer") != {"model": "gpt-6-sol", "reasoning_effort": "medium",
                                    "web_search": "live", "container_network": "bridge"}
            or source.get("search_domain_path") != "configs/search-domain-v3c.json"
            or b0.get("status") != "observed_b0"
            or b0.get("capacity_confirmed") is not False
            or b0.get("baseline_config_id") != baseline_id
            or b0.get("policy_sha256") != sha256_file(policy_path)):
        raise FastPilotError("pinned v4 proposer/domain or B0 policy identity differs")
    campaign = json.loads(json.dumps(source))
    campaign["campaign_id"] = CAMPAIGN_ID
    campaign["qualification_requirements"] = {"mode": "fast_pilot_v4",
                                               "scope": "exploratory_operator_screens_only"}
    campaign["search_budget"] = {"max_distinct_proposals": ATTEMPT_BUDGET,
                                 "max_expanded_finalists": MAX_FINALISTS,
                                 "proposal_timeout_seconds": 300}
    campaign["screen_scenario_ids"] = [SCREEN_ID]
    campaign.pop("development_scenario_ids", None)
    campaign.pop("sla_study_path", None)
    registry = ScenarioRegistry(root / campaign["workload_registry"], root=root)
    screen = registry.load(SCREEN_ID)
    checked = verify_scenario(screen.metadata["manifest"], root=root)
    if (screen.expected_count != 36 or screen.traffic_mode != "independent_open_loop"
            or screen.history_mode != "single_turn" or len(checked["planned"]) != 36):
        raise FastPilotError("OPS36 screen is not the validated frozen reference")
    if not shutil.which("codex"):
        raise FastPilotError("isolated Codex wrapper is unavailable")
    evidence = baseline_evidence_refs(b0, b0_path, root)
    return {"status": "ready_for_exploratory_pilot", "campaign": campaign,
            "domain": domain, "registry": registry, "screen": screen,
            "baseline_evidence_refs": evidence,
            "b0_path": b0_path, "b0_sha256": sha256_file(b0_path),
            "campaign_source_sha256": sha256_file(source_path),
            "domain_sha256": sha256_file(domain_path),
            "policy_sha256": sha256_file(policy_path),
            "screen_manifest_sha256": sha256_file(Path(screen.path)),
            "screen_payload_sha256": sha256_file(checked["payload_path"]),
            "capacity_confirmed": False}


def rate_lock(prepared: dict[str, Any], root: Path) -> dict[str, Any]:
    """Use a declared diagnostic rate, with no invented adaptive B0 profile."""
    screen = prepared["screen"]
    return {"schema_version": "rate-screen-lock-v1",
            "claim": "fixed_rate_matched_36_request_exploratory_triage_only",
            "exact_arrival_pairing": False, "capacity_confirmed": False,
            "selection_reason": "versioned_v4_diagnostic_rate_not_sla_capacity",
            "selected_rate_rps": RATE_RPS, "base_seed": BASE_SEED,
            "source_profile_path": str(prepared["b0_path"].relative_to(root)),
            "source_profile_sha256": prepared["b0_sha256"],
            "screen_scenario_id": screen.scenario_id,
            "screen_manifest_sha256": prepared["screen_manifest_sha256"],
            "screen_payload_sha256": prepared["screen_payload_sha256"],
            "arrival_pattern": "poisson",
            "arrival_seed": BASE_SEED + round(RATE_RPS * 1_000_000),
            "client_concurrency_cap": 512}


def _cells(ledger: Ledger, ids: list[str]) -> list[dict[str, Any]]:
    wanted = set(ids)
    return [event["payload"] for event in ledger.events(CAMPAIGN_ID, "cell")
            if event["payload"].get("cell_id") in wanted]


def export_screen_points(out: Path, baseline: dict[str, Any],
                         rows: list[dict[str, Any]]) -> dict[str, str]:
    """Persist every point, including invalid ones; plots are descriptive."""
    points = []
    for label, cell, decision in [("B0", baseline, None), *[
            (row["proposal"].proposal_id, row["cell"], row["decision"]) for row in rows]]:
        points.append({"label": label, "cell_id": cell["cell_id"],
                       "config_id": cell["config_id"], "status": cell["status"],
                       "reason_codes": cell.get("reason_codes", []),
                       "shortlisted_eligible": decision["promote_to_shortlist"] if decision else None,
                       "metrics": cell.get("metrics", {}),
                       "claim": "single_fixed_load_observation_no_capacity"})
    json_path, csv_path = out / "all-screen-points.json", out / "all-screen-points.csv"
    write(json_path, {"campaign_id": CAMPAIGN_ID, "rate_rps": RATE_RPS,
                      "points": points, "capacity_confirmed": False})
    names = ("output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms", "ttft_p99_ms",
             "tpot_p50_ms", "tpot_p90_ms", "tpot_p99_ms", "dispatch_lag_p99_ms")
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["label", "cell_id", "config_id", "status",
                                                        "reason_codes", "shortlisted_eligible", *names])
        writer.writeheader()
        for point in points:
            writer.writerow({"label": point["label"], "cell_id": point["cell_id"],
                             "config_id": point["config_id"], "status": point["status"],
                             "reason_codes": ";".join(point["reason_codes"]),
                             "shortlisted_eligible": point["shortlisted_eligible"],
                             **{name: point["metrics"].get(name) for name in names}})
    valid = [point for point in points if point["status"] == "valid"
             and all(isinstance(point["metrics"].get(name), (int, float))
                     for name in ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms"))]
    front = []
    for point in valid:
        a = point["metrics"]
        if not any(other is not point and
                   other["metrics"]["output_tokens_per_s"] >= a["output_tokens_per_s"] and
                   other["metrics"]["ttft_p90_ms"] <= a["ttft_p90_ms"] and
                   other["metrics"]["tpot_p90_ms"] <= a["tpot_p90_ms"] and
                   any(other["metrics"][key] != a[key] for key in
                       ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms"))
                   for other in valid):
            front.append(point["cell_id"])
    frontier_path = out / "provisional-fixed-load-frontier.json"
    write(frontier_path, {"cell_ids": front, "rate_rps": RATE_RPS,
                          "claim": "descriptive_nondominance_one_noisy_fixed_load_only",
                          "capacity_confirmed": False})
    result = {"json": str(json_path), "csv": str(csv_path), "frontier": str(frontier_path)}
    if valid:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        figure, axis = plt.subplots(figsize=(8, 5))
        for point in valid:
            metric = point["metrics"]
            axis.scatter(metric["ttft_p90_ms"], metric["output_tokens_per_s"],
                         marker="*" if point["cell_id"] in front else "o")
            axis.annotate(point["label"], (metric["ttft_p90_ms"],
                                             metric["output_tokens_per_s"]))
        axis.set(xlabel="Aggregate TTFT p90 (ms)", ylabel="Output tokens/s",
                 title="Provisional operator contrast at 0.4 requests/s")
        axis.grid(True, alpha=0.3)
        figure.tight_layout()
        svg_path = out / "provisional-throughput-ttft.svg"
        figure.savefig(svg_path)
        plt.close(figure)
        result["scatter_svg"] = str(svg_path)
    return result


def run(root: Path, out: Path) -> dict[str, Any]:
    root, out = root.resolve(), out.resolve()
    prepared = preflight(root, out)
    controller_pin_path = out / "controller-image-pin.json"
    if not controller_pin_path.is_file():
        raise FastPilotError("controller source/image parity receipt is absent")
    controller_pin = read(controller_pin_path)
    if (not isinstance(controller_pin.get("source_tree_sha256"), str)
            or not isinstance(controller_pin.get("isolated_wrapper_sha256"), str)):
        raise FastPilotError("controller source/image parity receipt is incomplete")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "pilot-process.lock").open("a+") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if any((out / name).exists() for name in
               ("pilot-campaign-lock.json", "run-status.json", "proposals", "ledger.sqlite")):
            raise FastPilotError("pilot already started; inspect artifacts before any new campaign")
        idle_gpu()
        lock = {key: prepared[key] for key in
                ("campaign_source_sha256", "domain_sha256", "policy_sha256",
                 "screen_manifest_sha256", "screen_payload_sha256", "b0_sha256")}
        lock.update({"campaign_id": CAMPAIGN_ID, "rate_rps": RATE_RPS,
                     "base_seed": BASE_SEED, "attempt_budget": ATTEMPT_BUDGET,
                     "skill_sha256": sha256_file(root / "agent/SKILL.md"),
                     "reference_sha256": sha256_file(root / "agent/reference.md"),
                     "controller_pin_sha256": sha256_file(controller_pin_path),
                     "controller_source_tree_sha256": controller_pin["source_tree_sha256"],
                     "isolated_wrapper_sha256": controller_pin["isolated_wrapper_sha256"],
                     "capacity_confirmed": False})
        write(out / "pilot-campaign-lock.json", lock)
        def require_frozen() -> None:
            sources = {"campaign_source_sha256": root / "configs/campaign-sla-serving-v3c.json",
                       "domain_sha256": root / "configs/search-domain-v3c.json",
                       "policy_sha256": root / "configs/sla-policy-v3.json",
                       "screen_manifest_sha256": Path(prepared["screen"].path),
                       "screen_payload_sha256": Path(prepared["screen"].metadata["asset"]),
                       "b0_sha256": prepared["b0_path"],
                       "skill_sha256": root / "agent/SKILL.md",
                       "reference_sha256": root / "agent/reference.md",
                       "controller_pin_sha256": controller_pin_path}
            for name, source in sources.items():
                if sha256_file(source) != lock[name]:
                    raise FastPilotError(f"frozen pilot input changed: {name}")
        fixed_rate = rate_lock(prepared, root)
        write(out / "screen-rate-lock.json", fixed_rate)
        state = {"status": "running", "campaign_id": CAMPAIGN_ID,
                 "started_at_utc": datetime.now(UTC).isoformat(),
                 "stage": "baseline_screen", "attempts_completed": 0,
                 "capacity_confirmed": False, "sealed_test_touched": False}
        write(out / "run-status.json", state)
        campaign, domain, registry = prepared["campaign"], prepared["domain"], prepared["registry"]
        ledger = Ledger(out / "ledger.sqlite")
        engine = _engine("real", campaign, domain, registry, out, ledger,
                         root / "configs/campaign-sla-serving-v3c.json")
        proposer = CodexProposer(domain, out, timeout_s=300,
                                 skill_path=root / "agent/SKILL.md",
                                 model="gpt-6-sol", reasoning_effort="medium",
                                 web_search="live")
        evidence = prepared["baseline_evidence_refs"]
        baseline = CandidateProposal(proposal_id="B0-v4-screen", parameters={},
                                     experiment_kind="exploration",
                                     hypothesis="Fixed rate exploratory screen reference")
        try:
            b0_result = run_rate_screen(engine, baseline, prepared["screen"], fixed_rate,
                                        ledger, CAMPAIGN_ID, out)
            require_frozen()
            b0_cells = _cells(ledger, b0_result.cell_ids)
            if b0_result.status != "valid" or len(b0_cells) != 1 or not eligible(b0_cells[0]):
                raise FastPilotError("fresh matched B0 diagnostic screen failed")
            b0_cell = b0_cells[0]
            export_screen_points(out, b0_cell, [])
            ledger.append(CAMPAIGN_ID, "pilot_baseline_screen", b0_cell["cell_id"],
                          {"cell_id": b0_cell["cell_id"], "rate_rps": RATE_RPS,
                           "base_seed": BASE_SEED, "capacity_confirmed": False})
            proposed_ids = {config_identity(campaign, campaign["baseline"])}
            rows: list[dict[str, Any]] = []
            for attempt in range(1, ATTEMPT_BUDGET + 1):
                require_frozen()
                state.update({"stage": "proposal", "attempts_completed": attempt - 1,
                              "updated_at_utc": datetime.now(UTC).isoformat()})
                write(out / "run-status.json", state)
                visible = [b0_cell, *[row["cell"] | {"screen_decision": row["decision"]}
                                       for row in rows]]
                context = ProposalContext(
                    campaign_id=CAMPAIGN_ID,
                    mission="Explore vLLM settings at one fixed diagnostic load; seek operator tradeoffs without a capacity claim",
                    domain=domain.raw, baseline=campaign["baseline"], frontier=[],
                    recent_results=visible, evidence_refs=evidence,
                    remaining_budget={"distinct_proposals": ATTEMPT_BUDGET - attempt + 1},
                    qualification={"mode": "fast_pilot_v4", "search_allowed": True,
                                   "qualification_grade": "exploratory_fixed_rate_screens",
                                   "evidence_ids": [ref["evidence_id"] for ref in evidence]
                                   + [b0_cell["cell_id"]]})
                try:
                    proposal = proposer.propose(context)
                except (ProposerError, ValueError) as exc:
                    ledger.append(CAMPAIGN_ID, "pilot_proposal_rejected", f"attempt-{attempt}",
                                  {"reason": "proposer_failed", "error": str(exc),
                                   "attempt": attempt})
                    state["attempts_completed"] = attempt
                    write(out / "run-status.json", state)
                    continue
                require_frozen()
                try:
                    domain.validate(proposal.parameters)
                    config_id = config_identity(campaign,
                        domain.effective(campaign["baseline"], proposal.parameters))
                except ValueError as exc:
                    ledger.append(CAMPAIGN_ID, "pilot_proposal_rejected", f"attempt-{attempt}",
                                  {"reason": "domain_invalid", "error": str(exc),
                                   "attempt": attempt})
                    state["attempts_completed"] = attempt
                    write(out / "run-status.json", state)
                    continue
                if config_id in proposed_ids:
                    ledger.append(CAMPAIGN_ID, "pilot_proposal_rejected", f"attempt-{attempt}",
                                  {"reason": "equivalent_configuration", "config_id": config_id,
                                   "attempt": attempt})
                    state["attempts_completed"] = attempt
                    write(out / "run-status.json", state)
                    continue
                proposed_ids.add(config_id)
                ledger.append(CAMPAIGN_ID, "proposal", proposal.proposal_id,
                              {"attempt": attempt, "proposal": asdict(proposal),
                               "config_id": config_id,
                               "claim": "exploratory_fixed_rate_proposal"})
                state.update({"stage": "candidate_screen", "active_proposal_id": proposal.proposal_id})
                write(out / "run-status.json", state)
                result = run_rate_screen(engine, proposal, prepared["screen"], fixed_rate,
                                         ledger, CAMPAIGN_ID, out)
                require_frozen()
                cells = _cells(ledger, result.cell_ids)
                if len(cells) != 1:
                    raise FastPilotError("candidate screen produced no unique CellResult")
                decision = screen_viability(cells[0], b0_cell, REGRESSION_RULE)
                ledger.append(CAMPAIGN_ID, "pilot_screen_decision", proposal.proposal_id,
                              {"attempt": attempt, "cell_id": cells[0]["cell_id"],
                               "baseline_cell_id": b0_cell["cell_id"], **decision})
                rows.append({"proposal": proposal, "cell": cells[0], "decision": decision})
                export_screen_points(out, b0_cell, rows)
                state.update({"attempts_completed": attempt, "completed_candidate_screens": len(rows),
                              "active_proposal_id": None})
                write(out / "run-status.json", state)
            selection = select_screen_finalists(
                [row["cell"] | {"screen_promoted": row["decision"]["promote_to_shortlist"]}
                 for row in rows], MAX_FINALISTS)
            write(out / "provisional-finalists.json", selection | {
                "claim": "operator_shortlist_from_noisy_fixed_rate_screens_only",
                "capacity_confirmed": False, "further_evaluation_required": True})
            ledger.append(CAMPAIGN_ID, "pilot_shortlist", CAMPAIGN_ID, selection)
            summary = {"status": "exploratory_pilot_complete", "campaign_id": CAMPAIGN_ID,
                       "attempts": ATTEMPT_BUDGET, "valid_candidate_screens": sum(
                           eligible(row["cell"]) for row in rows),
                       "baseline_screen_cell_id": b0_cell["cell_id"],
                       "candidate_screen_cell_ids": [row["cell"]["cell_id"] for row in rows],
                       "provisional_finalists": selection["selected_cell_ids"],
                       "rate_rps": RATE_RPS, "capacity_confirmed": False,
                       "sealed_test_touched": False,
                       "claim": "exploratory_fixed_rate_operator_comparisons_only"}
            write(out / "pilot-summary.json", summary)
            state.update({"status": "complete", "stage": "complete",
                          "finished_at_utc": datetime.now(UTC).isoformat()})
            write(out / "run-status.json", state)
            return summary
        except Exception as exc:
            state.update({"status": "blocked", "stage": "blocked",
                          "error": f"{type(exc).__name__}: {exc}",
                          "updated_at_utc": datetime.now(UTC).isoformat()})
            write(out / "run-status.json", state)
            raise

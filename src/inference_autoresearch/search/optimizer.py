"""Persistent Optuna proposals for the bounded serving configuration domain.

Optuna supplies sampling, Pareto bookkeeping and SQLite resume. The trusted
controller still owns the GPU, candidate validation and all measurements.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal, ProposalContext

from .domain import Domain, config_identity, scientific_campaign_hash
from .report import eligible


DEFERRED_AXES = frozenset({"enable_prefix_caching", "mtp_draft_tokens"})


class OptunaProposer:
    """Ask/tell multiobjective sampler with each trial linked to ledger evidence."""

    def __init__(self, campaign: dict[str, Any], domain: Domain, artifact_root: Path,
                 ledger: Any, backend: str):
        try:
            import optuna
        except ImportError as exc:
            raise ImportError("Optuna proposer requires optuna; install the optimizer extra") from exc
        self.optuna = optuna
        self.campaign = campaign
        self.domain = domain
        self.artifact_root = Path(artifact_root)
        self.ledger = ledger
        self.backend = backend
        self.study_dir = self.artifact_root / "optimizer"
        self.study_dir.mkdir(parents=True, exist_ok=True)
        self.storage_path = self.study_dir / "optuna.sqlite3"
        seed = int(campaign.get("search_budget", {}).get("optimizer_seed", 20261018))
        sampler = optuna.samplers.NSGAIISampler(seed=seed)
        self.study = optuna.create_study(
            study_name=campaign["campaign_id"],
            storage=f"sqlite:///{self.storage_path}",
            directions=["maximize", "minimize"],
            sampler=sampler,
            load_if_exists=True,
        )
        identity = {"campaign_hash": scientific_campaign_hash(campaign),
                    "domain_hash": domain.digest, "backend": backend,
                    "objective_version": "mixed-throughput-vs-worst-p90-ratio-v1"}
        old = self.study.user_attrs.get("identity")
        if old is not None and old != identity:
            raise ValueError("Optuna study identity differs; use a new campaign/output directory")
        self.study.set_user_attr("identity", identity)
        self._pending: dict[str, Any] = {}

    def reconcile(self) -> None:
        """Recover completed ledger results after a crash; fail orphaned asks.

        This is called only when the operator explicitly resumes a campaign.
        A concurrently running search is outside the single-GPU-lease contract.
        """
        states = self.optuna.trial.TrialState
        finished = {row["payload"].get("proposal_id"): row["payload"] for row in
                    self.ledger.events(self.campaign["campaign_id"], "optimizer_feedback")}
        for frozen in self.study.get_trials(deepcopy=False, states=(states.RUNNING,)):
            proposal_id = frozen.user_attrs.get("proposal_id")
            if proposal_id in finished:
                values = finished[proposal_id].get("values")
                if values and len(values) == 2:
                    self.study.tell(frozen.number, values)
                    continue
            self.study.tell(frozen.number, state=states.FAIL)

    def propose(self, context: ProposalContext) -> CandidateProposal:
        axes = {key: spec for key, spec in self.domain.raw["parameters"].items()
                if spec.get("active") is not False and key not in DEFERRED_AXES
                and len(spec["values"]) > 1}
        if not axes:
            raise ValueError("Optuna has no admitted serving axes")
        seen = {event["payload"].get("config_id") for event in
                self.ledger.events(context.campaign_id, "proposal")}
        seen.add(config_identity(self.campaign, self.campaign["baseline"]))
        for _ in range(48):
            trial = self.study.ask()
            overrides = {key: trial.suggest_categorical(key, spec["values"])
                         for key, spec in axes.items()}
            overrides = {key: value for key, value in overrides.items()
                         if value != axes[key]["baseline"]}
            try:
                effective = self.domain.effective(self.campaign["baseline"], overrides)
                config_id = config_identity(self.campaign, effective)
            except (ValueError, KeyError) as exc:
                trial.set_user_attr("rejection", f"invalid_domain:{exc}")
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                continue
            if config_id in seen:
                trial.set_user_attr("rejection", "duplicate_effective_config")
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                continue
            proposal_id = f"optuna-{trial.number:05d}"
            trial.set_user_attr("proposal_id", proposal_id)
            trial.set_user_attr("config_id", config_id)
            trial.set_user_attr("effective", effective)
            self._pending[proposal_id] = trial
            return CandidateProposal(
                proposal_id=proposal_id, parameters=overrides,
                experiment_kind="exploration",
                hypothesis="Explore admitted vLLM serving settings using Optuna NSGA-II",
                expected_tradeoff="Measure output throughput against chat/long-prefill latency",
                predictions=[{"observation": "mixed workload throughput and p90 latency",
                              "expected_change": "unknown; sampler exploration",
                              "scope": "frozen mixed development screen"}],
                falsification_condition="Invalid accounting, failed boot, or dominated measured result",
            )
        raise ValueError("Optuna could not find a distinct valid configuration in 48 asks")

    def complete(self, proposal: CandidateProposal, cells: list[dict[str, Any]],
                 baselines: list[dict[str, Any]], disposition: str) -> None:
        trial = self._pending.pop(proposal.proposal_id, None)
        if trial is None:
            raise ValueError(f"missing Optuna trial for {proposal.proposal_id}")
        trial.set_user_attr("disposition", disposition)
        trial.set_user_attr("cell_ids", [cell.get("cell_id") for cell in cells])
        if disposition != "valid" or not cells or any(not eligible(cell) for cell in cells):
            self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
            self._record(proposal, trial, cells, None, "failed_or_ineligible")
            return
        by_scope = {_scope(cell): cell for cell in baselines if eligible(cell)}
        throughput_ratios: list[float] = []
        latency_ratios: list[float] = []
        quantiles: list[str] = []
        for cell in cells:
            baseline = by_scope.get(_scope(cell))
            if baseline is None:
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                self._record(proposal, trial, cells, None, "missing_matched_baseline")
                return
            cm, bm = cell["metrics"], baseline["metrics"]
            quantile = "p90" if all(f"{metric}_p90_ms" in row for row in (cm, bm)
                                    for metric in ("ttft", "tpot")) else "p99"
            if quantile == "p99" and self.backend == "real":
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                self._record(proposal, trial, cells, None, "missing_p90_for_real_trial")
                return
            denominators = [bm["output_tokens_per_s"],
                            bm[f"ttft_{quantile}_ms"], bm[f"tpot_{quantile}_ms"]]
            if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
                   for value in denominators):
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                self._record(proposal, trial, cells, None, "invalid_baseline_denominator")
                return
            vals = [cm["output_tokens_per_s"] / bm["output_tokens_per_s"]]
            vals.extend(cm[f"{metric}_{quantile}_ms"] / bm[f"{metric}_{quantile}_ms"]
                        for metric in ("ttft", "tpot"))
            if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
                   for value in vals):
                self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
                self._record(proposal, trial, cells, None, "invalid_objective_denominator")
                return
            throughput_ratios.append(vals[0])
            latency_ratios.extend(vals[1:])
            quantiles.append(quantile)
        values = [math.exp(sum(math.log(value) for value in throughput_ratios) /
                           len(throughput_ratios)), max(latency_ratios)]
        trial.set_user_attr("quantiles", quantiles)
        trial.set_user_attr("throughput_ratios", throughput_ratios)
        trial.set_user_attr("latency_ratios", latency_ratios)
        self._record(proposal, trial, cells, values, "complete")
        self.study.tell(trial, values)

    def fail_pending(self, reason: str) -> None:
        for proposal_id, trial in list(self._pending.items()):
            trial.set_user_attr("failure_reason", reason[:500])
            self.study.tell(trial, state=self.optuna.trial.TrialState.FAIL)
            self._pending.pop(proposal_id)

    def _record(self, proposal: CandidateProposal, trial: Any, cells: list[dict[str, Any]],
                values: list[float] | None, status: str) -> None:
        self.ledger.append(self.campaign["campaign_id"], "optimizer_feedback", proposal.proposal_id,
                           {"proposal_id": proposal.proposal_id, "trial_number": trial.number,
                            "values": values, "status": status,
                            "cell_ids": [cell.get("cell_id") for cell in cells],
                            "study_path": str(self.storage_path)})


def _scope(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(key, "")) for key in
                 ("scenario_id", "offered_load", "load_unit", "cache_protocol",
                  "stage", "measurement_protocol"))

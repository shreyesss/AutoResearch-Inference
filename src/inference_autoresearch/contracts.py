"""Shared public DTOs for the controller, workload, runtime and evaluator adapters.

The frozen wire contracts remain the JSON schemas in the handoff. These small DTOs
make dependencies explicit without assigning experimental authority to a proposer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


def as_json(value: Any) -> dict[str, Any]:
    """Return JSON-compatible dataclass fields with Paths rendered as strings."""
    def convert(item: Any) -> Any:
        if isinstance(item, Path):
            return str(item)
        if isinstance(item, dict):
            return {str(k): convert(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [convert(v) for v in item]
        return item
    return convert(asdict(value))


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    raw: dict[str, Any]
    path: Path | None = None
    backend: str = "mock"


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CharacterizationReport:
    report_id: str
    status: str
    artifacts: dict[str, str] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    source_id: str = ""
    suite_role: str = "diagnostic"
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioManifest:
    scenario_id: str
    workload_id: str = ""
    path: Path | None = None
    group_id: str = ""
    offered_load: float | None = None
    load_unit: str = "requests_per_s"
    expected_count: int = 0
    output_policy: str = "forced_length"
    traffic_mode: str = "independent_open_loop"
    history_mode: str = "single_turn"
    cache_protocol: str = "cold_stream"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateProposal:
    proposal_id: str
    parameters: dict[str, Any]
    schema_version: str = "0.2"
    experiment_kind: str = "hypothesis"
    hypothesis: str = ""
    expected_tradeoff: str = ""
    predictions: list[dict[str, Any]] = field(default_factory=list)
    falsification_condition: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    parent_configuration_ids: list[str] = field(default_factory=list)
    requested_observations: list[str] = field(default_factory=list)

    @property
    def parent_ids(self) -> list[str]:
        return self.parent_configuration_ids


@dataclass(frozen=True)
class ResolvedServeConfig:
    config_id: str
    argv: list[str] = field(default_factory=list)
    effective_settings: dict[str, Any] = field(default_factory=dict)
    model_pins: dict[str, Any] = field(default_factory=dict)
    image_digest: str = ""
    env: dict[str, str] = field(default_factory=dict)
    feasibility: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerHandle:
    server_id: str
    base_url: str
    config_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def origin_url(self) -> str:
        return self.base_url


@dataclass(frozen=True)
class MeasurementPolicy:
    stage: str
    replicate: int = 1
    window_s: float = 60.0
    deadline_s: float = 180.0
    min_eligible: int = 0
    cache_protocol: str = "cold_stream"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CellResult:
    cell_id: str
    scenario_id: str
    config_id: str
    status: str
    behavior: str = "unknown"
    evidence_grade: str = "provisional"
    counts: dict[str, int] = field(default_factory=dict)
    metrics: dict[str, float | None] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_id: str
    config_id: str
    stage: str
    cell_ids: list[str] = field(default_factory=list)
    status: str = "incomplete"
    failure_reasons: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProposalContext:
    campaign_id: str
    mission: str
    domain: dict[str, Any]
    baseline: dict[str, Any]
    frontier: list[dict[str, Any]]
    recent_results: list[dict[str, Any]]
    evidence_refs: list[dict[str, Any]]
    remaining_budget: dict[str, Any]
    qualification: dict[str, Any]


@dataclass(frozen=True)
class CampaignResult:
    campaign_id: str
    stop_reason: str
    tested_count: int
    proposed_count: int
    archive_paths: dict[str, str] = field(default_factory=dict)


class TraceCharacterizer(Protocol):
    def characterize(self, spec: SourceSpec, output_dir: Path) -> CharacterizationReport: ...


class WorkloadBuilder(Protocol):
    def build(self, spec: WorkloadSpec, output_dir: Path) -> ScenarioManifest: ...


class BenchmarkAdapter(Protocol):
    def run_cell(self, server: ServerHandle, scenario: ScenarioManifest,
                 policy: MeasurementPolicy, output_dir: Path) -> CellResult: ...


class RuntimeManager(Protocol):
    def inspect_hardware(self) -> dict[str, Any]: ...
    def start(self, config: ResolvedServeConfig, output_dir: Path) -> ServerHandle: ...
    def stop(self, handle: ServerHandle) -> None: ...


class Evaluator(Protocol):
    def evaluate(self, candidate: CandidateProposal, scenario_ids: list[str],
                 stage: str) -> EvaluationResult: ...


class Proposer(Protocol):
    def propose(self, context: ProposalContext) -> CandidateProposal: ...

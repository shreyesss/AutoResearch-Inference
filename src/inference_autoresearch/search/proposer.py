"""Schema-bound Codex CLI proposal driver and explicitly labeled deterministic mock."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import CandidateProposal, ProposalContext
from .domain import Domain


class ProposerError(RuntimeError):
    pass


def _write_snapshot(path: Path, content: bytes) -> str:
    """Write a controller-owned research input and return its content digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ProposerError(f"research snapshot changed: {path}")
        return digest
    path.write_bytes(content)
    path.chmod(0o444)
    return digest


def _stage_previous_attempts(proposal_root: Path, run_dir: Path) -> list[dict[str, Any]]:
    """Copy bounded prior research artifacts; never mount old writable attempts."""
    history = []
    for previous in sorted(proposal_root.glob("attempt-[0-9][0-9][0-9][0-9]"))[-12:]:
        if previous == run_dir or not previous.is_dir() or previous.is_symlink():
            continue
        record = {"attempt": previous.name, "files": []}
        for relative in ("workspace/notes.md", "proposal.normalized.json", "proposer-receipt.json"):
            source = previous / relative
            if not source.is_file() or source.is_symlink():
                continue
            content = source.read_bytes()
            if len(content) > 65536:
                record["files"].append({"source": relative, "omitted": "over_64_kib"})
                continue
            target = run_dir / "history" / previous.name / Path(relative).name
            digest = _write_snapshot(target, content)
            record["files"].append({"path": str(target.relative_to(run_dir)), "sha256": digest,
                                    "bytes": len(content)})
        history.append(record)
    return history


_CELL_RESEARCH_FILES = (
    "cell-result.json", "cell-result-v02.json", "controller-validation.json", "timing.json",
    "aiperf/normalized-requests.jsonl", "aiperf/profile_export.jsonl",
    "aiperf/profile_export_aiperf.json", "aiperf/profile_export_aiperf.csv",
    "aiperf/server_metrics_export.csv", "aiperf/server_metrics_export.json",
    "aiperf/profile_export_console.txt", "aiperf/workload-class-summaries.json",
    "aiperf/aiperf-console.log", "aiperf/aiperf-argv.json", "aiperf/aiperf-exit.json",
    "server/server.log", "server/startup.log", "server/telemetry.jsonl",
    "server/requested-config.json", "server/resolved-startup.json", "server/hardware.json",
)
_EVALUATION_RESEARCH_FILES = (
    "resolved-config.json", "evaluation-result.json", "proposal.json", "evaluation-policy.json",
)
_ADAPTIVE_RESEARCH_BASENAMES = {"normalized-search-points.json", "search_history.json"}


def _stage_measurements(context: ProposalContext, artifact_root: Path,
                        run_dir: Path) -> dict[str, Any]:
    """Expose only controller-recorded, non-heldout same-campaign run files."""
    root = artifact_root.resolve()
    rows = [row for row in context.recent_results if isinstance(row, dict)]
    for scope in context.frontier:
        if isinstance(scope, dict):
            rows.extend(row for row in scope.get("cells", []) if isinstance(row, dict))
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    budget = 128 * 1024 * 1024
    for row in rows:
        cell_id = str(row.get("cell_id", ""))
        stage = str(row.get("stage", ""))
        if not cell_id or cell_id in seen or not stage or any(
                marker in stage.lower() for marker in ("heldout", "sealed", "test")):
            continue
        seen.add(cell_id)
        artifacts = row.get("artifacts") or {}
        if not isinstance(artifacts, dict):
            artifacts = {}
        record = {"cell_id": cell_id, "stage": stage, "scenario_id": row.get("scenario_id"),
                  "config_id": row.get("config_id"), "measurement_protocol": row.get("measurement_protocol"),
                  "offered_load": row.get("offered_load"), "load_unit": row.get("load_unit"),
                  "matched_baseline_cell_id": row.get("matched_baseline_cell_id"),
                  "evidence_grade": row.get("evidence_grade", "ungraded"),
                  "metrics": row.get("metrics", {}), "counts": row.get("counts", {}),
                  "status": row.get("status"), "behavior": row.get("behavior"),
                  "reason_codes": row.get("reason_codes", []),
                  "uncertainty": row.get("uncertainty", "unavailable"),
                  "files": [], "omitted": []}
        for label, artifact_path in artifacts.items():
            if not isinstance(artifact_path, str) or Path(artifact_path).name not in _ADAPTIVE_RESEARCH_BASENAMES:
                continue
            adaptive_source = Path(artifact_path).resolve()
            if not adaptive_source.is_relative_to(root):
                record["omitted"].append({"artifact": label, "reason": "adaptive_artifact_outside_campaign"})
                continue
            budget = _copy_research_file(adaptive_source,
                                         run_dir / "measurements" / "adaptive" / f"record-{len(records):04d}"
                                         / adaptive_source.name, run_dir, record, budget)
        reference = artifacts.get("raw_requests") or artifacts.get("aiperf_export")
        if not isinstance(reference, str):
            record["omitted"].append({"reason": "no_raw_artifact_reference"})
            records.append(record)
            continue
        source = Path(reference).resolve()
        if not source.is_relative_to(root):
            record["omitted"].append({"reason": "raw_artifact_outside_campaign"})
            records.append(record)
            continue
        cell_dir = next((part for part in source.parents if part.name.startswith("cell-")
                         and part.parent.name.startswith("eval-")), None)
        if cell_dir is None or not cell_dir.is_relative_to(root):
            record["omitted"].append({"reason": "raw_artifact_not_in_cell"})
            records.append(record)
            continue
        evaluation_dir = cell_dir.parent
        destination = run_dir / "measurements" / evaluation_dir.name / cell_dir.name
        for relative in _CELL_RESEARCH_FILES:
            source_file = cell_dir / relative
            budget = _copy_research_file(source_file, destination / relative, run_dir,
                                         record, budget)
        for relative in _EVALUATION_RESEARCH_FILES:
            source_file = evaluation_dir / relative
            budget = _copy_research_file(source_file,
                                         run_dir / "measurements" / evaluation_dir.name / relative,
                                         run_dir, record, budget)
        records.append(record)
    result = {"cells": records, "file_size_limit_bytes": 16 * 1024 * 1024,
              "total_size_limit_bytes": 128 * 1024 * 1024,
              "scope": "controller-provided visible development cells; heldout/test excluded",
              "excluded": "Unlisted native raw exports, model weights and unrelated artifacts"}
    _write_snapshot(run_dir / "measurements-index.json", (json.dumps(result, indent=2) + "\n").encode())
    _write_snapshot(run_dir / "evaluation-index.json", (json.dumps({
        "schema_version": "evaluation-index-v1", "campaign_id": context.campaign_id,
        "cells": records, "visible_cell_count": len(records),
        "note": "Controller-provided development evidence only; source files listed with SHA-256 in files."
    }, indent=2) + "\n").encode())
    return result


def _copy_research_file(source: Path, destination: Path, run_dir: Path,
                        record: dict[str, Any], budget: int) -> int:
    if not source.is_file() or source.is_symlink():
        return budget
    size = source.stat().st_size
    relative = str(destination.relative_to(run_dir))
    if size > 16 * 1024 * 1024:
        record["omitted"].append({"path": relative, "reason": "file_over_16_mib", "bytes": size})
        return budget
    if size > budget:
        record["omitted"].append({"path": relative, "reason": "total_128_mib_budget", "bytes": size})
        return budget
    content = source.read_bytes()
    if len(content) != size:
        record["omitted"].append({"path": relative, "reason": "changed_while_staging"})
        return budget
    already_staged = destination.exists()
    digest = _write_snapshot(destination, content)
    record["files"].append({"path": relative, "sha256": digest, "bytes": size})
    return budget if already_staged else budget - size


def parse_proposal(raw: dict[str, Any], domain: Domain, allowed_evidence_ids: set[str]) -> CandidateProposal:
    from jsonschema import Draft202012Validator
    errors = sorted(Draft202012Validator(domain.proposal_schema()).iter_errors(raw), key=lambda x: list(x.path))
    if errors:
        raise ProposerError(f"proposal schema violation: {errors[0].message}")
    if raw.get("schema_version") != "0.2":
        raise ProposerError("proposal schema_version must be 0.2")
    allowed_keys = set(domain.proposal_schema()["properties"])
    if set(raw) != allowed_keys:
        raise ProposerError(f"proposal fields differ from contract: {sorted(set(raw) ^ allowed_keys)}")
    domain.validate(raw["parameters"])
    if not raw["proposal_id"] or not raw["falsification_condition"] or not raw["predictions"]:
        raise ProposerError("proposal ID, falsification and predictions are required")
    if not set(raw["evidence_ids"]).issubset(allowed_evidence_ids):
        raise ProposerError("proposal cites evidence outside allowlist")
    return CandidateProposal(
        proposal_id=raw["proposal_id"], parameters=raw["parameters"],
        parent_configuration_ids=raw["parent_configuration_ids"], hypothesis=raw["hypothesis"],
        expected_tradeoff=raw["expected_tradeoff"], evidence_ids=raw["evidence_ids"],
        experiment_kind=raw["experiment_kind"], predictions=raw["predictions"],
        falsification_condition=raw["falsification_condition"],
        requested_observations=raw["requested_observations"],
    )


def parse_codex_output(raw: dict[str, Any], domain: Domain,
                       allowed_evidence_ids: set[str]) -> CandidateProposal:
    """Validate strict model output, then normalize nullable overrides to v0.2."""
    from jsonschema import Draft202012Validator
    errors = sorted(Draft202012Validator(domain.codex_output_schema()).iter_errors(raw),
                    key=lambda x: list(x.path))
    if errors:
        raise ProposerError(f"Codex output schema violation: {errors[0].message}")
    sparse = dict(raw)
    sparse["parameters"] = {key: value for key, value in raw["parameters"].items()
                            if value is not None}
    return parse_proposal(sparse, domain, allowed_evidence_ids)


class CodexProposer:
    def __init__(self, domain: Domain, artifact_root: Path, timeout_s: int = 180,
                 skill_path: Path | None = None, cli: str = "codex",
                 expected_version: str | None = None, model: str | None = None,
                 reasoning_effort: str | None = None, web_search: str = "disabled"):
        self.domain = domain
        self.artifact_root = Path(artifact_root)
        self.timeout_s = timeout_s
        self.skill_path = Path(skill_path) if skill_path else Path(__file__).resolve().parents[3] / "agent" / "SKILL.md"
        self.cli = cli
        self.expected_version = expected_version
        if model is not None and (not model or any(c.isspace() for c in model)):
            raise ValueError("proposer model must be one nonempty model ID")
        if reasoning_effort not in (None, "low", "medium", "high", "xhigh", "max", "ultra"):
            raise ValueError("unsupported proposer reasoning effort")
        if web_search not in ("disabled", "cached", "indexed", "live"):
            raise ValueError("unsupported proposer web-search mode")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.web_search = web_search

    def propose(self, context: ProposalContext) -> CandidateProposal:
        binary = shutil.which(self.cli)
        if binary is None:
            raise ProposerError("Codex CLI unavailable; no fallback proposer")
        # Codex's own shell sandbox is unavailable inside the nested proposer.
        # The full-access mode below is safe only when the Docker wrapper is the
        # executable. Refuse a host Codex binary in the default real path.
        if self.cli == "codex":
            with open(binary, "rb") as executable:
                marker = executable.read(2048)
            if b"IAR_ISOLATED_CODEX_WRAPPER=1" not in marker:
                raise ProposerError("real Codex proposer requires the isolated Docker wrapper")
        env_keys = ("HOME", "CODEX_HOME", "PATH", "LANG", "LC_ALL", "HTTPS_PROXY", "HTTP_PROXY",
                    "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "IAR_REPO_ROOT",
                    "IAR_CODEX_HOME", "IAR_PROPOSER_IMAGE")
        env = {key: os.environ[key] for key in env_keys if key in os.environ}
        version = subprocess.run([binary, "--version"], capture_output=True, text=True,
                                 timeout=10, check=False, env=env)
        if version.returncode or "codex-cli" not in version.stdout:
            raise ProposerError(f"Codex CLI version check failed: {version.stderr[:300]}")
        if self.expected_version and self.expected_version not in version.stdout:
            raise ProposerError("Codex CLI version differs from campaign pin")
        auth = subprocess.run([binary, "login", "status"], capture_output=True, text=True,
                              timeout=15, check=False, env=env)
        if auth.returncode:
            raise ProposerError("Codex CLI authentication unavailable; no fallback proposer")
        proposal_root = self.artifact_root / "proposals"
        previous = [int(path.name.split("-")[-1]) for path in proposal_root.glob("attempt-*")
                    if path.name.split("-")[-1].isdigit()]
        run_dir = proposal_root / f"attempt-{max(previous, default=0) + 1:04d}"
        run_dir.mkdir(parents=True, exist_ok=False)
        workspace = run_dir / "workspace"
        workspace.mkdir(mode=0o777)
        workspace.chmod(0o777)
        schema_file = run_dir / "proposal.schema.json"
        final_file = run_dir / "proposal.final.json"
        event_file = run_dir / "codex.events.jsonl"
        stderr_file = run_dir / "codex.stderr.txt"
        input_file = run_dir / "context.json"
        _write_snapshot(schema_file, (json.dumps(self.domain.codex_output_schema(), indent=2) + "\n").encode())
        skill = self.skill_path.read_text()
        reference = self.skill_path.with_name("reference.md").read_text()
        _write_snapshot(run_dir / "SKILL.md", skill.encode())
        _write_snapshot(run_dir / "reference.md", reference.encode())
        retrieval_audit = []
        staged_refs = []
        evidence_dir = run_dir / "evidence"
        evidence_dir.mkdir()
        for ref in context.evidence_refs:
            path = Path(ref.get("snapshot_path", ""))
            if not path.is_file():
                continue
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != ref.get("sha256"):
                raise ProposerError(f"evidence changed: {ref.get('evidence_id')}")
            evidence_id = str(ref["evidence_id"])
            if not evidence_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in evidence_id):
                raise ProposerError("unsafe evidence ID")
            staged = evidence_dir / f"{evidence_id}.txt"
            _write_snapshot(staged, data)
            staged_refs.append({"evidence_id": ref["evidence_id"], "source_sha256": ref["sha256"],
                                "path": str(staged.relative_to(run_dir)), "bytes": len(data)})
            retrieval_audit.append({"evidence_id": ref["evidence_id"], "bytes": len(data),
                                    "sha256": ref["sha256"], "path": str(staged.relative_to(run_dir))})
        context_payload = asdict(context)
        context_payload["evidence_refs"] = staged_refs
        _write_snapshot(input_file, (json.dumps(context_payload, indent=2, default=str) + "\n").encode())
        _write_snapshot(run_dir / "retrieval-audit.json", (json.dumps(retrieval_audit, indent=2) + "\n").encode())
        (run_dir / "history").mkdir()
        history = _stage_previous_attempts(proposal_root, run_dir)
        measurements = _stage_measurements(context, self.artifact_root, run_dir)
        research_index = {
            "current": {"skill": "../SKILL.md", "reference": "../reference.md",
                        "context": "../context.json", "evidence": "../evidence/",
                        "schema": "../proposal.schema.json",
                        "measurements": "../measurements-index.json",
                        "evaluation": "../evaluation-index.json"},
            "previous_attempts": history,
            "measurement_cells": len(measurements["cells"]),
            "writable_notes": "notes.md",
            "authority": "Only parameter proposals; the controller owns traffic and evaluation.",
        }
        _write_snapshot(run_dir / "research-index.json", (json.dumps(research_index, indent=2) + "\n").encode())
        # The isolated proposer runs as uid 1000 while the controller may run as
        # root. Codex writes its last message itself, so pre-create only that
        # output as writable; keep the staged inputs and directory read-only to it.
        final_file.touch()
        final_file.chmod(0o666)
        prompt = ("You are the serving autoresearch proposer. First read ../SKILL.md and "
                  "../reference.md. Inspect ../research-index.json and ../context.json; open "
                  "the staged evidence under ../evidence/, prior notes under ../history/, "
                  "and scoped real-run files listed by ../evaluation-index.json and ../measurements-index.json. "
                  "Use shell/file reads freely inside this isolated research container. "
                  "Write any durable reasoning for the next attempt to notes.md here. "
                  "Return exactly one JSON proposal matching ../proposal.schema.json. "
                  "The controller alone validates and evaluates it.")
        argv = [binary, "exec", "--sandbox", "danger-full-access", "--skip-git-repo-check",
                "--ignore-user-config", "--ephemeral", "--json"]
        if self.model:
            argv.extend(("--model", self.model))
        if self.reasoning_effort:
            argv.extend(("--config", f'model_reasoning_effort="{self.reasoning_effort}"'))
        argv.extend(("--config", f'web_search="{self.web_search}"', "--cd", str(workspace),
                     "--output-schema", str(schema_file), "--output-last-message", str(final_file), "-"))
        receipt_file = run_dir / "proposer-receipt.json"
        receipt = {"driver": "codex-cli", "version": version.stdout.strip(), "argv": argv,
                   "model": self.model, "reasoning_effort": self.reasoning_effort,
                   "web_search": self.web_search,
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "skill_sha256": hashlib.sha256(skill.encode()).hexdigest(),
                   "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
                   "schema_sha256": hashlib.sha256(schema_file.read_bytes()).hexdigest(),
                   "sandbox": "docker-isolated-research-workspace", "cwd": str(workspace),
                   "research_index": str(run_dir / "research-index.json"),
                   "staged_evidence_count": len(staged_refs),
                   "staged_measurement_cells": len(measurements["cells"]),
                   "staged_measurement_files": sum(len(cell["files"]) for cell in measurements["cells"]),
                   "previous_attempts": len(history),
                   "status": "started"}
        receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
        try:
            with event_file.open("w") as event_out, stderr_file.open("w") as err_out:
                process = subprocess.run(argv, input=prompt, stdout=event_out, stderr=err_out,
                                         text=True, timeout=self.timeout_s, check=False, env=env)
        except subprocess.TimeoutExpired as exc:
            receipt["status"] = "timeout"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex proposer timed out after {self.timeout_s}s; events={event_file}") from exc
        receipt["exit_code"] = process.returncode
        if process.returncode:
            receipt["status"] = "failed"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex proposer failed exit={process.returncode}; stderr={stderr_file}")
        if not final_file.exists() or not final_file.stat().st_size:
            receipt["status"] = "missing_final"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex returned no final JSON; events={event_file}")
        try:
            raw = json.loads(final_file.read_text())
        except (ValueError, OSError) as exc:
            receipt["status"] = "invalid_final_json"
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise ProposerError(f"Codex final response is not JSON: {final_file}") from exc
        # The qualification report's immutable scenario and B0 cell IDs are
        # exposed in context.json and backed by staged measurement files.
        # Accept those citations as well as the separately staged documents.
        allowed = {str(ref["evidence_id"]) for ref in staged_refs}
        allowed.update(item for item in context.qualification.get("evidence_ids", [])
                       if isinstance(item, str))
        allowed.update(item["cell_id"] for item in measurements["cells"]
                       if isinstance(item.get("cell_id"), str))
        try:
            proposal = parse_codex_output(raw, self.domain, allowed)
        except (ProposerError, ValueError) as exc:
            receipt["status"] = "invalid_proposal"
            receipt["validation_error"] = str(exc)
            receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
            raise
        normalized_file = run_dir / "proposal.normalized.json"
        normalized_tmp = run_dir / "proposal.normalized.json.tmp"
        normalized_bytes = (json.dumps(asdict(proposal), indent=2, sort_keys=True) + "\n").encode()
        normalized_tmp.write_bytes(normalized_bytes)
        os.replace(normalized_tmp, normalized_file)
        receipt["status"] = "validated"
        receipt["proposal_sha256"] = hashlib.sha256(final_file.read_bytes()).hexdigest()
        receipt["normalized_proposal_path"] = str(normalized_file)
        receipt["normalized_proposal_sha256"] = hashlib.sha256(normalized_bytes).hexdigest()
        receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")
        return proposal


class MockProposer:
    """Deterministic contract test driver; never silently used for real search."""

    def __init__(self, domain: Domain):
        self.domain = domain
        self.index = 0

    def propose(self, context: ProposalContext) -> CandidateProposal:
        axes = self.domain.raw["parameters"]
        options = [(key, value) for key, spec in axes.items() if spec.get("active") is not False for value in spec["values"]
                   if value != spec["baseline"]]
        if self.index >= len(options):
            raise ProposerError("mock proposal domain exhausted")
        key, value = options[self.index]
        self.index += 1
        return CandidateProposal(
            proposal_id=f"mock-{self.index:03d}", parameters={key: value},
            experiment_kind="exploration", hypothesis=f"Exercise {key}={value} in mock mode",
            expected_tradeoff="Contract test only; no performance claim",
            predictions=[{"observation": key, "expected_change": "mock cell completes",
                          "scope": "mock evaluator"}],
            falsification_condition="Mock evaluator rejects the candidate",
        )

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
                 expected_version: str | None = None):
        self.domain = domain
        self.artifact_root = Path(artifact_root)
        self.timeout_s = timeout_s
        self.skill_path = Path(skill_path) if skill_path else Path(__file__).resolve().parents[3] / "agent" / "SKILL.md"
        self.cli = cli
        self.expected_version = expected_version

    def propose(self, context: ProposalContext) -> CandidateProposal:
        binary = shutil.which(self.cli)
        if binary is None:
            raise ProposerError("Codex CLI unavailable; no fallback proposer")
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
        schema_file = run_dir / "proposal.schema.json"
        final_file = run_dir / "proposal.final.json"
        event_file = run_dir / "codex.events.jsonl"
        stderr_file = run_dir / "codex.stderr.txt"
        input_file = run_dir / "context.json"
        schema_file.write_text(json.dumps(self.domain.codex_output_schema(), indent=2) + "\n")
        skill = self.skill_path.read_text()
        reference = self.skill_path.with_name("reference.md").read_text()
        (run_dir / "SKILL.md").write_text(skill)
        (run_dir / "reference.md").write_text(reference)
        excerpts = []
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
            clipped = data[:12000]
            staged = evidence_dir / f"{ref['evidence_id']}.txt"
            staged.write_bytes(clipped)
            staged_refs.append({"evidence_id": ref["evidence_id"], "source_sha256": ref["sha256"],
                                "excerpt_path": str(staged), "excerpt_bytes": len(clipped),
                                "truncated": len(clipped) < len(data)})
            excerpts.append(f"EVIDENCE {ref['evidence_id']} sha256={ref['sha256']}\n"
                            + clipped[:3000].decode("utf-8", errors="replace"))
            retrieval_audit.append({"evidence_id": ref["evidence_id"], "bytes": len(clipped),
                                    "sha256": ref["sha256"], "excerpt_path": str(staged)})
        context_payload = asdict(context)
        context_payload["evidence_refs"] = staged_refs
        input_file.write_text(json.dumps(context_payload, indent=2, default=str) + "\n")
        (run_dir / "retrieval-audit.json").write_text(json.dumps(retrieval_audit, indent=2) + "\n")
        # The isolated proposer runs as uid 1000 while the controller may run as
        # root. Codex writes its last message itself, so pre-create only that
        # output as writable; keep the staged inputs and directory read-only to it.
        final_file.touch()
        final_file.chmod(0o666)
        prompt = (skill + "\n\n" + reference + "\n\nFROZEN PROPOSAL CONTEXT:\n"
                  + input_file.read_text() + "\n\nALLOWLISTED SOURCE EXCERPTS:\n"
                  + "\n\n".join(excerpts) + "\nReturn exactly one schema-valid JSON proposal.")
        argv = [binary, "exec", "--sandbox", "read-only", "--skip-git-repo-check",
                "--ignore-user-config", "--ephemeral", "--json", "--cd", str(run_dir),
                "--output-schema", str(schema_file), "--output-last-message", str(final_file), "-"]
        receipt_file = run_dir / "proposer-receipt.json"
        receipt = {"driver": "codex-cli", "version": version.stdout.strip(), "argv": argv,
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "skill_sha256": hashlib.sha256(skill.encode()).hexdigest(),
                   "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
                   "schema_sha256": hashlib.sha256(schema_file.read_bytes()).hexdigest(),
                   "sandbox": "read-only", "cwd": str(run_dir), "status": "started"}
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
        allowed = {str(ref["evidence_id"]) for ref in context.evidence_refs}
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

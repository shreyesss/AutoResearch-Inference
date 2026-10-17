#!/usr/bin/env python3
"""Exercise only the isolated Codex proposer. No vLLM, GPU or evaluator calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from inference_autoresearch.contracts import ProposalContext
from inference_autoresearch.search.domain import Domain
from inference_autoresearch.search.evidence import EvidenceStore
from inference_autoresearch.search.proposer import CodexProposer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    root = args.repo.resolve()
    campaign = json.loads((root / "configs/campaign.json").read_text())
    domain = Domain.load(root / campaign["search_domain_path"])
    out = root / ".artifacts/proposer-smoke"
    evidence = EvidenceStore(root, out / "evidence").snapshot()
    context = ProposalContext(
        campaign_id=campaign["campaign_id"],
        mission="Proposer integration smoke only. Return one schema-valid proposal; no evaluation will run.",
        domain=domain.raw, baseline=campaign["baseline"], frontier=[], recent_results=[],
        evidence_refs=evidence, remaining_budget={"distinct_proposals": 1, "wall_seconds": args.timeout},
        qualification={"search_allowed": False, "reason": "proposer-only smoke; real campaign gate closed"},
    )
    proposal = CodexProposer(domain, out, timeout_s=args.timeout,
                             skill_path=root / "agent/SKILL.md",
                             expected_version=campaign["runtime"]["codex_cli_version_observed"]).propose(context)
    print(json.dumps({"status": "proposer_only_no_evaluation", "proposal_id": proposal.proposal_id,
                      "sparse_parameters": proposal.parameters, "evidence_ids": proposal.evidence_ids},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

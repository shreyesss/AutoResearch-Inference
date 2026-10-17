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
from inference_autoresearch.storage import Ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--campaign", type=Path, default=Path("configs/campaign.json"))
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output-dir", type=Path,
                        help="Isolated proposer smoke artifacts; no evaluator or GPU work")
    parser.add_argument("--real-artifact-root", type=Path,
                        help="Existing real campaign artifact directory; stage its recorded cells for a proposer-only smoke.")
    args = parser.parse_args()
    root = args.repo.resolve()
    campaign = json.loads((root / args.campaign).read_text())
    domain = Domain.load(root / campaign["search_domain_path"])
    out = (args.real_artifact_root.resolve() if args.real_artifact_root else
           (args.output_dir or root / ".artifacts/proposer-smoke").resolve())
    if not out.is_relative_to(root / ".artifacts"):
        raise ValueError("proposer smoke output must stay under .artifacts")
    recent = []
    if args.real_artifact_root:
        ledger_path = out / "ledger.sqlite3"
        if not ledger_path.is_file() or not out.is_relative_to(root / ".artifacts"):
            raise ValueError("real artifact root must be an existing campaign directory under .artifacts")
        heldout_ids = set(campaign.get("heldout_scenario_ids", []))
        recent = [event["payload"] for event in Ledger(ledger_path).events(campaign["campaign_id"], "cell")
                  if event["payload"].get("scenario_id") not in heldout_ids
                  and "heldout" not in str(event["payload"].get("stage", "")).lower()]
    evidence = EvidenceStore(root, out / "evidence",
                             sources=campaign.get("evidence_sources")).snapshot()
    context = ProposalContext(
        campaign_id=campaign["campaign_id"],
        mission="Proposer integration smoke only. Return one schema-valid proposal; no evaluation will run.",
        domain=domain.raw, baseline=campaign["baseline"], frontier=[], recent_results=recent[-12:],
        evidence_refs=evidence, remaining_budget={"distinct_proposals": 1, "wall_seconds": args.timeout},
        qualification={"search_allowed": False, "reason": "proposer-only smoke; no evaluator calls"},
    )
    proposer_config = campaign.get("proposer", {})
    proposal = CodexProposer(domain, out, timeout_s=args.timeout,
                             skill_path=root / "agent/SKILL.md",
                             expected_version=campaign["runtime"]["codex_cli_version_observed"],
                             model=proposer_config.get("model"),
                             reasoning_effort=proposer_config.get("reasoning_effort"),
                             web_search=proposer_config.get("web_search", "disabled")).propose(context)
    print(json.dumps({"status": "proposer_only_no_evaluation", "proposal_id": proposal.proposal_id,
                      "sparse_parameters": proposal.parameters, "evidence_ids": proposal.evidence_ids},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

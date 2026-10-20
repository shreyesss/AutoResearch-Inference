# Three-tool verification — 20 October 2026

Latest changes, caching checks and corrected MoE run: [current verified state](CURRENT_STATE.md). The earlier runs and timestamped corpus snapshot below are preserved as history.

## Environment

Deployed to `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/ideation`.

- Python 3.12, isolated `.venv-research`.
- DiscoveryRSI pinned commit imports successfully; PyAlex, JSON Schema and pypdf installed.
- Resolved environment: [research-environment.txt](research-environment.txt).
- Tools are callable individually through `python -m ideation tool NAME --args JSON`.
- OpenAlex was subsequently configured from the supplied key; live search and forward/backward citations passed. See [provider integration](FATHOM_INTEGRATION.md). PaperQA model/embedding credentials remain unconfigured; no paid PaperQA inference is claimed.

## Tests

29 unit tests passed on the VM: nine corpus tests, eleven hypothesis/domain tests, two provider/evidence boundary tests, five cache/budget tests and two cheap-helper tests:

- High rubric scores cannot override a failed critic gate.
- HF/abstract/full-text mirrors count as one paper.
- Fabricated quotations and inadequate prior-art retrieval fail selection.
- Missing competing explanation or inconclusive criterion fails selection.
- Out-of-range reviewer scores fail schema validation.
- Passing only grants eligibility for test design; exact repeated mechanisms are flagged.
- Repository scope is applied before search limiting.
- Publication date windows exclude unknown dates and the exclusive upper bound.
- Generated discovery output cannot serve as primary evidence or enter the evidence extractor.
- Provider loading preserves existing values and does not interpolate or export unrelated secrets.
- HTML and browser extractions of the same web page count as one source.
- Identical concurrent cache misses produce one fetch; expiry and forced refresh work.
- Provider budgets are atomic and count failed attempts; Serper repeats with different display limits reuse the same result.
- The helper rejects invented URLs and invalidates results when source text changes.
- Cited source passages survive excerpt truncation before critique.

```bash
.venv-research/bin/python -m unittest discover -s tests -v
```

The original vLLM paper `2309.06180v1` was fetched as HTML and explicitly as PDF. The PDF path produced 82,136 characters through pypdf, with page markers and raw SHA-256 recorded. This verifies text extraction, not figure/table interpretation.

## Live run

Artifacts: [three-tools-002](../runs/three-tools-002/), especially:

- [Evidence packet](../runs/three-tools-002/evidence/packet.json)
- [Prior-art retrieval](../runs/three-tools-002/hypotheses/prior-art-1.json)
- [Critique](../runs/three-tools-002/hypotheses/critique-1.json)
- [Decision](../runs/three-tools-002/hypotheses/decision.md)
- [Run manifest](../runs/three-tools-002/hypotheses/manifest.json)
- [DiscoveryRSI replay](../runs/three-tools-002/hypotheses/episodes.jsonl)

The run made live GitHub-corpus searches, arXiv/HF queries and an SSD full-text read. Eight source records yielded ten evidence claims. The first attempt (`three-tools-001`) stopped because a rendered Markdown-link quotation did not exist verbatim in the source. A bounded quote-repair pass was added; the second run retained its initial errors and repair artifact and passed quote checks.

The hypothesis stage ran 03:35:54–03:36:55 IST. It proposed one mechanism against a requested count of two. Zero passed selection. The proposed bounded asynchronous speculation cache overlapped retrieved vLLM RFC #42109; the critic also questioned state/accounting correctness, equal-resource comparison and resource feasibility. The paper's measured gains were not treated as B200/vLLM results.

This establishes a functioning evidence → proposal → retrieved prior art → critique → no-selection path. It does not establish novel optimization discovery, hypothesis ranking quality, or measured serving improvement. No GPU experiment was run. Unit tests exercise the eligible branch; this live run did not produce an eligible card.

After inspecting the critique, the prompt was clarified: entailment applies to reported facts, while predictions remain untested; an unmeasured bottleneck can itself be a first-test question. The session's no-GPU constraint does not prohibit proposing a later experiment. These prompt clarifications have not been benchmarked in another live run. Selection gates were not relaxed to force a positive result.

## Remaining practical limits

The default evidence extractor uses bounded source excerpts; the caller should inspect full records and relevant code before promoting a proposal to implementation. Cross-engine prior-art coverage, independent human review, historical backtests and actual GPU experiment feedback remain unverified. Keyed OpenAlex citation expansion now has a live check. Collector comment completeness is a separate existing issue, not resolved by this tool refactor.

## Corpus status — 03:55 IST, October 20

The initial issue endpoint pass, which includes PR opening bodies, completed at 03:32:09 IST. At this snapshot the corpus contains 19,138 issues and 42,577 PRs. The separate PR metadata pass has completed 122 pages (12,200 PR records) and is continuing at page 123. Bulk issue comments and review comments have not started; 20 comments and two formal reviews come from earlier targeted hydration.

This is not a claim of a fully reconciled archive: GitHub's live PR count remained ahead of the corpus during checks, including new PRs created after the body pass ended. Metadata enumeration and subsequent incremental passes are still required. Formal reviews and file patches remain selective, on-demand downloads. Exact checkpoints and counts: [corpus-status-latest.json](corpus-status-latest.json).

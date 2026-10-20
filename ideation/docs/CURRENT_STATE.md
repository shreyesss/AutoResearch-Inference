# Verified state — October 20, 2026

## H200 rerun — live deployment inspected

[H200 report](../runs/h200-pr-evaluation-audit-001/REPORT.md) · [26 experiment designs](../runs/h200-pr-evaluation-audit-001/EXPERIMENT_INDEX.md) · [Full disposition ledger](../runs/h200-pr-evaluation-audit-001/PR_DISPOSITIONS.csv) · [Observed baseline](../runs/h200-pr-evaluation-audit-001/BASELINE.md).

User selected the actual running layout on `217.18.55.219`: eight H200s in two TP1/DP4/EP4 groups, DSpark k5, seq64, MBT16384, graph cap512. SSH inspection found Marlin selected for MoE. Small-head TP4 kernels and TP4 padding savings are outside this layout; Blackwell-only Engram fusion is held.

All 5,532 catalog identities were mechanically reclassified; 73 primary snapshots and 27 complete changed-file lists were retrieved. This is targeted source review plus a full triage ledger, not full implementation review of every item. There are 16 ranked live-layout hypotheses, three exploratory integrations, three topology alternatives and four correctness gates. Eight cached keyword/date queries returned results from a 92,050-document controller corpus; this count includes document kinds and is not a claim of 92,050 PRs.

Registered 26 conditional hypotheses and planned tests, with 18 B200-parent links. Exact source quotes and card schemas passed validation. No GPU test, speedup, image build or deployment was produced. At 12:27 UTC, both containers were running but still logging weight loading and their host health ports refused connections. The native sweep launcher still hardcodes B200 paths and needs an H200 adapter before execution. Readiness and the adapter are explicit execution prerequisites.


## Supplied PR catalog → B200 evaluation audit

[Report](../runs/pr-evaluation-audit-001/REPORT.md) · [5,532-row disposition ledger](../runs/pr-evaluation-audit-001/PR_DISPOSITIONS.csv) · [Ranked PRs](../runs/pr-evaluation-audit-001/RANKED_PRS.csv) · [23 experiment plans](../runs/pr-evaluation-audit-001/EXPERIMENT_INDEX.md) · [Existing evaluator source audit](../runs/pr-evaluation-audit-001/evaluation/EVALUATION_CAPABILITIES.md).

All input rows were triaged; 94 items received primary-source review, yielding 64 candidate/dependency records and 30 exclusions/holds. Another 1,089 items remain explicitly deferred for source review. This is a complete triage ledger, not a claim that every body/diff was independently reviewed. The source catalog's B300/v0.32 assumptions differ from the actual configured B200 image (`ac9126e…`).

The existing synthetic and Mooncake performance evaluations are retained. Additional checks are limited to demonstrated gaps such as sampling distributions, kernel numerical correctness, actual tool-turn encoding and lifecycle timing. Three specialist tracks and a final kernel applicability review informed the designs. No proposal/critic model loop was invoked for this audit.

Registered 23 agent-authored hypotheses and 23 planned tests through the existing memory API; all selection statuses are deferred pending runtime applicability. Exact quotes and card schemas passed validation. This run has 23 produced, 23 reviewed and 23 test-planned events, with no test-start/result events. No GPU run, source patch, image build or deployment occurred.

## Multi-agent B200 exploration — 05:07 IST

[Full report](../runs/frontier-exploration-001/REPORT.md) · [Six experiment designs](../runs/frontier-exploration-001/experiment-bundle.json) · [Evaluation protocol](../runs/frontier-exploration-001/EVALUATION_PROTOCOL.md) · [Verification](../runs/frontier-exploration-001/verification.json).

Three subagents ran32 recorded local keyword queries, seven distinct full-paper reads, pinned-code inspections, evidence extraction and hypothesis reviews. Six latest designs are **deferred pending concrete baseline/safety/backend prerequisites**. Prior rejection/repair ancestry is preserved. The strongest first investigations are warm-prefix overload escape, pressure-aware prefill admission, and schedulable mixed-shape verification calibration.

Memory now has104 proposal/revision/partial-lead records,306 events and8 **planned** tests (six consolidated plans plus two earlier routing drafts). Zero GPU experiments or result events for this exploration. Read-only access attempts found both configured B200 hosts terminated; archived reports/configs do not establish a live deployment.

The audit also distinguishes strict AIPerf goodput from the campaign's length-aware score and checks exact token lengths across the historical frontier. All six plans include controls, causal ablations, instrumentation, metrics, correctness/quality guards, proposed statistical rules and bounded stage budgets. Input hashes and global IDs verified after sync.

## Adaptive policy and hypothesis memory — 04:50 IST

Implemented and deployed: [task-derived rubric and memory](ADAPTIVE_POLICY_AND_MEMORY.md). Novelty is off unless requested; task weights, requirements and threshold are generated and frozen before proposals. Known techniques/flags/ports are allowed. Every valid proposal is recorded before critique, with explicit task/baseline/policy/evidence links. Selection and scoped test outcomes are separate.

Live migration retained 93 historical records (revisions and partial leads included), plus one linked reconsideration = **94 records, 279 events, zero experiment tests**. Repeat import added zero records with zero errors. [Verification report](adaptive-memory-verification.json).

The original low-M GEMM proposal remains rejected under its historical novelty rule. [Reconsideration](../runs/deployment-revisit-001/decision.md) under the new [task rubric](../runs/deployment-policy-001/rubric.json) accepted it for test design at 70/100. Its experimental status remains untested. [Exported memory graph](../runs/deployment-revisit-001/memory-graph.json).

This change used one rubric model call and one critique call, reused the frozen evidence, made local prior-implementation searches and no GPU calls. Task-aware memory recall now supplies 12 compact summaries (~15,175 characters in the live check); full histories remain durable. Evaluator/test-agent execution is still future work; plan/start/result recording interfaces are implemented and tested.

## Deployment and tests

Code and documentation are deployed to `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/ideation`. The UI serves port 8765 on loopback. Its prefilled-query links and BM25 display were checked live.

**49 unit tests pass.** Live repeat checks passed for Serper, OpenAlex, Fathom page extraction, arXiv text and the inexpensive helper. GitHub on-demand repeated reads hit the cache. [Cache report](cache-live-check.json).

The earlier retrieval session used **one actual Serper request and two gpt-5.6-luna helper calls**. The second helper call followed a cache-key change to include full source hashes; subsequent identical calls hit the cache. These counts do not include the primary-model planning/evidence/hypothesis calls: one plan, evidence plus one quote repair, and two proposal/critique pairs (seven calls). No paid OpenAI API helper call was made; the helper used existing Codex login. No aggregate model cost is measured or claimed.

## Earlier search and hypothesis artifacts (historical policy)

- User guide: 20 topics, 878 terms in `config/keyword-guide.json` and the verbatim text file.
- [Editable plan](../runs/moe-low-m-001/planning/plan.json): low-concurrency DeepSeek/B200 MoE GEMM/graph selection; excludes speculation/MTP.
- [Manual inspection report](../runs/moe-low-m-001/search/inspection.md): eight local GitHub queries plus three arXiv/HF queries in the corresponding results JSON.
- Evidence: [eight sources, ten exact-quote validated claims](../runs/moe-low-m-001-analysis/evidence/packet.json), including two paper full texts and one exact-SHA source file.
- [Initial decision](../runs/moe-low-m-001-analysis/decision.md): one proposal, zero selected. The critique exposed an excerpt truncation problem: a genuine quotation was absent from its shortened source context.
- Fixed source excerpt construction to append cited passages with surrounding original text. Regression test added; the evidence packet was reused without another extraction call.
- [Corrected run decision](../runs/moe-low-m-002/decision.md), finished **04:15:14 IST**: one proposal, zero selected. Entailment now passes. Distinction from prior art still fails: load-dependent grouped/dense GEMM selection already exists, and the B200-specific implementation difference is unestablished.

The proposal is a conditional graph-compatible shape-selection experiment, not an accepted optimization. It identifies needed observations: actual backend eligibility, current dispatch, routed rows per expert, selection synchronization cost, and repeated TPOT against current and best static controls. No GPU experiment or measured speedup was produced. Both model calls remain judgments, not validated independent expert review.

## Download snapshot — 04:50:57 IST

| Scope | Actual state |
|---|---|
| Historical issue endpoint, including PR opening bodies | Initial pass completed at 03:32:09 IST |
| Stored issue records | 19,138 |
| Stored PR records | 42,601 |
| Separate PR metadata enumeration | Checkpoint: page 396 next; first 395 pages processed |
| Bulk issue/review comments | Not started; 20 comments and two formal reviews from selected hydration |
| Diffs | 16 selected file records; not a full repository diff archive |
| GitHub rate budget at latest collector response | 4,787 remaining; collector running |

[Exact checkpoints](corpus-status-latest.json). Live repository totals and new changes still need reconciliation. This is **not a complete archive of every PR plus all discussion/reviews/diffs**. The existing large-comment-feed boundary needs auditing before claiming full comment coverage. The hourly timer resumes progress; the currently running collector keeps its loaded code until the next process starts. New on-demand calls already use the cache; collector feed requests intentionally stay fresh.

## Start using it

[Interactive guide](PLAYGROUND.md) · [System diagrams and exact architecture](SYSTEM_ARCHITECTURE.md) · [Tool contracts](THREE_TOOLS.md).

---
name: inference-research
description: Develop source-level vLLM and DeepEP optimization hypotheses from B200 measurements, Deepseek_serve code, literature and upstream PRs. Use for inference research planning, PR analysis, bottleneck investigation and experiment design before human review.
---

# Inference researcher

## Context

Resolve paths from the repository root. Read `research/README.md` and `research/SOURCES.md`, then the relevant batch's `brief.md` and `decision.md` if resuming. Follow links selectively. The completed TPE/GuideLLM parameter study is frozen; current work is source-level research for a human-reviewed experiment shortlist.

Write to `research/runs/<batch-id>/`. Use an existing requested batch or choose a descriptive new ID. Record the question, environment and source pins in `brief.md`. Keep source checkouts under ignored `.artifacts/reference-repos/`; never rewrite historical results to fit a hypothesis.

## Investigate

1. Identify a concrete measured symptom and its exact workload/configuration. Reconstruct profile overlays and metric definitions. A Pareto point supplies a baseline candidate, not a causal explanation.
2. Follow the suspected execution path in pinned source. Establish backend/model/hardware applicability. In particular, confirm whether the B200 backend actually calls DeepEP; EP alone is insufficient. Distinguish one-node replicas from multi-node operation.
3. Research online using primary papers, official source/docs, issues and PRs. Search for counterexamples and existing fixes. Open relevant diffs and review discussions; record URL, state, access date, base/head SHA, symbols, tests and evidence limitations. Check whether a merged change is already in the baseline. Mark unavailable evidence explicitly.
4. Chunk notes by mechanism under `notes/<topic>.md`: observation → source path → supporting/contradicting sources → uncertainty → possible experiment. Index sources and discarded leads in `sources.md`. Keep only useful excerpts and evidence pointers; do not indiscriminately load whole repos or skill collections.
5. Generate up to four strong hypotheses for the initial batch, allowing fewer. Use `research/HYPOTHESIS_TEMPLATE.md`. Give each an exact code surface, expected directional effect, alternative explanation, correctness check and cheapest falsification. Prefer an attributable upstream port over invented novelty when it is useful. Do not force a DeepEP idea if applicability fails; state what a separate DeepEP study would require.

## Design for useful results

- Select a relevant measured frontier configuration and freeze its serving settings for the first patch comparison. A coherent change may touch multiple files. Later retuning of both parent and patch uses equal budgets.
- Reuse the existing workload/evaluator appropriate to the baseline. Specify input/output lengths, traffic mode, cache treatment, load points, request counts/duration and repeats with rationale. Do not inherit Qwen SLOs as B200 constraints.
- Separate mechanism profiling from scored measurements. Report latency distributions, throughput, failures and diagnostic counters, including unfavorable operating points. Performance estimates are predictions until tested.
- Cache hypotheses need token/prefix identity and actual hit evidence. MTP hypotheses need acceptance/verification and output correctness evidence. DeepEP hypotheses need the actual communication path, tensor shapes, topology and correctness oracle. Latency alone does not establish any of these mechanisms.
- End-to-end benefit is the objective; a faster isolated kernel is a lead. Distinguish source-update benefits, settings benefits and code-change effects.

## Deliver and stop

Write concise `hypotheses/H*.md` cards and `decision.md` with a ranked shortlist, cheapest next check and unresolved blockers. Request independent review via the separate `inference-critic` skill; do not impersonate an independent reviewer. If the user asks for parallel agents, split investigations by mechanism and give the critic the original evidence as well as proposals.

In this research-only stage, stop before source patches, builds, benchmark launches or deployment; the user requested manual proposal review first. A later explicit instruction to implement/test advances that stage. When revising, preserve the review and record changed claims and rejected ideas so a fresh agent can resume without chat history.

See `research/THIRD_PARTY.md` for the Orchestra guidance adapted here.

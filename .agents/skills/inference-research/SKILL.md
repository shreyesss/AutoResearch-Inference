---
name: inference-research
description: Research inference-serving improvements through literature, source code, PRs and experiments; generate a requested number of distinct hypotheses, critique and revise them within the same run. Covers library changes, feature activation, backend integration and runtime policies.
---

# Inference optimization research

## Objective and scope

Find useful ways to improve measured inference-serving frontiers. Read `research/README.md`, `research/SOURCES.md` and the relevant entries in `research/META.md`. For research execution, also read `research/METHODOLOGY.md` for literature/PR discovery, delegation and the review rubric.

The B200 results and Deepseek_serve provide starting evidence. They do not limit research to currently enabled features or the historical source version. Consider new algorithms, online/adaptive serving policies, kernels, scheduling, attention, speculation, KV/cache management, routing, communication, CPU/GPU overlap, feature activation, upstream ports and cross-engine ideas. Choose directions that could matter for the user's target, rather than mechanically covering every category.

A feature being absent, disabled or already implemented upstream is an integration question. Identify how to activate/adapt it, required dependencies, quality implications and a fair comparison. Reject a claimed current-path improvement if the path is inactive; retain a distinct activation/integration hypothesis when justified. DeepEP is one possible research surface, not a required ingredient or assumed baseline backend.

## Run contract

Record the user's requested idea count N, scope, available hardware, time budget and research batch ID in `brief.md`. If N is omitted, use five as a disclosed working default. Honor requested breadth and count; do not silently stop at one convenient PR. Generate more leads than N, deduplicate by mechanism, investigate alternatives and select N distinct plausible ideas. Do not fabricate support to fill the quota: if a genuine evidence/access/budget limit prevents N, report the shortfall, attempted directions and lower-confidence leads separately. Novelty means new relative to prior batches when the user requests new ideas; upstream reuse is welcome and must be labeled.

Use `research/runs/<new-id>/`; inspect prior decisions and rejected leads before searching. Revisit an old lead only with a changed premise or new evidence. Preserve earlier batches and the completed TPE study.

## Research and synthesis

- Combine evidence-led investigation with opportunity-led literature and source research. A profile is useful evidence, not a prerequisite for proposing a new mechanism.
- Follow the discovery procedure in `research/METHODOLOGY.md`. Search and read papers, relevant references/citing work, upstream diffs/reviews and implementations in other serving engines. Verify crucial claims in primary sources; log searches, findings, counterevidence and access limits.
- Use native subagents for separable research directions when available and permitted. This workflow requests delegation for broad multi-idea batches; use a few bounded assignments matched to the requested scope. Give each the target, baseline facts, assigned question, output contract and execution limits. Have agents write separate notes; synthesize and deduplicate centrally. Do not prescribe the conclusion. If delegation is unavailable, do these passes sequentially and say so.
- Trace the relevant pinned code, or specify a proposed integration path when introducing a capability. Distinguish measured baseline, current upstream and proposed version. Explain what transfers from another model/hardware/workload and what still needs testing.
- Form cards with `research/HYPOTHESIS_TEMPLATE.md`. Each needs a concrete mechanism, strongest supporting and opposing evidence, implementation/activation surface, expected tradeoffs and cheapest informative experiment. Label confidence and readiness separately.

## Critique and improve in this run

Apply `research/METHODOLOGY.md`'s rubric to every shortlisted idea. Self-critique is the default; a subagent adversarial pass is optional. No separate critic chat is required. Record whether review was self, delegated or external. Challenge assumptions, inspect contrary sources, revise the hypothesis or replace weak ideas. Carry substantive objections and their resolution into the final cards and `review.md`; do not merely append a disclaimer. Stop iterating when the requested deliverable is useful or the declared budget is reached, reporting unresolved uncertainty.

## Fast path to evidence

Choose an experiment suited to the change: isolated operation, component/trace replay, or one matched serving point. Preserve the service contract and measurement conditions; allow all candidate implementation/configuration changes necessary to test the idea. Separate a system-benefit comparison from later causal ablations. A coherent multi-change integration is valid; one-knob-at-a-time is not required.

Plan correctness before performance. Cache work needs actual prefix/hit evidence; speculation needs acceptance and quality checks; communication needs representative topology and messages. Profile separately from scored runs. Expand to curves and selected repeats only when warranted. Record setup/build/startup and measurement time separately. Do not invent universal sample floors, speedup predictions or SLOs.

## Deliver

Write sources, mechanism notes, N hypothesis cards, critique/revisions and a concise ranked `decision.md`: proposal, benefit/tradeoff, evidence, required changes, confidence/readiness, cheapest next test and cost. Include exploration coverage and why discarded alternatives lost. Keep filesystem memory concise and linked; do not force-load all historical context.

The current human-in-the-loop stage ends at experiment selection. Do not build, patch serving code or launch GPUs unless the user has authorized that stage. Existing authorization continues to apply. Recommend process improvements to the meta coordinator, which maintains `research/META.md`; do not rewrite project-wide policy as an incidental research action.

Adapted research principles: `research/THIRD_PARTY.md`.

# Inference optimization research

## Goal and current checkpoint

Find upgrades that improve real inference-serving operating curves and Pareto frontiers: algorithms, kernels, serving policies, feature activation, backend integration, upstream ports and new code. B200 evidence and Deepseek_serve provide a starting point. Current enabled features and historical versions do not bound the search.

The completed Optuna TPE / auto-tuning-vLLM / GuideLLM parameter study stays complete. The current human-in-the-loop deliverable is **the requested number of distinct plausible ideas, critiqued and revised within one research run, with cheap experiments and a ranked shortlist**. The human then selects what to implement/test. No performance improvement is established by a proposal.

## Run in a fresh Codex session

Use this prompt, changing the number and batch ID as desired:

```text
Use $inference-research. Read research/README.md, research/META.md and
research/SOURCES.md. Follow research/METHODOLOGY.md.

Create research/runs/b200-source-002/. Generate 6 distinct plausible
inference-serving improvement ideas. Read b200-source-001 to avoid
rediscovering its ideas without a new premise; retain H01 as prior work.

Investigate papers and their references/citing work, open/merged/rejected
PRs and relevant implementations in other serving systems. Use native
subagents for distinct research directions. Explore beyond features
currently enabled: activation, new backends, runtime policies, library
upgrades and original adaptations are valid. Connect ideas to our target
workload/hardware and explain requirements when proposing a new setup.

Critique and revise the ideas yourself within this run; optional subagent
review is welcome. Give each idea supporting and opposing evidence,
required changes, confidence/readiness, a correctness check, the cheapest
informative experiment and a route to its first measured serving point.
Honor the requested count without duplicates or invented evidence.

Finish with cards, critique/revisions, an exploration coverage table and
a ranked decision.md. Stop for human experiment selection. Do not patch
serving code, build images or launch GPUs in this research run.
```

The [research skill](../.agents/skills/inference-research/SKILL.md) owns discovery, synthesis and critique/revision. The [critic skill](../.agents/skills/inference-critic/SKILL.md) remains available for an optional targeted or external review. **A separate critic chat is not required.** Self-review is labeled honestly; independent review is optional.

Skills live in `.agents/skills/`, the repository-local layout described in [OpenAI's skill workflow](https://developers.openai.com/blog/skills-agents-sdk). If a client does not discover them, explicitly ask it to read the linked SKILL.md. Tools and model choice come from the session; the user's preferred starting model is `gpt-6-sol`. Subagents use available session capabilities; if unavailable, perform the research passes sequentially and disclose that.

## How the work flows

1. Record requested idea count, scope, constraints and evidence. Read prior decisions selectively.
2. Explore both observed bottlenecks and opportunities from literature/code; use distinct subagent questions when helpful.
3. Synthesize different mechanisms and identify activation/integration requirements. Existing upstream work is reusable; disabled features can be opportunities.
4. Apply the [rubric](METHODOLOGY.md), investigate counterevidence, revise or replace weak ideas and rank the requested set. Report genuine shortfalls if evidence or budget limits prevent completion.
5. Bring the human a comparison: expected benefit/tradeoff, evidence, required changes, confidence/readiness, cheapest test and cost.
6. After selection/authorization, test the smallest relevant component, then one matched serving point; expand promising candidates to curves and repeat/held-out confirmation as appropriate.

Comparison fairness preserves the service contract and measurement conditions. It allows required candidate changes to code, features and settings. A focused patch test can freeze unrelated settings for attribution; a complete system upgrade can be tested as a combined candidate, with later ablations if needed. Keep profiles separate from scored timing. Distinguish operation speedups, provisional serving points and replicated frontier improvements.

## Memory and roles

The **meta coordinator** maintains goals, process lessons and future-harness decisions in [META.md](META.md). It improves skills and helps the user choose experiments. Research workers execute discovery and maintain batch evidence. This separation preserves the user's observer role without requiring another critic session.

Each batch uses ordinary files:

```text
brief.md             requested count, question, scope, hardware, source pins
sources.md           searches, sources, dates, useful/rejected leads
notes/<topic>.md     bounded evidence chunks and subagent findings
hypotheses/H01.md    idea and experiment card; additional IDs as requested
review.md            self/delegated/external critique and substantive revisions
decision.md          ranked set, coverage, unresolved issues, next test
```

Use the [hypothesis template](HYPOTHESIS_TEMPLATE.md). Create files when they have content; preserve previous batches and negative outcomes. A resumed agent starts with brief/decision and follows relevant links. No database, forced full-history injection or new execution controller is required. Save evidence and decisions, not hidden reasoning. Record available transcript locations without claiming a custom logger exists.

## Current status

- Completed TPE and imported B200 results remain unchanged.
- Deepseek_serve was refreshed to `2e6fa28`; recorded source pins are in [SOURCES.md](SOURCES.md).
- Batch `b200-source-001` contains one proposed backport and a review requesting revision; no measured improvement is claimed. It predates the broadened instructions.
- The current skills support requested idea counts, broader discovery, delegation and integrated critique. Their research quality must be checked through actual batch outcomes, not just file validation.
- Future autonomous-harness ideas are recorded in [META.md](META.md); this update creates instructions and documents, not a running autonomous service.

[Research method](METHODOLOGY.md) · [Sources](SOURCES.md) · [Attribution](THIRD_PARTY.md) · [Completed study](../results/2026-10-18-direct-optuna/ANALYSIS.md)

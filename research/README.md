# Source-level inference research

## Decision and next checkpoint

The completed parameter study used **Optuna multivariate TPE**, the InseeFrLab auto-tuning-vLLM controller and **GuideLLM**. Leave its code, protocol and results at that stage. Grid search and more parameter trials are deferred.

The next deliverable is a **human-reviewed shortlist of executable source-code hypotheses** for vLLM / DeepEP, grounded in the B200 evidence and `Deepseek_serve`. Success means a proposal worth testing, with a plausible mechanism and a cheap way to prove it wrong. No improvement is claimed until measured.

Two repository skills implement this stage:

| Role | Reads | Produces |
|---|---|---|
| [inference-research](../.agents/skills/inference-research/SKILL.md) | Benchmark evidence, pinned source, papers, PR diffs and reviews | Small evidence notes, hypotheses, concrete experiments |
| [inference-critic](../.agents/skills/inference-critic/SKILL.md) | The proposals and original sources, independently checked | Advance / revise / reject decisions with reasons and cheapest fixes |

These are instructions for a capable coding agent with filesystem and online research tools. There is no new runner, database, scheduler or model API wrapper. Files are the shared memory. The agent reads relevant records as needed. Model choice remains a session setting; the user's preferred starting model is `gpt-6-sol`, not an expensive fixed model in a launcher.

## Run in a fresh Codex session

Open this repository and use:

```text
Use $inference-research. Read research/README.md and research/SOURCES.md.
Start research/runs/b200-source-001. Use B200 evidence and the refreshed
Deepseek_serve source to research vLLM and DeepEP opportunities online,
including PR diffs and review discussions. Produce up to four grounded
hypotheses and their cheapest falsification experiments. Prioritize useful
improvements over novelty. Stop at a shortlist for human review.
```

Then in a **separate fresh session**, to make the critique independent:

```text
Use $inference-critic on research/runs/b200-source-001.
Check the original evidence, source applicability and current PR status.
Write review.md with advance/revise/reject per hypothesis. Identify the
single most useful next experiment, or explain why none is ready.
```

Finally ask the researcher to revise once against `review.md`, preserving the original claims and the review. The human chooses the experiment. These prompts do not start builds or GPU measurements.

Skills live in `.agents/skills/`, the repository-local layout described in [OpenAI's skill workflow](https://developers.openai.com/blog/skills-agents-sdk). If a client does not discover them, explicitly ask it to read the linked `SKILL.md` and follow it. Internet/tool availability comes from that session; the skill does not grant access. Record inaccessible evidence rather than filling gaps from memory.

## Research loop

1. **Choose the baseline and workload.** Start with a relevant B200 frontier configuration, reconstructing all profile overlays, router and cache settings. Keep topology comparisons separate from isolated code changes. The local Qwen study is a separate evidence track.
2. **Find a concrete opportunity.** Read evidence and source together. Distinguish a measured symptom from a proposed cause. An upstream PR can supply an idea or implementation; record attribution and whether it already exists in the baseline.
3. **Chunk the investigation by mechanism.** For example scheduler/prefill, routing/cache locality, or MoE communication. Each note links a measurement, code path, paper/PR, counterevidence and unresolved questions. Avoid dumping whole repositories into context.
4. **Form hypotheses.** Up to four strong candidates for the first batch; fewer is fine. Each needs a source change, applicability argument, correctness check, cheapest falsification and matched serving test. Use the [card](HYPOTHESIS_TEMPLATE.md).
5. **Critique and revise.** Check evidence, alternative explanations, code reachability, prior work, experiment design and expected cost. A useful upstream backport can advance without being novel. Preserve rejected ideas and why they failed.
6. **Human checkpoint.** Choose one proposal, the target hardware and the experiment budget. This is the current endpoint.

### Later, after choosing a proposal

Reproduce the chosen clean source build → implement in an isolated checkout → correctness test → focused microbenchmark/profile → matched end-to-end comparison → selected repetitions and held-out inputs → operating curves and Pareto comparison. Reuse existing benchmark tooling for the selected protocol.

Freeze serving settings for the first parent-versus-patch comparison. A coherent patch may change several related code sites; there is no one-line or one-knob rule. If the patch changes the best configuration, retune parent and patch with equal budgets as a separate experiment. Profile separately from scored runs. Do not force every rejected idea through the long suite.

Report TTFT and request-level decode TPOT p50/p90/p99, throughput, errors, workload/cache facts and mechanism-specific counters where available. Keep full operating points and dominated configurations. State objectives and tradeoffs before collecting results; do not import Qwen SLA targets into the B200 workload. Tail estimates and causal claims must reflect the actual sample and repeat evidence.

## Files and memory

Each research batch is a normal directory under `research/runs/<id>/`:

```text
brief.md             question, baseline, hardware, source pins, scope
sources.md           searched sources, URLs/commits, dates, useful/rejected leads
notes/<topic>.md     small evidence chunks; exact paths/rows/symbols
hypotheses/H01.md    hypothesis and experiment card (additional IDs as needed)
review.md            independent critic decisions and evidence checks
decision.md          shortlist, revisions, unresolved issues, human decision
```

Create files only when they have content. A resumed agent reads the brief and decision first, then follows links. Before proposing an old idea again, inspect previous decisions and the relevant evidence. No forced full-history injection or vector memory. Save findings, sources and decisions; an agent's hidden reasoning is not a research artifact. When a client exposes a session transcript, record its location alongside these files; no custom transcript collector is installed here.

## Setup status

- Completed TPE study and imported B200 evidence retained unchanged.
- `Deepseek_serve` successfully fast-forwarded from `de864ee` to `2e6fa28`; checkout is clean.
- Orchestra skills inspected and the relevant research/review principles adapted with attribution.
- Two repository skills and the source map are ready for a fresh session. Source access is via the local reference checkout and pinned online links; vLLM and DeepEP are not built or qualified locally by this setup.
- No hypothesis batch, independent critic session, source patch or new GPU run has been executed by this setup. Skill-format validation is not evidence of research quality.

[Source map and pins](SOURCES.md) · [Attribution](THIRD_PARTY.md) · [Completed study](../results/2026-10-18-direct-optuna/ANALYSIS.md)

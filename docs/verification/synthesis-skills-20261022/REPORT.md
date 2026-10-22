# Synthesis skills: implementation and observed evaluation

22 October 2026. **Research/skill work only. No GPU experiments, model launches,
training, serving patches or deployment changes.** The supplied frozen TreeSpark
execution plan is an example of good adaptation, not authorization to run it.

## What changed

The research and critic skills now explicitly separate paper components before
accepting or rejecting a method. They record selected/omitted components, necessary
dependencies, cross-source compatibility, baseline delta, competing explanations,
and a discriminating comparison. The example is using frozen-weight tree policies
without importing a neural trainer, while retaining branch-correct verification.

Task-derived rubric judgments and self-review must cite an observation or identify
a missing discriminator. For consequential commands retain:

`decision gap → command receipt → evidence/failure → decision change → next action`

The existing hypothesis and decision tools retain optional synthesis/review/tool-use
fields; no new orchestration engine or hidden LLM judge was added. Semantic reasoning
is performed by the host. See [skill guidance](../../../.agents/skills/inference-research/references/synthesis.md).

An explicit attributed user waiver can now make the separate ROI screen optional
in a new task brief. A structurally complete plan can reach review with unknown ROI;
source grounding, experiment pins, correctness and execution boundaries remain.
See [the exact policy](../../EVALUATION_GATING.md#explicit-task-waiver). Historical
hypotheses retain their original policy.

## Literature used, selectively

Six primary sources were read: Scideator, DiscoveryRSI, official AI Scientist v3,
AI co-scientist, SciMON and a self-correction study. The useful contributions are
component/facet recombination, repair of nonfundamental assumptions, meaningful
revision tracking and evaluator invariants. Their novelty objectives, training
systems and large orchestration pipelines were not adopted. These are engineering
adaptations, not reproduced results. [Literature and limits](LITERATURE.md),
[source identities](sources.json), [retrieval log](retrieval-log.json).

The explicit arXiv tool query timed out. Literature findings came from successful
primary-source web reads, not a successful paper-tool discovery run. The actual
tool failure and fallback are preserved. The official SakanaAI AI-Scientist-v3 and
findalexli's similarly named project are distinguished.

## Actual before/after skill experiment

An evaluator froze four case packets and six evidence-based criteria before seeing
revised skills or generator outputs. Two fresh agents received identical case
packets, output limits and model settings; one received the old skill package, one
the revised package. They generated **eight retained handoffs**. The evaluator
judged anonymous A/B outputs before version labels were revealed.

| Case | Old skill / 12 | Revised skill / 12 | Observed result |
|---|---:|---:|---|
| D00: supplied TreeSpark development example | 10 | 12 | Clearer shared policy interface and matched-budget versus tuned-deployment comparisons |
| H01: synthetic routing/predictor transfer | 12 | 12 | Tie; complementary signal-availability and replay-feedback checks |
| H02: synthetic cache compaction versus learned quantization | 12 | 12 | Tie; both selectively reuse lossless components and preserve safety constraints |
| H03: synthetic disabled callback and hardware mismatch | 12 | 12 | Tie; both distinguish configuration opportunity, error and unproven performance |

**No critical failures were found. There is no demonstrated held-out improvement.**
The development-example difference is encouraging but insufficient for a general
quality claim. One generation per arm, three synthetic held-out cases, a rubric
ceiling and shared case context limit inference. Blinding was procedural on a
shared filesystem. Self/model judgments are not empirical serving validation.

These cases evaluate reasoning from supplied evidence and proposed next actions;
they do not measure retrieval recall or execute the proposed commands. All original
outputs, evidence packets, score explanations, freeze hashes and the revealed map
are retained. These cases are now opened; future confirmation needs fresh cases.

- [Anonymous review](ANONYMOUS_REVIEW.md) and [criterion-level evidence](scores.json)
- [Procedure](PROCEDURE.md) and [experiment metadata](experiment.json)
- [Old outputs](outputs/before/D00.md) and [revised outputs](outputs/after/D00.md)

## Actual tool-use findings and fixes

The preceding live research round used repeated online/local retrieval, rejected
recycled bounded-replay/prefill proposals, and narrowed generic Engram prefetch to
WKV-only lookahead. It inspected actual source and hash-checked three Mooncake
traces on CPU. That is a real adaptive-use example, not a controlled proof that
the new skill beats the old one. [Field report](../adaptive-research-20261022/FIELD_REPORT.md).

Live use exposed a reproducible module-import bug: from repository-root Python,
the artifact directory `ideation/evidence` shadowed the code module. A source-
checkout package bridge fixes it. A clean-process regression removes pytest's
special import path, initializes state and imports the actual paper-search tools.
The installed inner package remains unchanged.

The earlier field test also corrected missing explicit query plans silently falling
back to lexical expansion and allowed retained CPU scripts to be pinned by their
actual SHA256 instead of inventing a Git revision. These fixes came from exercised
tools, independently of the model's rubric scores.

## Verification and remaining limits

- Full research suite: **243 passed in 5.55 seconds**.
- Bootstrap dry run: passed; no installation or service mutation.
- Both changed skills pass the skill-creator validator.
- No measured inference improvement, GPU availability claim or serving authorization.
- A returned plan is a proposal; only a later authorized, correct matched experiment
  can establish target performance. Unknown ROI and scientific uncertainty remain
  visible without turning them into a universal implementation prohibition.

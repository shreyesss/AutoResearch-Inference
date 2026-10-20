# Lessons that change the next experiment

These are evidence-backed process decisions, not a replacement for historical verdicts. Updated 2026-10-21 (Asia/Calcutta).

| Lesson | What happened | Rule for subsequent work |
| --- | --- | --- |
| A real inefficiency is not necessarily an expensive bottleneck. | C03 changed the intended graph selection, but selection never measured how much exposed time the occasional smaller draft graph could save. | Before spending a full attempt, identify the affected work, measure its exposed contribution, and show a plausible saving after overhead. Event count, row count and reviewer score do not substitute for time. |
| Do not invent the cause of a disappointing result. | C03's service screen worsened long ITL and TTFT; no component timing establishes the cause. Kernel tiling, collectives, CPU work and scheduling are possibilities. | Separate observations, source-supported mechanisms and causal conjectures. Keep the regression unexplained until an experiment discriminates the causes. |
| Use the correct denominator. | Warmup-inclusive diagnostic histograms differ from strict profiling events; DP ranks participate in one event. | Label phase, cohort and rank aggregation. Do not multiply correlated ranks into a larger sample or turn graph-capacity changes into FLOPs/time claims. |
| Keep a valid unfavorable screen. | One fresh paired screen met the scoped gates and failed its promotion rule. | Preserve the frozen stop. Do not retry for a favorable seed or explain away cache/acceptance differences as external noise. One screen is also not a precise universal effect estimate. |
| Distinguish complete, valid, eligible and statistically conclusive. | C03 exports completed, but both arms missed service SLO eligibility; one valid AB seed did not establish a confidence interval. | State each property separately and retain errors and failed diagnostic attempts. |
| Check source-level constraints precisely. | A trained/default proposal width was initially interpreted too strongly as a hard k3 restriction. | Cite the actual guard and model path. A configuration default is not an assertion, and a Qwen guard is not a DeepSeek constraint. Correct the research record when evidence changes. |
| Keep evaluator independence. | C03 used separate evaluator designer, evaluator tooling builder and optimization developer. | Continue that separation. The root orchestrator launches workloads, preserves the original environment and publishes evidence. |
| Preserve evidence where the reader can recover it. | Detailed logs and evaluator sources spanned two local worktrees and were not yet upstream. | Push readable records plus compressed, checksummed evidence and a restoration map. Retain sealed byte contents and original paths; organize through indexes. |

Primary local basis: [C03 mechanism review](../runs/c03-mechanism-review-001/REPORT.md), [execution report](../runs/c03-execution-001/REPORT.md), [paired context](../runs/c03-execution-001/SCREEN_PAIR_CONTEXT.md), and [analysis correction](ANALYSIS.md). These lessons do not assert that adaptive verification will succeed.

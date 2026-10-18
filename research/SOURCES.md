# Research source map

This map was prepared after the requested reference refresh on 18 October 2026 UTC. Record the actual access date and commit again in each research batch. A latest checkout is not the source of an older measurement.

## Local evidence and reference code

| Source | Revision / status | Start here |
|---|---|---|
| Imported B200 evidence | Original campaign/config snapshot attributed to `724cee8`; 73 original files | [Provenance and limits](../docs/B200_REFERENCE.md), [findings](../b200-bench-analysis/PARETO_FINDINGS.md), [report points](../b200-bench-analysis/pareto-data.json) |
| Refreshed Deepseek_serve | `2e6fa287d90adf7318ad314de27aa2f595aac821`, `master`; fast-forward pull from `de864eeeca4ef71147cff22e6929395603f61197` | Local `Deepseek_serve/`; [pinned upstream tree](https://github.com/mukundkhanna123/Deepseek_serve/tree/2e6fa287d90adf7318ad314de27aa2f595aac821) |
| Completed local Qwen/RTX PRO study | TPE / GuideLLM; 25 trials, 24 unique configs, plus held-out confirmation | [Analysis](../results/2026-10-18-direct-optuna/ANALYSIS.md), [evidence archive](../results/2026-10-18-direct-optuna/evidence/README.md) |

`Deepseek_serve` is a separate checkout, not vendored into the parent repository. On another host, clone the upstream URL and check out the recorded commit for the same reference. Do not replace the imported B200 snapshot with the newer checkout or assume its newest scripts produced the imported points.

### Read only what answers the question

| Question | Paths relative to `Deepseek_serve/` |
|---|---|
| Which image, source, model and backend? | `serving/b200/vllm/images.yaml`, `serving/b200/vllm/README.md`, `serving/b200/vllm/base.yaml` |
| Exact serving configuration? | `serving/b200/vllm/profiles/`, `serving/b200/vllm/experiments.yaml`, `serving/b200/vllm/serve.sh` |
| Workload and measurement protocol? | `ops_latency/campaign.yaml`, `ops_latency/README.md`, `testing/workloads/aiperf/`, `ops_aiperf/campaign.yaml` |
| DEP8 vs two DEP4 implementation and comparability? | `ops_latency/compare_dep8_2xdep4.py`, `ops_latency/run_dep8_vs_2xdep4.sh`, `ops_latency/run_2xdep4.sh`, `ops_latency/run_2xdep4_smoke.sh` |
| Router or API-process effects? | `lib/router.py`, `ops_latency/run_2xdep4_tuning_sweep.sh`, serving profiles and overlays |
| How scores and frontiers were computed? | `ops_aiperf/analyze.py`, `ops_latency/report/build_report.py`, `experiments/export/build_latency_cost_pareto.py` |

**Observed setup facts, not hypotheses:**

- The imported B200 subset has aggregate reports, scores, manifests and configs; it is not the full approximately 119 GB raw inventory. Do not infer kernel times or per-request correlations from aggregate latency alone.
- The refreshed serving README describes **one eight-B200 NVLink/NVSwitch node**, including DEP8 and two DEP4 engines. Two engines do not imply two nodes. Public endpoint topology is not established by the imported scores.
- The comparable agent slice is approximately 8K input / 1K output with a 75% cacheability target. Target prefix reuse is not proof of the actual cache-hit fraction. Follow the run's own manifest for timing, concurrency and exact workload.
- TP and DEP profiles select different attention/MoE stacks; the refreshed README names `deep_gemm_mega_moe` for DEP8. **DeepEP use is not established simply by EP being enabled.** Trace the active backend before proposing a DeepEP change as an improvement to these measurements.
- At refresh, `ops_latency/report/latency-dep8-vs-2xdep4.json` has an empty `aggregates` list. The presence of a comparison script/report contract does not prove completed comparison measurements.
- The local Qwen result is a useful TTFT/TPOT tradeoff lead, not a universal best configuration. Its single-GPU workload cannot validate multi-GPU MoE communication changes.

## vLLM and DeepEP source research

The B200 reference records vLLM commit **`ac9126e58aa7bbab1856ba6593ba4d5003fea516`** and image **`sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`**. The model revision is **`2cba9e42aa026125f3ed06c6d98c1db82f7ca027`**. These are recorded provenance, not an independently reproduced source/image match.

- [vLLM at the recorded source pin](https://github.com/vllm-project/vllm/tree/ac9126e58aa7bbab1856ba6593ba4d5003fea516): inspect the relevant implementation before making a mechanism claim.
- [vLLM PRs](https://github.com/vllm-project/vllm/pulls): search by the observed bottleneck and code symbol; inspect both open and merged/rejected work.
- [DeepEP source](https://github.com/deepseek-ai/DeepEP) and [PRs](https://github.com/deepseek-ai/DeepEP/pulls): record the exact inspected commit. The benchmark's DeepEP version/backend is **unresolved**. Current-main documentation is not a historical dependency pin.
- [vLLM profiling documentation](https://docs.vllm.ai/en/stable/contributing/profiling/): use the documentation matching the selected source revision when designing instrumentation.

Fetch narrowly needed source into `.artifacts/reference-repos/` or read pinned upstream files; record pins in the batch. No GPU dependencies need installing to read code. If an alleged source pin cannot be retrieved, label it unresolved rather than substituting main. Preserve both the measured baseline version and the current research version when comparing them.

For each relevant PR: record URL, access date, state, base/head SHA, changed files/symbols, mechanism, reported measurements, review objections, tests, dependencies and whether the baseline already contains it. PR-title summaries are not sufficient. A backport must account for APIs, build dependencies and backend differences.

## Orchestra reference

Inspected [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) at **`773a52944ba4747a18bd4ae9ade53fff041adcbc`**, MIT. Local optional reference checkout: `.artifacts/reference-repos/ai-research-skills/`.

Selected sources:

- `21-research-ideation/brainstorming-research-ideas/SKILL.md`: problem-first ideas, assumptions and alternative explanations.
- `22-agent-native-research-artifact/rigor-reviewer/SKILL.md`: evidence relevance, falsifiability, scope, coherent mechanisms, honest exploration and experimental rigor.
- `12-inference-serving/vllm/SKILL.md`: inspected as a topic guide. Its generic throughput/latency targets and deployment snippets are **not** adopted as validated settings for this project.

Our critic checks external evidence and source itself. We do not adopt Orchestra's artifact-only review restriction, prerequisite ARA pipeline, numeric scoring or paper-generation machinery. [Attribution and license](THIRD_PARTY.md).

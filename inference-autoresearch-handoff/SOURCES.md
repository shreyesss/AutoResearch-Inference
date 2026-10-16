# Primary references and verification status

Reviewed for this handoff on 17 October 2026. Web/main documentation can move; implementation must pin code and verify installed help/export schemas. No server or GPU benchmark was run while writing these documents.

## Model and vLLM

- Qwen3.8-27B recipe: https://recipes.vllm.ai/Qwen/Qwen3.8-27B
- Recipe source, including hardware-specific overrides and MTP options: https://github.com/vllm-project/recipes/blob/main/models/Qwen/Qwen3.8-27B.yaml
- The initially supplied, different model: https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next
- Model card: https://huggingface.co/Qwen/Qwen3.8-27B
- vLLM optimization concepts: https://docs.vllm.ai/en/stable/configuration/optimization/
- Prefix manager design: https://docs.vllm.ai/en/latest/design/prefix_caching/

The model-specific recipe identifies a hybrid dense model and documents compatible serving features. It does not establish performance or exact memory feasibility on the unidentified target GPU. Hardware-specific overrides are not universal recommendations.

## AIPerf

- Repository: https://github.com/ai-dynamo/aiperf
- Metrics definitions: https://github.com/ai-dynamo/aiperf/blob/main/docs/metrics-reference.md
- Raw payload replay: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/raw-payload-replay.md
- Timestamped replay: https://github.com/ai-dynamo/aiperf/blob/main/docs/benchmark-modes/trace-replay.md
- Cache reset / warmup hook ordering: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/benchmark-control-hooks.md
- Synthetic generator/content source: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/synthetic-dataset.md
- Prefix synthesis: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/prefix-synthesis.md
- Duration/drain behavior: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/time-based-benchmarking.md
- Arrival controls: https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/arrival-patterns.md
- Multi-turn history modes: https://github.com/ai-dynamo/aiperf/blob/main/docs/reference/conversation-context-mode.md
- Adaptive benchmark search (future conventional comparator/reference): https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/adaptive-search.md

Some source reads in the preceding research resolved at commit `3fc7d4c54248080336750e4f901c6c969acfd8d3`; this is a provenance example, not a certified compatible installation lock. Confirm one actual install before adopting any CLI flag. The application contracts in this package are intentionally independent of AIPerf's own YAML schema.

## Codex

- Noninteractive invocation and structured result: https://developers.openai.com/codex/noninteractive (currently redirects to https://learn.chatgpt.com/docs/non-interactive-mode)
- Official schema-constrained exec example: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- Repository implementation instructions/long-running plans: https://developers.openai.com/cookbook/articles/codex_exec_plans

Verify the installed Codex binary/version, authentication and current argument spelling. Use final schema-constrained output separately from JSON event logging. No particular model, account entitlement or CLI installation is assumed by this handoff.


## v0.2 additions: source roles and limitations

Reviewed documentation/schema descriptions on 17 October 2026; raw data has not been empirically mined in this handoff. Main/latest URLs are moving references, not deployment pins. Agent 1 must produce a source and installed-capability audit before claiming support.

| Reference | What to inspect/use | Boundary |
|---|---|---|
| https://data.freeinference.org/ | Dataset availability, agent/serving metadata and analysis hypotheses | Do not conflate released metadata with planned raw-text releases or treat fleet observations as causal tuning labels |
| https://huggingface.co/datasets/harvardMadsys/freeinference_agentic_trace | Schema, missing text, provider usage, context mutations, tool/session relationships, tokenizer and scoped IDs | Target-tokenize reconstructed topology; complete sessions/time splits and namespace audit |
| https://github.com/HarvardMadSys/freeinference_agentic_trace | Reproduction/analysis code and data handling | Mining results require actual runs and exact source selection |
| https://docs.nvidia.com/aiperf/reference/command-line-options | Complete version-specific control families | Installed release/help/schema is the executable authority |
| https://docs.nvidia.com/aiperf/tutorials/datasets-inputs/agentic-code-dataset-generator | Existing growing-session/prefix/delay/reset/restart synthesis and quality reports | Generator defaults are assumptions to validate, not our trace findings |
| https://docs.nvidia.com/aiperf/tutorials/datasets-inputs/prefix-data-synthesis-tutorial | Prefix/schedule/length transforms | Scaling changes the workload; document fidelity consequences |
| https://github.com/AMD-AGI/Hyperloom | Framework plus kernel inference-optimization phases and durable recipe reuse | Borrow discipline, not claimed target-system gains |
| https://github.com/AMD-AGI/Hyperloom/blob/main/docs/conceptual/optimization-loop.md | Persisted state, reference/outcome/failure retrieval and execution authority | Our minimal proposer and Pareto policy are adaptations |
| https://github.com/AMD-AGI/Hyperloom/blob/main/src/hyperloom/agents/critic/SKILL.md | Reasoning/runtime separation and evidence-backed knowledge promotion | Read as design evidence; do not import external approval rules into our user workflow |
| https://github.com/inference-sim/inference-sim/blob/main/docs/guide/latency-models.md | Simulator vs actual execution, model/hardware cost support, speculative acceptance input and saturation limitations | Deferred integration; not a replacement for AIPerf real-hardware evidence |

Use URLs plus exact retrieval date, source commit/release/hash and scope in implementation outputs. Public workload statistics are hypotheses/priors until verified on selected accessible data. No numerical speedup, empirical mixture proportion or target-specific simulator accuracy is asserted by this package.

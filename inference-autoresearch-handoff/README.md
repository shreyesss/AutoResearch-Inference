# vLLM inference autoresearch: three-agent execution handoff

Version 0.2 • 17 October 2026 • Replaces the 0.1 design in this same package.

## Executive summary

Build a containerized experiment that lets a Codex agent optimize supported vLLM serving parameters for `Qwen/Qwen3.8-27B` on one identified NVIDIA GPU. AIPerf generates/replays traffic against the actual server. The current GPU description, “RTX 86 GB,” is unresolved; no runtime or performance claim is validated yet.

The research question has two stages. First establish that realistic, documented workloads activate mechanisms our allowed settings can affect, with effects distinguishable from noise. Then test whether a minimal hypothesis → evaluation → feedback loop discovers reproducible serving tradeoffs. A flat sensitivity pilot is a legitimate outcome; do not manufacture difficult traffic or weaken the baseline to obtain gains.

Primary objectives remain output tokens/s ↑, TTFT p99 ↓ and TPOT p99 ↓. Report both p50s and all failures, backlog, client lag and uncertainty. Maintain empirical Pareto fronts per workload/protocol over a fixed common load ladder, with separate matched-load views. There is no weighted score, invented SLA, or global-optimum claim.

The previous twelve fixed-shape/prefix packs remain diagnostic controls. They are no longer the finalized production-like suite. First analyze public trace structure; construct a compact representative suite including mixed prefill/decode traffic and session/cache behavior; validate actual requests and traffic; then run parameter-sensitivity probes. Freeze search and held-out packs before adaptive optimization. Use real content when evaluating content-sensitive MTP behavior.

FreeInference supplies evidence for workload construction, not labels identifying the best vLLM configuration. Mooncake traces supply structural replay inputs. AIPerf is the real-hardware benchmark layer. BLIS predicts modeled execution and is deferred. Hyperloom supplies useful patterns for evidence retrieval, durable state and measured knowledge reuse; its entire multi-agent runtime is not a v1 dependency.

Broaden observation now: resolved settings, queue/batch/token-budget behavior, memory/cache/preemption, speculation and graph observations, plus targeted profiles when available. Keep initial interventions to a declared serving-parameter domain. Add controls only through a versioned, evidence-backed amendment; future source/kernel/precision experiments reuse the evaluator but require new qualification.

## Read and execute

1. [Understanding and experiment design](docs/UNDERSTANDING.md): rationale, workload construction, mechanism map, metrics and limits.
2. [Judgments and decisions](DECISIONS.md): normative choices, assumptions, rejected approaches and revision conditions.
3. [Implementation runbook](docs/IMPLEMENTATION.md), [interfaces](docs/INTERFACES.md), [repository instructions](AGENTS.md), and [acceptance](ACCEPTANCE.md).
4. Three implementation assignments under [docs/agents](docs/agents). All sessions receive the whole package.

## Three implementation agents

| Agent | Ownership | Required deliverables |
|---|---|---|
| 1 | Workloads and AIPerf adapter | Trace audit/mining, workload cards, input-control inventory, deterministic assets, actual-traffic validation and normalized request records |
| 2 | Runtime and evaluator | Hardware/capability qualification, lifecycle, observability, correctness, calibration and sensitivity pilot |
| 3 | Search, storage and integration | Shared contracts, readiness gates, structured hypotheses/feedback, evidence retrieval, memory, Pareto archives, CLI and reports |

Builders work concurrently using the common scaffold and mocks. All real GPU measurements run sequentially under one lease. There is one optimization proposer in v1; three implementation builders do not imply three simultaneous GPU search agents.

## Paste into the coordinating Codex session

> Implement this handoff. Read README.md, AGENTS.md, DECISIONS.md, docs/UNDERSTANDING.md, docs/IMPLEMENTATION.md, docs/INTERFACES.md and ACCEPTANCE.md first. Preserve existing user work. Scaffold shared v0.2 DTOs/protocols and schema fixtures, then dispatch exactly three builders using docs/agents/AGENT_1_WORKLOADS.md, AGENT_2_RUNTIME_EVALUATOR.md and AGENT_3_SEARCH_COORDINATION.md. Agent 3 owns integration and contract amendments. Use independent mocks and disjoint branches/worktrees. Complete the CPU workflow, qualify the actual GPU and pinned software, audit/mine accessible traces, construct documented workload packs, validate their realization, and run baseline plus sensitivity pilot before adaptive search. The old 12 synthetic cells are diagnostic controls, not a frozen representative suite. Do not choose representative packs because they produce gains. The optimization agent may read evidence and request bounded diagnostics but cannot modify workload or evaluation policy. Preserve multiple Pareto tradeoffs and all negative results. Implement doctor → characterize → prepare → baseline → pilot → search → report, with evaluate for explicit candidate trials and resume support. A closed gate is a documented result, not a reason to invent evidence. If GPU, model, source data or authenticated Codex is unavailable, finish independent implementation, report exact blockers and supply reproducible next commands. Never label mocks or schema examples as real evidence. No BLIS integration, kernel writing, source optimization, quantization branch, UI, Kubernetes or BO comparator is required initially.

If spawning is unavailable, start three Codex sessions with their briefs. Commands and JSON in this package specify interfaces to implement; no application binary is included.

## Package and status

The same 22-file handoff contains schemas, examples, three briefs, source references and validation notes. Examples with unresolved pins or fabricated numbers are explicitly ineligible for real execution. See [VALIDATION.md](VALIDATION.md) for checks actually run on this documentation package. No raw trace mining, Docker build, GPU pilot or optimization campaign has been executed while writing it.

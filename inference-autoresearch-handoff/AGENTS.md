# Agent execution instructions — v0.2

This directory is a handoff and starter contract set, not an implemented runtime. Build the described system. Read README.md, DECISIONS.md, docs/UNDERSTANDING.md, docs/IMPLEMENTATION.md, docs/INTERFACES.md and ACCEPTANCE.md before coding.

## Invariants

1. Actual vLLM/GPU execution is measured through AIPerf. Label mocks; never import them into real archives.
2. Discover hardware and verify the target model/runtime. No silent checkpoint, precision, parser or task substitutions.
3. Frozen workload and evaluator policy are outside proposal control. Builders may edit assigned code; the experimental proposer cannot edit evaluator/input code or launch arbitrary commands.
4. Primary objectives: throughput ↑, TTFT p99 ↓, TPOT p99 ↓. Report both p50s, errors, completion, client lag, backlog and uncertainty. No scalar score or assumed SLA.
5. Group frontiers by compatible workload/cache/execution/measurement identity; also export matched-load comparisons. B0 always appears.
6. Workload construction and sensitivity qualification precede adaptive real search. Fixed shapes are diagnostic, not production realism. Preserve flat and negative results.
7. Distinguish actual cache hits from intended reuse. Cache-off is a valid treatment. Prevent accidental full-prompt reuse and cross-cell carryover.
8. Account for every request, including dependency-blocked/not-dispatched requests, failures and censoring. Missing metrics are not zero.
9. Separate forced output from natural EOS, recorded replay from live histories, and representative from stress workloads. Do not claim identical realized requests for live-history protocols.
10. Persist hypotheses, predictions, evidence and outcomes. Only validated, scoped findings become durable lessons. No hidden chain-of-thought capture is required.
11. Proposer may retrieve read-only evidence and request controlled diagnostics. Evaluator owns measurement and GPU lifecycle; archive logic owns nondominance.
12. Short p99 screens are provisional. Exact fronts are empirical observations, not global-optimum certificates.

## Ownership and parallel build

Agent 3 establishes shared DTO/protocol/schema scaffolding first and owns subsequent coordinated amendments. Keep contract version 0.2 consistent across examples and code.

- Agent 1: `src/inference_autoresearch/workloads/**`, `benchmark/**`, `tests/workloads/**`, `tests/benchmark/**`; trace characterization and workload capability inventory.
- Agent 2: `src/inference_autoresearch/runtime/**`, `evaluation/**`, `deploy/**`, `tests/runtime/**`, `tests/evaluation/**`; environment, telemetry and sensitivity report.
- Agent 3: `src/inference_autoresearch/search/**`, `storage/**`, `cli.py`, `pyproject.toml`, `tests/{search,storage,integration}/**`; coordination, retrieval, learning, reporting and CLI.

Use isolated branches/worktrees, dependency injection and contract-valid fakes. Do not duplicate another owner's subsystem to avoid waiting. Agent 3 coordinates interface changes and merge conflicts. CPU checks can run concurrently. Real GPU experiments, preparation traffic and profiles acquire one controller-owned GPU lock. Three builders do not imply three optimization agents.

## Execution and completion

Implement the mock path first, then doctor, source characterization, pack preparation, B0 calibration, pilot, bounded search and reports. Version changes to the suite/domain; never silently edit a frozen campaign. Do not run an unbounded search while integrating. Reuse weights and compatible compile caches but reset measurement cache state according to the protocol.

When an external dependency is unavailable, complete independent work, write a precise blocker and leave reproducible commands. Distinguish code implemented, mock-tested, trace-mined, traffic-validated, pilot-qualified, campaign-executed and improvement-confirmed. Do not claim any later status from an earlier one.

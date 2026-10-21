# Refined research pack integration — 22 October 2026

## Outcome and implementation plan

The user's objective is useful, falsifiable optimization ideas that reach reproducible implementation and measured serving improvement. The supplied pack is design input; its example B200 target, novelty weight, database layout and cadence are not universal policy. Keep H200/DP4/EP4 and other task profiles valid.

1. **Reuse and durable contracts:** extend existing corpus revisions and hypothesis graph with immutable typed claims, screenings, evaluation plans and attributed decisions. Keep the independent experiment registry. No second source or hypothesis database.
2. **Useful tool surface:** add doctor, claim recording/inspection, hypothesis-linked no-GPU screening, evidence dossier, evaluation-plan qualification, change reports and a thin stdio MCP adapter over the same locked CLI/API.
3. **Research quality:** enforce source-version grounding, external-result versus target-estimate separation, explicit transfer mechanisms, contradictory evidence, missing-baseline deferral, and task-adaptive selection. Gate an executable plan on concrete pins, workload, metric definitions, correctness, cost and stopping rules. Do not convert selection into measured validation.
4. **Demonstrate:** offline complete trace and failure cases, then a real retained-source dossier and a deliberately scoped handoff. Report blocked requirements honestly; do not fabricate model/hardware pins or start GPUs.
5. **Integrate and deliver:** test existing and new research contracts, fast-forward main when ancestry permits, push with the separately supplied write credential, verify remote commit and update VM code without changing serving.

## Reuse map and concrete gaps

| Existing module | Reuse | Gap addressed here |
|---|---|---|
| store.py / github.py / discovery.py | FTS, immutable source revisions, archive/recent cursors, cached providers | Query version identity; durable source-change review; explicit doctor/coverage |
| deep_dive.py / evidence.py | Bounded primary full text, selected PR hydration, pinned code, citations, quote checks | Persist atomic revision-grounded author claims independently of agent proposals |
| hypothesis_memory.py / chat_memory.py | Immutable proposals, baseline/task snapshots, disposition events, source graph | Typed linked screening/plan/decision records; cold-start dossier and reopen triggers |
| controls.py / policy.py | Explicit units, accepted-token progress, conditional ROI, adaptive novelty | Attach screens to exact hypothesis and workload; incomplete target trace stays insufficient |
| experiments.py | Scoped attempts, artifacts and outcome journal | Resolve outcomes into dossier; prohibit component result from becoming service validation |
| foundation.py / journal.py | One writer lock, CLI, snapshots and command journal | Shared callable API for CLI/MCP; structured outputs and explicit unsupported capabilities |
| storage.py / replica.py | Approved S3 CAS publication and verified read replica | Preserve new typed records in existing snapshots; no new cloud provisioning |
| src/inference_autoresearch and retained Bitlane manifests | Existing AIPerf/Mooncake/agent-75 evaluation and serving campaigns | Plans must identify an evaluator's stimulus/observable coverage before adding custom tests |

## Initial state / dependencies

Foundation commit b48f899; origin/main eda47b9 is an ancestor. GitHub read token is working; GITHUB_TOKEN_PUSH is present and used only for Git operations. GitHub backfill continues; its count does not establish exhaustive literature coverage. Workstation is authoritative corpus writer, B200 VM reads S3 snapshots. No need for Postgres, embeddings, Hindsight, another orchestrator or copied production credentials.

MCP will use the official Python SDK as an optional dependency and stdio transport. Direct provider APIs remain the auditable retrieval path; external OpenAlex MCP is optional, not a substitute for our provenance/caching. No client configuration is silently modified.

## Deliberate limits

Provider spend telemetry is not yet a verified billing ledger; unknown costs must stay unknown. Model-produced output remains an attributed proposal and exact quote matching is not factual entailment. No-GPU tools cannot establish a serving gain. Live benchmark execution remains the existing authorized execution workflow. Historical files stay intact; mutable state stays outside Git.

## Implemented integration

The five steps above are implemented in the existing modules plus `research_flow.py`, `eval_plan.py` and the optional `mcp_server.py`. See [the operating guide](../docs/RESEARCH_TO_IMPLEMENTATION.md) and [real-source demonstration](../docs/verification/refined-research-20261022/REPORT.md). The input pack is design provenance, not a second policy authority. No copied schema or mandatory framework is introduced.

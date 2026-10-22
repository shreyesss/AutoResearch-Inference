# Adaptive evaluation and ROI screening

## The decision we need

Research should identify a plausible **change from our current implementation**, the condition under which it matters, and the least expensive observation that decides whether to continue. A scored rubric, component speedup, or fully populated manifest does not establish a service improvement. Novelty is required only when the task asks for it.

Use the task's workload, exact baseline, target metric, allowed changes and budget. For each candidate, distinguish:

| Question | Useful evidence | Appropriate next action when unknown |
| --- | --- | --- |
| Is this already implemented or bypassed? | Pinned source and dispatch conditions | Source inspection, PR discussion/diff retrieval |
| Does the mechanism occur in our workload? | Request/shape/path frequency or replay | Read existing traces; bounded CPU replay |
| Could fixing it matter? | Exposed critical-path contribution, frequency, candidate overhead | Conditional arithmetic or missing-input diagnosis |
| Will the change preserve required semantics? | Differential oracle, cache/state invariants | Small correctness test before performance work |
| Does it improve the selected service objective? | Matched target workload and correctly defined metrics | Controlled serving experiment when authorized |

These are questions, not a required linear workflow. Conflicting sources may send the researcher back to discovery. A baseline already containing the change ends a direct port proposal but can motivate a narrower unresolved question. Missing source access is a blocker, not a negative experimental result.

## What the tools enforce

`screen` stores an immutable hypothesis-linked conditional estimate. Unknown numeric inputs remain unknown. Exposed-time arithmetic accounts for component duration, calls, overlap and committed output progress; it does not extrapolate p99 ITL, TTFT, capacity or dollars from average iteration time. A task-specific minimum gain is optional in the arithmetic tool. An optimistic bound below a requested threshold is a conditional rejection, not a measured failure; inspect assumptions before treating it as decisive.

`eval-plan` has two paths:

| Path | Required evidence identity | Permitted conclusion |
| --- | --- | --- |
| Default `execution_kind=serving` | Exact implementation/container/model/workload pins, controlled design, correctness, evaluator coverage, explicit budgets | Plan ready for human/agent review; never validated benefit |
| `execution_kind=cpu`, `purpose=diagnostic` | Immutable hypothesis baseline ID, probe code revision or retained script hash, hashed inspected inputs, command/environment, observable and decision branches, evaluator rationale, zero GPU budget | Bounded applicability or input-to-ROI investigation ready for review |

Probe code can be pinned with `probe.git_sha` (40 hex), or `probe.sha256` (64 hex) for an ad hoc script whose exact bytes are retained among `probe.inputs`. The SHA256 must match an input hash; a script merely sitting beside a Git checkout must not borrow that checkout's commit as its provenance.

CPU diagnostics do not require inventing an image digest, CUDA version, GPU timing, candidate patch or minimum percentage gain. Their baseline may remain partly unknown; `diagnostic.target_path_status` explicitly distinguishes `observed`, `configured`, `unknown` and `proposed`. Supplied known baseline fields cannot contradict the frozen hypothesis.

Both paths still require a grounded supporting claim and a recorded no-GPU screen. Recording `screen` with missing target provenance intentionally preserves `insufficient_evidence` and null target gain; it can accompany a diagnostic plan. It cannot support qualification. Simulation and agent-estimate inputs also cannot clear a qualification plan, even when their conditional numerical gain is positive. Target-trace/reproduced-measurement labels are provenance assertions, not an automated audit of their scientific validity. Here `purpose=qualification` means planning a controlled target comparison capable of qualifying a change; it never means the experiment has passed. A target-evidence-backed plan may reach review with null numeric ROI (for example, TTFT cannot be predicted by iteration arithmetic). The gate does not demand a guessed percentage before designing that trial.

`ready_for_review` checks completeness and consistency. It **does not** certify that inputs exist, commands are safe or correct, the source claim is true, the experiment discriminates alternatives, or the hypothesis is valuable. The response includes `scientific_validity=unverified` and concrete review questions. The separate reviewer examines those questions. No plan tool runs its command, and `execution_authorized` remains false.

## Minimal CPU plan shape

This is a schema illustration, not a runnable experiment. Replace every placeholder with actual identities and a real bounded probe. The executable synthetic fixture is `cpu_manifest` in `ideation/tests/test_research_flow.py`.

```json
{
  "purpose": "diagnostic",
  "execution_kind": "cpu",
  "scope": "component",
  "baseline": {"id": "IMMUTABLE_HYPOTHESIS_BASELINE_ID"},
  "probe": {
    "git_sha": "EXACT_40_HEX_PROBE_CODE_COMMIT",
    "description": "Inspect whether the null-prefix fast path already exists",
    "environment": "Actual interpreter/dependency versions",
    "read_only": true,
    "command_argv": ["python", "pinned_probe.py", "--offline"],
    "inputs": [{"id": "pinned-target-source", "role": "source being inspected", "sha256": "EXACT_64_HEX_INPUT_HASH"}]
  },
  "diagnostic": {
    "question": "Is the proposed change absent and reachable?",
    "mechanism": "Avoid unnecessary null-entry scans on the free path",
    "target_code_path": "Exact file and function once resolved",
    "target_path_status": "unknown",
    "observable": "Current implementation and dispatch predicate",
    "supports_if": "Old path is reachable and equivalent fast path is absent",
    "refutes_if": "Equivalent optimization already runs on this path",
    "inconclusive_if": "Source cannot be tied to intended deployment",
    "limitations": "Does not measure workload turnover or service latency"
  },
  "evaluation": {
    "existing": [{"name": "Mooncake", "coverage": "not_applicable", "reason": "Serving latency does not identify exact source-path equivalence"}]
  },
  "budget": {"gpu_minutes": 0, "wall_minutes": 5, "max_attempts": 1},
  "stop_rules": ["Stop and report inconclusive if exact target source is unavailable"]
}
```

This is passed to the existing `researchctl eval-plan HYPOTHESIS_ID --record plan.json` or MCP `plan_experiment` tool. It creates a plan record, not a process. `probe.read_only` concerns the serving deployment; a later authorized probe may write its own results directory. A CPU simulation remains component/native evidence even if it predicts a service metric.

## Evaluator choice and honest outcomes

Assess existing Mooncake and agent-75/AIPerf stimuli and observables for the actual question. Reuse their workload controls when they expose the mechanism. A custom probe needs a named gap: for example, source eligibility, a rare cache boundary, or an unavailable internal timing. Explaining this gap is more useful than listing every installed benchmark.

For the previous node run:

- N01's exact-source check can proceed without a running model; failure to locate the matching source remains inconclusive. A transcribed helper passing synthetic layouts establishes only that helper's tested behavior.
- N02's explicit rank bypass rejects a direct affinity-PR port. A placement replay is a distinct question requiring real session/rank/cache traces and EP coupling; a high simulated hit rate alone is insufficient.
- N03's existing MegaMoE overlap implementation must be inspected before proposing another overlap mechanism. A paper's hardware result is background evidence, not our ROI.

Preserve each proposal, source linkage, review, screen, plan and attributed selection decision. Record actual attempts/results separately with their scope. Accepted means selected for the stated next step; `inconclusive`, `error`, `invalidated` and `validated` are distinct experiment outcomes. Reopen a rejected idea only with an explicit new premise, baseline or evidence.

## Verification and limits

Focused CPU tests cover unknown ROI with missing serving pins, forbidden CPU-to-service qualification, zero GPU budget, exact input/source pins, missing falsification branches, malformed sections, and simulated-positive ROI rejection for qualification. Existing serving-plan tests remain in place. These tests validate contracts and persistence, not scientific judgment or serving performance.

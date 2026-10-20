# H200 evaluation contract

This is an experiment design, not a benchmark result. No generation, GPU fixture,
profiling, server restart or candidate deployment is performed by this research
run. The frozen `evalset-contract.json` predates candidate generation. This file
explains how to execute that contract without importing B200 assumptions.

## Control and scope

Use the runtime inventory and installed-source hashes in `baseline/`: eight H200
SM90 GPUs, two independent TP1/DP4/EP4 replicas, two API processes per replica,
seq64, MBT16384, context1048576, graph cap512, FP8 KV/block64, real DSpark k5 with
probabilistic drafts and block rejection, adaptive verification off. Model
revision is `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`; image digest is
`sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`.

Startup logs resolve Marlin experts, AG/RS communication, and host Engram with
`dp_shared_memory=True`. Preserve these settings except for the explicitly
changed factor. Keep request/output/delta logging identical between arms;
disabling it is a separate potential optimization, not an invisible benchmark
cleanup. The H200 graph inventory has target384/draft320 capacity for seq64/k5;
increasing seq128 is a different arm with different graph and memory needs.

Before comparing a patch, attest the runtime again and check exact behavior,
not merely PR merge date. Record patch tip/base/dependency SHAs, image digest,
tokenizer and draft revisions, model configuration, source hashes, topology,
all GPU identities, resolved flags, router source/settings and package versions.
The current DeepGEMM header has the ordering addressed by #448/#59129; run the
affected reference/repeatability fixture before evaluating mHC alternatives.
Passing source inspection does not qualify a cached compiled binary.

## Workloads and decision units

| Cohort | Fixed comparison and purpose |
|---|---|
| D1 cheap decode diagnostic | Reuse the prepared H200 attach-only 1K/1K dataset, 512 distinct warmup and 2,048 measurement requests, exact server token counts, separate cache salts; c8/c64/c256 are node-wide client concurrency. This is not agent-f75. |
| E1-H200 | Preserve native agent-f75 8K/1K, 6,144-token constructed shared prefix, Zipf64, 120s warmup/150s measure, c256/384/512. Explicitly label seq64 H200 adaptation; never call it a reproduction of the B200 seq128 R7b result. |
| E2-H200 | Preserve Mooncake source/window hashes, median/burst/cache-heavy fixed 600s schedules and original custom scorer. Test 1x/1.25x/1.5x/2x timestamp speedup. Extend the frozen grid only to bracket saturation, retaining every failed point. |
| Mechanism-specific diagnostics | Ragged arrivals/idle DP ranks for padding; mixed prefill/decode for coordination; cold/warm and final-rank locality for prefix caching; context bands for sparse scoring; 1–8 actual rows for the small-mHC kernel. Freeze each trigger before measurements. |
| Held-out confirmation | Untuned E1 seed and distinct Mooncake window. Long-context claims need held-out lengths and concurrency, including short-context and single-request counterexamples. |

The exact prepared datasets, seeds, scorer revision and trace hashes must be
frozen before GPU execution. Existing historical hash references are retained
in the prior audit; this run has not regenerated or executed E1/E2 datasets.
Local AIPerf is 0.11.0 while the enhanced evaluator documentation assumes 0.13.0.
Provision an isolated pinned environment and verify its registry/export format
before executing E2/SPEED-Bench. Do not silently upgrade a live service environment.

Use complete A/B runs as replication units. An initial pair can reject obvious
failures. For a small promising effect, use at least five paired blocks with
alternating order, matched warmup, cache state, seed and offered load. Report
paired run-level intervals and baseline drift. Requests and DP ranks are not
independent server replicates. A difference below run-to-run drift is inconclusive.

## Six independent verdicts

1. **Applicability:** installed behavior, architecture, dtype, shape, dependency
   and active backend match the proposed change.
2. **Activation:** count changed-path hits and eligible opportunities. Zero with
   adequate coverage means inactive; unavailable telemetry means unverified.
3. **Correctness:** pass changed-path numerical, graph replay, distributed and
   sampler tests before promotion. Failures block performance conclusions.
4. **Mechanism:** the proposed internal work changes in the expected direction,
   and a competing explanation has been distinguished.
5. **Service value:** unprofiled latency/qualified-goodput results improve at
   matched load without unacceptable quality or tail regressions.
6. **Integration cost:** source-port size, native build, startup, memory/KV loss,
   maintenance and rollback requirements remain visible.

An inactive path is not an invalidated algorithm. A faster kernel with unchanged
service performance is a useful negative result. Missing evidence is not zero.

## Measurement and correctness

Join request/run identifiers through router, API process and final DP rank when
the hypothesis depends on placement. Capture interval deltas from every replica
and rank, retain raw labels, and detect missing samples and counter resets. Save
logical and padded target/draft rows, actual graph mode/bucket, proposed/accepted
drafts, verify steps, delivered tokens, per-rank request counts, cache-hit source,
KV blocks, preemption and the hypothesis-specific CPU/GPU spans.

Compute request TPOT from server-accounted output tokens:
`(last_token_time - first_token_time) / (output_tokens - 1)` for outputs longer
than one token. SSE chunk gaps under speculative decoding are not token ITL.
Report TTFT, TPOT and E2E distributions, errors, exact lengths, client saturation,
replay lag and completion/drain. Keep raw failed points. A closed-loop diagnostic
does not establish sustainable open-loop capacity.

Use short Nsight Systems captures only when counters cannot establish the
mechanism; CPU collective/scheduler questions need CPU sampling/context-switch
capture. Inspect the actual profiler launch and clean-marker contract. Use
Nsight Compute only for an identified kernel. Profiled points never enter the
service frontier. Preserve all-rank coverage and profiler overhead separately.

Scoped correctness includes: shared-plan compatibility/lifetime; changed-input
and changed-length graph replay; FP8 candidate logits and selection including
ties, invalid candidates and causal bounds; expert permutation/scatter, empty
ranks, scales and SwiGLU clamp; mHC independent references and repeatability;
prefix/preemption/cancellation/idle-wake fixtures; and stochastic rejection
distribution tests. DSpark acceptance length alone is not sampling correctness.
For changed precision, approximations or engine, add pinned generation-quality
tasks and real tool/reasoning/tokenization fixtures. Native synthetic sessions
do not by themselves test tool-message semantics.

## Frontier and cost

Production H200 SLOs and the actual node price are unspecified. The existing
manual diagnostic's TTFT<=2s/TPOT<=50ms thresholds are provisional; retain them
as named diagnostic thresholds, not a production commitment. Its >=2% primary
improvement and <=3% secondary regressions are pilot choices. Freeze any
candidate-specific practical threshold and interval rule before its test.

Qualified goodput counts successful requests satisfying both declared TTFT and
TPOT limits, divided by the declared elapsed interval including drain where
the scorer specifies it. Keep the original Mooncake scorer rather than replacing
it with AIPerf's different goodput metric. With full eight-GPU hourly price P:

`cost_per_1000_qualified_requests = P * 1000 / (3600 * qualified_rps)`.

Leave P unset or show explicitly labeled scenarios; do not copy B200's $36/hour.
Build the cost–TTFT–TPOT nondominated set separately per workload from qualifying,
unprofiled points. Preserve HBM/KV capacity tradeoffs and failed load points.
Do not collapse conflicting workload outcomes into one winner without declared
weights. Register plans in hypothesis memory, and record outcomes only after
actual artifact-backed execution.

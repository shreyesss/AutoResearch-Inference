# C24: joint DP dispatch and deployable information

Source analysis only. These are legal constructed inputs, not captured AV choices,
measured timings or performance estimates. The authoritative installed sources
are in [the manifest](source-manifest.json); they match the relevant prior source
chain while preserving the actual installed model-state deviation.

## Four-rank counterfactual

Each of four ranks has five requests, each with one mandatory target token and
up to five draft tokens. AV target graph rules create varlen buckets with request
capacity `min(bucket_tokens,64)` and max query length6. For this range the
configured buckets are8,16,24,32. The inherited draft uses fixed q5 and the
**synced target descriptor request capacity**, not the true five requests.

| Local additional draft budgets [r0,r1,r2,r3] | Local target rows before sync | Synced target rows / request capacity on every rank | Subsequent draft rows / request capacity on every rank |
| --- | --- | --- | --- |
| [25,25,25,25] | [30,30,30,30] | 32 /32 | 160 /32 |
| [3,25,25,25] | [8,30,30,30] | 32 /32 | 160 /32 |
| [3,3,3,25] | [8,8,8,30] | 32 /32 | 160 /32 |
| [3,3,3,11] | [8,8,8,16] | 16 /16 | 80 /16 |
| [3,3,3,3] | [8,8,8,8] | 8 /8 | 40 /8 |

All cases fit the real request bound and max query length. The fixed-k5 AV-off
control has a different target inventory: q6 graph36/request capacity6, followed
by q5 graph35/request capacity7 for this five-request fixture. AV row reduction
is therefore not a guaranteed cycle reduction. The hypothetical AV inventory
must still be attested if an AV service is started.

Source chain: `model_runner.py:1294` calls `get_num_tokens` during local batch
state construction; `:1759` subsequently dispatches and synchronizes. The actual
`dp_utils.py:76` gathers six rows of rank data in one CPU `all_reduce`. It takes
max target tokens, computes agreed query bounds, dispatches the target and
replaces the original token vector with the padded count (`:181–210`). FULL mode
sets sync request capacity from the target descriptor. Shared
`spec_decode/speculator.py:513` multiplies that by draft q5. DFlash
`speculator.py:495` reuses this agreement and selects the draft graph without
another collective.

Thus a local objective that charges its own target bucket plus a request-only
draft cost can prefer a reduction which does not reduce either executed graph
when another rank determines the maximum. Target row capacities alone cannot
quantify accepted progress, attention cost, collective waiting or client ITL.

## What is available when the decision is made

Before the current target DP collective, `get_num_tokens` has local request IDs,
state slots, scheduled draft capacities, non-draft tokens, two-slot stale CPU
confidence arrays, local costs and sampler-logit limits. It has **no current
remote candidate budget curve, remote confidence or remote untrimmed request
state**. The existing CPU collective carries each rank's already chosen token
count, mode, uniform length, maximum query length, ubatching flag and request
count. The public returned sync keeps the common padded counts and request bound,
not the original vector or a curve of alternative budgets.

An exact current-step joint policy cannot simply look up a remote maximum inside
the existing local `get_num_tokens` call. Options include (a) enlarging and
reorganizing the existing collective payload to exchange sufficient candidate
progress/cost state, then making a deterministic common decision; (b) a new
collective; or (c) a stale remote estimate, whose approximation and instability
must be measured. None is an implemented correction here. Enlarging an existing
collective avoids an extra collective count but still changes communication,
controller placement and mode-agreement logic; it is not free.

## Narrow no-new-collective intervention worth designing

A potentially cheaper revision is **fill already selected target capacity after
DP sync**. In the [3,3,3,25] fixture, ranks0–2 pay for target32 and draft160 yet
verify only8 useful target rows. Up to25 local draft tokens were originally
scheduled and the graph can hold30 actual target rows. Before CPU compaction,
raise the stored local draft budget to the maximum supported by that already
selected descriptor, original per-request capacities, mandatory token rows,
max-total-logits minus bonus rows and max-query-length6. On this fixture the
local budget can become25 without selecting a new target or draft descriptor.

The natural hook is immediately after target DP sync and before `prepare_inputs`:
`compact_batch` reads `_batch_budget`; `reallocate_drafts` later reads the same
budget and caps individual allocations by originally scheduled drafts. Both must
see the same revised budget, as must the CPU batch token totals and all derived
query buffers. Do not patch only the GPU selector. Dummy, mixed-prefill, eager,
PIECEWISE, microbatch, partial draft and sampler-chunk cases should initially
fall back unchanged; a first qualified implementation can restrict to the
well-defined pure-decode FULL-varlen case.

This does not remove paid graph work. Its causal claim is increased accepted
progress for a similar cycle, conditional on actual draft confidence and rejection
behavior. Even at fixed graph capacity, useful attention sequence lengths and
sampling/rejection work can change runtime, so cost is not proven constant and
no performance claim follows from the table. Correctness requires valid prefix
allocation, query/cache ownership, EOS and cancellation semantics. Qualification
must compare fixed-k5, stock AV and this locked revision on the same traces and
include controller/coordination/whole-cycle cost per accepted token. This new
revision must be recorded explicitly; it must not relabel the prior synthetic
coupled-cost counterexample as support for measured gain.

## Confidence access

The checkpoint has `mtp.2.confidence_head.proj.weight`, BF16 `[1,5376]`. The loaded
DSpark model exposes `compute_confidence`, but `_sample_sequential` only computes
it when `enable_adaptive_verification` and a non-null learned head both hold.
AV-off traces consequently do not contain valid learned confidence arrays merely
because the checkpoint has the weights.

With AV enabled, `_sample_sequential` computes confidence from head hidden states
and Markov embeddings after drafting. `record_confidences` copies current values
into per-state GPU storage, synchronizes the other copy event, swaps double
buffers and starts an asynchronous D2H copy. CPU budget selection reads the older
buffer, while GPU prefix allocation uses current per-state confidence. Request
addition resets stale values to1 and records pending resets. Instrumentation must
identify cycle/request-slot generation and which confidence age was used; dumping
`_confidence_probs` without the CPU buffer age would not reproduce the budget.
A hypothetical post-sync fill uses the existing stored capacities and can avoid
adding a fresh D2H path, but its selected prefix still uses the installed current
GPU ranking. No confidence calibration or native choice frequency is measured.

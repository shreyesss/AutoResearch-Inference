# C25 native integration: minimal overlay feasibility

Developer source plan, 2026-10-20 UTC, after component qualification and before
native integration implementation/timings. The independent evaluator owns the
new pilot contract and measurement; the root owns resource allocation and all
launches. This plan does not change the component candidate or its contract.

## Lifecycle and exact hook

The base `DraftModelSpeculator.load_model` assigns `self.model` from
`self.load_draft_model(...)` only after that method returns (installed
`spec_decode/speculator.py:224`). The generic adapter reads `self.model`, so it
must not run inside the existing `DSparkSpeculator.load_draft_model` body.

Add an override of `DSparkSpeculator.load_model(target_model)` which calls
`super().load_model(target_model)` first, then invokes the already reviewed
guarded accessor using the **draft** parallel config's TP size and allocates a
single persistent `DSparkFusedMarkovSampler` if eligible. This happens before
initial memory profiling and graph capture. The target/draft models and shared
embedding/LM-head weights are already loaded and linked at that point; the
adapter references existing Markov embedding storage without copying weights.
No SM100 specialization or target-model patch is needed.

Keep the qualified component helper unchanged, but add outer integration guards
for engine `watermark_config is None` (target-only watermark fallback is excluded),
both target and draft TP1, the exact installed V4.1 DSpark model module, and
anchor-as-first q5 layout. The component helper alone checks the draft watermarker;
that is insufficient to exclude a target-only engine watermark configuration.

Initialize the optional sampler attribute to None in DSpark's constructor.
At `_sample_sequential`, if the optional sampler exists, dispatch to the new
wrapper; otherwise preserve the exact existing top-k/unfused function body.
The fused wrapper retains the same `sample_indices` gather and
`compute_draft_logits`, reshapes the unchanged base logits to `[B,5,V]`, gets
anchors from `input_buffers.input_ids[r*num_query_per_req]`, and invokes the
unchanged `model.markov_bias` before every frozen sampler `sample_step`.
The passed state mapping, sample position, temperature, seeds, cache and draft
output buffers are exactly the installed speculator's buffers. No acceptance
prediction is lost in the eligible path: AV is off and the installed
`acceptance_estimator` is None. Confidence paths remain in the fallback.

The FULL graph already captures `_generate_draft`, including backbone and
`_sample_sequential` (DSpark source250–268), so the changed wrapper is captured
in the existing draft graph naturally. No new capture policy, dynamic mode
switch, graph-manager modification or extra collective is required. The scratch
is owned by that speculator and used on its existing ordered draft workspace
lane. Changes to anchors/rows feed the existing fixed-address preparation
buffers; no per-request Python cache is introduced.

## Proposed treatment mounts

1. Modified installed `vllm/v1/worker/gpu/spec_decode/dspark/speculator.py`.
2. New sibling `c25_fused_sampler.py`: byte-identical copy of the qualified
   `developer/candidate/fused_sampler.py`, SHA256
   `7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`.
3. New sibling `c25_adapter.py`: byte-identical copy of the guarded accessor.

The overlay is read-only. Baseline uses the actual installed DSpark source;
identical observation-only evaluator mounts apply to both arms. New pycache and
artifact destinations stay writable outside immutable evidence. Record base and
candidate hashes, image identity, model revision and full mounts/argv. Preserve
all original profiles, source and captured historical runs.

Activation attestation must show every participating rank's eligibility, model
class, TP1/k5, BF16 table/cache shapes, AV off, ordinary sampler, no draft mapping
or top-k, and allocated scratch dimensions. The independent builder can read
these attributes and record actual native graph descriptors/replay. A startup
log stating eligible is insufficient alone to prove replay of the fused path;
require a native graph witness tied to the frozen code/capture identity. Fallback
is semantically safe but an inactive treatment cannot support a timing claim.

## Native timing choices and limitations

Two freshly attested arm starts on the same two-replica profile avoid toggling a
captured graph's Python branch after capture; existing graphs retain their
recorded kernels. Reusing one startup would require safe independent native
captures and scratch/input ownership, a separate intervention design with a
larger qualification burden. The two-start pilot is simpler to audit.

Installed `_dummy_run` plus `StepTimingCollector.collect` already records
same-stream CUDA target-forward and drafter-propose events without CUPTI.
`uniform_decode=True` and `num_tokens=6*requests` select fixed-k5 target shapes;
actual graph request padding still determines the draft shape. Context length
is supported. The collector synchronizes after the block, then resolves all
steps. These mechanisms can supply a declared native graph proxy.

However `_dummy_run(is_profile=False)` constructs `is_padding=True`, zeroes input
token IDs/positions and has no scheduled draft-token/rejection state. Its mapping
is **dense valid arange** (an earlier tentative invalid-mapping suspicion was
corrected after inspecting the constructor). It skips actual target sampling and
calls proposal with manufactured accepted/rejected counts. `valid_dummy_state_slots`
only changes block-table metadata, and `is_profile=True` forces eager execution.
Temperatures/seeds need explicit witnessed setup if the pilot intends temp1.
These timings are not a complete accepted-token decode cycle or a service result.
They can still answer whether the native wrapper/capture activates and whether
fixed-shape native drafting retains a speed improvement, with those limits.

Live controlled request traffic with evaluator-owned timing around actual
`speculator.propose` would exercise valid native routing and state, but requires
new identical observation mounts and careful collection/cleanup. It is not
implemented by the developer. Source-level dummy limitations should guide the
prospective measurement claim, rather than silently changing graph mode.

## Correctness inheritance and new obligations

The qualified component provides exact installed RNG/cache/embedding behavior
under its recorded fixtures and repeated graphs. Do not rerun that entire suite
merely to show activity. Native integration must still establish real model
class/weight/guard activation, native graph and request-state ownership, cache
transport into unchanged block rejection, independent controlled token outputs,
EOS, cancellation and post-cancellation recovery, and all-rank cooperation.
Existing C03 controlled integration fixtures can be adapted by the independent
builder, preserving their scope and unresolved freeform baseline repeatability.
A successful native proxy does not erase those integration requirements or
consume a full service attempt by naming alone. Root/evaluator determine the
bounded pilot allocation and progression after reviewing the concrete overlay.

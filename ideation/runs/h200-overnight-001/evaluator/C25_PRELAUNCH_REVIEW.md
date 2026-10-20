# Independent C25 component prelaunch acceptance

Accepted for one bounded component allocation under
`C25_COMPONENT_CONTRACT.md` and `C25_SHAPE_ADDENDUM.md`, before any candidate
GPU result. Root alone executes and records the 45-minute/one-device limit,
runtime identity, clock/power context, actual resource use and cleanup.

Accepted evaluator harness `tooling/c25_component.py` SHA256
`afce6bcb1df15e89dff89798d0a76b3ac61a9e6a391fcb24dcb099609fca420c` and
candidate `developer/candidate/fused_sampler.py` SHA256
`7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`.
The separately authored harness obtains expected answers from installed
`UnquantizedEmbeddingMethod.apply` and `gumbel_sample`, never the fused
candidate. It verifies two real checkpoint weights and records tensor-byte and
installed-source hashes. Batch-invariant mode fails closed. Installed FP32
Gumbel precision is the default false `use_fp64_gumbel` flag, with no contrary
flag in the prior attested argv; FP64 remains an explicit correctness stress.

Source review checked baseline-repeatability, exact token/cache/sentinel and
step-0-through-3 next-embedding comparisons; independent greedy/tie/rounding
expectations; padded/permuted request state; all declared temperatures and
precisions; six deliberately rejected corruption/seed/rounding/counter controls;
zero-active behavior; and persistent scratch with changing shapes. The final
prelaunch revision performs 128 unchanged and 32 changed-input captured replays
at **all eight shapes and both precisions**, covering the shape addendum rather
than testing only the largest batch. Runtime compilation/correctness remains
unobserved; a source-read approval is not a pass receipt.

The reference anchor index is preallocated, matching the installed loop; extra
expected-embedding calculations run only in fixture generation. Both timed arms
capture the entire five-step component, retain the same bias projection and
have no extra evaluator comparison inside capture. The harness keeps all 30
alternating paired blocks per shape with 100 replays per arm, uses same-stream
CUDA events without CUPTI, and checks outputs/counters after timing. The
predeclared component bootstrap uses NumPy's `default_rng(20261020)` and 10,000
whole-pair resamples with linear percentile interpolation; this engine is frozen
for this component and does not replace the service contract's Python-random
bootstrap. No observed-output threshold selection or timing block exclusion.

Approved in-container command:

```text
python3 /work/tooling/c25_component.py --candidate /work/developer/candidate/fused_sampler.py --model /model --output /out/component
```

Use the original pinned image, physical GPU 0 only, `/work` read-only, pinned
resolved `/model` read-only and unique writable `/out`, no network or package
changes. Preserve failures and stop before timing if required correctness fails.
No automatic repair/retry or model service launch follows this acceptance.

## Prospective materiality clarification

Before any C25 timing output, clarify the component contract's final
"optimistic primary-latency opportunity bound": an additive calculation from
saved microseconds and invocation counts is a **direct-contribution scenario**,
not a hard upper bound on service ITL. Queueing, scheduling and utilization can
amplify or hide a component effect. This supersedes the literal rule to defer
solely because that arithmetic falls below 2%; all measured component gates
remain unchanged.

The subsequent allocation decision must show native call/shape frequencies and
exposure, report the direct-contribution scenario with its denominator, and
state what evidence supports any claimed queueing amplification. Neither a
small direct scenario alone nor unmeasured amplification establishes the service
decision. Expected practical value, uncertainty, integration correctness and
total evaluation cost determine whether to spend a full attempt. The frozen
2% confirmed service criterion and 3% tail guards remain unchanged.

## Final prelaunch native-layout correction

Before root launched any C25 allocation, the builder identified that the
sentinel-stressed correctness buffers were also used for timing. Their extra
row/column/vocabulary padding changes strides from the installed service.
Independently reviewed the narrow correction: only timing now allocates native
contiguous cache `[64,5,129280]` and tokens `[64,5]`, and reports those layouts;
correctness retains the stronger sentinel buffers. Both arms use identical
native timing buffers. No output has been observed and no threshold changes.

The **final accepted harness SHA256 is
`584504d817c0cb64e47cb94e9e536581f84c79361e0cb8c0eb67ad4c0e093482`**,
superseding the earlier prelaunch hash above. Candidate hash, approved command,
45-minute/one-GPU cap and all other gates are unchanged. Root may execute only
this final harness hash; record this completed review's actual hash in its
receipt. Runtime correctness and timing remain unobserved.

A further prelaunch two-line tightening explicitly requires the reference cache
to be finite in every ordinary real-weight fixture before using the comparator;
only separately labeled NaN stress may rely on equal NaN masks. Independently
read and accepted. **The execution-authorized final harness hash is now
`7de227dafd67e555155166aa14d8c069e8f010d77750bcd6d5eceea8a7f46019`.**
This supersedes both earlier prelaunch hashes. Root was notified to hold before
execution while the change was reviewed. The builder is instructed to freeze
the file, and all inputs remain subject to root's before/after hash checks.

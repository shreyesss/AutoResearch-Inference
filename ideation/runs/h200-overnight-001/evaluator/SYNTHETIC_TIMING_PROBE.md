# Prospective C24 synthetic timing diagnostic

Independent evaluator design, before implementation or execution. This is a
single-device measurement-instrument diagnostic, with no model service or
candidate optimization. It may resolve whether the retained trace chronology
symptom reproduces on a deliberately known causal workload before another
eight-GPU model cold start. It cannot validate AV, service latency, production
profile representativeness or all-rank cycle coverage.

## Allocation and environment

Root alone launches one isolated container from the existing pinned image
`sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`,
with only physical GPU 0 visible, no network, no model mount and no package
installation. Record GPU UUID, image ID, driver, CUDA, torch/Kineto versions,
script SHA256, exact command and idle-before/after allocation. Maximum wall time
15 minutes including compilation/warmup/export; maximum one visible GPU and
0.25 GPU-hours. One execution allocation, no replacement after an adverse or
inconclusive result. A coding failure may be fixed before root starts the
allocation; runtime failure remains in the record and needs review before any
new allocation.

The separate evaluator builder writes the script and parser. Root freezes their
hashes after review. The optimization builder has no ownership of this probe.

## Fixed workload and recording

Use a fixed seed of 20261020, FP32 tensors on the one device, and the current
stream. Preallocate two 1024x1024 input matrices and output buffers. Use an
ordinary matrix multiplication into a preallocated output; no arbitrary sleeps,
custom kernel, modified clock setting or correctness-dependent device branch.
Warm up eight executions and synchronize before capture. Retain deterministic
finite-value/checksum sanity results without copying full tensors to the report.

Prepare three modes before profiling: one eager matrix multiplication; one
CUDA graph replay of the same single multiplication; and one CUDA graph replay
containing eight sequential multiplications on that stream. Use the same fixed
inputs and preallocated outputs, and preserve capture/warmup details. Graph
captures occur outside the profiled windows. No service or model loading.

Each mode has two separately named profiler episodes, each with exactly 64
iterations. Every iteration has a distinct CPU `record_function` label binding
mode, episode and index. Preallocated CUDA timing events bracket its known
same-stream operation. Queue the 64 iterations without per-iteration host
synchronization; synchronize once after the last queued iteration and before
ending that profiler episode. Events are measured afterward. No schedule-based
vLLM worker stepping, request-dependent missing work or export concurrent with
an unfinished measured stream is involved. Use torch profiler CPU+CUDA activity,
shapes/memory/stacks/FLOPs disabled, and save all six raw trace files.

This design deliberately differs from serving: events and explicit end-of-window
completion are instrumentation, and any observed operation times are diagnostic
only. Do not add such synchronization to the server based on this document.

## Required analysis and independent controls

For every CPU launch and GPU activity retain exact raw category, event index,
process/thread/device/stream, correlation ID, external ID, graph ID when emitted,
CPU start/end and GPU start/end. CPU scope parents must be CPU user annotations,
never GPU annotation mirrors. Retain runtime and driver categories separately;
state the association domain and prove uniqueness within it. Check emitted
flows/external identifiers as independent corroboration when available, and
report their absence rather than manufacturing them.

Use only explicit unique associations, not kernel names, nearest timestamps or
ordinal launch matching. Source-known iteration/mode identity can check a
proposed association, but cannot replace a missing emitted association. Count
all missing, duplicate and ambiguous mappings, graph/non-graph identities and
any dropped/truncated activity warning. Parser fixtures must reject duplicate
correlation candidates and a removed required launch; adding a deliberately
misleading GPU annotation name must not create a CPU parent.

For each unambiguous pair, report signed GPU-start minus CPU-start and GPU-end
minus CPU-start without shifts, clipping or tolerances. Separately retain every
same-device CUDA-event elapsed interval, trace device activity unions/spans,
mode/episode coverage and per-iteration finite elapsed checks. CUDA-event
relative times have no shared origin with trace CPU timestamps; never subtract
one domain from another. Event durations corroborate positive device execution
and known stream ordering; agreement does not itself calibrate an absolute
CPU/GPU offset or establish client exposure.

## Decision rules

- **Symptom reproduced in a uniquely associated known-causal case:** retain the
  specific event pairs. This supports investigating profiler timestamp-domain
  or association semantics independently of vLLM's model/dummy behavior. It does
  not identify a numerical correction or prove the entire old trace readable.
- **No symptom observed:** report the six finite samples and their conditions.
  Absence in a small synthetic probe does not prove clock alignment under the
  old serving workload. Preserve its chronology failures and continue the
  source/instrument investigation only within remaining allocation.
- **Ambiguous mappings, missing operations, nonfinite events, profiler warnings,
  execution errors or cap exhaustion:** instrumentation-inconclusive, preserving
  all partial artifacts. Do not discard a mode or repeat until clean.

No outcome automatically releases a model recapture. That still needs a
prospective addendum resolving native/dummy identity and all-rank adequacy,
with actual instrumentation hashes, capture windows, perturbation handling and
the unchanged ten-cycle/95%-coverage rules. No service attempt is consumed by
this probe, and no optimization gain may be claimed from its timings.

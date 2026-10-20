# Prospective C24 short-operation, implicated-device diagnostic

This is a distinct instrument experiment following the clean GPU-0 matmul
probe, not a replacement of that result. The first probe used a device whose old
cells also passed and operations substantially longer than the old chronology
offsets. The old anomalies occurred on physical GPUs 4, 6 and 7; GPU 6 had the
largest affected count. A short, minimally queued workload on that specific
device over a finite longer recording has greater diagnostic value than another
model cold start or another identical matmul probe.

## Allocation and ownership

One execution after C25 has completed and released its GPU, using physical
**GPU 6, UUID GPU-63d6a52f-f4e3-722c-2821-4b411f9e2ec8**, alone in the existing
pinned image. Root's separately versioned runner controls exact UUID, timeout,
telemetry, immutable inputs and cleanup. No model mount, service, traffic,
network or installs. Maximum **five minutes / 0.083334 visible-GPU hours**.
Record whole-node opportunity time separately. No repeat or replacement if
clean, adverse or inconclusive. The evaluator builder owns the new probe/parser;
old probe files and outputs remain unchanged. Independent code review must bind
hashes before root executes.

## Fixed experiment

Seed 20261020; one explicitly current nondefault CUDA stream. Preallocate
contiguous FP32 vectors of length 4096, with two independent input vectors and
two output vectors. Retain finite inputs and checksums. Define two ordinary
operations without custom kernels: `torch.add(a,b,out=add_output)` and
`copy_output.copy_(a)`. Prepare one-operation CUDA graphs for each outside
profiling; retain capture details. Warm each eager and graph operation 16 times
and synchronize before recording. Preallocate timing-event pairs outside
recording.

Use one continuous torch CPU+CUDA profiler recording with shapes, stacks,
memory and FLOPs disabled. At fixed elapsed recording offsets **0, 20 and 40
seconds**, run these four modes in this order: eager add, graph add, eager copy,
graph copy. Each mode has exactly **128 iterations**. CPU labels bind epoch,
operation, execution mode and iteration; all 1,536 labels must be unique.
Record actual epoch starts/lateness and do not substitute later windows.
Start each epoch no earlier than its fixed monotonic deadline; if work itself
overruns, record the delay and continue the declared remaining modes once.

Each iteration brackets its operation with same-stream CUDA events and waits
for the end event before the next iteration. This intentional synthetic-only
per-iteration completion keeps work from hiding a small clock-domain error
behind a long queue. It is **not** a proposed service synchronization change or
a usable latency benchmark. Waits between epochs must be finite and at most
20 seconds each. After the last iteration, synchronize the stream, end the
recording and export one raw trace. Retain all 1,536 event elapsed intervals and
exact finite add/copy output checks against independently computed expected
values. No clocks, timestamps or parser tolerances are adjusted.

## Analysis and falsification

Use the same explicit unique-correlation and CPU-only annotation-parent
principles as the accepted first probe. The new parser must independently
retain raw category/event index, runtime/driver launch, external ID, graph/node
ID when emitted, device/stream and all signed CPU/GPU offsets. No name-based,
nearest-time or ordinal association fallback. Require a consistent positive
device-activity multiplicity for each operation and equal eager/graph
multiplicity for that operation across all fixed epochs; copies may be emitted
as memcpy or a kernel, and the actual category must be reported. Explicit
graph-launch association is required for graph modes. Missing graph/node IDs
are reported as limited metadata; they cannot be invented, and any claimed
complete graph-node accounting remains unqualified without them.

The frozen analysis must reject duplicate/missing launch records, GPU annotation
mirrors as CPU parents, conflicting external IDs, incorrect scope inventory,
missing device activity and a dropped iteration. Report epochs separately;
do not select a favorable operation/window. Inspect all console/profiler
warnings and finite positive event intervals. Keep CUDA-event relative duration
separate from absolute trace CPU/GPU timestamps. Report observed operation
durations so a negative result cannot conceal that operations were too long.

If a uniquely associated known-causal operation ends before its CPU launch
start, retain the exact event pair as a reproduced chronology symptom. That
supports a timestamp/association interpretation problem under the stated
conditions; it still does not identify a correction or validate all old
activities. If no symptom appears, the old problem remains unreproduced even
on an implicated device with shorter low-queue operations. Missing associations,
coverage, finite outputs or cap completion are instrumentation-inconclusive.
Partial observations remain available, but no all-modes adequacy claim is made.

Regardless of result, this completes the additional small diagnostic allocation.
No fitted shift, retrospective old-verdict promotion, automatic full-model
recapture or full service attempt follows. A future serving measurement still
needs real/dummy identity, collective/export coordination and the original
all-rank adequacy gates; this isolated probe cannot supply them.

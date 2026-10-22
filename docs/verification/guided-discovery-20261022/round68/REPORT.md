# Round68 — omit two superseded metadata publications in adaptive verification

**One selective author direction, AV68-01: deferred pending independent review and native validation. No typed creation, GPU execution or performance claim.** This continues the component parked in round65; it is not a second independent discovery of that component, and it does not broaden HM65's sampling-state dirty flag.

Planned baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`: Flash1017 checkpoint `1bae0e1088993b9b82de08f59de5be5a34e42170`, callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`, B200 TP1/DP4/EP4, DSpark5/temp1/top_p1. Source compatibility is conditional on adaptive verification actually being enabled and drafts scheduled. No live attestation.

## Decision gap and prior recall

Two complete compact pages cover145 canonical cards. The operation differs from MP17 sparse-index publication reuse, RD02 host-runner construction, RUNTIME-R2-01's already-existing DP agreement reuse and CF59's projection/sampling overlap. Round14 already warns that AV's CPU/device spans differ; its context-row trimming does not remove these copies. Round55 consumes actual history positions. The precise overwritten-copy lead was explicitly parked, uncounted, in round65. `prior-comparison.json` retains the scope and inventory hash.

No new online query was run: exact producer/consumer source can resolve this gap, while another generic host-overhead paper cannot prove which metadata values are read. Recent PR62748 and its exact three-file diff/head were reused from round65, with original retrieval receipts. Its pooled staging still performs both subsequently superseded copies. This is a source-driven continuation, not new paper yield. A first recall with unsupported limit200 failed and was corrected to two100-item pages; the empty failed output and command journal remain.

## Actual source path

`GPUModelRunner.prepare_inputs` constructs general metadata before the AV-specific replacement:

| Step | Current operation | Relevant consumer |
|---|---|---|
| model_runner1416–1419 | Build CPU cumulative logit counts and publish an allocated device `cu_num_logits` | No device read before1450 overwrites the local reference in the active AV branch |
|1422–1435 | Select AV only when scheduled draft dictionary is nonempty; compact CPU token budget | Keep this entirely |
|1439–1447 | Build full CPU query-start array, including padding, and copy into persistent `input_buffers.query_start_loc` | No content read before AV overwrites every element |
|1448–1452 | `reallocate_drafts` returns manager-owned cumulative logits, same persistent query-start buffer, actual draft budget | These are the values downstream sees |
|1453 onward | Expand row mapping, slice padded metadata, prepare prefill/positions, combine tokens, prepare attention | Must consume unchanged final values |

The AV manager is constructed with **the same** `self.input_buffers.query_start_loc` object at model_runner700. Reallocation writes index0=0, cumulative active entries1..N, and every remaining query-start entry through capacity with the final token count. It returns its own `_cu_num_logits[:N+1]`, also initialized from index0 and a cumulative sum. Neither computation reads the overwritten general device values.

Therefore guard exactly two publications:

1. general `async_tensor_h2d(cu_num_logits_np, device=...)` only when **not** `(manager present AND nonempty scheduled drafts)`;
2. query-start publication only when local `adaptive_verification is None`.

The AV replacement remains at its existing point. This is a copied-AST proposal, not a patch to the runtime repository. A production implementation should express the effective AV gate once to avoid future branch divergence.

## What remains necessary

Keep CPU `cu_num_logits_np`, `query_start_loc_np`, assertions, compact_batch, original scheduled-token upper bounds and all CPU slices. Under partial AV budget, CPU counts intentionally distribute drafts evenly and can differ from device allocation. Budget0 has a special exact CPU cumulative-logit result. Fast-prefill and later InputBatch metadata still consume CPU values.

Keep the request-index mapping H2D, scheduled-capacity H2D where needed, non-draft-token H2D, device budget selector, all cumulative sums and padding writes. No confidence/acceptance logic, random draw, token choice, DP collective, KV operation or numerical model operation changes. This is not eliminating AV itself or assuming CPU spans equal GPU spans.

## Branch, graph and lifetime limits

- **Manager absent:** both general copies remain.
- **Manager present but no scheduled drafts:** effective AV is None; both original paths remain, including the general no-draft `num_new_sampled_tokens_per_step != 1` branch.
- **Scheduled drafts but chosen budget0:** the dictionary is still nonempty; reallocation writes complete zero-draft metadata, so both publications can be omitted.
- **Partial/full budget and mixed prefill:** actual per-request device counts still come from reallocation, not the CPU evenly distributed approximation.
- **FULL graph:** final query-start pointer is the same persistent object as before; preserve its whole-capacity padding, then slice to `num_reqs_padded+1`. General temporary cumulative logits was already discarded in the baseline.
- **PIECEWISE/eager:** retain the same final arrays and consumer ordering. No new graph capture is introduced.
- **Zero-token/dummy rank:** source takes its existing early-return or `InputBatch.make_dummy` branch rather than this real prepare_inputs path. Do not apply an unrelated blanket copy skip to dummy/capture setup.

Unlike HM65's dirty-state arm, this proposal introduces no cached published version, rotating pool or cross-step retained pointer. The two writes are overwritten in the same step on the ordinary current-stream path. Existing asynchronous reader/graph contracts still need native verification, but no new ring-retry protocol is part of this change. Preserve existing exceptions/abort behavior; do not invent automatic recovery.

## Executed CPU falsifier

`metadata_probe.py` extracts the exact source prepare_inputs metadata phase through the padded slices, and the full exact compact_batch/reallocate_drafts methods. One copied-AST variant guards only source lines1419 and1447. It executes with stdlib vector/cumsum stand-ins and manually supplied valid capacity allocations; no target imports, tensors, GPU or native selector.

Fourteen paired controls cover:

- budget0/full/partial;
- one request and mixed three-request prefill/decode metadata;
- FULL-style padded capacity5 and unpadded/PIECEWISE-style slices;
- manager absent;
- manager present with no draft tokens, including two-bonus-token general branch.

All compared CPU and device metadata values and the first expanded-index consumer outputs agree. Exactly two copy-call records disappear only in active AV+scheduled-draft cases. The persistent query array begins **unwritten**, so the adapted result must be fully initialized before the first consumer; FULL padding is checked in the returned slice. Two deliberately unconditional-elision controls fail on missing general cumulative logits or unwritten query values.

This is finite control/dataflow evidence, not native Torch integer-kernel, stream, graph, selector or complete-runner proof. Later attention/prefill kernels are source-inspected consumers, not executed by the probe. The probe does not establish actual AV activation frequency or latency.

## Work removed and relevance

For N requests and capacity R, logical host→device payload omitted is:

`4*(N+1) + 4*(R+1)` bytes per eligible step.

`async_tensor_h2d` may first allocate/copy a pinned contiguous host staging tensor. The temporary cumulative-logit path also allocates a device result; the query path writes an existing buffer. Thus this removes two helper invocations, two explicit copy submissions and associated staging/allocation work in the actual eligible path. It does not establish that both copies each cost a fixed launch latency or that all their bytes reach HBM.

The byte count is small. The plausible benefit is fixed host/transfer overhead, especially when request counts are small, and may already be hidden behind device work. If eligible-step fraction is p and exposed eliminated cost is H, mean step reduction is at most p*H before any guard overhead. Neither p nor H is measured. No B300 donor timing, PCIe bandwidth calculation or graph-launch count is converted into client ITL gain. C025/CF59/HM65 benefits are not added to this bound.

## Next useful test and stop conditions

The source test removes the most immediate falsifier: a necessary pre-reallocation consumer or incompletely overwritten padding. A later authorized native differential should compare original/adapted InputBatch device metadata at the existing synchronization boundary over empty/full/partial budgets, mixed requests, graph modes and changing padded shapes; compare final seeded outputs/RNG progression. Do not add a production synchronization solely to recover CPU spans.

Then paired unchanged standard agent-p75/Mooncake runs can test the frozen long-output ITL objective and separate tail/TTFT/E2E guards, with actual effective-AV/draft-eligible counters and a host/device timeline. No new workload is required to invent exposure. If AV is disabled, zero drafts are scheduled or transfer costs are hidden, this arm is inactive or unprofitable and should be parked. A tiny host microbenchmark win alone does not qualify service improvement.

## Yield and provenance

Zero new queries/fulltexts and zero new provider calls. One previously parked component advanced into a concrete deferred author direction; zero typed/canonical identities, implementation acceptances or service wins. Sources reuse exact known identities/revisions; source-manifest and original PR retrieval receipts remain. No GPU/native/model imports, serving changes, canonical/cloud/Git writes occurred.

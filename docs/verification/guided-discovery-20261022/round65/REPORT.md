# Round 65 — selectively avoid unchanged sampler metadata publication

**Disposition: one source-backed deferred author direction, HM65-01. No typed hypothesis, implementation qualification or service win.** The proposed intervention is small and concrete enough for a future bounded experiment. Unknown CPU exposure limits the forecast, not the validity of investigating it.

Target is the planned Flash1017 checkpoint `1bae0e1088993b9b82de08f59de5be5a34e42170`, callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`, B200 TP1/DP4/EP4, DSpark5, temperature1/top_p1. Baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`. No live deployment equivalence is claimed.

## What adaptive discovery changed

Complete compact recall returned143 canonical cards; source-specific62748 recall returned0. MP17 reuses physical sparse-attention mappings; RD02 caches host runner construction; RUNTIME-R2-01 rejects repeated DP synchronization because native DSpark already inherits it. Their actual operations differ from static sampling-parameter publication. Current standalone reports and exact62748/idle-sampler wording search did not expose an existing same-component card. This is a scoped recall result, not proof that every unpublished note was searched.

One dated arXiv query (August1–October22) returned10 papers. All abstracts were read, zero fulltexts selected. Most hits concern KV/expert offloading, SSD restore, CXL, model-changing quantization or unrelated watermark/observer work. They did not answer the concrete host-step question. `paper-dispositions.json` preserves every hit and the narrow reason. No artificial paper citation was added to decorate a code-led result.

Four local PR searches then found **vLLM#62748**, whose actual three-file diff changes precisely this host path. Public detail and diff were retained; normal `investigate` fetched three files at exact head `mgoin/vllm@19dfac35aae5e12973af9fc8d759445f624c9656`. The PR is open at observed retrieval. Its broader whole-sampler gate creates a callback-contract concern, motivating selective reuse. Related62749/61868 opening bodies were triaged, not represented as newly audited diffs. Search and failed-tool receipts are retained; no new tool implementation was needed.

## Exact current operation and proposed change

`GPUModelRunner.add_requests` calls `Sampler.apply_staged_writes` even with no new requests. `SamplingStates.apply_staged_writes` unconditionally refreshes five full-capacity arrays:

- temperature, top_p, top_k, min_p: four32-bit arrays;
- effective seeds: one64-bit array.

The narrow proposal adds a conservative dirty flag **only inside SamplingStates**. Initial dirty=true; mark before admission/reused-slot mutation; clear only after all five original publications succeed. A clean step reuses the already published contents. Keep `Sampler.apply_staged_writes`, every custom/native processor callback, thinking-budget state, logprob state and trace replay running with their current per-step semantics.

This differs from copying the donor wholesale: donor moves the entire sampler flush under `scheduled_new_reqs` and changes the processor interface documentation. Existing custom processors may depend on the old per-step contract. No callback-contract change is needed for HM65-01.

Seven AST-observed host writes to the five arrays occur only in the exact constructor and `add_request` (two initialization fills and five indexed assignments). A literal inventory over the retained vllm Python tree found31 references to `sampling_states`; no additional direct writer was found. Explicit and generated seeds are set at admission. Trace replay overwrites sampled outputs using its separate trace state. PPHandler transports sampled outputs, rather than these static arrays. This does not certify arbitrary aliases or external plugins: any external writer must participate in invalidation or disable the optimization.

## These are UVA publications, not five DMA launches

The exact class is **UvaBackedTensor**, which owns a UvaBufferPool. `copy_to_uva` rotates that pool, copies CPU data into pinned host storage, and assigns a new `.gpu` view. On the UVA path, removing five publications removes five CPU-to-CPU copies/pool rotations and `24 * max_num_reqs` logical bytes per clean step. It does not eliminate five explicit host-to-device DMA launches. The non-UVA fallback uses explicit copies and must retain its own correct behavior.

This pool already exists in the selected arm; it is separate from donor62748's newly introduced InputBuffers pools. Therefore skipping publication changes pointer rotation even in the narrow arm. Clean reuse is plausible under immutable contents and the existing outstanding-step bound, but graph argument binding and reader retirement require later native validation.

**Failure is not a safe automatic retry guarantee.** A partial five-array publication can advance one pool before another copy fails. With depth2, retrying immediately can rotate the first array back onto an outstanding reader's slot. The retained symbolic negative reproduces this conditional schedule. On copy exception, keep dirty state and abort normal processing or retire affected readers before retry. The successful scalar dirty-protocol retry checks content/seed bookkeeping only, not native lifetime safety.

## Executed CPU evidence and limits

`control_probe.py/json` extracts unchanged target/donor admission methods:8 controls show target's empty-admission sampler callback still runs, donor's does not. An extracted exact SamplingStates flush performs five fake copy calls. Four list-backed adaptive-verification cases establish that the chosen manual allocation overwrites every query-start position including padding, independent of prior contents. Those stand-ins do not execute the native confidence allocator or CUDA code.

`dirty_protocol_probe.py/json` wraps the unchanged SamplingStates admission/flush methods in a **proposed protocol proxy**. Seven cases cover initial flush, idle skip, batched admissions, stable generated seed on idle, reused slot, failed-copy dirty preservation and content retry. All seven outer processor callbacks still run. An untracked host write without invalidation leaves stale published contents, intentionally detecting the missing-writer contract. `retry_ring_negative.py/json` adds the independent native-recovery warning above.

These are source/control diagnostics. No target implementation was patched, no native UVA allocation or graph was executed, and no latency was timed. Test counts are not serving coverage or proof of exact decoding.

## Other donor components kept separate

1. **AV overwritten-copy lead:** in the scheduled-draft adaptive-verification branch, general cu_num_logits construction is replaced by manager-owned data, and reallocate_drafts rewrites the entire persistent query_start_loc. CPU metadata remains needed. These two potential copy eliminations are parked separately; branch, padding and graph proof must precede porting. They are not counted as another hypothesis here.
2. **InputBuffers pinned pool:** donor avoids repeated pinned allocation for mapping/cu/query arrays but still copies data, including the AV-overwritten work. Lifetime/capacity handling and exposure differ from SamplingStates dirty gating. Parked control, no bundled gain.
3. **Whole-Sampler admission gate:** direct port not admitted because of custom per-step callbacks; its five-static-array component is retained above.

## Relevance, bounds and next experiment

Long-output serving can have stretches without admissions while the same requests continue decoding. Whether this produces appreciable exposed host time depends on actual turnover, batch capacity, pipeline overlap and client streaming. No exact compatible timing or clean-step frequency was recovered here.

If clean-step fraction is `p` and exposed refresh cost per clean step is `H`, optimistic mean step reduction is at most `p*H` before guard/recovery overhead. Both are unknown. Five array copies and logical byte counts are not an ITL forecast. Donor author timings on B300/small OPT/Qwen models are not transferred to Flash1017/B200. GPU-dominated serving may show no improvement despite less host work.

The fastest next falsifier is a bounded lifecycle audit/native control once authorized: verify all mutation entry points, initial flush, queue/graph pointer binding, admission batching, slot reuse, explicit/generated seed, custom callbacks and reader-safe failure recovery. A missing writer or a captured stale pointer rejects the naive implementation. This packet completed only the source/proxy portion.

Then run paired unchanged standard agent-p75 and Mooncake workloads, collecting actual admissions/clean steps and host-to-client release timing. Freeze the existing long-output ITL objective with its separate tail/TTFT/E2E guards; do not inherit donor thresholds. Include turnover-heavy negative controls and seeded differential outputs. No novel benchmark is required to claim relevance, but actual exposure instrumentation is required before claiming gain.

## Yield and remaining uncertainty

One paper query,10 abstract-level hits,0 fulltexts; four canonical local PR searches and four isolated selected-corpus replays; one PR detail+diff pair; three pinned donor-code reads. One deferred author direction; zero typed creations, implementations or service qualifications. This is known upstream work selectively adapted to a stricter callback contract, not a novel algorithm claim. The evidence supports a small future experiment, not ranking it above PJ01/CF59 without exposed-time measurements.

All source bodies, exact short quotes/revisions, query hits/edges, command journal, prior comparisons, failed path/CLI/quote checks, CPU scripts and outcomes are retained. No GPU, native model imports, cloud/canonical writes or serving changes occurred.

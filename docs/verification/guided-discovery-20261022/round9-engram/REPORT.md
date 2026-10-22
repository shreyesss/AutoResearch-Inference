# Round 9 — Engram host lookup audit and selective component recovery

## Decision

**EG01: defer implementation; advance only a bounded representation/eligibility audit.** Recover the **unsharded/shared-host direct-MXFP8 staging component** from closed vLLM PR [58766](https://github.com/vllm-project/vllm/pull/58766), adapting it to the pinned engine's existing prefetch lifetime. This is known upstream work omitted from the merged DP-sharded implementation, not a newly invented algorithm or a measured serving improvement.

**EG02: defer software hot-row caching/dedup pending trace evidence.** October STAPLE supplies a transferable inference-only component despite being primarily a training paper. But repeated rows can already remain in the hardware cache, and the cache admission/lookup work and HBM opportunity cost may exceed any residual saving. No target reuse/traffic trace is available. No cache implementation is proposed yet.

No GPU, CUDA, MPS, live-node probes, model execution or serving changes were performed. No speedup or real checkpoint numerical parity was measured. Both directions are deferred; the diagnostic below changes how we test EG01, not its production status.

## 1. Actual route at the pinned source

Pin: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`. Target model metadata: Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, retained from prior research. This is a source/model-config audit, not confirmation of the running image.

1. `config/engram.py` defaults to host offload. Shared host tables can be selected for colocated DP replicas, subject to configuration, topology, `/dev/shm` and availability checks. Do not derive effective settings from DP4 alone.
2. `ParallelEngramEmbedding` sets its effective `dp_size=1` when `dp_shared_memory` is true. Shared host memory therefore avoids Engram DP collectives.
3. `nvidia/model.py:1027–1037` stages Engram rows before decoder layers. If no `EngramBatch`, each Engram layer prepares its own rows.
4. `EngramBatch.create` at `common/engram.py:1443` rejects `table.dp_size==1`; it also requires TP1, head dimension divisible by128, no LoRA, and the exact supported MXFP8 consumer ABI. Thus **the shared-host branch does not enter the packed DP batch/peer path**.
5. The shared-host route already prefetches on a dedicated stream, records a per-layer event, uses persistent buffers, sorts sufficiently large row sets, and switches large lookups inline. These mechanisms are not missing proposals.
6. Its lookup reads FP8 values plus UE8M0 scales from host/UVA, multiplies them on GPU, and stores BF16. `Engram.forward` feeds these BF16 values to `wkv`; FlashInfer MXFP8 consumers quantize tensor inputs, while accepting `QuantizedActivation` without re-quantization.
7. Two Engram layer IDs are configured: **1 and14**, not all40 layers. The DSpark model constructs three draft layers without `engram_layout`; the decoder-layer default is None. There is no basis for multiplying Engram savings by five Markov sampling steps or three draft layers. Target prefill/verify forwards may hit Engram when real hash state is present; exact frequency and shape remain workload measurements.

## 2. What the donor actually supplies

PR58766 head `5030d5dd66884830e5b20149218ca27e9864901b` directly writes unsharded FP8 values and F8_128x4-swizzled scale bytes into persistent buffers, then returns a `QuantizedActivation`. No unpack kernel is required in its unsharded route. Its explicit consumer check is important: the quantization key alone does not encode scale layout. W8A16 Marlin is not a candidate because it consumes BF16 and did not incur the MXFP8 requantization.

The PR is closed/unmerged. The fetched issue comments contain a merge-conflict/rebase message. That demonstrates a textual conflict, not proof of functional rejection or the entire closure rationale. Model evaluation remained pending in the body. Author-reported tests and timings were on GB300, not this B200 deployment.

Merged [59923](https://github.com/vllm-project/vllm/pull/59923) keeps packed rows through DP-sharded exchange and into `wkv`, but explicitly preserves the prior BF16 path for shared tables and single replicas. Its code is already in our pin. **Do not port its exchange machinery into the no-exchange shared path.** Recover only the direct producer/consumer component, preserving the current prefetch event, stream lifetime, sorted lookup and graph-replay behavior.

### Work and ROI boundaries

- Both paths read the same source FP8+scale bytes from host:256+8 bytes per head row for256-wide rows. **There is no claimed PCIe-byte reduction.** The shared path has no Engram DP exchange to shrink.
- The candidate removes GPU BF16 conversion/staging and an MXFP8 activation quantization call. Raw stored FP8 payload is smaller, but scale padding means total output writes are not uniformly smaller: at one token,6144 values plus24576 padded scale bytes exceed the12288-byte BF16 payload. Native equation diagnostics preserve this counterexample.
- PR58766 reports about1.5–1.6us removed per layer for small host-backed shapes on its GB300 setup, and49.7us at16384tokens. These are opposing materiality evidence for a large standalone decode win, not B200 predictions. Do not sum them as measured service gains.
- The maximum service gain is bounded by **exposed conversion/requantization on the actual critical path**. Lookup overlap, graph mode, queueing, accepted tokens per DSpark round and other work determine whether removing it changes ITL.
- Existing A01 WKV lookahead is a different intervention: it moves projection execution earlier. EG01 changes projection input representation. They may combine, but first evaluate EG01 alone; a combined claim needs producer readiness and MegaMoE fence checks and cannot double-count the same critical-path time.

## 3. Representation audit: why equivalence is a gate

Executed `python3 representation_audit.py` using standard-library CPU arithmetic and AST-extracted pinned scale-index helpers only.

-13shape cases covered empty and128-row padding boundaries; extracted F8_128x4 offset equations are bijective over each allocated scale region.
-3556 finite FP8/scale combinations in donor-like moderate scale range120..133 round-trip through the scalar BF16 model exactly.
-Ten retained low-scale counterexamples disprove the unrestricted claim that *all* FP8×power-of-two values are exactly BF16-representable. Tiny values can underflow. This does **not** show such values exist in the checkpoint or predict GPU behavior.

The fixture does not execute the FlashInfer quantizer, either GEMM backend, CUDA denormal handling, loader, stream synchronization, staging writes or real weights. Layout coverage is not runtime parity. Donor tests use random synthetic weights/moderate scales and a real CuTe test according to source, but those tests were not run here.

### Bounded remaining CPU work before any port

1. Capture effective per-layer `wkv` consumer names, Engram mode and source/digest from saved deployment artifacts when available; preserve unknowns if not available. No live GPU probing during this task.
2. Inspect actual checkpoint table/scale ranges from a bounded CPU reader or supplied tensor metadata. Verify scale dtype/zero handling and finite FP8 range; do not download huge weights merely to pass this gate.
3. Model swizzled output on varied token/head counts, dead IDs, sorted permutations and padded last tiles; verify byte identity to table rows, with intentionally dirty scale padding and full-reference fallback.
4. Review the two pinned consumer contracts separately. Arithmetic value equivalence alone is insufficient to certify exact GEMM outputs or greedy tokens.
5. Preserve the native prefetch event and buffer-lifetime guarantees; repeated graph-shaped calls must refresh values and padding. No new collective is allowed on this path.

## 4. Future evaluation design, not executed

First correctness: actual checkpoint rows/scales; both eligible CuTe and CUTLASS consumers; direct vs current BF16→requant `wkv` output; invalid/padded hashes; alternating token counts1/7/127/128/129/130; sorted/unsorted lookup; eager/full/breakable graphs; sleep/wake; repeated fresh input; then target-only/native-DSpark token differential and relevant quality guard.

Then performance: paired A/B on unchanged deployment with current shared route versus direct packed shared route. Keep images, weights, DSpark policy, workload hashes, arrival rate/concurrency and warmup fixed. Measure lookup, exposed requantization, WKV, prefetch waits, total target forward, committed tokens per round, TTFT, long-output ITL, tail guards and goodput. Kernel savings without service gain remain a rejected service optimization.

**Use existing agent-p75 and Mooncake first.** EG01 changes the same target forward input representation regardless of text contents, so no new serving workload is required merely to see activation. Add a small correctness/shape microtest because neither load generator certifies packing or graph lifetime. Realistic hash diversity/cold vs repeated hashes are needed to interpret EG02's cache value; existing benchmark renderer/payload traces must establish this before proposing a custom cache benchmark. No extra evaluator is justified just by a paper having different workloads.

## 5. Paper-led component selection and exclusions

STAPLE arXiv2610.12599v1 §9.1 describes prompt-token dedup, an LFU GPU cache, pinned-host miss staging for prefill, and direct registered-host reads for decode. Its training/upcycling is excluded, but its inference memory ideas were **not rejected just because the paper trains weights**.

Transfer limitations: STAPLE tables are token-indexed and reuse one token inverse map across layers; our Engram hashes depend on n-gram history, head and layer-specific tables. A cache key must include model/table revision, layer, head/row identity, and representation. Token ID alone or cross-layer numeric hash equality is unsafe. Cache-hit bookkeeping, HBM reservation, stale pointers after wake and traffic already served by hardware caches are costs. PR59923 explicitly observes repeated prompts/decode tokens hiding lookup cost in its setup.

Other screens: generic prefetch/sorting/DP exchange duplicate installedcode; SGLang44028 projection lookahead duplicates A01; FlashInfer6358 host cache targets disk PLE rereads, not our resident host tables; Mooncake4242 many-small remoteRDMA gather targets a transport absent from this local-UVA route; MemoryAttention/STAPLE architecture training is not eligible under frozenweights but systemscomponents remain reusable; provenance paper is correctness context, not a demonstrated current missing latency component.

## 6. Actual search, failures and yield

Two bounded online calls: OpenAlex broad embedding/dedup/cache search returned8hits; adaptive arXiv Engram-specific search returned1mirror of STAPLE. **Eight unique paper identities, not9 independent papers.** Local corpus search retained33records, then exact-reference lookup for58766/57893/56989 returnedzero. Following59923's reference online recovered58766 and its pinned files. This is a useful corpus-coverage gap, not evidence the tool searched exhaustively.

The first `init --defer-snapshot` attempt failed (init without this flag succeeded), the first agent plan had invalid string observations (corrected to schema objects), and an attempted `--query` flag was invalid (paper-search takes a positional query). No provider calls occurred in those failures. A local HTML text conversion attempted an unavailable bs4 dependency, then used the standard-library HTML parser. All successful paper receipts and journals are in isolated `state/`; no canonical writes or snapshots to S3 here.

**Yield:**2new scoped directions considered,0validated improvements,0implementation promotions. EG01 is a concrete old-component recovery with a verified source gap; EG02 remains an exposure-gated research lead. Independent review pending at initial report creation. Exact candidate/review states are in `candidates.json` and appended review receipt.

## Independent review and final freeze

`../review/round9/REVIEW.md` and `review.json` retain EG01 deferred and EG02 as a low-priority discovery lead. No blocking factual correction. Added explicit gates: actual SM100 FlashInfer cute-dsl quantizer (the torch reference is not its execution); lookup scale-byte0 semantics; dirty padding across130→1→129 tokens; values and scales must share the existing per-layer completion event. Native host bytes remain unchanged. Review is source-only; zero GPU/model execution.

# Round 117 — the controlled packed-stride comparator remains unlocated

## Decision

**Zero new hypotheses; retain round 93's physical row-co-location component as conditional research.** This bounded follow-up does not recover the executable comparator behind PR44521's reported native separate-plane versus native packed-row result. It establishes why the two released benchmark programs and the small correctness tests cannot substitute for it. The reported result remains useful author evidence motivating a controlled experiment, not reproduced evidence for c455 or proof that EngramStore improves serving.

Round116's frozen packet is unchanged. No native code, model, GPU, build, benchmark, cloud or canonical operation ran here.

## Coverage and provenance

Read both complete PR bodies and file lists: SGLang44521 at `70915471caa457d1482083bd40a98b1ca9a85953` (12 changed paths) and Mooncake4701 at `76e15dc913a160b66382a453ae1257f1c2941183` (19 changed paths). Their controlled-experiment prose repeats the same evidence, not an independent replication. The body identifies the tested Mooncake implementation as `e3d395959eee`; later source-only moves are author assertions, not independently verified equivalence here.

Six complete added files were reconstructed from retained API patches and checked against their exact Git blob IDs. Two modified companion files were retrieved through normal code-only `investigate`: no paper selection, repository hydration, citations or model reasoning. Read the two benchmarks, two tests, native host-registration/CUDA gather sources and two documentation files. Reused the exact target Engram and adapter source identities from round116.

The three Actions artifact listings linked by SGLang's body each returned `total_count: 0`. This excludes downloadable Actions artifacts at those endpoints at the observed time; it does not inspect job logs, private/unlinked experiment files or prove the harness exists nowhere. No comments endpoint was queried; the retained PR details report zero issue comments. Inline review discussions were not exhaustively searched.

Network: two explicit Mooncake PR API GETs, two normal-tool pinned-file cache misses, three Actions artifact metadata GETs. No failures in those reads. Six source files reused patches without HTTP. Zero new paper queries/fulltexts, zero native tests, zero measured performance results. Initialization was awaited without defer; later isolated commands deferred publication as instructed.

## What the released code actually measures

| Artifact | Source-confirmed boundary | Why it is not the controlled comparison |
|---|---|---|
| SGLang `test/manual/bench_mooncake_engram.py` | Whole Engine asynchronous request; first/final streamed output timing; separate native/Mooncake processes | Includes model, scheduling, IPC and detokenization. No native packed-stride third arm, matched host-page allocator or isolated lookup timing |
| Mooncake `scripts/bench_engram_store_27b.py` | Synchronous NumPy-ID/output table API; local storage or existing remote Store; eight 50,000-row tables, 64 bytes/row; 10 warmups/50 iterations | No CUDA graph, native fused lookup, 264-byte layout, shard masks, L2 flush or huge-page comparator |
| SGLang DeepSeek correctness test | 17×256 FP8 values plus eight scales, explicit out-of-shard IDs, native output equality and graph replay | Native comparison weights/scales are explicitly moved to GPU. Not a host-backed 48M-row performance test, and not a native packed-row implementation |
| Mooncake table tests | Small widths including264; offsets, immutable ownership, positive outer strides, graph replay and invalid-ID handling | Correctness tests without timing; no native separate-plane or dequantized packed-stride competitor |
| Mooncake C++/CUDA gather | Pins a contiguous uint8 host table; retains owner; copies raw row bytes to caller output on its stream | No FP8 dequantization, native shard-zero mask or sorting. ID−1 leaves output untouched; adapter handles initialization and dequantization separately |

The last row explains a real design boundary: the existing Mooncake kernel demonstrates physical contiguous rows, but porting this whole adapter adds work that the hypothetical native stride-only comparator avoids. Its timing cannot establish the comparator's cost.

## What the PR body says versus what remains unverified

The controlled body describes 48,000,771 rows, 256 value bytes plus8 scale bytes,24 IDs/token,1/8 expected ownership,1024 tokens, anonymous mappings in both layouts, ordinary/huge-page arms, changing random IDs, graph replay,L2 flushing, randomized order,5 discarded/40 measured trials and exact output checks. It reports native separate→packed timings 200.46→123.22µs (ordinary) and186.69→123.10µs (huge pages). These are **author-reported results only**.

Missing executable evidence is specifically:

- Native packed kernel source/diff and baseline source revision; exact value/scale strides, pointer offsets, launch and sorting parameters.
- Allocation/madvise/page-coverage code and raw observations proving equal policy within each pair; layout and backing are separate variables.
- Actual identical per-trial IDs across variants, ownership/mask realization, duplicate locality, seed and output reference construction.
- CUDA-event/graph boundaries, whether sort/packing/dequantization/mask/output initialization and flush are inside or outside timing, replay count and synchronization.
- Per-trial paired outputs/timings and commands linking this code to the body table.

The body is explicit that the whole Mooncake path costs193.71/193.15µs and is near native; its separately profiled byte-gather time excludes dequantization/masking. The reversed-order E2E follow-up is near parity and does not reproduce the earlier large TTFT advantage. None of these numbers can fill the missing native packed-comparator provenance.

## Transfer to exact c455

Target `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883` uses a persistent fused gather/dequant kernel, optional sorted IDs/output destinations, per-shard masks and private-UVA versus shared-host storage branches. The shared-host branch sets internal DP size1; the planned TP1 full-head lookup is not established to have the donor's1/8 ownership. Current lookup geometry, background grid sizing and sort threshold must remain explicit controls. A matching264-byte logical row does not establish a matching launch or memory distribution.

The portable hypothesis remains narrow: change physical value/scale adjacency while retaining exact bytes, native arithmetic, masks, destinations, output type and caller/event lifecycle. It is separate from EG01 output-staging conversion removal and EG02 caching. Round93 already covers this direction; no new identity or status change is justified. The released Mooncake ownership protocol is informative, but not a drop-in target loader or mapped-view proof.

## Next decision and stop rule

The cheapest next action is to obtain the precise controlled native comparator script/patch and paired raw receipt from its author or a subsequently published artifact. This packet does not send messages to authors. Then inspect that source against c455 before any authorized native evaluation. Required eventual controls are native separate/native packed/whole adapter, each under matched allocation and IDs, plus the unchanged native sorting and shared/private branches. End-to-end evaluation should use the existing serving workload; a lookup win alone is insufficient.

No further generic search or toy timing is warranted to repair this particular missing artifact. The scope-limited negative is actionable: the current public files inspected here do not expose the claimed comparator, so its transfer remains unverified. This does not reject row co-location or discredit the reported measurement.

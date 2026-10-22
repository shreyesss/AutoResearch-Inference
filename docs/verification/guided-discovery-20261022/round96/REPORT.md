# Round96 — optional producer-fused index-K arm for round92

## Decision

**Retain an optional implementation arm within the parked round92 component; zero new identities and no qualification change.** Source supports computing index-K at the normalized-latent producer without a separate row-compaction pass. It does not support the claim that this is a cheap extension of the existing kernel. The producer is organized around individual boundary rows, whereas the current512→128 projection is a batched backend GEMM. Fusion changes arithmetic, resources and the stream dependency graph. A particularly important counterexample is that it can delay main-cache insertion formerly overlapped with K projection.

No new paper/provider query was run: the unresolved question is the exact retained producer, not missing literature coverage. The original round92 and round5 reports are copied with their provenance; all original packets remain unchanged. Seven target source files are pinned to `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`. Planned Flash1017 configuration is reused, not live-attested. Work is source/AST/stdlib only; no native compilation, GPU, model import, serving or canonical write.

## Existing producer variants and candidate insertion point

`fused_save_compress_norm` launches `num_reqs + ceil(num_tokens/ratio)` programs with four warps. For ratio2:

1. A request program may close a group at the chunk's first token using a predecessor ring row (or PCP-gathered predecessor), then saves the chunk's ring tail. Its `_store_latent` call is before the tail writes.
2. Pair programs choose the actual boundary from token positions. They skip a request's first token, which belongs to the request program, and pool two raw rows.

Both call `_store_latent`, which computes512-value RMS normalization and writes `normed.to(tl.bfloat16)` at the original token row. Ratio1 uses one program per token and no ring. On CUDA the joined predecessor/current path is active in source selection; the ROCm separate-load variant is not part of the initial arm. PCP gathers/ring saving impose additional contracts and should remain excluded initially.

Exact ratio2 K-owning layers are2,8,14; owner20 is ratio1. This round deliberately keeps round92's three-layer scope. The candidate hook could receive the owning indexer's BF16 `wk` weight and a full-shape `[tokens,128]` BF16 `k_pre` output. At each existing valid latent emission, compute projection from **the BF16-rounded latent**, store projected BF16 at the same original row, and continue all original latent and ring writes. No packing/map is necessary for this minimal arm. The later indexer norm/RoPE/quant/cache writer remains and still enforces its independent index-slot and position predicates.

Do not early-return the producer merely because an index slot is invalid: its ring and main-cache latent work may still be required. The producer ring/main slot map is not interchangeable with the indexer cache slot map. A minimal producer arm can compute every emitted latent row and let the unchanged writer mask invalid index slots; optional extra projection gating needs the correct second map. Original main-cache latent remains fully materialized. This arm therefore does **not** save its allocation or store bytes.

The attention layer owns both compressor and indexer; their parameters are separate module objects. A future optional interface must pass the actual current owner's weight, preserve profile/no-metadata fallback and both normal/short-context/`forward_kv` producer entry paths. Bind before graph capture and preserve current reload/capture semantics; do not cache a stale derived/transposed weight. No such interface was implemented.

## Numerical contract

There are two material BF16 boundaries: normalized compressor latent before `wk`, and projected `k_pre` before its128-value norm/RoPE/quant writer. Reusing the unrounded FP32 normalization result changes the computation. A two-coordinate exact dyadic negative control embedded in512 dimensions gives reference0 versus incorrect unrounded0.5 after cancellation; this is a synthetic boundary demonstration, not observed target activations.

Even preserving both casts is insufficient to certify native parity. Current `UnquantizedLinearMethod` selects a backend implementation; the default delegates to `torch.nn.functional.linear`, explicit FlashInfer options and batch-invariant mode may select others. A new Triton reduction or tensor-core dot can change accumulation order/tactic. The exact target output contract still requires admitted-backend numerical/cache-output tests when native execution is authorized. The source observation that matrix rows are mathematically independent is not a bitwise-equivalence proof.

## Tiling, weight traffic and launch accounting

One boundary projection has65,536 MACs and128 output dot products over512 input coordinates. The BF16 weight matrix is128KiB. The current producer's512-vector layout and four-warps do not already implement that matrix operation. A direct scalar/SIMT extension must tile/reduce the output columns and increases live registers/work; replicating all weights in registers is not a demonstrated feasible design. A tensor-core version needs an appropriate M/N/K tile and a way to share work across boundary rows; existing request/ring programs do not provide that tile automatically.

A one-row producer extension logically accesses the same128KiB weight operands per boundary program. That is **not** measured HBM traffic: L2/coalescing can reuse them. Conversely the batched baseline may share weights and use efficient tensor-core tiles. At very small M, baseline minimum tiles and launch overhead may make fusion useful; at larger prefill M, losing batched reuse may make it worse. Neither outcome follows from source alone.

The arm could remove the separate `wk` call/kernel work and that consumer's latent read without a gather pass. It retains the main latent, the full-shape K-pre output, and the separate K norm/RoPE/store kernel. It is not a claim that the actual library uses exactly one launch in every configuration. CUDA graph execution also means a removed GPU kernel node is not automatically a removed Python launch overhead per step.

Round5 already examined fused state-save/compress/norm and found it present. This arm adds the downstream weight projection, so it is an alternative for the same round92 unused-row mechanism, not another newly counted fusion hypothesis.

## Stream dependency counterexample

Current `_prepare_and_attn` first joins main Q/SWA preparation with compression, then joins main-cache insertion with indexer preparation. The indexer produces K before forward-Q work. `maybe_execute_in_parallel` records the compressor event after its function's queued kernels and waits before returning. Writing latent earlier inside one enlarged kernel cannot expose it to the other stream before that kernel/event completes without a new synchronization protocol, which is out of scope.

Let Q,C,K,J,I be hypothetical work units for main-Q preparation, compression, current K GEMM, remaining indexer work and main-cache insert. Ignoring contention and launch details:

- current preparation: `max(Q,C) + max(K+J,I)`;
- producer-fused arm: `max(Q,C+Kf) + max(J,I)`.

The retained scalar model has both beneficial and harmful examples, including equal Kf=K where moving K delays a dominant main-cache insert. These are dependency counterexamples, **not timing predictions**. The helper disables multistream overlap during active breakable graph capture; sequential mode instead compares total work/resource costs. Actual replay topology and contention must be measured, not inferred from this simple expression.

## Cheapest next falsifier and future comparison

The cheapest remaining source/design gate is a concrete tile/resource plan for this existing request/pair kernel that preserves both BF16 boundaries and ring ordering, with explicit weight reuse and supported graph/backend conditions. If it merely turns a batched GEMM into repeated scalar GEMVs without a credible small-row advantage, keep it parked. No additional literature query would resolve emitted code or exposed time.

A future authorized evaluator should compare unchanged baseline, round92 packing arm and this producer-fused arm on identical real admitted shapes. Keep current K-store, main-cache output and stream policy fixed; include odd-start predecessor-ring groups, request boundaries, empty/padded rows, invalid index slots, repeats/reload and graph replay. Measure the whole two-stage preparation and client-facing workload, not just eliminated launches. Long prefill and variable DSpark verification are separate shape strata; gains cannot be added to the other arm. Standard Mooncake/agent-p75 remain the service workload. No new load harness, numeric gain or performance threshold is asserted.

## Retained evidence

`claims.json`: eleven exact source excerpts with source byte hashes/URLs. `source_controls.py/json`: AST confirms two producer hooks, one dyadic BF16-boundary negative control and three hypothetical schedule examples. No source function, tensor/backend or native kernel was executed. `source-manifest.json` pins seven copied target files. The result is a source-supported optional arm with concrete arithmetic and scheduling objections, not an implemented optimization.

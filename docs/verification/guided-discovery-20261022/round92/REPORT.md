# Round92 — boundary-only indexer K projection

## Decision

**Zero new formal hypotheses; one source-supported component parked for a practical packing/shape check. No implementation or service qualification.** The exact pin computes index-K projection rows that its cache writer discards. This is a concrete work-removal opportunity, but the affected projection is small, appears at only three ratio-2 owning layers, and requires additional packing or producer layout work. No measured benefit is available.

Target: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, TP1/DP4/EP4, DSpark5. These are source/configuration pins, not runtime attestation. All work was source/stdlib/isolated research tooling; no GPU, native backend, model, serving, canonical or cloud mutation.

## Adaptive discovery and provenance

The complete reused inventory contains 153 prior identities. AT01 score certificates/route seeds, M02 exact selection, MP17 mapping reuse, and rounds47/66 compression/selector findings were checked before expansion. One real dated OpenAlex search (2026-09-01 inclusive to 2026-10-23 exclusive) returned ten identities. All dispositions are in `paper-dispositions.json`; most useful mechanisms were known. The missing abstract for one hit remains insufficient evidence, not a paper rejection.

RouteRelay v1 was selectively reread from a previously retained, hash-pinned HTML file, with zero new fulltext HTTP. Its approximation is the chosen support, so direct reuse does not preserve target attention. Current-rescored seed reuse was already AT01. It did not originate the new boundary-K observation. No recent paper was artificially credited for that source-derived component.

Two bounded local PR scouts retained up to 40 and 30 matches. They are capped, broad local-corpus screens, not exhaustive PR coverage. FI5972 was hydrated at `yyihuang/flashinfer@69e795fcca8376c6b2022a8160f73eeb7f13663b`: two logical GitHub requests, 27 returned file patches, two selected public/backend patches read deeply. Its fused training indexer requires BF16 packed keys, FP32 score accumulation without the native intermediate rounding contract, and deterministic tie rules. This does not directly replace the target paged MXFP4/FP8 indexer. The general score-materialization component is already an examined family. SGLang45114 CP transfer narrowing is inactive for the initial PCP1 scope; SGLang41660 compressor fusion is already present. Those two were body-only screens, not full implementation audits.

## Exact source delta and consumers

In `DeepseekV4Indexer._produce_k`, the current code executes `k_pre, _ = self.wk(latent)` before `indexer_k_norm_rope_store`. The source explicitly says non-boundary latent rows contain garbage and the writer skips them. The writer first rejects negative slots, then requires `(position + 1) % COMPRESS_RATIO == 0`. The relevant coordinate is the actual token position, not flattened row parity.

The indexer K projection is unquantized, bias-free, 512→128. Exact configuration and ownership restrict ratio-2 K producers to layers **2, 8, 14**. Owner20 is ratio1; later index-source layers reuse K. This is not a 5120→1024 compressor reduction, not all eight index-source layers, and not every model layer. Both ordinary and short-context forward still produce owned K; bypassing TopK for short context does not bypass K production. `forward_kv` also reaches this producer.

The compressor's original latent independently feeds main compressed-cache insertion. Current preparation overlaps that insertion with indexer preparation. Compacting the shared latent in place would violate the other consumer's contract. A possible selective arm would retain the original tensor, create a K-only compact input plus original-row map, project it, and use original positions and slots during normalization/RoPE/cache storage. Compressor ring history and main-cache insertion remain unchanged. PCP aggregation requires a separate admission proof; the initial scope is PCP1.

## Geometry, numerics and cost limits

`boundary_geometry.py/json` is a symbolic predicate model only. Eight examples cover even/odd prefix starts, ragged requests, padding, empty/single rows and 5/6-row verification spans. Two negative controls demonstrate why global every-other-row slicing and ignoring start parity lose required writes. A conservative per-request capacity is the sum of ceil(n/2); for 64 one-token requests that capacity is still 64. Actual admitted DSpark lengths vary with adaptive verification; neither five drafts nor six rows may be assumed for every request.

One removed row avoids 65,536 mathematical MACs per eligible owner. The 131,072-byte BF16 weight matrix per owner remains, as does generally the GEMM launch. Long regular spans may have about half the eligible rows, but small-M minimum tiles can perform the same native work. Packing/gather, mapping loads, compact workspace and extra writes can outweigh savings. Dynamic GPU count extraction must not introduce host synchronization; a graph-compatible capacity policy is unresolved.

Row independence in real arithmetic does not certify bitwise native results after changing GEMM M/tactic. Valid index-K values/scales, cache slots, subsequent attention and output contract need native differential checks before deployment. Removing work helps latency only to the extent this branch is exposed at the preparation join; existing main-cache/Q overlap may hide it. No logical MAC or byte count is converted to an ITL forecast.

## Cheapest next action and evaluator

Before a runtime patch, design one fixed-capacity packing/map for recorded scheduler geometry and establish that its projected row capacity is smaller on meaningful long-prefill or verification shapes. Reject the arm if this requires a host count sync, corrupts original consumers or merely replaces one GEMM with many per-request GEMMs. Existing symbolic cases only constrain that design; they do not establish runtime eligibility.

If this gate survives, compare unchanged baseline versus one packed batched projection per owning layer, separately for long prefill and actual variable verification spans. Preserve target cache bytes/indices and output semantics; test odd starts, ragged requests, prefix reuse, padding, empty batches and both producer entry paths. Future profiling must include gather/map/copy, GEMM tactic and cache-store costs plus preparation overlap. Existing Mooncake/agent-p75 serving workloads remain the eventual evaluation; no new load harness or service threshold is invented here.

## Rubric and honest yield

| Criterion | Finding |
|---|---|
| Concrete absent operation | Full-row index-K projection precedes boundary/slot gate |
| Distinctness | Downstream projection-row removal differs from selector/prior compressor fusion |
| Frozen-model compatibility | Plausible algebra; native tactic/rounding and cache mapping unproved |
| Workload exposure | Reachable source; actual M, graph capacity and exposed time unknown |
| Cost/materiality | Three small projections; weight traffic, minimum tiles and packing remain |
| Actionability | Bounded packing/shape admission design, then native differential if authorized |
| Decision | Park component; zero formal cards, zero implementation/service wins |

One query / ten returned paper identities, zero newly fetched fulltexts / one retained selective reread, one exact-head PR hydration with two selected patch reads, eight symbolic examples / two negative controls. These denominators describe this screen, not literature recall or general research quality. The isolated export retains 21 documents, 21 revisions, 110 edges and eight exact source quotes.

Navigation failures are retained in `tool-use-ledger.json`, including an absent guessed prior state and mistakenly continued dependent reads. Recovery reused the retained HTML; no provider result was fabricated. Stop reason: further generic top-K queries would repeat known families, while the unresolved packing and native small-M execution boundary is more decision-relevant.

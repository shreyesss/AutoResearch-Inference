# SL97 refinement: restore native output owners with an explicit transport

## Decision

Keep the original SL97 hypothesis deferred. This resolves a source-level output mapping question, not numerical correctness, compiled efficiency or service ROI. No new hypothesis, paper query, native patch, build or GPU operation.

## Pinned grounding

Target DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, `deep_gemm/include/deep_gemm/epilogue/sm100_mega_mhc.cuh`, run_mix_task: lanes8–23 store the sixteen row-major Comb coefficients. Pre lanes0–3, Post lanes4–7 and the returned original mix_value have separate consumers. Final warp synchronization remains.

FlashInfer donor head `8384ebb9db9e1a8ec440d5f10893723340a17e41`, retained `head-two-lane.cu` lines887–942: all lanes gather eight coefficients; even lanes hold matrix rows0/1, odd lanes rows2/3. The normalization preserves that ownership. Lines951 onward use two store owners. Exact source copies match frozen round97; its arithmetic/epsilon/build differences remain excluded from transfer.

## Proposed transport, after normalization

For each lane define `k=(lane>>1)&7`. Select its local `comb[k]` using an explicit eight-way selection over scalar registers. For a Comb destination define `idx=lane-8`, and use safe idx0 on every other lane. All32 lanes then execute one source-level indexed shuffle from `src=2*(idx&7)+(idx>>3)` of the selected send value. Only original Comb owners consume the returned value in the unchanged scalar store. Preserve original mix_value for Pre/Post and function return.

The sender lane has parity `idx>>3` and selected register `idx&7`, so its value is matrix cell idx. Sources0–15 cover all16 cells exactly once; upper lanes hold duplicate layout values and still participate. This makes the transport explicit without eight separate exit broadcasts. It is not a free inverse map.

```text
all lanes: send = select8(comb0,...,comb7, (lane>>1)&7)
all lanes: idx = is_comb_lane ? lane-8 : 0
all lanes: normalized = shuffle(full_mask, send, 2*(idx&7)+(idx>>3))
original lanes8..23: store normalized at original Comb destination
original Pre/Post stores and return mix_value unchanged
```

## CPU discriminator actually run

transport_control.py uses unique integer cell tags, not floats. All16 destination mappings match. A tempting incorrect alternative—each receiver selecting its desired register then broadcasting from lane0/1—fails14/16 cells because a shuffle reads the sender-selected value. This is a mapping proof only. Full-warp participation is a precondition; no divergent partial-warp shuffle is permitted.

## Physical costs and remaining gates

- One source-level exit shuffle plus eight-way register selection and integer mapping. An explicit seven-select chain is possible; compiler lowering, predicate/register pressure and spills are unknown. Dynamic local-array indexing must not be assumed register-only.
- Existing donor entry uses eight gathers. Native entry uses two row-max shuffles. Native and donor each have four source-level shuffles per normalization stage; no total stage-count reduction is claimed.
- The donor replicates eight coefficients per lane. Keeping original mix_value and the transport selection may extend liveness. Shifted Mix has a40-register budget versus Normal80 in the retained target. No compiled occupancy/SASS evidence exists.
- Use target fmaxf/__expf/fast reciprocal, epsilon1e-6, exact iteration count20 and reduction grouping. Mapping equality cannot establish FP parity, NaN/signed-zero semantics or codegen preservation.
- Confirm actual native route exposure; the small-token FULLgraph mHC stream branch uses TileLang coefficients. Do not disable existing overlap to manufacture a benefit.
- Later, only when execution is authorized: native coefficient/output parity including Pre/Post/return, both Normal/Shifted paths, compiled register/spill inspection, exposed component timing, then unchanged Mooncake and agent-p75 service comparisons with tail guards. Current ROI stays null.

## Yield

One unresolved implementation contract narrowed; one incorrect transport ruled out; zero new candidates, zero implementation qualifications, zero measured wins. This is a refinement of SL97, not an additional discovery count.

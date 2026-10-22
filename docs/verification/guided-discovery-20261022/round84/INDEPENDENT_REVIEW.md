# Independent round84 review

**No blocker to the zero-new source screen, with the additive locator correction required for retention.** This is a bounded source and receipt review, not native correctness, scheduling, cache-latency or service qualification. Author original42-file packet remains unchanged.

## The missing-operation premise is not established on the inspected target

The donor change is real. The exact FlashInfer6951 base source reads `k_scale[...]` after identifying a selected64-token block in the softmax path (base:537). The exact head consumes `ring_f` after a full-barrier wait (head:505–522), while producer warps14/15 compute indices/valid size and load the global scales (head:2391,2492 onward). Its ring full/empty handoff adds synchronization and1280bytes of shared storage, rather than making these costs disappear. I recomputed the retained complete main-kernel diff from the pinned base/head bytes; it matches. The head is yyihuang/flashinfer e566ec77…, base flashinfer-ai/flashinfer38214409…; both source receipts match the PR object and retained file bodies. This does not claim all six PR files or every donor optimization was independently reviewed.

The inspected target already has an indices producer (warp10) including a one-block-ahead register load (target core:1255–1295). Warp11 waits for index/slot readiness and issues raw gathers. **Its separate CTA0 scale-copy path is conditional on IS_2CTA** (1385–1400); the other CTA's scale bytes ride with its raw gather. Dequantization waits for raw-stage completion (1486 onward), obtains the staged scale locations (129–142), and reconstructs values before attention math. Softmax's local score multiplier (906–916) is not the donor's per16-token global K-scale lookup chain.

This source evidence defeats the narrow proposed port premise that this target has that donor softmax-dependent scale load waiting to be moved into two empty producer warps. Assigned target warp roles are not proof that every lane is always busy, that no producer stall remains, or that no alternative schedule can improve it. Reopening requires a specific remaining target dependency and a legal resource/lifetime mapping. Neither existing prefetch code nor a donor speedup substitutes for an actual target trace. Do not broaden this conclusion to every backend or prefill path.

The cache resolver argument is appropriately conditional: generic auto/fp8 selects the backend-preferred packed representation; that is not a universal all-FP8 physical record claim. No installed backend/configuration was attested here. Distinct typed occurrences, masks, scale formats and output transformation remain required adaptation contracts.

## Coverage and date scopes

I independently checked both retained scout receipts, all returned IDs/date filters, disposition appearances and the two prior pages:

- Created-date [2026-10-01,2026-10-23):14+2+40+40=96 returned appearances; the FlashInfer/vLLM results are capped against916/408 local matches.
- Updated-date [2026-10-21,2026-10-23):1+0+20+14=35 appearances; FlashInfer is capped against168 local matches.
- Union:131 appearances,126 unique PR identities, all represented in dispositions and corrected export. The149 prior IDs are unique across the two pages and share the recorded inventory hash.

These are retained-current local counts and two date scopes, not independent evidence sources, a globally consistent upstream snapshot or126 implementation reviews. In particular, **the FlashMLA scout actually queried deepseek-ai/FlashMLA**, whose local scope has only3 PR documents. Its2/2 October-created result is not coverage of the target vllm-project/FlashMLA fork. The real scout receipts must not be relabeled during locator correction. Title-only nonselection is correctly kept distinct from scientific rejection.

## Provenance repair

The original target bytes were valid but the constructed source identity used deepseek-ai/FlashMLA. The additive correction maps to the already retained vllm-project/FlashMLA5dce… source/revisions, with byte-identical body. I verified correction hashes, correct identity/body, removal of the erroneous code identity from corrected-source-export.json, and preservation of all126 PR IDs. Future retention must use this corrected export/mapping and retain the original packet as disclosed history. Do not import both identities as independent evidence or infer a commit exists in the wrong repository from identical bytes.

## Scope and disposition

Body-only alternative leads remain scoped screens. No target defect is established for DG480/478; no body-only lead is treated as a complete diff review. Donor bit-identity and1.01–1.08x timing claims remain reported donor results, not reproduced target evidence. The source comparison was the useful falsifier and no extra scalar workload or paper search is needed to dress up the zero-new outcome.

Verified42 author hashes, additive correction hashes,7 retained source anchors, exact donor diff, date/count/identity coverage and selected source branches. No network, backend/module import, compiler, GPU or canonical mutation occurred.

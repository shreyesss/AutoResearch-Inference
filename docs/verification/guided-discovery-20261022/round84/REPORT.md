# Round84 — recent PR opportunity audit

## Decision

**Zero new hypotheses.** FlashInfer #6951 supplies a real selective optimization: move dependent metadata/scale loads out of softmax onto ahead-of-consumption producer warps. Exact source comparison found that the selected FlashMLA target already separates those consumers through its indices/scale/dequant pipeline. The donor removes work from a different place in a different attention representation. Preserve the component and its implementation evidence; do not create another generic prefetch card.

No GPU, native module, compiler, model, serving process, canonical writer or cloud action ran. Target source remains callgideon/vllm c4557869393db4d75c483d92edd02a5125500883 with FlashMLA5dceadbd9eabc9acfc547ef18ec8f7b14b980682, planned Flash1017/B200/TP1/DP4/EP4. These source conditions are not live attestation.

## Coverage and adaptive selection

All149 compact prior cards were recalled in two pages (inventory hash c543328973294852aa37233bfbec2144a5a970e9e8d0c7f90d6f05b5d6eea809), supplemented by already-read reports. The local created-date scout used [2026-10-01,2026-10-23), newest first: DeepGEMM14/14 matching records, FlashMLA2/2, FlashInfer40/916, vLLM40/408. This is96 title inspections, not96 source reviews. The independent updated-date scout used [2026-10-21,2026-10-23), newest first, cap20 per repository. Its35 returned records include older-created items: notably already-reviewed BF16 tuner6360. The two scouts produce131 appearances and126 unique PR identities. Full explanatory receipts record counts, dates and local coverage. Neither updated time nor a high PR number proves a new mechanism; neither local completeness nor upstream exhaustiveness is claimed.

`dispositions.json` retains every returned identity and depth. Most are title-only nonselections, not scientific rejections. Bodies for6951,6937,6926,5720,6933,5666 and selected prior/correctness leads were inspected at the explicitly recorded depth. Code was hydrated only for6951. All126 PR documents and their available immutable revisions are imported into the isolated corpus and exported; original dates and incident provenance remain. A normal `pr-search` replay confirms selected local discovery without provider calls.

The next action changed after reading6951: the body mentioned dependent global K-scale loads on the softmax path, so the audit checked the target consumer before proposing a port. The target showed an existing producer pipeline. We then fetched the exact donor head/base main kernel because GitHub's six-file response omitted that large patch. No paper query was added: another generic prefetch paper could not resolve this specific source comparison.

## Exact donor and target mechanism

Donor [FlashInfer6951](https://github.com/flashinfer-ai/flashinfer/pull/6951) head e566ec7744241bc3891c7ab2d3b57d168fcc6d82; base3821440929ee342fe9f939dbf5186c3e667a851c. Its Cake Sage block-sparse kernel uses head dimension128, E4M3 Q/K/V, per-token Q scales, per16-token K scales, per-channel V scales and selected64-token blocks. Two previously empty producer warps become metadata/scale stages. The exact main kernel diff changes26 barriers to46 and shared allocation119040 to120320 bytes (+1280). Warps14–15 fetch block index, clamp valid size and load K scales; a ring has full/empty barriers, while softmax consumes `ring_f` and metadata shared memory. This is a real implementation delta; unchanged quantizer patches are largely temporary-expression cleanup and are not credited as additional optimization.

The retained target kernel is a typed sparse mixed-cache reader. Warp10 generates physical indices/validity/TMA coordinates. Warp11 launches raw gathers and scale copies into protected KV stages before consumption. CTA0 stages separately addressed scales with `copy_kv_scales_async`, bound to raw-stage completion; dequantization reads these staged bytes and reconstructs BF16 rows before QK/SV. Softmax uses its local score multiplier and validity data, not the donor's per16-token global K-scale load chain. Target decode also already permits the next QK and SV to issue according to separate readiness barriers. Every target role has assigned work; borrowing the donor's two idle warps is not a justified mapping.

This does not prove target pipeline optimality or zero latency headroom. It falsifies the proposed missing-operation premise "softmax must wait for uncached dependent K-scale global loads that could simply be moved to idle warps." A residual optimization would need a specific remaining dependency or stall and a lifetime-safe role mapping. No such delta was demonstrated in this round.

### Cache-format boundary

The exact V4.1 resolver maps generic auto/fp8 to the selected backend's preferred packed format. Mega prefers nvfp4_ds_mla; its compressed and SWA records can therefore differ. Explicit fp8_ds_mla and fallback backend selection differ. Do not interpret a generic FP8 CLI label as all target caches FP8, and do not map Sage scale geometry onto the target mixed reader. Round83's independent resolver audit provides the detailed528B/288B interpretation; this round retains the actual resolver/property source without executing it. No baseline identity is rewritten.

## Other selected opening leads

- **6937:** next-QK-before-PV component already has target scheduling support; changed softmax anchors overlap the prior softmax numerical family. Dense grouped-Q planner gains do not establish compatibility with typed sparse selected occurrences. Body-only screen, no whole-PR rejection.
- **6926:** body says changed routes are dense FP4 or64-head prefix-zero classes; paged routes unchanged. No target decode benefit established; no claim these components are universally unusable.
- **5720:** H512 and NVFP4 labels are insufficient for porting Gemma mixed FMHA. Target typed sparse slots and fused query/output transformations remain different. Native BF16 output is not automatically useful where current target emits quantized output. QMUL4 remains an unqualified component, not a new performance hypothesis.
- **6933:** its352-byte D576/H16 sparse MLA packaging is not the target's D512 mixed records. Near-neutral packaging benchmark does not prove a missing algorithm.
- **5666:** CuTe DSL finalize API belongs to a different MegaMoE implementation than target DeepGEMM a7; no direct-finalize port asserted.
- **62745/62748/62749/6360/60843:** existing round70/HM65/graph-metadata/round54/round44 families; new timestamps do not produce new cards.
- **DG480/478:** preserve potentially important TMEM/barrier correctness bodies. They were not source-validated against the target here and are not claimed as target defects or latency opportunities.

## Evaluation and stop condition

The donor reports bit-identical O/LSE and1.01–1.08x B200 kernel speedup on its own4096-token,MHA,H128,cold-L2 cases; this was not independently reproduced. It neither isolates an exposed Flash1017 dependency nor predicts client ITL. The target's format, fused operations, sparse support, head grouping, roles and contention differ. Shared-memory/barrier increases can also affect occupancy.

Fastest useful falsifier was the completed source consumer/producer comparison, not another symbolic case counter. Reopen only with an exact target source change or compatible trace identifying a remaining dependent metadata load on the critical path, plus a resource/lifetime mapping preserving actual scale formats and selected-slot multiplicity. Existing matched target correctness and serving workloads can then evaluate a concrete adaptation. No numerical speed forecast, accepted diagnostic plan, implementation or service qualification was generated.

## Tool usefulness and limitations

Two local date-qualified scouts (eight Store searches), one selected normal CLI lexical search, three selected import invocations, one investigate command with two exact code files, and four logical GitHub detail/files/comments/reviews reads were used. Provider paper searches/fulltexts:0. New PRs fully hydrated:1. Unique returned PR identities126; source-screened optimization1; new hypotheses0. The receipts do not imply126 complete reviews. Successful raw GitHub request receipts and source retrieval cache metadata are retained; logical tool calls are not claimed to count transient HTTP retries.

One attempted unsupported `export-corpus --help` and an incorrect initial V4 rather than V4.1 path lookup were corrected locally; neither produced state evidence or a model claim. Source export uses existing Store rows/revisions. The prior skill-path typo was corrected to inference-pr-research. `investigate` correctly exposed the missing patch's complete pinned files. No tool implementation change was warranted.

# Round 106 — TMA communication components against native MegaMoE

## Decision

**Zero new formal hypotheses; five concrete component screens.** The recent T-CCL paper supplies a useful decomposition of data movement, reduction, scheduling and resource allocation. The pinned target already implements several of these mechanisms. Its bulk-reduction component remains a conditional research option, with unresolved arithmetic and buffer contracts; this round does not qualify an implementation or predict an ITL gain. RailWave's scale-out rail schedule is outside the planned single-node configuration.

No GPU, model, native-library import, build, serving, canonical-state or cloud operation was performed. The source plan is B200, TP1 / DP4 / EP4, frozen Flash-1017 at `1bae0e1088993b9b82de08f59de5be5a34e42170`, callgideon/vLLM `c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`. These pins establish source applicability, not live dispatch or measured exposure.

## Discovery and adaptation

Read all 153 compact prior cards in two pages and retained matching prior/report evidence, including rounds 52, 100 and 102. This distinguishes A52 readiness, D52 activation deduplication, R3 dispatch staging, N03 SM allocation, M01 tile selection, RD01 localization, WP38 weight packets and EC79 lossy output transport from a new communication primitive.

One actual OpenAlex query, `mixture experts inference memory interconnect communication scheduling`, used the tool's September 1–October 22, 2026 bounds and returned 12 identities. The fulltext decision selected **T-CCL (2610.07098)** and **RailWave (2610.03415)**. Both returned version-1 text. Retrieval used unversioned HTML locators, so the retained bytes/content revisions establish what was read; this was not a version-pinned URL request. Other hits are explicitly metadata screens in `paper-dispositions.json`, not claims of full-paper rejection.

T-CCL exposed three separable questions: is native dispatch missing asynchronous movement, can multiple pulls be pipelined at the target width, and can reduction move from registers to a TMA engine? The first two closed from source, so there was no second synonym query. The third justified PR triangulation. Bounded canonical read-only FTS inspected 24 returned rows across three searches, selected three existing PR records, and ran the normal search command on that explicit subset. This replay does not claim new whole-corpus coverage.

The actual FlashInfer #2529 head is `nv-yunzheq/flashinfer@4ce7581ac37e2a873c39dbaa7824d81f7c0c2dae`. Normal code investigation fetched its `utils.py` and `blockscaled_contiguous_grouped_gemm_finalize_fusion.py`. This older donor supplies an implementation component for the recent paper question; the donor PR body alone was not used as absence evidence. T-CCL's own artifact implementation and RailWave's implementation were not fetched. Their algorithm/evaluation sections were read; no claim of inspecting their kernels is made.

## Source findings and dispositions

| Component | Exact target test | Disposition |
|---|---|---|
| C106-1: replace communication with TMA / swap NCCL backend | Native MegaMoE already issues TMA loads/stores in its custom routed dispatch/combine. TP1 does not expose the paper's per-layer dense TP collective path. | Reject this direct target intervention; do not claim every NCCL use is absent. |
| C106-2: multi-stage pulls within one activation row | Scaled FP8 H=5120 uses the 8192-byte pull limit, so native dispatch has one 5120-byte pull. Its final pull already overlaps metadata/scale retrieval before the store. | Reject the within-row multi-chunk premise at this geometry. Cross-token staging is a separate R3-related question, not demonstrated here. |
| C106-3: offload combine addition to bulk reduction | Native combine uses BF16 partials, FP32 ordered register sums, two load stages, one store stage and a final BF16 cast. Donor has optional BF16/FP32 bulk-add helpers. | Retain a conditional component; not implementation-qualified and not a new formal card. |
| C106-4: fan-out or per-peer CTA scheduling | T-CCL's sender fan-out differs from target receiver pulls. Native per-token peer readiness, R3 staging and A52/D52 cover related ownership/readiness changes. | No distinct justified intervention after this read. Keep the component, do not rename prior ideas. |
| C106-5: RailWave rail redistribution and permutation waves | Paper schedules inter-node NIC rails over multi-node DeepEP traffic. Planned single-node EP4 has no such rail demand matrix. | Reject the direct topology transfer. This is not a claim about future scale-out deployments. |

### Dispatch and combine are different paths

In `sources/target-heuristic.hpp:223`, the pull size begins with hidden size times input element bytes and halves only above the mode-dependent limit. Scaled FP8 selects 8192 bytes. Substituting H5120 yields one pull. In `sources/target-kernel.cuh:540–606`, the pipeline handles earlier chunks if present and overlaps scale/route-weight retrieval with the final chunk; adding a deeper within-row pipeline cannot remove repeated waits that are absent for this geometry. New stages also require storage/barrier accounting. No inference from logical copies to physical traffic is made.

**Combine has two chunks, not one.** At `target-kernel.cuh:1391`, H5120 exceeds the independent 4096-element register condition, forcing two 2560-element chunks. Within each chunk, two load slots alternate over selected expert contributions; a third slot holds the output. At lines 1460 onward, the shared contribution comes first, followed by top-k slots. The source casts BF16 partials into FP32 accumulation and finally rounds to BF16. It also contains `fence_view_async_shared`; the older DeepGEMM #389 fence concern is not evidence of a missing fence here.

### Bulk reduction: useful component, incomplete target adapter

T-CCL moves both copy and add work to TMA. FlashInfer #2529 independently exposes `cp.reduce.async.bulk...add.noftz.bf16` and `...add.f32`, so this is a concrete component rather than only a paper slogan. The donor's optional `use_blkred` finalizer performs weighted output conversion, shared-memory staging, proxy fencing and destination-row reduction. Its full backend/type assumptions and output ownership differ from the target. Its timing table is not target evidence; small-token point estimates are mostly neutral and include a regression, without variance establishing a general regression or win.

A direct BF16-add replacement changes the baseline's single final rounding into intermediate rounding. FP32 bulk additions avoid that specific issue but still need a compatible FP32 source representation, initialized destination, completion and reuse protocol, eventual BF16 conversion and a decision about addition order. Unordered atomics do not preserve the existing shared-first/top-k fold. Serializing additions may preserve that order, with synchronization and global accumulator traffic that must be counted. None of these facts establishes that a quality-admitted numerical change is impossible; they prevent calling a naive substitution exact or free.

The first useful consumer is the combined hidden activation after all selected contributions. A target adapter must preserve masks, slot ownership, shared contribution multiplicity, peer visibility, destination initialization, output readiness and captured-buffer lifetime. Moving initialization or final cast to another launch can erase a small combine saving. The current FP32 register buffer also provides local accumulation; removing it can introduce a different memory bottleneck. Actual compiled resources and exposure are unknown.

## Executed CPU diagnostic and its limits

Command, run from the repository: `PYTHONPATH=ideation .venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/round106-recent-moe-memory/source_discriminator.py`. Output is retained in `diagnostic-command-output.json`; repeating the same deterministic control does not add independent cases.

- Source substitution: FP8 H5120, limit8192 -> pull5120 -> dispatch chunks1.
- Legal finite BF16 inputs `(256, 1, -256)` produce `1` with an FP32 fold then BF16 cast, versus `0` with BF16 rounding after each addition.
- Legal finite BF16 inputs `(2^24, 1, -2^24)` produce `0` in the shown FP32 order and `1` under the shown alternative order.

These are two arithmetic contract witnesses and one source calculation, not three workloads. They do not execute the hardware instruction, establish native rounding/atomic behavior, prove target occurrences, measure quality loss, validate nonfinite handling or estimate latency. The conclusion is only that intermediate format and order cannot be discarded from the adapter contract.

## Exposure, break-even and evaluator relevance

The planned native path is directly relevant to decode, but there is no compatible retained trace demonstrating that combine addition rather than remote readiness, GEMMs, payload movement or the rest of the layer dominates the ITL critical path. TP1 makes generic dense-collective replacement a poor target even when a paper reports impressive TP gains. T-CCL itself reports small-message regressions and TP4 overlap cases slower than sequential execution. RailWave's communication timing excludes grouping, prepacking and output reconstruction, and its experiments use multiple nodes. None of these results is a service forecast here.

For C106-3, a necessary break-even condition is that saved exposed register/load/add or resource pressure exceeds extra conversion, initialization, ordering, finalization and buffer costs. Every term is presently unknown; no numerical ROI is assigned. There is no source-grounded reason to prioritize this over narrower retained candidates.

The cheapest remaining design discriminator, if this component is revisited, is to specify a legal FP32 reduction source/destination and exact initialization/completion schedule under current slot ownership, then account for unavoidable new passes. A source design that requires full-size extra passes without removing an exposed dependency is a reason to stop before implementation. This is more informative than another scalar sweep. Hardware instruction semantics and compiled resource checks would follow only under separate authorization.

Existing Mooncake and agent-p75 mixed request benchmarks can evaluate the eventual long-output ITL/goodput and stability change without creating a new serving workload. They do not establish numerical/task quality for a changed sum order or format. Such an arm would additionally require a predeclared target-derived numerical/output/task-quality admission gate, compared against the current target, before promotion. No tolerance is borrowed from the donor and no GPU evaluation is authorized by this report. A correct implementation with unchanged or worse ITL is the null result; no forced promotion.

## Tool usefulness, failures and retention

The first expansion used invalid observation status `relevant`; the existing safe error listed allowed values and the corrected plan used `useful`. This is observed guidance usefulness, not a controlled skill-quality improvement. A local GitHub helper initially treated `Sources.request`'s `(bytes, content_type)` result as parsed JSON; the retry reused the cached response. This was a helper failure, not a provider failure. An exact-quote assertion then caught a source newline mismatch; the corrected quote uses an exact contiguous substring. All three failures are retained.

The successful normal tools supplied dated discovery, two primary fulltexts, selected-source PR import/search, two pinned code bodies, complete prior-card recall and the command-history receipt. Manual pinned local source reuse was explicitly committed, closed, and reopened read-only before export. `source-readback.json` records 23 documents, 26 revisions and 210 provenance/derived edges; nine exact claims are checked against revision bodies. The copied hypothesis inventory is only a prior lookup fixture, not new hypotheses.

Yield: one paper query; 12 returned paper identities; two fulltexts read; two pinned donor code files read; five concrete component screens; one conditional component retained; zero formal new identities; zero implementation-qualified proposals; zero measured improvements. These denominators deliberately preserve rejected and duplicate branches.

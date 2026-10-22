# Round116 — conditional-memory lookup: selective transfer and a round93 refinement

**Result: zero new hypotheses.** One recent paper was read selectively, three inference components were screened, and one new donor comparison strengthens the existing round93 host-row layout question. No implementation, quality, or service qualification changed. No GPU/native/model import, build, runtime patch, canonical write, or cloud operation occurred.

## Search and prior coverage

Read the retained153-card compact inventory and bounded campaign REPORT files for Engram, embeddings, NUMA and page placement. Relevant prior families are EG02 row caching/dedup, EG01 packed output staging, A01 WKV lookahead, projected-tuple reuse, ER73 remainder arithmetic, EM75 token/request maps, round55 early lookup and round93 backing-row co-location. This inventory is a historical snapshot plus report scan, not a claim of current canonical point-in-time completeness. Frozen predecessors are unchanged.

An August1–October23(exclusive),2026 arXiv query returned10 abstracts, mostly architectural/application memory. A second OpenAlex query changed coverage to embedding inference/offload/placement and returned15 references. Both plan and execution have structured dates and the second plan cites the first query identity. All25 reference dispositions are retained. Results are bounded relevance rankings, not exhaustive literature coverage.

Selected **Memory Attention,2609.28399** from OpenAlex. Normal `investigate` fetched an unversioned HTML URL whose body identifies **v2,14October2026**. The observed body/revision hashes are retained; the request itself was not version-pinned. Read its model definition, inference folding, offload, recall extension, inference setup/results and scope qualifications. Other hits remain abstract-only; downloading a fulltext is not represented as reading every section.

A local PR scout searched literal Engram with norm/NUMA, plus Memory Attention titles:69 local matches, newest30 by updated_at inspected as candidates, three bodies selected for relevant sections. This is local retained coverage, not69 complete PR reviews or publication-date filtering. Selected PRs were imported with original revisions and replayed through normal `pr-search`. The new mechanism question prompted exact head/diff retrieval only for SGLang44521.

## Paper component1: fold a row-local normalization

[Memory Attention §3.3](https://arxiv.org/html/2609.28399v2) normalizes each retrieved token-memory vector independently. Once parameters are fixed, its table can store the normalized vector. This is a legitimate inference-only component even though the surrounding architecture is trained. Rejecting it merely because the paper contains training would miss the transferable question.

Native Flash1017 Engram has a different dependency. At `common/engram.py:1688–1691`,24 retrieved256-wide rows are concatenated and projected by WKV. The fused post-WKV kernel then computes a key RMS over each5120-wide projected key, plus a hidden-state RMS and gate (`1247–1254`). There is no independent per-native-table-row RMS operation to fold away.

In real arithmetic, if projected key contributions are a and b, squared norm of a+b includes cross term2a·b. Independent normalization of the source rows does not recover this norm. The hidden RMS also depends on the current contextual state. Precomputing a whole tuple's projected/normalized key is a different reuse strategy already screened in `engram-projected-cache-preflight`; its key, capacity, numeric and recurrence gates remain. This source argument closes the direct row-fold port, not every possible Engram transform. No synthetic numerical test was needed.

## Paper component2: prefetch token-indexed memory

§3.4 identifies rows before hidden states are ready and overlaps lookup/transfer with model computation. Native c455 already hashes token history before consuming Engram, stages table rows on its prefetch stream, records per-layer events and waits at the consumer (`Engram` staging/prefetch code1600–1650). Moving WKV itself earlier is A01, not a new proposal from this citation.

The donor's prototype uses24-layer H800/BF16 models; decode offload groups four layers with prefetch depth4. Its timing excludes sampling and GPU-to-CPU token-ID transfer and assumes IDs already available on both devices. Native hashes/IDs and UVA lookup are device-side; a CPU gather pipeline cannot inherit those free-input assumptions. The reported forward latency combines architecture, memory and scheduling changes and does not isolate overlap. Two native Engram layers and their existing serialized lookup stream also differ from the donor's24-layer schedule.

**Disposition:** existing mechanism/different input contract. Preserve the paper's explicit measurement boundary as useful contrary evidence; no additional prefetch card or forecast.

## Paper component3: reconstruct historical values

§3.5 MA-Recall relies on the architectural identity V=K+normalized token memory and explicitly was not included in its inference measurements. Native shared-latent attention does not contain that identity or a separate analogous persistent V history to remove; retained c455 Mega callsites pass the compressed/SWA latent caches. A frozen Engram block writes a gated residual before subsequent computations rather than providing the donor's additive attention-value representation. Replacing the architecture would change the model. This excludes the direct reconstruction component; it does not dismiss all inference-only work in the paper.

## Source audit: obvious host placement is not a missing default capability

Native `DPSharedEngramStorage` allocates one registered shared mmap per local group and has one loading writer. Private table storage supports prefaulted transparent huge pages with pinned fallback. These features are already present, not proposed again.

Worker NUMA CPU/memory binding also exists: `_get_numactl_worker_args` emits `--membind` and CPU binding, and multiprocess launch applies it when configured. `numa_bind` defaultsFalse; failed memory-policy probes can fall back to CPU-only binding. This is source availability, not proof of active policy, actual table page placement or benefit. A shared physical table cannot become independently local to every GPU merely because workers are bound. No host topology/page-policy probe was performed. Missing topology/exposure evidence does not justify a new NUMA-placement card here.

## Decision-changing PR evidence: refine round93 rather than create another idea

[SGLang44521](https://github.com/sgl-project/sglang/pull/44521), exact head **70915471caa457d1482083bd40a98b1ca9a85953**, integrates an external EngramStore. Read its12-file change list and complete added `embedding.py`/`storage.py`; raw-file contents agree with the corresponding complete additions. Companion Mooncake4701 implementation was **not** inspected or built.

`storage.py::lookup_deepseek` concatenates native FP8 bytes and scale bytes along each CPU row before populating an immutable store snapshot. Lookup then creates contiguous value/scale tensors, dequantizes and masks on GPU. It preserves model-side hashing and keeps CPU checkpoint parameters as well as the snapshot. Thus the adapter establishes a real packed-row interface, but adds ownership/peak-memory and downstream work; it is not the faster fused native gather comparator itself.

The PR body separately reports a controlled1024-token lookup with264-byte records,24 IDs/token and1/8 expected shard ownership, comparing the same native arithmetic on separate versus packed strides under matched page backing. It reports packed-stride lookup faster in that test. This is relevant **author-reported evidence for the existing round93 co-location mechanism**, whose earlier address control found no automatic sector-count saving. It does not establish the cause as TLB locality, a small-decode gain, or c455/B200 applicability. The actual microbenchmark implementation/receipts were not present in the two inspected adapters; their absence from this bounded read is not a claim that no harness exists.

Crucially, the PR's earlier end-to-end DeepSeek advantage did not repeat in a reversed-order follow-up: the body reports near-parity TTFT/TPOT/request latency and explicitly declines a stable causal speedup. Page backing varied across launches. The whole adapter's complete lookup also incurs operations excluded by comparing only its byte-gather kernel. Small controlled exact-output tests and longer performance runs have different conditions and output-match rates; do not conflate them.

The other two selected bodies do not establish new mechanisms: vLLM62692 addresses InstantTensor startup loading placement, not decode lookup; vLLM61868's Engram WKV lookahead is A01 and its combined GB300 results do not isolate the target TP1/DP4 arm. No fresh whole-PR performance claim is adopted.

## Next useful check and stopping condition

For round93, request the donor's actual controlled packed-stride kernel/harness, pinned source, allocation/page backing and shape receipts, then compare its read/store geometry with c455's native shared-storage path. That would strengthen implementation evidence without running a model. Do not transplant EngramStore wholesale or add its memory duplication by default. A future authorized native check should compare complete native lookup paths on the same allocation policy, masks, IDs, sort regime and staging schedule, then use existing serving workloads. Earlier trace-applicability work found no compatible exact-target lookup exposure trace; this round did not repeat that search or infer recurrence from shared prompts.

For the Memory Attention components, source dependencies resolve the immediate transfer question; more generic queries would not change admission. There is no source-backed newly removed operation with an exposed-time estimate. Unknown runtime cost alone did not cause rejection: the direct normalization/reconstruction substitutions lack the required native semantics, while generic prefetch already exists.

## Yield and provenance

Two online provider queries;25 references/abstract dispositions; one newly selected fulltext; three paper components screened; three selected PR-body sections; one PR exact-head/files response; two donor full files; five pinned target files. Zero new formal hypotheses, implementations, quality tests or measured improvements. One prior component gained narrower external implementation/comparison evidence. Read depth and review limits are explicit rather than counting all downloaded PR text as read.

Initial `init --defer-snapshot` was rejected before mutation; retry without that flag succeeded. A manual read-only fulltext database extraction failed; normal `show` recovered the already retained body without another network fetch. Both failures remain. Research commands use isolated state; subsequent mutations defer recovery snapshot/publication. The source export includes original records, immutable revisions and provenance edges. Frozen artifacts omit mutable databases/caches; no canonical retention or S3 durability is claimed.

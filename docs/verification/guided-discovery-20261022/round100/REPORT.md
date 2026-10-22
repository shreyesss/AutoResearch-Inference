# Round100: expert prefetch and producer scheduling

## Outcome

**Zero new formal hypotheses. Two concrete proposed additions were stopped because their mechanisms already exist in the pinned target.** This is a useful implementation closure, not evidence that current communication or prefetch is optimal.

1. Separate local expert-weight prefetch from remote-activation readiness: already implemented through independent TMA producer warps.
2. Move task/index preparation off operand/compute warps into a bounded producer queue: already implemented through a dedicated scheduler and two-stage task metadata pipeline.

The task was source/CPU-only. No GPU/device/native/model imports, compilation, serving change, canonical mutation or cloud operation occurred. Planned model/source configuration remains Flash1017/c455, DeepGEMM a7a927, TP1 DP4 EP4. Static source reachability is not an attestation of a running backend.

## Retrieval was driven by the code question

Read CURRENT/checkpoint35 navigation, candidate map30, all153 compact prior projections across two pages with identical inventory hash, the21 lexical communication/prefetch matches, and selected round52/38 reports. These priors cover activation dedup, ready-source scheduling, replicas, packet layout, physical weight placement, resource partitioning, DeepEP prefetch, EC79 and Engram. Compact recall is typed-memory coverage; bounded standalone report search supplemented it and is not an exhaustive semantic novelty test.

The first dated OpenAlex query, August1–October22, returned ten papers about expert prefetch and activation pipelines. Most addressed host/flash offloading, trained predictors, replicas or non-P2P hardware. Source inspection then found that simple local-weight/remote-activation decoupling already exists. The second explicit dated arXiv query switched terminology to warp specialization / producer-consumer pipelines rather than repeating model names. It returned two papers. There was no automatic query relaxation.

Selected **FlashMask-3: Efficient and Expressive Mask-Aware Distributed Attention**, `2610.17901v1`, October13, for its separately reusable forward producer/index-generation component. A bounded canonical source lookup found no retained source; `investigate` retrieved the versioned fulltext with one cache miss. Read selected §3.1, §3.4/C.4 and limitations, not every paragraph or the released repository. Training results were not rejected merely because the paper trains: the forward scheduling component was explicitly tested against inference source.

Twelve query references correspond to twelve canonical paper identities. One new fulltext was read selectively; CoMoE and MegaFlux are recognized prior reads, not new corroboration. All hit dispositions and dates are preserved. No third query was useful after native source resolved both component questions.

## Component1: operand producers are already decoupled

At a7a927 `sm100_fp8_fp4_mega_moe.cuh:693–823`, activation+SFA and weight+SFB have different producer warps. The activation warp waits for the full Linear1 token block or SharedLinear2 completion; its routed Linear2 path additionally waits on K-block readiness. The weight warp has no corresponding token-arrival wait. Once it receives a task and a reusable stage, it can issue weight and scale TMA independently of the activation producer.

Both paths still use the shared stage's empty/full barrier lifecycle; MMA must wait for both required operands. This bounds lookahead and prevents overwriting a stage still in use. It does not serialize the weight warp behind the activation warp's readiness polling. Removing the empty wait or claiming unbounded prefetch would be a different, unsafe proposal. The source demonstrates the independence, not actual overlap duration or HBM transaction behavior.

Thus a generic proposal to introduce a weight-prefetch warp adds nothing missing. There is no new break-even win to forecast from this already-present feature. A future change to stage depth, next-task lookahead or cache residency needs its own concrete policy and buffer/resource proof; increasing a stage count cannot be assumed to improve latency.

## Component2: paper-inspired metadata producer already exists

FlashMask-3 §3.1 reuses otherwise idle producer-group threads as a KV Index Generator, which scans its compact masks and feeds valid blocks to a KV Loader. A persistent scheduler claims query tiles in that role. This is a useful separable principle: prepare control metadata away from the operand/compute critical path without changing mathematical work.

The native MegaMoE kernel already assigns `warp_idx == kNumDispatchWarps + 3` to `scheduler.mainloop` on the leader CTA. `MegaMoEScheduler` has two task slots, full/empty barriers and a consumer API. The scheduler waits for a free slot, claims a task, then publishes it. Consumers read the slot before it is released; the epilogue releases metadata after UMMA arrival with the fence protocol. Per-expert counts are cached, and locality-aware queues/work stealing already select work. Shared L1 tasks precede routed-count admission; shared L2 is placed early only when its wave fits the dispatch gap.

Therefore the paper's basic third-role/queue mechanism is not missing. Its mask-specific scans cannot be inserted into expert routing as though the objects were equivalent. The fixed target has expert/task counts and ring generations, not per-column attention mask intervals. Its mask-driven CP all-gather pruning also targets a different collective than the planned EP4 dispatch. We do not discard the entire paper: producer/consumer separation and progress reasoning remain valid design references, but this read does not establish a new target delta.

The paper's forward all-gather appendix discusses resource reservation and scheduling to avoid a consumer starving its communication producer. This reinforces a safety obligation for any future external prefetch stream; it does not license adding one here. Its H100 long-context training results and eight-GPU/IB topology are not a B200 decode gain estimate.

## PR triangulation and contrary evidence

Three bounded read-only full-corpus FTS queries were followed by selected import of three opening records and an actual `pr-search` over that explicitly limited subset. These are body-level screens, not inspections of their complete diffs:

- **DeepGEMM404:** independently controls routed-weight demand-load EVICT_FIRST and explicitly excludes previous-active-expert prefetch because benefit is routing-sensitive. This is not evidence of installed prefetch. Weight cache policy overlaps the already retained WP38 optional policy component; no new cache-hint card is created. Donor H4096/EP8 timings do not describe this target.
- **FlashInfer6447:** SM107 sparse metadata/reset/dispatch changes and separately tuned paths. Its prefetch prototypes remain outside the described diff. It does not establish an SM100 native prefetch implementation to port; other components are left outside this bounded question rather than declared globally ineligible.
- **SGLang36657:** donor body describes grid-barrier liveness under competing streams and an SM reserve. This is a caution against assuming a new prefetch stream is free. It is not a target bug proof or a new resource-partition proposal.

No further diff hydration was needed to reject the two already-implemented additions: exact target source, rather than PR prose, establishes those facts. No source performance claim is treated as an independently reproduced experiment.

## Fastest falsifier and evaluation boundary

The cheapest falsifier was the actual source audit: find whether the weight producer is behind activation readiness and whether task computation is inline in the operand loop. Both proposed missing-work premises failed. No artificial timeline or repeated scalar case sweep could improve that determination, so none was run.

For any later *different* prefetch proposal, the necessary break-even condition is exposed critical-path wait removed exceeding added prediction/metadata/copy/cache-contention/occupancy cost under the same route and workload. Payload counts and a prettier overlap diagram are insufficient. It must preserve exact weight/scale identity, ring/stage generations, producer publication, termination, shared-expert work and numerical/tactic semantics. Prior A52 already covers moving all-rank admission; this round does not repackage that larger scheduler rewrite.

The unchanged Mooncake and agent-p75 loads remain the serving evaluator if a concrete new intervention emerges. Neither currently supplies exact operand-ready/stage-wait measurements for this source plan. A narrowly scoped all-rank timeline or stage-wait diagnostic would be needed only to discriminate an actual new policy, after separate GPU authorization. No new workload, numerical tolerance, ROI percentage or deployment promotion is justified by this screen.

## Yield and tool usefulness

-153 compact prior cards,21 selected lexical matches; current map and complementary report coverage retained.
-2 authored expansions and2 actual dated provider calls;12 references/12 identities;1 selected new versioned fulltext.
-3 local PR FTS queries;3 selected opening records;1 bounded subset PR-search replay.
-2 concrete additions rejected as already implemented; remaining offload/approximation/hardware branches retain scoped dispositions;0 new formal cards and0 measured improvements.
-Existing exact source files were reused. Four code documents were explicitly committed to isolated Store, then reopened read-only to verify persistence and hashes; source export contains the immutable evidence.
-The only CLI mistake was trying the nonexistent top-level `recall-hypotheses` command while checking help; corrected to `hypothesis recall`. Broad source-search output was bounded/truncated, then decisive source sections were read directly. Neither is claimed as a new tool defect.

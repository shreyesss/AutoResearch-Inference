"""Source-grounded reconciliation; preserves all original runs and identities."""
import csv,json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
RUNS={'B':'pr-evaluation-audit-001','A':'h200-pr-evaluation-audit-001','F':'h200-fresh-research-001'}
rows=[]
def add(id,title,rank,b,a,f,stage,problem,solution,feasibility,first,measure,stop,transfer):
 rows.append(dict(id=id,title=title,rank=rank,prior={'B':b.split(),'A':a.split(),'F':f.split()},stage=stage,problem=problem,solution=solution,feasibility=feasibility,first_check=first,evaluation=measure,stop_rule=stop,b200_transfer=transfer,status='comparison_only_unexecuted'))
add('C01','Humming: backend first, then indexed versus grouped',1,'E18','H01 H07','H01','existing controls, conditional',
 'Marlin currently executes the MXFP4 experts. Backend GEMMs and expert packing can consume different amounts of time for the same routed tokens; EP also affects grouped versus indexed execution.',
 'Compare Marlin, Humming grouped and Humming indexed at identical BF16 activation semantics, routing, transport and graph settings. Use installed controls first; port only missing dispatch behavior.',
 'Both audits agree. Fresh adds Humming0.1.16 schema counterevidence and failed #59488 patch application. A selectable name is not proof of legal W1/W2 schemas. Three fixed arms are more informative than bundling backend, activation and precision.',
 'Record effective backend, W1/W2 schema and GEMM type for both target and draft on every rank. Logs contain E384/top6/local96 and E128/top3/local32 configurations; resolve their role tags and qualify both. Preserve clamp10.',
 'Existing E1/E2 plus exact-shape expert/reference fixtures. Measure full routed-expert span including permutation/quantization/combine, HBM/KV loss, accepted tokens and qualified goodput. Static indexed must beat static grouped to support indexed preference.',
 'Stop on illegal schema, silent precision fallback, dispatch mismatch, numerical failure or no useful service improvement. Do not infer a win from GEMM time alone.',
 'Generic MoE evaluation logic transfers; Blackwell MegaMoE and precision defaults do not. Humming is a particularly concrete Hopper comparator.')
add('C02','Share compatible FlashMLA planning metadata',2,'','','H02','small source port',
 'Compatible attention groups can each rebuild the same execution plan during one metadata-building pass, repeating host work and planner launches.',
 'Reuse a plan holder within that pass only when all live compatibility fields match. A tensor-shape match alone is insufficient if lengths, masks or graph buffers differ.',
 'Genuinely new to the fresh shortlist: #58818. Its three vLLM source-file changes applied to disposable installed-source copies. No execution, correctness or end-to-end gain was demonstrated.',
 'Trace active sparse attention builders and count duplicate planner calls plus compatible opportunities. Inspect existing same-type reuse and the holder lifetime. Include target and draft and changing graph replay lengths.',
 'E1/E2 remain sufficient for performance. Add shared-versus-separate plan reference tests for ragged lengths, masks, mixed groups, prefill/decode and graph replay. Measure eliminated launches, exposed CPU/planning time and unprofiled TPOT.',
 'Hold if planning is already shared or no compatible duplicates occur. Reject unsafe reuse; mark a tiny effect inconclusive if drift exceeds it.',
 'Potentially portable orchestration improvement, not a small-head TP4 optimization. No H200 gain follows from H20 synthetic-acceptance results.')
add('C03','Use logical requests rather than target padding for drafting',3,'E02','H02','H04','source adaptation',
 'Target CUDA graphs pad requests to a capture capacity. Reusing this padded capacity for DP draft dispatch schedules unnecessary rows, including on lightly loaded/dummy ranks.',
 'Carry real request counts alongside graph capacity and use them coherently in draft inputs, metadata and dispatch, retaining full startup capture capacity.',
 'All three audits converge on #58984. Fresh shows source conflicts with the pinned image, so this is an adaptation rather than a demonstrated clean cherry-pick.',
 'Trace DSpark inheritance into the installed helper; record real, target-padded and draft-padded request counts and every dummy rank. Check equivalent behavior before editing.',
 'Use existing E1 and burst/idle-skew E2. Add upstream dummy-rank/distributed fixtures. Compare draft rows/time, collectives, graph mode and ITL at identical acceptance and load.',
 'No eligible excess rows means inactive. Inconsistent per-rank counts or graph-buffer bounds block execution. Padding reduction without service value is a negative serving result.',
 'The repeated-work mechanism transfers. Seq128 saturation claims and Blackwell timing do not.')
add('C04','Reduce CPU DP metadata synchronization overhead',4,'E04','H03','H05','source adaptation',
 'Tiny CPU reductions can delay dispatch even when GPU compute and GPU collectives are fast. Time waiting for late ranks can look like slow transport.',
 'Use the reviewed low-latency CPU reduction implementation only for compatible groups and message ordering; preserve fallback and failure behavior.',
 'All three identify #61767. Fresh finds patch conflicts and exposes group-local rank/tag/order checks. Two local DP4 groups differ from the source multi-node benchmarks.',
 'Measure arrival skew separately from time after the last rank arrives. Attest actual process-group backend, ranks, tensor shape, tags and sequence of calls.',
 'E1/E2 plus upstream collective tests and CPU spans. Track scheduler-to-GPU gaps, all-rank progress, collective cost, TTFT/TPOT tails and qualified goodput.',
 'Defer if skew dominates or reduction cost is hidden. Reject ordering/deadlock failures or worse end-to-end tails.',
 'Hardware-independent CPU logic may transfer, but topology and NUMA determine actual benefit.')
add('C05','Tune SM90 mHC for actual one-to-eight-row launches',5,'','H06','H03','small port; low-load lane',
 'The repeated fused mHC post/pre-norm kernel uses a launch split tuned for Blackwell. Hopper can prefer a different split at tiny row counts.',
 'Apply #61461 only for SM90 and rows1–8, preserving other shapes and math except documented reduction order.',
 'Fresh confirms source hunks apply. Both H200 runs cite H20 evidence; neither measured H200. k5 suggests six logical rows for one request, but graph padding can exceed the gate.',
 'Count actual executed delayed5120-wide kernel rows, not client concurrency. Resolve the active prenorm binary and qualify the relevant DeepGEMM448/59129 lifetime fix first if executed.',
 'Existing client at node concurrency1/2/8 plus normal E1/E2; upstream numerical tests. Track eligible-row fraction, mHC microseconds and low-load TPOT. Treat saturation as a separate endpoint.',
 'Do not rank as a broad capacity win without exposure. A small kernel gain can be beneath server noise; no global benefit if most calls have >8 rows.',
 'Architecture-specific tuning changes. B200 parameters are precisely what must not be assumed optimal on H200.')
add('C06','Repair demonstrated prefix-cache/draft interactions',6,'E11','H04','','diagnosis before selecting a patch',
 'A target prefix hit may be vetoed by draft-group bookkeeping or expose draft context whose KV was not written. Junction handling can lose reachable sibling prefixes.',
 'Select one matching fix among #47926/#62278/#57110 and related annotations only after distinguishing invalid restored draft context from target-hit loss.',
 'Earlier H200/B200 work covers this more explicitly than fresh17. Prefix cache and DSpark are active; symptoms and exact missing behavior remain unmeasured.',
 'Correlate cached token counts per group, final DP rank, hit length, unaligned boundaries and acceptance. APC-off/cold/warm controls distinguish cache bugs from general drafter weakness.',
 'Reuse agent-f75 and cache-heavy Mooncake. Add small same-client sibling/unaligned-prefix fixtures only when absent from the trace. Track recomputed prefill, acceptance, TTFT and reference quality.',
 'Do not cherry-pick a bundle or treat higher acceptance alone as correctness. Hold if equivalent fixes already exist or no specific symptom appears.',
 'Generic cache/drafter semantics transfer, but V4 flags and other-model evidence need V4.1 inspection.')
add('C07','Remove repeated scheduler cache work',7,'E12','H05','','profile-triggered small port',
 'Long SWA block tables have large null heads; unchanged partial-prefix boundaries can be registered repeatedly in Python before GPU work starts.',
 'Test #61724 null-head skipping separately from #51333 registration memoization; preserve promotion, copy-on-write, release and preemption invalidation.',
 'Retain from earlier audit. Fresh omission is not rejection. Seq64 and H200 GPU costs may leave less exposed CPU time than the B200 high-concurrency source case.',
 'CPU sample the actual scheduler; count scanned null entries and repeat registrations at identical block/hash. Verify missing implementation.',
 'E1/E2 with long-context cohorts and CPU spans; upstream cache lifecycle tests. Measure GPU idle gaps and useful end-to-end improvement.',
 'No measured repeated work or hidden CPU cost means defer. Cache lifetime regressions reject the patch.',
 'Code-level mechanism transfers; source percentages from roughly900 running requests do not.')
add('C08','Hopper selector integration and length-aware block selection',8,'E01 E06','H09','H07','native dependency + narrow dispatch',
 'The installed selector gates DeepSelect to SM100; candidate-block selection can scan max-context-width padding instead of only valid blocks.',
 'First qualify SM90 native DeepSelect with the correct FP32/stride contract. Then isolate #61039 valid-length selection from the selector replacement. These are distinct factors.',
 'Fresh #59204 Python hunks apply, but native compilation/tests were excluded from that check. Earlier H200 correctly identifies #61039 cannot deliver its intended Hopper path merely by changing Python.',
 'Resolve extension revision/build target, actual dtype/K/width/alignment, valid counts and loaded binary. Test actual width rather than equating prompt tokens with compressed logit columns.',
 'E1 short live contexts under large max context diagnose padded work; E2 covers ragged cases. Upstream top-k bounds/ties/NaN and changed-input graph tests; compare selector-only, then length-aware.',
 'Do not confuse this with candidate-only decode scoring C09. No native support or mismatched numerical/ordering contract blocks execution.',
 'B200 can access different native selector paths; the same PR ID does not imply equal integration effort on Hopper.')
add('C09','Candidate-only long-context decode scoring',9,'','H08','H06','source adaptation; long-context lane',
 'Dense Hopper decode indexing can score the full compressed context even though only a candidate subset will be consumed.',
 'Compare dense scoring with #62000 candidate-K gathering and #62463 direct paged-K scoring as separate alternatives, keeping selection semantics and prefill unchanged.',
 'Both H200 audits converge. Fresh shows both patches conflict with installed code; #62000 reports a single-request regression. Neither author result proves current H200 value.',
 'Match FP8 cache format, compressed row IDs, causal bounds and candidate producer. Count candidates versus full live columns; configured pool2048×8 is not automatically the number used on every request.',
 'Inspect Mooncake length histogram before adding a new cohort. Existing client can extend32K/128K and feasible longer lengths if needed. Measure bytes, gather/temp cost, score/selection agreement and context-stratified ITL, including short/C1 controls.',
 'If candidate setup costs exceed avoided dense work, keep dense fallback. Fixed8K E1 alone cannot establish a long-context frontier improvement.',
 'Earlier B200 E01 length-aware block selection is related, not the same algorithm; do not count them as repeated independent confirmation.')
add('C10','Preserve cache affinity at the final DP rank',10,'E14','H12','H09','routing adaptation',
 'Endpoint affinity can be lost when separate API workers choose different internal DP ranks, scattering warm prefixes.',
 'Use load-aware internal prefix tie-breaking (#52464), retaining salt isolation and load precedence. Shared frontend state is a distinct expansion beyond a local tie-break.',
 'All three contain the idea; source high-load effects are weak/mixed. Actual router source differs between baseline snapshots and must be reconciled.',
 'Join request, endpoint, API PID and final rank. Show locality loss at the internal selector and absent equivalent affinity before implementation.',
 'Existing E1 prefix pools and E2 cache-heavy/burst. Measure token-weighted hit rate, queue skew, CPU overhead and TTFT tails; hold out new sessions and heavy imbalance.',
 'Reject stale/unsafe shared state or worsened tails. Affinity that only improves idle C1 does not establish saturation throughput value.',
 'Generic routing idea transfers; different router source/settings can entirely change the apparent opportunity.')
add('C11','Bound coordinated DP prefill release',11,'E13','H11','H10','scheduler/protocol adaptation',
 'A prefill-heavy rank can stall decode peers during synchronized steps, producing decode tail spikes.',
 'Compare existing scheduling with one of #51199/#61834, separately. Freeze a bounded policy after discovery; preserve dummy/pause/cancel participation.',
 'Shared lead across all audits. A check performed only when a step starts does not guarantee a hard wall-clock waiting bound during long steps.',
 'Measure mixed-step interference and oldest-prefill age. Inspect starvation escape, long-step timing and interaction with existing prefill interval controls.',
 'E1 and E2 burst/mixed loads plus distributed lifecycle fixtures. Track TTFT and TPOT together, per-rank backlog, accepted tokens/step and collective wait.',
 'Reject decode gains bought with violated prefill SLOs or deadlocks. Do not interpret fixed steps as fixed emitted tokens under DSpark.',
 'Scheduling mechanism transfers, but slower/faster prefill and communication change the useful policy.')
add('C12','Contiguous prefill MQA epilogue',12,'','H16','H08','narrow kernel change; numerical gate',
 'The contiguous SM90 MQA logits epilogue can spend instructions on ReLU that a different arithmetic form may reduce.',
 'Evaluate DeepGEMM452 at identical compile/launch settings, with an enforceable numerical domain or stock fallback. Paged decode is unchanged.',
 'Fresh strengthens earlier H16: installed header is old, but loaded JIT artifact remains unproved. Saved CPU counterexample disproves universal finite-input equivalence, not actual deployment correctness.',
 'Trace actual contiguous prefill calls, FP8/BF16 API and logit dtype, loaded header/JIT binary and input/scale ranges. Positive x near FLT_MAX can overflow in x+abs(x) before later compensation.',
 'Existing uncached/mixed prefill E1/E2; warm-prefix and paged-only negative controls. Add extreme/real-range, scale-underflow, tie/top-k and quality references. Compare full prefill TTFT, not best-of-three kernel time.',
 'No defendable bounds or reference mismatch blocks the arithmetic change. An extreme CPU counterexample alone does not prove real H200 model failure.',
 'Hardware-specific Hopper kernel lead; do not attribute any decode gain to this prefill-only epilogue.')
add('C13','Per-token FP8 Humming activation',13,'E18','H07','H11','separate precision arm',
 'Activation format can change expert GEMM arithmetic and memory cost, independently of backend choice and indexed/grouped execution.',
 'After C01 establishes a legal incumbent, compare BF16 and explicitly supported per-token FP8 with fixed GEMM/transport; quantify conversion costs and quality.',
 'Fresh correctly splits this from backend selection. Humming0.1.16 block-FP8 schema mismatch and MXFP8 limitations cannot be ignored or silently bypassed.',
 'Attest effective target/draft W1/W2 scales, formats and no fallback. Do not infer that advertised schema acceptance proves a legal SM90 kernel.',
 'E1/E2 plus actual generation-quality/reference fixtures because arithmetic changes. Measure quantization+GEMM+combine, acceptance, output quality and KV/workspace cost.',
 'Reject hidden format fallback, unsupported schema, quality regression or no useful combined-span improvement.',
 'Precision names and native hardware support differ; Blackwell FP4/FP8 choices are not interchangeable Hopper controls.')
add('C14','Fuse top-k with physical KV-slot mapping',14,'','','H13','consumer-aware kernel integration',
 'After selection, index IDs may be converted to physical KV slots in separate launches, creating temporary traffic and synchronization.',
 'For consumers needing only physical slots, fuse mapping into selection. Preserve raw-ID paths and ordering for consumers that still need logical positions.',
 'Fresh cross-engine extension (SGLang41561); also inspect FlashInfer5889/current vLLM equivalents before custom implementation. Torch-chain microbench is not the strongest comparator.',
 'Trace all consumers, block64 mapping, causal/order/tie contracts and native SM90 operator. Compare to C08 selector-only with identical selected sets.',
 'Three arms: current chain, fast selector+separate mapping, fast selector+fused mapping. Same E1/E2 plus raw-ID fallback, page-reuse and changed-length graph correctness.',
 'If raw IDs are still needed, saved traffic may disappear. Do not attribute fast-selector gains to mapping fusion.',
 'Transfer concept from another engine, not a drop-in PR; existing vLLM implementation must be checked.')
add('C15','Shared Engram placement and exposed lookup cost',15,'E10','H10','H17','rescope; shared path only',
 'CPU-offloaded lookup cost may depend on shared physical backing, NUMA placement and translation behavior even when private allocation waste is absent.',
 'Keep current shared ownership. First compare supported NUMA-local placement/settings; only then consider separately scoped shared-cuMem or lookup-threshold changes.',
 'Fresh proves dp_shared_memory=True on both replicas. Earlier H10 included multiple arms: its private exact-allocation arm is inactive, but shared placement is not disproven. dp_shared_memory does not identify physical backing by itself.',
 'Inspect /dev/shm versus cuMem, physical PSS, registration/page type, allocation NUMA and exposed lookup spans. Probe FABRIC/export support before proposing a shared-cuMem implementation.',
 'Reuse E1/E2 with host memory/NUMA/lookup counters. Keep sorting and placement isolated; compare lookup span and end-to-end prefill, not summed RSS of shared mappings.',
 'No active allocation delta or fully hidden lookup cost means hold. Host-memory savings alone do not free GPU KV or lower node price.',
 'GB200 coherent-memory/page-walk thresholds are not H200 defaults. Requires a new shared-storage scope rather than reviving the rejected private card.')
add('C16','Scheduler budget reserved for separate drafts',16,'E07','H13','','low priority; prove binding budget',
 'Charging separate DSpark draft slots against target scheduling can reduce usable work when the token budget is tight.',
 'Compare #59468 at unchanged seq64/MBT16384/k5 only when actual budget-bound steps are observed.',
 'Earlier audit retains this; fresh top17 omits it. At this large budget, source MBT512 gains are a weak transfer. Prefill can still consume budget, so not a mathematical proof of inactivity.',
 'Measure charged versus scheduled target tokens and requests blocked by budget, separating prefill pressure and buffers.',
 'E1/E2 and upstream buffer-bound tests. Preserve MBT; a smaller-budget synthetic diagnostic is labelled separately.',
 'Do not lower MBT merely to manufacture a baseline benefit. No binding resource means defer.',
 'Generic scheduler logic transfers; original bottleneck severity does not.')
add('C17','Unreachable draft graph buckets',17,'E03','H14','','low priority; boundary evidence required',
 'Rounding target-derived capture sizes to draft query length can omit an otherwise legal full draft batch.',
 'Apply #62040 boundary correction only if an actual missing bucket or eager fallback is demonstrated.',
 'Both H200 audits reject carrying seq128×6 pressure unchanged: target384 and draft320 fit cap512 at seq64. Capacity coverage alone still does not prove every intermediate bucket exists.',
 'Enumerate actual target/draft capture ladders and observe selected bucket/eager fraction at live shapes.',
 'Existing E1/E2 and boundary tests; record launch overhead, graph HBM and remaining KV blocks.',
 'No missing live bucket means no-op. Do not increase graph cap blindly and consume KV headroom.',
 'B200 benchmark seq128 differs from H200 seq64; a launch-configuration diagnosis is not an architecture-independent fact.')
add('C18','Bound drafter context if long-context acceptance collapses',18,'E17','H15','','symptom-dependent',
 'Draft attention cost or acceptance can deteriorate outside a drafter-compatible context range.',
 'Test #61261 bounded window only after separating length effects from prefix-restoration bugs and workload domain. Adaptive verification stays off.',
 'Earlier audit retains this; absence from fresh17 is not a refutation. Current evidence comes from another model/hardware.',
 'Measure draft time and accepted length versus actual context, hit state and content; inspect drafter training context/RoPE.',
 'Existing long-context/session/Mooncake cohorts and cached real-domain SPEEDBench if necessary. Keep short-context control and task quality.',
 'No length-dependent problem means hold. Acceptance gain with quality or throughput loss does not support serving value.',
 'Concept may transfer; the original Kimi evidence does not validate DeepSeek.')
add('C19','Native MXFP4 SM90 fused expert backend',19,'E18','X02','H12','large native integration',
 'Separate expert dispatch, staging, GEMM and combine can expose more time than a compatible fused implementation.',
 'Compare FlashInfer6343/6517 and DeepGEMM411/473 eligibility before writing an adapter. Keep native MXFP4 semantics and required activation clamp; use a dependency-matched unfused control.',
 'Fresh materially improves old X02 with native-MXFP4 leads. vLLM62603 is block-FP8, not a ready native-MXFP4 adapter. Current FlashInfer0.7.0.post1 may lack required APIs.',
 'Prove E384/top6/local96 AND E128/top3/local32 routing branches, H5120/I2304, clamp10, nibble order, scale ranges, EP4 workspace agreement, empty ranks and graph lifetimes.',
 'Kernel/reference and distributed correctness before E1/E2. Measure fused expert span plus workspace/KV loss and quality. If precision changes, label combined backend/precision effect instead of pure fusion.',
 'Stop unsupported semantics before spending on serving builds. EP8 push-dispatch source gains do not predict EP4.',
 'Blackwell integrated MegaMoE is an active incumbent there; Hopper requires separate integration, so priority and cost change sharply.')
add('C20','DeepEP activation, then triple-buffer dispatch',20,'','','H14','communication backend integration',
 'Direct-NVLink dispatch may benefit from overlapping hidden/scales/metadata movement, but the current allgather/reducescatter path never executes that DeepEP kernel.',
 'Stage1: compatible fixed DeepEP versus current AG/RS. Stage2: DeepEP baseline versus #693 triple buffering, with combine unchanged.',
 'Fresh-only explicit design. H100 direct-NVLink evidence and later elastic API changes require version-matched adapter work.',
 'Check EP4 payload/scales, routing ranks, shared-memory/workspace limits, direct path eligibility and exact adapter API. Require independent idle/zero-token collective participation.',
 'E1/E2 with skew and mixed loads; measure dispatch AND combine, queue/compute overlap and memory/KV cost. Isolate activation from the kernel patch.',
 'No active compatible DeepEP path means the patch is inapplicable; a changed backend gain does not validate triple buffering.',
 'Communication concepts transfer but actual selected backend and EP topology govern eligibility.')
add('C21','SM90 mHC coefficient overlap',21,'','X01','H15','experimental integration',
 'Coefficient work may run concurrently with another stage if dependencies and GPU resources permit useful overlap.',
 'Opt in to #60768 on SM90 after qualifying affected prenorm synchronization. Keep TF32 overlap separate from compensated-BF16 primitives.',
 'Both H200 runs retain as exploratory; old installed gate is SM100. Draft proposal has no target serving validation.',
 'Trace executed JIT artifact, event/stream dependencies and resource occupancy; first resolve DeepGEMM448/vLLM59129 applicability.',
 'Reference/repeatability and changed-input graph fixtures; short Nsight timeline separate from unprofiled E1/E2. Measure exposed critical path, not merely concurrent kernel bars.',
 'Overlap that slows both kernels or introduces races is rejected. CPU tests do not establish GPU lifetime safety.',
 'SM100 fused-allreduce overlap implementation cannot simply be enabled on SM90.')
add('C22','KV offload as a separate capacity configuration',22,'E16','X03','','feature activation + correctness',
 'Cache eviction may force repeated prefill; external KV capacity helps only when avoided recomputation exceeds transfer and management costs.',
 'Activate one compatible connector as a separate baseline, then test matching save/restore fixes individually.',
 'Not enabled in the observed commands. Engram CPU offload and Mooncake trace replay do not imply KV offload is active.',
 'Prove reuse beyond GPU capacity and resolve draft-group ownership, transport and host budget. Verify each connector prerequisite and restore lifetime.',
 'Existing cache-heavy replay plus narrow eviction/restore/cancel/stale-KV fixtures. Measure hit-source tokens, transfers, acceptance, TTFT and physical memory.',
 'No pressure/benefit means hold. Wrong restored KV or transfer-induced tail failure vetoes the path.',
 'Generic capacity tradeoff, but H200 memory and transfer costs change the crossover.')
add('C23','Matched SGLang control',23,'','','H16','external engine comparator',
 'A different serving engine may expose an achievable service gap, but engine-level differences bundle many mechanisms.',
 'Match checkpoint/tokenizer, TP1/DP4/EP4, host Engram, KV precision, graph/cache settings and actual DSpark rejection. Then isolate any group32 tuning within SGLang separately.',
 'Fresh adds a useful external comparator. It is not a vLLM-fork patch and should not displace cheap first experiments.',
 'Produce a parity checklist with irreducible differences, including tool encoding, target/drafter math, sampling and output counts.',
 'Same frozen E1/E2 and quality gates; report unmatched factors. A matched engine gap motivates investigation, not attribution to a single kernel.',
 'No semantic parity means report an informative but confounded comparison, not a valid A/B for one PR.',
 'Source H200 bundle headlines cannot be decomposed into additive vLLM patch gains.')
add('D01','Private Engram exact allocation: inactive',None,'E10','H10','H17','hold: contradicted path',
 'The exact-registration proposal targets rounded private tables.',
 'No live change proposed: preserve the historical card and reject its private-path applicability; use separately scoped C15 for shared storage.',
 'Fresh resolved logs prove dp_shared_memory=True for both replicas. That meets the private card\'s own rejection condition.',
 'Reopen only if a future baseline actually uses private rounded allocations.',
 'No GPU experiment needed for an inactive branch. Retain the evidence in the decision ledger.',
 'Do not call all Engram work disproven; only this allocation intervention is inactive.',
 'Original GB10/B200 private allocation evidence is not this deployed branch.')
add('D02','TP4 Marlin alignment alternative',None,'','T01','','different topology',
 'TP4 expert width576 pads to640 at128 alignment;64 alignment avoids that padding.',
 'Only evaluate #56697 against a separately qualified TP4 baseline.',
 'Current TP1/EP4 width2304 is already128-aligned, so this mechanism is inactive.',
 'User must deliberately select a TP topology study; do not mix a topology switch with the patch effect.',
 'Same E1/E2 with TP4-specific memory/quality checks and standalone baseline.',
 'No padding difference at live TP1 means no live patch gain.',
 'Shape arithmetic, not GPU brand alone, determines applicability.')
add('D03','Small-head sparse attention alternative',None,'','T02','','different topology',
 'Padding8/16/32 local attention heads to64 can waste work.',
 'Native-head prefill #61615 and decode #59418, or alternative #57673, only on eligible local-head shapes.',
 'TP1 retains64 heads; live configuration does not match. TP4 gives16, a different experiment.',
 'Confirm local heads and actual query rows; resolve FlashMLA26 dependency.',
 'Separate TP4 E1/E2 plus numerical attention references; alternatives isolated.',
 'No small-head shape means inactive on the requested deployment.',
 'Architecture-specific backend support and topology both matter.')
add('D04','TP-sharded fused prefill projection',None,'','T03','','different topology',
 'Replicated TP projection can duplicate work at sufficiently large prefill batches.',
 'Shard rows and all-gather via #58872 only when TP>1 and break-even is measured.',
 'TP1 has no cross-TP redundancy; H20-derived H200 thresholds are unmeasured.',
 'Separate TP4 baseline and compatible collective/SP/LoRA checks.',
 'Prefill E1/E2, projection plus gather timing, numerical references.',
 'No TP redundancy means no current benefit.',
 'Do not extrapolate a TP4 optimization to DP4.')
add('D05','Blackwell MegaMoE warmup and activation repacking',None,'E05 E08','','','hold: backend not established',
 'First-use compilation and redundant activation packing can waste time on particular MegaMoE paths.',
 'Retain B200 designs; reopen only for the exact equivalent active Hopper backend.',
 'Current H200 Marlin/AGRS does not establish the Blackwell MegaMoE call path. Cold-start time is also distinct from warm serving capacity.',
 'Find matching symbols/dtypes in an actually selected H200 route before porting any PR.',
 'If active later, independent startup or packing diagnostics plus E1/E2, appropriate to the claim.',
 'Hardware-tag keywords do not prove a generic fix irrelevant, but no active equivalent path means no recommendation.',
 'B200 E05/E08 priorities cannot be inherited unchanged.')
add('D06','B200 FlashMLA pipeline and Engram/mHC fusion',None,'E09 E15','', '', 'hold: explicit architecture gate',
 'The B200-specific FlashMLA pipeline and Blackwell-only TP1 fusion target unavailable SM100 behavior.',
 'Retain as B200 work; a real SM90 adaptation would be a new scoped proposal.',
 'TP1 matching alone does not bypass the Blackwell gate in #60938.',
 'Require an actual Hopper implementation and correctness evidence before reopening.',
 'No current H200 experiment from a mere flag change.',
 'Do not silently remove architecture guards.',
 'These are major examples of why copying the B200 rank would be wrong.')
add('Q01','Sampling distribution qualification',None,'G01','Q01','','correctness prerequisite',
 'Reused random draws across block-verification rounds can bias generation despite normal acceptance and throughput.',
 'Qualify #61161/equivalent implementation on the actual stochastic path.',
 'Probabilistic DSpark/block rejection is configured; source membership and executed path still matter.',
 'Use upstream analytical target/draft fixture and independent seeds/temperatures.',
 'Distribution tests with predeclared tolerance and comparisons; temperature0 E1 cannot prove this property.',
 'A sampling failure blocks affected performance comparisons; no speedup is claimed.',
 'Semantic correctness transfers; image membership must be checked.')
add('Q02','Index/graph bounds and mHC lifetime qualification',None,'G02 G03','Q02','','correctness prerequisite; scope kernels',
 'Invalid top-k tail lanes, graph state or asynchronous operand lifetime can silently corrupt results.',
 'Map each active H200 kernel to its relevant fix, especially62467 and DeepGEMM448/59129; retain Blackwell-only barrier checks in B200 scope.',
 'Fresh source shows affected TF32 header ordering, but executed JIT/binary must be resolved. Source presence is not observed corruption.',
 'Identify exact dispatch, dependency binary and changed-input graph/tail/empty-row cases.',
 'Upstream references, replay/repeatability and bounded sanitizer cases for changed paths; no unrelated universal test quota.',
 'Do not claim a slow/fast candidate is valid before this scope passes.',
 'B200 G03 SM100 mega_mhc barrier fix is not identical to Hopper WGMMA lifetime fix.')
add('Q03','API2 liveness and restart identity',None,'G05','Q03','','correctness prerequisite; topology-specific',
 'DP wake-up ordering and draft compile-cache identity can fail during idle/resume or cached restart.',
 'Qualify #59559 and #62062 only when the specific coordinated/independent DP semantics match.',
 'API2 is present; #62062 dense independent DP evidence is not automatically coordinated EP4 proof.',
 'Inspect data_parallel_index and pause/wave transitions on a test deployment.',
 'Small lifecycle fixtures; steady E1/E2 alone do not cover them.',
 'No restart of user services performed during this comparison.',
 'Generic lifecycle concerns transfer, exact DP mode determines each fix.')
add('Q04','Tool encoding, parser and changed-math quality',None,'G04','Q04','','correctness prerequisite',
 'Fast token output can hide malformed tool encodings/streams or degraded task quality after precision/engine changes.',
 'Freeze intended checkpoint encoding, use reference tool-role fixtures and evaluate changed-math quality with a pinned suitable suite.',
 'DeepSeek v41 parser is active; encoder upgrades change input token counts and must become a common qualified control.',
 'Check #62199/#62259/equivalent behavior and actual tokenizer revision.',
 'Golden token IDs/JSON stream assembly plus quality only where math/engine changes warrant it. Synthetic text sessions are insufficient for actual tool-role semantics.',
 'Correctness/quality regression vetoes affected serving promotion.',
 'Same checks across hardware, while deployed revisions may differ.')

def main():
 (R/'families').mkdir(exist_ok=True)
 maps=[]
 identities={}
 for run in [RUNS['A'],RUNS['B']]:
  for rec in json.loads((R.parent/run/'memory-registration.json').read_text()):identities[(run,rec['experiment_id'])]=rec['hypothesis_id']
 for card in (R.parent/RUNS['F']/'experiments').glob('H*.md'):
  match=re.search(r'Latest immutable identity: `(hypothesis:[^`]+)`',card.read_text())
  if match:identities[(RUNS['F'],card.stem)]=match.group(1)
 for row in rows:
  links=[]
  for alias,ids in row['prior'].items():
   for id in ids:
    rel='../'+RUNS[alias]+'/experiments/'+id+'.md'
    assert (R/rel).exists(),rel
    links.append(f'[{alias}:{id}]({rel})')
    relation='mechanism_correspondence'
    if alias=='B' and id=='E18':relation='broad_backend_precision_umbrella'
    if alias=='B' and id=='E06':relation='related_selector_family'
    if alias=='B' and id=='G03':relation='architecture_specific_correctness_analogy'
    if row['id']=='C15' and alias=='F':relation='new_shared_scope_after_private_rejection'
    if (alias=='A' and id in ['H07','H10']) or (alias=='B' and id=='E10'):relation='separate_arm_of_broad_original'
    maps.append({'relation':relation,'source_run':RUNS[alias],'source_id':id,'comparison_id':row['id'],'title':row['title'],'priority':row['rank'] or '', 'disposition':row['stage'],'source_hypothesis_id':identities[(RUNS[alias],id)]})
  row['source_plan_links']=links
  text=f"# {row['id']} — {row['title']}\n\nExecution inspection priority: **{row['rank'] or 'outside performance ranking'}**. Feasibility: **{row['stage']}**. No GPU test or new empirical outcome.\n\n## 1. Original proposals\n\n"+' · '.join(l.replace('](../','](../../') for l in links)+'\n\n'
  for n,title,key in [(2,'Underlying problem','problem'),(3,'Proposed solution','solution'),(4,'What the combined evidence establishes','feasibility'),(5,'Cheapest decisive feasibility check','first_check'),(6,'Evaluation and causal attribution','evaluation'),(7,'When to stop, reject or defer','stop_rule'),(8,'What transfers from B200','b200_transfer')]:text+=f"## {n}. {title}\n\n{row[key]}\n\n"
  text+='Apply the [shared decision protocol](../EVALUATION_RECONCILIATION.md). Primary PR citations and frozen snapshots remain in the linked original cards; this comparison preserves their identities and does not overwrite their verdicts.\n'
  (R/'families'/(row['id']+'.md')).write_text(text)
 expected={}
 for alias in ['A','B']:
  expected[alias]={e['id'] for e in json.loads((R.parent/RUNS[alias]/'experiments.json').read_text())}
 expected['F']={p.stem for p in (R.parent/RUNS['F']/'experiments').glob('H*.md')}
 actual={alias:{id for row in rows for id in row['prior'][alias]} for alias in RUNS}
 assert actual==expected,(expected,actual)
 with (R/'CROSSWALK.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(maps[0]));w.writeheader();w.writerows(maps)
 (R/'memory-correspondence.json').write_text(json.dumps({'scope':'Artifact-only comparison links; original memory DBs and verdicts unchanged. No new hypothesis or outcome registered.','links':maps},indent=2)+'\n')
 (R/'comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
 idx='# Consolidated H200 ranking\n\nB = original B200 audit; A = earlier H200 audit on Sofia (runtime219); F = fresh H200 research on223. Ranks are engineering inspection order, not predicted gains. All original cards are mapped, including inactive and correctness scopes.\n\n| Rank | Mechanism | Feasibility | Original cards |\n|---|---|---|---|\n'
 for x in rows:idx+=f"| {x['rank'] or '—'} | [{x['id']} — {x['title']}](families/{x['id']}.md) | {x['stage']} | {' · '.join(x['source_plan_links'])} |\n"
 (R/'RANKING.md').write_text(idx)
 stats={'source_card_counts':{k:len(v) for k,v in expected.items()},'source_cards_mapped':sum(len(v) for v in expected.values()),'families':len(rows),'ranked_families':sum(x['rank'] is not None for x in rows),'unmapped_source_cards':0,'new_gpu_experiments':0,'new_validated_claims':0}
 (R/'coverage.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))
if __name__=='__main__':main()

"""Render root engineering decisions; keep model artifacts and scores distinct."""
import csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parents[1];sys.path.insert(0,str(P))
from ideation.evidence import quote_errors,write_json
from ideation.hypotheses import assess
from ideation.hypothesis_memory import HypothesisMemory
from ideation.store import now
ledger=HypothesisMemory(P/'data/hypotheses.sqlite')
# Editorial repair of a short exact quote, with immutable ancestry and unchanged critique.
p=R/'prefill-mqa/hypotheses';old=json.loads((p/'history.json').read_text())[0]
sources=json.loads((p/'sources.json').read_text());policy=json.loads((p/'rubric.json').read_text())
card=json.loads(json.dumps(old['card']));card.update(id='H200-MQA-REPAIR-001',parents=[old['global_id']],operation='repair',revision_reason='Root editorial repair: expand the exact nine-character quote to satisfy the minimum quote length; mechanism, claims and experiment unchanged. Original rejection retained.')
for e in card['evidence']:
 if e['quote']=='avg +3.7%':e['quote']='sweep (192 contiguous MQA cases on SM90):\navg +3.7%'
assert not quote_errors(card['evidence'],sources)
review={**old['review'],'id':card['id']}
gate=assess(card,review,sources,policy=policy)
out=R/'prefill-mqa/quote-repair';out.mkdir(exist_ok=True)
identity=ledger.register(str(out),card,json.loads((p/'brief.json').read_text()),policy,sources)
ledger.review(identity,gate,review,policy=policy,context={'sources':sources,'actor_note':'Root applied unchanged model judgments to a quote-only editorial repair; no new model review and no performance evidence.'})
repaired={'card':card,'global_id':identity,'review':review,'assessment':gate,'provenance':'Root quote-only repair with unchanged model criterion judgments'}
write_json(out/'history.json',[repaired]);write_json(out/'sources.json',sources)
write_json(out/'repair-receipt.json',{'at':now(),'original':old['global_id'],'descendant':identity,'quote_validation':True,'assessment':gate,'new_model_call':False})
# Each tuple provides an independent root decision, not an alteration of a model score.
D=[]
def add(key,lane,local,title,priority,observation,fix,prediction,check,comparator,activation,diagnostic,falsifier,correctness,workload,urls):
 D.append(dict(key=key,lane=lane,original_id=local,title=title,priority=priority,source_observation=observation,source_fix=fix,root_prediction=prediction,baseline_check=check,strongest_comparator=comparator,activation=activation,mechanism_diagnostic=diagnostic,reject_or_defer_if=falsifier,correctness=correctness,workloads=workload,urls=urls))
V='https://github.com/vllm-project/vllm/pull/'
add('H01','compute','H200-COMP-001','Humming backend and indexed/grouped comparison',1,
 'Startup selects Marlin. Humming 0.1.16 and explicit backend/GEMM-type controls are installed; automatic MXFP4 priority excludes Humming.',
 '#59488 adds explicit activation selection and SM90 indexed handling. It is broader than the first comparison and has source conflicts on this image.',
 'At fixed BF16 activation semantics, indexed Humming may reduce gather/permutation and grouped execution overhead on some token-per-expert distributions. This is unmeasured.',
 'Resolve actual W1/W2 schemas, GEMM type, EP4 AG/RS compatibility, target/drafter backend and graph coverage. Use shipped flags first; adapt only the missing behavior.',
 'Running Marlin, fixed Humming grouped, fixed Humming indexed; hold precision, transport, routing and checkpoint constant. Include total permutation/quantization/reduction time.',
 'Backend and indexed-path calls / eligible expert invocations on every rank; tokens per expert and padded/empty experts.',
 'End-to-end expert span, permutation bytes and exposed GEMM time versus total forward time; distinguish faster math from less data movement.',
 'No legal installed path, silent precision fallback, gain only from changing transport/precision, or HBM/workspace cost causing worse service.',
 'Expert IDs/scatter, scales, top6 routing, empty ranks, graph replay, SwiGLU clamp10, target/drafter parity and quality.',
 'D1 then E1/E2, with low and high tokens-per-expert and held-out routing skew.',
 [V+'59488','https://github.com/vllm-project/vllm/issues/60600','https://github.com/vllm-project/humming/issues/38'])
add('H02','attention','h200-attn-20261020-01','Share compatible FlashMLA plans',2,
 'Multiple compatible attention groups can repeat planning; #58818 reports small synthetic-acceptance H20 gains. The three-file source patch applies to the captured image.',
 'Cache/reuse planning metadata within the intended compatibility and lifecycle scope.',
 'Removing repeated planning may reduce exposed host/device overhead at the actual group count. Small source gains may disappear into service noise.',
 'Identify active metadata builder and group compatibility, all live fields and graph lifetime. Source application is not execution proof.',
 'Same image with per-group planning; same groups, scheduler and graph buckets. Do not silently use a previously prepared but unverified image.',
 'Shared-plan hits / compatible planning opportunities; builds per scheduler step and group, invalidation reasons.',
 'Planning CPU span and launches, then unprofiled forward/TPOT; compare cold and warm paths.',
 'No duplicate active planning, incompatible live lengths/masks, no service benefit after adequately powered confirmation, or gain below drift.',
 'Mixed groups, changed lengths and masks, graph replay, prefill/decode, cache invalidation/lifetime and fallback.',
 'D1 and E1/E2; held-out mixed groups and ragged lengths.',[V+'58818'])
add('H03','compute','H200-COMP-003','SM90 small-row mHC launch tuning',3,
 'Installed split-k selection is GB300-derived. #61461 introduces SM90 configuration for one to eight rows; its source hunk applies.',
 'Use the SM90 tile/split/thread configuration only within the guarded shape range, retaining the existing fallback.',
 'A better launch shape may shorten the delayed fused mHC operation, if actual padded rows enter the small band.',
 'Confirm hc_mult4, H5120, executed delayed kernel and actual padded row histogram. Check the executed TF32 prenorm implementation first.',
 'Correctness-qualified unchanged launch config, then the narrow #61461 change alone; no concurrent overlap or dtype change.',
 'Tuned launches / eligible delayed-mHC launches; row histogram including padded rows and graph buckets.',
 'Kernel time and exposed mHC span; distinguish configuration benefit from compilation/cache warmup.',
 'No eligible rows at seq64 load, output mismatch, gain outside the guard only, or no service effect.',
 'Independent mHC reference, repeatability, warmup and graph replay, fallback shapes; apply relevant synchronization gate before timing.',
 'Low-load D1 plus native E1/E2; held-out 1–8 rows and larger fallback rows.',[V+'61461',V+'59129','https://github.com/deepseek-ai/DeepGEMM/pull/448'])
add('H04','systems','h200-systems-001','Use real request counts for draft sizing',4,
 'Installed uniform-batch helper takes target DP-sync request counts. #58984 separates real requests from target graph capacity; its multi-commit patch conflicts with this image.',
 'Carry DP-wide logical request count separately and use it for draft batches while retaining target padding and distributed liveness.',
 'Ragged/idle-rank workloads may spend less time drafting dummy rows. Fixed adaptiveOFF makes the observed padding gap a necessary activation question.',
 'Follow DSpark inheritance into the installed helper and compare logical, target-padded and draft-padded counts. Adapt exact final patch behavior; do not blindly cherry-pick.',
 'Identical k5, seq64, graph buckets and sampler with current request accounting; compare balanced as a negative control.',
 'Steps with logical count below target graph capacity / all draft steps; dummy rows avoided by every rank.',
 'Draft rows and time, acceptance and verify frequency, CPU synchronization and graph fallback. A better batch mix is a competing explanation.',
 'No active padding gap, draft resizing changes graph policy/acceptance, distributed mismatch, or only synthetic speedup.',
 'G01/G02/G05: sampling distributions, KV offsets, idle ranks, pause/resume, dummy inputs and graph replay.',
 'Ragged D1, mixed E1 and fixed burst E2; balanced and held-out arrival schedules.',[V+'58984','https://arxiv.org/abs/2404.15778'])
add('H05','systems','h200-systems-002','Small CPU DP reductions',5,
 'Installed DP synchronization calls dist.all_reduce. #61767 offers CPU recursive doubling; its large multi-node measurements do not predict local DP4 benefit and its source port conflicts.',
 'Use a guarded CPU collective for eligible small groups/tensors with normal collective fallback.',
 'Shorter exposed CPU control synchronization may improve steps where GPU work waits; observed allreduce duration might instead be arrival skew.',
 'Attest process-group backend, group-local ranks, tensor shape and invocation ordering; inspect fixed tags and fallback before adaptation.',
 'Current Gloo call with identical ranks/arrival skew; single-process and balanced timing controls where meaningful.',
 'New collective calls / eligible CPU reductions; all-rank entry/exit times and skew.',
 'Separate arrival wait, communication and exposed CPU critical path; trace only as a diagnostic.',
 'Mostly rank skew or hidden time, no eligible calls, inconsistent ordering/tags, or unchanged service despite microbenchmark gain.',
 'Group-local rank mapping, sequential/concurrent collectives, fallback, cancellation and idle/wake liveness.',
 'D1/E1 and burst E2, with deliberately balanced versus skewed batches.',[V+'61767'])
add('H06','attention','h200-attn-20261020-02','Candidate gather versus direct paged indexer scoring',6,
 '#62000 and #62463 provide Hopper candidate-only implementations. The first reports single-request regression; the second has small samples and incomplete quality coverage. Both conflict with installed source.',
 'Score only retained candidate blocks, either after KV gathering or directly through page tables; retain dense fallback.',
 'Avoiding irrelevant scoring may win at long contexts, while gather, irregular access or candidate bookkeeping may dominate shorter contexts.',
 'Match FP8 cache layout, compressed row IDs, candidate selection semantics and dependencies to this model; preserve dense selection semantics before claiming a lossless port.',
 'Current dense scoring, gather variant, direct-paged variant as separate arms. Compare exact candidate sets and equivalent fallback rules.',
 'Candidate-path calls / eligible indexer calls; candidate fraction, fallback reasons, live lengths and token rows.',
 'Scored KV bytes, gather traffic, launch count, logits allocation and exposed indexer time; check whether smaller candidate sets, rather than implementation, explain gains.',
 'No eligible long-context work, selection/quality failure, single-request/short-context regression beyond guard, or failed graph replay.',
 'Causal bounds, invalid candidates, ties, physical remapping, changing lengths inside graphs, numerical logits/top-k and quality.',
 'Long-context bands plus D1/E1/E2; held-out lengths and low concurrency, especially single request.',[V+'62000',V+'62463','https://github.com/sgl-project/sglang/pull/40860'])
add('H07','attention','h200-attn-20261020-03','Native DeepSelect SM90 integration',7,
 'Current gate permits SM100. #59204 has applicable Python hunks; DeepSelect #14 supplies SM90 work. Native extension/CMake compatibility was not tested.',
 'Build and dispatch a supported SM90 FP32 selector with existing fallback and shape checks.',
 'A faster selector may reduce indexer overhead for sufficiently wide eligible logits; current optimized top-k may already be competitive.',
 'Pin/build native dependency, match FP32 logits, strides and row bounds, verify installed dispatcher and full-head kernel eligibility.',
 'Current optimized vLLM top-k, not torch.topk alone; compare selector-only before adding page-mapping fusion.',
 'Native SM90 selections / eligible selector calls, with dimensions/dtype and fallback counts.',
 'Selection time, output conversion and total indexer span; hold logits and selected K constant.',
 'Unsupported native build, different tie/causal semantics, no current-selector improvement, or small component gain with no service value.',
 'FP32 edge cases, ties, short rows, strides, invalid rows, graph replay and deterministic/index-equivalent selection where specified.',
 'Context/row-count matrix then E1/E2; held-out short and wide logits.',[V+'59204','https://github.com/deepseek-ai/DeepSelect/pull/14'])
add('H08','prefill-mqa','h200-contiguous-mqa-epilogue-001','Contiguous prefill MQA epilogue',8,
 'Installed SM90 contiguous header still uses fmaxf and uncompensated scales. DeepGEMM #452 reports H200 kernel gains, with a best-of-three timing caveat and an overbroad numerical exactness claim.',
 'Replace ReLU arithmetic with x+abs(x) and halve downstream scale factors in the contiguous kernel.',
 'Fewer epilogue instructions may help exposed prefill scoring. Intermediate overflow/underflow and rounding require a defensible domain or a stock fallback.',
 'Resolve include and JIT artifact, actual FP8/BF16 logit API and shape bands; source presence alone does not prove active dispatch. Preserve the saved CPU overflow counterexample.',
 'Equally compiled/warmed unchanged contiguous kernel; paged decode is a negative control, not an expected gain.',
 'Changed contiguous calls / independently identified eligible prefill calls, by shape/dtype and cache-hit regime.',
 'Epilogue and total kernel time, prefill span and TTFT; separate cold JIT, prefix reuse and hidden overlap.',
 'No enforceable numerical bounds, selected-token/quality mismatch, inactive contiguous path, or component gain without qualifying service improvement.',
 'Finite extremes, NaN/Inf, signed zero, subnormals/FTZ, scale halving, reduction bounds, logits/top-k and generation quality.',
 'Cold/warm prefill and mixed E1/E2, held-out lengths/dtypes; paged decode negative control.', ['https://github.com/deepseek-ai/DeepGEMM/pull/452','https://github.com/deepseek-ai/DeepGEMM/pull/303'])
add('H09','systems','h200-systems-003','Shared prefix affinity at final DP rank',9,
 'PRs #59468/#52464/#51199 and CacheRoute expose cache locality and worker-local routing issues. Two API workers per replica mean endpoint affinity need not imply final-rank affinity.',
 'Existing upstream tie-break/locality mechanisms inform a shared per-replica affinity table at the final rank decision; this shared adaptation is a root hypothesis.',
 'Stable prefix placement may reduce duplicate prefill, but stale placement and hot-prefix imbalance may cost more than they save.',
 'Inspect existing router and rank-selection behavior, prefix key/salt semantics and shared-state lifetime before implementation.',
 'Current routing, least-loaded routing and a simple fixed hash at equal load; optimize only if baseline already fails to exploit useful locality.',
 'Affinity-eligible requests, decisions honored at final rank, cache-hit source, stale entries and bypass rate across both API workers.',
 'Avoided prefill tokens versus queue imbalance, lookup/locking overhead and routing-to-rank mismatch.',
 'Current routing already provides equivalent locality, all hits occur upstream, or hotspot/tail regressions outweigh saved compute.',
 'Tenant/cache isolation, stale state, cancellation, restarts, concurrent API workers and G04/G05 semantics.',
 'Prefix-heavy E1 and cache-heavy E2 plus cold/unique-prefix negative controls.',[V+'59468',V+'52464',V+'51199','https://arxiv.org/abs/2608.19677'])
add('H10','systems','h200-systems-004','Bounded coordinated prefill release',10,
 '#61834 coordinates prefill across DP ranks to reduce mixed-phase interference; its topology/workload results do not establish value on two local EP4 replicas.',
 'Use per-step coordination; the root extension compares an overdue-request escape rule with simple static scheduling controls.',
 'Aligned prefill could protect decode tails, but added waiting/communication may worsen TTFT and burst recovery.',
 'Inspect installed scheduler compatibility and exposed mixed-step interference; a per-step wall-clock check does not guarantee a hard waiting-time bound.',
 'Tuned existing scheduler, MBT and fixed prefill interval under the same budget before adaptive coordination.',
 'Mixed-phase opportunities, coordination holds/releases/escapes and actual oldest-request wait; capture every rank.',
 'Decode stalls versus coordination time, prefill debt, queue tails and synchronized burst behavior.',
 'No mixed-step interference, simple tuning matches it, starvation/liveness failure, or TTFT regressions beyond predeclared bounds.',
 'Fixed DP4/EP4 contract, idle/wake/cancel, no elastic/custom-scheduler assumptions, distributed agreement and bounded backlog.',
 'Mixed E1 and burst E2; held-out prefill lengths and sustained overload.',[V+'61834'])
add('H11','compute','H200-COMP-002','Humming per-token FP8 activation arm',11,
 '#59488 and #60600 distinguish per-token FP8 from unsupported or slow grouped-scale formats on installed Humming 0.1.16.',
 'At a validated fixed Humming GEMM path, change activation quantization to per-token FP8 and log the effective schema.',
 'Reduced activation traffic/arithmetic may outweigh quantization overhead while meeting an explicit quality tolerance.',
 'Require H01-compatible backend first; resolve named-format plumbing, W1/W2 scales, target/drafter inheritance and fallback.',
 'Same fixed Humming path in BF16; do not compare a bundled backend/precision change and attribute it to quantization.',
 'Requested versus effective FP8 calls, quantization sites, dtype/scale format and fallback counts.',
 'Quantization plus GEMM and memory time, acceptance/quality and KV capacity; backend changes are a confound.',
 'Silent fallback, incompatible schema, quality/sampler failure, or overhead/regressions erase gain.',
 'Scale/clipping extremes, numerical expert reference, graph replay and pinned generation-quality/tool fixtures.',
 'Low/high expert occupancy E1/E2 with held-out prompt/route distributions.',[V+'59488','https://github.com/vllm-project/vllm/issues/60600'])
add('H12','compute','H200-COMP-005','Native-MXFP4 SM90 MegaMoE adapter',12,
 'FlashInfer #6343 includes EP4 and native MXFP4, but benchmark model dimensions differ. #6517 repairs stale workspace and documents scale conversion; its H200 push tuning is EP8-only.',
 'Build a framework adapter for the native FP4 API, weight transformation, collective symmetric workspace and execution plans; #62603 is not that native-FP4 adapter.',
 'Fusing dispatch/expert computation/reduction may reduce communication and staging cost at eligible shapes, after accounting for packing and workspace.',
 'Check E384/H5120/I2304/top6,96 local experts, clamp10, weight byte order, scale ranges, group semantics and installed FlashInfer0.7.0 API. Alignment alone is insufficient.',
 'Current Marlin+AG/RS and qualified Humming at identical checkpoint/routing; do not combine backend gain with an EP8 topology change.',
 'Native FP4 plan calls / eligible MoE calls, actual selected plans and all-rank workspace usage.',
 'Include staging/packing/dispatch/combine, graph lifetime and HBM/KV loss; published kernel tables exclude some preparation.',
 'No exact-shape/clamp/layout support, stale hot-expert workspace, scale saturation, or workspace/precision cost removes service gain.',
 'Weight conversion versus FP32 reference, hot/empty experts, repeated launches/graphs, collective ordering, all-rank errors and quality.',
 'Exact-shape component matrix before E1/E2; held-out expert skew and token counts.', ['https://github.com/flashinfer-ai/flashinfer/pull/6343','https://github.com/flashinfer-ai/flashinfer/pull/6517',V+'62603'])
add('H13','cross-engine','h200-transfer-20261020-01','Fuse top-k with physical KV mapping',13,
 'SGLang #41561 replaces separate selection/page conversion work. Its microbenchmark compares a Torch chain and cannot establish a win over the current optimized vLLM selector.',
 'Fuse physical-slot mapping into a compatible selection kernel; this is a consumer-aware adaptation beyond selector-only H07.',
 'Removing intermediate IDs and launches may help only where consumers do not need raw logical IDs or a different ordering.',
 'Trace all consumers, native SM90 build, block64 mapping and raw-index requirements; inspect newest DeepSelect before custom work.',
 'H07 selector-only and the current optimized chain; preserve raw-index fallback where needed.',
 'Fused eligible consumers / all selector consumers; raw-index fallback and mapping launches avoided.',
 'Intermediate traffic, mapping launches and total indexer span at identical selected set.',
 'Raw IDs remain needed, baseline already fuses equivalent work, or layout/order/tie differences invalidate the comparison.',
 'Logical/physical equality, block boundaries, causal bounds, ordering, padded rows and live-input graph replay.',
 'Context/row matrix and E1/E2; held-out layouts and fallback consumers.', ['https://github.com/sgl-project/sglang/pull/41561',V+'59204'])
add('H14','cross-engine','h200-transfer-20261020-03','DeepEP activation then triple-buffer dispatch',14,
 'DeepEP #693 reports H100 direct-NVLink dispatch gains while combine is unchanged. Current startup uses AG/RS, so the patched DeepEP kernel is not the baseline path.',
 'First integrate a compatible fixed DeepEP backend; then independently compare the direct-dispatch triple-buffer patch against that DeepEP control.',
 'Pipelining hidden/scales/metadata loads may reduce exposed dispatch time on EP4, but communication may already be hidden or backend conversion may dominate.',
 'Pin adapter/API version, direct-NVLink eligibility, payload/scales, rank topology, shared-memory limit and workspace. Account for newer elastic API migration rather than mixing revisions.',
 'AG/RS versus unpatched DeepEP; then unpatched versus patched DeepEP with identical backend and payload.',
 'Direct-NVLink dispatch calls / eligible expert calls; actual warp/buffer policy, fallback and per-rank bytes.',
 'Dispatch, combine, GEMM overlap and full expert span; compare balanced and skewed routes.',
 'No compatible native adapter/path, no exposed dispatch, buffer-lifetime failure, or increased workspace removes goodput.',
 'Token identity, empty/hot experts, repeated graph replay, TMA buffer reuse, all-rank liveness and scales.',
 'EP4 component skew matrix then E1/E2; held-out traffic skew.', ['https://github.com/deepseek-ai/DeepEP/pull/693'])
add('H15','compute','H200-COMP-004','Opt-in mHC coefficient-stream overlap',15,
 'Installed source excludes SM90. #60768 provides dispatch-only CPU checks, not Hopper GPU validation; #60777 is a distinct compensated-BF16 draft path.',
 'Add a narrow opt-in Hopper overlap path only after qualifying TF32 correctness; retain serial control.',
 'Independent coefficient work may overlap other work, but stream/event/graph overhead or resource contention may eliminate benefit.',
 'Resolve executed JIT artifact and exact dependency schedule; qualify #448/#59129 if the affected path executes. Do not conflate TF32 overlap with compensated-BF16 math.',
 'Correctness-qualified serial TF32 and, separately, H03 launch tuning; compensated BF16 is a separate precision experiment.',
 'Overlapped opportunities / eligible mHC invocations, active streams/events and dependency waits.',
 'Exposed critical-path span with event overhead and contention, not just summed kernel durations.',
 'No independent exposed work, mock-only validation, graph/race/numerical failure or no service benefit.',
 'Independent mHC reference, repeatability/race checks, stream ordering, changing graph inputs and fallback.',
 'Small and large rows, D1/E1/E2; held-out graph modes.',[V+'60768',V+'60777','https://github.com/sgl-project/sglang/pull/39664'])
add('H16','cross-engine','h200-transfer-20261020-02','Matched SGLang control and isolated group32 tuning',16,
 'SGLang #41251 reports a multi-change H200 bundle under materially different engine/topology/precision settings. #40417 also supplies backend near-parity counterevidence.',
 'Build a matched engine control if parity is feasible, then isolate the relevant GEMM tuning within SGLang before considering transfer.',
 'A reproducible service gap could identify worthwhile components; it would not establish which bundled mechanism caused the gap.',
 'Match model/tokenizer revision, TP1/DP4/EP4, host Engram, FP8 KV, graph settings and real DSpark rejection semantics. Report any irreducible mismatch.',
 'Pinned vLLM versus pinned matched SGLang, followed by a single SGLang tuning change; do not call an unmatched recipe a kernel ablation.',
 'Backend/shape/format coverage, target/drafter semantic parity and exact workload completion.',
 'Per-component critical path plus service frontier, workload mix and per-engine overhead.',
 'Parity is unavailable, quality differs, only old-engine comparison establishes gain, or tuning is inactive for our geometry.',
 'Tokenizer/tool/reasoning encoding, stochastic sampling, quality, KV semantics and liveness across engines.',
 'Same E1/E2 input bytes/arrival schedule and held-out workload; engine comparison remains a separate lane.', ['https://github.com/sgl-project/sglang/pull/41251','https://github.com/sgl-project/sglang/issues/40417'])
add('H17','systems','h200-systems-005','Private-shard Engram allocation — inactive',17,
 'Late startup logs establish shared DP memory in both replicas. The generated card explicitly targets private tables; that premise is false for this control.',
 '#59849 exact-size private registration and #59923 packed shard exchange address different storage branches. #62359 shared cuMem is a different mechanism.',
 'No current-baseline improvement is predicted for the private branch. Retain the rejected card for lineage; reconsider only under an explicitly different storage configuration.',
 'Resolved dp_shared_memory=True is already established. Shared cuMem would require an independent FABRIC/export/NUMA capability probe and a new scoped card.',
 'Existing shared /dev/shm registration; do not disable sharing simply to create applicability.',
 'Private-path hits are expected zero on this configuration; configuration and branch evidence suffice to stop this card.',
 'No performance run for this card. For a separate shared-backing study, distinguish prefill lookup exposure from already-overlapped decode.',
 'Current scope is rejected as inactive. GB200 shared-cuMem gains and zero decode improvement do not predict H200 PCIe behavior.',
 'Any future shared-backing card needs collective allocation/import/failure cleanup and table-value correctness.',
 'No test planned against the current control.',[V+'59849',V+'59923',V+'62359'])
# Map immutable recovery descendants to original proposal IDs.
records={}
for lane in ['attention','systems','compute','cross-engine','prefill-mqa']:
 original=json.loads((R/lane/'hypotheses/propose-1.json').read_text())['hypotheses']
 folder=R/lane/('review-recovery' if lane in ['systems','compute','cross-engine'] else 'hypotheses')
 hist=json.loads((folder/'history.json').read_text())
 for c,h in zip(original,hist):records[(lane,c['id'])]=(h,folder)
records[('prefill-mqa','h200-contiguous-mqa-epilogue-001')]=(repaired,out)
experiments=R/'experiments';experiments.mkdir(exist_ok=True)
index=['# H200 mechanism cards','','Untested. Root research order is separate from frozen-policy model eligibility. Every card includes original model detail, root scope corrections and a falsification plan.','', '| Priority | Card | Latest selection | Score / 100 |','|---|---|---|---|']
ranking=['# H200 research priority','','This orders **conditional investigation**, not approved deployment or predicted speedup. No candidate has completed the required GPU correctness and activation checks. The frozen rubric remains unchanged; model deferrals are preserved. Start with the applicable G01–G05 and DeepGEMM correctness checks, then inspect H01–H03 eligibility.','','| Rank | Mechanism | First decision | Model selection / score |','|---|---|---|---|']
plans=[]
for d in D:
 h,folder=records[(d['lane'],d['original_id'])];card=h['card'];gate=h['assessment']
 d.update(global_id=h['global_id'],latest_card_id=card['id'],model_assessment=gate,model_artifact=str(folder.relative_to(R)),root_disposition='planned conditional diagnostic; prerequisites unresolved' if d['priority']<=8 else 'inactive on current baseline' if d['priority']==17 else 'defer implementation; retain conditional design')
 lines=['# '+d['key']+' — '+d['title'],'',f"Research priority: {d['priority']}. Root disposition: **{d['root_disposition']}**. Frozen-policy selection: **{gate['status']}**, score **{gate['score']}/100**. Scores are judgments, not speedups.",'',f"Original proposal: `{d['original_id']}`. Latest immutable identity: `{h['global_id']}`.",'']
 for label,key in [('Source observation','source_observation'),('Upstream fix','source_fix'),('Root transfer prediction (untested)','root_prediction'),('Baseline eligibility and cheapest first step','baseline_check'),('Strongest comparator','strongest_comparator'),('Activation denominator','activation'),('Mechanism and competing explanation','mechanism_diagnostic'),('Reject, stop or defer','reject_or_defer_if'),('Correctness scope','correctness'),('Workload and held-out conditions','workloads')]:lines+=['## '+label,'',d[key],'']
 lines+=['## Decision rules and cost','', 'Keep applicability, activation, correctness, mechanism, service value and integration verdicts separate. Missing telemetry or intervals wider than the decision margin are inconclusive; an inactive branch is not a disproved algorithm. Freeze adequate exposure and correctness tolerances before GPU work. Use the protocol’s provisional 2% service-improvement / 3% secondary-regression pilot guard only when explicitly chosen; production SLO and node price remain unset. A component gain alone does not qualify service promotion.','', 'Initial budget: at most two engineer-hours for source/build eligibility, then at most 20 minutes of component/activation GPU measurement if prerequisites pass. Stop on incompatibility or correctness failure. Any confirmation is a separate allocation: at least five paired full-run blocks plus held-out workloads, budgeted from their fixed durations. No automatic indefinite tuning or fleet-cost estimate. These are future test limits; no such work ran here.','', '## Model statement and experiment','',card['statement'],'']
 for k,v in card['experiment'].items():lines+=['**'+k.replace('_',' ').capitalize()+':** '+v,'']
 lines+=['## Critique retained','', '\n'.join('- '+x for x in (gate['reasons']+h['review'].get('objections',[]))) or 'No objections recorded.','', '**Required revision:** '+h['review'].get('required_revision',''),'', '## Primary sources','']
 lines+=['- ['+u.split('github.com/')[-1]+']('+u+')' for u in d['urls']]
 lines+=['', '[Evaluation protocol](../EVALUATION_PROTOCOL.md) · [Original model artifacts](../'+str(folder.relative_to(R))+'/history.json)']
 (experiments/(d['key']+'.md')).write_text('\n'.join(lines)+'\n')
 index.append(f"| {d['priority']} | [{d['key']}: {d['title']}]({d['key']}.md) | {gate['status']} | {gate['score']} |")
 ranking.append(f"| {d['priority']} | [{d['title']}](experiments/{d['key']}.md) | {d['baseline_check']} | {gate['status']} / {gate['score']} |")
 if d['priority']<=8:
  plan={'request_id':'h200-fresh-001-'+d['key'],'status':'planned_only','experiment':card['experiment'],'root_design':d,'protocol':str(R/'EVALUATION_PROTOCOL.md'),'execution_requires':'Fresh attestation and unresolved activation/correctness/build prerequisites; model deferral is not overridden.'}
  scope={'baseline_inventory_sha256':hashlib.sha256((R/'baseline/runtime-inventory.json').read_bytes()).hexdigest(),'evalset_contract_sha256':hashlib.sha256((R/'evalset-contract.json').read_bytes()).hexdigest(),'hardware':'8xH200 SM90','topology':'two TP1/DP4/EP4 replicas API2, seq64, MBT16384, DSpark k5 adaptiveOFF','workloads':d['workloads'],'meaning':'Conditional planned diagnostic, no test executed and no measured result'}
  plans.append(ledger.plan_test(h['global_id'],plan,scope,actor='root_research_planning'))
(experiments/'README.md').write_text('\n'.join(index)+'\n')
ranking+=['','## What is outside the first execution block','','H09–H16 retain useful designs but require routing, precision, native integration or engine-parity work. H17 is excluded on the pinned shared-memory baseline. Compensated-BF16 mHC, MISA head pruning, DeepJIT cold-start changes, sequence-parallel TP paths and small-head attention are not silently folded into the top eight. Their scope and counterevidence are in the repository/literature reviews.','','[Source research report](REPORT.md) · [Model decisions](MODEL_REVIEW.md) · [Evaluation contract](EVALUATION_PROTOCOL.md)']
(R/'RANKING.md').write_text('\n'.join(ranking)+'\n')
write_json(R/'root-review.json',{'at':now(),'actor':'root engineering synthesis','gpu_experiments':0,'candidates':D})
write_json(R/'planned-tests.json',plans)
with (R/'decision-ledger.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['key','priority','title','original_id','global_id','model_status','model_score','root_disposition','card']);w.writeheader()
 for d in D:w.writerow({**{k:d[k] for k in ['key','priority','title','original_id','global_id','root_disposition']},'model_status':d['model_assessment']['status'],'model_score':d['model_assessment']['score'],'card':'experiments/'+d['key']+'.md'})
write_json(R/'memory-export.json',{'stats':ledger.stats(),'hypotheses':[ledger.get(d['global_id']) for d in D],'scope':'Latest 17 mechanism records; prior originals and recovery lineage remain in persistent ledger and model artifacts.'})
print(json.dumps({'mechanisms':len(D),'planned_tests':len(plans),'latest_statuses':dict(Counter(d['model_assessment']['status'] for d in D))}))

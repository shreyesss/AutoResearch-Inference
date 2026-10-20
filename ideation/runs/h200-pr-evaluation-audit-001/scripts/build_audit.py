"""Reproducible H200 catalog dispositions and agent-authored experiment plans.
No model calls, GPU tests, service writes, or inferred empirical outcomes.
"""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'pr-evaluation-audit-001'
V='vllm-project/vllm'
experiments=[]
def add(id,title,refs,problem,change,gate,metrics,gap,limits,lane='main',parent=None):
    experiments.append(dict(id=id,title=title,refs=[(V,x) if isinstance(x,int) else x for x in refs],hypothesis=problem,arms=change,eligibility=gate,mechanism_metrics=metrics,evaluation_gap=gap,limitations=limits,lane=lane,parent_experiment=parent,status='planned_conditional',gpu_executed=False,outcome=None))
add('H01','Compare Humming with the observed Marlin MoE backend',[52318],
    'MXFP4 expert GEMMs currently dispatch to Marlin on this H200 host. A different Hopper GEMM implementation may reduce expert time at the same routing, weights and precision.',
    'A: observed auto-selected Marlin. B: explicit --moe-backend humming, BF16 activations unchanged. Freeze TP1/DP4/EP4, DSpark k5 and every scheduler setting. Confirm actual kernel dispatch; do not silently include #59488 or FP8 activations.',
    'Startup logs prove Marlin selection; Humming 0.1.16 is installed. Confirm that the pinned model route supports explicit Humming, expert shape 5120/2304 and current all-to-all prepare/finalize interface. Backend load and numerical fixtures precede any timed run.',
    'MoE GEMM and packing time per layer; EP collective time; tokens/expert distribution; HBM and available KV blocks; acceptance; qualified goodput and TTFT/ITL.',
    'E1 and E2 already exercise MoE. Add only upstream kernel/reference and fixed real-text quality fixtures because synthetic and Mooncake performance scoring cannot detect altered numerical semantics.',
    'PR is closed without merge; it motivates a backend A/B, not a blind cherry-pick. Author tests use an older DeepSeek V4 checkpoint/H20; headline gains are not a forecast for this host.')
add('H02','Use real request counts for DP draft graph dispatch',[58984],
    'Target graph capacity can be reused as the drafter request count. Idle or lightly loaded DP ranks then process padded draft rows instead of only live requests.',
    'A: pinned runtime. B: isolated #58984 equivalent after source-inclusion check. Preserve startup capture capacity and coherent dummy-rank metadata.',
    'DP4 and DSpark k5 are active. Inspect the installed DP sync/drafter implementation for equivalent logical counts; measure padded versus real rows before porting.',
    'Per-rank live/padded requests, dummy draft rows, draft graph bucket, draft GPU time and EP waits; acceptance and low-load/loaded ITL.',
    'Reuse E1/E2, emphasizing burst and rank imbalance. Add existing upstream DP/dummy tests and short rank-idle/cancel fixtures; no new load generator.',
    'Merged upstream does not establish inclusion in ac9126. Benefit requires actual padded dispatch. H20 source results are not H200 measurements.',parent='E02')
add('H03','Reduce CPU DP metadata collective cost',[61767],
    'Per-step CPU metadata synchronization may delay GPU dispatch even when the GPU collective itself is fast.',
    'A: existing CPU transport. B: isolated #61767 implementation, same participant groups, affinity and workload.',
    'DP4 is live. Identify actual transport and separate rank arrival skew from transport time; require CPU synchronization on the critical path.',
    'Collective wall time after last rank arrives; rank skew; CPU utilization; GPU idle gaps; p99 ITL/TTFT and goodput.',
    'E1/E2 suffice. Add CPU spans and upstream distributed stateful/stateless group tests, including orderly shutdown.',
    'Inherited primary review, not freshly downloaded here. Multi-node microbench gains cannot be transferred to two local four-rank groups.',parent='E04')
add('H04','Recover prefix reuse without corrupting draft context',[47926,62278,57110],
    'Prefix restoration and draft-group junction rules can either veto usable target hits or expose draft KV that was never written, lowering acceptance and increasing repeated prefill.',
    'Diagnose first. Compare A versus exactly one matching fix: restored-context masking (#47926), reachable sibling junction positions (#62278), or appropriate DSpark group handling (#57110). Never stack all three as the first arm.',
    'Record target/draft group IDs, cache-hit boundaries, actual final DP rank and acceptance on warm hits. Verify annotation ownership and existing equivalent fixes before selecting a patch.',
    'Token-weighted hits per KV group; computed prefill tokens; acceptance by draft position and hit length; TTFT; output/reference correctness.',
    'Existing E1 prefixes and Mooncake cache-heavy measure benefit. If existing samples miss exact sibling/unaligned-block boundaries, add small two-turn/sibling fixtures using the same client; this is the documented correctness coverage gap.',
    'A hit-rate increase alone is not success. Mooncake trace replay does not imply a MooncakeStore connector is installed.',parent='E11')
add('H05','Remove repeated scheduler/cache bookkeeping',[61724,51333],
    'Python scans of long null SWA block-table prefixes and repeated unchanged partial-prefix registration may consume scheduler time before GPU work can begin.',
    'A versus #61724; separately A versus #51333. Combine only individually confirmed fixes in a later integration arm.',
    'Verify live stack samples and absent equivalent implementation. #61724 needs long null heads; #51333 needs repeated same block/hash registration. Current seq64/rank is smaller than the source high-concurrency profile.',
    'Scheduler CPU samples and step time; scanned entries; repeated registration count; GPU idle gaps; long-context TTFT/ITL and qualified goodput.',
    'Reuse E1/E2; stratify existing long-context requests. Only add long synthetic lengths through the existing driver if the frozen trace lacks this cohort. Upstream release/promotion/preemption tests guard cache correctness.',
    'Low applicability at short contexts or GPU-bound high load; do not credit faster Python code as a frontier improvement.',parent='E12')
add('H06','Tune the Hopper mHC kernel at small token counts',[61461],
    'The fused mHC post/pre-norm split configuration was tuned on Blackwell. A Hopper-specific split can reduce repeated per-layer cost for 1–8 query tokens.',
    'A: existing tile configuration. B: #61461 SM90 specialization; all larger-token paths unchanged.',
    'Confirm the delayed mHC variant for hidden size5120 and actual per-rank query rows1–8. DSpark k5 at one active request can produce six rows, but DP padding must be observed.',
    'mHC kernel microseconds at rows1,2,6,8 and negative control16; per-rank shape histogram; low-load ITL and full-node qualified goodput.',
    'Use existing clients at total concurrency1/2/8, then normal E1/E2. Add upstream numerical tests because FP32 reduction order changes; no new benchmark service.',
    'Author reports H20 microbench gains and roughly1% low-load end-to-end gain; H200 unmeasured. Not a promise of capacity improvement.')
add('H07','Use indexed Humming GEMM with expert parallelism',[59488],
    'After Humming is selected, Hopper EP can use grouped GEMM even though the indexed implementation better matches DeepSeek V4.1 expert execution.',
    'Use correctness-qualified H01 Humming/BF16 control. B: indexed dispatch only, retaining BF16 activations. Separate later arm for supported per-token FP8 activation with its own quality gate.',
    'Requires Humming, SM90 V4.1 MXFP4 experts and no all2all kernels or allgather_reducescatter. Inspect actual prepare/finalize backend. If existing env override selects indexed, test that before source changes.',
    'Actual grouped/indexed dispatch; GEMM/packing/collective time; HBM; acceptance; numerical error and E1/E2 goodput.',
    'E1/E2 sufficient for performance. Upstream kernel checks and real-text quality are required for activation-format changes; they cannot be replaced by throughput tests.',
    'Conditional on H01; current backend is Marlin. Humming0.1.16 block-FP8 support conflicts with #61875; keep block-FP8 out of this arm.')
add('H08','Avoid full-context candidate-indexer decode work on Hopper',[62463,62000,61830],
    'Hopper can materialize scores over the entire compressed context before consuming only the selected candidate pool. Candidate-only FP8 paged scoring may cut memory traffic at very long context.',
    'A: dense Hopper decode indexer. B: #62463 direct paged-K candidate-only path, explicitly enabled. C: #62000 gather-based alternative as a separate arm. Keep candidate producer, prefill and top-k semantics fixed.',
    'Verify actual text-indexer backend and absence of candidate-only path. Model uses2048 candidate blocks ×8 positions =16384 compact columns; measure actual compressed context and candidate coverage. Require contexts where dense work exceeds useful pool.',
    'Scored columns and bytes; candidate gather/intermediate allocation; indexer GPU time; selected top-k agreement/ties; context-stratified ITL and goodput.',
    'E1 fixed8K cannot establish long-context benefit. Inspect frozen Mooncake length histogram first. If insufficient, use existing synthetic/AIPerf client at32K/128K/512K/1M feasible lengths, exact output lengths, matched cache states and explicit OOM reporting; no new harness.',
    'Both PRs are alternatives. H20 long-context claims do not establish H200 benefit; #62000 reports a single-request regression. Short-context correctness for #62463 is incomplete. No expected gain asserted for E1.',parent='E01')
add('H09','Enable Hopper length-aware candidate-block top-k',[59204,61039,('deepseek-ai/DeepSelect',14)],
    'Candidate-block selection may scan max-context-width scores even when live contexts are short. Valid block counts plus a Hopper-compatible selector can avoid the padded tail.',
    'A: current full-width selector. B: correctness-qualified SM90 DeepSelect build/integration. C: B plus #61039 valid-block selection; isolate extension replacement from length-awareness.',
    'Installed _has_deep_select is SM100-only; candidate_blocks still lacks valid_blocks. #59204 is draft; validate actual FP32 SM90 extension, not just the library BF16 benchmark. Check workspace/capture safety.',
    'Allocated versus valid block count; top-k time and memory traffic; FP32 top-k agreement/ties, out-of-range/NaN handling; E1/E2 goodput.',
    'Reuse E1/E2 plus upstream exact selector tests and graph-replay tests. Include short-context/large-max-context cases; fixed8K request is appropriate for padded-work diagnosis.',
    'Not a drop-in #61039-only H200 gain: its useful selector requires SM90 integration. PR59204 body is a template; patch source, not author speedup, supports the mechanism.',parent='E01')
add('H10','Improve CPU-offloaded Engram placement and allocation',[59849,59327],
    'CPU-offloaded Engram tables may waste pinned host capacity or suffer remote-NUMA reads and translation overhead. H200 host topology differs from GB200 coherent CPU/GPU systems.',
    'A: existing allocation and affinity. B: NUMA-local allocation/worker placement only. Separate C: exact registered allocation #59849. Separate D: measured H200 thresholds for sorting/inline lookups based on #59327, never copied GB200 thresholds.',
    'Engram offload and embedding_across_dp are on. Verify shared physical backing, per-group NUMA ownership, page size, actual host-memory path and existing allocation code. Do not duplicate shared tables blindly.',
    'Host RSS/PSS, locked bytes, NUMA locality, lookup latency by row count, PCIe traffic, CPU/GPU overlap and EP rank waits; prefill TTFT and goodput.',
    'E1/E2 already use Engram. Add read-only NUMA/host-memory counters and short Nsight diagnostic capture. Correct allocation lifetime/sharing tests precede runs.',
    '#59327 enables measured thresholds only on Blackwell; H200 adaptation is a new measured tuning task. #59849 evidence is GB10, not proof of H200 speedup.',parent='E10')
add('H11','Coordinate DP prefill to protect decode progress',[51199,61834],
    'A prefill-heavy rank can delay synchronized decode peers. Bounded cross-DP coordination may improve decode tails while risking prefill starvation.',
    'A: existing scheduler. B and C: separate #51199/#61834 proposals, only after protocol review. Train one bounded policy on discovery trace and freeze it for held-out windows.',
    'Observe mixed prefill/decode steps and peer waits first. Existing prefill interval controls must not overlap. All dummy, pause, cancellation and shutdown participants must remain synchronized.',
    'Per-rank backlog, oldest-prefill age, mixed-step time, accepted output tokens/step, collective wait, TTFT and ITL tails.',
    'Existing E1/E2 burst and cache-heavy suffice; add distributed protocol/deadlock fixtures, not a new load generator.',
    'Inherited primary review. A decode gain accompanied by TTFT starvation is rejected; source step counts must be translated to variable DSpark accepted tokens.',parent='E13')
add('H12','Preserve cache affinity at the final DP rank',[52464],
    'Endpoint/session affinity can be lost when API processes independently select internal DP ranks. A load-aware tie-break can recover warm prefix locality.',
    'A: existing endpoint router and internal selector. B: #52464 internal tie-break only. API1 is diagnostic, not the production comparator.',
    'Trace endpoint, API PID and final DP rank; verify current selector lacks equivalent tie-break and actual requests traverse it. Preserve cache salt/tenant boundaries and load priority.',
    'Final-rank affinity, token-weighted hits, queue skew, CPU routing overhead, TTFT tails and qualified goodput.',
    'Reuse E1 shared-prefix and E2 cache-heavy/burst, plus existing session client at low load. No new harness.',
    'Inherited H100 evidence showed only partial low-load recovery and flat/negative high-load results. Must not sacrifice load balance for hits.',parent='E14')
add('H13','Remove scheduler reservations for separate DSpark drafts',[59468],
    'Scheduler accounting can charge K−1 draft slots even though DSpark drafts outside the target batch, reducing usable target tokens when the token budget binds.',
    'A: current accounting. B: #59468, unchanged seq64, MBT16384 and k5. A later smaller-budget diagnostic is a separate config study.',
    'Confirm MRV2 route, missing change and counters showing token budget prevents otherwise feasible work. At seq64, k5, the live16384 budget may make this irrelevant.',
    'Scheduled target tokens versus charged tokens; budget-bound steps; active sequences; prefill/decode mix; E1/E2 goodput and tails.',
    'E1/E2 and upstream scheduler buffer-bound tests suffice. Do not lower MBT just to manufacture a production gain.',
    'Author result at MBT512 is not transferable to16384. Defer if live scheduler never binds.',parent='E07')
add('H14','Repair unreachable draft graph buckets only if observed',[62040],
    'Rounding target-derived capture sizes to draft query length can omit a full draft batch even when nominal graph capacity is sufficient.',
    'A: current manager. B: #62040 boundary clamp, unchanged cap512/seq64/k5. No blind cap increase.',
    'Inspect generated target and draft bucket sets and eager fallback counters. Here64×6=384 fits512; the earlier B200 seq128×6 argument does not apply. Prove a rounded missing bucket at actual shapes.',
    'Requested/selected graph sizes, eager fallback fraction, launch overhead, graph HBM/KV blocks and ITL.',
    'Reuse E1/E2 with graph counters and upstream boundary tests. No new load generator.',
    'Source example seq72 does not prove failure at64; classify no-op if all live buckets are reachable.',parent='E03')
add('H15','Bound draft attention only after context-dependent acceptance loss',[61261],
    'At long contexts, an unsuitable drafter context may increase draft time or reduce accepted tokens. A bounded draft window could improve useful tokens per engine step.',
    'A: fixed k5/full draft context. B: bounded draft_context_window selected on discovery data; keep adaptive verification off.',
    'Measure acceptance versus context while controlling cache-hit/restoration and workload domain. Inspect drafter training context and RoPE. Stop if no degradation or draft bottleneck.',
    'Acceptance by position/context, draft time, accepted tokens/step, ITL, real-text quality and goodput.',
    'Reuse existing long-context/session and Mooncake cohorts; add lengths through existing client only when missing. SPEEDBench/SpecBench supplies domain coverage if current synthetic/trace texts cannot represent draft acceptance.',
    'Kimi evidence does not establish DeepSeek gain. Short8K E1 likely misses the target mechanism.',parent='E17')
add('H16','Reduce Hopper contiguous MQA epilogue cost',[('deepseek-ai/DeepGEMM',452)],
    'The SM90 contiguous MQA logits epilogue may use a costlier reduction/clamp sequence than needed. A revised epilogue could reduce prefill indexer work.',
    'A: exact vendored DeepGEMM. B: #452 at the same build options, isolated from other library updates.',
    'Resolve actual vendored library/header commit and prove the changed contiguous kernel is called by this model. Paged decode is not changed.',
    'Contiguous MQA kernel time and launch shapes, prefill fraction, TTFT, indexer top-k agreement and output quality.',
    'E1/E2 prefill cohorts suffice for performance; upstream finite/edge numerical tests including overflow/NaN/ties are additional correctness coverage.',
    'Distribution-package absence does not mean vendored DeepGEMM is absent. Do not claim decode gain from a prefill-only change.')
add('X01','Explore Hopper mHC overlap only after synchronization qualification',[60768,59129,('deepseek-ai/DeepGEMM',448)],
    'Overlapping coefficient work with attention may shorten the critical path if H200 has spare concurrent resources.',
    'A: current no-overlap SM90 dispatch. B: opt-in #60768 only, after #59129/DeepGEMM448 equivalence is confirmed.',
    'Installed supports_mhc_overlap is SM100-only. SM90 port is draft; register-operand lifetime correctness must pass first.',
    'Nsight overlap timeline, occupancy, coefficient and attention time, EP waits, model quality and ITL.',
    'E1/E2 plus upstream synchronization/numerical fixtures; short diagnostic profile explains mechanism, unprofiled runs decide.',
    'CPU validation only in proposal; do not import SM100 fused-allreduce code. Integration experiment, not ready gain.',lane='exploratory')
add('X02','Evaluate a Hopper-native MXFP4 expert kernel route',[('deepseek-ai/DeepGEMM',473),62603,53709],
    'A native Hopper expert kernel could avoid Marlin/Humming overhead, but existing proposals use different expert layouts and precisions.',
    'First integrate and validate one MXFP4 route for hidden5120/intermediate2304/EP4. #62603 block-FP8 and #53709 weight conversion are separate alternatives, never interchangeable prerequisites.',
    'DeepGEMM473 evidence uses H20 EP8 and4096/2048; #62603 requires FlashInfer0.7.2 versus installed0.7.0.post1 and block-FP8 weights. Reject unsupported shape/layout before full-model runs.',
    'Expert kernel parity/time, packing and communication, weight/HBM expansion, KV capacity, quality and SLO goodput.',
    'Reuse E1/E2 only after kernel/reference and task-quality gates. Weight-conversion route requires capacity and precision evaluation that performance traces cannot provide.',
    'Not cherry-pick-ready. FP8 weights can nearly double expert-weight storage relative to MXFP4 and shrink KV headroom.',lane='exploratory',parent='E18')
add('X03','Evaluate KV offload as a separate cache-capacity configuration',[59096,59140,62041,47891,61375,61961],
    'A larger reusable KV working set could avoid recomputation under cache pressure if transfer cost is lower than repeated prefill.',
    'A: current GPU-only cache. B: one qualified offload connector with explicit dependency set and fixed host budget. Compare alternative restore paths independently.',
    'No KV offload tier is enabled in observed command. Prove cache pressure, compatible DSpark group ownership, save/restore lifetime and transport availability first.',
    'GPU versus host hit tokens; transfer bytes/latency; eviction/recompute; host memory; acceptance and TTFT tails.',
    'Existing cache-heavy replay tests benefit. Add eviction/restore, cancellation and stale-KV fixtures because ordinary warm traces do not prove connector correctness.',
    'Engram CPU offload is unrelated to KV offload. Mooncake workload does not itself activate a connector.',lane='exploratory',parent='E16')
add('T01','TP4 alternative: remove Marlin expert padding',[56697],
    'Pure TP4 shards expert width2304 to576; rounding to128 pads it to640, whereas64 alignment keeps576.',
    'Only in a separately qualified two-TP4 baseline, compare alignment128 versus64 for SM90 BF16 Marlin without A8.',
    'Current TP1/EP4 retains expert width2304, already divisible by128: no padding reduction in the requested live layout.',
    'Padded weight bytes, allocated HBM, KV blocks, expert kernel time and goodput.',
    'Same E1/E2 plus kernel/loading tests after a separate TP4 baseline. Do not attribute a topology change to the PR.',
    'Author H20 TP8 GiB savings do not apply to live TP1; held outside live ranking.',lane='different_topology')
add('T02','TP4 alternative: native small-head sparse attention',[61615,59418,57673,('vllm-project/FlashMLA',26)],
    'With64 attention heads, TP4 has16 local heads; padding to64 wastes work. Native16-head prefill/decode can avoid that work.',
    'Separate TP4 baseline: prefill #61615 plus required FlashMLA26; independently decode #59418; broader #57673 is an alternative backend, not a stacked first arm.',
    'Live TP1 has64 local heads: small-head gates do not apply. Decode eligibility also uses query rows, not client concurrency.',
    'Local head count, query rows, prefill/decode kernel time, temporary buffers, quality, TTFT/ITL and goodput.',
    'Reuse E1/E2 and low-query-row cases; add upstream attention numerical tests. Separate model/compiler/backend manifests per alternative.',
    'No direct live DP4 gain; dependency and head-padding absence checked in installed sources.',lane='different_topology')
add('T03','TP4 alternative: shard replicated fused prefill projection',[58872],
    'At sufficient prefill tokens, sharding replicated fused_wqa_wkv projection across TP ranks can outweigh an all-gather.',
    'Separate TP4 control versus #58872; measure a Hopper threshold before fixing it.',
    'TP1 cannot benefit from TP sharding. Requires custom AR availability and no SP/LoRA/ubatching/batch-invariant conflicts.',
    'Projection and all-gather time versus prefill rows; TTFT and mixed-load decode tails.',
    'E1/E2 prefill cohorts suffice; upstream collective/numerical tests required.',
    '2048-token H200 threshold is extrapolated from H20 and needs measurement.',lane='different_topology')
add('Q01','Qualify probabilistic block-verification sampling',[61161],
    'Reusing random draws across verification rounds can bias the generated distribution even when throughput looks normal.',
    'Check source inclusion; if missing, reproduce upstream tiny target/draft distribution test then apply #61161 before comparing speculative performance.',
    'Live DSpark uses probabilistic drafts and block rejection, so this semantic path is relevant. Confirm actual RNG implementation.',
    'Output marginals with confidence intervals, seed repeatability, request-order/batch-splitting behavior; no throughput win claimed.',
    'E1 temperature0 and throughput traces cannot detect stochastic distribution bias. Reuse upstream nonzero-temperature statistical fixtures and real-text quality checks.',
    'Correctness prerequisite, not a performance candidate.',lane='correctness_gate',parent='G01')
add('Q02','Qualify sparse-index tails and Hopper asynchronous operand lifetime',[62467,59129,('deepseek-ai/DeepGEMM',448)],
    'Vectorized top-k tail lanes or asynchronous WGMMA register lifetimes can expose invalid values and silently alter computation.',
    'Inspect each active kernel independently; apply only missing relevant fixes. Repeat graph and eager numerical tests with tail lengths and repeated calls.',
    'Top-k gate requires actual persistent kernel; WGMMA gate requires actual DeepGEMM mHC call. Resolve vendored source version instead of assuming every installed path uses these kernels.',
    'Reference output/indices, invalid reads, nondeterministic differences, repeated graph correctness; no perf score.',
    'Performance tests cannot prove memory safety. Upstream small shape/tail/replay fixtures and bounded sanitizer run are necessary additions.',
    'Do not carry Blackwell-only mega_mhc barriers into H200 automatically.',lane='correctness_gate',parent='G02')
add('Q03','Qualify API2 DP liveness and draft compile-cache identity',[59559,62062],
    'Multiple API processes can race DP wake-up; separately, improperly inherited draft replica indices can select another replica compile cache.',
    'A/B only when exact bug is present: idle/pause/resume API2 fixture for59559; cold/cached-start fixture for62062 after confirming independent-DP index semantics.',
    'API2 is active. #62062 evidence is dense independent DP; applicability to coordinated EP4 is not established and requires inspecting data_parallel_index.',
    'All-rank progress, timeout/hang count, restart success, draft cache paths and time-to-ready.',
    'Steady-state E1/E2 omit idle/restart transitions. Add small lifecycle fixtures; preserve live production services until a separate test deployment is available.',
    'Planned lifecycle tests, no service restart executed.',lane='correctness_gate',parent='G05')
add('Q04','Qualify actual tool-turn encoding and streamed arguments',[62199,62259],
    'Incorrect tool-turn boundaries or truncated DSML streaming can produce invalid model inputs/outputs while token throughput remains plausible.',
    'Golden tool conversations versus the intended checkpoint encoding; separate parser fixtures for truncated/closed streamed arguments, one patch at a time.',
    'Observed parser is deepseek_v41; checkpoint revision is pinned. Decide intentional encoding-version migration explicitly rather than silently changing workload tokens.',
    'Exact encoded token IDs, reference reasoning retention, JSON validity and streaming assembly.',
    'Synthetic and Mooncake text traces are not tool-role correctness suites. Reuse upstream golden fixtures; a new performance harness is unnecessary.',
    'Freeze any qualified encoder change in common A/B baseline because it changes input lengths.',lane='correctness_gate',parent='G04')

NEG={
 (V,60938):'Explicit Blackwell-only fusion despite TP1 matching; SM90 port and GPU validation absent. Do not rank for H200.',
 (V,61875):'Block-FP8 Humming activation proposal conflicts with 0.1.16 support described in59488; olderV4 evidence. Hold until version/format support resolved.',
 (V,60777):'BF16x3 primitive has no serving dispatch integration and no GPU qualification; not an immediately executable serving optimization.',
 (V,52795):'Adaptive verification is off; SM90 AV flatten fix becomes prerequisite only in a separately qualified AV-on lane.',
 (V,54011):'Hopper adaptive-verification failure report; use as prerequisite evidence if AV is enabled, not a current performance patch.',
 (V,54077):'Adaptive verification profiling path inactive in this baseline.',
 (V,56448):'Inspect DSpark profiling safety if dummy shapes overflow; current64*k5=320 is below MBT16384. No established live performance gain.',
 (V,52164):'SM90 native next_n=3 MTP path is distinct from the observed DSpark k5 method.',
 (V,53852):'TP all-reduce override does not optimize current TP1 layout; revisit only with TP>1.',
 (V,58684):'SM90 sparse attention backend targets GLM/V3-style route; V4.1 FlashMLA path compatibility unproven.',
 (V,61399):'Hardware keyword matches but generic FlashInfer sparse backend does not prove V4.1 path support.',
 (V,58540):'Earlier Hopper MegaMoE integration is superseded/removed in follow-up62603; evaluate actual layout dependency there.',
 ('deepseek-ai/FlashMLA',200):'656-byte GLM5.2/V3.2 cache format is not the V4.1 path; no direct compatible port.',
 ('deepseek-ai/DeepGEMM',350):'Tiny grouped-GEMM helper expected_k<=256 does not match expert hidden K5120; prove a matching invocation before reopening.',
 ('deepseek-ai/DeepGEMM',455):'Conditional small-M JIT alignment correctness; no actual failing H200 call established.',
 ('deepseek-ai/DeepGEMM',469):'Conditional overwrite correctness; inspect exact active shape/call before port.',
 ('deepseek-ai/DeepGEMM',477):'Conditional einsum accumulation fix; no actual affected serving call established.',
}

def dump(name,obj): (ROOT/name).write_text(json.dumps(obj,indent=2)+'\n')
def writecsv(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def main():
    old=json.loads((OLD/'experiments.json').read_text())
    oldc={(c.get('repo',V),int(c['number'])):c for e in old for c in e['candidates']}
    sources={}
    for p in (ROOT/'sources').glob('*__*.json'):
        d=json.loads(p.read_text())
        if d.get('document'):sources[(d['repo'],int(d['number']))]=(p,d)
    rank=0
    for e in experiments:
        if e['lane']=='main':rank+=1;e['performance_rank']=rank
        else:e['performance_rank']=None
        e['role']='correctness_gate' if e['lane']=='correctness_gate' else 'performance_hypothesis'
        e['families']=[e['title']];e['candidates']=[]
        for repo,n in e.pop('refs'):
            if (repo,n) in sources:
                p,s=sources[(repo,n)];d=s['document'];body=d.get('body') or ''
                # Short exact quote anchors provenance, not an automatic endorsement.
                lines=[x.strip() for x in body.splitlines() if x.strip() and not x.lstrip().startswith(('#','<!--','```'))]
                quote=' '.join((lines[0] if lines else d['title']).split()[:18])
                # Preserve exact whitespace when selecting a body substring.
                line=lines[0] if lines else ''
                if line:
                    spans=list(re.finditer(r'\S+',line));quote=line[:spans[min(17,len(spans)-1)].end()]
                c=dict(repo=repo,number=n,url=d['html_url'],title=d['title'],source_quote=quote,source_snapshot=str(p.relative_to(ROOT)),source_body_sha256=s.get('body_sha256'),head_sha=(d.get('head') or {}).get('sha'),merged_at=d.get('merged_at'),state=d.get('state'),draft=d.get('draft'),review_depth='current_primary_metadata_and_selected_diff' if 'files' in s else 'current_primary_body',files_complete=s.get('files_complete'))
            else:
                c=dict(oldc[(repo,n)])
                c['source_quote']=c.get('source_quote',c.get('source_basis',{}).get('quote',''))
                c['source_snapshot']='../pr-evaluation-audit-001/'+c.get('review_file','')
                c['review_depth']='inherited_primary_review_reassessed_for_h200'
            c['gate']=e['eligibility'];e['candidates'].append(c)
        e['existing_loads']='E1: native agent-f75; E2: frozen Mooncake median/burst/cache-heavy. H200 capacity discovery and held-out confirmation in PROTOCOL.md.'
        e['baseline_inclusion']='Runtime image and launch observed; per-patch membership must be demonstrated from installed source. Specific absence evidence in BASELINE.md.'
    dump('experiments.json',experiments)
    override={}
    for e in experiments:
        for c in e['candidates']:override.setdefault((c['repo'],int(c['number'])),[]).append(e)
    rows=list(csv.DictReader((OLD/'PR_DISPOSITIONS.csv').open()))
    output=[]
    for original in rows:
        r={k:v for k,v in original.items() if k not in ['experiment_id','experiment_document','performance_rank','priority_lane','reason','rule','disposition','evaluation_route','review_depth','baseline_inclusion']}
        r.update(previous_disposition=original['disposition'],previous_experiment_id=original['experiment_id'],previous_review_depth=original['review_depth'])
        key=(r['repo'],int(r['number'])); txt=' '.join(r.get(x,'') for x in ['title','affects_us','action','catalog_reason']).lower()
        r.update(experiment_id='',experiment_document='',performance_rank='',baseline_inclusion='unknown_unless_explicit_runtime_source_evidence',review_depth='catalog_rules_not_primary_validation')
        if key in override:
            es=override[key];r.update(disposition='planned_'+es[0]['lane'],reason=' | '.join(e['eligibility'] for e in es),experiment_id=';'.join(e['id'] for e in es),experiment_document=';'.join('experiments/'+e['id']+'.md' for e in es),performance_rank=min([e['performance_rank'] for e in es if e['performance_rank']] or ['']),review_depth=next(c['review_depth'] for e in es for c in e['candidates'] if (c['repo'],int(c['number']))==key),rule='explicit_h200_mechanism_review')
        elif key in NEG:
            r.update(disposition='reviewed_hold_or_inactive',reason=NEG[key],review_depth='current_primary_review',rule='explicit_h200_negative_review')
        elif re.search(r'h200|h100|hopper|sm90',txt):
            r.update(disposition='deferred_hopper_source_review',reason='Hopper keyword rescue: previous B200 judgment is insufficient. Shape/model/path and primary implementation still need review; no automatic recommendation.',rule='hopper_rescue')
        elif original['experiment_id']:
            r.update(disposition='deferred_previous_candidate_path_check',reason='Previous B200 family assignment (often only a review destination); no H200 active-path qualification established in this audit. Preserve evidence and reconsider if profiling identifies this mechanism.',rule='previous_candidate_not_silently_transferred')
        elif re.search(r'blackwell|sm100|sm103|b200|b300|gb200|gb300',txt):
            r.update(disposition='deferred_hardware_path_check',reason='Hardware-tagged catalog evidence requires architecture/path inspection. A Blackwell mention alone does not prove exclusion of generic logic.',rule='hardware_claim_needs_proof')
        elif original['disposition'].startswith(('exclude','catalog_excl','reviewed_excl')) or ('no:' in r.get('affects_us','').lower()):
            r.update(disposition='catalog_low_relevance_unverified',reason='Original catalog negative relevance retained only as triage: '+original['reason'],rule='catalog_negative_not_primary_proof')
        else:
            r.update(disposition='deferred_source_review',reason='No source-validated H200 mechanism selected. Retain for targeted retrieval; not a semantic rejection or evidence of no benefit.',rule='unresolved')
        output.append(r)
    assert len(output)==5532 and len({r['identity'] for r in output})==5532
    assert {r['identity'] for r in output}=={r['identity'] for r in rows}
    writecsv('PR_DISPOSITIONS.csv',output)
    ranked=[]
    for e in experiments:
        for c in e['candidates']:
            ranked.append(dict(rank=e['performance_rank'] or '',experiment=e['id'],lane=e['lane'],repo=c['repo'],number=c['number'],url=c['url'],title=c['title'],mechanism=e['hypothesis'],eligibility=e['eligibility'],limitations=e['limitations'],source_snapshot=c['source_snapshot'],head_sha=c.get('head_sha',''),review_depth=c['review_depth']))
    writecsv('RANKED_PRS.csv',ranked)
    writecsv('REVIEWED_HOLDS.csv',[dict(repo=k[0],number=k[1],reason=v,url=(sources[k][1]['document']['html_url'] if k in sources else 'https://github.com/'+k[0]+'/pull/'+str(k[1]))) for k,v in NEG.items()])
    fetched=[s for p,s in sources.values()]
    coverage=dict(input_rows=len(output),unique_identities=len({r['identity'] for r in output}),input_sha256=hashlib.sha256((OLD/'inputs/vllm-dsv41-dspark-items.csv').read_bytes()).hexdigest(),dispositions=dict(Counter(r['disposition'] for r in output)),plans=len(experiments),lanes=dict(Counter(e['lane'] for e in experiments)),fresh_primary_snapshots=len(fetched),diff_snapshots=sum('files' in s for s in fetched),incomplete_diff_snapshots=sum('files' in s and not s.get('files_complete') for s in fetched),planned_unique_sources=len(override),planned_sources_in_catalog=sum(k in {(r['repo'],int(r['number'])) for r in rows} for k in override),gpu_tests_started=0,performance_results=0,scope='All catalog rows mechanically reclassified; only explicit overrides reviewed as hypotheses. Deferred means unresolved, not rejected.')
    dump('coverage.json',coverage)
    out=ROOT/'experiments';out.mkdir(exist_ok=True)
    for e in experiments:
        text=f"# {e['id']} — {e['title']}\n\nLane: **{e['lane']}**. Live-layout priority: **{e['performance_rank'] or 'not ranked'}**. Status: conditional plan; no GPU test or measured gain.\n\n## Problem and causal hypothesis\n\n{e['hypothesis']}\n\n## Applicability to our H200 deployment\n\n{e['eligibility']}\n\n## Isolated control and treatment\n\n{e['arms']}\n\n## Evaluation and predicted mechanism\n\n{e['existing_loads']}\n\nMeasure: {e['mechanism_metrics']}\n\n## Why an additional evaluation is or is not needed\n\n{e['evaluation_gap']}\n\n## Decision and falsification\n\nApply [the preregistered protocol](../PROTOCOL.md). Confirm path and missing behavior before spending GPU time. Support requires correctness, predicted mechanism movement and a useful held-out SLO outcome. Reject an active, well-measured change with no useful endpoint gain or a correctness/tail regression. Mark absent-path, underpowered or failed-replay cases inapplicable/inconclusive; do not label them disproven. Correctness lanes establish only scoped correctness.\n\n## Evidence limits\n\n{e['limitations']}\n\n## Sources\n\n"
        for c in e['candidates']:
            text+=f"- [{c['repo']}#{c['number']}: {c['title']}]({c['url']}) — {c['review_depth']}; snapshot `{c['source_snapshot']}`; head `{c.get('head_sha') or 'see snapshot'}`.\n"
        if e['parent_experiment']:text+=f"\nDerived from [B200 {e['parent_experiment']}](../../pr-evaluation-audit-001/experiments/{e['parent_experiment']}.md), with H200 eligibility and evaluation changes above.\n"
        (out/(e['id']+'.md')).write_text(text)
    index='# H200 experiment index\n\nTarget confirmed by user: live217.18.55.219, two TP1/DP4/EP4 groups, DSpark k5. Priority is an engineering test order, not a measured gain estimate.\n\n| Order | Plan | Lane | First gate |\n|---|---|---|---|\n'
    for e in experiments:index+=f"| {e['performance_rank'] or '—'} | [{e['id']} — {e['title']}](experiments/{e['id']}.md) | {e['lane']} | {e['eligibility'].replace('|','/')} |\n"
    (ROOT/'EXPERIMENT_INDEX.md').write_text(index)
    print(json.dumps(coverage,indent=2))
if __name__=='__main__':main()

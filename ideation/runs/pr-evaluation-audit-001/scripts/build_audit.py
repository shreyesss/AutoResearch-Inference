"""Rebuild the catalog disposition ledger and experiment documents from frozen inputs.

Rules provide conservative triage, NOT 5,532 independent semantic reviews.
Selected source reviews override rules. No network, serving or GPU actions.
"""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write_json(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

# IDs are stable across the CSV, experiment documents and hypothesis memory.
# Each arm below is evaluated separately, never an un-attributable patch bundle.
SPECS = [
 ('E01','Length-aware decode indexer',1,'length_aware_indexer','Limit index selection to each live context instead of the configured maximum.','A: unchanged; B: length-aware selection only; C: precision ablation only on an older compatible API with a separable dtype leg; #61149 already makes SM100 logits BF16 and removes logits_dtype, so omit C there.','E1 8K/1K c256/384/512; E2 all windows; existing text-grid 32K/128K as sensitivity.','Indexer GPU time, scored rows, TPOT, qualified goodput.','No new performance evaluation; kernel reference checks are required if logits precision changes.'),
 ('E02','Remove unnecessary DSpark drafter padding',2,'draft-padding','Logical DP request counts avoid work on target graph padding.','A: current padding; B: #58984 with k5 and adaptive verification OFF in both.','E1 c256/384/512 and ragged arrival parameters; E2 burst/median.','Per-rank logical requests, target graph capacity, draft rows, draft GPU time, acceptance and goodput.','Reuse E1/E2; add counters. If padding never leaks in this configuration, stop before benchmarking.'),
 ('E03','Make full decode graph buckets reachable',3,'graph-reachability,graph_capture_floor','Correct target/draft bucket arithmetic and capture limits can reduce eager fallback at occupied ranks.','A: cap512; B: config-only reachable k5 buckets up to768/1024; C: #62040 at same B buckets. Do not change k simultaneously.','E1 occupancy around observed graph boundaries, then full c sweep; E2 ragged bursts.','Actual scheduled tokens and graph mode per rank, padding, graph pool HBM, TPOT and goodput.','Reuse workload parameters and add dispatch counters. 128*(5+1)=768 is a capacity bound, not proof of occupancy. InferenceX3095 floor64 is a separate low-load diagnostic.'),
 ('E04','Lower CPU DP metadata collective overhead',4,'dp-metadata','Shorter CPU metadata synchronization may bring forward GPU dispatch.','A: existing transport; B: reviewed #61767 transport. #60267 is provenance/superseded, not a second patch.','E1 c256/384/512 and low-load control; E2 median/burst.','DP metadata wall time with arrival skew separated, CPU utilization, GPU idle gaps, p99 TTFT/ITL, goodput.','Reuse E1/E2 and CPU spans; vendor DP16 multi-node result does not predict two DP4 groups on one node.'),
 ('E05','Compile relevant MegaMoE shapes before readiness',5,'jit_readiness,runtime_prefill_jit','Moving first-use JIT before readiness reduces first-request stalls, at a possible boot-time cost.','A/B clean isolated compile-cache directories; repeat A/B with retained identical caches; fixed first-request shape sequence.','Reuse E1 requests at first launch and E2 after ready; existing readiness/log collection.','Process start→ready, start→first SLO-qualified request, cold TTFT, JIT events, subsequent warm goodput.','Warm E1/E2 omit startup. Add a lifecycle timestamp/cache-state wrapper, not a new request generator. Do not delete shared caches.'),
 ('E06','Select an appropriate top-k implementation',6,'topk_backend,producer_assisted_topk','DeepSelect may avoid inefficient persistent-topk dispatch for actual verification batch shapes.','A: actual baseline backend; B: #60802 routing at unchanged numerical mode. C: #59922 producer-assisted TopK separately with #59921 and vllm-project/DeepGEMM #24/#25 dependencies; require BF16 top512/H32/D128/page128/n1..6. Include short-context n6 as a negative-control shape; do not replace the default everywhere.','E1 c sweep and longer existing shape grid; E2 all windows.','Backend dispatch counts, top-k GPU time, selected-index correctness, TPOT and goodput.','Reuse E1/E2; source numerical/reference checks for selected indices, no new load harness.'),
 ('E07','Recover scheduler budget reserved for parallel drafts',7,'scheduler-budget','Unneeded K-1 target reservations may constrain prefill admission.','A: current accounting; B: #59468, fixed k5; first compare at actual MBT16384, then separately 8192/4096 only if justified.','E1 mixed prefill/decode and E2 burst with identical arrivals.','Admitted tokens, unused token budget, queue oldest age, TTFT/ITL tails and qualified capacity.','Reuse E1/E2; little benefit is expected if the budget does not bind. Smaller-budget gains are a separate configuration result.'),
 ('E08','Avoid repeated activation repacking',8,'packed_activation_chain,redundant_cast','Keep compatible packed activations across the affected compute chain; remove separately measured cast overhead.','A: unchanged; B: #57977 dependency-qualified packed chain; C: #61971 separately, not bundled.','E1 and E2; profile only a separate diagnostic pass.','Quantization/repack bytes and kernels, GPU duration, numerical parity, TPOT and goodput.','Reuse E1/E2 plus upstream numerical checks; changes in quantization require a held-out quality guard.'),
 ('E09','Use the B200-specific FlashMLA pipeline',9,'fused_attention_pipeline','A compatible SM100 148-SM/H64 decode or prefill kernel may reduce attention latency.','A: pinned FlashMLA; B: #227 port with #229 layout reconciled, restricted to eligible BF16-KV prefill OR all-FP8-KV decode, H64/QNorm-off/148SM (source tested TopK640). Mixed-FP4 decode falls back; measure actual engagement under compressed NVFP4 MegaAttention.','E1 actual-shape dispatch then E2; reject unsupported mixed-FP4 shapes before capacity tests.','Eligible call fraction, attention GPU time, numerical error, KV capacity and qualified goodput.','Reuse E1/E2; upstream kernel shape/reference tests first. Report whole-server gain, not vendor kernel speedup.'),
 ('E10','Share and place host Engram backing correctly',10,'engram_host_backing,engram_allocator,engram_host_lookup,packed_engram_dp','Avoid redundant host table registration or improve locality when the B200 host supports the allocation path.','A: resolved current storage mode, recording dp_shared_memory/use_thp/embedding_across_dp. B: #59849 if pinned-table registration engages. C: #62359 only for DP-shared backing with FABRIC/host support. D: #59327 only if missing or policy retuning is justified. E: #59923 only TP1 DP-sharded tables with dp_shared_memory=false, supported WKV and CPU-offload peer path; this is a different branch from C. Separate arms.','E1 prefill and E2 cache-heavy/burst; same CPU binding and NUMA policy.','Host RSS/locked bytes, table duplication, NUMA traffic, Engram GPU stalls, TTFT and goodput.','Reuse E1/E2 plus host counters. GB200 host topology and decode gains cannot be assumed on x86 B200.'),
 ('E11','Fix observed DSpark prefix-hit loss',11,'prefix-correctness','Correct draft-group/junction handling may restore usable prefix hits without stale state.','Diagnose group-level misses first; evaluate one of #47926/#62278/#57110 at a time; #61455/#62206 annotations are alternatives. #48459 guards v4, so requires deliberate v4.1 adaptation.','E1 existing prefix fractions and session load; E2 cache-heavy; compare cold vs warm prefixes.','Measured local hit tokens per group and turn, recomputed prefill tokens, acceptance, correctness and goodput.','Reuse existing loaders plus hit-source instrumentation. Actual tool-role correctness uses G04 fixture; session driver alone is insufficient.'),
 ('E12','Reduce scheduler CPU cost only where observed',12,'scheduler-cpu,prefix-bookkeeping,prefix_cpu_bookkeeping','Avoid repeated prefix bookkeeping or long-prompt admission work when it consumes meaningful scheduler time.','A: baseline; B: #61724 only after hotspot reproduction; separate #51333 adaptation if its partial-tail path is active.','E1 high occupancy and long-context shape variant; E2 median/cache-heavy.','Scheduler spans, cache registration counts, GPU idle, allocation correctness and goodput.','Reuse E1/E2. A CPU microbenchmark improvement with unchanged serving goodput does not support a Pareto claim.'),
 ('E13','Coordinate prefill across DP ranks',13,'prefill-coordination,cross_dp_prefill_alignment','Bounded prefill synchronization may protect decode steps from rank-asymmetric prefill stalls.','A: existing schedule; B: #61834 opt-in; C: #51199 alternative, never both. Keep max wait bounded and record interaction with prefill interval.','E1 mixed shape and E2 burst/median at matched arrival speedups.','Mixed-step rate, prefill wait, starvation, new CPU collective cost, p99 TTFT/ITL and qualified capacity.','Existing evaluations suffice; add per-rank prefill decisions. Simulation-only evidence does not establish B200 benefit.'),
 ('E14','Preserve prefix locality at the final DP rank',14,'rank-affinity,prefix_affinity','A load-aware internal DP tie-break may preserve cache locality beyond existing endpoint hashing.','A: existing bounded endpoint/session router; B: #52464 or narrow equivalent at actual internal DP routing only.','E1 shared-prefix workloads and E2 cache-heavy/burst; identical endpoint router settings.','Endpoint and final-rank IDs, cache hits, queued work skew, TTFT tails and goodput.','Reuse E1/E2 plus routing trace. Stop if routing bypasses the modified internal selector or equivalent affinity already exists.'),
 ('E15','Fuse eligible Engram/mHC work at TP1',15,'engram_mhc_fusion','A shape-compatible fusion may remove launches and memory movement on the TP1 path.','A: current kernels; B: #60938 prototype restricted to verified TP1/model shapes.','E1 and E2 after kernel numerical equivalence and graph replay tests.','Launch count, moved bytes, kernel time, correctness and qualified goodput.','Existing performance evaluations suffice; upstream numerical/replay checks are required for fused math.'),
 ('E16','Activate KV offload only as a separate configuration lane',16,'kv-offload','External reuse may reduce recompute when HBM misses dominate enough to repay transfer cost.','A: current no-tier profile; B: explicit connector/tier profile with prerequisite #59096/#59140/#62041 checked; then test #47891/#61375/#61961 separately.','E1 reuse/working-set sweeps and E2 cache-heavy plus burst.','External vs local hit tokens, DMA time/bytes, recompute avoided, cancellation failures, HBM use and goodput.','E1/E2 plus existing cancellation_probe suffice. Mooncake workload does not imply Mooncake connector enabled; this is not a current-path patch.'),
 ('E17','Limit drafter context only if long-context degradation appears',17,'draft-context,adaptive-calibration','A bounded draft context or corrected adaptive statistics might reduce wasted speculation at long context.','A: fixed k5/full draft context; B: #61261 only after degradation seen; C: adaptive verification as an independent arm after G01/G02.','Existing long-context/session variants; E2 long-context cohorts.','Acceptance and accepted tokens/step by context, draft time, TTFT/ITL, quality and goodput.','Reuse load generators; k5 adaptive-off baseline gets no direct benefit from adaptive-only #54077. Kimi evidence is not DeepSeek evidence.'),
 ('E18','Evaluate alternative precision/layout/kernel routes',18,'fp8_indexer_sparse,generated_kernel_catalog,weight_packet_layout,weight_cache_policy,indexer_cleanup_schedule,flashmla_layout_upgrade,deepgemm_api_upgrade,tp2_host_engram,flashinfer_prefill_host_metadata,incremental_encoding','A separately isolated backend or layout may improve the frontier but can sacrifice KV capacity or quality.','One dependency/layout/precision/topology arm at a time. #61149/#61371 are dependency baselines, not free bundled optimizations; FlashInfer5523 requires actual integration.','E1 and E2 after exact model shape, route, precision and topology eligibility; same eight-GPU cost.','KV bytes/token, admitted concurrency, model numerical/quality scores, memory traffic, tails and goodput.','Existing performance evaluations suffice. Precision changes require held-out quality evaluation; source tests alone do not prove task quality. No checkpoint change in a serving-only comparison.'),
 ('G01','Qualify speculative sampling semantics',0,'sampling-validity','Fresh random draws prevent repeated-round sampling bias.','Audit #61161 presence and exact block/probabilistic path; corrected sampler vs reference distributions.','Upstream categorical/reference sampler fixture plus existing E1/E2 for performance regression.','Expected distribution error across temperature/top-p/top-k, rejection rounds, batch partition/order; then latency.','Required correctness fixture: fixed-length performance records and GSM8K/NLL cannot establish equality of sampling distributions.'),
 ('G02','Qualify graph, SWA and sparse-index memory safety',0,'graph-safety,sparse_sentinel,topk_bounds','Correct dispatch and initialized indices prevent silent corruption under mixed or padded work.','Test #62535 vs #59986 as distinct dispatch/capability fixes; #61174 rows, #60767 SWA columns and #60613 sentinel each separately. #62467 only if its reachable shape gate passes.','E1 shrink/grow/short-prompt variants and E2 burst; upstream targeted numerical/index repros.','Graph descriptor, index bounds, NaN/cross-request corruption, eager/reference agreement, crashes and acceptance.','Reuse performance loads; narrow source regression assertions are needed because successful HTTP responses do not prove correct outputs.'),
 ('G03','Qualify persistent-kernel synchronization',0,'graph_epoch','Safe epochs/readiness prevent stale state when CUDA graphs replay changed inputs.','Inspect actual vendored DeepGEMM headers; test #478 mHC epoch and #451 MegaMoE readiness separately if absent.','Upstream changed-input/contention graph replay reproducer; E1/E2 after reference parity.','Changed-input output equality within declared dtype tolerances, replay failures and hangs, then kernel time.','Required kernel regression fixture: E1/E2 have no reference outputs to catch silent graph reuse errors. Reuse upstream reproducer, not a new benchmark harness.'),
 ('G04','Qualify actual tool-turn encoding and parser semantics',0,'agent-encoding,agent-parser','Reference-consistent tool turns prevent prompt/cache-key changes from masquerading as performance gains.','Pin tokenizer/reference; compare #62199 Python encoding and #62259 parser separately; checkpoint unchanged.','Reference assistant/tool-role fixtures with tool IDs and arguments, incremental vs full encoding; E1/E2 as regression only.','Token IDs, retained reasoning, valid tool schema/arguments, prefix keys and streaming/nonstreaming agreement.','Required narrow fixture: smoke does not assert tool arguments and session_loadgen removes tools and substitutes user text. Rebaseline changed prompt tokens explicitly.'),
 ('G05','Qualify idle/API2 liveness and restart state',0,'dp-api-liveness,restart-correctness','Coherent DP wave wake-ups and compilation identity prevent hangs or wrong restart state.','Audit #59559 API/engine protocol and #62062 draft DP compile identity separately.','First inspect E2 gaps; use an idle→burst schedule with existing generator only if gap insufficient; existing launcher restart.','All submitted requests including timeouts, per-rank heartbeats, start/stop logs, TTFT after idle, errors.','No new harness. Add a schedule fixture only if the current trace never exercises the necessary idle interval; add readiness timestamps for restart.'),
]

def main():
    rows = list(csv.DictReader((ROOT/'inputs/vllm-dsv41-dspark-items.csv').open()))
    md = (ROOT/'inputs/vllm-dsv41-dspark-issues-prs.md').read_text().splitlines()
    notes = defaultdict(list)
    for line_no,line in enumerate(md,1):
        if not line.startswith('|'): continue
        for repo,num in re.findall(r'https://github.com/([^/]+/[^/]+)/(?:issues|pull)/(\d+)',line):
            notes[(repo,num)].append({'line':line_no,'text':line})
    corpus={}
    cp=ROOT/'inputs/corpus-opening-records.jsonl'
    if cp.exists():
        for line in cp.read_text().splitlines():
            d=json.loads(line); corpus[d['id']]=d
    selected={}; excluded={}
    for folder in ['spec-candidates','kernel-candidates','root-candidates']:
        path=ROOT/folder/'candidates.json'
        if not path.exists(): continue
        d=json.loads(path.read_text())
        for c in d.get('candidates',[]):
            c=dict(c); c['review_file']=folder+'/candidates.json'
            if folder=='root-candidates' and c['number'] in [60779,58169]:
                excluded[(c['repo'],str(c['number']))]={'reason': c['gate']+' '+str(c.get('limitations',''))}
                continue
            selected[(c.get('repo','vllm-project/vllm'),str(c['number']))]=c
        for c in d.get('excluded_or_delegated',d.get('excluded_or_held',[])):
            excluded[(c.get('repo','vllm-project/vllm'),str(c['number']))]=c
    by_family={f:s[0] for s in SPECS for f in s[3].split(',')}
    experiments=[]
    for ident,title,rank,families,hypothesis,arms,loads,metrics,gap in SPECS:
        cs=[c for c in selected.values() if c.get('family',c.get('experiment_family')) in families.split(',')]
        ex=dict(id=ident,title=title,performance_rank=rank or None,role='correctness_gate' if ident.startswith('G') else 'performance_hypothesis',families=families.split(','),hypothesis=hypothesis,arms=arms,existing_loads=loads,mechanism_metrics=metrics,evaluation_gap=gap,candidates=cs,status='planned_conditional',gpu_executed=False,baseline_inclusion='Inspect actual image/source first; catalog v0.32 membership is not proof.')
        experiments.append(ex)
        lines=[f'# {ident}: {title}','',f'**Status:** planned, untested; {"correctness prerequisite, not a throughput claim" if ident.startswith("G") else "performance inspection rank " + str(rank)}.','', '## Hypothesis','',hypothesis,'','## Source-grounded change and eligibility','']
        for c in cs:
            source=c.get('source_basis',{})
            quote=c.get('source_quote',source.get('quote',''))
            lines += [f"- [{c.get('repo','vllm-project/vllm')}#{c['number']}]({c['url']}): {c.get('mechanism',c.get('rationale',''))}",f"  - Gate: {c.get('gate',c.get('first_inspection',''))}",f"  - Limits/dependencies: {c.get('dependencies_and_limits',c.get('b200_eligibility_and_dependencies',c.get('limitations','')))}",f"  - Evidence: “{quote}” See [{c['review_file']}](../{c['review_file']}) for snapshot, state and provenance."]
        if not cs: lines += ['- This family is a retained diagnostic plan; see the catalog-linked backlog. No individually verified patch is approved by this document.']
        lines += ['', '## Isolated arms','',arms,'','## Existing evaluation and mechanism measurement','',loads,'',metrics,'','## Why an evaluation addition is or is not needed','',gap,'','## Decision contract','', 'Follow [the common protocol](../PROTOCOL.md). First prove the relevant path is active and the delta is absent. A failed applicability check means **not applicable**, not an experiment failure. Keep raw requests and failures. Run the mechanism diagnostic separately from unprofiled capacity measurements.','', '**Support:** the predicted mechanism changes in the intended direction, correctness passes, and the preregistered objective improves with repeatable run-level evidence. A correctness gate supports only its scoped correctness claim.','', '**Reject for this scope:** triggered mechanism and adequate measurement precision, but no practical end-to-end benefit; or a reproducible correctness/SLO regression. Retain successful kernel-only results separately.','', '**Inconclusive:** inactive/unverified path, missing baseline identity, too few qualifying requests, noisy confidence interval, changing workload/cache state, replay degradation or insufficient coverage.','', '**Alternative explanation:** changed prompt tokens, graph memory/KV capacity, cache hit rates, output lengths, arrival pressure or dependency upgrades may cause the apparent gain. Hold them fixed or report the change as a separate arm.','', '**Held-out check:** confirm on the other existing workload and a held-out Mooncake window; do not tune and claim success on the same window alone.','', '**Execution:** use the verified command forms in [evaluation audit](../evaluation/EVALUATION_CAPABILITIES.md); substitute candidate digest and isolated arm/profile. No image, benchmark, fixture implementation or deployment has been run for this plan.','']
        (ROOT/'experiments'/f'{ident}.md').write_text('\n'.join(lines))
    # Explicit fallback maps retain potentially applicable mechanisms instead of
    # pretending title-only exclusions are definitive semantic findings.
    group_map={'spec-decode':'E17','kv-offload':'E16','cudagraph':'E03','dp-ep':'E04','perf-decode':'E01','perf-prefill':'E13','kernels':'E18','memory-kv':'E18','quant':'E18','engram':'E10','startup':'E05','api':'G04','crash':'G02','observability':'E12','config':'E03','blackwell':'E18'}
    ledger=[]
    for original in rows:
        r=dict(original); key=(r['repo'],r['number']); identity='github:'+':'.join(key)
        c=selected.get(key); n=notes.get(key,[])
        r.update(identity=identity,source_markdown_lines=';'.join(str(x['line']) for x in n),catalog_reason=' '.join(x['text'] for x in n[:2]),cached_opening_record=identity in corpus,opening_record_hash=corpus.get(identity,{}).get('content_hash',''),baseline_inclusion='unknown_actual_runtime',experiment_id='',review_depth=('fields_and_rules_only' if r['action']=='auto' else 'catalog_semantics_and_rules'),priority_lane='backlog',reason='',rule='',performance_rank='')
        if c:
            family=c.get('family',c.get('experiment_family')); eid=by_family.get(family)
            if not eid: raise ValueError('Unmapped reviewed candidate: '+str((key,family)))
            r.update(disposition='reviewed_conditional_experiment',experiment_id=eid,review_depth='primary_source_review',priority_lane='correctness_gate' if eid.startswith('G') else 'ranked_performance',reason=c.get('rationale',c.get('mechanism','')),rule='review_override',performance_rank=next(s[2] for s in SPECS if s[0]==eid) or '')
        elif key in excluded:
            r.update(disposition='reviewed_exclude_or_hold',reason=excluded[key]['reason'],rule='reviewed_negative_override',review_depth='primary_source_review')
        else:
            title=r['title'].lower(); a=r['action'].lower(); affects=r['affects_us'].lower()
            # Exclude only explicit title-scoped targets, retaining any stated
            # cross-platform applicability from the source classification.
            foreign = re.search(r'\b(rocm|amd|mi300|mi325|mi355|xpu|gaudi|tpu|ascend|riscv|risc-v)\b',title)
            othermodel = re.search(r'\b(qwen|qwen3|qwen4exp|glm|gemma|kimi|mamba|minimax|longcat|ovis|jamba|gpt-oss)',title)
            generic = re.search(r'\b(core|scheduler|generic|all models|shared|metadata|block table|prefix|dp)\b',title)
            if (foreign and not affects.startswith(('yes','maybe'))) or (r['group']=='platform-other' and a!='auto' and a.startswith('irrelevant')):
                r.update(disposition='exclude_current_hardware',reason='Explicit different-platform scope; no current SM100 path established. Original rationale: '+r['affects_us'],rule='explicit_platform')
            elif othermodel and not generic and not affects.startswith(('yes','maybe')):
                r.update(disposition='exclude_named_model_path',reason='Title-scoped other-model implementation; no shared serving mechanism established. Reopen if shared call path is demonstrated.',rule='explicit_other_model')
            elif a.startswith('irrelevant'):
                r.update(disposition='catalog_exclusion_retained',reason='Retained source catalog exclusion, not independently proven against runtime: '+(r['affects_us'] or r['action']),rule='source_catalog_negative')
            elif a=='auto':
                r.update(disposition='deferred_source_review',review_depth='fields_and_rules_only',experiment_id=group_map.get(r['group'],''),reason='Original auto item was not semantically classified. No direct eligibility decision from keyword/body presence; inspect changed code and shared backend before promoting. Family is a review destination, not an approved experiment.',rule='auto_uncertainty_preserved')
            elif a.startswith('already in'):
                r.update(disposition='verify_baseline_membership',experiment_id=group_map.get(r['group'],''),reason='Catalog inclusion refers to v0.32/B300. Check actual ac912 image or runtime fork for this behavior; do not discard as already implemented.',rule='release_membership_not_runtime')
            elif r['group']=='docs-recipes':
                r.update(disposition='reference_configuration',reason='Recipe/documentation is configuration provenance, not a source patch. Verify shapes and compare isolated flags using E1/E2.',experiment_id='E18',rule='recipe_not_patch')
            else:
                r.update(disposition='conditional_family_backlog',experiment_id=group_map.get(r['group'],''),reason='Catalog supplies potential relevance; current path and primary diff require review before adding an arm. '+r['affects_us']+'; '+r['action'],rule='catalog_positive_pending_runtime')
        if r['experiment_id']=='E16' and r['rule'] not in ['review_override']:
            hint=(r['title']+' '+r['affects_us']).lower()
            if 'prefix' in hint and not re.search(r'offload|connector|tier|transfer|disagg|nixl|mooncake|cpu.cache',hint):
                r['experiment_id']='E11'
        r['experiment_document']='experiments/'+r['experiment_id']+'.md' if r['experiment_id'] else ''
        r['evaluation_route']='See experiment; E1/E2 retained, additions require documented gap' if r['experiment_id'] else 'No experiment now; reopen on stated evidence'
        ledger.append(r)
    ledger.sort(key=lambda r:(0 if r['priority_lane']=='correctness_gate' else 1 if r['priority_lane']=='ranked_performance' else 2,int(r['performance_rank'] or 999),r['repo'],-int(r['number'])))
    with (ROOT/'PR_DISPOSITIONS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0])); w.writeheader(); w.writerows(ledger)
    with (ROOT/'RANKED_PRS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0])); w.writeheader(); w.writerows(r for r in ledger if r['rule']=='review_override')
    write_json('experiments.json',experiments)
    write_json('coverage.json',dict(input_rows=len(rows),unique_identities=len({r['identity'] for r in ledger}),cached_opening_records=len(corpus),original_auto=sum(r['action']=='auto' for r in rows),dispositions=dict(Counter(r['disposition'] for r in ledger)),review_depth=dict(Counter(r['review_depth'] for r in ledger)),reviewed_candidates=len(selected),reviewed_negative_items=len(excluded),experiment_plans=len(experiments),gpu_experiments_run=0))
    write_json('input-manifest.json',{p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in (ROOT/'inputs').iterdir() if p.is_file()})
    # Coverage and links are deliverable invariants, not performance tests.
    assert len(rows)==5532 and len({r['identity'] for r in ledger})==5532
    assert all(r['reason'] and r['rule'] for r in ledger)
    assert all(not r['experiment_document'] or (ROOT/r['experiment_document']).exists() for r in ledger)
    print(json.dumps(json.loads((ROOT/'coverage.json').read_text()),indent=2))

if __name__=='__main__': main()

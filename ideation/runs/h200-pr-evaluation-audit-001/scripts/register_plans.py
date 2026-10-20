"""Validate source quotes/cards, then persist untested H200 designs in existing memory."""
import hashlib, importlib.util, json, sqlite3
from pathlib import Path
import jsonschema
from ideation.hypotheses import CARD
from ideation.hypothesis_memory import HypothesisMemory
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'pr-evaluation-audit-001'
RUN='runs/h200-pr-evaluation-audit-001'
spec=importlib.util.spec_from_file_location('prior_register',OLD/'scripts/register_plans.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def main():
 found={}
 for folder in [ROOT/'sources']+[OLD/x for x in ['spec-candidates','kernel-candidates','root-candidates']]:
  for p in folder.rglob('*.json'):
   if p.name=='candidates.json':continue
   prior.walk(json.loads(p.read_text()),str(p),found)
 for line in (OLD/'inputs/corpus-opening-records.jsonl').open():prior.walk(json.loads(line),'prior corpus opening snapshot',found)
 parents={x['experiment_id']:x['hypothesis_id'] for x in json.loads((OLD/'memory-registration.json').read_text())}
 policy={'id':'h200-live-dp4-audit-2026-10-20','author':'calling agent; primary-source and runtime inspection','require_novelty':False,'objective':'Improve live eight-H200 SLO-qualified frontier','ranking':'Active path, repeated-work impact, primary evidence, isolation cost, correctness/tail/capacity risk; explicit engineering order, no invented percent forecasts.','required':['active eligible shape/backend','missing behavior','source grounding','correctness','existing evaluation or explicit gap'],'decision':'Conditional plans; no GPU experiment or empirical outcome.'}
 baseline={'host':'217.18.55.219','hardware':'8xH200','topology':'two TP1/DP4/EP4 groups','api_per_group':2,'max_num_seqs':64,'max_num_batched_tokens':16384,'graph_cap':512,'dspark_k':5,'adaptive_verification':False,'moe_backend_observed':'MARLIN','model':'deepseek-ai/DeepSeek-V4.1-Flash','model_revision':'2cba9e42aa026125f3ed06c6d98c1db82f7ca027','vllm_version':'0.30.1rc1.dev493+gac9126e58','image_digest':'sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c','launch_and_hardware_attested':True,'serving_readiness_attested':False,'workloads':['native agent-f75','Mooncake median/burst/cache-heavy'],'evidence':RUN+'/evaluation/runtime-inventory.json'}
 brief={'instructions':'Rerun systematic PR audit and hypothesis design for H200, rest unchanged. User explicitly selected observed DP4/EP4 rather than intended TP4. Novelty not required. No GPU execution.','baseline':baseline,'selection':{'require_novelty':False}}
 prepared=[]
 for ex in json.loads((ROOT/'experiments.json').read_text()):
  citations=[];sources=[]
  for c in ex['candidates']:
   ident='github:'+c['repo']+':'+str(c['number']);quote=c['source_quote']
   source=next((s for s in found.get(ident,[]) if quote and quote in s['body']),None)
   if c['repo']=='vllm-project/vllm' and c['number']==59204:
    snap=json.loads((ROOT/'sources/vllm-project__vllm__59204.json').read_text())
    f=next(f for f in snap['files'] if f['filename'].endswith('indexer_topk.py'))
    ident+=':diff:'+snap['document']['head']['sha'];quote='or current_platform.is_device_capability(90)'
    source={'id':ident,'url':c['url']+'/files','title':c['title']+' (pinned implementation diff)','body':f['patch'],'snapshot':c['source_snapshot'],'file':f['filename'],'head_sha':snap['document']['head']['sha']}
   if not source or quote not in source['body']:raise ValueError('Missing exact primary source '+ident)
   citations.append({'source_id':ident,'quote':quote,'relation':'supports'});sources.append(source)
  parent=[parents[ex['parent_experiment']]] if ex['parent_experiment'] else []
  contract={'control':'Attested live H200 launch, then common correctness-qualified C1; resolve source membership and readiness first.','treatment':ex['arms'],'metrics':ex['mechanism_metrics'],'supports_if':'Eligibility, correctness, predicted mechanism and held-out useful SLO outcome pass PROTOCOL.md. Correctness lanes establish only scoped correctness.','rejects_if':'Confirmed active mechanism with adequate measurement yields no practical benefit, or correctness/SLO regression.','inconclusive_if':'Absent/unknown path, unavailable integration, insufficient requests, noisy interval or replay invalidity.','held_out_condition':'Other existing workload and untuned Mooncake window; paired seeds/cache states.','correctness':ex['evaluation_gap'],'cost':'One diagnostic pair then >=5 paired confirmation blocks if justified. H200 node price unknown; normalized cost or explicit supplied price. No GPU spend incurred.'}
  card={'id':ex['id'],'parents':parent,'operation':'evolve' if parent else 'generate','statement':ex['hypothesis'],'observed_bottleneck':'Launch and selected source eligibility observed; runtime bottleneck unmeasured. '+ex['eligibility'],'mechanism':ex['hypothesis'],'proposed_change':ex['arms'],'code_surface':'; '.join(c['url'] for c in ex['candidates']),'applicability':ex['eligibility'],'predicted_direction':'Scoped correctness improvement' if ex['lane']=='correctness_gate' else 'Lower qualified serving cost or latency if active; no numerical gain forecast.','classification':'adaptation' if ex['lane'] in ['exploratory','different_topology'] else 'upstream_port','alternatives':[{'explanation':'Apparent improvement comes from cache, routing skew, precision, graph memory, logging, output lengths or a dependency change.','distinguishing_test':'Freeze manifest, isolate arms, match workload/cache state, inspect mechanism counters and confirm unprofiled held-out result.'}],'evidence':citations,'novelty':{'scientific':'Not required.','implementation':'Existing upstream implementation or explicit H200 adaptation.','workload':'Untested relative to observed H200 baseline.','nearest_prior_art':'; '.join(c['url'] for c in ex['candidates']),'specific_delta':ex['arms']},'prior_art_query':'Full5532-row catalog triage,73 refreshed primary snapshots,27 selected diffs, inherited generic reviews and cached keyword/date retrieval.','experiment':contract,'revision_reason':'H200 and actual live TP1/DP4/EP4 eligibility reassessment; not a fabricated hypothesis.run or benchmark result.'}
  jsonschema.validate(card,CARD);prepared.append((ex,card,sources,contract))
 # Entire batch is schema/quote validated before mutation. A receipt makes retries idempotent here.
 db=Path('data/hypotheses.sqlite');backup=ROOT/'memory-before.sqlite'
 if not backup.exists():
  with sqlite3.connect(db) as src,sqlite3.connect(backup) as dst:src.backup(dst)
 memory=HypothesisMemory(db);receipts=[]
 for ex,card,sources,contract in prepared:
  ident=memory.register(RUN,card,brief,policy,sources)
  memory.review(ident,{'status':'deferred','eligible_for_design':True,'reasons':[ex['eligibility'],'No GPU result; serving readiness and per-patch membership must pass.']},{'reviewer':'calling agent','decision':'Conditional H200 design','limitations':ex['limitations']},policy=policy,context={'sources':sources})
  plan=memory.plan_test(ident,{'request_id':RUN+':'+ex['id']+':v1','document':RUN+'/experiments/'+ex['id']+'.md','contract':contract,'existing_evaluation':ex['existing_loads'],'evaluation_gap':ex['evaluation_gap'],'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest()},baseline,actor='agent-h200-design-audit')
  receipts.append({'experiment_id':ex['id'],'hypothesis_id':ident,'test_id':plan['id'],'parents':card['parents'],'selection':'deferred','test_status':'planned','outcome':None})
 for name,value in [('memory-registration.json',receipts),('task-policy.json',policy),('task-brief.json',brief),('hypothesis-cards.json',[x[1] for x in prepared])]:
  (ROOT/name).write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps({'registered_plans':len(receipts),'parent_links':sum(bool(r['parents']) for r in receipts),'gpu_tests_started':0,'results_recorded':0,'schema_and_quote_validation':'passed'}))
if __name__=='__main__':main()

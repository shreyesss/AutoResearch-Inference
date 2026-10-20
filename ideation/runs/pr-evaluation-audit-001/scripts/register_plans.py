"""Register explicit agent-authored designs, not fabricated model-run or GPU results.

Run from ideation with its research venv after build_audit.py. Existing ledger API
provides immutable identities and retry-safe test IDs. No inference/network call.
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import jsonschema
from ideation.hypotheses import CARD
from ideation.hypothesis_memory import HypothesisMemory

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/pr-evaluation-audit-001'

def walk(value, location, found):
    if isinstance(value, dict):
        if isinstance(value.get('body'), str):
            url=value.get('html_url') or value.get('url','')
            m=re.search(r'github.com/([^/]+/[^/]+)/(?:pull|issues)/(\d+)',url)
            if m:
                ident='github:'+m[1]+':'+m[2]
                found.setdefault(ident,[]).append(dict(id=ident,url=url,body=value['body'],kind='pr',title=value.get('title',''),snapshot=location,body_sha256=hashlib.sha256(value['body'].encode()).hexdigest()))
        for x in value.values():
            if isinstance(x,(dict,list)): walk(x,location,found)
    elif isinstance(value,list):
        for x in value: walk(x,location,found)

def main():
    found={}
    for folder in ['spec-candidates','kernel-candidates','root-candidates']:
        for p in (ROOT/folder).rglob('*.json'):
            if p.name=='candidates.json': continue
            walk(json.loads(p.read_text()),str(p.relative_to(ROOT)),found)
    for line in (ROOT/'inputs/corpus-opening-records.jsonl').open():
        walk(json.loads(line),'inputs/corpus-opening-records.jsonl',found)
    experiments=json.loads((ROOT/'experiments.json').read_text())
    policy={'id':'pr-audit-2026-10-20','author':'calling agent with three specialist source reviews','require_novelty':False,'objective':'Improve existing eight-B200 SLO cost/throughput frontier','ranking':'Applicability, repeated-work impact, source evidence, isolation cost, correctness and tail risk; see PROTOCOL.md','required':['attested runtime and missing behavior','active eligible backend and shape','primary evidence','existing evaluation reuse or demonstrated gap'],'decision':'All designs deferred for execution until applicability gates pass; no inferred empirical outcomes.'}
    brief={'instructions':'Filter supplied PR catalog against actual eight-B200 serving workloads and propose isolated reproducible evaluations. Novelty is not required.','baseline':{'serving_repo_sha':'2e6fa287d90adf7318ad314de27aa2f595aac821','configured_vllm_sha':'ac9126e58aa7bbab1856ba6593ba4d5003fea516','runtime_attested':False,'hardware':'8xB200','model':'DeepSeek-V4.1-Flash; preserve actual pinned checkpoint','profile':'latency-2xdep4-sla + lat-seqs-128','workloads':['native agent-f75','Mooncake median/burst/cache-heavy']},'selection':{'require_novelty':False}}
    prepared=[]
    for ex in experiments:
        citations=[]; sources=[]
        for c in ex['candidates']:
            ident='github:'+c.get('repo','vllm-project/vllm')+':'+str(c['number'])
            quote=c.get('source_quote',c.get('source_basis',{}).get('quote',''))
            source=next((s for s in found.get(ident,[]) if quote and quote in s['body']),None)
            if not source: raise ValueError('Missing exact primary quote: '+ident)
            citations.append({'source_id':ident,'quote':quote,'relation':'supports'})
            sources.append(source)
        if not citations: raise ValueError('No sources: '+ex['id'])
        contract={'control':'Attested baseline, then correctness-qualified common control as described in PROTOCOL.md.','treatment':ex['arms'],'metrics':ex['mechanism_metrics']+' E1/E2 qualified goodput and existing tail SLOs.','supports_if':'Eligibility proven; predicted mechanism improves; relevant correctness passes; preregistered endpoint meets PROTOCOL.md confirmation rule. Correctness gates support only scoped correctness.','rejects_if':'Reproducible correctness/SLO regression, or active mechanism with adequate precision but no practically meaningful objective benefit.','inconclusive_if':'Runtime inclusion/path unknown, insufficient requests, noisy interval, changed workload, replay degradation or missing counters.','held_out_condition':'Other existing workload and untuned Mooncake window with matched seed/cache state.','correctness':ex['evaluation_gap'],'cost':'One discovery pair before full sweep; then >=5 paired confirmation blocks if promising. All8GPU node-cost scenario$36/hour; no actual spend incurred.'}
        card={'id':ex['id'],'parents':[],'operation':'generate','statement':ex['hypothesis'],'observed_bottleneck':'Source-reported mechanism; not measured in this audit. '+ex['mechanism_metrics'],'mechanism':ex['hypothesis'],'proposed_change':ex['arms'],'code_surface':'; '.join(c['url'] for c in ex['candidates']),'applicability':'; '.join(c.get('gate',c.get('first_inspection','')) for c in ex['candidates']),'predicted_direction':'Scoped correctness improvement' if ex['role']=='correctness_gate' else 'Lower qualified serving cost or latency if the stated mechanism is active. No numerical gain predicted.','classification':'upstream_port','alternatives':[{'explanation':'Apparent gain is caused by workload, cache, output-length, graph-HBM or dependency changes.','distinguishing_test':'Freeze manifests; isolate arms and compare mechanism counters with the unprofiled E1/E2 outcome.'}],'evidence':citations,'novelty':{'scientific':'Not required.','implementation':'Existing upstream implementation or adaptation.','workload':'Benefit relative to this serving baseline remains untested.','nearest_prior_art':'; '.join(c['url'] for c in ex['candidates']),'specific_delta':ex['arms']},'prior_art_query':'Supplied5532-row catalog and saved primary records; no novelty gate.','experiment':contract,'revision_reason':'New agent-authored source-grounded plan; not generated by hypothesis.run.'}
        jsonschema.validate(card,CARD)
        prepared.append((ex,card,sources,contract))
    # Validate every card and quote before first persistent mutation.
    db=Path('data/hypotheses.sqlite'); backup=ROOT/'archive/memory/memory-before.sqlite'
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db) as src, sqlite3.connect(backup) as dst: src.backup(dst)
    memory=HypothesisMemory(db); receipts=[]
    for ex,card,sources,contract in prepared:
        identity=memory.register(RUN,card,brief,policy,sources)
        memory.review(identity,{'status':'deferred','reasons':['Actual running image/source inclusion and active-path prerequisites require attestation.'], 'eligible_for_design':True},{'reviewer':'calling agent consolidating source specialists','decision':'Documented conditional design; not experimentally validated.'},policy=policy,context={'sources':sources})
        plan=memory.plan_test(identity,{'request_id':RUN+':'+ex['id']+':v1','document':RUN+'/experiments/'+ex['id']+'.md','contract':contract,'existing_evaluation':ex['existing_loads'],'evaluation_gap':ex['evaluation_gap'],'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest()},brief['baseline'],actor='agent-design-audit')
        receipts.append({'experiment_id':ex['id'],'hypothesis_id':identity,'test_id':plan['id'],'selection':'deferred','test_status':'planned','outcome':None})
    for name,value in [('memory-registration.json',receipts),('task-policy.json',policy),('hypothesis-cards.json',[x[1] for x in prepared])]:
        (ROOT/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'registered_plans':len(receipts),'gpu_tests_started':0,'results_recorded':0,'quote_and_schema_checks':'passed'}))

if __name__=='__main__': main()

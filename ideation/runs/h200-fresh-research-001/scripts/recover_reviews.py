"""Recover model reviews after oversized cross-repo context; preserve originals."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from ideation.evidence import quote_errors,write_json
from ideation.store import Store,now
from ideation.hypothesis_memory import HypothesisMemory
R=Path(__file__).resolve().parents[1]
s=Store(Path('data/corpus.sqlite'))
def document(id,title,body,path):
 s.put(dict(id=id,source='baseline-readonly',kind='code',url='file:'+str(path),title=title,body=body,metadata={'artifact':str(path),'captured_at':now(),'scope':'Read-only snapshot, no GPU execution'}))
 s.db.commit();return s.get(id)
checks=R/'baseline/patch-application-checks.json'
patchdoc=document('code:h200:port-checks','Patch application to disposable installed-source copies',checks.read_text(),checks)
p=R/'baseline/dispatch-log-excerpts.txt'
b='\n'.join(x for x in p.read_text().splitlines() if 'Resolved Engram configuration' in x)
engram=document('code:h200:resolved-engram','Both replicas resolve Engram shared DP storage',b+'\n'+(R/'baseline/replica1-dispatch.txt').read_text(),p)
p=R/'baseline/source/vllm/v1/worker/gpu/spec_decode/speculator.py'
b=p.read_text();start=b.index('    def _build_uniform_batch_dp_sync(');end=b.find('\n    def ',start+10)
draft=document('code:h200:draft-dp-sync','Installed uniform drafter DP synchronization',b[start:end if end>0 else None],p)
for lane in ['systems','compute','cross-engine']:
 request=json.loads((R/lane/'hypothesis-request.json').read_text())
 packet=json.loads(Path(request['packet']).read_text())
 additions=[patchdoc]+([engram,draft] if lane=='systems' else [])
 packet['sources']+=additions
 packet['enrichment_provenance']={'actor':'root engineering review','at':now(),'reason':'Supply late read-only baseline/port checks before recovering failed critic; not model-generated claims.'}
 if lane=='systems':
  packet['claims'].append(dict(id='ROOT-ENGRAM-1',source_id=engram['id'],quote='dp_shared_memory=True, use_thp=False',claim='Startup resolves shared DP storage in both H200 replicas; private-shard allocation/exchange optimizations are inactive unless a different arm disables shared storage.',relation='challenges',conditions='Pinned running baseline, startup logs',reported_result='Resolved configuration only; no timing result.',transfer_inference='Defer private-shard allocation for this baseline. Shared registration remains a separate conditional investigation.',limitations='Does not establish NUMA placement or memory bandwidth.'))
 packet['quote_validation']={'valid':not quote_errors(packet['claims'],packet['sources']),'errors':quote_errors(packet['claims'],packet['sources'])}
 assert packet['quote_validation']['valid'],packet['quote_validation']
 out=R/lane/'evidence/packet-review.json';write_json(out,packet)
 cards=json.loads((R/lane/'hypotheses/propose-1.json').read_text())['hypotheses']
 request.update(packet=str(out),output=str(R/lane/'review-recovery'),revisit=[HypothesisMemory.identity(str(R/lane/'hypotheses'),c['id']) for c in cards],timeout=1200)
 write_json(R/lane/'recovery-request.json',request)
# A valid short excerpt was rejected because it was under the 12-character guard.
# Preserve failed packet and expand only the excerpt, without changing the claim.
p=R/'prefill-mqa/evidence/packet.json';packet=json.loads(p.read_text())
for c in packet['claims']:
 if c['quote']=='avg +3.7%':c['quote']='sweep (192 contiguous MQA cases on SM90):\navg +3.7%'
packet['quote_validation']={'valid':not quote_errors(packet['claims'],packet['sources']),'errors':quote_errors(packet['claims'],packet['sources'])}
packet['enrichment_provenance']={'actor':'root engineering review','reason':'Expanded existing exact 9-character quote to include its adjacent context; claims unchanged; original failed packet retained.'}
assert packet['quote_validation']['valid']
write_json(R/'prefill-mqa/evidence/packet-reviewed.json',packet)
request=json.loads((R/'prefill-mqa/hypothesis-request.json').read_text());request['packet']=str(R/'prefill-mqa/evidence/packet-reviewed.json')
write_json(R/'prefill-mqa/hypothesis-request-reviewed.json',request)

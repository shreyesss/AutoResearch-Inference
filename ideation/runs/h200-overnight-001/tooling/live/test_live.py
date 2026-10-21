"""CPU fixtures exercise association, bounded ownership and reader failure modes."""
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import c25_live_observer as observer
from parse_live import worker_external_id,read_client,classify,stratum,summarize,validate_launch

X='6dcaad5a-caa6-44f5-a8ad-b1f88e5ce79e';EXTERNAL='chatcmpl-'+X;INTERNAL=EXTERNAL+'-be32565e'
def raw(phase='profiling'):
    return dict(metadata=dict(x_request_id=X,benchmark_phase=phase,phase_index=1),request_headers={'X-Request-ID':X},status=200,
        responses=[dict(packets=[dict(name='data',value=json.dumps(dict(id=EXTERNAL,choices=[dict(finish_reason='length')],usage=dict(completion_tokens=3)))),dict(name='data',value='[DONE]')])])
def record():
    return dict(req_ids=[INTERNAL],has_prefill=False,target=dict(cg_mode='FULL',num_reqs=1,num_tokens=6),draft=dict(cg_mode='FULL',num_reqs=1,num_tokens=5),context_upper=[8191],actual_rows=1,duration_us=10)
class FakeEvent:
    def __init__(self,value):self.value=value;self.syncs=0
    def synchronize(self):self.syncs+=1
    def elapsed_time(self,other):return self.value

class LiveTests(unittest.TestCase):
    def test_exact_suffix(self):self.assertEqual(worker_external_id(INTERNAL),EXTERNAL)
    def test_no_suffix_unknown(self):self.assertIsNone(worker_external_id(EXTERNAL))
    def test_long_suffix_unknown(self):self.assertIsNone(worker_external_id(INTERNAL+'a'))
    def test_bad_suffix_unknown(self):self.assertIsNone(worker_external_id(EXTERNAL+'-zzzzzzzz'))
    def test_duplicate_suffix_unknown(self):self.assertIsNone(worker_external_id(INTERNAL+'-12345678'))
    def test_client_complete(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'profile_export_raw.jsonl').write_text(json.dumps(raw())+'\n');_,s,_=read_client(d);self.assertEqual(s['profiling_complete'],1)
    def test_missing_done(self):
        with tempfile.TemporaryDirectory() as d:
            x=raw();x['responses'][0]['packets'].pop();Path(d,'profile_export_raw.jsonl').write_text(json.dumps(x)+'\n');_,s,_=read_client(d);self.assertEqual(s['profiling_complete'],0)
    def test_duplicate_client(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'profile_export_raw.jsonl').write_text((json.dumps(raw())+'\n')*2)
            with self.assertRaises(AssertionError):read_client(d)
    def test_header_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            x=raw();x['request_headers']['X-Request-ID']='wrong';Path(d,'profile_export_raw.jsonl').write_text(json.dumps(x)+'\n')
            with self.assertRaises(AssertionError):read_client(d)
    def test_response_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            x=raw();x['responses'][0]['packets'][0]['value']=json.dumps(dict(id='wrong'));Path(d,'profile_export_raw.jsonl').write_text(json.dumps(x)+'\n')
            with self.assertRaises(AssertionError):read_client(d)
    def test_primary(self):self.assertEqual(classify(record(),{EXTERNAL:dict(phase='profiling')}),('profiling',True,0))
    def test_warmup_excluded(self):self.assertEqual(classify(record(),{EXTERNAL:dict(phase='warmup')})[1],False)
    def test_unknown_excluded(self):self.assertEqual(classify(record(),{}),('unknown',False,1))
    def test_prefill_excluded(self):
        x=record();x['has_prefill']=True;self.assertFalse(classify(x,{EXTERNAL:dict(phase='profiling')})[1])
    def test_eager_excluded(self):
        x=record();x['draft']['cg_mode']='NONE';self.assertFalse(classify(x,{EXTERNAL:dict(phase='profiling')})[1])
    def test_mixed_phase_excluded(self):
        x=record();other='chatcmpl-11111111-1111-1111-1111-111111111111';x['req_ids'].append(other+'-12345678')
        self.assertEqual(classify(x,{EXTERNAL:dict(phase='profiling'),other:dict(phase='warmup')}),('mixed_phase',False,0))
    def test_bins(self):
        x=record()
        for n,expected in [(8191,'lt8192'),(8192,'8192to32767'),(32767,'8192to32767'),(32768,'ge32768')]:
            x['context_upper']=[n];self.assertEqual(stratum(0,0,x)[-1],expected)
    def test_pool_exact_gap_indices(self):
        p=observer.EventPool.__new__(observer.EventPool);p.pairs=[(FakeEvent(i+1),FakeEvent(0)) for i in range(4)]
        values,_=p.resolve([0,2]);self.assertEqual(values,[1000,3000]);self.assertEqual([b.syncs for _,b in p.pairs],[0,0,1,0])
    def test_pool_empty_no_sync(self):
        p=observer.EventPool.__new__(observer.EventPool);p.pairs=[];self.assertEqual(p.resolve([])[0],[])
    def test_output_copy(self):
        from types import SimpleNamespace
        row={'output':None};observer._STATE={'lock':__import__('threading').Lock(),'errors':[]}
        x=SimpleNamespace(_c25_live_call=row,num_sampled_tokens_np=SimpleNamespace(tolist=lambda:[1]))
        y=SimpleNamespace(req_ids=['id'],sampled_token_ids=[[42]])
        observer.output_ready(x,y);y.sampled_token_ids[0][0]=9;self.assertEqual(row['output']['sampled_token_ids'],[[42]])
        observer.output_ready(x,y);self.assertEqual(observer._STATE['errors'],['duplicate output callback']);observer._STATE=None
    def test_flush_wrong_run(self):
        observer._STATE=dict(active=True,identity=dict(run_id='correct',arm='A'))
        with self.assertRaises(AssertionError):observer.flush(run_id='wrong',arm='A',nonce='n')
        observer._STATE=None
    def test_overflow_no_recording(self):
        observer._STATE=dict(active=True,real_calls=observer.CAPACITY,records=[None]*observer.CAPACITY,pending={},overflow=0)
        with patch.dict('sys.modules',{'torch':object()}):self.assertIsNone(observer.begin(None,None))
        self.assertEqual(observer._STATE['overflow'],1);observer._STATE=None
    def test_raw_incomplete_gap_owned(self):
        import threading
        with tempfile.TemporaryDirectory() as d:
            p=observer.EventPool.__new__(observer.EventPool);p.pairs=[(FakeEvent(i+1),FakeEvent(0)) for i in range(3)];p.stream=type('S',(),{'cuda_stream':5})();p.initialization={}
            observer._STATE=dict(identity=dict(run_id='r',arm='A',rank=0,replica=0),active=True,base=Path(d)/'rank0',pool=p,lock=threading.Lock(),records=[dict(call_index=0,output={}),dict(call_index=2,output={})],pending={1:{}},real_calls=3,dummy_calls=0,overflow=0,errors=[],activation={})
            r=observer.flush(run_id='r',arm='A',nonce='n');self.assertEqual(r['status'],'incomplete')
            rows=[json.loads(x) for x in Path(d,'rank0.records.jsonl').read_text().splitlines()];self.assertEqual([x['duration_us'] for x in rows],[1000,3000]);observer._STATE=None
    def test_descriptor_enum(self):
        from enum import Enum
        class Mode(Enum):FULL=1
        @dataclass
        class D:cg_mode:Mode=Mode.FULL;num_reqs:int=2
        self.assertEqual(observer.descriptor(D()),dict(cg_mode='FULL',num_reqs=2))
    def test_launch_binding(self):
        ids={(r,k):f'00000000-0000-0000-0000-{4*r+k:012d}' for r in range(2) for k in range(4)}
        a=dict(run_id='run',uuids=ids);launch=dict(run_id='run',gpu_inventory='\n'.join(f'{4*r+k}, GPU-{u}' for (r,k),u in ids.items()))
        validate_launch(a,a,launch);wrong=copy.deepcopy(a);wrong['run_id']='wrong'
        with self.assertRaises(AssertionError):validate_launch(a,wrong,launch)
        wrong=copy.deepcopy(a);wrong['uuids'][0,0]=wrong['uuids'][0,1]
        with self.assertRaises(AssertionError):validate_launch(a,wrong,launch)
    def test_b_activation_and_native_capture(self):
        from parse_live import validate_activation
        r=dict(activation={'active':True,'outer_eligible':True})
        n=dict(native_oracle_passed=True,capture_attestation_passed=True,guards={'source':True},activation=r['activation'],captures=[dict(branch='fused',sample_steps=[0,1,2,3,4])])
        validate_activation(r,n,'B')
        bad=copy.deepcopy(r);bad['activation']['active']=False
        with self.assertRaises(AssertionError):validate_activation(bad,n,'B')
        bad=copy.deepcopy(n);bad['captures'][0]['branch']='installed'
        with self.assertRaises(AssertionError):validate_activation(r,bad,'B')
        bad=copy.deepcopy(n);bad['native_oracle_passed']=False
        with self.assertRaises(AssertionError):validate_activation(r,bad,'B')
    def test_completion_primer_suffix(self):
        self.assertEqual(worker_external_id('cmpl-8d8500d407b254f3-0-be32565e'),'cmpl-8d8500d407b254f3-0')
        self.assertIsNone(worker_external_id('cmpl-8d8500d407b254f3-be32565e'))
        self.assertIsNone(worker_external_id('cmpl-8d8500d407b254f3-1-be32565e'))
    def test_primers_excluded(self):
        x=record();x['req_ids']=['cmpl-8d8500d407b254f3-0-be32565e']
        self.assertEqual(classify(x,{'cmpl-8d8500d407b254f3-0':dict(phase='metric_primer')}),('metric_primer',False,0))
    def test_live_primer_counts(self):
        from run_traffic import attest_primer_counts,FINISH_REASONS
        value=dict(zero=True,request_counts={'0':4,'1':4},success_counts={str(r):{str(k):{f:int(f=='length') for f in FINISH_REASONS} for k in range(4)} for r in range(2)})
        attest_primer_counts(value);value['success_counts']['1']['3']['length']=None
        with self.assertRaises(AssertionError):attest_primer_counts(value)
    def test_primer_manifest_identity(self):
        from parse_live import read_primers
        with tempfile.TemporaryDirectory() as d:
            rows=[];caps=(17,19,23,29);tokens=(671,2581,3967,10059,678)
            for r in range(2):
                for k in range(4):rows.append(dict(replica=r,requested_internal_rank=k,independent_token_oracle='pass',token_ids=[tokens[(r+k)%5]]*caps[k],finish_reason='length',usage=dict(completion_tokens=caps[k]),headers={'X-data-parallel-rank':str(k)},response_id=f'cmpl-{4*r+k:016x}'))
            p=Path(d,'control.json');p.write_text(json.dumps(dict(primer_status='passed',requests=rows)))
            clients={};summary=read_primers(p,clients);self.assertEqual(summary['requests'],8);self.assertEqual({x['phase'] for x in clients.values()},{'metric_primer'})
            rows[1]['requested_internal_rank']=0;p.write_text(json.dumps(dict(primer_status='passed',requests=rows)))
            with self.assertRaises(AssertionError):read_primers(p,{})
    def test_standardization(self):
        def arm(x,y):
            rows=[record(),record()];rows[0]['duration_us']=x;rows[1]['duration_us']=y
            return dict(run_id='r',uuids={},cells={('k1',):[rows[0]]*2,('k2',):[rows[1]]},contexts={('k1',):[5],('k2',):[10]},exposure={},clients=dict(committed_tokens_by_phase={'profiling':3}),raw=[(0,0,x,'profiling')],blocks={},receipts=[],client_sha='h')
        result=summarize(arm(10,20),arm(5,20));self.assertAlmostEqual(result['standardized']['gain_percent'],25)

def synthetic_arm(root):
    import uuid
    root=Path(root);artifacts=root/'artifacts';artifacts.mkdir()
    client=[]
    for i in range(480):
        request=raw();xid=str(uuid.UUID(int=i+1));external='chatcmpl-'+xid
        request['metadata']['x_request_id']=xid;request['request_headers']['X-Request-ID']=xid
        event=json.loads(request['responses'][0]['packets'][0]['value']);event['id']=external
        request['responses'][0]['packets'][0]['value']=json.dumps(event);client.append(request)
    (artifacts/'profile_export_raw.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in client))
    caps=(17,19,23,29);tokens=(671,2581,3967,10059,678);requests=[]
    for r in range(2):
        for k in range(4):requests.append(dict(replica=r,requested_internal_rank=k,independent_token_oracle='pass',token_ids=[tokens[(r+k)%5]]*caps[k],finish_reason='length',usage=dict(completion_tokens=caps[k]),headers={'X-data-parallel-rank':str(k)},response_id=f'cmpl-{4*r+k:016x}'))
    control=root/'live-control.json';control.write_text(json.dumps(dict(primer_status='passed',requests=requests)))
    (root/'live-traffic.json').write_text(json.dumps(dict(status='passed',arm='A',run_id='run',nonce='nonce',control_receipt=dict(sha256=hashlib.sha256(control.read_bytes()).hexdigest()))))
    for replica in range(2):
        for rank in range(4):
            directory=root/'live-observations'/f'replica{replica}';directory.mkdir(parents=True,exist_ok=True)
            native=root/'observations'/f'replica{replica}';native.mkdir(parents=True,exist_ok=True)
            external='chatcmpl-'+str(uuid.UUID(int=4*replica+rank+1));row=record();row['req_ids']=[external+'-12345678']
            row.update(call_index=0,time_unix_s=100,stream=5,output=dict(req_ids=row['req_ids'],output_worker_pid=100+rank,num_sampled_tokens=[1],sampled_token_ids=[[42]]))
            data=directory/f'rank{rank}.records.jsonl';data.write_text(json.dumps(row)+'\n')
            receipt=dict(activation={'active':False},status='passed',arm='A',run_id='run',replica=replica,rank=rank,nonce='nonce',overflow=0,unfinished_calls=0,missing_outputs=0,errors=[],observer_sha256='observer',pid=100+rank,pid_start_ticks=123,
                gpu_uuid=str(uuid.UUID(int=4*replica+rank+1)),initialization=dict(capacity=65536,events=131072),records_path=data.name,records_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),real_calls=1,admitted_calls=1,dummy_calls=2,stream=5)
            (directory/f'rank{rank}.json').write_text(json.dumps(receipt));(native/f'rank{rank}.json').write_text(json.dumps(dict(receipt,restored=True,native_oracle_passed=True,capture_attestation_passed=True,guards={'fixture':True},captures=[dict(branch='installed',sample_steps=[0,1,2,3,4])])))

class ReceiptTests(unittest.TestCase):
    def mutate(self,field,value):
        from parse_live import load_arm
        with tempfile.TemporaryDirectory() as d:
            synthetic_arm(d);p=Path(d,'live-observations/replica0/rank0.json');r=json.loads(p.read_text());r[field]=value;p.write_text(json.dumps(r))
            with self.assertRaises(AssertionError):load_arm(d,'A',observer_sha='observer')
    def test_whole_arm(self):
        from parse_live import load_arm
        with tempfile.TemporaryDirectory() as d:
            synthetic_arm(d);a=load_arm(d,'A',observer_sha='observer')
            self.assertEqual(len(a['cells']),8);self.assertEqual(a['exposure']['real_calls'],8);self.assertEqual(a['exposure']['dummy_calls'],16)
    def test_wrong_source(self):self.mutate('observer_sha256','wrong')
    def test_wrong_run(self):self.mutate('run_id','wrong')
    def test_missing_output(self):self.mutate('missing_outputs',1)
    def test_overflow(self):self.mutate('overflow',1)
    def test_unfinished(self):self.mutate('unfinished_calls',1)
    def test_wrong_hash(self):self.mutate('records_sha256','wrong')
    def test_wrong_nonce(self):self.mutate('nonce','wrong')
    def test_wrong_device(self):self.mutate('gpu_uuid','wrong')
    def test_wrong_output_owner(self):
        from parse_live import load_arm
        with tempfile.TemporaryDirectory() as d:
            synthetic_arm(d);p=Path(d,'live-observations/replica0/rank0.records.jsonl');row=json.loads(p.read_text());row['output']['output_worker_pid']=999;p.write_text(json.dumps(row)+'\n')
            rpath=p.with_name('rank0.json');r=json.loads(rpath.read_text());r['records_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();rpath.write_text(json.dumps(r))
            with self.assertRaises(AssertionError):load_arm(d,'A',observer_sha='observer')

if __name__=='__main__':unittest.main(verbosity=2)

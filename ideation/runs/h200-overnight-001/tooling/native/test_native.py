"""CPU controls for fixed inventory, capture lifecycle and independent traffic oracle."""
import copy
import sys
import types
import unittest
from unittest.mock import patch
import c25_native_observer as observer
from parse_native import validate_rank, validate_bindings
from native_metrics import initial_values, attest_initial_counts, validate_observed_metrics
from service_rank_control import FINISH_REASONS, counter_delta, success_values
from service_lifecycle import drain_values
from controlled_traffic import validate_completion, CAPS, TOKEN_IDS


def valid_rank():
    result={'arm':'A','replica':0,'rank':0,'status':'passed','restored':True,'native_oracle_passed':True,
      'capture_attestation_passed':True,'timed_samples':960,'observer_sha256':'obs','reference_sha256':'ref',
      'run_id':'test','gpu_uuid':'test-gpu','pid_start_ticks':17,'guards':{'all':True},'restore_checks':{'all':True},
      'captures':[],'oracles':[],'samples':[],'device':{'stream':7}}
    dispatches={}
    for n,target,draft in ((1,1,1),(2,2,2),(4,4,4),(5,6,7)):
        def desc(rows,width):return {'cg_mode':'FULL','num_reqs':rows,'num_tokens':rows*width,'uniform_token_count':width}
        dispatch={'target':{'descriptor':desc(target,6),'graph_object_id':10+n},'draft':{'descriptor':desc(draft,5),'graph_object_id':20+n}}
        head={'shape':[draft*5,4096],'data_ptr':1000+n}
        result['captures'].append({'graph_object_id':20+n,'descriptor':desc(draft,5),'head_info':head,
          'branch':'installed','sample_steps':[0,1,2,3,4],'capturing':True})
        dispatches[n]=dispatch
        for phase in ('before','after'):
            result['oracles'].append({'phase':phase,'logical_requests':n,'dispatch':dispatch,'head':head,
              'active_state_rows':list(range(target)),'mapping':[[i]*5 for i in range(target)]+[[-1]*5 for _ in range(draft-target)],
              'temperature':[1.0]*target,'seeds':[731+i for i in range(target)],'tokens':[[42]*5 for _ in range(target)],
              **{k:True for k in ('exact_tokens','exact_finite_cache','reference_repeat','inactive_rows_preserved','counters_zero')}})
    logical=(1,2,4,5)
    for rd in range(30):
        order=list(logical[rd%4:]+logical[:rd%4])
        if rd%2:order.reverse()
        for n in order:
            for cy in range(8):
                td=dispatches[n]['target']['descriptor']
                result['samples'].append({'round':rd,'logical_requests':n,'cycle':cy,'dispatch':dispatches[n],
                  'stream':7,'full_cudagraph':True,'num_reqs':td['num_reqs'],'num_target_tokens':td['num_tokens'],
                  'forward_ms':1.0,'drafter_ms':0.5})
    return result


def counts():
    return {str(r):{str(e):{reason:(5 if e==0 and reason=='length' else (0 if e==0 else None))
      for reason in FINISH_REASONS} for e in range(4)} for r in range(2)}


class NativeTests(unittest.TestCase):
    def check(self,value):return validate_rank(value,'A',0,0,'obs','ref')
    def test_complete_inventory(self):self.assertEqual(len(self.check(valid_rank())['samples']),960)
    def test_missing_sample(self):
        v=valid_rank();v['samples'].pop()
        with self.assertRaises(ValueError):self.check(v)
    def test_duplicate_sample(self):
        v=valid_rank();v['samples'][-1]=copy.deepcopy(v['samples'][0])
        with self.assertRaises(ValueError):self.check(v)
    def test_wrong_schedule(self):
        v=valid_rank();v['samples'][0],v['samples'][1]=v['samples'][1],v['samples'][0]
        with self.assertRaises(ValueError):self.check(v)
    def test_missing_oracle(self):
        v=valid_rank();v['oracles'].pop()
        with self.assertRaises(ValueError):self.check(v)
    def test_wrong_head_reference(self):
        v=valid_rank();v['oracles'][0]['head']={'data_ptr':-1}
        with self.assertRaises(ValueError):self.check(v)
    def test_missing_native_step(self):
        v=valid_rank();v['captures'][0]['sample_steps']=[0,1,2,3]
        with self.assertRaises(ValueError):self.check(v)
    def test_wrong_padded_mapping(self):
        v=valid_rank();v['oracles'][-1]['mapping'][-1]=[0]*5
        with self.assertRaises(ValueError):self.check(v)
    def test_nonfinite_event(self):
        v=valid_rank();v['samples'][0]['drafter_ms']=float('nan')
        with self.assertRaises(ValueError):self.check(v)
    def test_unrestored_state(self):
        v=valid_rank();v['restore_checks']['all']=False
        with self.assertRaises(ValueError):self.check(v)
    def test_source_mismatch(self):
        v=valid_rank();v['reference_sha256']='candidate'
        with self.assertRaises(ValueError):self.check(v)
    def test_profile_capture_retains_nothing(self):
        with patch.dict('os.environ',{'C25_NATIVE_RUN_ID':'test'}),patch.dict(sys.modules,{'torch':types.SimpleNamespace()}):
            observer._CAPTURE[1]='stale'
            observer.begin_capture(None,profile_only=True)
            with observer.observe_sampling(None,1,5,None):pass
            self.assertEqual(observer._CAPTURE,{})
            self.assertFalse(observer._CAPTURE_ENABLED)
    def test_capture_actual_calls_and_wrapper_restore(self):
        class Spec:
            def _sample_logits(self,a,b,c,step):return step
        spec=Spec()
        class Head:
            shape=(5,8);dtype='bf16';device='cuda:0'
            def data_ptr(self):return 123
        fake_torch=types.SimpleNamespace(cuda=types.SimpleNamespace(is_current_stream_capturing=lambda:True))
        with patch.dict('os.environ',{'C25_NATIVE_RUN_ID':'test'}),patch.dict(sys.modules,{'torch':fake_torch}):
            observer.begin_capture(None,profile_only=False)
            with observer.observe_sampling(spec,1,5,Head()):
                for step in range(5):spec._sample_logits(None,None,None,step)
            self.assertNotIn('_sample_logits',vars(spec))
            self.assertEqual(observer._CAPTURE[id(spec)][1,5]['sample_steps'],[0,1,2,3,4])
            with self.assertRaises(AssertionError):
                with observer.observe_sampling(spec,1,5,Head()):pass
            observer.begin_capture(None,profile_only=True)


class BindingTests(unittest.TestCase):
    def bindings(self):
        return {(arm,replica,rank):{'run_id':'run','gpu_uuid':f'00000000-0000-0000-0000-{replica*4+rank+1:012d}'} for arm in ('A','B') for replica in range(2) for rank in range(4)}
    def test_valid_pair(self):self.assertTrue(validate_bindings(self.bindings()))
    def test_wrong_run(self):
        b=self.bindings();b['B',0,0]['run_id']='wrong'
        with self.assertRaises(ValueError):validate_bindings(b)
    def test_wrong_device(self):
        b=self.bindings();b['B',0,0]['gpu_uuid']='00000000-0000-0000-0000-999999999999'
        with self.assertRaises(ValueError):validate_bindings(b)
    def test_duplicate_device(self):
        b=self.bindings();b['A',0,0]['gpu_uuid']=b['A',0,1]['gpu_uuid']
        with self.assertRaises(ValueError):validate_bindings(b)
    def test_final_disable(self):
        observer._CAPTURE_ENABLED=True;observer._CAPTURE[1]='reference'
        observer.disable_capture()
        self.assertFalse(observer._CAPTURE_ENABLED);self.assertEqual(observer._CAPTURE,{})


class TrafficTests(unittest.TestCase):
    def test_unknown_initial_gauges_not_zero(self):
        router=[('dsv41_router_in_flight',{'backend':str(r)},0.0) for r in range(2)]
        value=initial_values(router,[[],[]],'model')
        self.assertIsNone(value['engines']['0:vllm:num_requests_running']['0'])
        self.assertFalse(value['zero'])
        self.assertEqual(value['request_counts'],{'0':None,'1':None})
    def test_posttraffic_missing_gauges_rejected(self):
        router=[('dsv41_router_in_flight',{'backend':str(r)},0.0) for r in range(2)]
        with self.assertRaises(ValueError):drain_values(router,[[],[]])
    def test_initial_exact_used_unknown_unused(self):
        result=attest_initial_counts({'request_counts':{'0':5,'1':5},'zero':True,'success_counts':counts()})
        self.assertEqual(len(result['unknown_unused_terminal_series']),30)
    def test_missing_used_counter_rejected(self):
        c=counts();c['0']['0']['stop']=None
        with self.assertRaises(AssertionError):attest_initial_counts({'request_counts':{'0':5,'1':5},'zero':True,'success_counts':c})
    def test_unexpected_rank_traffic_rejected(self):
        row=('vllm:request_success_total',{'model_name':'m','engine':'2','finished_reason':'length'},1.0)
        with self.assertRaises(AssertionError):success_values([[row],[]],'m')
    def test_missing_unused_delta_retained_unknown(self):self.assertIsNone(counter_delta(None,None,expected=0,unused_rank=True))
    def test_missing_expected_delta_rejected(self):
        with self.assertRaises(AssertionError):counter_delta(None,1,expected=1,unused_rank=False)
    def test_bad_gauge_rejected(self):
        row=('vllm:num_requests_running',{'model_name':'m','engine':'0'},float('nan'))
        with self.assertRaises(AssertionError):validate_observed_metrics([],[[row],[]],'m')
    def good_completion(self):
        return {'http_status':200,'response_id':'cmpl-x','token_ids':[671]*17,'finish_reason':'length','done_marker':True,
          'cancelled':False,'usage':{'completion_tokens':17},'metrics':{'speculative_decoding':{'num_spec_tokens':5,'num_spec_steps':1}}}
    def test_expected_tokens(self):validate_completion(self.good_completion(),671,17)
    def test_wrong_owned_token_rejected(self):
        v=self.good_completion();v['token_ids'][0]=2581
        with self.assertRaises(AssertionError):validate_completion(v,671,17)
    def test_missing_k5_rejected(self):
        v=self.good_completion();v['metrics']['speculative_decoding']['num_spec_steps']=0
        with self.assertRaises(AssertionError):validate_completion(v,671,17)
    def test_false_cancel_rejected(self):
        v=self.good_completion();v['cancelled']=True
        with self.assertRaises(AssertionError):validate_completion(v,671,4096,cancel=True)

if __name__=='__main__':unittest.main()

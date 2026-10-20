"""Saved A002 missing-gauge regression and prospective primer/drain controls."""
import ast
import asyncio
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,patch
from service_rank_control import Harness,MetricsNotReady,FINISH_REASONS,counter_delta,success_values
from service_lifecycle import parse_metrics
from native_metrics import attest_initial_counts,validate_observed_metrics
from parse_native import validate_bindings
HERE=Path(__file__).resolve().parent
RUN=HERE.parents[1]
SAVED=RUN/'native-executions/native-pair-002/A/controlled-traffic.observations'

def counts():return {str(r):{str(k):{f:(5 if k==0 else 1) if f=='length' else 0 for f in FINISH_REASONS} for k in range(4)} for r in range(2)}
def after():return dict(request_counts={'0':8,'1':8},zero=True,success_counts=counts())

def fixtures():
    return [(SAVED/f'0001-{name}.txt').read_text() for name in ('router','replica-0','replica-1')]

class RepairTests(unittest.TestCase):
    def test_actual_saved_snapshot_is_not_ready(self):
        async def run():
            with tempfile.TemporaryDirectory() as d:
                args=SimpleNamespace(base_url='http://router',backend_urls=['http://r0','http://r1'],model='deepseek-v4.1-flash',output=Path(d)/'out.json')
                receipt={'observations':[],'drains':[]};h=Harness(args,receipt,None);texts=dict(zip(h.urls,fixtures()))
                async def get(url):return texts[url.removesuffix('/metrics')]
                h.get_text=get
                with self.assertRaises(MetricsNotReady) as raised:await h.snapshot()
                self.assertEqual(len(raised.exception.missing),12);self.assertEqual(raised.exception.observation_index,0)
                self.assertEqual(len(receipt['observations']),1)
                self.assertEqual(len(list(h.observations.glob('*.txt'))),3)
        asyncio.run(run())
    def test_three_zero_polls_reset_on_missing(self):
        async def run():
            with tempfile.TemporaryDirectory() as d:
                args=SimpleNamespace(base_url='http://router',backend_urls=[],output=Path(d)/'out.json');receipt={'observations':[],'drains':[]};h=Harness(args,receipt,None)
                h.snapshot=AsyncMock(side_effect=[{'zero':True},MetricsNotReady(1,[[0,'running','1']]),{'zero':True},{'zero':True},{'zero':True}])
                with patch('service_rank_control.asyncio.sleep',new=AsyncMock()):result=await h.drain('fixture')
                self.assertTrue(result['zero']);self.assertEqual(h.snapshot.call_count,5)
                self.assertEqual(receipt['drains'][0]['samples'][1]['status'],'not_ready')
        asyncio.run(run())
    def test_malformed_is_immediate(self):
        async def run():
            with tempfile.TemporaryDirectory() as d:
                args=SimpleNamespace(base_url='u',backend_urls=[],output=Path(d)/'o');h=Harness(args,{'observations':[],'drains':[]},None);h.snapshot=AsyncMock(side_effect=AssertionError('malformed'))
                with self.assertRaises(AssertionError):await h.drain('bad')
                self.assertEqual(h.snapshot.call_count,1)
        asyncio.run(run())
    def test_exact_initial_counts(self):self.assertTrue(attest_initial_counts(after())['passed'])
    def test_old_count_inventory_rejected(self):
        x=after();x['request_counts']={'0':5,'1':5}
        with self.assertRaises(AssertionError):attest_initial_counts(x)
    def test_missing_counter_rejected(self):
        x=after();x['success_counts']['1']['2']['length']=None
        with self.assertRaises(AssertionError):attest_initial_counts(x)
    def test_wrong_rank_primer_rejected(self):
        x=after();x['success_counts']['0']['0']['length']=6;x['success_counts']['0']['1']['length']=0
        with self.assertRaises(AssertionError):attest_initial_counts(x)
    def test_unexpected_error_rejected(self):
        x=after();x['success_counts']['1']['3']['error']=1
        with self.assertRaises(AssertionError):attest_initial_counts(x)
    def test_missing_never_zero_imputed(self):
        with self.assertRaises(AssertionError):counter_delta(None,None,expected=0,unused_rank=False)
    def test_primers_preserved_in_later_deltas(self):self.assertEqual(counter_delta(1,1,expected=0,unused_rank=False),0)
    def test_all_actual_terminal_series_required(self):
        values=[parse_metrics(x) for x in fixtures()[1:]];success_values(values,'deepseek-v4.1-flash')
        values[0]=[r for r in values[0] if not (r[0]=='vllm:request_success_total' and r[1]['engine']=='1' and r[1]['finished_reason']=='length')]
        with self.assertRaises(AssertionError):success_values(values,'deepseek-v4.1-flash')
    def test_duplicate_gauge_rejected(self):
        values=[parse_metrics(x) for x in fixtures()];values[1].append(next(r for r in values[1] if r[0]=='vllm:num_requests_running'))
        with self.assertRaises(AssertionError):validate_observed_metrics(values[0],values[1:],'deepseek-v4.1-flash')
    def test_wrong_gauge_identity_rejected(self):
        values=[parse_metrics(x) for x in fixtures()];row=next(r for r in values[1] if r[0]=='vllm:num_requests_running');row[1]['engine']='9'
        with self.assertRaises(AssertionError):validate_observed_metrics(values[0],values[1:],'deepseek-v4.1-flash')
    def test_nonfinite_rejected(self):
        values=[parse_metrics(x) for x in fixtures()];values[1].append(('vllm:num_requests_waiting',{'engine':'1','model_name':'deepseek-v4.1-flash'},float('nan')))
        with self.assertRaises(AssertionError):validate_observed_metrics(values[0],values[1:],'deepseek-v4.1-flash')
    def test_cancel_witness_skips_missing_publication(self):
        from controlled_traffic import ControlledHarness
        async def run():
            h=ControlledHarness.__new__(ControlledHarness)
            request=dict(response_id='cmpl-fixture',live_rank_witness='missing',live_cancel_observation_index=1,
                attested_live_cancel_rank=0,started_unix_s=1,closed_unix_s=2)
            h.receipt=dict(groups=[],requests=[request],external_abort_acceptance={'requests':[]},
                identity_receipt={'sha256':'fixture'},drains=[{'samples':[
                    dict(status='not_ready',observation_index=2,zero=False),
                    dict(router={'0':0,'1':0},engines={f'{r}:{m}':{str(k):0 for k in range(4)} for r in range(2) for m in ('vllm:num_requests_running','vllm:num_requests_waiting')},observation_index=3,time_unix_s=3)]}])
            before=after();before['observation_index']=0;end=copy.deepcopy(before);end['request_counts']['0']=9;end['observation_index']=3
            h.snapshot=AsyncMock(return_value=before);h.drain=AsyncMock(return_value=end);h.completion=AsyncMock(return_value=request)
            await h.group(0,'cancel',[{}],1,'frontend_cancel')
            self.assertEqual(h.receipt['external_abort_acceptance']['requests'][0]['positive_rank_observation_indices'],[])
        asyncio.run(run())
    def test_original_oracles_unchanged(self):
        def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        old=nodes(HERE.parent/'native/controlled_traffic.py');new=nodes(HERE/'controlled_traffic.py')
        for name in ('row_token','completion_body','validate_completion','cancel_engine_witness','validate_live_cancel_rank'):
            self.assertEqual(old[name],new[name])
    def test_crossrun_binding(self):
        ids={i:f'00000000-0000-0000-0000-{i:012d}' for i in range(8)};loaded={};launch={}
        for arm,run_id in [('A','native-pair-002'),('B','native-B-continuation-003')]:
            launch[arm]={'run_id':run_id,'gpu_inventory':'\n'.join(f'{i}, GPU-{v}' for i,v in ids.items())}
            for replica in range(2):
                for rank in range(4):loaded[arm,replica,rank]={'run_id':run_id,'gpu_uuid':ids[4*replica+rank]}
        self.assertTrue(validate_bindings(loaded,launch));bad=copy.deepcopy(loaded);bad['B',0,0]['run_id']='native-pair-002'
        with self.assertRaises(ValueError):validate_bindings(bad,launch)
        bad=copy.deepcopy(loaded);bad['B',0,0]['gpu_uuid']=ids[1]
        with self.assertRaises(ValueError):validate_bindings(bad,launch)
    def test_original_statistic_unchanged(self):
        def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
        old=functions(HERE.parent/'native/parse_native.py');new=functions(HERE/'parse_native.py')
        for name in ('validate_rank','bootstrap'):self.assertEqual(old[name],new[name])

if __name__=='__main__':unittest.main(verbosity=2)

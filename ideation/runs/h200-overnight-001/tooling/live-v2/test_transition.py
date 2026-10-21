"""CPU-only controls of prior lifecycle authorization, phases and source invariants."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from lifecycle_transition import expected_labels,lifecycle_baseline,require_same_baseline,validate_transition,sha
from parse_live import read_lifecycle,worker_external_id,classify,validate_launch
HERE=Path(__file__).resolve().parent

def lifecycle():
    requests=[]
    for i,label in enumerate(sorted(expected_labels())):
        replica=int(label.split('-')[1]);natural=label.endswith('natural-stop');cancel=label.endswith('-cancel') and 'after' not in label
        finish=None if cancel else 'stop' if (natural or label.endswith('-eos')) else 'length'
        requests.append(dict(label=label,replica=replica,response_id=('chatcmpl-' if natural else 'cmpl-')+f'{i:016x}',http_status=200,
            independent_token_oracle='pass',finish_reason=finish,cancelled=cancel,usage=None if cancel else {'completion_tokens':3}))
    baseline=dict(zero=True,router={'0':0,'1':0},request_counts={'0':13,'1':13},
        engines={f'{r}:{m}':{str(k):0 for k in range(4)} for r in range(2) for m in ('vllm:num_requests_running','vllm:num_requests_waiting')},
        success_counts={str(r):{str(k):dict(length=7 if k==0 else 1,stop=2 if k==0 else 0,abort=0,error=0,repetition=0) for k in range(4)} for r in range(2)},observation_index=0)
    return dict(arm='B',run_id='run',scoped_observable_checks='pass',status='pending_external_abort_acceptance',requests=requests,
        replicas=[dict(replica=r,controlled_committed_token_ownership='pass',forced_eos_exact_id_and_wake='pass',unconstrained_natural_stop='observed') for r in range(2)],
        drains=[dict(status='pass',samples=[copy.deepcopy(baseline) for _ in range(3)])])

def inputs(directory):
    directory=Path(directory);identity=directory/'identity.json';life=directory/'controlled-traffic.json';review=directory/'lifecycle-prefix-review.json'
    identity.write_text(json.dumps(dict(run_id='run',arm='B',fresh_exclusive_service=True,no_prior_client_requests=True)))
    value=lifecycle();value['identity_receipt']={'sha256':sha(identity)};life.write_text(json.dumps(value))
    review.write_text(json.dumps(dict(schema_version=1,status='accepted',arm='B',run_id='run',allowed_next_phase='live_profiling',identity_sha256=sha(identity),lifecycle_receipt_sha256=sha(life))))
    return identity,life,review

class TransitionTests(unittest.TestCase):
    def test_valid_baseline(self):self.assertEqual(lifecycle_baseline(lifecycle())['request_counts'],{'0':13,'1':13})
    def test_not_fresh_zero(self):
        value=lifecycle();value['drains'][-1]['samples'][-1]['request_counts']={'0':0,'1':0}
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_missing_counter_not_zero(self):
        value=lifecycle();value['drains'][-1]['samples'][-1]['success_counts']['0']['1']['length']=None
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_wrong_counter(self):
        value=lifecycle();value['drains'][-1]['samples'][-1]['success_counts']['1']['0']['error']=1
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_drain_missing(self):
        value=lifecycle();value['drains'][-1]['samples'][-2]['zero']=False
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_wrong_inventory(self):
        value=lifecycle();value['requests'].pop()
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_duplicate_id(self):
        value=lifecycle();value['requests'][0]['response_id']=value['requests'][1]['response_id']
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_failed_oracle(self):
        value=lifecycle();value['requests'][0]['independent_token_oracle']='fail'
        with self.assertRaises(AssertionError):lifecycle_baseline(value)
    def test_inconclusive_natural_scope(self):
        value=lifecycle();value['status']='inconclusive_natural_stop';value['replicas'][0]['unconstrained_natural_stop']='inconclusive_at512'
        next(r for r in value['requests'] if r['label']=='replica-0-natural-stop')['finish_reason']='length'
        for sample in value['drains'][-1]['samples']:sample['success_counts']['0']['0'].update(length=8,stop=1)
        lifecycle_baseline(value)
    def test_unauthorized_prior_traffic(self):
        baseline=lifecycle_baseline(lifecycle());observed=dict(copy.deepcopy(baseline),zero=True);observed['request_counts']['0']+=1
        with self.assertRaises(AssertionError):require_same_baseline(observed,baseline)
    def test_exact_matching_drain(self):
        baseline=lifecycle_baseline(lifecycle());require_same_baseline(dict(baseline,zero=True),baseline)
    def test_approval_hash(self):
        with tempfile.TemporaryDirectory() as d:
            identity,life,review=inputs(d)
            _,_,proof=validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=d,verify_files=False)
            self.assertEqual(proof['authorized_prior_requests'],26)
            with life.open('a') as out:out.write(' ')
            with self.assertRaises(AssertionError):validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=d,verify_files=False)
    def test_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            identity,life,review=inputs(d);r=json.loads(review.read_text());r['status']='rejected';review.write_text(json.dumps(r))
            with self.assertRaises(AssertionError):validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=d,verify_files=False)
    def test_wrong_run(self):
        with tempfile.TemporaryDirectory() as d:
            identity,life,review=inputs(d)
            with self.assertRaises(AssertionError):validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='other',arm_output=d,verify_files=False)
    def test_lifecycle_phase_and_cancel_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d,'life.json');path.write_text(json.dumps(lifecycle()));clients={};summary=read_lifecycle(path,clients)
            self.assertEqual(len(clients),26);self.assertEqual(summary['cancelled'],2);self.assertEqual(summary['unknown_committed_requests'],2)
            self.assertEqual({v['phase'] for v in clients.values()},{'lifecycle_control'})
            for external in clients:
                internal=external+'-12345678';self.assertEqual(worker_external_id(internal),external)
                row=dict(req_ids=[internal],has_prefill=False,target={'cg_mode':'FULL'},draft={'cg_mode':'FULL'})
                self.assertFalse(classify(row,clients)[1])
    def test_phase_never_guessed(self):self.assertEqual(worker_external_id('chatcmpl-0000000000000000-zzzzzzzz'),None)
    def test_full_hash_bound_transition_and_prefix_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);identity,life,review=inputs(d);value=json.loads(life.read_text())
            value['adapter_sha256']=sha(HERE.parent/'native-v2/controlled_traffic.py')
            value['dependencies']=[dict(path=str(HERE.parent/'native-v2'/name),sha256=sha(HERE.parent/'native-v2'/name)) for name in ('service_rank_control.py','service_lifecycle.py','native_metrics.py')]
            value['native_receipts']=[]
            for r in range(2):
                for k in range(4):
                    p=root/'observations'/f'replica{r}'/f'rank{k}.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
                    value['native_receipts'].append(dict(path=str(p),sha256=sha(p)))
            metric=root/'metric.prom';metric.write_text('fixture metric\n');value['observations']=[{'files':[dict(path=str(metric),sha256=sha(metric))]}]
            logs=[]
            for r in range(2):
                original=root/f'replica{r}.log';original.write_text('complete owned line\nappended line\n');snap=root/f'prefix{r}.log';snap.write_text('complete owned line\n')
                logs.append(dict(replica=r,path=str(snap),original_log_path=str(original),sha256=sha(snap),byte_length=len(snap.read_bytes())))
            life.write_text(json.dumps(value))
            att=root/'prefix-attestation.json';att.write_text(json.dumps(dict(arm='B',run_id='run',logs=logs,identity_sha256=sha(identity),lifecycle_receipt_sha256=sha(life))))
            r=json.loads(review.read_text());r.update(lifecycle_receipt_sha256=sha(life),log_prefix_attestation=dict(path=str(att),sha256=sha(att)));review.write_text(json.dumps(r))
            validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=root)
            original_attestation=att.read_bytes();wrong=json.loads(original_attestation);wrong['identity_sha256']='0'*64
            att.write_text(json.dumps(wrong));r['log_prefix_attestation']['sha256']=sha(att);review.write_text(json.dumps(r))
            with self.assertRaises(AssertionError):validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=root)
            att.write_bytes(original_attestation);r['log_prefix_attestation']['sha256']=sha(att);review.write_text(json.dumps(r))
            (root/'replica0.log').write_text('changed prefix\n')
            with self.assertRaises(AssertionError):validate_transition(identity_path=identity,lifecycle_path=life,review_path=review,arm='B',run_id='run',arm_output=root)
    def test_observer_mounts_and_client_argv_unchanged(self):
        old=json.loads((HERE.parent/'live/manifest.json').read_text());new=json.loads((HERE/'manifest.json').read_text())
        self.assertEqual(old['files'],new['files'])
        old=json.loads((HERE.parent/'live/traffic-manifest.json').read_text());new=json.loads((HERE/'traffic-manifest.json').read_text())
        self.assertEqual(old['client_command_template'],new['client_command_template'])
    def test_numerical_functions_unchanged(self):
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
        old=functions(HERE.parent/'live/parse_live.py');new=functions(HERE/'parse_live.py')
        for name in ('stats','classify','stratum','context_stats','validate_activation'):self.assertEqual(old[name],new[name])
    def test_order_binding(self):
        import uuid
        ids={(r,k):str(uuid.UUID(int=4*r+k+1)) for r in range(2) for k in range(4)};arm=dict(run_id='run',uuids=ids)
        launch=dict(run_id='run',arm_order=['B','A'],gpu_inventory='\n'.join(f'{4*r+k}, GPU-{v}' for (r,k),v in ids.items()))
        validate_launch(arm,arm,launch);launch['arm_order']=['A','B']
        with self.assertRaises(AssertionError):validate_launch(arm,arm,launch)

if __name__=='__main__':unittest.main(verbosity=2)

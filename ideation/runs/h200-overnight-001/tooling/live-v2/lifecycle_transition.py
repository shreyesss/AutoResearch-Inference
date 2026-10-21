"""Hash-bound authorization of the exact completed26-request lifecycle."""
from pathlib import Path
import hashlib
import json


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_json(path):return json.loads(Path(path).read_text())

def expected_labels():
    labels={f'replica-{r}-row-{k}' for r in range(2) for k in range(5)}
    labels|={f'replica-{r}-rank-{k}-metric-primer' for r in range(2) for k in (1,2,3)}
    for r in range(2):
        labels|={f'replica-{r}-{suffix}' for suffix in ('cancel','reference-after-cancel','eos','reference-after-eos','natural-stop')}
    return labels

def lifecycle_baseline(lifecycle):
    assert lifecycle['scoped_observable_checks']=='pass'
    assert lifecycle['status'] in ('pending_external_abort_acceptance','inconclusive_natural_stop')
    requests=lifecycle['requests'];assert len(requests)==26
    assert {x['label'] for x in requests}==expected_labels()
    assert len({x['response_id'] for x in requests})==26
    assert all(x['http_status']==200 for x in requests)
    for request in requests:
        if not request['label'].endswith('natural-stop'):
            assert request['independent_token_oracle']=='pass'
    assert len(lifecycle['replicas'])==2 and {x['replica'] for x in lifecycle['replicas']}=={0,1}
    assert all(x['controlled_committed_token_ownership']=='pass' and x['forced_eos_exact_id_and_wake']=='pass'
        and x['unconstrained_natural_stop'] in ('observed','inconclusive_at512') for x in lifecycle['replicas'])
    last=lifecycle['drains'][-1]
    assert last['status']=='pass' and len(last['samples'])>=3
    assert all(x.get('zero') is True and x.get('status')!='not_ready' for x in last['samples'][-3:])
    baseline=last['samples'][-1]
    assert baseline['request_counts']=={'0':13,'1':13}
    assert baseline['router']=={'0':0,'1':0}
    for replica in range(2):
        natural=next(x for x in requests if x['label']==f'replica-{replica}-natural-stop')
        assert natural['finish_reason'] in ('length','stop')
        for metric in ('vllm:num_requests_running','vllm:num_requests_waiting'):
            assert baseline['engines'][f'{replica}:{metric}']=={str(k):0 for k in range(4)}
        for rank in range(4):
            expected=dict(length=(7+int(natural['finish_reason']=='length') if rank==0 else 1),
                stop=(1+int(natural['finish_reason']=='stop') if rank==0 else 0),abort=0,error=0,repetition=0)
            assert baseline['success_counts'][str(replica)][str(rank)]==expected
    return {k:baseline[k] for k in ('router','engines','request_counts','success_counts')}

def require_same_baseline(observed,baseline):
    assert observed['zero'] is True
    for key in ('router','engines','request_counts','success_counts'):
        assert observed[key]==baseline[key],f'unauthorized traffic or changed lifecycle baseline: {key}'

def validate_transition(*,identity_path,lifecycle_path,review_path,arm,run_id,arm_output,verify_files=True):
    identity=load_json(identity_path);lifecycle=load_json(lifecycle_path);review=load_json(review_path)
    for value in (identity,lifecycle,review):assert value['arm']==arm and value['run_id']==run_id
    # These fields describe historical ownership at lifecycle start, not current counters.
    assert identity['fresh_exclusive_service'] is True
    assert lifecycle['identity_receipt']['sha256']==sha(identity_path)
    assert review['schema_version']==1 and review['status']=='accepted' and review['allowed_next_phase']=='live_profiling'
    assert review['identity_sha256']==sha(identity_path) and review['lifecycle_receipt_sha256']==sha(lifecycle_path)
    baseline=lifecycle_baseline(lifecycle)
    if verify_files:
        here=Path(__file__).resolve().parent
        assert lifecycle['adapter_sha256']==sha(here.parent/'native-v2/controlled_traffic.py')
        expected_dependencies={str(here.parent/'native-v2'/name) for name in ('service_rank_control.py','service_lifecycle.py','native_metrics.py')}
        assert {x['path'] for x in lifecycle['dependencies']}==expected_dependencies
        for dependency in lifecycle['dependencies']:assert sha(dependency['path'])==dependency['sha256']
        assert len(lifecycle['native_receipts'])==8
        expected={str((Path(arm_output)/'observations'/f'replica{r}'/f'rank{k}.json').resolve()) for r in range(2) for k in range(4)}
        assert {str(Path(x['path']).resolve()) for x in lifecycle['native_receipts']}==expected
        for native in lifecycle['native_receipts']:assert sha(native['path'])==native['sha256']
        attestation=review['log_prefix_attestation'];assert sha(attestation['path'])==attestation['sha256']
        prefix=load_json(attestation['path']);assert prefix['arm']==arm and prefix['run_id']==run_id
        assert prefix['identity_sha256']==review['identity_sha256']
        assert prefix['lifecycle_receipt_sha256']==review['lifecycle_receipt_sha256']
        assert len(prefix['logs'])==2 and {x['replica'] for x in prefix['logs']}=={0,1}
        for entry in prefix['logs']:
            data=Path(entry['path']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==entry['sha256'] and len(data)==entry['byte_length'] and data.endswith(b'\n')
            original=Path(entry['original_log_path'])
            assert original.resolve()==(Path(arm_output)/f"replica{entry['replica']}.log").resolve()
            with original.open('rb') as handle:assert handle.read(len(data))==data
        index=lifecycle['drains'][-1]['samples'][-1]['observation_index']
        for entry in lifecycle['observations'][index]['files']:assert sha(entry['path'])==entry['sha256']
    return lifecycle,baseline,dict(identity_sha256=sha(identity_path),lifecycle_receipt_sha256=sha(lifecycle_path),
        lifecycle_review_sha256=sha(review_path),authorized_prior_requests=26,
        scope='exact completed lifecycle on unchanged loaded service; natural-stop coverage retained separately')

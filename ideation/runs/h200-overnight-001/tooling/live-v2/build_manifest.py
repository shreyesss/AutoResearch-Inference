"""Version only lifecycle admission/phase accounting; all GPU observation mounts unchanged."""
from pathlib import Path
import hashlib
import json
HERE=Path(__file__).resolve().parent;RUN=HERE.parents[1];OLD=HERE.parent/'live'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    observation=json.loads((OLD/'manifest.json').read_text())
    observation['arm_order']=['B','A']
    observation['review_inputs'] += [str(HERE/name) for name in ('run_traffic.py','parse_live.py','lifecycle_transition.py','test_transition.py','build_manifest.py')]
    observation['review_inputs'] += [str(RUN/'tooling-evidence/live-v2'/name) for name in ('BUILD_REVIEW.md','tests.txt','build-receipt.json')]
    observation['lifecycle_admission']='same existing26 fixtures eacharm, exact hashbound independent prefix review, current actual counterbaseline; no8primer phase'
    (HERE/'manifest.json').write_text(json.dumps(observation,indent=2)+'\n')
    traffic=json.loads((OLD/'traffic-manifest.json').read_text())
    traffic['command_template']=['/home/ubuntu/Deepseek_serve/.venv/bin/python',str(HERE/'run_traffic.py'),
        '--arm','{arm}','--run-id','{run_id}','--arm-output','{arm_output}','--identity','{arm_output}/identity.json',
        '--lifecycle-receipt','{arm_output}/controlled-traffic.json','--lifecycle-review','{arm_output}/lifecycle-prefix-review.json']
    traffic['input_sha256'].update({str(HERE/name):sha(HERE/name) for name in ('run_traffic.py','parse_live.py','lifecycle_transition.py','test_transition.py','build_manifest.py')})
    for key in ('metric_primers','primer_caps','primer_expected_length_per_rank','primer_router_counts'):traffic.pop(key,None)
    traffic.update(arm_order=['B','A'],authorized_prior_lifecycle_requests=26,
        additional_metric_primers=0,phase='lifecycle_control exactIDs excluded from profiling',
        prior_traffic_admission='immutable identity+lifecycle26+independent accepted prefixreview+matching actual40counter/routerbaseline',
        total_post_readiness_cap_seconds=1080,lifecycle_cap_seconds=300,prefix_review_cap_seconds=180,complete_cap_seconds=600)
    (HERE/'traffic-manifest.json').write_text(json.dumps(traffic,indent=2)+'\n')
if __name__=='__main__':main()

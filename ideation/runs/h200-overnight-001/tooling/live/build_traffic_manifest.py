from pathlib import Path
import hashlib
import json
HERE=Path(__file__).resolve().parent;RUN=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=Path('/home/jl_fs/datasets/aiperf/mooncake/scaled/0p5x/median.jsonl')
    assert sha(source)=='91fb37aac45c4aafc4c8c04e42d92bb0654f68eebd4f02b09adeee5449c5e1e1'
    lines=source.read_bytes().splitlines(keepends=True);origin=json.loads(lines[0])['timestamp']
    prefix=b''.join(line for line in lines if 0<=json.loads(line)['timestamp']-origin<150000)
    assert hashlib.sha256(prefix).hexdigest()=='aebcfacdd261c5eb214c9430aaacc51c6e63cfb34fe9ec852919976bd938bd70'
    dest=HERE/'median-0p5x-150s.jsonl';dest.write_bytes(prefix)
    prior=RUN.parent/'av-k5-timing-001/client-dryrun.json';argv=json.loads(prior.read_text())['command']
    argv[argv.index('--input-file')+1]=str(dest)
    argv[argv.index('--artifact-dir')+1]='{arm_output}/artifacts'
    native=json.loads((RUN/'tooling/native/traffic-manifest.json').read_text())
    files=[HERE/x for x in ('run_traffic.py','parse_live.py','build_traffic_manifest.py','median-0p5x-150s.jsonl')]
    files += [RUN/'tooling/native-v2'/x for x in ('service_lifecycle.py','native_metrics.py','service_rank_control.py','controlled_traffic.py')]
    files += [prior,source,Path('/home/ubuntu/Deepseek_serve/lib/router.py')]
    out=dict(schema_version=1,command_template=['/home/ubuntu/Deepseek_serve/.venv/bin/python',str(HERE/'run_traffic.py'),
        '--arm','{arm}','--run-id','{run_id}','--arm-output','{arm_output}','--identity','{arm_output}/identity.json'],
        router_command=native['router_command'],router_environment_absent=native['router_environment_absent'],
        input_sha256={str(p):sha(p) for p in files},client_command_template=argv,
        expected_profiling_requests=480,metric_primers=8,primer_caps=[17,19,23,29],primer_expected_length_per_rank=1,primer_router_counts=[4,4],warmup_seconds=120,warmup_grace_max_seconds=300,
        complete_cap_seconds=600,output='live-traffic.json',
        live_observations='live-observations',native_observations='observations',
        flush_urls=['http://127.0.0.1:8100/c25_live/flush','http://127.0.0.1:8101/c25_live/flush'],
        pass_predicate=dict(status='passed',profiling_complete=480,overflow=0,unfinished_calls=0),
        exit='0 only if full480 profiling cohort + all warmup complete + strict drain + both RPCs + all8 bound receipts; otherwise2',
        original_client_argv_sha256=sha(prior),changes=['exact150second480row original-byte prefix','unique artifact directory only'])
    (HERE/'traffic-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()

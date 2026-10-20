"""Render reviewed native A/B launch inputs without launching any process."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PKG='/usr/local/lib/python3.12/dist-packages/'
DS=PKG+'vllm/v1/worker/gpu/spec_decode/dspark/speculator.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--observer-manifest',required=True,type=Path);ap.add_argument('--traffic-manifest',required=True,type=Path);ap.add_argument('--id',default='native-pair-001');ap.add_argument('--manifest-output',type=Path);args=ap.parse_args()
    if not args.id.replace('-','').isalnum():raise ValueError('Simple run ID required')
    base_path=ROOT/'native-root/baseline-inputs-v2.json';dev_path=ROOT/'developer/integration/manifest.json'
    base=json.loads(base_path.read_text());dev=json.loads(dev_path.read_text());obs=json.loads(args.observer_manifest.read_text());traffic=json.loads(args.traffic_manifest.read_text())
    out=ROOT/'native-executions'/args.id
    if out.exists():raise ValueError('Execution output already exists')
    inputs=[base_path,dev_path,args.observer_manifest,args.traffic_manifest,Path(__file__).resolve(),ROOT/'native-root/controller.py',ROOT/'native-root/watchdog.py',ROOT/'evaluator/C25_NATIVE_PILOT_CONTRACT.md',ROOT/'evaluator/C25_NATIVE_OVERLAY_REVIEW.md',Path(base['source_command_file']),Path(base['profile_path'])]
    if sha(base['profile_path'])!=base['profile_sha256']:raise ValueError('Profile drift')
    if sha(base['source_command_file'])!=base['source_command_sha256']:raise ValueError('Baseline command source drift')
    arms={}
    for arm in ('A','B'):
        mounts={}
        if arm=='B':
            for row in dev['files']:mounts[row['destination']]=dict(row)
        for row in obs['files']:
            if arm not in row['arms']:continue
            dest=row['destination']
            if dest in mounts:
                if dest!=DS or row.get('replaces_candidate_sha256')!=mounts[dest]['sha256']:raise ValueError('Unproven overlay collision '+dest)
            if dest==DS and arm=='A' and row.get('base_sha256')!='97bcfaa655c6d4a5ecdfb17ab87b80547e8216b9d15a91c341798ebbb558f146':raise ValueError('Unproven baseline observer')
            mounts[dest]=dict(row)
        if DS not in mounts:raise ValueError('Missing arm DSpark observer')
        for row in mounts.values():
            if sha(row['source'])!=row['sha256']:raise ValueError('Overlay source drift '+row['source'])
            inputs.append(Path(row['source']))
        commands=[];names=[]
        for rep,old in enumerate(base['commands']):
            argv=list(old);name='h200-c25-'+args.id+'-'+arm.lower()+'-'+str(rep);names.append(name);argv[argv.index('--name')+1]=name
            # Preserve baseline engine/config/cache inputs. Added hooks and unique Python
            # bytecode paths are identical across arms except their declared treatment.
            additions=['--env','PYTHONPYCACHEPREFIX=/c25-native-pycache','--env','C25_NATIVE_OUTPUT=/c25-native-out','--env','C25_NATIVE_ARM='+arm,'--env','C25_NATIVE_REPLICA='+str(rep),'--env','C25_NATIVE_RUN_ID='+args.id,'--volume',str(out/arm/'observations')+':/c25-native-out:rw','--volume',str(out/arm/'pycache')+':/c25-native-pycache:rw']
            for dest,row in sorted(mounts.items()):additions.extend(['--volume',row['source']+':'+dest+':ro'])
            at=argv.index('--entrypoint');argv[at:at]=additions;commands.append(argv)
        replacements={'{arm}':arm,'{arm_output}':str(out/arm),'{run_id}':args.id}
        traffic_argv=[]
        for arg in traffic['command_template']:
            for key,value in replacements.items():arg=arg.replace(key,value)
            traffic_argv.append(arg)
        arms[arm]={'names':names,'commands':commands,'mounts':list(mounts.values()),'traffic_command':traffic_argv}
    for path,expected in traffic['input_sha256'].items():
        if sha(path)!=expected:raise ValueError('Traffic dependency drift '+path)
        inputs.append(Path(path))
    for path in obs.get('review_inputs',[]):inputs.append(Path(path))
    for path in [ROOT/'evaluator/C25_COMPONENT_RESULT_REVIEW.md',ROOT/'meta-critic/CONTRACT_REVIEW_003.md']:inputs.append(path)
    result={'run_id':args.id,'output':str(out),'base_manifest':str(base_path),'observer_manifest':str(args.observer_manifest.resolve()),'traffic_manifest':str(args.traffic_manifest.resolve()),'arms':arms,'router_command':traffic['router_command'],'router_url':'http://127.0.0.1:8000','backend_urls':['http://127.0.0.1:8100','http://127.0.0.1:8101'],'gpu_inventory':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name','--format=csv,noheader'],text=True).strip(),'input_sha256':{str(p.resolve()):sha(p) for p in inputs}}
    path=args.manifest_output.resolve() if args.manifest_output else ROOT/'native-root'/('launch-'+args.id+'.json')
    with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(path)
if __name__=='__main__':main()

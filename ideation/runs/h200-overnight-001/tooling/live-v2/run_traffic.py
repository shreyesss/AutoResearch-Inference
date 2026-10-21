"""Root-launched bounded traffic+drain+flush; subprocess stays in root process group."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'native-v2'))
from service_lifecycle import parse_metrics,drain_values
from native_metrics import validate_observed_metrics
from service_rank_control import Harness
from lifecycle_transition import validate_transition,require_same_baseline
from service_rank_control import FINISH_REASONS
from types import SimpleNamespace
from parse_live import read_client,validate_activation
MODEL='deepseek-v4.1-flash'
URLS=['http://127.0.0.1:8000','http://127.0.0.1:8100','http://127.0.0.1:8101']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def validate_rank_receipts(root,arm,run_id,nonce):
    files=[];uuids=[]
    for replica in range(2):
        for rank in range(4):
            p=root/'live-observations'/f'replica{replica}'/f'rank{rank}.json';v=json.loads(p.read_text())
            native=json.loads((root/'observations'/f'replica{replica}'/f'rank{rank}.json').read_text())
            ready=json.loads(p.with_name(f'rank{rank}.ready.json').read_text())
            for field,expected in dict(arm=arm,run_id=run_id,replica=replica,rank=rank,nonce=nonce,status='passed').items():assert v[field]==expected
            for field in ('gpu_uuid','pid','pid_start_ticks'):
                assert v[field]==native[field]==ready[field]
            assert ready['status']=='ready' and native['status']=='passed' and native['restored'] is True
            validate_activation(v,native,arm)
            assert v['overflow']==v['unfinished_calls']==v['missing_outputs']==0 and not v['errors']
            assert v['real_calls']==v['admitted_calls']
            assert v['initialization']['capacity']==65536 and v['initialization']['events']==131072
            raw=p.with_name(v['records_path']);assert sha(raw)==v['records_sha256']
            assert v['observer_sha256']==sha(HERE.parent/'live/c25_live_observer.py')
            files.append(dict(path=str(p),sha256=sha(p),records_sha256=sha(raw),replica=replica,rank=rank));uuids.append(v['gpu_uuid'])
    assert len(set(uuids))==8
    return files

async def work(args,receipt):
    import aiohttp
    identity=json.loads(args.identity.read_text())
    assert identity['arm']==args.arm and identity['run_id']==args.run_id
    lifecycle,baseline,authorization=validate_transition(identity_path=args.identity,
        lifecycle_path=args.lifecycle_receipt,review_path=args.lifecycle_review,
        arm=args.arm,run_id=args.run_id,arm_output=args.arm_output)
    receipt['identity_sha256']=sha(args.identity)
    receipt['lifecycle_authorization']=authorization
    receipt['lifecycle_receipt']={'path':str(args.lifecycle_receipt),'sha256':sha(args.lifecycle_receipt)}
    receipt['lifecycle_review']={'path':str(args.lifecycle_review),'sha256':sha(args.lifecycle_review)}
    manifest=json.loads((HERE/'traffic-manifest.json').read_text())
    for p,h in manifest['input_sha256'].items():assert sha(p)==h
    if any(k.startswith('DSV41_ROUTER_') for k in os.environ):raise AssertionError('unexpected router override environment')
    for replica in range(2):
        for rank in range(4):
            base=args.arm_output/'live-observations'/f'replica{replica}'
            ready=json.loads((base/f'rank{rank}.ready.json').read_text())
            assert ready['status']=='ready' and ready['run_id']==args.run_id and ready['arm']==args.arm
    control_path=args.arm_output/'live-control.json'
    control=dict(observations=[],drains=[],authorized_prior_requests=26,lifecycle_baseline=baseline)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180,connect=10,sock_read=60)) as client:
        hargs=SimpleNamespace(base_url=URLS[0],backend_urls=URLS[1:],model=MODEL,output=control_path)
        harness=Harness(hargs,control,client)
        try:
            health=json.loads(await harness.get_text(URLS[0]+'/health'))
            assert health['backends']==URLS[1:]
            initial=await harness.drain('post-lifecycle-admission-drain')
            require_same_baseline(initial,baseline)
            control['prior_lifecycle_baseline_match']=True
            control_path.write_text(json.dumps(control,indent=2)+'\n')
            cmd=[x.format(arm_output=str(args.arm_output),arm=args.arm,run_id=args.run_id) for x in manifest['client_command_template']]
            receipt['client_command']=cmd
            with (args.arm_output/'aiperf.log').open('xb') as stdout:
                child=await asyncio.create_subprocess_exec(*cmd,stdout=stdout,stderr=asyncio.subprocess.STDOUT)
                receipt['client_pid']=child.pid
                try:receipt['client_exit_code']=await child.wait()
                finally:
                    if child.returncode is None:
                        child.terminate()
                        try:await asyncio.wait_for(child.wait(),5)
                        except asyncio.TimeoutError:child.kill();await child.wait()
            assert receipt['client_exit_code']==0,'AIPerf failed; retained partial artifacts'
            _,summary,raw_sha=read_client(args.arm_output/'artifacts')
            receipt['client_summary']=summary;receipt['client_raw_sha256']=raw_sha
            assert summary['profiling']==summary['profiling_complete']==480 and not summary['errors']
            await harness.drain('complete-workload-drain')
            receipt['nonce']=str(uuid.uuid4());receipt['flushes']=[]
            async def flush(url):
                async with client.post(url,json={k:receipt[k] for k in ('run_id','arm','nonce')}) as response:
                    text=await response.text()
                    receipt['flushes'].append(dict(url=url,status=response.status,response=text))
                    assert response.status==200,'flush RPC failed'
            await asyncio.wait_for(asyncio.gather(*(flush(url) for url in manifest['flush_urls'])),45)
        finally:
            control_path.write_text(json.dumps(control,indent=2)+'\n')
            receipt['control_receipt']=dict(path=str(control_path),sha256=sha(control_path))
    receipt['rank_receipts']=validate_rank_receipts(args.arm_output,args.arm,args.run_id,receipt['nonce'])
    receipt['profiling_complete']=480;receipt['overflow']=0;receipt['unfinished_calls']=0;receipt['status']='passed'

async def main_async(args,receipt):
    await asyncio.wait_for(work(args,receipt),timeout=600)

def main():
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=['A','B'],required=True);p.add_argument('--run-id',required=True);p.add_argument('--arm-output',type=Path,required=True);p.add_argument('--identity',type=Path,required=True);p.add_argument('--lifecycle-receipt',type=Path,required=True);p.add_argument('--lifecycle-review',type=Path,required=True);args=p.parse_args()
    output=args.arm_output/'live-traffic.json'
    assert not output.exists()
    receipt=dict(schema_version=1,arm=args.arm,run_id=args.run_id,status='incomplete',started_unix_s=time.time())
    try:asyncio.run(main_async(args,receipt));code=0
    except Exception as exc:receipt['error']=f'{type(exc).__name__}: {exc}';code=2
    finally:
        receipt['ended_unix_s']=time.time();output.write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(code)
if __name__=='__main__':main()

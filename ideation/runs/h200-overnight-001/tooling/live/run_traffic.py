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
from controlled_traffic import ControlledHarness,completion_body,row_token,CAPS
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
            assert v['observer_sha256']==sha(HERE/'c25_live_observer.py')
            files.append(dict(path=str(p),sha256=sha(p),records_sha256=sha(raw),replica=replica,rank=rank));uuids.append(v['gpu_uuid'])
    assert len(set(uuids))==8
    return files

def attest_primer_counts(value):
    assert value['zero'] and value['request_counts']=={'0':4,'1':4}
    for replica in range(2):
        for rank in range(4):
            for reason in FINISH_REASONS:
                assert value['success_counts'][str(replica)][str(rank)][reason]==int(reason=='length')

async def work(args,receipt):
    import aiohttp
    identity=json.loads(args.identity.read_text())
    assert identity['arm']==args.arm and identity['run_id']==args.run_id
    assert identity['fresh_exclusive_service'] is True and identity['no_prior_client_requests'] is True
    receipt['identity_sha256']=sha(args.identity)
    manifest=json.loads((HERE/'traffic-manifest.json').read_text())
    for p,h in manifest['input_sha256'].items():assert sha(p)==h
    if any(k.startswith('DSV41_ROUTER_') for k in os.environ):raise AssertionError('unexpected router override environment')
    for replica in range(2):
        for rank in range(4):
            base=args.arm_output/'live-observations'/f'replica{replica}'
            ready=json.loads((base/f'rank{rank}.ready.json').read_text())
            assert ready['status']=='ready' and ready['run_id']==args.run_id and ready['arm']==args.arm
    control_path=args.arm_output/'live-control.json'
    control=dict(requests=[],groups=[],observations=[],drains=[],primer_status='incomplete')
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180,connect=10,sock_read=60)) as client:
        hargs=SimpleNamespace(base_url=URLS[0],backend_urls=URLS[1:],model=MODEL,output=control_path)
        harness=ControlledHarness(hargs,control,client)
        try:
            health=json.loads(await harness.get_text(URLS[0]+'/health'))
            assert health['backends']==URLS[1:]
            control['initial']=await harness.snapshot(initial=True)
            primer_calls=[(replica,rank) for replica in range(2) for rank in range(4)]
            results=await asyncio.gather(*(harness.completion(replica,
                label=f'live-metric-primer-replica{replica}-rank{rank}',
                body=completion_body(MODEL,replica,rank),token_id=row_token(replica,rank),
                cap=CAPS[rank],internal_rank=rank) for replica,rank in primer_calls),return_exceptions=True)
            if any(isinstance(x,BaseException) for x in results):
                raise AssertionError('fixed metric primer exact-token oracle failed')
            initial=await harness.drain('metric-primer-drain')
            attest_primer_counts(initial)
            control['primer_status']='passed'
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
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=['A','B'],required=True);p.add_argument('--run-id',required=True);p.add_argument('--arm-output',type=Path,required=True);p.add_argument('--identity',type=Path,required=True);args=p.parse_args()
    output=args.arm_output/'live-traffic.json'
    assert not output.exists()
    receipt=dict(schema_version=1,arm=args.arm,run_id=args.run_id,status='incomplete',started_unix_s=time.time())
    try:asyncio.run(main_async(args,receipt));code=0
    except Exception as exc:receipt['error']=f'{type(exc).__name__}: {exc}';code=2
    finally:
        receipt['ended_unix_s']=time.time();output.write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(code)
if __name__=='__main__':main()

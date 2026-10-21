"""Root-owned bounded real-request proposal-stage pilot. Candidate-first distinct allocation; native checks and symmetric lifecycle retained."""
from __future__ import annotations
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request
import traceback

ROOT=Path(__file__).resolve().parents[1]

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=Path(p); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(v,indent=2)+'\n'); tmp.replace(p)
def cmd(argv): return subprocess.check_output(argv,text=True,timeout=30).strip()
def processes(): return cmd(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'])
def health(url):
    try:
        with urllib.request.urlopen(url+'/health',timeout=2) as f: return f.status==200
    except Exception: return False
def identity(pid):
    p=Path('/proc')/str(pid)
    return {'pid':pid,'exe':str((p/'exe').resolve()),'argv':(p/'cmdline').read_bytes().split(b'\0')[:-1] and [x.decode() for x in (p/'cmdline').read_bytes().split(b'\0')[:-1]],'start_ticks':(p/'stat').read_text().rsplit(')',1)[1].split()[19]}
def container_identity(name, detail):
    pid=detail['State']['Pid'];p=Path('/proc')/str(pid)
    host={'pid':pid,'start_ticks':(p/'stat').read_text().rsplit(')',1)[1].split()[19]}
    try:host['exe']=str((p/'exe').resolve())
    except PermissionError as exc:host['exe_unavailable']=repr(exc)
    code="import json;from pathlib import Path;p=Path('/proc/1');print(json.dumps({'pid':1,'exe':str((p/'exe').resolve()),'argv':[x.decode() for x in (p/'cmdline').read_bytes().split(bytes([0]))[:-1]],'start_ticks':(p/'stat').read_text().rsplit(')',1)[1].split()[19]}))"
    local=json.loads(cmd(['docker','exec',name,'python3','-c',code]))
    after=json.loads(cmd(['docker','inspect',name]))[0]
    if after['Id']!=detail['Id'] or after['State']['Pid']!=pid or not after['State']['Running']:raise RuntimeError('Container identity changed during attestation')
    if host['start_ticks']!=local['start_ticks']:raise RuntimeError('Host/container PID1 start identity mismatch')
    if (p/'stat').read_text().rsplit(')',1)[1].split()[19]!=host['start_ticks']:raise RuntimeError('Host PID start identity changed')
    return {'host_process':host,'container_process':local,'host_container_start_ticks_match':True,'container_id':detail['Id']}
def unchanged(hashes): return [p for p,h in hashes.items() if not Path(p).is_file() or sha(p)!=h]
def journal(event,**kw):
    with (ROOT/'journal.jsonl').open('a') as f: f.write(json.dumps({'time_utc':now(),'event':event,**kw})+'\n')
def telemetry(path):
    sample={'time_utc':now()};started=time.monotonic()
    argv=['nvidia-smi','--query-gpu=index,uuid,temperature.gpu,power.draw,clocks.sm,clocks.mem,pstate,memory.used,utilization.gpu','--format=csv,noheader']
    try:
        sample.update(status='observed',csv=subprocess.check_output(argv,text=True,timeout=5).strip())
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
        sample.update(status='missing',error=repr(exc),command=argv)
    sample['elapsed_seconds']=time.monotonic()-started
    with Path(path).open('a') as f: f.write(json.dumps(sample)+'\n')
def cleanup(names,router,deadline):
    receipts=[]
    def left(cap): return max(0.1,min(cap,deadline-time.monotonic()))
    if router is not None and router.poll() is None:
        try:
            router.terminate()
            try: router.wait(timeout=left(5))
            except subprocess.TimeoutExpired: router.kill();router.wait(timeout=left(5))
        except Exception as e: receipts.append({'router_error':repr(e)})
    for name in names:
        try:
            q=subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=left(35))
            receipts.append({'name':name,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
        except Exception as e: receipts.append({'name':name,'error':repr(e)})
    try:
        until=min(time.monotonic()+60,deadline)
        while processes() and time.monotonic()<until: time.sleep(min(2,max(0.01,until-time.monotonic())))
        return {'containers':receipts,'gpu_processes_after':processes(),'running_containers_after':cmd(['docker','ps','--format','{{.Names}}'])}
    except Exception as e:return {'containers':receipts,'gpu_processes_after':'UNKNOWN','running_containers_after':'UNKNOWN','error':repr(e)}

def signal_stop(sig,frame): raise RuntimeError('Controller interrupted by signal '+str(sig))

def run(manifest_path,review):
    manifest=json.loads(manifest_path.read_text()); out=Path(manifest['output']);out.mkdir(exist_ok=False,parents=True)
    hashes=manifest['input_sha256'] | {str(manifest_path):sha(manifest_path),str(review):sha(review),str(Path(__file__).resolve()):sha(__file__),str(Path(__file__).with_name('watchdog.py')):sha(Path(__file__).with_name('watchdog.py'))}
    if unchanged(hashes): raise RuntimeError('Input hash mismatch')
    write(out/'frozen-inputs.json',hashes)
    signal.signal(signal.SIGTERM,signal_stop); signal.signal(signal.SIGINT,signal_stop)
    with Path('/tmp/autoresearch-h200-gpu.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if processes() or cmd(['docker','ps','-q']): raise RuntimeError('Node not idle')
        if any(k.startswith('DSV41_ROUTER_') for k in __import__('os').environ):raise RuntimeError('Unexpected router environment override')
        for port in (8000,8100,8101):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1',port))==0: raise RuntimeError('Required service port occupied: '+str(port))
        inventory=cmd(['nvidia-smi','--query-gpu=index,uuid,name','--format=csv,noheader'])
        if inventory!=manifest['gpu_inventory']: raise RuntimeError('GPU inventory mismatch')
        record={'started_at_utc':now(),'state':'running','arms':{},'allocated_gpus':8,'service_attempts_consumed':0,'GPU_inventory':inventory,'manifest':str(manifest_path),'review':str(review),'limits':{'work_seconds':4200,'hard_seconds':4500,'startup_native_seconds_per_arm':2400,'lifecycle_seconds_per_arm':300,'review_seconds_per_arm':180,'traffic_seconds_per_arm':600}}
        start=time.monotonic();campaign_start=start;work_deadline=start+4200;hard_deadline=start+4500
        if manifest['prior_C25_GPU_hours']+10>22:raise RuntimeError('Cumulative C25 budget would exceed22 GPU-hours')
        record['prior_C25_GPU_hours']=manifest['prior_C25_GPU_hours'];record['total_C25_GPU_hours_ceiling']=22
        record['scope']='actual real-request proposal-stage diagnostic; not unprofiled service ITL'
        origin=datetime.datetime.fromisoformat(record['started_at_utc'])
        record['work_deadline_utc']=(origin+datetime.timedelta(seconds=4200)).isoformat();record['hard_deadline_utc']=(origin+datetime.timedelta(seconds=4500)).isoformat()
        active_names=[];router=None
        owned_processes=[]
        write(out/'owned-processes.json',{'processes':owned_processes})
        def register_owned(process,role):
            item=identity(process.pid);item.update(role=role,pgid=__import__('os').getpgid(process.pid))
            if item['pgid']!=process.pid:raise RuntimeError('Owned child lacks isolated process group')
            owned_processes.append(item);write(out/'owned-processes.json',{'processes':owned_processes})
        watchargv=['python3',str(Path(__file__).with_name('watchdog.py')),'--parent',str(__import__('os').getpid()),'--ticks',identity(__import__('os').getpid())['start_ticks'],'--start',str(campaign_start),'--receipt',str(out/'watchdog.jsonl'),'--owned-processes',str(out/'owned-processes.json')]
        for arm in ('B','A'):
            for name in manifest['arms'][arm]['names']:watchargv.extend(['--name',name])
        watchdog=subprocess.Popen(watchargv,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        write(out/'execution.json',record); journal('live_pilot_started',receipt=str(out/'execution.json'))
        try:
            for arm in ('B','A'):
                if time.monotonic()>=work_deadline:raise TimeoutError('No remaining arm budget')
                if unchanged(hashes): raise RuntimeError('Frozen inputs changed before arm '+arm)
                if arm=='A':
                    required=record['arms']['B']['startup_native_seconds']+300+180+600+120
                    record['A_budget_preflight']={'remaining_work_seconds':work_deadline-time.monotonic(),'required_seconds':required,'basis':'observed B startup/native +300 lifecycle +180 review +600 traffic +120 reserve; no timing outcome selection'}
                    if work_deadline-time.monotonic()<required:raise TimeoutError('Insufficient remaining budget for a defensible A cold start')
                spec=manifest['arms'][arm]; armout=out/arm; armout.mkdir(); (armout/'observations').mkdir();(armout/'live-observations').mkdir();(armout/'pycache').mkdir()
                for rep in (0,1):
                    (armout/'observations'/('replica'+str(rep))).mkdir();(armout/'live-observations'/('replica'+str(rep))).mkdir()
                ar={'started_at_utc':now(),'state':'starting','commands':spec['commands'],'container_names':spec['names'],'no_prior_client_requests':True}
                record['arms'][arm]=ar;write(out/'execution.json',record)
                ast=time.monotonic(); startup_deadline=min(ast+2400,work_deadline)
                children=[];logs=[];active_names=[];router=None
                try:
                    telemetry(armout/'gpu-telemetry.jsonl')
                    for i,argv in enumerate(spec['commands']):
                        log=(armout/('replica'+str(i)+'.log')).open('w');logs.append(log)
                        active_names.append(spec['names'][i]);p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(p);register_owned(p,'backend-docker-'+arm+'-'+str(i))
                    last=0
                    while True:
                        if time.monotonic()>=startup_deadline: raise TimeoutError('Startup/native deadline '+arm)
                        if any(p.poll() is not None for p in children): raise RuntimeError('Backend exited '+arm)
                        paths=[armout/'observations'/('replica'+str(rep))/('rank'+str(rank)+'.json') for rep in (0,1) for rank in range(4)]
                        existing=[json.loads(p.read_text()) for p in paths if p.exists()]
                        starts=list((armout/'observations').glob('replica*/rank*.started.json'))
                        for marker in starts:
                            final=marker.with_name(marker.name.replace('.started.json','.json'))
                            if not final.exists() and time.time()-json.loads(marker.read_text())['started_unix_s']>480:raise TimeoutError('Native collection eight-minute cap '+str(marker))
                        if any(x.get('status')=='failed' for x in existing): raise RuntimeError('Native observer failed '+arm)
                        if len(existing)==8:
                            for path in paths:
                                x=json.loads(path.read_text());rep=int(path.parent.name.removeprefix('replica'));rank=int(path.stem.removeprefix('rank'))
                                expected={'status':'passed','restored':True,'arm':arm,'run_id':manifest['run_id'],'replica':rep,'rank':rank,'native_oracle_passed':True,'capture_attestation_passed':True,'timed_samples':960}
                                if any(x.get(k)!=v for k,v in expected.items()):raise RuntimeError('Native receipt qualification/identity failure '+str(path))
                                gpu_uuid=manifest['gpu_inventory'].splitlines()[rep*4+rank].split(',')[1].strip()
                                if str(x.get('gpu_uuid','')).lower().removeprefix('gpu-')!=gpu_uuid.lower().removeprefix('gpu-'):raise RuntimeError('Observer GPU identity mismatch')
                                observer=next(row for row in spec['mounts'] if row['destination'].endswith('/c25_native_observer.py'))
                                if x.get('observer_sha256')!=observer['sha256'] or x.get('reference_sha256')!='97bcfaa655c6d4a5ecdfb17ab87b80547e8216b9d15a91c341798ebbb558f146':raise RuntimeError('Observer/reference source identity mismatch')
                            if all(health(url) for url in manifest['backend_urls']):
                                live_source=next(row for row in spec['mounts'] if row['destination'].endswith('/c25_live_observer.py'))
                                for path in paths:
                                    native=json.loads(path.read_text());rep=native['replica'];rank=native['rank']
                                    live=json.loads((armout/'live-observations'/('replica'+str(rep))/('rank'+str(rank)+'.ready.json')).read_text())
                                    expected_live={k:native[k] for k in ('arm','run_id','replica','rank','pid','pid_start_ticks','gpu_uuid')}
                                    expected_live.update(status='ready',observer_sha256=live_source['sha256'])
                                    if any(str(live.get(k))!=str(v) for k,v in expected_live.items()):raise RuntimeError('Live observer readiness/worker identity mismatch')
                                    if live['initialization']['capacity']!=65536 or live['initialization']['events']!=131072:raise RuntimeError('Live event pool capacity mismatch')
                                break
                        if time.monotonic()-last>=15:
                            telemetry(armout/'gpu-telemetry.jsonl');last=time.monotonic()
                            ar['elapsed_seconds']=time.monotonic()-ast;ar['observer_receipts']=len(existing);write(out/'execution.json',record)
                            print(json.dumps({'time_utc':now(),'arm':arm,'elapsed_seconds':round(ar['elapsed_seconds']),'observer_receipts':len(existing)}),flush=True)
                        time.sleep(2)
                    native_finished=time.monotonic();post_ready_deadline=min(native_finished+1080,work_deadline);ar['native_ready_at_utc']=now();ar['observer_receipts']=8;ar['startup_native_seconds']=native_finished-ast;ar['post_readiness_limit_seconds']=1080
                    with (armout/'router.log').open('w') as rl:
                        router=subprocess.Popen(manifest['router_command'],stdout=rl,stderr=subprocess.STDOUT,start_new_session=True)
                        register_owned(router,'router-'+arm)
                        ready_deadline=min(time.monotonic()+30,work_deadline)
                        while not health(manifest['router_url']):
                            if router.poll() is not None or time.monotonic()>ready_deadline: raise RuntimeError('Router not ready')
                            time.sleep(1)
                        ident={'time_utc':now(),'arm':arm,'run_id':manifest['run_id'],'fresh_exclusive_start':True,'fresh_exclusive_service':True,'no_prior_client_requests':True,'native_receipts_passed_restored':True,'containers':[],'router':identity(router.pid),'gpu_processes':processes()}
                        for name in active_names:
                            detail=json.loads(cmd(['docker','inspect',name]))[0]
                            ident['containers'].append({'name':name,'image':detail['Image'],'config_image':detail['Config']['Image'],'mounts':detail['Mounts'],'state':detail['State'],**container_identity(name,detail)})
                        ident['workers']=[]
                        for rep,name in enumerate(active_names):
                            expected_workers=[json.loads((armout/'observations'/('replica'+str(rep))/('rank'+str(rank)+'.json')).read_text()) for rank in range(4)]
                            worker_code="import json;from pathlib import Path; pids="+repr([x['pid'] for x in expected_workers])+";print(json.dumps({str(pid):(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19] for pid in pids}))"
                            actual=json.loads(cmd(['docker','exec',name,'python3','-c',worker_code]))
                            for worker in expected_workers:
                                if actual[str(worker['pid'])]!=str(worker['pid_start_ticks']):raise RuntimeError('Worker PID/start tick changed before traffic')
                                ident['workers'].append({'replica':rep,'rank':worker['rank'],'container_pid':worker['pid'],'start_ticks':actual[str(worker['pid'])],'gpu_uuid':worker['gpu_uuid']})
                        write(armout/'identity.json',ident)
                        ar['state']='lifecycle';write(out/'execution.json',record)
                        with (armout/'lifecycle.log').open('w') as lf:
                            lifecycle=subprocess.Popen(spec['lifecycle_command'],stdout=lf,stderr=subprocess.STDOUT,start_new_session=True)
                            register_owned(lifecycle,'lifecycle-'+arm)
                            ld=min(time.monotonic()+300,post_ready_deadline)
                            try:
                                while lifecycle.poll() is None:
                                    if time.monotonic()>=ld:raise TimeoutError('Lifecycle deadline')
                                    telemetry(armout/'gpu-telemetry.jsonl');time.sleep(2)
                                ar['lifecycle_exit_code']=lifecycle.returncode
                            finally:
                                if lifecycle.poll() is None:
                                    __import__('os').killpg(lifecycle.pid,signal.SIGTERM)
                                    try:lifecycle.wait(timeout=5)
                                    except subprocess.TimeoutExpired:__import__('os').killpg(lifecycle.pid,signal.SIGKILL);lifecycle.wait(timeout=5)
                        if ar['lifecycle_exit_code']!=0:raise RuntimeError('Scoped lifecycle failed '+arm)
                        lifecycle_path=armout/'controlled-traffic.json';lifecycle_receipt=json.loads(lifecycle_path.read_text())
                        if lifecycle_receipt.get('scoped_observable_checks')!='pass' or lifecycle_receipt.get('status') not in ('pending_external_abort_acceptance','inconclusive_natural_stop'):
                            raise RuntimeError('Lifecycle receipt not scoped-qualified '+arm)
                        prefix={'arm':arm,'run_id':manifest['run_id'],'time_utc':now(),'identity_path':str(armout/'identity.json'),'workers':ident['workers'],'containers':[{'name':x['name'],'container_id':x['container_id'],'host_process':x['host_process']} for x in ident['containers']],'identity_sha256':sha(armout/'identity.json'),'lifecycle_receipt_sha256':sha(lifecycle_path),'logs':[]}
                        for rep in range(2):
                            source=armout/('replica'+str(rep)+'.log');size=source.stat().st_size
                            with source.open('rb') as reader:data=reader.read(size)
                            if len(data)!=size:raise RuntimeError('Incomplete log prefix snapshot')
                            end=data.rfind(b'\n')+1
                            if end==0:raise RuntimeError('No complete backend log line in prefix')
                            data=data[:end]
                            target=armout/('replica'+str(rep)+'.lifecycle-prefix.log');target.write_bytes(data)
                            prefix['logs'].append({'replica':rep,'original_log_path':str(source),'source_size_at_snapshot':size,'byte_length':len(data),'path':str(target),'sha256':sha(target)})
                        prefix_path=armout/'lifecycle-prefix-attestation.json';write(prefix_path,prefix)
                        ar['state']='awaiting_lifecycle_prefix_review';ar['lifecycle_status']=lifecycle_receipt['status'];write(out/'execution.json',record)
                        journal('live_lifecycle_prefix_ready',arm=arm,run_id=manifest['run_id'],attestation=str(prefix_path))
                        approval_path=armout/'lifecycle-prefix-review.json';rd=min(time.monotonic()+180,post_ready_deadline)
                        while not approval_path.exists():
                            if time.monotonic()>=rd:raise TimeoutError('Lifecycle prefix review deadline')
                            if any(p.poll() is not None for p in children):raise RuntimeError('Backend exited during lifecycle review')
                            time.sleep(1)
                        approval=json.loads(approval_path.read_text())
                        expected_approval={'schema_version':1,'status':'accepted','arm':arm,'run_id':manifest['run_id'],'identity_sha256':prefix['identity_sha256'],'lifecycle_receipt_sha256':prefix['lifecycle_receipt_sha256'],'allowed_next_phase':'live_profiling','log_prefix_attestation':{'path':str(prefix_path),'sha256':sha(prefix_path)}}
                        if any(approval.get(k)!=v for k,v in expected_approval.items()):raise RuntimeError('Lifecycle approval binding mismatch')
                        ar['lifecycle_approval_sha256']=sha(approval_path)
                        remaining=min(600,post_ready_deadline-time.monotonic())
                        if remaining<=0: raise TimeoutError('No traffic budget remaining')
                        ar['state']='controlled_traffic';write(out/'execution.json',record)
                        with (armout/'traffic.log').open('w') as tf:
                            traffic=subprocess.Popen(spec['traffic_command'],stdout=tf,stderr=subprocess.STDOUT,start_new_session=True)
                            register_owned(traffic,'traffic-'+arm)
                            td=time.monotonic()+remaining
                            try:
                                while traffic.poll() is None:
                                    if time.monotonic()>td: raise TimeoutError('Traffic deadline')
                                    telemetry(armout/'gpu-telemetry.jsonl');time.sleep(5)
                                ar['traffic_exit_code']=traffic.returncode
                            finally:
                                if traffic.poll() is None:
                                    __import__('os').killpg(traffic.pid,signal.SIGTERM)
                                    try: traffic.wait(timeout=5)
                                    except subprocess.TimeoutExpired: __import__('os').killpg(traffic.pid,signal.SIGKILL);traffic.wait(timeout=5)
                        if ar['traffic_exit_code']!=0: raise RuntimeError('Controlled traffic failed '+arm)
                        traffic_receipt=json.loads((armout/'live-traffic.json').read_text())
                        if traffic_receipt.get('status')!='passed' or traffic_receipt.get('arm')!=arm or traffic_receipt.get('run_id')!=manifest['run_id']:raise RuntimeError('Real-request traffic receipt is not qualified')
                        ar['traffic_status']=traffic_receipt['status'];ar['integration_basis']={'path':str(approval_path),'sha256':sha(approval_path)};ar['historical_native_review']=manifest['native_lifecycle_review']
                    ar['state']='completed'
                except BaseException as e:
                    ar['state']='failed'; ar['error']=repr(e); raise
                finally:
                    ar['cleanup']=cleanup(active_names,router,hard_deadline);active_names=[];router=None
                    for p in children:
                        try: p.wait(timeout=10)
                        except subprocess.TimeoutExpired: p.terminate()
                    for f in logs: f.close()
                    attestation={'time_utc':now(),'arm':arm,'run_id':manifest['run_id'],'collection':'root-owned Docker foreground stdout/stderr logs, closed after container cleanup','logs':[{'replica':i,'container_name':spec['names'][i],'path':str(armout/('replica'+str(i)+'.log')),'sha256':sha(armout/('replica'+str(i)+'.log'))} for i in range(len(logs))],'input_mounts':spec['mounts']}
                    for name in ('identity.json','controlled-traffic.json','lifecycle-prefix-attestation.json','lifecycle-prefix-review.json','live-traffic.json'):
                        if (armout/name).exists():attestation[name]={'path':str(armout/name),'sha256':sha(armout/name)}
                    prefix_path=armout/'lifecycle-prefix-attestation.json'
                    if prefix_path.exists():
                        ar['log_prefix_preserved']=True
                        for item in json.loads(prefix_path.read_text())['logs']:
                            with Path(item['original_log_path']).open('rb') as f:closed_prefix=f.read(item['byte_length'])
                            if hashlib.sha256(closed_prefix).hexdigest()!=item['sha256'] or sha(item['path'])!=item['sha256']:
                                ar['log_prefix_preserved']=False
                        attestation['lifecycle_prefix_preserved']=ar['log_prefix_preserved']
                    write(armout/'abort-log-attestation.json',attestation)
                    ar['wall_seconds']=time.monotonic()-ast;ar['allocated_GPU_hours']=ar['wall_seconds']*8/3600;ar['finished_at_utc']=now()
                    telemetry(armout/'gpu-telemetry.jsonl');write(out/'execution.json',record)
                if ar.get('log_prefix_preserved') is False:raise RuntimeError('Closed backend log prefix mismatch')
                if ar['cleanup']['gpu_processes_after'] or ar['cleanup']['running_containers_after']: raise RuntimeError('Cleanup did not restore idle node')
                if time.monotonic()>=work_deadline: raise TimeoutError('Shared work deadline')
            record['state']='completed'
        except BaseException as e:
            record['state']='failed';record['error']=repr(e);record['traceback']=traceback.format_exc()
        finally:
            if active_names or router: record['emergency_cleanup']=cleanup(active_names,router,hard_deadline)
            record['wall_seconds']=time.monotonic()-start;record['allocated_GPU_hours']=record['wall_seconds']*8/3600
            record['finished_at_utc']=now();record['changed_inputs']=unchanged(hashes);record['gpu_processes_after']=processes();record['running_containers_after']=cmd(['docker','ps','--format','{{.Names}}']);record['hard_cap_exceeded']=time.monotonic()>hard_deadline
            record['owned_children_alive']=[]
            for child in owned_processes:
                proc=Path('/proc')/str(child['pid'])/'stat'
                try:
                    if proc.exists() and proc.read_text().rsplit(')',1)[1].split()[19]==child['start_ticks']:record['owned_children_alive'].append(child)
                except FileNotFoundError:pass
            safe_to_disarm=not record['gpu_processes_after'] and not record['running_containers_after'] and not record['owned_children_alive']
            record['watchdog_disarmed_after_verified_idle']=safe_to_disarm
            if safe_to_disarm:
                watchdog.terminate()
                try:watchdog.wait(timeout=5)
                except subprocess.TimeoutExpired:watchdog.kill();watchdog.wait(timeout=5)
            else:
                record['watchdog_retained_for_emergency_cleanup']=True
            write(out/'execution.json',record);journal('live_pilot_finished',state=record['state'],GPU_hours=record['allocated_GPU_hours'],receipt=str(out/'execution.json'))
        print(json.dumps(record,indent=2),flush=True)
        return 0 if record['state']=='completed' and not record['changed_inputs'] and not record['gpu_processes_after'] and not record['hard_cap_exceeded'] and record['watchdog_disarmed_after_verified_idle'] else 1
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--review',type=Path,required=True);a=ap.parse_args();raise SystemExit(run(a.manifest.resolve(),a.review.resolve()))

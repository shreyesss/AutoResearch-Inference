"""Independent root-owned deadline enforcement for one separately frozen real-request allocation."""
import argparse
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ap=argparse.ArgumentParser();ap.add_argument('--parent',type=int,required=True);ap.add_argument('--ticks',required=True);ap.add_argument('--start',type=float,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--name',action='append',required=True);ap.add_argument('--owned-processes',type=Path,required=True);a=ap.parse_args()
def alive():
    try:return (Path('/proc')/str(a.parent)/'stat').read_text().rsplit(')',1)[1].split()[19]==a.ticks
    except (FileNotFoundError,ProcessLookupError):return False
def log(**data):
    with a.receipt.open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**data})+'\n')
def cleanup_children():
    results=[]
    try:items=json.loads(a.owned_processes.read_text())['processes']
    except Exception as e:return [{'read_error':repr(e)}]
    for item in items:
        try:
            pid=item['pid'];stat=Path('/proc')/str(pid)/'stat'
            if not stat.exists() or stat.read_text().rsplit(')',1)[1].split()[19]!=item['start_ticks']:continue
            if item['pgid']!=pid or os.getpgid(pid)!=pid:raise RuntimeError('Unattested process group')
            os.killpg(pid,signal.SIGTERM)
            until=time.monotonic()+3
            while stat.exists() and time.monotonic()<until:time.sleep(0.1)
            if stat.exists() and stat.read_text().rsplit(')',1)[1].split()[19]==item['start_ticks']:os.killpg(pid,signal.SIGKILL)
            results.append({'pid':pid,'role':item['role'],'terminated_owned_group':True})
        except ProcessLookupError:pass
        except Exception as e:results.append({'pid':item.get('pid'),'error':repr(e)})
    return results
def wait_until(offset):
    while time.monotonic()<a.start+offset:
        if not alive():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:log(action='parent_disappeared_cleanup',children=cleanup_children(),results=list(pool.map(remove,a.name)))
            raise SystemExit(0)
        time.sleep(max(0,min(2,a.start+offset-time.monotonic())))
def remove(name):
    try:
        q=subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=35)
        return {'name':name,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr}
    except Exception as e:return {'name':name,'error':repr(e)}
wait_until(4200)
if alive():os.kill(a.parent,signal.SIGTERM);log(action='work_deadline_SIGTERM')
# Reserve 90 seconds for Docker/kernel cleanup before the outer allocation cap.
wait_until(4410)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:log(action='owned_container_deadline_cleanup',children=cleanup_children(),results=list(pool.map(remove,a.name)))
wait_until(4500)
if alive():os.kill(a.parent,signal.SIGKILL);log(action='hard_deadline_SIGKILL')

"""Read-only hardware/container/config evidence; never emit environment or requests."""
import datetime,json,subprocess

def run(args):
 p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 return p.returncode,p.stdout
out={'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':run(['hostname'])[1].strip(),'gpus':run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'])[1].splitlines(),'containers':[]}
for i in [0,1]:
 name='dsv41-h200-vllm-latency-2xdep4-sla-'+str(i)
 code,raw=run(['docker','inspect',name])
 if code:continue
 d=json.loads(raw)[0]
 rec={'name':name,'image_id':d['Image'],'started_at':d['State']['StartedAt'],'state':d['State']['Status'],'args':d['Config']['Cmd']}
 # Docker commonly writes logs to stderr; use a filtering stream to avoid saving request data.
 p=subprocess.Popen(['docker','logs','--tail','100000',name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 rec['resolved_engram_lines']=[]
 for line in p.stdout:
  if 'config/vllm.py:' in line and 'Resolved Engram configuration: EngramConfig(' in line:rec['resolved_engram_lines'].append(line.strip())
 p.wait(timeout=30)
 rec['resolved_engram_lines']=list(dict.fromkeys(rec['resolved_engram_lines']))[:8]
 rc,status=run(['curl','-sS','--max-time','5','-o','/dev/null','-w','%{http_code}','http://127.0.0.1:'+str(8100+i)+'/health'])
 rec['health_http_status']=status;rec['health_curl_exit']=rc
 out['containers'].append(rec)
print(json.dumps(out,indent=2))

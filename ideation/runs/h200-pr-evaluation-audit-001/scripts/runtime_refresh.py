import datetime,json,subprocess
def run(args):
 p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25);return dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
names=['dsv41-h200-vllm-latency-2xdep4-sla-0','dsv41-h200-vllm-latency-2xdep4-sla-1']
out={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'health':{},'containers':{}}
for port in [8100,8101]:out['health'][str(port)]=run(['curl','-sS','--max-time','5','-o','/dev/null','-w','%{http_code}','http://127.0.0.1:'+str(port)+'/health'])
for name in names:
 s=run(['docker','inspect','--format','{{json .State}}',name]);out['containers'][name]={'state':s}
 logs=run(['docker','logs','--tail','100',name]);lines=(logs['stdout']+'\n'+logs['stderr']).splitlines();out['containers'][name]['startup_status_lines']=[l for l in lines if any(k in l.lower() for k in ['error','loading','loaded','ready','application startup','traceback','out of memory','capturing','compiling'])][-20:]
print(json.dumps(out,indent=2))

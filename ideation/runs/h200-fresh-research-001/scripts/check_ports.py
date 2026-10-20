"""Recheck downloaded PR Python hunks against captured source; never touch serving.

Usage: .venv-research/bin/python runs/h200-fresh-research-001/scripts/check_ports.py
Writes a new patch-application-repeat.json; the original checks remain immutable.
Native dependencies, CMake and tests are deliberately outside this check.
"""
import json,re,shutil,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
output=R/'baseline/patch-application-repeat.json'
if output.exists():raise SystemExit('Choose a new output path; prior checks are immutable')
results=[]
for number in [58818,58984,61767,61461,59488,62000,62463,59204,61875]:
 p=R/'primary'/f'vllm-project--vllm--{number}'/'changes.patch'
 pieces=re.split(r'(?=^From [0-9a-f]{40} Mon Sep 17)',p.read_text(),flags=re.M)
 pieces=[x for x in pieces if x.strip()]
 stages=[]
 with tempfile.TemporaryDirectory(prefix='h200-port-check-') as tmp:
  root=Path(tmp);shutil.copytree(R/'baseline/source',root,dirs_exist_ok=True)
  subprocess.run(['git','init','-q',str(root)],check=True,capture_output=True)
  for i,piece in enumerate(pieces):
   part=root/'candidate.patch';part.write_text(piece)
   checked=subprocess.run(['git','apply','--check','--verbose','--include=vllm/*',str(part)],cwd=root,capture_output=True,text=True)
   details=checked.stdout+checked.stderr
   code=checked.returncode
   if code==0 and 'Checking patch vllm/' not in details:
    code=1;details+='\nNo vllm hunks checked; refusing a vacuous success.'
   stages.append({'commit_index':i,'sha':piece.splitlines()[0].split()[1],'exit_code':code,'details':details})
   if code:break
   subprocess.run(['git','apply','--include=vllm/*',str(part)],cwd=root,check=True,capture_output=True)
 results.append({'pr':number,'all_vllm_hunks_apply_in_order':len(stages)==len(pieces) and all(x['exit_code']==0 for x in stages),'commits_in_patch':len(pieces),'stages':stages,'scope':'vllm source hunks only, applied sequentially to disposable copy; cmake/tests/native dependencies excluded; no serving mutation'})
output.write_text(json.dumps(results,indent=2))
print(output)

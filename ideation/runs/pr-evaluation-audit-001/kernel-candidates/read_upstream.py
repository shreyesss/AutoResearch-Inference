import json
from pathlib import Path
from ideation.store import Store
from ideation.github import GitHub
p=Path('runs/pr-evaluation-audit-001/kernel-candidates');s=Store('data/corpus.sqlite')
items={'deepseek-ai/FlashMLA':[227,229,196,187], 'deepseek-ai/DeepGEMM':[381,386,394,404,436,451,478,471], 'SemiAnalysisAI/InferenceX':[3095,3181], 'vllm-project/recipes':[1002], 'flashinfer-ai/flashinfer':[5523,6059]}
out=[]
for repo,nums in items.items():
 gh=GitHub(s,repo)
 for n in nums:
  try:
   d,headers=gh.get('pulls/'+str(n));out.append(d);print(repo,n,d['state'],d.get('merged_at'),d['title'],flush=True)
  except Exception as e:out.append({'repo':repo,'number':n,'error':str(e)});print('ERROR',repo,n,type(e).__name__,flush=True)
  (p/'upstream-records.json').write_text(json.dumps(out,indent=2))

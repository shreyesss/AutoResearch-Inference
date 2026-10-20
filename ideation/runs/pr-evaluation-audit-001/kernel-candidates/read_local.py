import json
from pathlib import Path
from ideation.store import Store
s=Store('data/corpus.sqlite');p=Path('runs/pr-evaluation-audit-001/kernel-candidates');p.mkdir(parents=True,exist_ok=True)
nums=[61039,60468,60613,62467,60802,57977,58818,59849,60938,62359,61971,62011,61868,57843,58559,60936,61371,61149,57218,62269,61530,62091,59922,60220,57575,56989,59327,59923]
a=[]
for n in nums:
 d=s.get(f'github:vllm-project/vllm:{n}')
 if d:a.append(d);print(n,d['title'],'STATE',d['state'],d['merged_at'],'HEAD',(d['metadata'].get('head')or{}).get('sha'),'\n',d['body'][:6500],'\n',flush=True)
 else:print('MISSING',n)
(p/'local-records.json').write_text(json.dumps(a,indent=2))

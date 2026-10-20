import json,random
from pathlib import Path
from ideation.store import Store
from ideation.toolbox import registry
p=Path('runs/frontier-exploration-001/kernels');p.mkdir(parents=True,exist_ok=True)
s=Store('data/corpus.sqlite');t=registry(s)
queries=['quantize dispatch','communication overlap','CUDA graph staging','activation lifetime','DeepSeek gather quantization','MegaMoE scale','alltoall SM','DeepEP block scale']
r=random.Random(20261020);r.shuffle(queries)
results=[]
for q in queries:
 rows=t.call('github.search',query=q,match='all',after='2026-08-01',limit=6)
 results.append({'query':q,'after':'2026-08-01','date_field':'updated_at','results':rows})
 print(q,[(x['metadata']['number'],x['title']) for x in rows],flush=True)
(p/'search.json').write_text(json.dumps({'seed':20261020,'method':'seeded permutation of mechanism-oriented queries; all-token matching; updated date filter','queries':results},indent=2))
for n in [62541,62073,61962,54683]:
 d=t.call('github.get',number=n);(p/f'{n}.json').write_text(json.dumps(d,indent=2));print('SEED',n,d['document']['body'][:5500],flush=True)

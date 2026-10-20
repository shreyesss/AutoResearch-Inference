"""Exercise existing cached keyword/date retrieval; no GitHub API traffic."""
import json
from pathlib import Path
from ideation.store import Store, now
ROOT=Path('runs/h200-pr-evaluation-audit-001')
s=Store('data/corpus.sqlite')
queries=[('hopper','moe'),('h200','dspark'),('sm90','indexer'),('deepseek','padding'),('dspark','prefix'),('engram','numa'),('dp','metadata'),('candidate','decode')]
results=[]
for a,b in queries:
 q=a+' '+b
 hits=s.search(q,match='all',after='2026-08-01',date_field='updated_at',id_prefix='github:vllm-project/vllm:',limit=25)
 results.append({'query':q,'match':'all','after':'2026-08-01','date_field':'updated_at','hits':[dict((k,x.get(k)) for k in ['id','title','url','updated_at','kind','rank']) for x in hits]})
out={'captured_at':now(),'source':'controller SQLite cache; network-free retrieval','ranking':'FTS5 BM25(title5/body1/tags2), updated_at tie-break; lower rank is better. Retrieval rank is not experiment priority.','documents':s.db.execute('SELECT COUNT(*) FROM documents').fetchone()[0],'queries':results}
(ROOT/'search-results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'documents':out['documents'],'queries':len(results),'hits_per_query':[len(x['hits']) for x in results]}))

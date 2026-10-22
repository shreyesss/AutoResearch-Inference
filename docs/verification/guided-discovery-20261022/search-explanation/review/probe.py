from pathlib import Path
import tempfile,json,sqlite3,hashlib
from ideation.store import Store
H=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='search-explain-independent-')as tmp:
 p=Path(tmp)/'db.sqlite';w=Store(p)
 def doc(n):return {'id':f'github:a/b:{n}','kind':'pr','source':'test','title':'needle','body':'needle','url':f'local:{n}'}
 w.put(doc(1));w.db.commit();r=Store(p,readonly=True)
 original=r.decode;committed=[]
 def decode(row):
  if not committed:w.put(doc(2));w.db.commit();committed.append(True)
  return original(row)
 r.decode=decode
 out=r.search('needle',explain=True)
 assert len(out['hits'])==out['total_matches']==out['source_scope']['documents']==1
 assert not r.db.in_transaction
 r.decode=original
 fresh=r.search('needle',explain=True);assert fresh['total_matches']==2
 kinds=[]
 for kind in ['pull_request',"pr' OR 1=1 --",'PR',' pr ']:
  x=r.search('needle',kind=kind,explain=True);assert x['hits']==[] and x['filters']['kind']==kind and x['warnings'][0]['code']=='kind_absent_in_scope';kinds.append(kind)
 paging=[]
 for limit,expected in [(0,1),(-2,1),(1000,500)]:
  x=r.search('needle',limit=limit,offset=2,explain=True);assert x['limit']==expected and not x['hits'] and x['next_offset'] is None and x['warnings'][0]['code']=='offset_past_matches';paging.append([limit,expected])
 for offset in [-1,True,1.2]:
  try:r.search('needle',offset=offset,explain=True)
  except ValueError:pass
  else:raise AssertionError('invalid offset accepted')
 r.db.execute('BEGIN');r.search('',explain=True);assert r.db.in_transaction;r.db.rollback()
 # Existing caller savepoint retains its identity and rollback semantics.
 w.db.execute('SAVEPOINT search_explanation');w.db.execute("UPDATE documents SET state='pending'")
 assert w.search('',state='pending',explain=True)['total_matches']==2
 w.db.execute('ROLLBACK TO search_explanation');w.db.execute('RELEASE search_explanation')
 assert w.search('',state='pending',explain=True)['total_matches']==0
 # Explain failure releases only its own savepoint, preserves caller pending work.
 w.db.execute("UPDATE documents SET state='pending' WHERE id='github:a/b:1'")
 old=w.decode
 def broken(row):raise ValueError('synthetic decode failure')
 w.decode=broken
 try:w.search('',explain=True)
 except ValueError:pass
 else:raise AssertionError('failure expected')
 assert w.db.in_transaction;w.decode=old;w.db.rollback()
 assert w.search('',state='pending',explain=True)['total_matches']==0
 r.db.close();w.db.close()
 absent=Path(tmp)/'absent.sqlite'
 try:Store(absent,readonly=True)
 except sqlite3.OperationalError:pass
 else:raise AssertionError('missing corpus silently created')
 assert not absent.exists()
 result={'snapshot_concurrent_commit':{'first_hits_count_scope':1,'next_call_total':2,'same_snapshot':True},'kind_literal_controls':kinds,'limit_clamps':paging,'invalid_offsets_rejected':3,'caller_transaction_preserved':True,'same_named_savepoint_preserved':True,'decode_failure_preserves_pending_caller_rollback':True,'absent_readonly_corpus_not_created':True,'scope':'Temporary local SQLite only; no canonical, network, GPU or retrieval-quality claim.'}
(H/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

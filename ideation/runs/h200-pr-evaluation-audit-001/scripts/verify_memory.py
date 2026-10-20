import hashlib,json,sqlite3
from pathlib import Path
root=Path('runs/h200-pr-evaluation-audit-001')
db=sqlite3.connect('file:data/hypotheses.sqlite?mode=ro',uri=True)
run=str(root)
events=dict(db.execute('SELECT e.type,count(*) FROM events e JOIN hypotheses h ON h.id=e.hypothesis_id WHERE h.run=? GROUP BY e.type',(run,)))
counts={'hypotheses':db.execute('SELECT count(*) FROM hypotheses WHERE run=?',(run,)).fetchone()[0],'tests':db.execute('SELECT count(*) FROM tests t JOIN hypotheses h ON h.id=t.hypothesis_id WHERE h.run=?',(run,)).fetchone()[0],'parent_edges':db.execute("SELECT count(*) FROM edges e JOIN hypotheses h ON h.id=e.src WHERE h.run=? AND e.relation='derived_from'",(run,)).fetchone()[0]}
protocol_hash=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest()
plans=[json.loads(x[0]) for x in db.execute('SELECT n.data FROM nodes n JOIN tests t ON t.id=n.id JOIN hypotheses h ON h.id=t.hypothesis_id WHERE h.run=?',(run,))]
# The node's exact stored shape is retained for transparent inspection.
plan_hashes=[]
for p in plans:
 def collect(v):
  if isinstance(v,dict):
   if 'protocol_sha256' in v:plan_hashes.append(v['protocol_sha256'])
   for x in v.values():collect(x)
  elif isinstance(v,list):
   for x in v:collect(x)
 collect(p)
assert counts=={'hypotheses':26,'tests':26,'parent_edges':18},counts
assert len(plan_hashes)==26 and set(plan_hashes)=={protocol_hash}
assert not any('started' in k or 'result' in k for k in events),events
out={'run':run,'counts':counts,'events':events,'protocol_sha256':protocol_hash,'all_stored_test_protocol_hashes_match':True,'gpu_tests_started':0,'results_recorded':0}
(root/'memory-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sqlite3
from ideation.store import Store, content_fingerprint, _RETRIEVAL_METADATA
from ideation.hypothesis_memory import HypothesisMemory
from ideation.hypothesis_artifacts import resolve_artifact
b=Path('/Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001')
c=Path('/Users/shreyas/.local/share/inference-autoresearch')
out=b/'root-checkpoint30/canonical-readback.json'
assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
db=sqlite3.connect((c/'research/corpus.sqlite').as_uri()+'?mode=ro',uri=True);db.execute('BEGIN')
hdb=sqlite3.connect((c/'research/hypotheses.sqlite').as_uri()+'?mode=ro',uri=True);hdb.row_factory=sqlite3.Row;hdb.execute('BEGIN')
m=HypothesisMemory.__new__(HypothesisMemory);m.db=hdb;m.path=c/'research/hypotheses.sqlite'
rows=[]
for tag,ver,name,mpin in [('6566','v1','HM65','d047bef9b462561fb024d1ccf982ef7a6894a881039e640f225687605458feef'),('6768','v3','AV68','a3c665cd4331143557e3f73cefa155ce279b6b15e80316537b180fd93523794e')]:
 receipt=b/f'canonical-retention-{tag}/v1';p=b/f'retention-{tag}-production/{ver}'
 assert sha(receipt/'manifest.json')==mpin
 for f in json.loads((receipt/'manifest.json').read_text())['files']: assert sha(receipt/f['path'])==f['sha256']
 refs=json.loads((p/'artifact-map.json').read_text())
 for a in refs: assert resolve_artifact(c,a)['resolution_status']=='verified'
 export=sqlite3.connect((p/'source-export.sqlite').as_uri()+'?immutable=1',uri=True);n=0;differences=[]
 for identity,h,raw in export.execute('select id,content_hash,document from document_revisions'):
  r=db.execute('select document from document_revisions where id=? and content_hash=?',(identity,h)).fetchone();assert r
  actual=Store.decode(json.loads(r[0]));expected=Store.decode(json.loads(raw))
  assert content_fingerprint(actual)==h==content_fingerprint(expected)
  if actual!=expected:
   fields={k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k)}
   md={k for k in set(actual['metadata'])|set(expected['metadata']) if actual['metadata'].get(k)!=expected['metadata'].get(k)}
   assert fields<= {'fetched_at','metadata'} and md<=_RETRIEVAL_METADATA
   differences.append({'source_id':identity,'revision_hash':h,'fields':sorted(fields),'metadata_keys':sorted(md)})
  n+=1
 export.close()
 saved=json.loads((receipt/f'{name}-readback.json').read_text());actual=m.get(saved['hypothesis']['id']);assert actual==saved['hypothesis']
 rows.append({'packet':tag,'canonical_manifest_sha256':mpin,'artifacts_verified':len(refs),'source_revisions_verified':n,'retrieval_envelope_differences':differences,'hypothesis_id':actual['id'],'full_hypothesis_matches_canonical_receipt':True,'status':actual['status'],'claims_in_receipt':len(saved['claims']),'records_in_receipt':len(saved['records'])})
pjafter=json.loads((b/'canonical-retention-6768/v1/PJ01-after.json').read_text());pj=pjafter.get('hypothesis',pjafter);assert m.get(pj['id'])==pj
hdb.close();db.close()
result={'observed_at':datetime.now(timezone.utc).isoformat(),'packets':rows,'PJ01_full_state_matches_after_receipt':True,'source_export_without_WAL':True,'review_correction':'Initial root read-only check demanded equality of complete retrieval envelopes and stopped. Three existing 6566 paper revisions differ only in fetched_at/query/effective_arxiv_query, excluded from scientific identity by the actual Store contract. Corrected check verifies both content hashes and explicitly bounds every envelope difference. No canonical mutation or source-content repair occurred.','scope':'Independent canonical read-only source/artifact/full-hypothesis comparison; no new snapshot or S3 coverage asserted.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

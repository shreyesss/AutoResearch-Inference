"""Build review/validation receipts for the completed source-research run."""
import json,hashlib,re,sys,csv
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];P=R.parents[1];sys.path.insert(0,str(P))
from ideation.evidence import quote_errors
from ideation.hypotheses import CARD
from ideation.policy import review_schema
from ideation.hypothesis_memory import HypothesisMemory
from ideation.store import now
import jsonschema
lanes=['attention','systems','compute','cross-engine','prefill-mqa'];initial=[];latest=[];prompts=[];validation=[]
root=json.loads((R/'root-review.json').read_text());policy=json.loads((R/'policy/frozen-rubric.json').read_text())
lines=['# Model review and recovery record','','All 17 distinct initial mechanisms are retained. There were 13 unchanged-mechanism recovery descendants and one root quote-only repair, for 31 new immutable records. The latest selection is **16 deferred, 1 rejected, 0 accepted** under the frozen rubric. Eight conditional diagnostic plans were registered without changing those selections. No GPU experiment ran.','','| Lane | Initial proposals / requested | Initial outcome | Recovery / latest outcome |','|---|---:|---|---|']
for lane in lanes:
 p=R/lane/'hypotheses';m=json.loads((p/'manifest.json').read_text());cards=json.loads((p/'propose-1.json').read_text())['hypotheses'];initial+=cards
 final=R/lane/('review-recovery' if lane in ['systems','compute','cross-engine'] else 'hypotheses')
 h=json.loads((final/'history.json').read_text());latest+=h
 note='New immutable revisit; original proposals preserved' if final!=p else 'Original separate critic completed'
 if lane=='prefill-mqa':note+='; quote-only root descendant changes structural rejection to deferred, critic criteria unchanged'
 lines.append(f"| {lane} | {len(cards)} / {m['requested']} | {m['status']} | {note} |")
 for x in [p,final]:
  for f in x.glob('*.prompt.txt'):
   if str(f) not in {i['path'] for i in prompts}:prompts.append({'path':str(f),'bytes':f.stat().st_size})
 sources=json.loads((final/'sources.json').read_text())
 for record in h:
  jsonschema.validate(record['card'],CARD);jsonschema.validate(record['review'],review_schema(policy)['properties']['reviews']['items'])
  errs=quote_errors(record['card']['evidence'],sources)
  validation.append({'lane':lane,'id':record['card']['id'],'quote_errors':errs,'historical_failure_preserved':bool(errs) and lane=='prefill-mqa'})
# Final root-repaired candidate must pass without changing selection policy.
p=R/'prefill-mqa/quote-repair';h=json.loads((p/'history.json').read_text())[0];s=json.loads((p/'sources.json').read_text());assert not quote_errors(h['card']['evidence'],s)
validation.append({'lane':'prefill-mqa quote repair','id':h['card']['id'],'quote_errors':[]})
lines+=['','## Failure and repair details','','- Systems, compute and cross-engine critic prompts exceeded the CLI limit of 1,048,576 input characters. They failed before producing reviews. The raw errors, oversized prompts and registered proposals remain in the original directories.','- The source-packing fix retains every packet/cited source, caps extra retrieval at 64 total documents and limits duplicated API metadata. Omitted IDs and excerpt flags are explicit. Recovered critic prompts were roughly 0.5–0.56 MB, and all three completed. Full records remain archived.','- Revisit cards link to originals; the mechanism is unchanged. The systems revisit adds late read-only evidence that Engram uses shared DP memory, leading to the private-branch rejection.','- Prefill evidence repair and the proposer both used the exact nine-character excerpt “avg +3.7%”, below the validator’s 12-character minimum. The original failures remain. The root expands the excerpt to its adjacent exact source context, registers a repair descendant and reapplies unchanged critic judgments. This is an editorial repair, not another model critique or a correctness pass.','- The generated policy rationale accidentally described a 0–1 scale; the frozen copy documents the prose correction to actual 0–5 weighted scoring. Weights, gates and threshold were not relaxed after outcomes.','','## Latest mechanisms','','| Card | Frozen selection | Score | Root disposition |','|---|---|---:|---|']
for d in root['candidates']:lines.append(f"| [{d['key']}](experiments/{d['key']}.md) | {d['model_assessment']['status']} | {d['model_assessment']['score']} | {d['root_disposition']} |")
lines+=['','Scores are prioritization judgments. Required unknowns override a high score; the 82/100 mHC card remains deferred. An experiment plan is an instruction for resolving unknowns, not an executed outcome or a waiver.','','Model calls used the existing authenticated CLI configuration, with no explicit model override. Proposer and critic are separate calls to the configured model, not independent experts. [Root synthesis](root-review.json), [decision ledger](decision-ledger.csv), [planned tests](planned-tests.json) and [memory export](memory-export.json) retain the distinction.']
(R/'MODEL_REVIEW.md').write_text('\n'.join(lines)+'\n')
# Aggregate exact-quote verification of final evidence packets.
packets=[]
for lane in lanes:
 name='packet-review.json' if lane in ['systems','compute','cross-engine'] else 'packet-reviewed.json' if lane=='prefill-mqa' else 'packet.json'
 p=R/lane/'evidence'/name;packet=json.loads(p.read_text());errs=quote_errors(packet['claims'],packet['sources']);assert not errs
 packets.append({'lane':lane,'path':str(p.relative_to(R)),'sources':len(packet['sources']),'claims':len(packet['claims']),'valid':True})
# Verify latest card quotes, all input hashes, and that no runtime test event exists.
for d in root['candidates']:
 p=R/d['model_artifact'];records=json.loads((p/'history.json').read_text());record=next(h for h in records if h['global_id']==d['global_id']);docs=json.loads((p/'sources.json').read_text());assert not quote_errors(record['card']['evidence'],docs)
inputs=json.loads((R/'input-manifest.json').read_text());hashes=[]
for name,expected in inputs.items():
 actual=hashlib.sha256((P/name).read_bytes()).hexdigest();assert expected==actual,name;hashes.append({'path':name,'sha256':actual,'valid':True})
ledger=HypothesisMemory(P/'data/hypotheses.sqlite')
ids=[row[0] for row in ledger.db.execute('SELECT id FROM hypotheses WHERE run LIKE ?',(str(R)+'%',))]
events=[dict(row) for row in ledger.db.execute('SELECT hypothesis_id,type FROM events') if row['hypothesis_id'] in ids]
assert not any(e['type'] in ('test_running','test_result') for e in events)
plans=json.loads((R/'planned-tests.json').read_text());assert len(plans)==8
assert sum(e['type']=='test_planned' for e in events)==8
# Audit literal local links in the written top-level documentation and card files.
broken=[]
for p in list(R.glob('*.md'))+list((R/'experiments').glob('*.md')):
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if re.match(r'[a-zA-Z]+:',dest) or dest.startswith('#'):continue
  target=(p.parent/dest.split('#')[0])
  if target.name=='validation.json':continue # Written below.
  if not target.exists():broken.append({'file':str(p.relative_to(R)),'link':dest})
assert not broken,broken
# Scan for exact environment secret values without printing or copying them.
from dotenv import dotenv_values
secrets=[v for k,v in dotenv_values('/home/ubuntu/.env').items() if v and len(v)>=8 and any(x in k.upper() for x in ['KEY','TOKEN','SECRET','PASSWORD'])]
leaks=[]
for p in R.rglob('*'):
 if p.is_file():
  data=p.read_bytes()
  if any(v.encode() in data for v in secrets):leaks.append(str(p.relative_to(R)))
assert not leaks,'Secret value found; inspect privately'
tests=(R/'full-tests-final.log').read_text();assert 'Ran 53 tests' in tests and tests.rstrip().endswith('OK')
result={'at':now(),'status':'passed','software_tests':53,'tests_log':'full-tests-final.log','mechanisms':len(root['candidates']),'initial_model_proposals':len(initial),'new_immutable_records':len(ids),'latest_selection':dict(Counter(d['model_assessment']['status'] for d in root['candidates'])),'planned_tests':len(plans),'gpu_experiments':0,'runtime_test_events':0,'final_evidence_packets':packets,'quote_checks':validation,'input_hash_checks':hashes,'local_doc_links_valid':True,'secret_value_scan':'passed; no values copied','prompt_sizes':prompts,'limits':['No GPU execution, generation or candidate deployment','No independent correctness or performance qualification','Primary discussion is HTML-visible and not exhaustive','Provider empty searches and patch rate limits preserved','Candidate source excerpts are bounded with explicit omission metadata']}
(R/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ['status','software_tests','mechanisms','new_immutable_records','latest_selection','planned_tests','gpu_experiments']}))

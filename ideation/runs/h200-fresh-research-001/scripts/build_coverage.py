"""Aggregate acquisition depth without treating URL discovery as primary evidence."""
import csv,json,hashlib,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];P=R.parents[1];sys.path.insert(0,str(P))
from ideation.store import Store,now
s=Store(P/'data/corpus.sqlite')
rows=list(csv.DictReader((P/'runs/pr-evaluation-audit-001/inputs/vllm-dsv41-dspark-items.csv').open()))
csvcounts=Counter(x['repo'] for x in rows)
receipts=[json.loads(p.read_text()) for p in sorted((R/'primary').glob('*/receipt.json'))]
(R/'primary-manifest.json').write_text(json.dumps(receipts,indent=2))
notes={
'vllm-project/vllm':'39 focused pages cover all five mechanism lanes. Prioritize H01–H08; reject small-head TP4/8 transfer and private Engram branch on TP1/shared storage. Patch and installed-source checks are selective, not all 4,209 original PRs.',
'deepseek-ai/DeepEP':'#693 direct-NVLink triple buffering is a conditional backend/kernel comparison (H14); current AG/RS is inactive for this kernel. Preserve newer adapter/API compatibility concerns.',
'deepseek-ai/DeepGEMM':'#448 correctness, #452 prefill epilogue, #350 narrow-K and #303 negative report; also inspect MegaMoE relatives. Narrow K<=256 groups4 paths do not establish our H5120 expert eligibility. Closed slowdown reports do not settle other shapes.',
'deepseek-ai/DeepSelect':'#14 SM90 implementation/build and integration via vLLM #59204. Python application succeeds; native FP32/stride/build remains a gate (H07/H13).',
'deepseek-ai/FlashMLA':'#200/#216 older layouts and #213 planner shared-memory lead; no broad H200 port inferred from old V3.2 kernels. Existing vLLM plan sharing is the stronger immediate experiment.',
'deepseek-ai/DeepSpec':'#30/#31/#48 provide sampling-distribution/correctness context. Use for G01 test design, not as evidence of a direct serving speedup.',
'deepseek-ai/DeepJIT':'#12/#14 startup/JIT concurrency ideas are a cold-start objective. No active DeepJIT steady-state serving path was established; do not spend warm-service budget here.',
'deepseek-ai/Engram':'#27 is a demo extension, not evidence for the installed vLLM storage branch. Follow implementation into vLLM #59849/#59923/#62359; logs rule out the private-path card.',
'deepseek-ai/TileKernels':'#18 mHC prototype and related kernel discussions are useful history. Use the already fused installed vLLM implementation as comparator; old prototype availability is not an end-to-end improvement.',
'deepseek-ai/deepseek-recipe':'#11/#15/#24/#25 contribute tool/text encoding and semantic invariants. Treat as G04 quality constraints, not kernel speed claims.',
'SemiAnalysisAI/InferenceX':'#2963/#3077/#3099 and related H200 recipes give workload/configuration comparators. TP4 recipes differ from current TP1/DP4/EP4; preserve cost, topology and benchmark definitions.',
'flashinfer-ai/flashinfer':'#6343/#6517 native FP4 SM90 MegaMoE, cleanup and weight conversion are concrete H12 leads. Benchmark geometry differs; EP4 is unchanged by new H200 push buckets. #62603 in vLLM concerns block-FP8 integration.',
'vllm-project/recipes':'#1005 H200 setup is a comparator; #1017 revision changes are a separate baseline arm. Recipe convenience does not justify a silent model/image update.',
'sgl-project/sglang':'Added beyond original CSV: 3 bounded API searches plus focused pages. #41251 bundle, #39664 mHC, #40860 candidate scorer, #41561 mapping fusion, #41659 metadata, #40417 near-parity and #43065 sequence-parallel paths. Preserve layout/topology and benchmark confounds.',
'vllm-project/humming':'#38 is primary negative evidence: grouped-scale synchronization and weight-preprocessing memory tradeoffs on Hopper. It argues for per-token/BF16 controls and total memory accounting.',
'vllm-project/FlashMLA':'#26 fork-level implementation context; dependency availability is not installed dispatch. Keep upstream/fork identities distinct.'}
lines=['# Repository acquisition and decisions','','All 13 original CSV repositories received URL/title indexing and fresh discovery attempts. Selected sources were then opened on demand. Supplemental repositories are explicit additions. Counts below measure available snapshots, not equal-depth review or exhaustive search.','','| Repository | Original CSV URLs | Primary pages | Patch snapshots | Decision/use |','|---|---:|---:|---:|---|']
coverage=[]
for repo in sorted(notes):
 rec=[x for x in receipts if x['repo']==repo]
 patches=sum((R/'primary'/f"{repo.replace('/','--')}--{x['number']}"/'changes.patch').exists() for x in rec)
 web=R/'discovery'/('web-'+repo.replace('/','--')+'.json')
 recweb=json.loads(web.read_text()) if web.exists() else None
 item={'repo':repo,'original_csv_urls':csvcounts[repo],'primary_pages':len(rec),'patch_files':patches,'web_discovery':('error_or_empty: '+str(recweb['error'])) if recweb and recweb.get('error') else 'search completed' if recweb else 'supplemental discovery','decision':notes[repo],'primary_ids':[x['id'] for x in rec]}
 coverage.append(item)
 lines.append(f"| `{repo}` | {csvcounts[repo]} | {len(rec)} | {patches} | {notes[repo]} |")
lines+=['','## Depth and limitations','','- **URL/title only:** all 5,532 original rows and 74 supplemental leads; this layer is not quotation evidence.','- **Opening record:** historical corpus and initial live feed. Fresh fetch time does not imply all discussions were read.','- **Primary page:** 108 selected HTML/text captures, retaining visible opening text, comments and some review discussion. Pagination and hidden replies are not complete.','- **Patch:** 69 downloaded patch snapshots. HTTP 429 failures remain in receipts; unavailable patches are not treated as inspected code.','- **Installed source:** exact read-only snapshots and hashes; no GPU dispatch or correctness measurement follows from text alone.','- **Model source use:** each evidence/proposal/critic input is archived. Critic context explicitly lists omitted extra retrieval IDs after its size fix.','','The initial feed refresh was four-day bounded discovery, not full history; final checkpoints completed that pass. Serper searches with empty-result errors (including some small repos) remain recorded. Those repositories still have CSV leads and selected primary reads. OpenAlex returned empty edge lists for two initial citation-expansion attempts; the full-text backward/forward path in [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) supplies an explicit alternative.','','See [primary receipts](primary-manifest.json), [coverage JSON](repository-coverage.json), [URL index](source-index.jsonl), [supplemental leads](supplemental-source-index.csv), and [discovery artifacts](discovery/).']
(R/'REPOSITORY_COVERAGE.md').write_text('\n'.join(lines)+'\n');(R/'repository-coverage.json').write_text(json.dumps(coverage,indent=2))
manifest=[]
for p in sorted((R/'baseline/source').rglob('*')):
 if p.is_file():manifest.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'baseline/source-manifest-final.json').write_text(json.dumps(manifest,indent=2))
# A backward edge from BASS and a forward edge from that cited work, verified in full text.
edges=[]
for src,dst,needle,direction in [('2404.15778','2310.18813','arXiv:2310.18813','backward from BASS'),('2408.11049','2310.18813','https://arxiv.org/abs/2310.18813','forward from Synergy to MagicDec')]:
 doc=s.get('fulltext:'+src);assert needle in doc['body'];s.edge('arxiv:'+src,'cites','arxiv:'+dst,doc['id'],{'verification':'literal full-text reference','needle':needle,'at':now()});edges.append({'src':'arxiv:'+src,'relation':'cites','dst':'arxiv:'+dst,'evidence_source':doc['id'],'exact_reference':needle,'traversal':direction})
s.db.commit()
for id in ['2404.15778','2608.19677','2603.19289','2605.07363','2310.18813','2408.11049']:
 (R/'discovery'/('paper-'+id+'.json')).write_text(json.dumps(s.get('fulltext:'+id),indent=2))
(R/'discovery/verified-citation-path.json').write_text(json.dumps(edges,indent=2))
print(json.dumps({'repos':len(coverage),'primary_pages':len(receipts),'patches':sum(x['patch_files'] for x in coverage),'installed_files':len(manifest),'papers':6,'verified_citation_edges':len(edges)}))

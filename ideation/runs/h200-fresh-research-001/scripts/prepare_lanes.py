"""Freeze focused source packets for the existing evidence/proposal/critic tools."""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

RUN = Path(__file__).resolve().parents[1]
PROJECT = RUN.parents[1]
sys.path.insert(0,str(PROJECT))
from ideation.store import Store, now

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def main():
    s=Store(PROJECT/'data/corpus.sqlite')
    # URL/title index is the breadth layer; bodies and discussions are demand-fetched.
    rows=list(csv.DictReader((PROJECT/'runs/pr-evaluation-audit-001/inputs/vllm-dsv41-dspark-items.csv').open()))
    with (RUN/'source-index.jsonl').open('w') as f:
        for r in rows:
            f.write(json.dumps({k:r[k] for k in ['repo','number','type','url','title']},ensure_ascii=False)+'\n')
    receipts=[json.loads(p.read_text()) for p in sorted((RUN/'primary').glob('*/receipt.json'))]
    write(RUN/'primary-manifest.json',receipts)
    for p in (RUN/'primary').glob('*/changes.patch'):
        receipt=json.loads((p.parent/'receipt.json').read_text())
        text=p.read_text()
        sections=re.split(r'(?=^diff --git )',text,flags=re.M)
        code='\n'.join(x for x in sections if x.startswith('diff --git a/vllm/') or x.startswith('diff --git a/csrc/') or x.startswith('diff --git a/deep_gemm/'))
        if not code:code=text
        s.put({'id':receipt['id']+':patch','source':'github','kind':'code','title':receipt['id']+' fetched implementation patch','body':code,'url':receipt['url']+'.patch','parent':receipt['id'],'metadata':{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'patch_commit_shas':receipt.get('patch_commit_shas',[]),'snapshot':str(p)}})
    # Exact bounded excerpts retain their full-file hashes and locations.
    selections={
      'attention': [('vllm/model_executor/kernels/attention/dsa/sparse_mqa_logits.py',25,54),('vllm/v1/attention/backends/mla/sparse_swa.py',870,910),('vllm/model_executor/layers/sparse_attn_indexer.py',1,45)],
      'compute': [('vllm/model_executor/layers/fused_moe/oracle/mxfp4.py',367,392),('vllm/model_executor/layers/fused_moe/experts/fused_humming_moe.py',108,123),('vllm/model_executor/kernels/mhc/tilelang_kernels.py',58,98),('vllm/models/deepseek_v41/nvidia/ops/mhc.py',30,72)],
      'systems': [('vllm/v1/worker/gpu/spec_decode/dspark/speculator.py',1,80),('vllm/v1/worker/gpu/dp_utils.py',1,100)],
    }
    for lane,parts in selections.items():
        snippets=[]
        for path,start,end in parts:
            p=RUN/'baseline/source'/path
            if not p.exists():continue
            snippets.append(f'FILE {path}:{start}-{end}; SHA256 {hashlib.sha256(p.read_bytes()).hexdigest()}\n'+'\n'.join(p.read_text().splitlines()[start-1:end]))
        if lane=='compute':
            lines=(RUN/'baseline/dispatch-log-excerpts.txt').read_text().splitlines()
            snippets.append('LIVE STARTUP LOG\n'+'\n'.join(x for x in lines if "Using 'MARLIN'" in x or 'Using MarlinExperts' in x)[:1200])
        body='\n\n'.join(snippets)
        (RUN/'baseline'/f'{lane}-source-excerpts.txt').write_text(body)
        s.put({'id':'code:h200-excerpts:'+lane,'source':'runtime_snapshot','kind':'code','title':'Exact installed H200 '+lane+' excerpts','body':body,'url':str((RUN/'baseline'/f'{lane}-source-excerpts.txt').resolve()),'metadata':{'captured_at':now(),'full_files':'baseline/source-manifest.json','note':'Read-only text inspection; source presence is not a GPU activation measurement.'}})
    lanes={
      'attention': {
        'prs':[58818,62000,62463,59204,59418,61615],
        'patches':[58818,62000,62463,59204],
        'other':['github:deepseek-ai/DeepSelect:14:live-page','github:deepseek-ai/FlashMLA:200:live-page','github:vllm-project/FlashMLA:26:live-page','fulltext:2605.07363'],
        'focus':'SM90 attention and indexer mechanisms: plan sharing, candidate gather versus direct paged scoring, DeepSelect SM90 integration. Distinguish TP1 64-head baseline from TP4/TP8 small-head papers and PRs. The two candidate-only implementations are alternatives, not a stack. Compare dense fallback at short contexts, current top-k, and old B200 exclusions. Read counterevidence: #62000 single-request regression, #62463 tiny sample and missing accuracy, architecture gate and graph-live-length correctness. Do not import H20 ITL as H200 TPOT or capacity.',
      },
      'compute': {
        'prs':[59488,60600,61875,61461,59129,60768,60777,62603],
        'patches':[59488,61461],
        'other':['github:deepseek-ai/DeepGEMM:448:live-page','github:flashinfer-ai/flashinfer:6517:live-page','github:sgl-project/sglang:39664:live-page','github:sgl-project/sglang:41251:live-page','fulltext:2603.19289'],
        'focus':'Hopper compute: Marlin to Humming backend activation and grouped versus indexed GEMM; separate activation precision arm; SM90 mHC launch configuration and TF32 correctness; SGLang compensated BF16/overlap transfer; FlashInfer/DeepGEMM MegaMoE branch eligibility. Runtime startup explicitly selected MARLIN and installed Humming is 0.1.16. Existing env VLLM_HUMMING_MOE_GEMM_TYPE=indexed and --moe-backend humming are the strongest simple comparators. #60600 and current #59488 contradict blindly enabling block-FP8 on Humming 0.1.16. #62603 is block-FP8 weights/GLM results, not direct native MXFP4 DSv4.1 evidence. Keep the exact shipped model geometry E384/H5120/I2304/top6 and swiglu_limit10. Separate proposed correctness gates from performance hypotheses.',
      },
      'systems': {
        'prs':[58984,61767,59468,52464,51199,61834,59849,59923,62359,56752],
        'patches':[58984,61767],
        'other':['github:deepseek-ai/DeepEP:693:live-page','github:deepseek-ai/DeepSpec:48:live-page','fulltext:2404.15778','fulltext:2608.19677'],
        'focus':'DP systems and speculation: logical vs padded drafter rows, CPU allreduce, queue/prefill alignment, final-rank prefix locality with API2, exact-size Engram and packed exchange, and DeepEP communication alternatives. Current AG/RS backend is not DeepEP; Engram is host offload with embedding_across_dp, resolve sharded versus shared allocation. Existing scheduler/MBT/static prefill interval is the comparator before complex policy. k5 fixed adaptiveOFF seq64 MBT16384 means the draft reservation saving is at most256 tokens/rank (not a speedup). Decoder SWA replay is deliberately approximate and disabled: separate quality lane, not a free correctness-preserving activation. DSpark acceptance diagnostics never replace sampler correctness. Use BASS and CacheRoute as mechanism context; do not assume their algorithms are drop-in.',
      },
    }
    brief=json.loads((RUN/'brief.json').read_text())
    for lane,definition in lanes.items():
        ids=['github:vllm-project/vllm:'+str(n)+':live-page' for n in definition['prs']]+['github:vllm-project/vllm:'+str(n)+':patch' for n in definition['patches']]+definition['other']+['code:h200-excerpts:'+lane,'runtime:h200:runtime-inventory']
        missing=[i for i in ids if s.get(i) is None]
        if missing:raise ValueError('Missing sources: '+str(missing))
        assert len(ids)<=20,(lane,len(ids))
        current={**brief,'name':brief['name']+' / '+lane,'count':4 if lane=='attention' else 5,'focus':definition['focus'],'instructions':brief['instructions']+' '+definition['focus']}
        write(RUN/lane/'brief.json',current)
        request={'question':definition['focus']+' Extract source inefficiency, proposed fix, hardware/shape applicability, strongest contrary evidence and specific uncertainty that can change selection. Our live H200 topology is TP1/DP4/EP4 per replica, two replicas, seq64; no new GPU experiment exists. Quotes must be short exact passages, not a copied benchmark table.','source_ids':ids,'output':str(RUN/lane/'evidence'),'timeout':900}
        write(RUN/lane/'evidence-request.json',request)
        write(RUN/lane/'hypothesis-request.json',{'brief':str(RUN/lane/'brief.json'),'packet':str(RUN/lane/'evidence/packet.json'),'output':str(RUN/lane/'hypotheses'),'policy':str(RUN/'policy/frozen-rubric.json'),'rounds':1,'timeout':1800})
    s.db.commit()
    print(json.dumps({'lanes':list(lanes),'url_index_rows':len(rows),'primary_snapshots':len(receipts)}))

if __name__=='__main__':main()

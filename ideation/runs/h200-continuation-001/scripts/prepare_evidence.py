"""Select reviewable source excerpts, preserving full-source hashes and origins."""
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from ideation.store import Store

s = Store(PROJECT / 'data/corpus.sqlite')
selected = []
manifest = []


def excerpt(identity, path, spans, url, title, note):
    path = Path(path)
    lines = path.read_text().splitlines()
    text = '\n\n'.join(f'LINES {start}-{end}\n' + '\n'.join(lines[start-1:end]) for start,end in spans)
    meta = {'full_source_path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'spans': spans, 'note': note}
    doc = {'id': identity, 'source': 'source_snapshot', 'kind': 'code', 'title': title, 'body': text, 'url': url, 'metadata': meta}
    s.put(doc); selected.append(identity);manifest.append(doc)


def opening(repo, number):
    identity = f'github:{repo}:{number}'
    assert s.get(identity), identity
    selected.append(identity)


def patch_excerpt(repo, number, paths):
    path = RUN / 'sources' / (repo.replace('/', '--') + '--' + str(number)) / 'changes.patch'
    sections = re.split(r'(?=^diff --git )', path.read_text(), flags=re.M)
    matches = [section for section in sections if any(section.startswith('diff --git a/' + p + ' ') for p in paths)]
    assert matches, paths
    body = '\n'.join(matches)
    identity = f'code:continuation:{repo}:{number}:selected-patch'
    doc = {'id': identity, 'source': 'github', 'kind': 'code', 'title': f'Proposed {repo} #{number} selected changed paths; unexecuted',
           'body': body, 'url': f'https://github.com/{repo}/pull/{number}',
           'metadata': {'full_patch': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'selected_paths': paths,
                        'note': 'Only specified paths are included. Full patch retained; applicability and correctness remain untested.'}}
    s.put(doc);selected.append(identity);manifest.append(doc)


deep = PROJECT / 'data/deepinfer-source'
pin = '774ce244b87cc0eb8d4b94ab9f5de2ab22049f01'
base = Path('/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu')
excerpt('code:continuation:installed-av-cost',base/'spec_decode/adaptive_verification.py',[(80,128),(283,352)],str(base/'spec_decode/adaptive_verification.py'),'Installed AV cost tables and budget objective','Attested baseline source; no AV-on timing.')
excerpt('code:continuation:installed-dspark',base/'spec_decode/dspark/speculator.py',[(99,115),(155,221)],str(base/'spec_decode/dspark/speculator.py'),'Installed sequential DSpark sampling and confidence path','Attested source; timing/materiality remains unmeasured.')
excerpt('code:continuation:av-feasibility',PROJECT/'runs/av-k5-timing-001/IMPLEMENTATION_FEASIBILITY.md',[(37,82)],str(PROJECT/'runs/av-k5-timing-001/IMPLEMENTATION_FEASIBILITY.md'),'AV target/draft dispatch interaction and confidence-head evidence','Source-derived counterfactual; not an AV run, performance result or authority to combine C03.')
excerpt('code:continuation:deepinfer-av',deep/'csrc/engine/mtp_varlen.hpp',[(40,78),(132,148),(215,252)],f'https://github.com/deepseek-ai/DeepInfer/blob/{pin}/csrc/engine/mtp_varlen.hpp','DeepInfer runtime-cost-corrected verification controller','Released pinned source; not a drop-in vLLM patch.')
excerpt('code:continuation:deepinfer-qa',deep/'doc/inference_deployment_qa.md',[(1,220)],f'https://github.com/deepseek-ai/DeepInfer/blob/{pin}/doc/inference_deployment_qa.md','DeepInfer deployment Q&A, source-author claims','Full file retained in pinned source; EP64 curve is not H200 EP4 evidence.')
opening('vllm-project/vllm',61869)
patch_excerpt('vllm-project/vllm',61869,['vllm/v1/worker/gpu/spec_decode/dspark/fused_sample.py','vllm/v1/worker/gpu/spec_decode/dspark/speculator.py'])
opening('deepseek-ai/DeepInfer',92)
opening('deepseek-ai/DeepInfer',54)
patch_excerpt('deepseek-ai/DeepInfer',54,['deepinfer/timer.py','deepinfer/worker/worker.py'])
opening('deepseek-ai/DeepInfer',111)
opening('deepseek-ai/DeepInfer',99)
opening('deepseek-ai/DeepInfer',107)
opening('vllm-project/vllm',59611)
opening('vllm-project/vllm',61903)
opening('sgl-project/sglang',45433)
opening('sgl-project/sglang',45407)
for paper in ['2607.05147','2310.18813']:
    identity='fulltext:'+paper
    if s.get(identity): selected.append(identity)

# Router baseline is a required applicability check, not assumed from an upstream label.
model=RUN/'sources/pinned-vllm/vllm/models/deepseek_v4/nvidia/model.py'
lines=model.read_text().splitlines()
positions=[i+1 for i,line in enumerate(lines) if 'self.gate = ' in line]
if positions:
    excerpt('code:continuation:pinned-router',model,[(max(1,n-10),n+32) for n in positions],
            'https://github.com/vllm-project/vllm/blob/ac9126e58aa7bbab1856ba6593ba4d5003fea516/vllm/models/deepseek_v4/nvidia/model.py',
            'Nominal pinned DeepSeek V4 router construction inherited by V4.1','Nominal upstream source; verify actual installed bytes and active branch before claiming eligibility.')
assert len(selected)<=20,len(selected)
s.db.commit()
(RUN/'sources/excerpt-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
question='Identify mechanisms and counterevidence for history-aware H200 research continuation. Prioritize causal implementation evidence over titles and upstream headline gains. Compare installed vLLM k5/EP4/Marlin with DeepInfer released code and proposed PRs. Extract precise support/challenges for (a) total target-plus-draft graph-aware AV cost, (b) a portable unsharded probabilistic DSpark sampling fusion separate from the SM100 specialized engine, (c) host/scheduler overhead and whether the same work exists locally, (d) Hopper router/indexer or backend opportunities subject to actual branch and arithmetic. Assess other grounded interventions if stronger. C03 fixed-k5 screen failed promotion; C24 timing is pending and must not be duplicated. DeepInfer #92 is an open broad Hopper port with author-reported H20 results, not a demonstrated H200 improvement. Distinguish accuracy tests, synthetic acceptance and actual service results. Include exact short code/primary-source quotes, unknown local gain and concrete cheap checks. Avoid claiming source presence proves dispatch or time. Do not quote long benchmark tables; capture limitations and the source condition that changes the decision.'
request={'question':question,'source_ids':selected,'output':str(RUN/'evidence'),'timeout':900}
(RUN/'evidence-request.json').write_text(json.dumps(request,indent=2)+'\n')
print(json.dumps({'sources':len(selected),'ids':selected}))

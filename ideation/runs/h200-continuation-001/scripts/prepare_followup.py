"""Freeze new eligibility evidence and revisit the three mechanisms without rewriting history."""
import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from ideation.continuation import ContinuationTools
from ideation.evidence import quote_errors
from ideation.hypotheses import HypothesisTools
from ideation.store import Store, now


def write(name, value):
    path = RUN / name
    if path.exists():
        raise ValueError('Do not overwrite follow-up inputs: ' + str(path))
    path.write_text(json.dumps(value, indent=2) + '\n')
    return str(path)


manifest = json.loads((RUN / 'hypotheses/manifest.json').read_text())
assert manifest['status'] in {'completed', 'completed_no_selection'}, manifest
history = json.loads((RUN / 'hypotheses/history.json').read_text())
router = next(x for x in reversed(history) if 'router GEMM' in x['card']['prior_art_query'])
latest = {}
for row in history:
    latest[row['card']['prior_art_query']] = row
packet = json.loads((RUN / 'combined-evidence.json').read_text())
new_sources = []
for identity, relative, title in [
    ('artifact:continuation:router-headers', 'router-checkpoint-metadata.json', 'Stored checkpoint router weights; loaded dtype unknown'),
    ('code:continuation:gate-linear', 'sources/pinned-vllm/vllm/model_executor/layers/fused_moe/router/gate_linear.py', 'Nominal GateLinear FP32-weight eligibility and BF16-weight branch'),
    ('code:continuation:draft-watermarker', 'sources/pinned-vllm/vllm/v1/watermarking/spec_decode.py', 'Pinned draft watermarker factory; hash matches prior installed-source attestation'),
    ('code:continuation:fused-sampler-complete', 'sources/proposed-fused-sampler.py', 'Complete unexecuted 284-line proposed fused sampler, extracted from retained PR61869 patch'),
    ('artifact:continuation:eligibility-checks', 'ELIGIBILITY_CHECKS.md', 'Post-generation source and CPU checks with explicit limits'),
]:
    path = RUN / relative
    doc = {'id': identity, 'source': 'source_snapshot', 'kind': 'code' if identity.startswith('code:') else 'artifact',
           'title': title, 'body': path.read_text(), 'url': str(path),
           'metadata': {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
    new_sources.append(doc)
packet['sources'].extend(new_sources)
for identity, quote, claim in [
    ('artifact:continuation:router-headers', '"dtype": "BF16"', 'Three sampled checkpoint gates are stored BF16; this weakens eligibility but does not prove final loaded dtype.'),
    ('code:continuation:gate-linear', 'and self.weight.dtype == torch.float32', 'The nominal BF16x3 branch requires FP32 weights. FP32 output alone is insufficient.'),
    ('code:continuation:draft-watermarker', 'if allow_target_only:\n        return None', 'The factory can return no draft watermarker only through a specific fallback; request-level watermark=true alone does not resolve ownership.'),
    ('code:continuation:fused-sampler-complete', 'tl.atomic_xchg(counter_ptr + req, 0, sem="acq_rel", scope="gpu")', 'The retained full implementation includes last-arriver reduction and counter reset; missing launcher text in the original excerpt was a packet-depth limitation, not a missing download.'),
    ('code:continuation:fused-sampler-complete', 'assert torch.promote_types(base_logits.dtype, bias.dtype) == (\n            logits_cache.dtype\n        )', 'The launcher asserts cache dtype equivalence with the unfused add. This is a design invariant requiring real-weight correctness tests, not a passed local test.'),
    ('code:continuation:fused-sampler-complete', 'USE_FP64=self.use_fp64,\n            HAS_NEXT=step + 1 < num_steps,', 'The complete launcher supplies RNG precision and next-position specialization explicitly; no source execution or SM90 validation has occurred.'),
]:
    packet['claims'].append({'id': 'E' + str(len(packet['claims']) + 1), 'source_id': identity, 'quote': quote,
                             'claim': claim, 'relation': 'challenges', 'conditions': 'Offline/source evidence only.',
                             'reported_result': claim, 'transfer_inference': 'Resolve baseline eligibility before implementation.',
                             'limitations': 'No runtime dispatch, component timing or service gain established.'})
errors = quote_errors(packet['claims'], packet['sources'])
assert not errors, errors
packet.update(created_at=now(), quote_validation={'valid': True, 'errors': []},
              previous_packet=str(RUN / 'combined-evidence.json'))
packet_path = write('followup-evidence.json', packet)
brief = json.loads((RUN / 'brief.json').read_text())
brief['name'] += '-eligibility-followup'
brief['count'] = 3
brief['instructions'] += (' Review the three existing mechanisms against the new eligibility evidence, especially BF16 checkpoint headers and GateLinear for the router. '
                          'Preserve original assessments; the stored dtype is not definitive loaded dtype. '
                          'Count is an upper bound, never a quota or a reason to manufacture a fourth idea. '
                          'No runtime has been launched. The original C24 and C03 results remain unchanged.')
brief['prior_decisions'].append(str(RUN / 'ELIGIBILITY_CHECKS.md'))
brief_path = write('brief-followup.json', brief)
state = json.loads((RUN / 'state.json').read_text())
state['next_actions'] = [
    {'id': 'router-followup', 'action': 'Reassess ' + router['global_id'] + ' with stored BF16 weights and nominal FP32 eligibility; no GPU pilot.'},
    {'id': 'c24-offline', 'action': 'Preserve timing hold; qualify joint-rank dispatch/cost measurement design offline.'},
    {'id': 'sampler-gates', 'action': 'Resolve effective draft watermark configuration and full isolated adapter before implementation.'},
]
state_path = write('state-followup.json', state)
store = Store(PROJECT / 'data/corpus.sqlite')
for doc in new_sources:
    store.put(doc)
store.db.commit()
tools = HypothesisTools(store)
handoff = ContinuationTools(tools).prepare(brief_path, str(RUN / 'handoff-002'), str(PROJECT / 'hypotheses'),
    state=state_path, artifacts=[packet_path, str(RUN / 'policy-current/rubric.json'),
                               str(RUN / 'hypotheses/history.json'), str(RUN / 'ELIGIBILITY_CHECKS.md')],
    previous=str(RUN / 'handoff-001/continuation.json'))
request = {'brief': brief_path, 'packet': packet_path, 'policy': str(RUN / 'policy-current/rubric.json'),
           'continuation': handoff['path'], 'revisit': [row['global_id'] for row in latest.values()], 'rounds': 1,
           'output': str(RUN / 'eligibility-followup'), 'timeout': 900}
write('followup-request.json', request)
print(json.dumps({'handoff': handoff['path'], 'revisit': request['revisit'], 'sources': len(packet['sources'])}))

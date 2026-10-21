import copy
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from ideation.research_flow import ResearchFlow
from ideation.store import Store
from ideation.foundation import invoke
from ideation.discovery import _paper_key

FIXTURE = json.loads((Path(__file__).resolve().parents[1] / 'examples/evidence_fixture.json').read_text())


@pytest.fixture
def flow(tmp_path):
    store = Store(tmp_path / 'research/corpus.sqlite')
    store.put(FIXTURE['source'])
    store.db.commit()
    store.db.close()
    value = ResearchFlow(tmp_path)
    yield value
    value.close()


def proposal(flow):
    claim = flow.claim(FIXTURE['claim'])
    record = copy.deepcopy(FIXTURE['proposal'])
    record['claim_links'] = [{'claim_id': claim['id'], 'relation': 'supports', 'rationale': 'Supports the mechanism only; target benefit remains unknown'}]
    result = flow.propose(record)
    return claim, result['id']


def ready_manifest(flow, hypothesis):
    h = flow.memory.get(hypothesis)
    return {
        'purpose':'diagnostic', 'scope':'service',
        'baseline': {'id': h['baseline'], 'git_sha': 'a'*40, 'image_digest': 'sha256:'+'b'*64,
          'model': {'id':'fixture/model', 'revision':'c'*40}, 'tokenizer': {'id':'fixture/tokenizer','revision':'d'*40},
          'runtime':{'driver':'fixture','cuda':'fixture','engine_version':'fixture'},
          'hardware':{'gpu_type':'fixture B200','gpu_count':8,'topology':'fixture NVSwitch'},
          'parallelism':{'tp':1,'dp':4,'ep':4}, 'serving':{'fixture':True}, 'quantization':{'mode':'fixture'}},
        'candidate':{'parent_git_sha':'a'*40,'patch_sha256':'e'*64,'description':'fixture bounded draft budget'},
        'workload':{'id':'fixture-agent-75','sha256':'f'*64,'seed':0,'arrival':'fixture fixed rate', 'concurrency':[1,8],
          'prompt_output_distribution':{'input':100,'output':1000},'cache_policy':'cold then warmed matched'},
        'objective':{'metric':'request_median_ITL','unit':'ms','aggregation':'median over long-output requests','direction':'lower',
          'min_relative_gain':0.01,'tail_guards':[{'metric':'p99_ITL','limit':100,'unit':'ms'}]},
        'correctness':{'oracle':'fixture committed-token comparison','tolerance':0,'failure_policy':'abort'},
        'design':{'paired_order':['B0','C','B1'],'replicates':2,'profiler_separate':True},
        'budget':{'gpu_minutes':1,'wall_minutes':10,'max_attempts':1}, 'stop_rules':['Abort on correctness failure or budget expiry'],
        'evaluation':{'existing':[{'name':'fixture-agent-75','stimuli':'long output','observables':['ITL','TTFT'],
          'coverage':'sufficient','reason':'Matched workload reaches long decode regime','command_argv':['fixture-only','not-executed']}], 'additions':[]}}


def test_revision_grounded_claim_and_distinct_target_prediction(flow):
    claim, hypothesis = proposal(flow)
    h = flow.dossier(hypothesis)
    assert claim['reported_metric']['value'] == 25
    assert h['hypothesis']['card']['prediction'] is None
    assert h['hypothesis']['experiment_status'] == 'untested'
    assert claim['verification_status'] == 'reported'
    assert flow.claim(FIXTURE['claim'])['id'] == claim['id']
    with pytest.raises(sqlite3.IntegrityError):
        flow.db.execute('DELETE FROM evidence_claims')


def test_updated_source_triggers_review_without_rewriting_claim(flow):
    claim, hypothesis = proposal(flow)
    store = Store(flow.root / 'research/corpus.sqlite')
    changed = {**FIXTURE['source'], 'body':'A later revision retracts this example claim.', 'updated_at':'2026-10-02T00:00:00Z'}
    store.put(changed); store.db.commit(); store.db.close()
    assert flow.dossier(hypothesis)['claims'][0]['newer_source_revision']
    assert claim['id'] in flow.dossier(hypothesis)['review_alerts']
    pinned = {**FIXTURE['claim'], 'revision_hash': claim['revision_hash']}
    assert flow.claim(pinned)['revision_hash'] == claim['revision_hash']
    changes = flow.changes()
    assert hypothesis in changes['changes'][-1]['hypotheses_to_review']
    assert not flow.changes(changes['next_cursor'])['changes']


def test_invalid_quote_or_promoted_author_result_rejected(flow):
    with pytest.raises(ValueError):
        flow.claim({**FIXTURE['claim'], 'quote':'This quotation is invented entirely.'})
    with pytest.raises(ValueError):
        flow.claim({**FIXTURE['claim'], 'verification_status':'reproduced'})
    record = copy.deepcopy(FIXTURE['proposal']); record['card']['expected_gain_pct'] = 25
    with pytest.raises(ValueError):
        flow.propose(record)


def test_cpu_screen_missing_trace_cannot_invent_gain(flow):
    _, hypothesis = proposal(flow)
    with patch('subprocess.run', side_effect=AssertionError('no commands')), patch('urllib.request.urlopen', side_effect=AssertionError('no network')):
        screen = flow.screen(hypothesis, {})
    assert screen['status'] == 'insufficient_evidence'
    assert screen['result']['target_relative_gain'] is None
    assert screen['gpu_calls'] == 0


def test_eval_handoff_and_selection_do_not_validate_experiment(flow):
    _, hypothesis = proposal(flow)
    flow.screen(hypothesis, {})
    blocked = flow.eval_plan(hypothesis, {})
    assert blocked['readiness'] == 'blocked'
    with pytest.raises(ValueError):
        flow.decide(hypothesis, {'status':'accepted','actor':'test','rationale':'test','reopen_when':'new evidence','eval_plan_id':blocked['id']})
    manifest = ready_manifest(flow, hypothesis)
    ready = flow.eval_plan(hypothesis, manifest)
    assert ready['blocking_gaps'] == []
    assert ready['execution_authorized'] is False
    # Selection may approve a bounded diagnostic even if gain is still unknown.
    d = flow.decide(hypothesis, {'status':'accepted','actor':'fixture-reviewer','rationale':'Bounded diagnostic resolves missing target trace','reopen_when':'Contrary trace or failed correctness','eval_plan_id':ready['id']})
    assert flow.decide(hypothesis, {k:v for k,v in d.items() if k not in ('id','hypothesis_id')})['id'] == d['id']
    assert flow.dossier(hypothesis)['hypothesis']['experiment_status'] == 'untested'
    with pytest.raises(ValueError):
        flow.decide(hypothesis, {'status':'validated','actor':'test','rationale':'paper was fast','reopen_when':'never'})


def test_custom_evaluator_needs_gap_and_plan_requires_pins(flow):
    _, hypothesis = proposal(flow); flow.screen(hypothesis, {})
    manifest = ready_manifest(flow, hypothesis)
    manifest['evaluation']['additions'] = [{'name':'custom','reason':'want another tool','fills_gaps_in':[]}]
    manifest['baseline']['model']['revision'] = 'main'
    result = flow.eval_plan(hypothesis, manifest)
    assert any('Custom evaluator' in g for g in result['blocking_gaps'])
    assert any('model revision' in g for g in result['blocking_gaps'])


def test_contradiction_retained_across_cold_start(flow):
    claim, hypothesis = proposal(flow)
    flow.link(hypothesis, claim['id'], 'refutes', 'Same text also limits applicability to target')
    flow.decide(hypothesis, {'status':'deferred','actor':'test','rationale':'Need target trace','reopen_when':'Target acceptance trace available'})
    another = ResearchFlow(flow.root)
    try:
        result = another.dossier(hypothesis)
        assert result['hypothesis']['status'] == 'deferred'
        assert len(result['claims']) == 2
        assert result['records'][-1]['reopen_when'] == 'Target acceptance trace available'
    finally:
        another.close()


def test_query_version_and_taxonomy_change_create_new_cursor():
    task={'provider':'arxiv','lane':'targeted','family':'spec','query':'draft'}
    cfg={'recency_days':30,'families':[{'id':'spec','terms':['draft']}]}
    assert _paper_key(task,cfg) != _paper_key(task,{**cfg,'query_version':2})
    assert _paper_key(task,cfg) != _paper_key(task,{**cfg,'families':[{'id':'spec','terms':['draft','tree']} ]})


def test_cli_trace_roundtrip(tmp_path):
    invoke(['--state-dir',str(tmp_path),'init'])
    store=Store(tmp_path/'research/corpus.sqlite');store.put(FIXTURE['source']);store.db.commit();store.db.close()
    file=tmp_path/'claim.json';file.write_text(json.dumps(FIXTURE['claim']))
    record=invoke(['--state-dir',str(tmp_path),'--local-only','claim','record','--record',str(file)])
    assert invoke(['--state-dir',str(tmp_path),'claim','show',record['record']['id']])['verification_status']=='reported'
    assert invoke(['--state-dir',str(tmp_path),'show',FIXTURE['source']['id'],'--claims'])['claims']


def test_screen_provenance_and_qualification_gates(flow):
    _, hypothesis = proposal(flow)
    with pytest.raises(ValueError, match='author-reported'):
        flow.screen(hypothesis, {'provenance':{'measurement_origin':'author_reported'}})
    with pytest.raises(ValueError, match='baseline'):
        flow.screen(hypothesis, {'provenance':{'baseline_id':'wrong'}})
    flow.screen(hypothesis, {})
    manifest = ready_manifest(flow, hypothesis)
    manifest['purpose'] = 'qualification'
    assert any('not qualification' in g for g in flow.eval_plan(hypothesis, manifest)['blocking_gaps'])
    with pytest.raises(ValueError, match='conflicts'):
        flow.decide(hypothesis, {'hypothesis_id':'wrong','status':'deferred','actor':'test','rationale':'test','reopen_when':'test'})


def test_model_packet_bridge_preserves_exact_quote(flow, tmp_path):
    from ideation.research_flow import retain_reasoned_packet
    source = FIXTURE['source']
    card = copy.deepcopy(FIXTURE['proposal']['card'])
    card['evidence'] = [{'source_id':source['id'], 'quote':FIXTURE['claim']['quote'], 'relation':'supports'}]
    run = tmp_path/'legacy-run'
    identity = flow.memory.register(str(run.resolve()), card, FIXTURE['proposal']['brief'], {}, {source['id']:source})
    packet = {'quote_validation':{'valid':True}, 'sources':[source], 'claims':[{'id':'c1','source_id':source['id'],
      'quote':FIXTURE['claim']['quote'],'claim':'Author mechanism, not a target forecast','reported_result':'25% in fixture conditions'}]}
    path = tmp_path/'packet.json';path.write_text(json.dumps(packet))
    result = retain_reasoned_packet(flow.root, path, run)
    assert result['linked_citations'] == 1
    dossier = flow.dossier(identity)
    assert dossier['claims'][0]['claim']['verification_status'] == 'reported'
    assert dossier['hypothesis']['card']['prediction'] is None


def test_snapshot_restore_preserves_typed_research_trace(flow, tmp_path):
    from ideation.storage import snapshot, restore
    claim, hypothesis = proposal(flow)
    flow.screen(hypothesis, {})
    flow.decide(hypothesis, {'status':'deferred','actor':'test','rationale':'No target evidence','reopen_when':'Trace available'})
    archive = tmp_path/'archive'
    manifest = snapshot(flow.root/'research', archive)
    fresh = tmp_path/'fresh-state'
    restore(archive, fresh/'research', manifest['id'])
    recovered = ResearchFlow(fresh)
    try:
        dossier = recovered.dossier(hypothesis)
        assert dossier['hypothesis']['status'] == 'deferred'
        assert dossier['claims'][0]['claim_id'] == claim['id']
        assert dossier['records'][0]['status'] == 'insufficient_evidence'
        assert dossier['records'][1]['reopen_when'] == 'Trace available'
    finally:
        recovered.close()

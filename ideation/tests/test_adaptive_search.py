import copy
import json
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest

from ideation.controls import expand_query
from ideation.evidence import ResearchTools
from ideation.foundation import invoke
from ideation.paper_search import search_papers
from ideation.sources import Sources
from ideation.store import Store


def semantic_plan():
    return {'mechanism': 'Avoid re-prefilling shared prompts without increasing queue skew',
            'constraints': {'must_keep': ['correct outputs'], 'may_relax': ['after']},
            'queries': [{'query': 'prefix locality load imbalance', 'provider': 'arxiv',
                         'purpose': 'transfer', 'why': 'Find the locality versus queueing tradeoff'},
                        {'query': '"data_parallel_rank" "affinity"', 'provider': 'local',
                         'repo': 'vllm-project/vllm', 'match': 'all', 'purpose': 'implementation',
                         'why': 'Find whether an explicit-rank route bypasses internal affinity'}],
            'open_questions': ['Does our gateway choose an explicit rank?']}


def test_semantic_plan_retains_purpose_filters_and_runnable_recipes():
    plan = semantic_plan()
    original = copy.deepcopy(plan)
    result = expand_query('Reduce TTFT', {}, '2026-06-01', '2026-10-23', plan)
    assert result['mode'] == 'agent_authored'
    assert result['queries'][0]['paper_search'] == {
        'query': 'prefix locality load imbalance', 'providers': ['arxiv'],
        'after': '2026-06-01', 'before': '2026-10-23'}
    store = Store(':memory:')
    try:
        store.put({'id': 'github:vllm-project/vllm:1', 'source': 'github', 'kind': 'pr',
                   'title': 'data_parallel_rank affinity', 'body': 'explicit rank bypass',
                   'url': 'https://github.com/vllm-project/vllm/pull/1', 'updated_at': '2026-09-01'})
        local = dict(result['queries'][1]['local'])
        local['id_prefix'] = 'github:' + local.pop('repo') + ':'
        assert store.search(**local)[0]['id'] == 'github:vllm-project/vllm:1'
    finally:
        store.db.close()
    assert plan == original
    assert result['limits']['model_calls'] == result['limits']['network_calls'] == 0


def test_round_observations_flag_exact_repetition_without_blocking_a_retry():
    plan = semantic_plan()
    plan['observations'] = [{'query': plan['queries'][0]['query'], 'provider': 'arxiv',
                             'after': '2026-06-01', 'before': '2026-10-23', 'status': 'error',
                             'reason': 'Provider timed out; retry may be useful'}]
    result = expand_query('Cache placement', {}, '2026-06-01', '2026-10-23', plan)
    assert result['warnings'][0]['kind'] == 'repeat'
    assert result['queries'][0]['previous_observations'][0]['status'] == 'error'
    assert len(result['queries']) == 2


def test_date_widening_requires_explicit_task_permission():
    plan = semantic_plan()
    plan['queries'][0]['after'] = '2025-01-01'
    with pytest.raises(ValueError, match='Widening'):
        expand_query('Cache placement', {}, '2026-06-01', None, plan)
    plan['queries'][0]['relaxes'] = ['after']
    assert expand_query('Cache placement', {}, '2026-06-01', None, plan)['queries'][0]['after'] == '2025-01-01'
    plan['constraints']['may_relax'] = []
    with pytest.raises(ValueError, match='permitted'):
        expand_query('Cache placement', {}, '2026-06-01', None, plan)


def test_stop_without_quota_and_no_metric_only_family_expansion():
    result = expand_query('latency', {'families': [{'terms': ['latency', 'perf']}]})
    assert result['mode'] == 'lexical_fallback' and not result['matched_families']
    result = expand_query('Next action', {}, plan={
        'mechanism': 'Prefix placement', 'queries': [],
        'stop_reason': 'Source proves this route already bypasses the proposed change'})
    assert result['queries'] == [] and result['stop_reason']


def test_arxiv_dated_relaxation_keeps_dates_and_cache_reuses_both_attempts(tmp_path):
    store = Store(tmp_path/'corpus.sqlite')
    requests = []
    def fetch(self, url, xml=False, headers=None):
        query = parse_qs(urlparse(url).query)['search_query'][0]
        requests.append(query)
        entries = '' if 'all:"tail"' in query else '''<entry><id>http://arxiv.org/abs/2608.12345v1</id>
        <title>Prefix placement</title><summary>Fixture evidence only</summary>
        <published>2026-08-01T00:00:00Z</published><updated>2026-08-01T00:00:00Z</updated></entry>'''
        return ('<feed xmlns="http://www.w3.org/2005/Atom">'+entries+'</feed>').encode(), 'application/atom+xml'
    try:
        with patch.object(Sources, '_request', fetch):
            first = search_papers(store, 'prefix cache routing tail latency', ['arxiv'], '2026-06-01', '2026-10-23')
            second = search_papers(store, 'prefix cache routing tail latency', ['arxiv'], '2026-06-01', '2026-10-23')
        assert len(requests) == 2
        assert all('submittedDate:[202606010000 TO 202610222359]' in q for q in requests)
        assert 'all:"tail"' in requests[0] and 'all:"tail"' not in requests[1]
        assert first['providers'][0]['attempts'][1]['relaxed'] is True
        assert all(a['cache']['hit'] for a in second['providers'][0]['attempts'])
        assert first['hits'][0]['abstract'] == 'Fixture evidence only'
        assert first['unique_paper_identities'] == 1
    finally:
        store.db.close()


def test_explicit_arxiv_expression_is_not_broadened_on_empty_result(tmp_path):
    store = Store(tmp_path/'corpus.sqlite')
    try:
        with patch.object(Sources, '_request', return_value=(b'<feed xmlns="http://www.w3.org/2005/Atom"/>', 'application/atom+xml')) as fetch:
            result = ResearchTools(store).search('ti:"routing" AND abs:"prefix"', provider='arxiv', after='2026-01-01')
        assert fetch.call_count == 1 and result['ids'] == []
        assert result['attempts'][0]['relaxed'] is False
    finally:
        store.db.close()


def test_cli_agent_plan_persists_a_round_without_network_or_snapshot(tmp_path):
    root = tmp_path/'state'
    invoke(['--state-dir', str(root), 'init'])
    plan = tmp_path/'round.json'
    plan.write_text(json.dumps(semantic_plan()))
    result = invoke(['--state-dir', str(root), '--defer-snapshot', 'expand',
                     '--question', 'Improve prefix placement', '--plan', str(plan)])
    assert result['result']['mode'] == 'agent_authored'
    assert result['snapshot']['deferred'] is True
    from pathlib import Path
    assert json.loads((Path(result['output'])/'result.json').read_text())['queries'][0]['purpose'] == 'transfer'


def test_explicit_plan_must_exist_and_cannot_silently_fallback(tmp_path):
    root = tmp_path/'state'
    invoke(['--state-dir', str(root), 'init'])
    plan = tmp_path/'missing.json'
    args = ['--state-dir', str(root), '--defer-snapshot', 'expand',
            '--question', 'Improve prefix placement', '--plan', str(plan)]
    with pytest.raises(FileNotFoundError):
        invoke(args)
    plan.write_text('null')
    with pytest.raises(ValueError, match='JSON object'):
        invoke(args)

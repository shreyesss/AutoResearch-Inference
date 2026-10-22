"""Distinguish filter/pagination mistakes from absence without relaxing search."""
import asyncio

import pytest

from ideation.foundation import invoke
from ideation.store import Store


def seed(path):
    store = Store(path)
    for number, kind, day, body in [(1, 'pr', '01', 'inter-token latency'),
                                     (2, 'pr', '02', 'inter-token latency'),
                                     (3, 'issue', '03', 'inter-token latency'),
                                     (4, 'custom-note', '04', 'unrelated')]:
        store.put({'id': f'github:example/repo:{number}', 'source': 'test', 'kind': kind,
                   'title': 'Retained record', 'body': body, 'url': f'local:{number}',
                   'created_at': f'2026-10-{day}T00:00:00Z', 'updated_at': '2026-10-21T00:00:00Z'})
    store.db.commit()
    return store


def test_explanation_distinguishes_wrong_kind_empty_query_scope_and_pagination(tmp_path):
    writer = seed(tmp_path / 'corpus.sqlite')
    reader = Store(tmp_path / 'corpus.sqlite', readonly=True)
    try:
        wrong = reader.search('tpot', kind='pull_request', explain=True)
        assert wrong['hits'] == [] and wrong['total_matches'] == 0
        assert wrong['warnings'][0]['code'] == 'kind_absent_in_scope'
        assert 'kind=pr' in wrong['warnings'][0]['message']
        assert wrong['filters']['kind'] == 'pull_request'  # not silently rewritten
        assert wrong['source_scope']['available_kinds']['pr'] == 2
        args = dict(query='tpot', kind='pr', limit=1, id_prefix='github:example/repo:',
                    date_field='created_at', after='2026-10-01', before='2026-10-03')
        first = reader.search(**args, explain=True)
        assert first['hits'] == reader.search(**args)
        assert first['total_matches'] == 2 and first['next_offset'] == 1
        assert 'inter-token latency' in first['filters']['effective_fts']
        second = reader.search(**args, explain=True, offset=1)
        assert second['next_offset'] is None and second['hits'][0]['id'] != first['hits'][0]['id']
        assert reader.search(**args, explain=True, offset=2)['warnings'][0]['code'] == 'offset_past_matches'
        empty = reader.search('absentterm', kind='pr', explain=True)
        assert empty['total_matches'] == 0 and empty['warnings'] == []
        scope = reader.search('', id_prefix='github:example/missing:', explain=True)
        assert scope['warnings'][0]['code'] == 'empty_source_scope'
        custom = reader.search('', kind='custom-note', explain=True)
        assert custom['total_matches'] == 1 and custom['warnings'] == []
    finally:
        reader.db.close()
        writer.db.close()


def test_explanation_does_not_commit_callers_pending_changes(tmp_path):
    store = seed(tmp_path / 'corpus.sqlite')
    try:
        store.db.execute("UPDATE documents SET state='pending' WHERE id='github:example/repo:1'")
        assert store.search('', state='pending', explain=True)['total_matches'] == 1
        assert store.db.in_transaction
        store.db.rollback()
        assert store.search('', state='pending', explain=True)['total_matches'] == 0
        assert not store.db.in_transaction
    finally:
        store.db.close()


def test_real_cli_and_mcp_explanation_keep_default_result_contract(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    store = seed(tmp_path / 'research/corpus.sqlite')
    store.db.close()
    prefix = ['--state-dir', str(tmp_path)]
    legacy = invoke(prefix + ['pr-search', 'tpot'])
    detailed = invoke(prefix + ['pr-search', 'tpot', '--explain'])
    assert isinstance(legacy, list) and detailed['hits'] == legacy
    assert detailed['total_matches'] == 2 and detailed['filters']['kind'] == 'pr'
    mcp = pytest.importorskip('mcp')
    from ideation.mcp_server import create_server

    async def check():
        async with mcp.Client(create_server(tmp_path)) as client:
            old = await client.call_tool('search_local', {'query': 'tpot', 'kind': 'pr'})
            new = await client.call_tool('search_local', {'query': 'tpot', 'kind': 'pr', 'explain': True})
            assert not old.is_error and not new.is_error
            assert old.structured_content == {'hits': legacy}
            assert new.structured_content == detailed
    asyncio.run(check())

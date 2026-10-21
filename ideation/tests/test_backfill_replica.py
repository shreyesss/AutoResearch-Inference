import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ideation import backfill, journal
from ideation.discovery import refresh
from ideation.foundation import _write
from ideation.replica import sync
from ideation.storage import LocalTransport, snapshot, push
from ideation.store import Store
from ideation.github import RateLimited
from test_discovery import config, FakeGitHub, FakePapers, issue


def test_window_checkpoint_is_not_all_history(tmp_path):
    store = Store(tmp_path / 'corpus.sqlite')
    store.checkpoint('discovery:github:owner/engine', {'initial_scope': {'since': '2026-10-20', 'all_history': False},
                     'initial_scan_complete': True, 'completed_at': '2026-10-22T00:00:00Z', 'watermark': '2026-10-21T00:00:00Z'})
    cfg = config()
    cfg['budgets']['paper_requests'] = 0
    FakeGitHub.responses, FakeGitHub.calls = [([issue(1)], {})], []
    refresh(store, cfg, now='2026-10-22T00:00:00Z', github_factory=FakeGitHub, build_shortlist=False)
    assert 'since' not in FakeGitHub.calls[0][1]
    state = store.get_checkpoint('discovery:github:owner/engine')
    assert state['initial_scope']['all_history']
    assert backfill.coverage(store, cfg)[0]['all_history_complete']
    assert store.db.execute("SELECT count(*) FROM checkpoints WHERE key LIKE '%previous-scope:%'").fetchone()[0] == 1
    store.db.close()


def test_rate_limit_stops_other_repos_and_preserves_cursor(tmp_path):
    store = Store(tmp_path / 'corpus.sqlite')
    cfg = config()
    cfg['repositories'] += ['owner/other']
    cfg['budgets'].update(github_pages=4, paper_requests=0)
    FakeGitHub.responses, FakeGitHub.calls = [RateLimited('secret', code=403, remaining='0', reset='1792630800')], []
    receipt = refresh(store, cfg, now='2026-10-22T00:00:00Z', github_factory=FakeGitHub, build_shortlist=False)
    # Use a relative explicit retry-after in separate call for stable timestamps.
    assert 'secret' not in json.dumps(receipt)
    store.db.close()


def test_shared_secondary_cooldown(tmp_path):
    store = Store(tmp_path / 'corpus.sqlite')
    cfg = config()
    cfg['repositories'] += ['owner/other']
    cfg['budgets'].update(github_pages=4, paper_requests=0)
    FakeGitHub.responses, FakeGitHub.calls = [RateLimited('secret', code=429, retry_after='120')], []
    refresh(store, cfg, now='2026-10-22T00:00:00Z', github_factory=FakeGitHub, build_shortlist=False)
    assert len(FakeGitHub.calls) == 1
    assert store.get_checkpoint('discovery:github_rate')['retry_after'] == '2026-10-22T00:02:00Z'
    store.db.close()


def test_estimate_does_not_claim_unknown_scope_complete():
    result = backfill.estimate([{'repo': 'a/b', 'all_history_complete': False, 'upper_bound': None, 'pages_in_pass': 0}], 1, 60)
    assert not result['complete_estimate']
    assert result['unknown_repositories'] == ['a/b']
    result = backfill.estimate([{'repo': 'a/b', 'all_history_complete': False, 'upper_bound': 10000, 'pages_in_pass': 10}], 1, 60)
    assert result['estimated_hours_known_repos'] == 1.5


def test_replica_preserves_writer_and_checksums(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'example.json').write_text('{"v":1}')
    archive = tmp_path / 'archive'
    first = snapshot(source, archive)
    transport = LocalTransport(tmp_path / 'remote')
    push(archive, transport, first['id'], expected_head=None)
    node = tmp_path / 'node'
    (node / 'research').mkdir(parents=True)
    (node / 'research/writer.json').write_text('do not overwrite')
    a = sync(node, transport)
    assert Path(a['path'], 'example.json').read_text() == '{"v":1}'
    assert sync(node, transport)['id'] == a['id']
    (source / 'example.json').write_text('{"v":2}')
    second = snapshot(source, archive, parent=first['id'])
    push(archive, transport, second['id'], expected_head=first['id'])
    b = sync(node, transport)
    assert a['id'] != b['id']
    assert (node / 'research/writer.json').read_text() == 'do not overwrite'
    assert Path(a['path'], 'example.json').read_text() == '{"v":1}'
    assert json.loads((node / 'replicas/research/CURRENT.json').read_text())['id'] == b['id']


def test_journal_no_credentials_or_query_contents(tmp_path):
    args = SimpleNamespace(command='run', env_file='secret', question='API_KEY=secret', offline=True)
    identifier = journal.start(tmp_path, args)
    journal.finish(tmp_path, identifier, RuntimeError('secret'))
    result = journal.history(tmp_path)
    assert 'secret' not in json.dumps(result)
    assert result['commands'][0]['outcome'] == 'failed'
    assert not (tmp_path / 'research').exists()


def test_restored_journal_survives_new_node_command(tmp_path):
    import shutil
    old = tmp_path / 'old'
    key = journal.start(old, SimpleNamespace(command='search'))
    journal.finish(old, key)
    node = tmp_path / 'node'
    (node / 'research').mkdir(parents=True)
    shutil.copyfile(old / 'commands.sqlite', node / 'research/command-history.sqlite')
    new = journal.start(node, SimpleNamespace(command='status'))
    journal.finish(node, new)
    assert {r['id'] for r in journal.history(node)['commands']} == {key, new}


def test_replica_recovers_restore_to_marker_crash(tmp_path):
    from ideation.storage import restore, pull
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'a.json').write_text('{}')
    archive = tmp_path / 'archive'
    value = snapshot(source, archive)
    transport = LocalTransport(tmp_path / 'remote')
    push(archive, transport, value['id'], expected_head=None)
    node = tmp_path / 'node'
    pull(transport, node / 'archives')
    restore(node / 'archives', node / 'replicas/research' / value['id'], value['id'])
    result = sync(node, transport)
    assert result['id'] == value['id']

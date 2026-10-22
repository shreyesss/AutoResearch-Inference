"""Interactive batches retain evidence and journal without promising remote durability."""
import json
from unittest.mock import patch

import pytest

from ideation.foundation import invoke
from ideation.store import Store
from ideation.storage import restore


def test_deferred_corpus_import_retains_revisions_edges_and_later_restore(tmp_path):
    root = tmp_path/'state'
    invoke(['--state-dir', str(root), 'init'])
    before = json.loads((root/'latest-snapshots.json').read_text())
    source = Store(tmp_path/'source.sqlite')
    doc = {'id':'paper:import', 'source':'arxiv', 'kind':'paper', 'title':'Cache plan',
           'url':'https://example.org/paper', 'body':'Old evidence'}
    source.put(doc)
    source.put({**doc, 'body':'New evidence'})
    revisions = {r['content_hash'] for r in source.revisions(doc['id'])}
    source.edge(doc['id'], 'discovered_by', 'query:fixture', doc['id'], {'scope':'fixture'})
    source.db.commit(); source.db.close()
    with patch('ideation.foundation._snapshot', side_effect=AssertionError('Deferred import must not publish')):
        result = invoke(['--state-dir', str(root), '--defer-snapshot', 'import-corpus', '--source', str(tmp_path/'source.sqlite')])
    assert result['snapshot']['deferred'] and not result['snapshot']['published']
    assert json.loads((root/'latest-snapshots.json').read_text()) == before
    assert json.loads((root/'pending-research-checkpoint.json').read_text())['snapshot_required']
    history = invoke(['--state-dir', str(root), 'history'])['commands']
    assert any(r['command']=='import-corpus' and r['outcome']=='succeeded' for r in history)
    receipt = invoke(['--state-dir', str(root), '--local-only', 'snapshot'])
    destination = tmp_path/'relocated'
    restore(root/'archives', destination/'research', receipt['id'])
    restored = Store(destination/'research/corpus.sqlite', readonly=True)
    try:
        assert restored.get(doc['id'])['body'] == 'New evidence'
        assert {r['content_hash'] for r in restored.revisions(doc['id'])} == revisions
        assert restored.db.execute('SELECT 1 FROM edges WHERE src=? AND relation=? AND dst=?',
                                   (doc['id'], 'discovered_by', 'query:fixture')).fetchone()
    finally:
        restored.db.close()


def test_local_only_corpus_import_cannot_publish_to_configured_remote(tmp_path):
    root = tmp_path/'state'
    invoke(['--state-dir', str(root), 'init'])
    remote = tmp_path/'remote'
    invoke(['--state-dir', str(root), 'remote', 'configure', '--local-remote', str(remote), '--auto-publish'])
    source = tmp_path/'source.jsonl'
    source.write_text(json.dumps({'id':'paper:local', 'source':'test', 'kind':'paper',
                                 'title':'Local evidence', 'url':'https://example.org', 'body':'Evidence'})+'\n')
    local = invoke(['--state-dir', str(root), '--local-only', 'import-corpus', '--source', str(source)])
    assert not local['snapshot']['published'] and not remote.exists()
    assert (root/'archives/research/manifests'/f"{local['snapshot']['id']}.json").exists()
    published = invoke(['--state-dir', str(root), 'import-corpus', '--source', str(source)])
    assert published['snapshot']['published']
    assert (remote/'research/HEAD').read_text().strip() == published['snapshot']['id']


def test_deferred_paper_search_retains_data_and_journal_then_checkpoints(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    before = json.loads((tmp_path / 'latest-snapshots.json').read_text())
    def search(store, *args):
        store.put({'id':'paper:test', 'source':'arxiv', 'kind':'paper', 'title':'Cache placement',
                   'url':'https://example.org/paper', 'body':'Source evidence retained locally'})
        store.db.commit()
        return {'hits':[{'id':'paper:test'}], 'status':'completed'}
    with patch('ideation.paper_search.search_papers', search):
        result = invoke(['--state-dir', str(tmp_path), '--defer-snapshot', 'paper-search', 'cache placement'])
    assert result['snapshot']['snapshot_required'] is True
    assert result['snapshot']['published'] is False
    assert json.loads((tmp_path / 'latest-snapshots.json').read_text()) == before
    assert invoke(['--state-dir', str(tmp_path), 'show', 'paper:test'])['title'] == 'Cache placement'
    history = invoke(['--state-dir', str(tmp_path), 'history'])['commands']
    assert any(r['command'] == 'paper-search' and r['outcome'] == 'succeeded' for r in history)
    assert (tmp_path / 'pending-research-checkpoint.json').exists()
    with patch('ideation.storage.snapshot', side_effect=OSError('injected checkpoint failure')):
        with pytest.raises(OSError):
            invoke(['--state-dir', str(tmp_path), '--local-only', 'snapshot'])
    assert json.loads((tmp_path / 'pending-research-checkpoint.json').read_text())['snapshot_required'] is True
    receipt = invoke(['--state-dir', str(tmp_path), '--local-only', 'snapshot'])
    assert receipt['published'] is False
    pending = json.loads((tmp_path / 'pending-research-checkpoint.json').read_text())
    assert pending['snapshot_required'] is False
    assert pending['snapshot_id'] == receipt['id']


def test_defer_cannot_skip_refresh_backfill_or_experiment_checkpoint(tmp_path):
    for command in (['refresh'], ['experiment', 'list'], ['backfill', 'start']):
        with pytest.raises(ValueError, match='restricted to interactive research'):
            invoke(['--state-dir', str(tmp_path), '--defer-snapshot', *command])


def test_source_show_selects_exact_revision(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    store = Store(tmp_path / 'research/corpus.sqlite')
    doc = {'id':'paper:test', 'source':'arxiv', 'kind':'paper', 'title':'Old version',
           'url':'https://example.org/paper', 'body':'Old evidence text'}
    store.put(doc)
    old = store.revisions('paper:test')[0]['content_hash']
    store.put({**doc, 'body':'Revised conflicting evidence'})
    store.db.commit(); store.db.close()
    record = invoke(['--state-dir', str(tmp_path), 'show', 'paper:test', '--revision-hash', old])
    assert record['body'] == 'Old evidence text'
    with pytest.raises(KeyError):
        invoke(['--state-dir', str(tmp_path), 'show', 'paper:test', '--revision-hash', 'absent'])


def test_missing_source_and_revision_report_local_absence(tmp_path, capsys):
    from ideation.foundation import main
    invoke(['--state-dir', str(tmp_path), 'init'])
    store = Store(tmp_path / 'research/corpus.sqlite')
    store.put({'id': 'paper:present', 'source': 'test', 'kind': 'paper',
               'title': 'Present', 'url': 'https://example.org', 'body': 'Evidence'})
    store.db.commit(); store.db.close()
    cases = [(['show', 'paper:missing'], 'source_not_retained'),
             (['show', 'paper:present', '--revision-hash', 'missing'], 'source_revision_not_retained')]
    with patch('urllib.request.urlopen', side_effect=AssertionError('Local lookup must not fetch')):
        for command, code in cases:
            assert main(['--state-dir', str(tmp_path), *command]) == 1
            failure = json.loads(capsys.readouterr().err)
            assert failure['error_code'] == code
            assert 'No provider request was made' in failure['message']
    history = invoke(['--state-dir', str(tmp_path), 'history'])['commands']
    assert sum(r['command'] == 'show' and r['outcome'] == 'failed' for r in history) == 2


def test_local_match_all_recipe_executes_as_conjunction(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    store=Store(tmp_path/'research/corpus.sqlite')
    for number, title in enumerate(('prefix routing', 'prefix eviction', 'routing queues')):
        store.put({'id':str(number),'source':'test','kind':'paper','title':title,'body':'','url':'https://example.org'})
    store.db.commit();store.db.close()
    base=['--state-dir',str(tmp_path),'search','prefix routing']
    assert len(invoke(base))==3
    assert [r['id'] for r in invoke([*base,'--match','all'])]==['0']

"""Interactive batches retain evidence and journal without promising remote durability."""
import json
from unittest.mock import patch

import pytest

from ideation.foundation import invoke
from ideation.store import Store


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


def test_defer_cannot_skip_ingestion_or_experiment_checkpoint(tmp_path):
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


def test_local_match_all_recipe_executes_as_conjunction(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    store=Store(tmp_path/'research/corpus.sqlite')
    for number, title in enumerate(('prefix routing', 'prefix eviction', 'routing queues')):
        store.put({'id':str(number),'source':'test','kind':'paper','title':title,'body':'','url':'https://example.org'})
    store.db.commit();store.db.close()
    base=['--state-dir',str(tmp_path),'search','prefix routing']
    assert len(invoke(base))==3
    assert [r['id'] for r in invoke([*base,'--match','all'])]==['0']

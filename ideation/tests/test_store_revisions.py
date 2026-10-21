import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ideation.store import Store, content_fingerprint


class SourceRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'corpus.sqlite')
        self.doc = {'id': 'github:vllm-project/vllm:25', 'source': 'github', 'kind': 'pr',
                    'url': 'https://github.com/vllm-project/vllm/pull/25',
                    'title': 'Reduce sampler overhead', 'body': 'Initial measurements',
                    'state': 'open', 'created_at': '2026-10-01T00:00:00Z',
                    'updated_at': '2026-10-02T00:00:00Z', 'fetched_at': '2026-10-03T00:00:00Z',
                    'metadata': {'labels': ['performance'], 'head': {'sha': 'abc', 'ref': 'main'}}}

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def test_fetch_date_and_nested_metadata_order_do_not_duplicate_revision(self):
        self.store.put(self.doc)
        another = {**self.doc, 'fetched_at': '2026-10-04T00:00:00Z',
                   'metadata': {'head': {'ref': 'main', 'sha': 'abc'}, 'labels': ['performance']}}
        self.store.put(another)
        self.assertEqual(len(self.store.revisions(self.doc['id'])), 1)
        self.assertEqual(self.store.get(self.doc['id'])['fetched_at'], another['fetched_at'])
        self.assertEqual(self.store.revisions(self.doc['id'])[0]['fetched_at'], self.doc['fetched_at'])

    def test_cache_receipts_and_detail_fetch_time_are_not_source_changes(self):
        original = {**self.doc, 'metadata': {**self.doc['metadata'], 'retrieval_cache': {'hit': False},
                    'pr_detail_fetched_at': '2026-10-03T00:00:00Z', 'query': 'sampler', 'retrieval_query': 'draft sampling'}}
        refreshed = {**original, 'metadata': {**original['metadata'], 'retrieval_cache': {'hit': True},
                    'pr_detail_fetched_at': '2026-10-05T00:00:00Z', 'query': 'speculation', 'retrieval_query': 'mtp overhead'}}
        self.store.put(original)
        self.store.put(refreshed)
        self.assertEqual(len(self.store.revisions(self.doc['id'])), 1)
        self.assertTrue(self.store.get(self.doc['id'])['metadata']['retrieval_cache']['hit'])

    def test_body_state_merge_and_source_metadata_changes_survive(self):
        changes = [{}, {'body': 'Revised measurements'}, {'body': 'Revised measurements', 'state': 'closed'},
                   {'body': 'Revised measurements', 'state': 'merged', 'merged_at': '2026-10-06T00:00:00Z'},
                   {'body': 'Revised measurements', 'metadata': {'labels': ['bug'], 'head': {'sha': 'def'}}}]
        for i, change in enumerate(changes):
            self.store.put({**self.doc, **change, 'fetched_at': f'2026-10-{10+i:02d}T00:00:00Z'})
        revisions = self.store.revisions(self.doc['id'])
        self.assertEqual(len(revisions), 5)
        self.assertEqual(revisions[0]['body'], 'Initial measurements')
        self.assertEqual(revisions[2]['state'], 'closed')
        self.assertEqual(revisions[3]['merged_at'], '2026-10-06T00:00:00Z')
        self.assertEqual(revisions[4]['metadata']['head']['sha'], 'def')

    def seed_legacy_document(self):
        # Simulate a pre-revision installation without mutating immutable history.
        legacy = {**self.doc, 'merged_at': None, 'parent': None, 'tags': '[]',
                  'metadata': json.dumps(self.doc['metadata']), 'content_hash': 'legacy-hash'}
        columns = [row[1] for row in self.store.db.execute('PRAGMA table_info(documents)')]
        self.store.db.execute('INSERT INTO documents (' + ','.join(columns) + ') VALUES (' + ','.join('?' for _ in columns) + ')',
                              [legacy[key] for key in columns])
        self.store.db.commit()

    def test_previous_legacy_document_retained_when_changed_on_first_refresh(self):
        self.seed_legacy_document()
        self.store.put({**self.doc, 'body': 'Changed after upgrade', 'fetched_at': '2026-10-07T00:00:00Z'})
        revisions = self.store.revisions(self.doc['id'])
        self.assertEqual(len(revisions), 2)
        self.assertEqual(revisions[0]['body'], self.doc['body'])
        self.assertEqual(revisions[0]['legacy_content_hash'], 'legacy-hash')
        self.assertEqual(revisions[0]['content_hash'], content_fingerprint(self.doc))

    def test_legacy_unchanged_refresh_does_not_create_duplicate_content(self):
        self.seed_legacy_document()
        self.store.put({**self.doc, 'fetched_at': '2026-10-07T00:00:00Z'})
        self.store.put({**self.doc, 'fetched_at': '2026-10-08T00:00:00Z'})
        self.assertEqual(len(self.store.revisions(self.doc['id'])), 1)
        self.assertEqual(self.store.revisions(self.doc['id'])[0]['fetched_at'], self.doc['fetched_at'])

    def test_revision_cannot_be_overwritten_or_deleted(self):
        self.store.put(self.doc)
        self.store.db.commit()
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'immutable'):
            self.store.db.execute("UPDATE document_revisions SET document='{}'")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'immutable'):
            self.store.db.execute('DELETE FROM document_revisions')
        self.assertEqual(len(self.store.revisions(self.doc['id'])), 1)

    def test_hash_does_not_collide_when_title_body_boundaries_move(self):
        # The original title+body concatenation formula could conflate these.
        self.assertNotEqual(content_fingerprint({**self.doc, 'title': 'ab', 'body': 'c'}),
                            content_fingerprint({**self.doc, 'title': 'a', 'body': 'bc'}))


if __name__ == '__main__':
    unittest.main()

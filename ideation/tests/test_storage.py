import hashlib
import io
from types import SimpleNamespace
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from ideation.storage import (CHUNK_BYTES, ConflictError, LocalTransport, S3Transport, StorageError,
                              bucket_plan, estimate_cost, pull, push, restore, snapshot)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.archive = self.root / 'archive'
        self.remote = LocalTransport(self.root / 'remote')

    def tearDown(self):
        self.tmp.cleanup()

    def seed(self):
        (self.state / 'settings.json').write_text('{"repositories":["vllm-project/vllm"]}')

    def test_wal_backup_preserves_corpus_graph_memory_and_checkpoints(self):
        db = sqlite3.connect(self.state / 'corpus.sqlite')
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA wal_autocheckpoint=0')
            for table in ['documents', 'edges', 'checkpoints', 'hypotheses', 'events']:
                db.execute(f'CREATE TABLE {table}(id TEXT)')
                db.execute(f'INSERT INTO {table} VALUES (?)', ('retained',))
            db.commit()
            self.assertGreater((self.state / 'corpus.sqlite-wal').stat().st_size, 0)
            manifest = snapshot(self.state, self.archive)
            push(self.archive, self.remote, manifest['id'])
            fresh_archive = self.root / 'fresh-archive'
            pulled = pull(self.remote, fresh_archive)
            restore(fresh_archive, self.root / 'fresh', pulled['id'])
            with sqlite3.connect(self.root / 'fresh' / 'corpus.sqlite') as restored:
                for table in ['documents', 'edges', 'checkpoints', 'hypotheses', 'events']:
                    self.assertEqual(restored.execute(f'SELECT id FROM {table}').fetchone()[0], 'retained')
            self.assertEqual(len(manifest['files']), 1)
        finally:
            db.close()

    def test_default_exclusions_and_budget_ledger_preservation(self):
        self.seed()
        for folder in ['raw', 'cache', '.aws', 'weights']:
            (self.state / folder).mkdir()
            (self.state / folder / 'bulk.json').write_text('private-or-duplicate')
        (self.state / '.env').write_text('API_KEY=secret')
        (self.state / 'credentials.json').write_text('secret')
        (self.state / 'alias.json').symlink_to(self.state / 'settings.json')
        db = sqlite3.connect(self.state / 'cache' / 'index.sqlite')
        db.execute('CREATE TABLE budget (used INTEGER)')
        db.execute('INSERT INTO budget VALUES (17)')
        db.commit()
        db.close()
        result = snapshot(self.state, self.archive)
        self.assertEqual({r['path'] for r in result['files']}, {'settings.json', 'cache/index.sqlite'})

    def test_incremental_push_deduplicates_and_preserves_old_snapshot(self):
        self.seed()
        first = snapshot(self.state, self.archive)
        self.assertEqual(push(self.archive, self.remote, first['id'])['objects_written'], 1)
        second = snapshot(self.state, self.archive, parent=first['id'])
        self.assertEqual(push(self.archive, self.remote, second['id'], expected_head=first['id'])['objects_written'], 0)
        self.assertIsNotNone(self.remote.get('research/manifests/' + first['id'] + '.json'))
        with self.assertRaises(ConflictError):
            push(self.archive, self.remote, first['id'])

    def test_retry_exact_remote_publication_after_local_lineage_write_failure(self):
        self.seed()
        first = snapshot(self.state, self.archive)
        push(self.archive, self.remote, first['id'])
        locally_known_parent = first['id']
        (self.state / 'settings.json').write_text('{"generation":2}')
        attempted = snapshot(self.state, self.archive, parent=locally_known_parent)
        with self.assertRaises(OSError):
            push(self.archive, self.remote, attempted['id'], expected_head=locally_known_parent)
            # Simulate the caller failing after durable publication but before
            # it can atomically save the returned identity as local lineage.
            raise OSError('local receipt disk failure')
        self.assertEqual(self.remote.head('research'), attempted['id'])
        recovered = push(self.archive, self.remote, attempted['id'], expected_head=locally_known_parent)
        self.assertTrue(recovered['already_published'])
        self.assertEqual(recovered['objects_written'], 0)
        sibling = snapshot(self.state, self.archive, parent=locally_known_parent)
        with self.assertRaises(ConflictError):
            push(self.archive, self.remote, sibling['id'], expected_head=locally_known_parent)
        with self.assertRaises(ConflictError):
            push(self.archive, self.remote, attempted['id'], expected_head=None)
        self.assertEqual(self.remote.head('research'), attempted['id'])

    def test_exact_publication_retry_still_requires_intact_local_and_remote_payloads(self):
        self.seed()
        result = snapshot(self.state, self.archive)
        push(self.archive, self.remote, result['id'])
        local_object = next((self.archive / 'objects').rglob('*.gz'))
        retained = local_object.read_bytes()
        local_object.write_bytes(b'broken')
        with self.assertRaises(StorageError):
            push(self.archive, self.remote, result['id'])
        local_object.write_bytes(retained)
        remote_object = next((self.remote.root / 'objects').rglob('*.gz'))
        remote_object.unlink()
        with self.assertRaisesRegex(StorageError, 'missing chunk'):
            push(self.archive, self.remote, result['id'])

    def test_corruption_and_incomplete_snapshots_leave_no_restored_state(self):
        self.seed()
        result = snapshot(self.state, self.archive)
        obj = next((self.archive / 'objects').rglob('*.gz'))
        good = obj.read_bytes()
        obj.write_bytes(b'bad gzip')
        with self.assertRaises(StorageError):
            restore(self.archive, self.root / 'destination', result['id'])
        self.assertFalse((self.root / 'destination').exists())
        obj.write_bytes(good)
        obj.unlink()
        with self.assertRaisesRegex(StorageError, 'missing chunk'):
            push(self.archive, self.remote, result['id'])
        self.assertIsNone(self.remote.head('research'))

    def test_unsafe_manifest_paths_schema_and_chunk_lengths_rejected(self):
        self.seed()
        result = snapshot(self.state, self.archive)
        base = {k: v for k, v in result.items() if k != 'id'}
        for mode in ['traversal', 'absolute', 'schema', 'length', 'duplicate']:
            value = json.loads(json.dumps(base))
            if mode == 'traversal':
                value['files'][0]['path'] = '../escape.json'
            elif mode == 'absolute':
                value['files'][0]['path'] = '/escape.json'
            elif mode == 'schema':
                value['schema'] = 9000
            elif mode == 'length':
                value['files'][0]['chunks'] = []
            else:
                value['files'].append(value['files'][0])
            raw = json.dumps(value).encode()
            identity = hashlib.sha256(raw).hexdigest()
            LocalTransport(self.archive).put_immutable('research/manifests/' + identity + '.json', raw)
            with self.assertRaises(StorageError, msg=mode):
                restore(self.archive, self.root / 'destination', identity)
        self.assertFalse((self.root / 'escape.json').exists())

    def test_dirty_and_symlink_destinations_refused(self):
        self.seed()
        result = snapshot(self.state, self.archive)
        dest = self.root / 'destination'
        dest.mkdir()
        (dest / 'important.txt').write_text('preserve')
        with self.assertRaisesRegex(StorageError, 'dirty'):
            restore(self.archive, dest, result['id'])
        self.assertEqual((dest / 'important.txt').read_text(), 'preserve')
        alias = self.root / 'alias'
        alias.symlink_to(dest)
        with self.assertRaisesRegex(StorageError, 'Symlink'):
            restore(self.archive, alias, result['id'])

    def test_two_writers_cannot_both_publish_same_parent(self):
        self.seed()
        first = snapshot(self.state, self.archive)
        push(self.archive, self.remote, first['id'])
        second = snapshot(self.state, self.archive, parent=first['id'])
        third = snapshot(self.state, self.archive, parent=first['id'])
        barrier = threading.Barrier(2)
        outer = self
        class ConcurrentTransport(LocalTransport):
            def compare_and_swap(self, namespace, expected, identity):
                barrier.wait(timeout=5)
                return super().compare_and_swap(namespace, expected, identity)
        target = ConcurrentTransport(self.remote.root)
        outcomes = []
        def run(identity):
            try:
                push(outer.archive, target, identity, expected_head=first['id'])
                outcomes.append('published')
            except ConflictError:
                outcomes.append('conflict')
        threads = [threading.Thread(target=run, args=(m['id'],)) for m in [second, third]]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.assertEqual(sorted(outcomes), ['conflict', 'published'])

    def test_chunk_dedup_and_size_limits(self):
        (self.state / 'big.txt').write_bytes(b'x' * CHUNK_BYTES + b'tail')
        first = snapshot(self.state, self.archive)
        self.assertEqual(len(first['files'][0]['chunks']), 2)
        push(self.archive, self.remote, first['id'])
        with (self.state / 'big.txt').open('r+b') as f:
            f.seek(CHUNK_BYTES)
            f.write(b'next')
        second = snapshot(self.state, self.archive, parent=first['id'])
        self.assertEqual(push(self.archive, self.remote, second['id'], expected_head=first['id'])['objects_written'], 1)
        with self.assertRaises(StorageError):
            snapshot(self.state, self.archive, max_total_bytes=10)

    def test_experiment_namespaces_are_independent(self):
        self.seed()
        research = snapshot(self.state, self.archive)
        experiment = snapshot(self.state, self.archive, namespace='experiments/C25')
        push(self.archive, self.remote, research['id'])
        push(self.archive, self.remote, experiment['id'], namespace='experiments/C25')
        self.assertEqual(self.remote.head('research'), research['id'])
        self.assertEqual(self.remote.head('experiments/C25'), experiment['id'])
        with self.assertRaises(StorageError):
            restore(self.archive, self.root / 'bad', experiment['id'])

    def test_selected_raw_paper_is_explicit_not_default(self):
        self.seed()
        (self.state / 'raw').mkdir()
        (self.state / 'raw' / 'paper.pdf').write_bytes(b'%PDF-selected-paper')
        default = snapshot(self.state, self.archive)
        self.assertEqual([r['path'] for r in default['files']], ['settings.json'])
        selected = snapshot(self.state, self.archive, include=['raw/paper.pdf'])
        restore(self.archive, self.root / 'selected', selected['id'])
        self.assertEqual((self.root / 'selected/raw/paper.pdf').read_bytes(), b'%PDF-selected-paper')

    def test_s3_conditional_writes_reject_racing_head_and_skip_existing_payload_get(self):
        class AwsError(Exception):
            def __init__(self, code):
                self.response = {'Error': {'Code': code}}
        class FakeS3:
            def __init__(self):
                self.data = {}
                self.gets = 0
                self.race = False
                shape = SimpleNamespace(members={'IfMatch': None, 'IfNoneMatch': None})
                self.meta = SimpleNamespace(service_model=SimpleNamespace(operation_model=lambda _: SimpleNamespace(input_shape=shape)))
            def get_object(self, Bucket, Key):
                self.gets += 1
                if Key not in self.data:
                    raise AwsError('NoSuchKey')
                data, meta = self.data[Key]
                return {'Body': io.BytesIO(data), 'ETag': hashlib.sha256(data).hexdigest()}
            def head_object(self, Bucket, Key):
                if Key not in self.data:
                    raise AwsError('404')
                data, meta = self.data[Key]
                return {'ContentLength': len(data), 'Metadata': meta}
            def put_object(self, Bucket, Key, Body, **options):
                if self.race and Key.endswith('/HEAD'):
                    self.data[Key] = ((('b' * 64) + '\n').encode(), {})
                if options.get('IfNoneMatch') == '*' and Key in self.data:
                    raise AwsError('PreconditionFailed')
                if 'IfMatch' in options:
                    if Key not in self.data or hashlib.sha256(self.data[Key][0]).hexdigest() != options['IfMatch']:
                        raise AwsError('PreconditionFailed')
                self.data[Key] = (Body, options.get('Metadata', {}))
        client = FakeS3()
        target = S3Transport('example', client=client)
        self.assertTrue(target.put_immutable('objects/a', b'payload'))
        gets = client.gets
        self.assertFalse(target.put_immutable('objects/a', b'payload'))
        self.assertEqual(client.gets, gets)
        target.compare_and_swap('research', None, 'a' * 64)
        client.race = True
        with self.assertRaises(ConflictError):
            target.compare_and_swap('research', 'a' * 64, 'c' * 64)
        self.assertEqual(target.head('research'), 'b' * 64)

    def test_nested_research_evidence_retained_while_legacy_evidence_root_pruned(self):
        self.seed()
        deep = self.state / 'records/run/dossier/evidence'
        deep.mkdir(parents=True)
        (deep / 'packet.json').write_text('{"claim":"quoted primary source"}')
        (self.state / 'evidence').mkdir()
        (self.state / 'evidence' / 'old_dump.json').write_text('archive')
        result = snapshot(self.state, self.archive)
        self.assertEqual({r['path'] for r in result['files']},
                         {'settings.json', 'records/run/dossier/evidence/packet.json'})

    def test_cost_estimate_is_explicit_and_rejects_invalid_assumptions(self):
        result = estimate_cost()
        self.assertEqual(result['estimated_retained_compressed_gb'], 6.45)
        self.assertEqual(result['subtotal_usd_month'], 0.23835)
        self.assertIn('internet/cross-region egress', result['excluded'])
        for args in [{'retained_snapshots': 0}, {'current_compressed_gb': float('nan')},
                     {'puts_per_month': -1}]:
            with self.assertRaises(StorageError):
                estimate_cost(**args)

    def test_bucket_plan_never_calls_aws_and_has_no_current_expiration(self):
        plan = bucket_plan()
        self.assertEqual(plan['mode'], 'plan-only')
        self.assertTrue(plan['approval_required'])
        policy = plan['application_iam_policy']
        self.assertNotIn('s3:DeleteObject', json.dumps(policy))
        lifecycle = plan['operations'][-1]['arguments']['LifecycleConfiguration']
        for rule in lifecycle['Rules']:
            self.assertNotIn('Expiration', rule)
            if 'NoncurrentVersionExpiration' in rule:
                self.assertTrue(rule['Filter']['Prefix'].endswith('/HEAD'))
        self.assertEqual(lifecycle['Rules'][0]['NoncurrentVersionExpiration']['NewerNoncurrentVersions'], 3)


if __name__ == '__main__':
    unittest.main()

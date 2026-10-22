"""Offline S3 publication behavior; no boto3 session or cloud credentials."""
import collections
import hashlib
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ideation.storage import ConflictError, LocalTransport, S3Transport, StorageError, push, snapshot


class AwsError(Exception):
    def __init__(self, code):
        super().__init__('SECRET fake provider exception body')
        self.response = {'Error': {'Code': code}, 'ResponseMetadata': {'RetryAttempts': 0}}


class FakeS3:
    def __init__(self):
        self.data = {}
        self.calls = []
        self.fail_chunk_put = False
        self.race = False
        self.clock = 0.
        shape = SimpleNamespace(members={'IfMatch': None, 'IfNoneMatch': None})
        self.meta = SimpleNamespace(service_model=SimpleNamespace(
            operation_model=lambda _: SimpleNamespace(input_shape=shape)))

    def call(self, operation, key):
        self.calls.append((operation, key))
        self.clock += .25

    def get_object(self, Bucket, Key):
        self.call('get', Key)
        if Key not in self.data:
            raise AwsError('NoSuchKey')
        data, meta = self.data[Key]
        return {'Body': io.BytesIO(data), 'ETag': hashlib.sha256(data).hexdigest(),
                'ResponseMetadata': {'RetryAttempts': 0}}

    def head_object(self, Bucket, Key):
        self.call('head', Key)
        if Key not in self.data:
            raise AwsError('404')
        data, meta = self.data[Key]
        return {'ContentLength': len(data), 'Metadata': meta,
                'ResponseMetadata': {'RetryAttempts': 0}}

    def put_object(self, Bucket, Key, Body, **options):
        self.call('put', Key)
        if self.fail_chunk_put and '/objects/' in Key:
            raise AwsError('AccessDenied')
        if self.race and Key.endswith('/HEAD'):
            self.data[Key] = ((('b' * 64) + '\n').encode(), {})
        if options.get('IfNoneMatch') == '*' and Key in self.data:
            raise AwsError('PreconditionFailed')
        if 'IfMatch' in options:
            if Key not in self.data or hashlib.sha256(self.data[Key][0]).hexdigest() != options['IfMatch']:
                raise AwsError('PreconditionFailed')
        self.data[Key] = (Body, options.get('Metadata', {}))
        return {'ResponseMetadata': {'RetryAttempts': 0}}


class PublicationDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.archive = self.root / 'archive'
        self.client = FakeS3()
        self.target = S3Transport('SECRET-bucket', prefix='state', client=self.client)

    def tearDown(self):
        self.tmp.cleanup()

    def seed(self):
        for name, value in [('a.txt', b'one'), ('b.txt', b'one'), ('c.txt', b'two')]:
            (self.state / name).write_bytes(value)
        return snapshot(self.state, self.archive)

    def object_key(self, digest):
        return 'objects/sha256/' + digest[:2] + '/' + digest + '.gz'

    def test_one_head_per_unique_chunk_missing_puts_and_measured_phases(self):
        manifest = self.seed()
        existing = manifest['files'][0]['chunks'][0]['sha256']
        key = self.object_key(existing)
        self.target.put_immutable(key, LocalTransport(self.archive).get(key))
        self.client.calls.clear()
        # Clock advances only during fake SDK calls: measured remote phases
        # must reflect those calls, not the count of repeated file references.
        with patch('ideation.storage.time.monotonic', side_effect=lambda: self.client.clock):
            result = push(self.archive, self.target, manifest['id'])
        heads = collections.Counter(k for op, k in self.client.calls if op == 'head' and '/objects/' in k)
        self.assertEqual(sorted(heads.values()), [1, 1])
        self.assertEqual(result['objects_written'], 1)
        diag = result['diagnostics']
        self.assertEqual(diag['counts']['duplicate_transfer_checks_skipped'], 1)
        self.assertEqual(diag['counts']['files_verified'], 3)
        self.assertEqual(diag['counts']['chunk_transfer_checks'], 2)
        missing = next(x['sha256'] for r in manifest['files'] for x in r['chunks'] if x['sha256'] != existing)
        self.assertEqual(diag['counts']['compressed_chunk_bytes_written'],
                         len(LocalTransport(self.archive).get(self.object_key(missing))))
        self.assertEqual(diag['s3_requests']['head_calls'], 3)  # chunks + manifest
        self.assertEqual(diag['s3_requests']['put_calls'], 3)  # missing chunk + manifest + HEAD
        self.assertEqual(diag['s3_requests']['get_calls'], 2)
        self.assertEqual(diag['phase_seconds']['immutable_chunk_transfer'], .75)
        self.assertEqual(diag['phase_seconds']['head_compare_and_swap'], .5)
        self.assertEqual(diag['total_seconds'], 2.)
        self.assertEqual(diag['s3_requests']['reported_retry_attempts'], 0)
        self.assertEqual(diag['s3_requests']['responses_with_retry_metadata'], 8)
        self.assertNotIn('SECRET', json.dumps(diag))
        # Retry recovery still validates payloads and cannot claim fresh uploads.
        recovered = push(self.archive, self.target, manifest['id'])
        self.assertTrue(recovered['already_published'])
        self.assertEqual(recovered['diagnostics']['counts']['compressed_chunk_bytes_written'], 0)
        self.assertEqual(recovered['diagnostics']['s3_requests'].get('put_calls', 0), 0)

    def test_upload_failure_keeps_head_unpublished_and_safe_partial_diagnostics(self):
        manifest = self.seed()
        self.client.fail_chunk_put = True
        with self.assertRaises(AwsError) as caught:
            push(self.archive, self.target, manifest['id'])
        self.assertNotIn('state/research/HEAD', self.client.data)
        self.assertFalse(any('/manifests/' in k for k in self.client.data))
        diag = caught.exception.publication_diagnostics
        self.assertEqual(diag['counts']['chunk_objects_written'], 0)
        self.assertEqual(diag['s3_requests']['put_failed'], 1)
        self.assertIn('immutable_chunk_transfer', diag['phase_seconds'])
        self.assertNotIn('SECRET', json.dumps(diag))
        self.client.fail_chunk_put = False
        self.assertEqual(push(self.archive, self.target, manifest['id'])['objects_written'], 2)

    def test_cas_race_preserves_other_head_and_original_exception_type(self):
        manifest = self.seed()
        self.client.race = True
        with self.assertRaises(ConflictError) as caught:
            push(self.archive, self.target, manifest['id'])
        self.assertEqual(self.client.data['state/research/HEAD'][0].decode().strip(), 'b' * 64)
        self.assertIn('head_compare_and_swap', caught.exception.publication_diagnostics['phase_seconds'])
        self.assertEqual(caught.exception.publication_diagnostics['s3_requests']['put_failed'], 1)
        self.assertIsNone(LocalTransport(self.archive).head('research'))
        # Stale expected parent still fails before immutable transfer.
        with self.assertRaises(ConflictError) as stale:
            push(self.archive, self.target, manifest['id'])
        self.assertEqual(stale.exception.publication_diagnostics['counts']['chunk_transfer_checks'], 0)

    def test_duplicate_transfer_does_not_skip_corrupt_file_validation(self):
        manifest = self.seed()
        raw = json.loads(LocalTransport(self.archive).get('research/manifests/' + manifest['id'] + '.json'))
        raw['files'][1]['sha256'] = 'f' * 64  # Same chunk, invalid second file digest.
        data = json.dumps(raw, sort_keys=True, separators=(',', ':')).encode()
        identity = hashlib.sha256(data).hexdigest()
        LocalTransport(self.archive).put_immutable('research/manifests/' + identity + '.json', data)
        with self.assertRaises(StorageError) as caught:
            push(self.archive, self.target, identity)
        self.assertIn('File checksum mismatch', str(caught.exception))
        diag = caught.exception.publication_diagnostics
        self.assertEqual(diag['counts']['duplicate_transfer_checks_skipped'], 1)
        self.assertEqual(diag['counts']['files_verified'], 1)
        self.assertNotIn('state/research/HEAD', self.client.data)
        self.assertFalse(any('/manifests/' in k for k in self.client.data))

    def test_retry_metadata_is_optional_and_never_inferred(self):
        manifest = self.seed()
        original = self.client.head_object
        def metadata_response(**args):
            response = original(**args)
            response['ResponseMetadata'] = {'RetryAttempts': 2, 'request': 'SECRET'}
            return response
        self.client.head_object = metadata_response
        # Seed one existing chunk so its HEAD has the controlled retry metadata.
        digest = manifest['files'][0]['chunks'][0]['sha256']
        key = self.object_key(digest)
        self.target.put_immutable(key, LocalTransport(self.archive).get(key))
        result = push(self.archive, self.target, manifest['id'])
        self.assertEqual(result['diagnostics']['s3_requests']['reported_retry_attempts'], 2)
        self.assertNotIn('SECRET', json.dumps(result['diagnostics']))

    def test_absent_retry_metadata_stays_unknown(self):
        manifest = self.seed()
        def without_retry_metadata(method):
            def call(**args):
                try:
                    response = method(**args)
                except AwsError as error:
                    error.response.pop('ResponseMetadata', None)
                    raise
                response.pop('ResponseMetadata', None)
                return response
            return call
        for name in ['get_object', 'head_object', 'put_object']:
            setattr(self.client, name, without_retry_metadata(getattr(self.client, name)))
        result = push(self.archive, self.target, manifest['id'])
        self.assertNotIn('reported_retry_attempts', result['diagnostics']['s3_requests'])
        self.assertNotIn('responses_with_retry_metadata', result['diagnostics']['s3_requests'])
        self.assertIsNone(self.target._publication_requests.get())

    def test_shared_transport_parallel_push_diagnostics_are_isolated(self):
        barrier = threading.Barrier(2)
        original = self.client.get_object
        def interleaved_get(**args):
            if args['Key'].endswith('/HEAD'):
                barrier.wait(timeout=3)
            return original(**args)
        self.client.get_object = interleaved_get
        manifests = []
        for name in ['first', 'second']:
            directory = self.root / name
            directory.mkdir()
            (directory / 'unique.txt').write_text(name)
            manifests.append(snapshot(directory, self.archive, namespace='experiments/' + name))
        results, errors = [], []
        def publish(manifest):
            try:
                results.append(push(self.archive, self.target, manifest['id'], namespace=manifest['namespace']))
            except Exception as error:
                errors.append(error)
        threads = [threading.Thread(target=publish, args=(manifest,)) for manifest in manifests]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        for result in results:
            counts = result['diagnostics']['s3_requests']
            self.assertEqual((counts['get_calls'], counts['head_calls'], counts['put_calls']), (2, 2, 3))

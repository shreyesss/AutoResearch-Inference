import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.hypothesis_artifacts import resolve_artifact
from ideation.hypothesis_memory import HypothesisMemory
from ideation.storage import snapshot, restore


class HypothesisArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / 'original'
        self.file = self.root / 'research/records/run/result.json'
        self.file.parent.mkdir(parents=True)
        self.file.write_text('{"scope":"CPU fixture"}')
        self.memory = HypothesisMemory(self.root / 'research/hypotheses.sqlite')
        self.hid = self.memory.register('run', {'id': 'H', 'mechanism': 'fixture', 'proposed_change': 'retention'}, {'baseline': {'id': 'fixture'}}, {})
        self.test = self.memory.plan_test(self.hid, {'request_id': 'one'}, {'kind': 'cpu'})

    def tearDown(self):
        self.memory.db.close()
        self.temp.cleanup()

    def record(self, legacy=False):
        if legacy:
            value = {'path': str(self.file.resolve()), 'sha256': hashlib.sha256(self.file.read_bytes()).hexdigest(), 'bytes': self.file.stat().st_size}
            with patch('ideation.hypothesis_memory.artifact_reference', return_value=value):
                return self.memory.test_result(self.test['id'], 'inconclusive', self.file, 'fixture')
        return self.memory.test_result(self.test['id'], 'inconclusive', self.file, 'fixture')

    def relocate(self):
        self.memory.db.close()
        archive = self.base / 'archive'
        manifest = snapshot(self.root, archive)
        dest = self.base / 'restored'
        restore(archive, dest, manifest['id'])
        shutil.rmtree(self.root)
        self.root = dest
        self.file = dest / 'research/records/run/result.json'
        self.memory = HypothesisMemory(dest / 'research/hypotheses.sqlite')

    def assert_portable_retry(self, event, method):
        original_data = json.dumps(event, sort_keys=True)
        self.relocate()
        before = self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0]
        value = self.memory.get(self.hid)
        projection = value['resolved_artifacts'][0]
        self.assertEqual(projection['resolution_status'], 'verified')
        self.assertEqual(projection['resolution_method'], method)
        self.assertEqual(Path(projection['resolved_local_file']), self.file.resolve())
        retried = self.memory.test_result(self.test['id'], 'inconclusive', self.file, 'fixture')
        self.assertEqual(json.dumps(retried, sort_keys=True), original_data)
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0], before)

    def test_new_state_relative_artifact_survives_actual_restore(self):
        event = self.record()
        self.assertEqual(event['data']['artifact']['path_base'], 'state')
        self.assertEqual(event['data']['artifact']['path'], 'research/records/run/result.json')
        self.assert_portable_retry(event, 'state_relative')

    def test_legacy_record_resolves_without_mutating_event_or_retry_id(self):
        event = self.record(legacy=True)
        self.assertNotIn('path_base', event['data']['artifact'])
        self.assert_portable_retry(event, 'legacy_records_suffix')

    def test_corrupt_restored_artifact_is_not_resolved_or_retry_accepted(self):
        self.record(legacy=True)
        self.relocate()
        self.file.write_text('{"scope":"BAD fixture"}')
        result = self.memory.get(self.hid)['resolved_artifacts'][0]
        self.assertIn(result['resolution_status'], ('size_mismatch', 'hash_mismatch'))
        self.assertNotIn('resolved_local_file', result)
        with self.assertRaisesRegex(ValueError, 'repeat test'):
            self.memory.test_result(self.test['id'], 'inconclusive', self.file, 'fixture')

    def test_missing_reference_and_modified_report_stay_explicit(self):
        self.record()
        with self.assertRaisesRegex(ValueError, 'repeat test'):
            self.memory.test_result(self.test['id'], 'validated', self.file, 'fixture')
        self.file.unlink()
        self.assertEqual(self.memory.get(self.hid)['resolved_artifacts'][0]['resolution_status'], 'missing')

    def test_traversal_and_symlink_escape_cannot_resolve(self):
        event = self.record()
        value = event['data']['artifact']
        self.assertEqual(resolve_artifact(self.root, {**value, 'path': '../outside.json'})['resolution_status'], 'invalid_reference')
        external = self.base / 'outside.json'
        external.write_bytes(self.file.read_bytes())
        self.file.unlink()
        self.file.symlink_to(external)
        result = resolve_artifact(self.root, value)
        self.assertEqual(result['resolution_status'], 'outside_state_root')
        self.assertNotIn('resolved_local_file', result)

    def test_external_and_ambiguous_paths_are_not_searched_by_basename(self):
        value = self.record()['data']['artifact']
        for path in ('/other/location/result.json', '/other/research/records/x/research/records/run/result.json'):
            result = resolve_artifact(self.root, {k: v for k, v in {**value, 'path': path}.items() if k != 'path_base'})
            self.assertEqual(result['resolution_status'], 'external_not_retained')
        wrong = self.root / 'research/records/other/result.json'
        wrong.parent.mkdir(parents=True)
        wrong.write_bytes(self.file.read_bytes())
        with self.assertRaisesRegex(ValueError, 'repeat test'):
            self.memory.test_result(self.test['id'], 'inconclusive', wrong, 'fixture')

    def test_same_size_wrong_content_fails_hash_check(self):
        value = self.record()['data']['artifact']
        self.file.write_bytes(b'x' * self.file.stat().st_size)
        self.assertEqual(resolve_artifact(self.root, value)['resolution_status'], 'hash_mismatch')

    def test_external_new_artifact_explicitly_not_retained(self):
        external = self.base / 'outside.json'
        external.write_text('external fixture')
        event = self.memory.test_result(self.test['id'], 'inconclusive', external, 'outside')
        self.assertNotIn('path_base', event['data']['artifact'])
        self.assertEqual(self.memory.get(self.hid)['resolved_artifacts'][0]['resolution_status'], 'external_not_retained')
        self.assertEqual(event, self.memory.test_result(self.test['id'], 'inconclusive', external, 'outside'))

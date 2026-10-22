import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.foundation import invoke, PublicationError
from ideation.hypothesis_artifacts import retain_artifacts, resolve_artifact, INDEX_REL, TEXT_LIMIT
from ideation.storage import restore


class ArtifactRetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / 'state'
        self.source = self.root / 'research/records/run/replay.py'
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'raise RuntimeError("never execute")\r\n')
        self.manifest = self.make_manifest(self.source)

    def tearDown(self):
        self.tmp.cleanup()

    def make_manifest(self, *paths):
        return {'reviewed': True, 'provenance': 'Explicit reviewed CPU fixture', 'artifacts': [
            {'path': p.relative_to(self.root).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
            for p in paths]}

    def ref(self):
        return {**self.manifest['artifacts'][0], 'path_base': 'state'}

    def retain(self, manifest=None):
        # CLI supplies the writer lock in production; this fixture has one writer.
        return retain_artifacts(self.root, manifest or self.manifest)

    def test_cli_snapshot_restore_exact_bytes_and_idempotence(self):
        html = self.source.with_name('paper.html'); html.write_bytes(b'<p>evidence</p>\r\n')
        cpp = self.source.with_name('kernel.cpp'); cpp.write_bytes(b'// archived, never compiled\n')
        tokenizer = self.source.with_name('cpu_tokenizer_audit.py'); tokenizer.write_text('# public tokenizer fixture')
        tokenizer_json = self.source.with_name('tokenizer.json'); tokenizer_json.write_text('{"kind":"public fixture"}')
        manifest = self.make_manifest(self.source, html, cpp, tokenizer, tokenizer_json)
        path = self.base / 'selection.json'; path.write_text(json.dumps(manifest))
        args = ['--state-dir', str(self.root), '--local-only', '--defer-snapshot', 'hypothesis', 'retain-artifacts', '--manifest', str(path)]
        result = invoke(args)
        self.assertEqual(result['retention']['mappings_added'], 5)
        self.assertTrue(result['snapshot']['deferred'])
        old = (self.root / INDEX_REL).read_bytes()
        self.assertEqual(invoke(args)['retention']['mappings_added'], 0)
        self.assertEqual((self.root / INDEX_REL).read_bytes(), old)
        snap = invoke(['--state-dir', str(self.root), '--local-only', 'snapshot', '--namespace', 'research'])
        restored = self.base / 'relocated'
        restore(self.root/'archives', restored/'research', snap['id'])
        for item in manifest['artifacts']:
            value = resolve_artifact(restored, {**item, 'path_base': 'state'})
            self.assertEqual(value['resolution_status'], 'verified')
            self.assertEqual(value['resolution_method'], 'retained_text_copy')
            self.assertEqual(Path(value['resolved_local_file']).read_bytes(), (self.root/item['path']).read_bytes())
            self.assertFalse((restored/item['path']).exists())
        self.assertTrue((self.root/'commands.sqlite').exists())

    def test_fallback_only_missing_original_not_hash_size_or_directory(self):
        self.retain()
        ref = self.ref()
        self.source.write_bytes(b'x' * self.source.stat().st_size)
        self.assertEqual(resolve_artifact(self.root, ref)['resolution_status'], 'hash_mismatch')
        self.source.write_bytes(b'x')
        self.assertEqual(resolve_artifact(self.root, ref)['resolution_status'], 'size_mismatch')
        self.source.unlink(); self.source.mkdir()
        self.assertEqual(resolve_artifact(self.root, ref)['resolution_status'], 'invalid_path')
        self.source.rmdir()
        self.assertEqual(resolve_artifact(self.root, ref)['resolution_status'], 'verified')
        self.assertEqual(resolve_artifact(self.root, {**ref, 'bytes': 999})['resolution_status'], 'size_mismatch')

    def test_wronghash_or_missing_in_batch_prevents_mutation(self):
        other = self.source.with_name('other.py'); other.write_text('other')
        manifest = self.make_manifest(self.source, other)
        manifest['artifacts'][1]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.retain(manifest)
        self.assertFalse((self.root/'research/artifacts').exists())
        other.unlink()
        with self.assertRaises(ValueError): self.retain(manifest)
        self.assertFalse((self.root/'research/artifacts').exists())

    def test_paths_secrets_and_symlinks(self):
        for bad in ['/tmp/replay.py', 'research/records/../replay.py', 'research/records//run.py',
                    'research/records/run/.env', 'research/records/run/api_key.py',
                    'research/records/run/credentials.json', 'research/records/run/id_ed25519',
                    'research/records/run/key.pem', 'research/records/run/ssh_host_key',
                    'research/records/run/token.txt', 'research/records/run/access_token.json',
                    'research/records/run/tokenizer_access_token.json']:
            m = json.loads(json.dumps(self.manifest)); m['artifacts'][0]['path'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): self.retain(m)
        self.source.unlink(); self.source.symlink_to(self.base/'missing.py')
        with self.assertRaises(ValueError): self.retain()
        self.source.unlink(); self.source.write_text('-----BEGIN OPENSSH PRIVATE KEY-----\nsecret')
        with self.assertRaisesRegex(ValueError, 'Private key'): self.retain(self.make_manifest(self.source))
        self.assertFalse((self.root/'research/artifacts').exists())

    def test_binary_and_size_skips_explicit(self):
        png = self.source.with_name('diagram.png'); png.write_bytes(b'\x89PNG\x00\xff')
        big = self.source.with_name('large.txt')
        with big.open('wb') as f: f.truncate(TEXT_LIMIT+1)
        result = self.retain(self.make_manifest(self.source, png, big))
        self.assertEqual([r['status'] for r in result['artifacts']], ['retained_verified','unsupported_non_utf8_text','unsupported_size'])
        self.assertEqual(result['mappings_added'], 1)

    def test_partial_failure_retry_adopts_verified_orphan_without_overwrite(self):
        with patch('ideation.hypothesis_artifacts._append_mapping', side_effect=OSError('fixture')):
            with self.assertRaises(OSError): self.retain()
        digest = self.ref()['sha256']; blob = self.root/f'research/artifacts/{digest}.txt'
        self.assertEqual(blob.read_bytes(), self.source.read_bytes())
        self.assertEqual(self.retain()['mappings_added'], 1)
        blob.write_text('corrupt')
        before = (self.root/INDEX_REL).read_bytes()
        with self.assertRaisesRegex(ValueError, 'copy differs'): self.retain()
        self.assertEqual(blob.read_text(), 'corrupt')
        self.assertEqual((self.root/INDEX_REL).read_bytes(), before)
        self.source.unlink()
        self.assertEqual(resolve_artifact(self.root,self.ref())['resolution_status'],'retained_copy_hash_mismatch')

    def test_corrupt_mapping_and_symlink_copy_fail_closed(self):
        self.retain(); ref=self.ref(); self.source.unlink()
        index=self.root/INDEX_REL; original=index.read_bytes(); index.write_text('{broken')
        self.assertEqual(resolve_artifact(self.root,ref)['resolution_status'],'invalid_retained_mapping')
        index.write_bytes(original)
        blob=self.root/f"research/artifacts/{ref['sha256']}.txt"; raw=blob.read_bytes(); blob.unlink()
        outside=self.base/'copy.txt';outside.write_bytes(raw);blob.symlink_to(outside)
        self.assertEqual(resolve_artifact(self.root,ref)['resolution_status'],'invalid_retained_mapping')

    def test_legacy_fallback_does_not_rewrite_reference(self):
        self.retain(); ref=self.ref(); ref.pop('path_base');ref['path']='/old/state/'+ref['path']
        original=json.dumps(ref,sort_keys=True); self.source.unlink()
        self.assertEqual(resolve_artifact(self.root,ref)['resolution_status'],'verified')
        self.assertEqual(json.dumps(ref,sort_keys=True),original)

    def test_checkpoint_failure_preserves_original_error_context(self):
        path = self.base / 'manifest.json'; path.write_text(json.dumps(self.manifest))
        publication = PublicationError({'published': False}, RuntimeError('offline fixture'))
        with patch('ideation.hypothesis_artifacts._append_mapping', side_effect=OSError('copy fixture')), \
             patch('ideation.foundation._research_snapshot', side_effect=publication):
            with self.assertRaises(PublicationError) as raised:
                invoke(['--state-dir',str(self.root),'--local-only','hypothesis','retain-artifacts','--manifest',str(path)])
        self.assertEqual(raised.exception.mutation_error_type, 'OSError')
        self.assertIsInstance(raised.exception.__cause__, OSError)

    def test_duplicate_selection_conflicts_fail_before_mutation(self):
        for field, value in [('bytes', self.source.stat().st_size + 1), ('provenance', 'conflicting description')]:
            manifest = json.loads(json.dumps(self.manifest))
            duplicate = dict(manifest['artifacts'][0]); duplicate[field] = value
            manifest['artifacts'].append(duplicate)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Conflicting duplicate'):
                self.retain(manifest)
            self.assertFalse((self.root/'research/artifacts').exists())
        manifest = json.loads(json.dumps(self.manifest))
        manifest['artifacts'].append(dict(manifest['artifacts'][0]))
        self.assertEqual(self.retain(manifest)['mappings_added'], 1)

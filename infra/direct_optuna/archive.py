"""Freeze or verify the completed study, including raw requests and logs.

No model files are included. This command does not start Docker or benchmarks.
"""
import argparse
import gzip
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.artifacts/optuna-direct-v1'
DEST = ROOT / 'results/2026-10-18-direct-optuna/evidence'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify():
    manifest = json.loads((DEST / 'manifest.json').read_text())
    archive = DEST / manifest['archive']
    assert digest(archive) == manifest['archive_sha256'], 'Archive hash mismatch'
    expected = {r['path']: r for r in manifest['files']}
    seen = set()
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle:
            path = Path(member.name)
            assert member.isfile() and not path.is_absolute() and '..' not in path.parts
            assert member.name not in seen and member.name in expected
            entry = expected[member.name]
            assert member.size == entry['bytes']
            with bundle.extractfile(member) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256'], member.name
            seen.add(member.name)
    assert seen == set(expected), 'Incomplete archive'
    print(f'Verified {len(seen)} files; {archive.stat().st_size:,} compressed bytes.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify()
        return
    DEST.mkdir(parents=True, exist_ok=True)
    target = DEST / 'study.tar.gz'
    if target.exists() or (DEST / 'manifest.json').exists():
        raise SystemExit('Existing evidence snapshot: use --verify; do not overwrite completed research.')
    receipts = {p: json.loads((SOURCE / f'{p}-finished.json').read_text()) for p in ('search', 'confirmation')}
    files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    assert not any(p.is_symlink() for p in SOURCE.rglob('*')), 'Symlinks are not archived'
    entries = [{'path': str(p.relative_to(SOURCE)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]
    temp = target.with_suffix('.tmp')
    with temp.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w|') as bundle:
            for p, entry in zip(files, entries):
                info = bundle.gettarinfo(str(p), arcname=entry['path'])
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mtime = 0
                with p.open('rb') as stream:
                    bundle.addfile(info, stream)
    assert all(digest(p) == e['sha256'] for p, e in zip(files, entries)), 'Study changed during archival'
    temp.replace(target)
    manifest = {'study_id': 'optuna-direct-v1', 'source_directory': str(SOURCE.relative_to(ROOT)),
                'archive': target.name, 'archive_sha256': digest(target), 'archive_bytes': target.stat().st_size,
                'uncompressed_bytes': sum(e['bytes'] for e in entries), 'completion_receipts': receipts,
                'scope': 'Complete study directory, including frozen inputs, native requests, databases, logs, failed preflights and explicitly labelled mock client smoke. No model weights or dependency environment.',
                'files': entries}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for name in ('search-trials.json', 'confirmation-trials.json', 'search-protocol.json',
                 'confirmation-protocol.json', 'confirmation-selection.json', 'confirmation-recovery.json',
                 'search-resolved-config.json', 'confirmation-resolved-config.json',
                 'search-source-hashes.json', 'confirmation-source-hashes.json'):
        (DEST / name).write_bytes((SOURCE / name).read_bytes())
    verify()


if __name__ == '__main__':
    main()

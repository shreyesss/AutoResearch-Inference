"""Restore and verify the AV k5 diagnostic evidence into a new directory (Python 3.10+)."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    catalog = json.loads((root / 'ARCHIVES.json').read_text())
    if args.destination.exists():
        parser.error('destination must not exist; original worktrees are never overwritten')
    for group in catalog['groups']:
        assert len(group['parts']) == 1, 'expected one Git LFS archive per group'
        archive = root / group['parts'][0]['path']
        if digest(archive) != group['archive_sha256']:
            raise ValueError(f'archive hash mismatch: {archive}; run git lfs pull first')
    args.destination.mkdir(parents=True)
    total = 0
    for group in catalog['groups']:
        archive = root / group['parts'][0]['path']
        expected = {item['path']: item for item in json.loads((root / group['manifest']).read_text())}
        proc = subprocess.Popen(['zstd', '-q', '-d', '-c', str(archive)], stdout=subprocess.PIPE)
        seen = set()
        try:
            with tarfile.open(fileobj=proc.stdout, mode='r|') as tar:
                for member in tar:
                    path = PurePosixPath(member.name)
                    if path.is_absolute() or '..' in path.parts or not member.isfile():
                        raise ValueError(f'unsafe archive member: {member.name}')
                    if member.name not in expected or member.name in seen:
                        raise ValueError(f'unexpected/duplicate member: {member.name}')
                    target = args.destination.joinpath(*path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, target.open('xb') as output:
                        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
                            output.write(chunk)
                    # Preserve executable/read-only source modes, never privilege bits.
                    target.chmod(member.mode & 0o777)
                    item = expected[member.name]
                    if target.stat().st_size != item['bytes'] or digest(target) != item['sha256']:
                        raise ValueError(f'restored file mismatch: {member.name}')
                    seen.add(member.name)
            if proc.wait() != 0 or seen != set(expected):
                raise ValueError(f'incomplete archive: {group["name"]}')
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdout.close()
        total += len(seen)
        print(f'{group["name"]}: verified {len(seen)} files')
    print(f'Restored and verified {total} files under {args.destination}')


if __name__ == '__main__':
    main()

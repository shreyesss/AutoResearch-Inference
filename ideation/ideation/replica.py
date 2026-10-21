"""Immutable versioned read replicas; never replace a node's writer databases."""
from pathlib import Path
import hashlib


def sync(root, transport, namespace='research', manifest_id=None):
    from .foundation import _write, _read
    from .storage import pull, restore
    identity = manifest_id or transport.head(namespace)
    current = _read(root / 'replicas' / namespace / 'CURRENT.json', {})
    if identity and current.get('id') == identity and Path(current['path']).is_dir():
        return {**current, 'already_current': True}
    value = pull(transport, root / 'archives', namespace=namespace, manifest_id=identity)
    identity = value['id']
    base = root / 'replicas' / namespace
    destination = base / identity
    marker = base / (identity + '.verified.json')
    if not marker.exists():
        if destination.exists():
            # Recover a crash between atomic restore and marker publication.
            # An altered destination is never overwritten or marked valid.
            for row in value['files']:
                path = destination / row['path']
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Incomplete or altered replica')
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if path.stat().st_size != row['bytes'] or digest != row['sha256']:
                    raise ValueError('Replica checksum mismatch')
        else:
            restore(root / 'archives', destination, identity, namespace=namespace)
        _write(marker, {'id': identity, 'files': len(value['files'])})
    elif not destination.is_dir():
        raise ValueError('Replica marker exists but directory is missing')
    pointer = {'id': identity, 'path': str(destination), 'namespace': namespace,
               'read_only_replica': True, 'writer_state_modified': False}
    _write(base / 'CURRENT.json', pointer)
    return pointer

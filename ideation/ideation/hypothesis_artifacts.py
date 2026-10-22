"""Portable, hash-verified projections for hypothesis test artifacts.

These helpers never rewrite immutable evidence or search the filesystem by name.
Only an explicit state-relative path or an unambiguous legacy research/records
suffix can relocate a record. External files are not implicitly retained.
"""
import hashlib
import json
import os
import tempfile
import re
from pathlib import Path, PurePosixPath


def state_root(memory_path):
    parent = Path(memory_path).resolve().parent
    return parent.parent if parent.name == "research" else parent


def artifact_reference(root, path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("A readable test artifact file is required")
    record = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    try:
        relative = path.relative_to(Path(root).resolve())
    except ValueError:
        return record  # Explicit external reference; no retention is promised.
    return {**record, "path": relative.as_posix(), "path_base": "state"}


def resolve_artifact(root, record):
    """Return a read-time projection, never an edited historical record."""
    result = {"original_reference": dict(record), "sha256": record.get("sha256")}
    root = Path(root).resolve()
    raw = record.get("path")
    if not isinstance(raw, str) or not raw or "\\" in raw:
        return {**result, "resolution_status": "invalid_path"}
    path = PurePosixPath(raw)
    if ".." in path.parts or not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", ""))):
        return {**result, "resolution_status": "invalid_reference"}
    if record.get("path_base") == "state":
        if path.is_absolute():
            return {**result, "resolution_status": "invalid_path"}
        relative = path
        method = "state_relative"
    elif record.get("path_base") is not None:
        return {**result, "resolution_status": "invalid_path_base"}
    elif path.is_absolute():
        try:
            relative = Path(raw).relative_to(root)
            method = "legacy_current_root"
        except ValueError:
            # No basename matching, arbitrary old-root probing, or global search.
            offsets = [i for i in range(len(path.parts)-1)
                       if path.parts[i:i+2] == ("research", "records")]
            if len(offsets) != 1 or offsets[0]+2 >= len(path.parts):
                return {**result, "resolution_status": "external_not_retained"}
            relative = PurePosixPath(*path.parts[offsets[0]:])
            method = "legacy_records_suffix"
    else:
        return {**result, "resolution_status": "unbased_relative_path"}
    try:
        candidate = (root / relative).resolve()
    except (OSError, RuntimeError):
        return {**result, "resolution_status": "invalid_path"}
    try:
        candidate.relative_to(root)
    except ValueError:
        return {**result, "resolution_status": "outside_state_root"}
    result.update(state_relative_path=relative.as_posix(), resolution_method=method)
    try:
        if not candidate.is_file():
            # Existing directories/dangling symlinks are not missing originals.
            original = root / relative
            if original.exists() or original.is_symlink():
                return {**result, 'resolution_status': 'invalid_path'}
            try:
                _safe_local(root, relative)
            except ValueError:
                return {**result, 'resolution_status': 'invalid_path'}
            return _retained_fallback(root, relative, record, result)
        if "bytes" in record and (type(record["bytes"]) is not int or record["bytes"] < 0 or candidate.stat().st_size != record["bytes"]):
            return {**result, "resolution_status": "size_mismatch"}
        if hashlib.sha256(candidate.read_bytes()).hexdigest() != record["sha256"]:
            return {**result, "resolution_status": "hash_mismatch"}
    except OSError:
        return {**result, "resolution_status": "unreadable"}
    return {**result, "resolution_status": "verified", "resolved_local_file": str(candidate)}


# Explicitly reviewed evidence only; these bytes are never imported or executed.
TEXT_LIMIT = 16 * 1024 * 1024
BATCH_LIMIT = 64 * 1024 * 1024
INDEX_REL = 'research/artifacts/index.jsonl'


def _sensitive_name(value):
    name = value.lower()
    # Only these whole public-source word segments may contain "token".
    # Authorization still requires an explicit reviewed path/hash manifest.
    without_source_terms = re.sub(r'(^|[_.-])(tokenizer|tokenization)(?=$|[_.-])', r'\1', name)
    return any(t in name for t in ('credential', 'secret', 'private_key', 'access_key', 'api_key')) or 'token' in without_source_terms


def _safe_selected_path(value):
    if not isinstance(value, str) or '\\' in value or '\x00' in value:
        raise ValueError('Invalid artifact path')
    parts = value.split('/')
    if len(parts) < 4 or parts[:2] != ['research', 'records'] or any(x in ('', '.', '..') for x in parts):
        raise ValueError('Artifacts must be state-relative research/records files')
    if any(x.startswith('.') or x.lower().startswith(('id_rsa', 'id_ed25519', 'id_ecdsa')) or
           _sensitive_name(x)
           for x in parts):
        raise ValueError('Sensitive artifact path is excluded')
    if Path(value).suffix.lower() in ('.pem', '.key', '.p12', '.pfx') or Path(value).name.lower() in ('authorized_keys', 'known_hosts') or Path(value).name.lower().endswith('_key'):
        raise ValueError('Key files are excluded')
    return value


def _safe_local(root, relative):
    path = root / relative
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError('Symlink artifact paths are excluded')
        if item == root:
            break
    if not path.resolve().is_relative_to(root):
        raise ValueError('Artifact escapes state root')
    return path


def _mapping(root):
    path = _safe_local(root, INDEX_REL)
    if not path.exists():
        return {}
    if path.stat().st_size > TEXT_LIMIT:
        raise ValueError('Artifact mapping exceeds size limit')
    result = {}
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            _safe_selected_path(row['original_path'])
            digest = row['sha256']
            if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('Invalid retained digest')
            if type(row['bytes']) is not int or not 0 <= row['bytes'] <= TEXT_LIMIT:
                raise ValueError('Invalid retained size')
            if row['blob_path'] != f'research/artifacts/{digest}.txt' or not isinstance(row.get('provenance'), str) or not row['provenance'].strip():
                raise ValueError('Invalid retained mapping')
            key = (row['original_path'], digest)
            if key in result and result[key] != row:
                raise ValueError('Conflicting retained mapping')
            result[key] = row
    return result


def _retained_fallback(root, relative, record, result):
    try:
        mapping = _mapping(root)
        row = mapping.get((relative.as_posix(), record['sha256']))
        if row is None:
            return {**result, 'resolution_status': 'missing'}
        if 'bytes' in record and (type(record['bytes']) is not int or record['bytes'] != row['bytes']):
            return {**result, 'resolution_status': 'size_mismatch'}
        path = _safe_local(root, row['blob_path'])
        if not path.is_file():
            return {**result, 'resolution_status': 'retained_copy_missing'}
        if path.stat().st_size != row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            return {**result, 'resolution_status': 'retained_copy_hash_mismatch'}
        return {**result, 'resolution_status': 'verified', 'resolution_method': 'retained_text_copy',
                'retained_state_relative_path': row['blob_path'], 'resolved_local_file': str(path)}
    except (OSError, ValueError, KeyError, TypeError):
        return {**result, 'resolution_status': 'invalid_retained_mapping'}


def _append_mapping(path, row):
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def retain_artifacts(root, manifest):
    """Caller holds the research writer lock; retain explicit reviewed UTF-8 bytes.

    All source hashes and existing copies are checked before mutations. A failed
    append can leave a verified orphan blob; retry adopts it without overwrite.
    A torn/invalid index fails closed and needs explicit recovery.
    """
    root = Path(root).absolute()
    if root.is_symlink():
        raise ValueError('State root cannot be a symlink')
    root = root.resolve()
    if not isinstance(manifest, dict) or manifest.get('reviewed') is not True:
        raise ValueError('Explicit reviewed manifest required')
    rows = manifest.get('artifacts')
    if not isinstance(rows, list) or not 0 < len(rows) <= 1000:
        raise ValueError('Select 1..1000 artifacts')
    index = _mapping(root)
    prepared, seen, total = [], {}, 0
    for selection in rows:
        relative = _safe_selected_path(selection['path'])
        digest, size = selection['sha256'], selection['bytes']
        provenance = selection.get('provenance', manifest.get('provenance'))
        if not isinstance(provenance, str) or not provenance.strip() or len(provenance) > 4096:
            raise ValueError('Bounded provenance description required')
        if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest) or type(size) is not int or size < 0:
            raise ValueError('Exact digest and byte length required')
        key = (relative, digest)
        signature = (size, provenance)
        if key in seen:
            if seen[key] != signature:
                raise ValueError('Conflicting duplicate artifact selection')
            continue
        seen[key] = signature
        source = _safe_local(root, relative)
        if not source.is_file() or source.stat().st_size != size:
            raise ValueError('Selected artifact missing or size differs')
        if size > TEXT_LIMIT:
            prepared.append(({'path': relative, 'sha256': digest, 'status': 'unsupported_size'}, None, None)); continue
        total += size
        if total > BATCH_LIMIT:
            raise ValueError('Selected batch exceeds 64MiB')
        with source.open('rb') as stream:
            raw = stream.read(TEXT_LIMIT + 1)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Selected artifact hash differs')
        if re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----', raw):
            raise ValueError('Private key material is excluded')
        try:
            raw.decode('utf-8', errors='strict')
            if b'\x00' in raw:
                raise UnicodeError('Binary NUL')
        except UnicodeError:
            prepared.append(({'path': relative, 'sha256': digest, 'status': 'unsupported_non_utf8_text'}, None, None)); continue
        row = {'original_path': relative, 'sha256': digest, 'bytes': size,
               'blob_path': f'research/artifacts/{digest}.txt', 'provenance': provenance}
        existing = index.get(key)
        if existing and any(existing[k] != row[k] for k in ('bytes', 'blob_path')):
            raise ValueError('Conflicting retained mapping')
        target = _safe_local(root, row['blob_path'])
        if target.exists() and (not target.is_file() or target.read_bytes() != raw):
            raise ValueError('Existing retained copy differs')
        prepared.append(({'path': relative, 'sha256': digest, 'status': 'retained_verified', 'blob_path': row['blob_path']}, raw, existing or row))
    # Bound index growth before any writes; exact retries append no mappings.
    additions = [row for _, raw, row in prepared if raw is not None and (row['original_path'], row['sha256']) not in index]
    index_path = _safe_local(root, INDEX_REL)
    if (index_path.stat().st_size if index_path.exists() else 0) + sum(len((json.dumps(r, sort_keys=True, ensure_ascii=False)+'\n').encode()) for r in additions) > TEXT_LIMIT:
        raise ValueError('Artifact mapping exceeds size limit')
    added = 0
    for result, raw, row in prepared:
        if raw is None:
            continue
        target = _safe_local(root, row['blob_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name); stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if _safe_local(root, row['blob_path']).read_bytes() != raw:
                    raise ValueError('Existing retained copy differs')
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        key = (row['original_path'], row['sha256'])
        if key not in index:
            _append_mapping(index_path, row); index[key] = row; added += 1
    return {'artifacts': [r for r, _, _ in prepared], 'mappings_added': added,
            'retained_verified': sum(r['status'] == 'retained_verified' for r, _, _ in prepared),
            'historical_events_modified': False, 'source_execution': False}

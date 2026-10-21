"""Portable immutable state snapshots. No cloud calls occur without explicit push/pull.

Every SQLite file is copied with SQLite's online backup API (including committed
WAL pages). Separate databases are consistent individually, not atomically as a
set: pause application writers for a causally consistent multi-database snapshot.
"""
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import time
from contextlib import closing, contextmanager
from pathlib import Path, PurePosixPath

SCHEMA = 1
CHUNK_BYTES = 4 * 1024 * 1024
MAX_MANIFEST = 16 * 1024 * 1024
MAX_FILES = 50000
MAX_TOTAL = 8 * 1024 ** 3
EXCLUDED = {'.git', '.aws', '.ssh', '.venv', 'venv', '__pycache__',
            'caches', 'http-cache', 'http_cache', 'vendor', 'node_modules',
            'weights', 'models', 'raw', 'responses', 'runs', 'evidence', 'archives'}
EXTENSIONS = {'.sqlite', '.sqlite3', '.db', '.json', '.jsonl', '.ndjson', '.csv',
              '.md', '.txt', '.yaml', '.yml'}
HEX = re.compile(r'^[a-f0-9]{64}$')


class StorageError(ValueError):
    pass


class ConflictError(StorageError):
    pass


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise StorageError('Invalid relative path')
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {'', '.', '..'} for x in value.split('/')):
        raise StorageError('Unsafe relative path: ' + value)
    return value


def _namespace(value):
    if value != 'research' and not re.fullmatch(r'experiments/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value):
        raise StorageError('Namespace must be research or experiments/<id>')
    return value


def _digest(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise StorageError('Invalid SHA256 digest')
    return value


def _manifest_key(namespace, identity):
    return f'{_namespace(namespace)}/manifests/{_digest(identity)}.json'


def _object_key(identity):
    return f'objects/sha256/{_digest(identity)[:2]}/{identity}.gz'


@contextmanager
def _lock(path):
    import fcntl
    with open(path, 'a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


class LocalTransport:
    """Single-machine filesystem transport; immutable writes and flock-protected CAS."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise StorageError('Transport root cannot be a symlink')
        self.root = self.root.resolve()

    def _file(self, key):
        path = self.root / _path(key)
        for item in (path, *path.parents):
            if item == self.root.parent:
                break
            if item.is_symlink():
                raise StorageError('Symlink in transport path')
        return path

    def get(self, key, limit=MAX_MANIFEST):
        path = self._file(key)
        try:
            with path.open('rb') as f:
                value = f.read(limit + 1)
        except FileNotFoundError:
            return None
        if len(value) > limit:
            raise StorageError('Object exceeds size limit')
        return value

    def put_immutable(self, key, data):
        path = self._file(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.link(tmp, path)
                return True
            except FileExistsError:
                if self.get(key, len(data)) != data:
                    raise ConflictError('Immutable object differs: ' + key)
                return False
        finally:
            os.unlink(tmp)

    def head(self, namespace):
        raw = self.get(_namespace(namespace) + '/HEAD')
        return _digest(raw.decode().strip()) if raw else None

    def compare_and_swap(self, namespace, expected, identity):
        _digest(identity)
        if expected is not None:
            _digest(expected)
        path = self._file(_namespace(namespace) + '/HEAD')
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock(self._file(namespace + '/HEAD.lock')):
            if self.head(namespace) != expected:
                raise ConflictError('HEAD changed; pull/reconcile before publishing')
            fd, tmp = tempfile.mkstemp(dir=path.parent)
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write((identity + '\n').encode())
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)


class S3Transport:
    """Optional boto3 adapter. Conditional writes are mandatory; never fall back.

    Credentials come from AWS's standard chain. Do not pass credentials in configs.
    """
    def __init__(self, bucket, prefix='autoresearch', profile=None, region=None, client=None):
        self.bucket, self.prefix = bucket, _path(prefix.strip('/'))
        if client is None:
            try:
                import boto3
            except ImportError as exc:
                raise StorageError('Install optional boto3 for S3 transport') from exc
            client = boto3.Session(profile_name=profile, region_name=region).client('s3')
        self.client = client
        members = client.meta.service_model.operation_model('PutObject').input_shape.members
        if not {'IfMatch', 'IfNoneMatch'} <= set(members):
            raise StorageError('AWS SDK lacks conditional PutObject; upgrade boto3. No unsafe fallback.')

    def _key(self, key):
        return self.prefix + '/' + _path(key)

    def _read(self, key, limit):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
        except Exception as exc:
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
            if code in {'NoSuchKey', '404', 'NotFound'}:
                return None, None
            raise
        body = response['Body']
        try:
            value = body.read(limit + 1)
        finally:
            body.close()
        if len(value) > limit:
            raise StorageError('Object exceeds size limit')
        return value, response['ETag']

    def get(self, key, limit=MAX_MANIFEST):
        return self._read(key, limit)[0]

    def _put(self, key, data, **condition):
        try:
            self.client.put_object(Bucket=self.bucket, Key=self._key(key), Body=data,
                                   ServerSideEncryption='AES256', Metadata={'sha256': _sha(data)}, **condition)
        except Exception as exc:
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
            if code in {'PreconditionFailed', 'ConditionalRequestConflict', '412', '409'}:
                raise ConflictError('Concurrent/duplicate conditional S3 write') from exc
            raise

    def put_immutable(self, key, data):
        # A read avoids PUT charges for unchanged chunks; IfNoneMatch resolves races.
        try:
            metadata = self.client.head_object(Bucket=self.bucket, Key=self._key(key))
        except Exception as exc:
            code = getattr(exc, 'response', {}).get('Error', {}).get('Code')
            if code not in {'NoSuchKey', '404', 'NotFound'}:
                raise
            metadata = None
        if metadata is not None:
            if metadata.get('Metadata', {}).get('sha256') == _sha(data) and metadata['ContentLength'] == len(data):
                return False
            if self.get(key, len(data)) != data:
                raise ConflictError('Immutable S3 object differs')
            return False
        try:
            self._put(key, data, IfNoneMatch='*')
        except ConflictError:
            if self.get(key, len(data)) != data:
                raise
            return False
        return True

    def head(self, namespace):
        raw = self.get(_namespace(namespace) + '/HEAD')
        return _digest(raw.decode().strip()) if raw else None

    def compare_and_swap(self, namespace, expected, identity):
        key = _namespace(namespace) + '/HEAD'
        _digest(identity)
        raw, etag = self._read(key, 1024)
        actual = _digest(raw.decode().strip()) if raw else None
        if actual != expected:
            raise ConflictError('HEAD changed; pull/reconcile before publishing')
        condition = {'IfMatch': etag} if etag else {'IfNoneMatch': '*'}
        self._put(key, (identity + '\n').encode(), **condition)


def _allowed(path, explicit=False):
    parts = [x.lower() for x in path.parts]
    if 'cache' in parts and path.name not in {'index.sqlite', 'index.sqlite3', 'index.db'}:
        return False
    excluded = EXCLUDED - {'runs', 'evidence'}
    if explicit:
        excluded = excluded - {'raw'}
    elif parts and parts[0] in {'runs', 'evidence'}:
        return False
    if any(x in excluded or x.startswith('.') or any(t in x for t in ('credential', 'secret', 'token', 'private_key')) for x in parts):
        return False
    extensions = EXTENSIONS | {'.pdf', '.html', '.log', '.parquet', '.gz'} if explicit else EXTENSIONS
    extension_ok = path.suffix.lower() in extensions or (explicit and bool(HEX.fullmatch(path.name)))
    return extension_ok and not path.name.lower().startswith('id_')


def _sqlite_backup(source, destination):
    deadline = time.monotonic() + 60
    def progress(status, remaining, total):
        if time.monotonic() > deadline:
            raise StorageError('SQLite backup exceeded 60 seconds; retry when writes settle')
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(str(destination))) as dst:
            src.backup(dst, pages=1024, progress=progress)
            dst.execute('PRAGMA journal_mode=DELETE')
            if dst.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise StorageError('SQLite integrity check failed')
            tables = [r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return tables


def snapshot(state_dir, archive_dir, namespace='research', include=None, parent=None,
             max_total_bytes=MAX_TOTAL, max_file_bytes=2 * 1024 ** 3):
    """Create a local immutable snapshot; never upload or publish HEAD implicitly.

    include is an optional list of relative file paths, not globs. Secret/path and
    extension exclusions still apply. Experiment artifacts require a separate
    experiments/<id> namespace and a dedicated directory (not a repo checkout).
    """
    namespace = _namespace(namespace)
    if parent is not None:
        _digest(parent)
    root = Path(state_dir).absolute()
    if not root.is_dir() or root.is_symlink():
        raise StorageError('State directory must be a real directory')
    root = root.resolve()
    archive = LocalTransport(archive_dir)
    if archive.root == root or root in archive.root.parents or archive.root in root.parents:
        raise StorageError('State and archive directories must be disjoint')
    if include is not None:
        selected = [root / _path(p) for p in include]
    else:
        selected = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs
                if d.lower() not in (EXCLUDED if Path(directory) == root else EXCLUDED - {'runs', 'evidence'})
                and not d.startswith('.') and not (Path(directory) / d).is_symlink())
            selected.extend(Path(directory) / name for name in sorted(files))
    records, skipped, total = [], [], 0
    with tempfile.TemporaryDirectory(prefix='ideation-snapshot-') as tmp:
        for path in selected:
            rel = path.relative_to(root)
            if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
                skipped.append(str(rel))
                continue
            if not path.is_file():
                if include is not None:
                    raise StorageError('Requested file is missing or not a regular file: ' + str(rel))
                continue
            if not _allowed(rel, explicit=include is not None):
                skipped.append(str(rel))
                continue
            size = path.stat().st_size
            if size > max_file_bytes or total + size > max_total_bytes or len(records) >= MAX_FILES:
                raise StorageError('Snapshot size/file-count limit exceeded')
            tables = None
            with path.open('rb') as f:
                is_db = f.read(16) == b'SQLite format 3\x00'
            source = path
            before = path.stat()
            if is_db:
                source = Path(tmp) / 'backup.sqlite'
                source.unlink(missing_ok=True)
                tables = _sqlite_backup(path, source)
            chunks, hasher, length = [], hashlib.sha256(), 0
            with source.open('rb') as f:
                while True:
                    data = f.read(CHUNK_BYTES)
                    if not data:
                        break
                    length += len(data)
                    if length > max_file_bytes or total + length > max_total_bytes:
                        raise StorageError('Snapshot size limit exceeded during read')
                    identity = _sha(data)
                    compressed = bytearray(gzip.compress(data, mtime=0))
                    compressed[9] = 255  # Portable gzip OS header across Python versions.
                    archive.put_immutable(_object_key(identity), bytes(compressed))
                    hasher.update(data)
                    chunks.append({'sha256': identity, 'bytes': len(data)})
            after = path.stat()
            if not is_db and (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise StorageError('File changed during snapshot: ' + str(rel))
            total += length
            row = {'path': rel.as_posix(), 'bytes': length, 'sha256': hasher.hexdigest(), 'chunks': chunks}
            if tables is not None:
                row['sqlite_tables'] = tables
            records.append(row)
    if not records:
        raise StorageError('No eligible state files; inspect selected directory and exclusions')
    manifest = {'schema': SCHEMA, 'namespace': namespace, 'parent': parent,
                'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                'selection': 'explicit' if include is not None else 'default',
                'chunk_bytes': CHUNK_BYTES, 'files': records, 'total_bytes': total,
                'skipped': sorted(set(skipped)),
                'consistency': 'SQLite online backup per database; pause writers for cross-file atomicity'}
    raw = _json(manifest)
    if len(raw) > MAX_MANIFEST:
        raise StorageError('Manifest exceeds limit')
    identity = _sha(raw)
    archive.put_immutable(_manifest_key(namespace, identity), raw)
    return dict(manifest, id=identity)


def _manifest(transport, identity, namespace):
    raw = transport.get(_manifest_key(namespace, identity))
    if raw is None or _sha(raw) != identity:
        raise StorageError('Missing/corrupt manifest')
    try:
        value = json.loads(raw)
        if value['schema'] != SCHEMA or value['namespace'] != namespace or value['chunk_bytes'] != CHUNK_BYTES:
            raise StorageError('Unsupported manifest schema/namespace/chunk size')
        files = value['files']
        if not isinstance(files, list) or not 0 < len(files) <= MAX_FILES:
            raise StorageError('Invalid file list')
        seen, total = set(), 0
        for row in files:
            path = _path(row['path'])
            if path in seen or not _allowed(PurePosixPath(path), explicit=value.get('selection') == 'explicit'):
                raise StorageError('Duplicate/excluded manifest path')
            seen.add(path)
            _digest(row['sha256'])
            if type(row['bytes']) is not int or not 0 <= row['bytes'] <= MAX_TOTAL:
                raise StorageError('Invalid file size')
            length = 0
            for chunk in row['chunks']:
                _digest(chunk['sha256'])
                if type(chunk['bytes']) is not int or not 0 < chunk['bytes'] <= CHUNK_BYTES:
                    raise StorageError('Invalid chunk size')
                length += chunk['bytes']
            if length != row['bytes']:
                raise StorageError('Incomplete chunk list')
            total += length
        if total != value['total_bytes'] or total > MAX_TOTAL:
            raise StorageError('Invalid total size')
        if value.get('parent') is not None:
            _digest(value['parent'])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise StorageError('Invalid manifest') from exc
    return dict(value, id=identity), raw


def _chunk(transport, row):
    import io
    raw = transport.get(_object_key(row['sha256']), CHUNK_BYTES + 65536)
    if raw is None:
        raise StorageError('Incomplete snapshot: missing chunk')
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            data = f.read(row['bytes'] + 1)
    except (OSError, EOFError) as exc:
        raise StorageError('Corrupt gzip chunk') from exc
    if len(data) != row['bytes'] or _sha(data) != row['sha256']:
        raise StorageError('Chunk checksum/size mismatch')
    return raw, data


def push(archive_dir, transport, manifest_id, namespace='research', expected_head=None):
    """Publish only after all objects exist. A stale writer cannot replace HEAD."""
    local = LocalTransport(archive_dir)
    value, raw = _manifest(local, manifest_id, namespace)
    if value.get('parent') != expected_head:
        raise ConflictError('Snapshot parent must equal expected HEAD')
    remote_head = transport.head(namespace)
    if remote_head == manifest_id:
        # Publication can succeed immediately before a client crashes saving its
        # local lineage. Recover only OUR exact immutable manifest, never adopt
        # an arbitrary remote head or rewrite the expected parent to bypass CAS.
        # Verify both copies: a dangling HEAD or damaged local archive is not a
        # successful recovery. This rare retry may download existing S3 chunks.
        _manifest(transport, manifest_id, namespace)
        for source in (local, transport):
            for row in value['files']:
                hasher = hashlib.sha256()
                for chunk in row['chunks']:
                    _, data = _chunk(source, chunk)
                    hasher.update(data)
                if hasher.hexdigest() != row['sha256']:
                    raise StorageError('File checksum mismatch during publication recovery')
        return {'id': manifest_id, 'namespace': namespace, 'objects_written': 0,
                'already_published': True}
    if remote_head != expected_head:
        raise ConflictError('HEAD changed; pull/reconcile before publishing')
    written = 0
    for row in value['files']:
        hasher = hashlib.sha256()
        for chunk in row['chunks']:
            compressed, data = _chunk(local, chunk)
            hasher.update(data)
            written += bool(transport.put_immutable(_object_key(chunk['sha256']), compressed))
        if hasher.hexdigest() != row['sha256']:
            raise StorageError('File checksum mismatch')
    transport.put_immutable(_manifest_key(namespace, manifest_id), raw)
    transport.compare_and_swap(namespace, expected_head, manifest_id)
    return {'id': manifest_id, 'namespace': namespace, 'objects_written': written}


def pull(transport, archive_dir, namespace='research', manifest_id=None):
    identity = manifest_id or transport.head(namespace)
    if identity is None:
        raise StorageError('No published snapshot')
    value, raw = _manifest(transport, identity, namespace)
    local = LocalTransport(archive_dir)
    for row in value['files']:
        hasher = hashlib.sha256()
        for chunk in row['chunks']:
            key = _object_key(chunk['sha256'])
            compressed, data = _chunk(local if local.get(key, CHUNK_BYTES + 65536) is not None else transport, chunk)
            hasher.update(data)
            local.put_immutable(key, compressed)
        if hasher.hexdigest() != row['sha256']:
            raise StorageError('File checksum mismatch')
    local.put_immutable(_manifest_key(namespace, identity), raw)
    return value


def restore(archive_dir, destination, manifest_id, namespace='research'):
    """Validate in staging then atomically rename; never merge into active state."""
    local = LocalTransport(archive_dir)
    value, _ = _manifest(local, manifest_id, namespace)
    dest = Path(destination).absolute()
    if dest.is_symlink():
        raise StorageError('Symlink in destination path')
    dest = dest.parent.resolve() / dest.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    with _lock(dest.parent / ('.restore-' + _sha(str(dest).encode())[:16] + '.lock')):
        if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
            raise StorageError('Refusing dirty destination; restore to a new directory')
        stage = Path(tempfile.mkdtemp(prefix='.restore-stage-', dir=dest.parent))
        try:
            for row in value['files']:
                target = stage / row['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                hasher = hashlib.sha256()
                with target.open('xb') as f:
                    for chunk in row['chunks']:
                        _, data = _chunk(local, chunk)
                        hasher.update(data)
                        f.write(data)
                if hasher.hexdigest() != row['sha256']:
                    raise StorageError('File checksum mismatch')
                if 'sqlite_tables' in row:
                    with closing(sqlite3.connect(target.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                            raise StorageError('Restored SQLite integrity check failed')
                        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                        if tables != row['sqlite_tables']:
                            raise StorageError('Restored SQLite schema differs')
            os.rename(stage, dest)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return value


def bucket_plan(bucket='autoresearch-641134885443-us-east-1', region='us-east-1', prefix='autoresearch'):
    """Return reviewable AWS API arguments ONLY. Never executes provisioning.

    The application needs the returned least-privilege policy attached separately.
    No current object expires automatically: manifests can reference old chunks.
    """
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket):
        raise StorageError('Invalid bucket name')
    prefix = _path(prefix.strip('/'))
    arn = 'arn:aws:s3:::' + bucket
    create = {'Bucket': bucket, 'ObjectOwnership': 'BucketOwnerEnforced'}
    if region != 'us-east-1':
        create['CreateBucketConfiguration'] = {'LocationConstraint': region}
    operations = [
        {'operation': 'create_bucket', 'arguments': create},
        {'operation': 'put_public_access_block', 'arguments': {'Bucket': bucket, 'PublicAccessBlockConfiguration': {
            'BlockPublicAcls': True, 'IgnorePublicAcls': True, 'BlockPublicPolicy': True, 'RestrictPublicBuckets': True}}},
        {'operation': 'put_bucket_encryption', 'arguments': {'Bucket': bucket, 'ServerSideEncryptionConfiguration': {
            'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}}},
        {'operation': 'put_bucket_versioning', 'arguments': {'Bucket': bucket, 'VersioningConfiguration': {'Status': 'Enabled'}}},
        {'operation': 'put_bucket_policy', 'arguments': {'Bucket': bucket, 'Policy': json.dumps({
            'Version': '2012-10-17', 'Statement': [{'Sid': 'DenyInsecureTransport', 'Effect': 'Deny',
                'Principal': '*', 'Action': 's3:*', 'Resource': [arn, arn + '/*'],
                'Condition': {'Bool': {'aws:SecureTransport': 'false'}}}]})}},
        {'operation': 'put_bucket_lifecycle_configuration', 'arguments': {'Bucket': bucket, 'LifecycleConfiguration': {
            'Rules': [
                {'ID': 'ResearchHeadHistory', 'Status': 'Enabled', 'Filter': {'Prefix': prefix + '/research/HEAD'},
                 'NoncurrentVersionExpiration': {'NoncurrentDays': 30, 'NewerNoncurrentVersions': 3}},
                {'ID': 'RegistryHeadHistory', 'Status': 'Enabled', 'Filter': {'Prefix': prefix + '/experiments/registry/HEAD'},
                 'NoncurrentVersionExpiration': {'NoncurrentDays': 30, 'NewerNoncurrentVersions': 3}},
                {'ID': 'AbortIncompleteUploads', 'Status': 'Enabled', 'Filter': {'Prefix': prefix + '/'},
                 'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 1}}]}}},
    ]
    policy = {'Version': '2012-10-17', 'Statement': [
        {'Effect': 'Allow', 'Action': ['s3:ListBucket'], 'Resource': arn,
         'Condition': {'StringLike': {'s3:prefix': [prefix + '/', prefix + '/*']}}},
        {'Effect': 'Allow', 'Action': ['s3:GetBucketLocation'], 'Resource': arn},
        {'Effect': 'Allow', 'Action': ['s3:GetObject', 's3:PutObject'], 'Resource': arn + '/' + prefix + '/*'},
    ]}
    return {'mode': 'plan-only', 'region': region, 'bucket': bucket, 'prefix': prefix,
            'approval_required': True, 'operations': operations, 'application_iam_policy': policy,
            'retention': 'All manifest/chunk versions retained. Research and registry HEAD: three latest noncurrent versions protected; older versions eligible after 30 days. Per-experiment HEAD histories retained. No automatic current-object GC.'}


def estimate_cost(current_compressed_gb=5.0, unique_changed_gb_per_snapshot=0.05,
                  retained_snapshots=30, puts_per_month=10000, gets_per_month=100000):
    """Pure planning estimate in USD, S3 Standard us-east-1 first storage tier.

    No AWS call, billing lookup, free-tier assumption or spending enforcement.
    All retained bytes priced for a full month (conservative for new uploads).
    Retained snapshots is a planning scenario, NOT an implemented deletion rule.
    """
    import math
    for name, number in [('current_compressed_gb', current_compressed_gb),
                         ('unique_changed_gb_per_snapshot', unique_changed_gb_per_snapshot),
                         ('puts_per_month', puts_per_month), ('gets_per_month', gets_per_month)]:
        if not isinstance(number, (float, int)) or not math.isfinite(number) or number < 0:
            raise StorageError('Cost input must be a finite nonnegative number: ' + name)
    if type(retained_snapshots) is not int or retained_snapshots < 1:
        raise StorageError('retained_snapshots must be a positive integer')
    retained = current_compressed_gb + unique_changed_gb_per_snapshot * (retained_snapshots - 1)
    storage = retained * 0.023
    puts, gets = puts_per_month / 1000 * 0.005, gets_per_month / 1000 * 0.0004
    return {
        'region': 'us-east-1', 'storage_class': 'S3 Standard', 'currency': 'USD',
        'pricing_reference': 'https://aws.amazon.com/s3/pricing/',
        'rates': {'gb_month': 0.023, 'per_1000_puts': 0.005, 'per_1000_gets_or_heads': 0.0004},
        'assumptions': {'current_compressed_gb': current_compressed_gb,
                        'unique_changed_gb_per_snapshot': unique_changed_gb_per_snapshot,
                        'retained_snapshots': retained_snapshots,
                        'puts_per_month': puts_per_month, 'gets_or_heads_per_month': gets_per_month,
                        'all_retained_bytes_charged_for_full_month': True},
        'estimated_retained_compressed_gb': round(retained, 6),
        'storage_usd_month': round(storage, 6), 'put_usd_month': round(puts, 6),
        'get_head_usd_month': round(gets, 6), 'subtotal_usd_month': round(storage + puts + gets, 6),
        'excluded': ['internet/cross-region egress', 'taxes', 'account free-tier credits',
                     'HEAD version storage', 'extra scientific artifacts', 'KMS (plan uses SSE-S3)'],
        'warning': 'Estimate, not a bill or hard spend cap. Immutable history has no automatic GC; retained data keeps growing. Rates must be rechecked before provisioning.',
    }

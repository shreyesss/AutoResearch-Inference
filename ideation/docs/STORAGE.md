# Durable research state and experiment state

The storage layer is `ideation/storage.py`. Local use needs Python's standard library only. S3 is an optional transport using `boto3`; it requires an SDK whose `PutObject` supports **both `IfMatch` and `IfNoneMatch`**. Unsupported SDKs fail before writing. Credentials use the normal AWS credential chain and never belong in a config, manifest, or Git repository.

## What is preserved

Use independent state directories, outside the code checkout:

```text
~/.local/share/inference-autoresearch/
  research/
    corpus.sqlite              documents, revisions, graph, ingest checkpoints
    hypotheses.sqlite          if configured here: full hypothesis/event graph
    cache/index.sqlite         successful responses AND provider budget ledger
  experiments/
    experiments.sqlite3        append-only execution journal and artifact references
  archives/                    local immutable compressed snapshot object store
```

The CLI owns the actual path configuration; point `state_dir` at the directory containing the relevant databases. The storage layer does not assume a particular SQLite schema: **all tables, indexes, triggers and committed WAL data survive**, including rejection history, checkpoints and provider usage. It cannot preserve files that were never placed in the chosen state directory. This is particularly relevant when migrating an older installation whose hypothesis memory is stored somewhere else.

Research has one authoritative writer. Other nodes pull a pinned snapshot for inspection or hand off the writer role explicitly. Experiment journals live separately; use `experiments/registry` for the journal database and `experiments/<experiment-id>` for an explicitly selected artifact directory. Independent experiments have independent publication heads. This avoids turning the research corpus into a dumping ground for model weights, traces or repeated benchmark logs.

An experiment journal is append-only at the application layer. Snapshot publication does **not** merge journals or reconcile conflicting event streams from multiple writers. Do not let two machines independently mutate the same registry then expect uploading to merge them. Assign ownership per experiment or reconcile records before advancing the registry head.

## Snapshot format and guarantees

```text
archive or s3://<bucket>/autoresearch/
  objects/sha256/<first-two>/<sha256>.gz
  research/manifests/<manifest-sha256>.json
  research/HEAD
  experiments/registry/manifests/<manifest-sha256>.json
  experiments/registry/HEAD
  experiments/<id>/manifests/<manifest-sha256>.json
  experiments/<id>/HEAD
```

1. Each SQLite file is copied using `sqlite3.Connection.backup`, not by copying a live main file and forgetting its WAL. The backup is checkpointed into one ordinary SQLite file and integrity-checked.
2. Files are split into 4 MiB chunks. Chunks use deterministic gzip headers and SHA-256 identities of **uncompressed bytes**. Changed files can reuse unchanged chunks. SQLite vacuuming or page movement can invalidate many chunks; this is not guaranteed row-level incremental backup.
3. A content-addressed manifest records file hashes, chunk hashes/sizes, database table lists, timestamp, namespace, parent manifest and selection policy. Manifest and chunk writes are immutable.
4. All objects and the manifest must upload successfully before publication. `HEAD` advances using compare-and-swap against the caller's **previously known parent**, not whatever happens to be remote at upload time. A stale writer fails. An interrupted upload may leave harmless unreferenced chunks but cannot publish an incomplete snapshot.
5. Restoration validates manifest schema, relative paths, namespace, chunk size/hash, complete file hash and SQLite integrity. Files are staged and renamed into a new or empty destination only. Existing nonempty state is never overwritten or merged.

**Consistency boundary:** each database backup is transactionally consistent. Several databases and JSON files are not one shared transaction. For a causally consistent corpus + memory + budget cut, pause application writers while taking the snapshot. Do not claim a cross-database atomic cut merely because SQLite backup succeeded.

**Historical provenance:** old immutable manifests remain available after HEAD advances. Pulling the current snapshot does not download every previous snapshot; pass an explicit manifest ID to restore historical state. Hashes establish integrity, not scientific correctness or authorship. Bucket IAM controls who can publish.

## Bounded selection and exclusions

Default selection includes `.sqlite`, `.sqlite3`, `.db`, `.json`, `.jsonl`, `.ndjson`, `.csv`, `.md`, `.txt`, `.yaml`, `.yml`. It prunes raw duplicate downloads, top-level legacy runs/evidence archives, models/weights, vendor code, Git directories, virtual environments and common cache trees. Nested `records/<run>/dossier/evidence/` packets are retained. **`cache/index.sqlite` is retained** because it contains budget accounting and useful responses; cache lockfiles and loose cached payloads are omitted.

Symlinks, dotfiles, credential/secret/token/private-key filenames and files named like SSH identities are excluded. The default bounds are 50,000 files, 2 GiB per file and 8 GiB total uncompressed state; oversize snapshots fail visibly. This is a filename/extension policy, **not a secret detector for arbitrary file content**. Keep state directories free of credentials. The app's cache stores hashed request identities, not raw credential-bearing requests.

For selected primary-source material, use an explicit file list, e.g. `include=['corpus.sqlite', 'raw/paper.pdf']`. Explicit selection allows selected raw files and PDF/HTML/log/Parquet/gzip extensions and hash-named raw source files but still refuses sensitive names and symlinks. It does not implicitly include everything else: list all desired files. Do not use explicit raw inclusion for a complete duplicate download tree. Full corpus bodies and provenance retained in SQLite generally make that redundant.

No model files, `.env`, SSH keys or AWS credential files should ever be uploaded. Large experimental profiles should have their own reviewed selection and namespace.

## Python interface

```python
from ideation.storage import (
    LocalTransport, S3Transport, snapshot, push, pull, restore, bucket_plan,
)

# Works entirely offline. The directories must be disjoint.
manifest = snapshot('/state/research', '/state/archives', namespace='research')
remote = LocalTransport('/backups/autoresearch')
push('/state/archives', remote, manifest['id'], expected_head=None)

# A new node: download then restore to a NEW directory.
retrieved = pull(remote, '/fresh/archives', namespace='research')
restore('/fresh/archives', '/fresh/research', retrieved['id'])

# The next writer starts from the previously restored parent.
parent = retrieved['id']
next_manifest = snapshot('/fresh/research', '/fresh/archives', parent=parent)
push('/fresh/archives', remote, next_manifest['id'], expected_head=parent)

# Only after cloud approval: explicitly replace the transport.
# This constructor itself does not provision anything.
# remote = S3Transport('autoresearch-641134885443-us-east-1',
#                      prefix='autoresearch', profile='sofia-ssm', region='us-east-1')

# Separate registry namespace; never publish it under research/HEAD.
registry = snapshot('/state/experiments', '/state/archives',
                    namespace='experiments/registry')
```

`push` returns newly written chunk count. S3 checks existing object metadata with HEAD before deciding whether to PUT; unchanged chunks do not require payload re-upload or download. Conditional creation protects against races. On read, bytes are always verified. The local adapter uses immutable hardlink publication and a short `flock` around HEAD replacement; do not rely on it for distributed locking on arbitrary network filesystems.

## Recover a completed publication after a local receipt failure

A process can publish HEAD successfully, then crash before saving its local lineage. Retry **the exact previously attempted manifest** with the same previously known parent:

```bash
researchctl push --bucket YOUR_BUCKET --profile YOUR_PROFILE \
  --manifest-id EXACT_PREVIOUS_ATTEMPT_ID --expected-head PREVIOUSLY_KNOWN_PARENT
```

For an initial publication whose parent was absent, omit `--expected-head`. If remote HEAD is exactly the requested manifest, storage verifies that the local manifest still has the expected parent and validates local **and remote** manifest/payload integrity before returning `already_published: true`. The CLI can then save that exact successful identity as lineage. This recovery may download existing S3 chunks for validation, but does not rewrite HEAD or upload duplicates.

A different remote manifest still raises a conflict. Never fix a conflict by supplying an arbitrary current remote HEAD as the parent of stale local state. If another writer has advanced further, restore/reconcile explicitly.

## Proposed cloud setup: approval required

`bucket_plan()` produces a **plan-only** sequence of AWS API calls and a least-privilege application IAM policy. Printing it does not create a bucket, upload data, change permissions, or install a lifecycle policy:

```bash
PYTHONPATH=ideation python3 - <<'PY'
import json
from ideation.storage import bucket_plan
print(json.dumps(bucket_plan(), indent=2))
PY
```

Proposed defaults:

| Setting | Proposal |
|---|---|
| Bucket | `autoresearch-641134885443-us-east-1` (availability untested) |
| Region | `us-east-1` |
| Public access | All four S3 public access blocks enabled |
| Ownership | Bucket owner enforced; ACLs disabled |
| Encryption | SSE-S3 AES256, avoiding per-request KMS charges |
| Transport | Bucket policy denies non-TLS requests |
| Versioning | Enabled, including accidental HEAD overwrite recovery |
| Research/registry HEAD noncurrent versions | Preserve newest 3; older versions eligible after 30 days |
| Immutable object/manifests and per-experiment HEAD versions | Retained |
| Incomplete uploads | Abort after 1 day |
| Current immutable chunks/manifests | No expiration rule |
| Application IAM | List scoped prefix; GetObject/PutObject only; no DeleteObject |

A provisioner can execute the reviewed operation/argument list after approval. The application does not provision the bucket. `CreateBucket` permission alone does not establish permissions for encryption, public-access, versioning, IAM attachment or actual later upload; those remain operational checks.

There is deliberately **no automatic current-object garbage collection** yet. Expiring a chunk because it is old can break a newer manifest that still references it. Safe future retention needs reference tracing across retained manifests before deleting unreachable objects. Immutable objects normally have one version; the lifecycle expiration rule is scoped exclusively to research and registry HEAD prefixes. Individual experiment HEAD versions are retained. Head history is not a replacement for the immutable manifest history.

Cost follows **retained compressed unique chunks**, not current SQLite size. Cheap defaults are metadata/text first, no blanket PDF mirroring, no model files, one snapshot after a bounded run, and explicit upload. For example, 5 GiB compressed current state plus 50 MiB/day unique changed chunks retains about 6.5 GiB after a month if history is kept. High corpus churn or database vacuuming can be much larger. Request charges, internet restore egress, existing account free-tier usage and taxes are separate. Use the main infrastructure proposal's dated AWS prices; the storage library does not bake in tariffs or pretend a dollar budget caps an account bill.

## Cost worksheet

`estimate_cost(...)` is pure local arithmetic using the proposed us-east-1 S3 Standard inputs: $0.023/GB-month, $0.005/1,000 PUTs and $0.0004/1,000 GET/HEADs. [AWS pricing](https://aws.amazon.com/s3/pricing/) is the reference; recheck rates before provisioning.

Example: 5 GB compressed initial state, 50 MB unique changed chunks per snapshot, 30 retained snapshots, 10,000 PUTs and 100,000 GET/HEADs per month gives **6.45 GB retained, $0.14835 storage + $0.05 PUT + $0.04 GET/HEAD = $0.23835/month**. This prices all retained data for the entire month, not a prorated first-month bill. Internet/cross-region egress, taxes, extra artifacts and HEAD-version bytes are excluded, as are any account free-tier credits. The graph may keep growing beyond the 30-snapshot scenario because no GC is enabled. This is not a cost cap.

The concrete provisioning plan is [storage-bucket-plan.json](storage-bucket-plan.json). Neither printing the plan nor computing the estimate invokes AWS.

## Verification and remaining limits

Run:

```bash
PYTHONPATH=ideation python3 -m unittest discover -s ideation/tests -p test_storage.py -v
```

Tests cover committed WAL data, graph/checkpoint/event preservation, cache budget retention, chunk reuse, missing/corrupted payloads, malicious paths, duplicate records, unsupported schemas, dirty destinations, two racing local writers, conditional S3 write simulation, selected paper provenance, independent namespaces and plan-only bucket configuration.

No real S3 bucket was created and no data was uploaded during implementation. The S3 conditional-write test uses a fake client, not a live IAM/region integration test. Archive state is a single-writer distribution protocol, not a distributed database. S3 protects durable copies only after an explicit successful push; a local snapshot on a destroyed VM is still lost.

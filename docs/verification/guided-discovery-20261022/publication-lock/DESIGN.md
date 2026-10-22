# Publication lock audit — design only

No implementation, process interruption, canonical mutation, cloud call or device query was performed. The observation uses local immutable manifests, job/lineage receipts and current repository source. Parent has approved the direction for review, not execution.

## Observed boundary

At 2026-10-22T04:19:25 UTC, local lineage still named published `5069c38cb001bfc79baf25dd6f9c2cb82fa090fd149a98e2427b32f8ccdaff74`, finalized at03:51:13. Latest local snapshot was `f3e4ec86d7687d07d5498dec0555a03e79853da736edfafbee2369be9967e3a1`, created03:58:11 with5069 as parent. The backfill receipt PID96920 was last updated03:56:38 before its snapshot call. These timestamps establish a long outstanding publication, not an SDK timing decomposition. They do not prove which individual request is in flight.

Current `backfill.work` holds `_locked(root)` across refresh, status writes, local snapshot and `storage.push` (backfill.py130–211). `foundation.invoke` also takes this global writer lock before the entire command execution, including snapshot/push. Even research `status` and local searches enter it. Immutable object validation and all remote requests consequently serialize unrelated local work.

The live process began before some code revisions. Its last publication receipt has no new diagnostics. Request counts below describe the **current source plus observed manifest**, not a recovered trace of the live process's loaded Python code.

## Exact request-count model

`manifest-counts.json` and the two hash-verified manifest copies contain the inputs:

| Quantity | Published5069 | Pendingf3e4 |
|---|---:|---:|
| Files |1,981|2,285|
| Uncompressed bytes |2,779,039,228|2,883,204,087|
| Chunk references |2,587|2,906|
| Distinct chunks |2,129|2,309|

Pendingf3e4 shares1,691 distinct chunks with its parent and has618 not referenced by that parent. Parent difference does **not** prove those618 objects are absent remotely: older snapshots or a partial attempt can already contain them.

Current `_push` deduplicates transfer checks within a snapshot, saving597 repeated checks for f3e4. It still validates every ordered file locally and checks each distinct remote object anew. With matching metadata on existing objects, no races/retries, all618 delta objects absent, and a new manifest:

- **2,310 HEAD** calls:2,309 distinct chunks plus one manifest.
- **2 GET** calls: remote HEAD pointer at entry and at compare-and-swap.
- **620 PUT** calls:618 chunks, one manifest, one conditional HEAD update.
- Total **2,932 logical SDK calls**. Wire retries are separate.

If all chunks already exist, the normal path still makes2,310 HEAD+2 GET+2 PUT. Metadata mismatch/missing checksum metadata can add content GETs; immutable-write conflict can add reconciliation GETs. Exact-already-published recovery is different: it validates the remote manifest and each file's chunk occurrences, so it can perform2,906 chunk GETs plus the manifest and HEAD pointer GETs. These paths must not be conflated with ordinary publication.

Trusting chunks reachable from the verified parent would reduce the modeled common path to619 HEAD+3 GET+620 PUT:1,690 fewer logical calls (about57.6%). **Not recommended as the first fix:** it removes the current per-invocation check against remote object deletion/corruption. A published parent and local positive cache are not proof that its objects still exist today. Listing object names also does not reproduce checksum/size validation.

Bounded parallel transfers could preserve request count/integrity but shorten the serial dependency chain. No wall-time speedup is estimated. Existing ContextVar diagnostics would need per-worker counter aggregation; copying a mutable counter dictionary into threads is not enough. Treat this as a separate change after the lock protocol.

## Smallest safe lock split

Keep local consistency and every existing S3 validation. Add one per-namespace publication mutex and a small persistent in-flight receipt, not a new database or research orchestrator.

1. **Acquire publication mutex outside the writer lock.** Never wait for it while holding writer. Every operation that changes namespace lineage—automatic publication, explicit push and restore—must obey the same ordering. No path may hold writer then block on publication.
2. **Capture under writer.** Read current local published/restored parent and remote configuration, seal the local immutable snapshot using existing machinery, and persist in-flight `{namespace, snapshot_id, expected_parent, remote_config_digest, dirty_token}`. Then release writer. Source files can now change safely because the archive is sealed.
3. **Publish outside writer.** Keep publication mutex while using existing `push`: local full-file validation, all immutable checks/transfers, manifest publication, final conditional HEAD. Do not adopt a remote HEAD or rewrite the snapshot's parent. No state DB remains open for writing on behalf of publication.
4. **Finalize briefly under writer.** Validate the in-flight identity/configuration and expected local lineage, then record that exact snapshot as published. Clear pending only if its dirty/checkpoint token still equals the captured token; otherwise record the successful historical checkpoint while leaving newer work pending. Release writer and publication mutex.

### Dirty-token requirement

Every mutation that may need a checkpoint must advance a durable token under writer, including backfill batches and explicit deferred operations. Compare the captured token at finalization. Comparing `latest-snapshots.json` alone is insufficient: a deferred mutation does not create a new snapshot. Never let publication of S erase the pending flag for a later mutation T.

Commands that finish local writes during an upload can retain their normal local snapshot or explicit deferred receipt. Their remote publication can wait **outside** writer, coalesce into a later fresh checkpoint, or return a clear pending receipt. If a previously sealed checkpoint has a stale parent after another local publication, preserve it locally and capture fresh state for a new publication. Do not silently reparent its immutable manifest.

### Crash and competing-writer requirements

The in-flight receipt is needed because newer local snapshots can replace `latest-snapshots.json` while S uploads. After a remote CAS succeeds but before local lineage updates, restart must retry/reconcile **S itself**, using the existing exact-publication recovery branch. It must not forget S and publish a different child of the old parent. If remote HEAD is neither expected parent nor S, retain conflict and pending state; no automatic adoption.

Explicit restore must wait outside writer on the same publication mutex. Otherwise it could replace local state/lineage while an older snapshot is uploading. A remote configuration change must likewise serialize with publication or cause explicit finalization refusal using the captured configuration digest. Namespace publication may be separate, but updates to shared lineage JSON remain under writer.

### Backfill scheduling

Lock splitting alone frees research writers but a synchronous backfill loop would still pause its own download while awaiting upload. To allow both, the existing backfill process can own **one bounded publication task** (one thread/future or one existing CLI subprocess), never more than one active per namespace. The loop keeps fetching/committing under writer and marks dirty. Completed publisher results are merged under writer without overwriting newer job progress. No queue database is required; the dirty token causes the next checkpoint to include accumulated changes. On shutdown, distinguish locally retained, publication pending and published; do not claim remote completion prematurely.

Local SQLite backups, compression and manifest construction still occupy writer in this minimal design. The observed job-update→manifest-creation timestamp gap was about93seconds, not a clean measured snapshot duration. Moving compression outside writer would require a separate consistent staging design; it is not implied by this proposal.

## Required bounded tests before implementation promotion

Use LocalTransport/fake S3 and deterministic barriers, never cloud mutation for these tests:

1. Pause transport after snapshot sealing; another local research mutation completes while publisher remains paused.
2. New mutation advances dirty token; old snapshot finalization cannot clear pending. Later snapshot includes both mutations with proper published parent.
3. Two publishers and restore exercise lock ordering without deadlock; only correct sequential lineage can advance.
4. Crash before upload, during immutable upload, after remote CAS but before local finalize, and after local finalize. Retry uses exact in-flight identity; archive remains immutable.
5. Competing remote HEAD change refuses CAS; local lineage is not adopted or rolled back.
6. Already-published exact-ID recovery still validates local/remote payloads; missing/corrupt old chunk still fails.
7. Remote config changes cannot mislabel a publication to another target as current durability.
8. Background backfill status merge preserves newer page/cursor/job fields; only one publication task runs; shutdown exposes pending status.
9. Journal outcomes distinguish local mutation completion, snapshot capture and remote publication. A failed upload must not imply the local research mutation was lost.
10. Existing counts remain2,310 HEAD checks for the common f3e4-shaped fixture before any separately reviewed transfer optimization.

## Recommendation

Implement the lock split and bounded single publisher first, retaining current validation and CAS semantics. It removes network time from the global writer critical section without claiming fewer requests or faster S3. Measure the existing per-phase/request diagnostics on a fresh process afterward. Only then consider bounded parallel transfer or a separately specified weaker remote-validation mode.

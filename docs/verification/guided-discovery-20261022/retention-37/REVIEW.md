# Independent retention97/98/99 production V5 audit

**Verdict: no blocking discrepancy in the frozen isolated evidence.** Parent approval and guarded, serialized canonical execution remain separate. This review applies to operational manifest `a1414737a75dec7fc0d2502f88bef32971a55f988ccddf14b57965f974f9eae7` and the APPLY_PLAN bytes it covers. It does not apply or approve a publication.

## Restore and provenance

Independently verified all 59 operational manifest entries, the apply-plan source/export/artifact hashes, both expected dossier hashes, and all 31 mapped record inputs against their original bytes and bundle destinations. The source export contains no hypothesis ledger and independently opens with `immutable=1` with 82 documents, 87 revisions and 343 edges; its file hash remains unchanged. Thus this sealed export does not depend on its WAL sidecar.

Used the normal local `storage.restore` on the existing default-selection snapshot `75e076c097baa15245f717f91b7092b05abd5902f10bc168578500b39d7c5a51`, into a fresh reviewer-owned destination. Every one of 267 refs resolves with the expected hash: 213 direct state-relative files and 54 explicit retained-text copies. All bundle bytes also match the original selected files. Compared the complete restored/source document, decoded revision and edge tables; all match. Verified every restored revision fingerprint.

Both original round98 query documents retain the exact frozen provider receipt, original query ID, original searched_at timestamp and all 22 discovered_by hit edges. This is provenance recovery, not a new online search. Original source identities and historical revisions remain available for exact quotes. Binary exports/WAL/SHM are explicitly excluded from text retention; their source contents use the corpus import path.

## Typed identities and history

Checked the restored database directly, through read-only connections and `HypothesisMemory.__new__` read access, against both original isolated author dossiers and V5 final dossiers. Identity, run/local ID, full card, brief, baseline, fingerprint, policy, status, assessment, event IDs/types/actors/data, record contents and claim contents agree. Linked source quotes resolve to the exact restored revision bodies.

| Identity | Status | ROI | Source claim links | Records |
|---|---|---|---:|---:|
| SL97 `c9c3ae4e…e11a43` | deferred | null | 11 (9 unique claims; 2 later support links) | 4 |
| SN98 `68e3668d…4df697` | deferred | null | 13 | 3 |

Both preserve baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`. Both diagnostic plans remain execution-unauthorized and target-relative gain null. Neither mathematical/source controls nor restored evidence are promoted into native correctness or service results.

SL97 retains the original `eval_plan:0b9bb062…dd9993`, readiness **blocked**, with gap “No grounded supporting claim linked to hypothesis.” Its later `eval_plan:8e8b5009…ad56e` is **ready_for_review** after the two support links. The original deferred decision remains. The first record must not be recomputed using the later evidence context.

## Retry guard

Read the actual V5 `prefix_guard` and `completed` implementations, then extracted and executed only those two read-only definitions against the fresh restore. All 33 completed typed operations are recognized without invoking any typed mutation or evaluator. Prefix checking compares the immutable fields and the exact expected event prefix; completed records compare exact node contents, not merely existence or current readiness.

For a negative control, changed the expected historical blocked plan to `ready_for_review` only in reviewer memory. The completed-record guard rejected that mismatch. An earlier attempt to corrupt a node in a separate reviewer-owned database was itself rejected by the append-only database trigger; it did not alter the restored authoritative history. This supports exact-record skip behavior, not context-free idempotency of rerunning eval-plan.

The apply plan explicitly requires the guard and mutation sequence under the normal writer lock and stops on unexpected events/status. The preparation script exercised guards around isolated calls; it does not itself prove a future canonical runner holds a single lock across a multi-command replay. Parent execution must implement that stated serialization/guard contract, preserve the original command order for partial completion, and skip completed historical operations. No atomic multi-command rollback guarantee is claimed.

## Failures and operational limits

Read the retained V1 syntax failure, V2 binary UTF8 failure and V3 nested proposal-response validation failure. Their scripts/logs are included in the artifact mapping. V4's missing indexed query-document coverage and V5's remedy are documented. The original round97 uncommitted author corpus problem is explicitly recorded and recovered from the immutable export. The round98 init-only command mirror is not misrepresented as complete history; its full journal correction is separately covered by round101.

Reviewer audit development also had three recorded stops, retained here: an overstrict raw JSON-serialization comparison (decoded revision contents matched), a reviewer assumption that claim ID was inside the claim payload rather than the link, and the append-only trigger rejecting the deliberate negative edit. These were reviewer-check issues, not source or retention defects. The final audit passes after scoped corrections. No author artifact was edited.

Commands executed include `PYTHONPATH=ideation .venv/bin/python .../review/retention979899-agent/audit.py` from the repository, plus bounded stdlib reference/hash checks. Only reviewer-owned restores and negative controls were written. No canonical apply, cloud operation, new snapshot publication, native/model import, GPU work or scientific probe rerun occurred. This establishes local default-snapshot recovery, not S3 completeness or cross-machine script executability.

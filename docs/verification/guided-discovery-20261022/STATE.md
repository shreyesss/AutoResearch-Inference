# Current persistence summary

Checkpoint6: round15 canonical import and selected-artifact retention are queued; round16 retention is being prepared. Snapshot omission audit found185/304 references restored,119 missing. Reviewed selection can retain117 text references; PNG and hidden `.gitignore` remain excluded. No repaired canonical/S3/VM state is claimed yet. See [checkpoint6](CHECKPOINT_6.md).

| Cohort | Canonical memory | S3 publication | VM restore |
|---|---|---|---|
| Rounds1–4 | Imported; independent readback completed | Verified through manifest `3bf6db32a1a516433190ae8966cfb5ceda475539792b682b1128c40443f33489` | Not checked |
| Round5 RD01/RD02 | Imported; both deferred;43 artifact hashes independently verified | Database + selected files published in `e05b413…`; raw-artifact completeness under audit | Not checked |
| Round6/7 refinements | Appended to existing AT03/RD01;12 claims,2 CPU results;49 artifact hashes checked | Database + selected files published in `e05b413…`; raw-artifact completeness under audit | Not checked |
| Round8 literature | Imported;8 exact revisions/search entries and6 artifact hashes independently checked | Database + selected files published in `e05b413…`; raw-artifact completeness under audit | Not checked |
| Round9 Engram | Imported; both deferred;9 original paper-revision references and54 artifact hashes checked | Database + selected files published in `e05b413…`; raw-artifact completeness under audit | Not checked |
| Round10 exposure | Frozen report retained externally and copied to Git | Not claimed | Not checked |
| Round11 EG01 refinement | Appended to same EG01;6 claims,2 inconclusive CPU records;12 artifact hashes and deferred status independently checked | Database + selected files published in `e05b413…`; raw-artifact completeness under audit | Not checked |
| Round12 projection | Imported; PJ01 deferred;51 artifact hashes and24 paper revision references independently checked | Not claimed | Not checked |
| Round13 lossless cache | Imported; two rejected/one deferred;39 artifact hashes and17 paper revision references independently checked | Not claimed | Not checked |
| Round14 context rows | Imported; TR01 deferred;50 artifact hashes and6 paper revision references independently checked | Not claimed | Not checked |

The downloader remains live. Snapshot `e05b413d4ff55f30bbe532094151622e32733ad698f696aecfa3739a1b607acc` published successfully and contains the database state plus selected files for rounds5–9/11. Default archive selection excludes some raw source/replay artifacts; publication alone does not establish complete replay portability. The audit is recorded in checkpoint5. Rounds12–14 imported after that snapshot and passed [independent readback](canonical-round12-14-readback.json); publication for those later writes remains unclaimed. Query-domain corpus import/publication is running. No process was restarted, no remote lineage overwritten and no VM restoration checked.

The history below records earlier checkpoints; this table and paragraph supersede their pending notes.

# Checkpoint history

- All **11 frozen proposals**, **9 source-grounded claims**, screening/decisions and **2 review-ready CPU plans** imported into canonical memory successfully. A separate read-only query verified every hypothesis and its linked records.
- **5 executed CPU checks** have immutable lifecycle records with explicit narrow scopes and artifact hashes. The later tile-constraint check is retained in the source appendix; it is not a serving experiment. No broad hypothesis is experimentally validated.
- Canonical batch: `~/.local/share/inference-autoresearch/research/records/guided-discovery-20261022-001/`. Full local discovery workspace: `~/.local/share/autoresearch-reviews/guided-discovery-20261022-001/`.
- Checkpoint 1 S3 publication **completed**, receipt `publication-checkpoint1.json`: manifest `f52e89f26bb34ebb1021691d947d0d84eab3b5130bbc5a7dc11547e7a06e44d6`, 463 files, 428 newly written immutable objects. This proves publication of the checkpoint-1 snapshot, not subsequent round2/round3 writes or VM restoration. No VM readback was performed in this continuation.
- Next-round research under `round2-runtime/`, `moe/round2/` and `round3-attention/` is separate from the frozen eleven-intervention denominator. New refinements must be imported/appended before claiming canonical persistence.

## Subsequent imports

- **Round2 canonical import completed:**7 immutable proposal records representing6 directions,13 grounded claims and3 scoped CPU results. Independent read-only inspection verified every latest disposition; the original unfinished-prefill rejection remains in history with its superseding revision. See `round2/canonical-receipt.json` and `round2/canonical-independent-readback.json`.
- The round2 import marked a checkpoint pending. The earlier S3 receipts do **not** cover it. Its historical `--local-snapshot` flag name was misleading: the executed helper used deferred mode and created only the pending marker, as the receipt states.
- **Round3 canonical import completed:**3 hypothesis cards,6 grounded claims,7 narrowly scoped CPU records and71 archived artifacts. Independent read-only inspection verified all3 dispositions and every one of the26 returned hit references against documents, immutable revisions and the search index. This preserves22 unique searchable papers,26 original discovery edges and3 explicitly receipt-derived query records. See `round3/canonical-receipt.json` and `round3/canonical-independent-readback.json`. S3 publication of this later state remains pending.
- Round4 source20 geometry/donor-PR refinement was appended to the existing AT03 identity:5 new grounded claims,2 scoped CPU records,zero new hypotheses. The first queued attempt safely aborted before mutation because a reviewer added source evidence; retry against frozen inputs succeeded. Independent read-only status check still reports implementation deferred. Its S3 publication remains pending; see `round4/canonical-receipt.json`.

## Latest research, not yet published

- Round5 RD01/RD02 retention packet passed isolated validation and idempotent retry; canonical import is queued behind the writer lock. Do not infer completion from its invocation.
- Round6 AT03 and round7 RD01 are source/CPU refinements of existing identities. Reports and independent reviews are frozen externally; retention preparation is ongoing.
- Round8 evaluator literature has its own isolated corpus, original search receipt and full-text dossier; canonical import is not yet performed. Two citation expansions failed explicitly.
- A separate snapshot command for rounds2/3/4 is running. No new publication receipt or VM readback is claimed here.

## Verified subsequent publication

Snapshot `3bf6db32a1a516433190ae8966cfb5ceda475539792b682b1128c40443f33489` successfully published with parent `c50e6f24ef8df0c455961685cdc71e49eba436c0e063d49d8ec2ac70d0c57776`:558 files,475 newly written immutable chunks. Local manifest inspection confirms round2/3/4 readback manifests are included; see `publication-checkpoint234.json`. This supersedes the pending-publication notes above for those cohorts only. Round5 import is still queued, and no VM restoration was checked.

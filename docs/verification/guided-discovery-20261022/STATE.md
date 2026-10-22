# Persistence state after canonical readback

- All **11 frozen proposals**, **9 source-grounded claims**, screening/decisions and **2 review-ready CPU plans** imported into canonical memory successfully. A separate read-only query verified every hypothesis and its linked records.
- **5 executed CPU checks** have immutable lifecycle records with explicit narrow scopes and artifact hashes. The later tile-constraint check is retained in the source appendix; it is not a serving experiment. No broad hypothesis is experimentally validated.
- Canonical batch: `~/.local/share/inference-autoresearch/research/records/guided-discovery-20261022-001/`. Full local discovery workspace: `~/.local/share/autoresearch-reviews/guided-discovery-20261022-001/`.
- Checkpoint 1 S3 publication **completed**, receipt `publication-checkpoint1.json`: manifest `f52e89f26bb34ebb1021691d947d0d84eab3b5130bbc5a7dc11547e7a06e44d6`, 463 files, 428 newly written immutable objects. This proves publication of the checkpoint-1 snapshot, not subsequent round2/round3 writes or VM restoration. No VM readback was performed in this continuation.
- Next-round research under `round2-runtime/`, `moe/round2/` and `round3-attention/` is separate from the frozen eleven-intervention denominator. New refinements must be imported/appended before claiming canonical persistence.

## Subsequent imports

- **Round2 canonical import completed:**7 immutable proposal records representing6 directions,13 grounded claims and3 scoped CPU results. Independent read-only inspection verified every latest disposition; the original unfinished-prefill rejection remains in history with its superseding revision. See `round2/canonical-receipt.json` and `round2/canonical-independent-readback.json`.
- The round2 import marked a checkpoint pending. The earlier S3 receipts do **not** cover it. Its historical `--local-snapshot` flag name was misleading: the executed helper used deferred mode and created only the pending marker, as the receipt states.
- **Round3 canonical import completed:**3 hypothesis cards,6 grounded claims,7 narrowly scoped CPU records and71 archived artifacts. Independent read-only inspection verified all3 dispositions and every one of the26 returned hit references against documents, immutable revisions and the search index. This preserves22 unique searchable papers,26 original discovery edges and3 explicitly receipt-derived query records. See `round3/canonical-receipt.json` and `round3/canonical-independent-readback.json`. S3 publication of this later state remains pending.
- Round4 source20 geometry/donor-PR refinements remain external retained artifacts awaiting an append-only update to AT03; they must not become another hypothesis in the yield denominator.

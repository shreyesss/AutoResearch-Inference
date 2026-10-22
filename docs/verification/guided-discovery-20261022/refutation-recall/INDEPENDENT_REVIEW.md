# Independent compact refuting-evidence recall review

Verdict: no blocker. The optional fields accurately flag linked objections while leaving the existing selection disposition, original card/baseline and ranking unchanged. This repairs visibility of a scoped limitation such as M01 without silently converting its accepted CPU-investigation history into rejection or implementation approval.

## Semantics and bounds

The join scans real hypothesis_claims/evidence_claims rows, groups refutes by distinct claim ID and keeps source identity matching as before. Multiple rationales for one claim count once; four interpretations from one source count as four claim IDs but one source. The discovery skill explicitly warns that this is not independent corroboration. Supports/background links do not count as refutations. A claim may have both support and refuting links; the warning does not resolve that scope conflict automatically.

Up to three unique IDs are sorted lexically, not by severity, age, source independence or evidential strength; omitted_refuting_claims makes the truncation explicit. Zero count does not prove correctness, freshness or absence of unlinked evidence. Existing query matching still searches card/latest disposition/source identity rather than new claim rationale text; users must open the dossier. No aliasing, semantic recall or evidence-quality grading was introduced.

## Inventory and read behavior

New represented claim IDs/counts participate in the existing hash of the compact result set, so a newly linked refuting claim changes the inventory hash. It is not a full ledger or source-revision hash. A new rationale for the same linked claim can add an evidence event while leaving the compact projection/hash unchanged; the independent probe confirmed this. This is consistent with the view’s stated purpose and freshness disclaimer, but callers must not use inventory_hash as proof that full dossiers are unchanged.

The method issues only SELECTs and does not create schemas, mutate nodes, transition status or commit/rollback caller transactions. It scans linked evidence and latest dispositions with the existing non-snapshot multi-query design; pagination docs explicitly disclaim snapshot isolation. A caller requiring one consistent read must provide its own read transaction. The new fields do not strengthen those concurrency semantics.

## Actual checks

Independently ran the two compact-recall tests (2 passed) after the author corrected whole-record equality to preserve non-event fields and the old event prefix while allowing two intentional evidence_linked events. An additional retained temporary fixture checked four same-source claims, cap/omission/order, duplicate-rationale behavior, unchanged status, unchanged hash for same-claim new rationale, absence of rationale-only literal matching, and execution through a WAL-aware read-only SQLite connection inside an existing transaction with zero changes.

All frozen author packet hashes verified and current source pins retained. Root-reported full365+29 tests/bootstrap/skill validation are not claimed as independently rerun here. No canonical writes, GPU, network, source freshness test or retrieval-quality improvement experiment occurred.

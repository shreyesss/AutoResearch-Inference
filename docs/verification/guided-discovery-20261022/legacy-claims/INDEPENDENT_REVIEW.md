# Independent review — historical claim revision identity

**No blocker found in the narrow fix.** Reviewed the frozen diff and surrounding `ResearchFlow.claim`, `dossier`, `changes`, `Store.put`/decode and fingerprint contracts. The two working files match the author's frozen hashes. No production files were changed by this review.

## Correctness findings

- Explicit historical selection now retains the actual `(source_id, revision_hash)` table key. Recomputing a modern fingerprint after reading an older revision could name an identity never stored; removing that recomputation is necessary.
- Implicit latest selection now follows the current document's recorded key into the immutable revision table. A missing revision fails before the claim-memory transaction. It does not silently manufacture a revision or migrate source rows.
- Exact quotes and offsets come from the selected historical body/title, not the current document. A separately executed historical-only quotation control confirmed this distinction.
- Dossier alerts compare the current and pinned documents under the same present fingerprint function. Retrieval-only hash-formula differences therefore do not imply substantive changes, while body and non-retrieval metadata changes still do. The underlying historical identity, encoded row and existing claim are preserved.
- The fix has no new lock ordering, network action or source migration. It uses existing tool-level writer serialization. Direct API callers still have the existing responsibility to avoid unsupported concurrent writers.

## Executed verification

1. `.venv/bin/python -m pytest ideation/tests/test_research_flow.py -q`: **36 passed in 0.45s**. This includes explicit/implicit legacy selection, idempotent claim identity, unchanged historical rows, semantic dossier comparisons and missing-revision failure before memory writes.
2. Reviewer-owned `probe.py`, isolated temporary state only: five controls passed. A quotation unique to the historical body resolves; equivalent refreshed content clears the dossier alert; substantive metadata change raises it; an explicit revision remains usable without a current document row; unavailable revision leaves claim-memory change count unchanged and original historical bytes intact.

These are provenance/tool tests, not research-quality or inference-performance measurements. The broad research suite and bootstrap were not repeated by this reviewer.

## Deliberate limits

The patch does not rewrite already-created bad legacy claims, repair a missing revision, validate arbitrary corrupted imported rows, or make `changes()` a semantic diff. That cursor remains an observed-revision feed keyed by stored identities and can emit a review trigger for equivalent content under a new key; the dossier now supplies the content-aware comparison. Existing missing-pinned-row dossier fallback is unchanged. None of those is a blocker to the stated narrow repair or should be described as solved by it.

# Retention39 v5 independent delta review

Verdict: no blocker in current v5 source-locator correction or isolated receipt integrity. This extends the earlier v4 code review; no canonical application or authorization is performed here.

Read the actual v4→v5 code delta. Original packet bytes remain87cbf706…; pinned target blob URLs are changed from the upstream namespace to callgideon/vllm at the same c455 commit. Source bodies and quotes remain identical, corrected source revisions are recomputed, and claims refer to those corrected revisions. The locator addendum/map are retained as additional artifacts and searchable records. This does not rewrite an old revision's URL in place. Existing v4 completed state is rejected by the v5 importer hash check rather than silently relabelled.

Verified current v5 operational hashes,72 restored artifact references,26 exact original source revisions, all5 claim quotes and corrected content hashes. C025 exact card/baseline/latest review unchanged. Isolated before/after counts remain141 hypotheses,722 hypothesis events,61 tests. No new hypotheses or state transitions. Four supplied negative controls remain scoped to their actual boundaries. No tests were repeated unnecessarily; this review performed read-only receipt/revision/hash verification and actual code inspection.

## Operational-history limitation

The v5 development flow reused shared isolated-validation/readback/negative-control filenames. Consequently, the older v4 operational manifest no longer validates fully at its original paths. This was raised during review. The author recovered6 exact-hash v4 files into history-v4 (independently rechecked here) and explicitly lists4 unavailable earlier versions in history-v4/SUPERSEDED_RECEIPTS.json: isolated-validation.json, negative_controls.py, negative-controls.json and OPERATIONAL_CORRECTION.md. No fabricated reconstruction is accepted. Do not claim complete immutable v4 operational history. This does not invalidate current v5 checks or original frozen scientific packet, which remain verified.

Cross-store writes remain non-atomic, and the current artifact fallback proves retained bytes, not universal relocated operational-script execution. Run the reviewed importer with assertions enabled. No canonical writes, network calls, model or GPU activity occurred in this review.

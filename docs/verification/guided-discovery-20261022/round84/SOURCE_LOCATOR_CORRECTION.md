# Round84 source-locator correction

The frozen packet reused the exact target kernel bytes but assigned the wrong repository identity, `deepseek-ai/FlashMLA`. The previously retained source is `vllm-project/FlashMLA` at the same5dceadbd9eabc9acfc547ef18ec8f7b14b980682 pin. The source body is byte-identical. No fresh HTTP lookup or claim of a commit in the wrong repository was made.

Use corrected-source-export.json for future retention instead of the frozen source-export.json. It removes the wrongly constructed identity/revision and copies the existing correct document and immutable revisions from round83. Preserve the frozen packet as history and this explicit mapping; do not import the incorrect identity as a second evidence source. All126 PR identities and original provider revisions are preserved. No canonical state was changed.

The scientific conclusion remains zero-new. This corrects provenance, not source behavior or measured performance. The original42-file manifest still validates.

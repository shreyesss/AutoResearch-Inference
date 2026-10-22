# Independent review: host prompt-tail registration

HS30-01 remains deferred and low priority. The source-backed missing memo is a plausible narrow optimization, not a qualified gain. All 47 author artifacts hash/size-verified; isolated replay of the exact helper AST matches 26 cases (4 repeated, 22 no-op). Synthetic geometry is not deployment attestation.

## Material qualifications from deeper pool read

The repeated call does **not** repeatedly insert an alias or recompute a cryptographic prefix hash. Pinned BlockPool._get_partial_block_hash (565+) indexes precomputed request.block_hashes. _insert_block_hash (626+) returns immediately for a matching primary hash or an already present alias. Remaining repeated work is Python calls, boundary arithmetic, hash/group construction and membership checks. Quantitative ROI is unknown and may be negligible.

The donor helper b00d7cc0829c3b1ca2fd638a3f9bb61b9fc9f837 computes boundary from num_prompt_tokens unconditionally. The pinned target distinguishes EAGLE from other groups, subtracting one token in the latter. Copying the complete old helper would change semantics: for8192/block256/hash32, target non-EAGLE registers8160 whereas the old boundary8192 skips it. Only adapt the memo component while preserving current semantics, if lifecycle proof justifies it.

A narrower alternative within the same family is an early return from cache_partial_block after already_cached && !replace_existing_hashes. The existing following _insert_block_hash is then a no-op and event generation is already disabled for already_cached. This avoids some redundant membership/call overhead without a new persistent memo. It removes less work and is only a source-derived option pending CPU differential checks, not an implemented or measured optimization.

The original synthetic test repeats a recorder call; it does not model alias ownership, actual event consumers, preemption, promotion, resets or the proposed memo. The 1024 repeats must not be described as1024 expensive insertions. Actual cache geometry/EAGLE flags and exposed host critical-path cost remain the first gates. N01 addresses different null-table walking; this is not that existing hypothesis. Keep all no-op and semantic-mismatch cases in any eventual evaluation.

No GPU operations, model/backend imports, performance benchmark or service qualification occurred.

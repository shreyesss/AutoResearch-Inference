# Compact hypothesis recall exposes later objections

## Observed failure

The M01 diagnostic selection remained `accepted` after three scoped source objections were correctly appended. Full dossiers showed those objections, but compact recall only showed the earlier selection and rationale. A discovery agent could therefore reuse the old arithmetic premise without noticing contrary evidence.

## Change

Compact recall now returns the number of unique linked `refutes` claim IDs, at most three IDs, and the omitted count. Duplicate rationales for the same claim count once. Multiple claims from one paper are not independent corroboration. Inventory hashes include this projection so a newly linked objection invalidates an earlier compact inventory hash. Literal matching, ordering, baseline and historical decisions are unchanged.

The skill and MCP description direct agents to `hypothesis show` for scope and full rationales. Zero refuting claims does not establish correctness, fresh sources or absence of criticism. This compact projection does not run the dossier's newer-source-revision check. A scoped refutation does not automatically invalidate the whole hypothesis or rewrite its selection status.

## Verification actually run

- New meaningful integration test: create a proposal, append two rationales on one refuting claim, confirm a single unique objection and unchanged original hypothesis fields/selection, then add three claims and verify bounded IDs and omission count.
- The initial assertion compared the complete record including its intentional new evidence events and failed. It was corrected to preserve all original non-event fields and the old event prefix, and require exactly two appended `evidence_linked` events. No production validation was weakened.
- Focused research-flow suite: 33 passed.
- Full research suite: 365 passed and 29 subtests passed in 10.63 seconds.
- Bootstrap dry run passed without changes.
- Actual canonical readback used SQLite `mode=ro` within a single read transaction, without calling schema initialization. All 143 cards were paged; M01 shows its original accepted diagnostic status, unchanged baseline and three refuting claim IDs. Connection `total_changes` was zero. This read does not certify cloud publication.

The change improves evidence visibility. It does not measure discovery precision, reasoning quality, hypothesis yield or inference performance. No GPU/native serving work occurred.

Skill validation initially failed because both default Python and the repo venv lack PyYAML. Reusing the existing isolated validator dependency directory via `PYTHONPATH=/tmp/autoresearch-skill-validator-deps` passed. No runtime dependency was installed.

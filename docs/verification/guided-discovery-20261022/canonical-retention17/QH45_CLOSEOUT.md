# QH45 canonical retention completed

Authorized replay completed successfully through production researchctl after waiting for the existing writer. No publisher interruption, direct database merge, GPU execution, cloud publication or Git mutation was performed.

- QH45: `hypothesis:4d38f92df2b2ade451a5487906d4354f000aab08cd0afbddd8aec508015be82e`.
- Exact baseline: `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`.
- Latest decision: `decision:2961da619f52158f5612ef1defe2ef45d63ffee9404447eebbbc70be2b738de2`, **deferred**, independently reviewed. No service qualification or evaluation execution was added.
- All13 expected typed IDs plus two evidence-link operations completed. Source readback finds all33 documents and34 exact content revisions.
- Five already-retained OpenAlex revision JSONs preserve their earlier fetched_at instead of overwriting it with the later packet observation. All other fields, including body, match. `revision-metadata-differences.json` records the precise difference; this is immutable existing-revision preservation, not lost paper content.
- All101 original staged artifact hashes and101 retained portable references (91 unique text blobs) verify. Existing conflicting files were not overwritten.

`canonical-receipts/` contains each command/result, staging preflight/readback and final selection. `readback-canonical-v1.json` and `portable-blob-readback.json` are independent read-only checks. Operations, scoped negative controls and preserved isolated failures are described in OPERATIONS.md. The frozen v3 source package was not modified.

All commands used `--local-only --defer-snapshot`; checkpoint remains pending. This report does not claim that a new recovery snapshot or S3 publication covers QH45. Parent coordinates the next checkpoint. This retains an already generated direction; it is not an additional scientific idea count.

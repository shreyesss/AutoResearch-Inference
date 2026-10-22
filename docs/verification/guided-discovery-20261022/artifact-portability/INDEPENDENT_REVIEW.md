# Independent selected-artifact review

Scope: new `hypothesis_artifacts.py` retention/resolution and `foundation.py` CLI integration, plus the exact omitted artifacts in the existing audit. No canonical mutation, provider call, GPU call, source execution, or historical record edit occurred.

## Reviewed selection

`reviewed-selection.json` selects **117 references**, **100 distinct hashes**, **5,717,242 reference bytes / 4,776,433 deduplicated bytes**. Its SHA256 is `21ff3654777f018386b6ffaf2e428d4d545475fde2e47572ae24884ef916590d`.

Every one of the 119 originally omitted references was rechecked against current canonical file bytes, exact SHA256/size, the original import receipt, and the durable canonical cohort readback receipt. `selection-provenance.json` pins these receipts and the original audit. This verifies the intended evidence identity; it does not revalidate the experimental conclusions or attest that every line of upstream source is safe to execute.

Two omissions remain explicit in `selection-exclusions.json`:

- SplitZip `figs/main.png`: non-UTF-8 binary, unsupported by text retention.
- SplitZip `.gitignore`: benign source metadata, but the existing hidden-name guard rejects it. Root explicitly chose to preserve that guard instead of introducing an exception.

The earlier audit correctly counted 118 UTF-8 references; **UTF-8 alone is insufficient under the new selected-path policy**, so 117 is the eligible retained count. This selection covers the scoped audit only, not every future cohort or snapshot.

## Code assessment

The design is suitably narrow: explicit reviewed path/hash/size selection, immutable content-addressed bytes, bounded UTF-8 transport, existing writer lock and journal, and exact path+hash fallback only when the original is absent. It does not silently replace a corrupt original or rewrite evidence events. Source files are never imported or executed. Snapshot defaults remain unchanged. Failed append can leave an immutable orphan that retry adopts; torn/conflicting index fails closed. This documented behavior is preferable to pretending multi-file atomicity.

One reproducible input-validation issue was reported to root: an identical `(path, sha256)` repeated with a different `bytes` value is skipped before source-size verification. An isolated manifest with one valid row and a duplicate with `bytes=999` was accepted and produced one mapping. No content was overwritten, but a contradictory reviewed manifest should fail. Root assigned the narrow fix and regression test to the implementation owner; final approval of that edge case depends on checking the resulting patch.

Other reviewed limits are deliberate, not security guarantees: filename/private-key/credential-pattern checks cannot detect every embedded secret; explicit provenance review remains necessary. No race-safety claim against a hostile concurrent filesystem writer is made. Returned `.txt` copies are transport evidence and do not materialize the original executable filenames. Preserve these scopes in user-facing documentation.

## Validation actually run

1. `PYTHONPATH=ideation .venv/bin/python -m pytest -q ideation/tests/test_artifact_retention.py ideation/tests/test_hypothesis_artifacts.py`: **17 tests, 12 subtests passed** before the duplicate fix. Existing tests exercise actual isolated CLI snapshot/restore, CRLF preservation, HTML/C++/Python, symlink/path guards, corruption, retry/orphan handling and publication-error preservation.
2. Executed `prepare_reviewed_selection.py`: read-only canonical identity checks, credential-like-value scan (without printing values), then copied only the 117 selected files into a temporary isolated root. Retention verified all 117; exact retry added zero mappings and left index bytes unchanged. Removed only isolated originals and verified **117/117 exact retained-copy fallbacks**. No selected Python/HTML/C++ code was executed. This is transport validation, not a science test.
3. The initial selection preparation intentionally failed on `.gitignore`; it was then explicitly excluded per root instruction. No canonical write occurred in either attempt.

Detailed counts and reviewed code hashes are in `selection-validation.json`. The preparer is reproducible and writes only this external audit directory plus temporary isolated state. Root owns any canonical retention, publication and subsequent restored-snapshot completeness check. No S3 completion is claimed here.

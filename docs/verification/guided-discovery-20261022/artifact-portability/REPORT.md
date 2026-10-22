# Artifact snapshot omission audit

Read-only audit completed 2026-10-22. No canonical data, repository code, manifests, cloud objects or GPU state changed. External audit outputs and two reconstructed corpus databases plus one local restore were created here.

## Findings

Published lineage observed: `e05b413d4ff55f30bbe532094151622e32733ad698f696aecfa3739a1b607acc`, created 01:40:23Z, published according to local lineage receipt at 01:52:40Z. Latest local snapshot observed: `b97f51c715a21d32324deb04e67819c0b080f8881ca32045dc3eb7efc38a49a1`, created 01:59:09Z. No live S3 HEAD request was made; this report does not assert that publication has remained unchanged after observation.

The scoped canonical readbacks contain **304 artifact references**. All local retained bytes match their readback hashes. Latest-local manifest contains **185 exact files and explicitly skips 119**. These 119 references represent **102 distinct content hashes, 5,269,096 deduplicated raw bytes** (6,209,905 bytes counting repeated references).

| Round | Readback artifacts | Published exact | Published skipped | Published predates/absent | Latest local exact | Latest local skipped | Omitted but exact body in latest corpus |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5 | 43 | 25 | 18 | 0 | 25 | 18 | 3 |
| 6-7 | 49 | 19 | 30 | 0 | 19 | 30 | 26 |
| 8 | 6 | 5 | 1 | 0 | 5 | 1 | 0 |
| 9 | 54 | 38 | 16 | 0 | 38 | 16 | 8 |
| 11 | 12 | 5 | 7 | 0 | 5 | 7 | 4 |
| 12 | 51 | 0 | 0 | 51 | 33 | 18 | 6 |
| 13 | 39 | 0 | 0 | 39 | 27 | 12 | 5 |
| 14 | 50 | 0 | 0 | 50 | 33 | 17 | 9 |

Round 10 has no separate canonical artifact receipt in this series; no invented empty cohort was counted. Rounds 6 and 7 share one refinement importer. Round 5 has 25 matching receipt artifacts, although counting all files under the cohort prefix produces extra administrative files; that broader count is not artifact completeness.

The e05 omission for rounds 12–14 is publication timing, not evidence they were filtered at e05 creation. The later b97 manifest explicitly skips their unsupported extensions too, proving a persistent filtering gap beyond the timing gap.

## What survived elsewhere

Both corpus files were reconstructed from local immutable snapshot chunks; every decompressed chunk length/SHA and complete SQLite file SHA matched its manifest. Read-only document revision inspection found, among the 119 latest omissions:

- **61** have byte-identical UTF-8 bodies in retained document revisions. Their source text survives, although file-path restoration and automatic artifact resolution do not.
- **5** have a matching digest in source metadata but no exact body. A metadata hash or transformed HTML text is not the original raw file.
- **53** have neither an exact body match nor such metadata digest. These include CPU fixtures, importer scripts and additional upstream source/test files.

The revision scan covers non-issue/PR documents and all guided-source IDs; it does not claim absence from arbitrary snippets embedded in issue prose. Exact full-file identity is the criterion. The complete row-level matches and precise revision hashes are in `audit.json`.

Latest omissions by extension: 93 `.py`, 8 `.html`, 5 `.hpp`, 3 `.cuh`, 3 `.cpp`, 3 `.h`, 1 `.cmake`, 2 extensionless files and 1 `.png`. Of these, 118 are strict UTF-8; the PNG is `round13-lossless-cache/sources/SplitZip/figs/main.png`.

Representative missing replay code: round5 `layout_contract.py`, round6 `workspace_contract.py`, round7 `domain_components.py`, round9 `representation_audit.py`, round11 `event_order.py` and `write_coverage.py`, round12 `slice_layout.py` and `context_projection_audit.py`, round13 `codec_contract.py`, round14 `tail_bound.py`, `context_row_bounds.py` and `threshold_audit.py`. Their output JSON may survive without the code needed to reproduce it.

## Direct restore check

Ran the existing `storage.restore` against **local b97 immutable archive**, into `restored-latest/research/`. It verified all chunks, file hashes and SQLite integrity checks. Then ran the existing `resolve_artifact` against each canonical state-relative path/hash under the relocated root: **185 verified, 119 missing**. See `restore-test.json`. Thus the reference portability fix works for present files but cannot compensate for snapshot selection omissions. No source script was executed.

## Root cause

`ideation/storage.py::_allowed` uses a default extension allowlist that excludes source/replay formats and HTML. Explicit selection adds HTML/PDF/log/parquet/gzip, but **still does not allow `.py` or C/C++ files**. `snapshot` silently records excluded selections in `skipped`; successful upload means the chosen manifest is complete, not that every hypothesis-linked artifact was chosen. `_manifest` enforces the same path policy during restore, so adding raw files to an old manifest would break identity/validation.

Filename substring filtering (`token`, `secret`, etc.) can also reject harmless source names elsewhere. **None of these 119 scoped omissions contains such a substring**; no relaxation of that protection is justified by this audit.

Existing experiment artifact retention already provides bounded, immutable, content-addressed copies and an append-only index; its own extension allowlist excludes source scripts. Existing hypothesis artifact resolution supplies hash verification and state-relative/legacy-suffix relocation but no retained-copy fallback. A new blanket extension allowlist would conflate arbitrary workspace files with deliberately selected evidence.

## Smallest proposed fix, not implemented

1. Reuse the immutable content-addressed retention pattern for **explicitly selected and hash-pinned research artifacts**, leaving default snapshot exclusions unchanged. Begin with known canonical `research/records/...` artifacts from reviewed import receipts, with matching byte hash/size, bounded size, no symlink/path escape, and explicit provenance. Do not crawl arbitrary repositories or rename files merely to bypass filtering.
2. For strict UTF-8 selected evidence, retain the **original bytes unchanged** at `research/artifacts/<sha256>.txt`. Record original state-relative path, hash, size, type, provenance and retained locator in a small append-only JSONL index under research/artifacts (no new database or orchestration). Reuse the existing state writer lock for deduplicated append and immutable copy. Avoid newline conversion or JSON reserialization. Existing `.txt`/SQLite snapshot handling can then transport the bytes without a storage manifest format change. Reuse an already retained identical blob; do not count a transformed document body as equivalent.
3. Extend read-time artifact resolution to consult that exact path+hash index when the original path is absent. Verify blob hash/size and safe root confinement; return a retained-file projection without editing immutable events. Add an explicit safe materialization/export operation only if replay needs the original filename. Never execute a restored artifact automatically.
4. Treat the one PNG separately: explicit bounded binary retention needs an approved representation (e.g. a typed base64 JSON envelope with original digest/size) or report it as external/unretained. Do not claim all-artifact completeness while leaving it implicit. All 118 text references can be covered without general binary support.
5. At checkpoint, compare selected required references with retained exact bytes and surface **missing/skipped required artifacts as an incomplete recovery checkpoint**, while still distinguishing optional artifacts. Publish a new immutable snapshot under normal lineage CAS. Keep e05/b97 and historical decisions untouched.

Security boundary: content-addressed names are not authorization to retain a secret. Selection must retain original source identity, existing credential/private-key exclusions and explicit review for benign names containing `token`; do not silently whitelist those names. Reject missing/mismatched sources before mutations and expose unsupported formats. Secret detection is an additional check, not a claim that every source file is harmless.

## Alternative: source copies in Git

Git is appropriate for maintained harness code and reusable CPU tests, but it is insufficient as the sole repair for these historical evidence references. A Git commit does not place bytes at restored state paths or satisfy the existing resolver; references need a pinned commit, a checked-out source fetch and mapping anyway. Bulk donor HTML/code and repeated immutable experimental scripts also create repository churn. Keep maintained tools in Git, and retain precisely reviewed historical artifacts in the existing state snapshot. The recommended text-blob mapping is smaller and preserves current S3 recovery semantics without network access during resolution.

No new database is needed: use a bounded append-only JSONL mapping with immutable hash-named payloads and existing writer locking. The resolver should index only verified entries for exact `(original relative path, sha256)` pairs; reject conflicting entries rather than guess by basename. A later materialization helper may create original filenames inside an explicitly selected empty export directory after validation; preserving the bytes as `.txt` does not itself make existing commands runnable under their old names.

## Focused validation proposed

- Fresh isolated selected-text fixture → retain → default snapshot → local restore under new root → resolve original reference → exact bytes and hash. Include one `.py`, raw HTML and a C/C++ fixture; never execute imported code in this transport test.
- Preserve existing event payloads and IDs; retries create no new artifact identity or changed bytes. Verify fail-before-write on mismatched selection, symlink, traversal, wrong size/hash, credential source and corrupt blob/index.
- A benign tokenization source needs explicit reviewed selection; a credential file remains rejected. Broad filename bypass must fail.
- Replay one already approved CPU fixture only as a later separately scoped execution check. Successful transport alone does not validate science.

This report requests no canonical mutation. The root can choose the bounded text-retention implementation after reviewing this evidence.

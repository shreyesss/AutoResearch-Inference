# Selected artifact portability implementation

Implemented only in the four repository files listed in `implementation-manifest.json`; not committed, no canonical state applied.

Command:

```text
researchctl --defer-snapshot hypothesis retain-artifacts --manifest selection.json
```

Explicit reviewed selection pins each state-relative research/records path, SHA256 and bytes, plus bounded provenance. All supported source hashes and existing copies are checked before mutation. UTF-8 bytes are copied unchanged to research/artifacts/SHA.txt; a JSONL mapping is appended under the existing writer lock and journal. No database or orchestration added. PNG/binary and oversized files return unsupported statuses. The existing default snapshot/restore transports .txt/index without policy changes.

Resolver fallback is only for a missing original path and requires exact original relative path+digest mapping, safe blob location, size and hash. Existing corruption is never masked. Historical events/manifests remain immutable. Returned retained files have .txt names; no original path materialization or source execution is automatic.

Security: explicit paths only, no filesystem crawl, outside paths/traversal/symlinks forbidden, credential/.env/key paths and private-key headers rejected. Only whole tokenizer/tokenization source-name segments are permitted through the token-name rule for reviewed selections; token.txt/access_token.json still rejected. Global storage guard unchanged. Review remains necessary; this is not a universal embedded-secret detector.

Failures/retries: immutable link creation never overwrites; copy-before-index failures can leave verified orphan blobs which retries adopt. Exact retries add zero mappings. Torn/conflicting JSONL fails closed; this is not a multi-file transactional database. If checkpoint/publication fails while recording a retention failure, original error is preserved as cause with sanitized mutation_error_type.

Validation actually run:

- Final full research suite: 276 tests, 23 subtests passed in 6.44s.
- Targeted portability suites:17 tests,12 subtests passed.
- Actual CLI retain → deferred marker → research snapshot → storage.restore at different root → resolver verification, including .py, .html, .cpp, cpu_tokenizer_audit.py and tokenizer.json. Exact CRLF byte preservation. Source fixture deliberately raises if executed; no source executed.
- Corrupt original, wrong hash/size, missing source, symlink/path/credential controls, unsupported binary/size, partial append failure, orphan recovery, immutable copy corruption, invalid index, legacy reference, publication-error preservation covered.
- scripts/bootstrap-node.sh --dry-run passed, no changes.
- git diff --check passed; narrow CLI help verified.

No GPU/model/provider/network calls, canonical retention, S3 publication or Git commits performed for implementation. Parent owns review and application. This patch supplies the transport mechanism; it does not claim the historical snapshot gap is repaired until selected canonical retention and a new publication/restore receipt exist.

Parent review correction: duplicate (path,sha) selections with conflicting bytes or effective provenance now fail during preflight; identical duplicates remain idempotent. Added focused tests:18passed+14subtests including prior portability suite. No canonical application. Full suite reported above predates this narrow fix.

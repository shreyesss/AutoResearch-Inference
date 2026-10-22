# Explicit OA PDF reading and honest coverage

## Observed failure

Round45 selected OpenAlex `W7220667292` (SpecEdge) through the real investigate command. The retained record has a DOI and Zenodo landing locations but no `pdf_url`. Before this patch, investigate returned `dossier_ready`, `reads=[]`, `errors=[]`, with only an abstract. Its full-text branch handled arXiv identities only; there was no receipt explaining the missing read.

## Implemented

- For a selected paper without an arXiv identity, use the first eligible HTTPS `pdf_url` in a retained location explicitly marked `is_oa: true`. Recognize `locations`, and optional `best_oa_location`/`primary_location` dictionaries. Do not infer a URL from DOI/title/landing pages or add a resolver.
- Reuse `Sources.fetch`, cache, shared miss budget, existing 8MB bound and pypdf. Require PDF magic and PDF or `application/octet-stream` MIME, then sufficient extracted text. Preserve original content type, raw hash, source record hash, location and source dates. No inferred PDF revision date or version pin.
- Return `fulltext_coverage` and a per-selected-paper `reads` result: completed, skipped with a missing-locator/count/HTTP-budget reason, or failed fetch/extraction. CLI and MCP use this same path. Dossier readiness may still reflect an abstract; generated reports and tool help say so.
- Parsed non-arXiv paper text retains a URL-derived `web:` record ID but `kind=fulltext`, the canonical paper identity and source attribution. Parent/has-fulltext links indicate the selected locator relationship; no paper-to-code relation is invented.
- Cached PDFs can be parsed offline with no network miss. New uncached reads under the zero budget are explicitly skipped.

URL eligibility checks are lexical (HTTPS, no embedded credentials, reject obvious local/private IP literals); they are not a DNS/redirect sandbox guarantee. External downloads remain bounded and must be explicit provider PDF metadata.

## Review-driven fixes

The existing PDF extraction threshold counted our inserted page labels. One blank page already failed, but many blank pages could clear the threshold without extracted paper text. The threshold now counts extracted page content before adding markers. A generated 30-page blank PDF fails and adds no full-text document; if the original source is also empty, no reasoning model is called. An original nonempty abstract remains explicitly labeled abstract evidence.

The former arXiv regex could match a substring on an unrelated host. The expanded PDF surface made that consequential: a selected external PDF path containing `arxiv.org/pdf/...` could be rewritten and assigned another paper identity. Fetch identification and immutable-cache classification now require the actual arXiv host and matching path. An external-host regression preserves its URL, DOI identity and ordinary cache lifetime.

Parent supplied an observed Zenodo PDF served as `application/octet-stream`. This MIME is accepted only with PDF signature and successful extraction; HTML with that MIME still fails.

## Actual field replay

`replay_specedge.py` uses the exact retained source snapshot in a fresh isolated state through real CLI init/import/investigate commands. Both online-enabled (transport denied) and offline calls now report:

```
completed=0, skipped=1, failed=0, selected_papers=1
reason=no_supported_oa_pdf_locator
```

The source remains abstract; no DOI lookup or network call occurs, and the original snapshot remains unchanged.

Separately, `replay_octet_pdf.py` feeds the **already downloaded** 247,351-byte Zenodo PDF into the existing fetch/parser in another isolated store. MD5 and SHA match the parent's receipt. It extracts 17,757 characters, retains octet-stream MIME and replays from cache. Transport is replaced with those retained bytes, so this is a real parser/cache check with no new live network call. It does not manufacture a locator in the original OpenAlex record or certify a general DOI resolver.

## Verification and limits

- Focused tests: 46 passed, plus 5 subtests.
- Full suite: 333 passed, plus 29 subtests.
- `git diff --check` and `scripts/bootstrap-node.sh --dry-run` pass.
- New tests exercise real PDF parsing, real cache, actual CLI and MCP handlers; only provider transport is mocked. They cover successful and malformed responses, missing/unsupported locators, partial failure, count/miss limits, date/hash provenance and offline replay.
- `_import_corpus` is unchanged. No canonical writes, GPU/native/model imports, serving changes or commits.
- PDF extraction remains text-only: no OCR, figure interpretation, table fidelity or scientific validity guarantee. First eligible locator only; no automatic DOI resolution, alternative-location retry or new general web crawler.

See `validation.json` for exact commands and initial test/bootstrap setup errors, `implementation-manifest.json` for reviewed source hashes, and the two replay receipts for field evidence. Parent owns publication.

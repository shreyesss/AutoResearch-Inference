# Independent selected OA-PDF tool review

Reviewer: guided_adversary. Reviewed sources.py, deep_dive.py, MCP description, tool documentation and actual-parser/CLI/MCP tests. No canonical writes, provider calls, model/GPU/backend execution.

## Verdict

No remaining blocker to the narrow change at the file hashes in checks.json. Selected non-arXiv papers can use an explicit eligible HTTPS PDF URL in retained metadata with `is_oa: true`. Missing locators, full-text limits, budget exhaustion and fetch/extraction failures are now explicit per-source outcomes. `dossier_ready` may still mean a usable abstract; full-text coverage is a separate field. This does not implement DOI resolution, landing-page discovery, universal full-paper availability or scientific verification.

## Two review-driven corrections

1. The preexisting parser threshold counted generated page labels. One blank page already failed;20 blank pages generate289 label characters despite zero extracted characters. The fix counts extracted page text before adding labels. My one-page control confirms the existing guard, and the20-page pipeline control ran after the worker's fix and returned `no_usable_sources` with failed full-text coverage. I separately evaluated the former label-count expression; I did not execute an original prepatch20-page pipeline. The author added a real30-blank-page regression. A nonempty original abstract remains available and must be labeled as such.
2. With arbitrary explicit OA hosts newly eligible, the old unanchored arXiv regex could reinterpret an unrelated URL containing `arxiv.org/pdf/...` in its path. Recognition and immutable-cache detection now require the exact arXiv host and matching path. The regression preserves the external locator/web identity and ordinary page TTL. This prevents fabricated paper identity and immutable-cache status.

## Contract checks

- Requests use the existing cache and shared logical HTTP-miss budget. Offline cached reads work; uncached reads are skipped with an explicit budget reason. The count is not a physical packet/redirect count.
- HTML login/abstract responses do not become PDF evidence. Explicit PDF reads require PDF or application/octet-stream MIME, a PDF signature and successful text parsing. The octet-stream allowance addresses the separately observed Zenodo response; it is not arbitrary binary acceptance.
- PDF extraction retains raw content hash, MIME, parser and source-record identity/hash/location. Unversioned PDFs have no invented publication-revision date or version pin. Extracted text availability does not establish paper identity/content correctness or complete figure/table interpretation.
- OpenAlex search already retains `locations`, so the reader can consume existing metadata without an invented arXiv alias. Original selected records remain unchanged; fulltext provenance is retained separately.
- Successful extraction is prioritized as evidence; failed/blank reads create no usable fulltext document. Existing code-only/no-usable-source reasoning guards remain in place.
- URL eligibility is lexical filtering, not a DNS/redirect/network sandbox guarantee. The helper says so. No authentication header is introduced for external PDF downloads.

## Independent execution

Ran the real tests for `test_oa_fulltext.py` and `test_deep_dive.py`:34 tests plus5 subtests passed after final fixes; diff check passed. Only remote transports are mocked in those tests, while actual parser/cache/CLI/MCP paths run. My generated blank-PDF probe used the real parser and investigate path with mocked transport. Initial reviewer receipt generation used system Python without pypdf and failed before writes; rerun used the repository venv, documented in checks.json.

## Remaining deliberate limits

Only the first eligible retained PDF locator is tried. There is no implicit DOI resolver, OA-location search, alternative-location retry, OCR, figure interpretation, or proof that extracted text is the entire relevant paper. A 200-character threshold is a minimum extraction check, not a quality score. Provider failures are exposed, not repaired. These constraints should remain visible to the host agent so it can choose a targeted follow-up rather than infer full-text coverage from dossier readiness.

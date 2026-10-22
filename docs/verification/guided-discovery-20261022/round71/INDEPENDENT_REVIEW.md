# Independent AIPerf ITL normalization review

Verdict: the final reviewed narrow correction is supported. Fifteen new ITL tests passed independently against the actual local normalizer. This does not certify a running AIPerf deployment, old benchmark exports, new inference performance or token-level delivery timing.

## Source and behavior

The exported `input_config.endpoint.per_chunk_usage` is authoritative when present, independently of wire usage/options. Explicit client-side counting, non-chat or non-streaming configurations are rejected by this supported path. Absent config falls back to the adapter's wire `continuous_usage_stats` as a documented compatibility assumption, not general proof of arbitrary historical evaluator configuration. With no opt-in evidence, legacy completion-minus-one validation remains.

For the opted-in supported raw chat export, the helper follows the first response with parsed content and nonempty usage. It handles prose, reasoning and tool function text while ignoring role/tool-ID-only and final usage-only chunks. It does not infer a denominator from ITL. Missing counts and nonpositive/out-of-range integer counts take the pinned fallback; unsupported formats, vendor aliases, malformed content/config/count types become token-counting mismatch rather than a fabricated adjusted result. Input count integrity now rejects nonintegral/negative/boolean counts, reasoning exceeding completion and explicit native OSL disagreement.

The returned count and validation-source label make the selected denominator inspectable. Existing request accounting, wrong length/input checks, timeout/error gates and final `measurement_failed` handling remain. A mismatched metric may still appear in diagnostic aggregates for a completed request, as before; the cell is ineligible, so it must not be read as a qualified success. Request-average ITL percentiles and the frozen objective have not become ICL/gap metrics.

## Concrete issue found and repaired

The initial reviewed code applied `or {}` before checking a present endpoint/options value. A bounded direct call demonstrated that explicit malformed endpoint values `[]`, `False`, `""`, and `0` all admitted an adjusted denominator `(7,3)` by falling through to the wire flag. The author replaced the truthiness coercion with presence/type checks and added full-normalizer negative cases for both endpoint and wire options. Present endpoint `None` is rejected; absent/None top-level optional input_config and absent/None wire stream_options have explicitly documented compatibility handling. The final fifteen-test run includes these new negatives and passes. This was a real malformed-input admission repair, not evidence of an affected historical run.

## Verification and limits

- Independently inspected the complete helper and caller diff plus relevant pinned AIPerf parser, Usage, ITL/OSL and exporter source.
- Independently ran `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/benchmark -p 'test_aiperf_itl.py' -v`: 15 passed. Actual normalizer/export-file fixtures, no model/backend or AIPerf service imports.
- An earlier broader `test_aiperf*.py` run executed 25 tests: 4 errors and2 failures were due to missing `.venv/bin/aiperf`; one saved-hardware export was unavailable and skipped. All then-existing14 ITL tests and other pure normalization tests passed. No full adapter-suite pass is claimed. No executable installation or native launch was performed to hide this prerequisite.
- Raw response parsing is intentionally bounded; it is not a replacement complete AIPerf endpoint library. The first qualifying data+usage response can occur after TTFT, mirroring the pinned helper. Semantic limitations remain disclosed.
- The source-stage reviewer memo remains separate. The critic skill paragraph correctly preserves the objective and demands explicit granularity/population provenance; no improvement in future research yield is claimed.

No remaining blocking issue found within this patch scope. Future broader endpoint/version support requires explicit source contracts and tests, not permissive guessing.

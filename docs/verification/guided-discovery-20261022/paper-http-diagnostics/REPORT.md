# Paper-provider diagnostics and exact-query retry

Round16 had two HTTPError receipts with no numeric status. The tool now preserves only numeric 100–599 HTTP status along with error type; it never copies authenticated URLs, headers or response messages. Four mocked end-to-end provider cases (arXiv429/400, HF503, OpenAlex401) verify status retention and secret-string exclusion, with one call each and no semantic retry.

One actual explicit retry of round16 query01 was run in separate state, retaining the exact query, June1 inclusive–Oct23 exclusive interval and limit8. It completed with eight results, one logical request and a cache miss. This does **not** identify the earlier error or empirically validate failure metadata: old receipts remain unknown-status failures; failure behavior is covered by injected tests. A failed query is not empty-result coverage.

All eight abstract dispositions are preserved. UlaCache (published October21) was forwarded for fulltext and pinned-source inspection in round17; no new hypothesis is accepted from its abstract. Other hits are background or fail current exposure/compatibility triage. No GPU/model calls or serving changes. Local isolated state retained; no canonical import or S3 publication claimed here.

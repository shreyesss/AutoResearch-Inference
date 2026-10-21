# Online paper discovery: capability and recall check

22 October 2026. This is an actual keyword retrieval check using the existing cached provider clients and the newly exposed `paper-search` CLI / `search_papers` MCP interface.

## What was running before this check

The detached background job backfills GitHub issue/PR opening records. It explicitly sets paper and citation budgets to zero. Paper discovery runs on `researchctl refresh` or online `researchctl run`; configured freshness (24 hours) is not a timer. The default discovery configuration contains arXiv, OpenAlex and HF providers, 20 keyword families, a 120-day recency window, eight paper-search calls and two citation calls per bounded refresh. Families rotate and incomplete arXiv queries retain cursors. A single refresh does not search every family.

Before this check, both TreeSpark identities were retained as user-provided seeds and had available full text. The four other original examples were absent. This did not establish independent discovery of the supplied papers. The VM sync timer replicates data; it does not discover literature.

## Actual retrieval

Four queries, each sent to arXiv and OpenAlex with 20 results maximum per provider:

1. `speculative decoding`
2. `tree speculative decoding`
3. `recurrent speculative decoding`
4. `diffusion speculative decoding`

Publication/submission window: **2026-09-01 inclusive to 2026-10-23 exclusive**. Eight logical provider searches, existing caching, zero Serper/model/GPU calls. Query words were chosen with prior domain context; no paper titles or IDs were passed as queries. This is not a blinded prospective recall evaluation.

| Supplied paper | Example keyword retrieval | Provider rank |
|---|---|---|
| [TreeSpark — learning to draft trees](https://arxiv.org/abs/2610.20175) | `tree speculative decoding` | OpenAlex 3; arXiv 13 |
| [ReaDy](https://arxiv.org/abs/2610.20503) | `recurrent speculative decoding` | arXiv 2; OpenAlex 5 |
| [D-Loop](https://arxiv.org/abs/2610.06011) | `diffusion speculative decoding` | OpenAlex 4; arXiv 6 |
| [On the SPOT](https://arxiv.org/abs/2610.22543) | `diffusion speculative decoding` | arXiv 5; OpenAlex 8 |
| [SpecFold](https://arxiv.org/abs/2610.04875) | `diffusion speculative decoding` | arXiv 3; OpenAlex 7 |
| [Additional TreeSpark — calibrated/load-adaptive](https://arxiv.org/abs/2609.22098) | Not returned by these four bounded queries | Retained from previous seed lookup only |

**5/5 original examples retrieved; 5/6 when including the additional TreeSpark identity.** The broad query alone did not retrieve the original TreeSpark in its top 20 per provider. It retrieved D-Loop through OpenAlex at rank 15, alongside the distinct paper [DLoop](https://arxiv.org/abs/2610.07659). Matching uses explicit arXiv IDs/provider canonical identity, not title similarity.

These are source metadata/abstract hits, not full-paper critiques or target suitability decisions. New sources are retained with revisions, query provenance and dated receipts. Cross-provider results are preserved as separate source records; ranks are within each provider, not a unified scientific relevance score. Full receipts and all returned ranks are in [keyword-retrieval.json](keyword-retrieval.json).

## What this changes

The underlying online search already existed. The missing direct provider/date controls are now exposed through both CLI and MCP, using the same writer lock, cache, journal and state store. An example:

```bash
researchctl paper-search 'recurrent speculative decoding' \
  --provider arxiv --provider openalex \
  --after 2026-09-01 --before 2026-10-23 --limit 20
```

MCP: `search_papers(query=..., providers=["arxiv","openalex"], after=..., before=..., limit=20)` requires server `--allow-network`. The host chat client is not automatically registered by this code change.

No continuous paper scheduler was installed. To discover on demand, call paper-search directly or invoke refresh/run for the configured feed rotation. For research quality, inspect source text and implementation, examine applicability/counterevidence, and only then propose and screen hypotheses. The additional TreeSpark miss is a reason to add a load-adaptive mechanism query or citation expansion, not to claim exhaustive recall.

Verification: **209 research tests passed**, including provider/date forwarding, exclusive upper dates, invalid-bound rejection, partial-provider failures, credential-safe errors, persistent query evidence and the MCP network boundary. Bootstrap dry run passed. No serving workload was changed.

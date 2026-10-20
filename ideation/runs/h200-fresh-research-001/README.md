# Fresh H200 hypothesis research

Fresh primary-source research against the running H200 configuration, including
all 13 CSV repositories and relevant SGLang, Humming and vLLM FlashMLA sources.
No new GPU performance result is claimed.

Research is complete. Read the [report](REPORT.md), [ranking](RANKING.md),
[17 mechanism cards](experiments/README.md), [repository coverage](REPOSITORY_COVERAGE.md)
and [literature review](LITERATURE_REVIEW.md). Eight conditional diagnostic plans
are registered; the frozen rubric retains 16 deferred mechanisms and one
inactive Engram rejection. No candidate is experimentally qualified.
The earlier `../pr-evaluation-audit-001/h200/` manual experiment remains intact.

- `source-index.jsonl`: all 5,532 original URL/title identities; no inherited
  B200 applicability filters.
- `supplemental-source-index.csv`: selected external repository leads.
- `discovery/`, `primary/`: live discovery, primary text, patches and provenance.
  Discussion capture is HTML-visible, not an exhaustive formal-review archive.
- `baseline/`: read-only live inventory, startup dispatch, installed code and
  dependency snapshots.
- `policy/`: generated rubric, preserved original and a documented prose-scale
  correction in the frozen copy. No novelty gate.
- `attention/`, `compute/`, `systems/`, `cross-engine/`, `prefill-mqa/`: separate evidence,
  proposal, prior-art lookup and critique artifacts using the existing tools.
- [Model review and repairs](MODEL_REVIEW.md): failed oversized inputs, immutable
  revisit ancestry, exact-quote repairs and all selection outcomes.
- [Validation receipt](validation.json): 53 software tests, final evidence/card
  quote checks, unchanged frozen inputs, local links and secret-value scan.
- `planned-tests.json`, `decision-ledger.csv`, `memory-export.json`: scoped
  conditional plans and durable decision history, with no runtime test events.
- [Evaluation protocol](EVALUATION_PROTOCOL.md): H200-specific activation,
  correctness, telemetry, paired confirmation and frontier contract.

Use the fast URL-first interface from `ideation/`:

```bash
.venv-research/bin/python -m ideation tool github.catalog --args '{"query":"Hopper SM90","limit":20}'
.venv-research/bin/python -m ideation tool github.open --args '{"url":"https://github.com/sgl-project/sglang/pull/41561","refresh":true,"pr_details":true}'
```

The original CSV was indexed without network requests. Reindexing unchanged
entries is idempotent. Primary bodies, PR refs, discussion and patches are
fetched only when useful. The initial four-day opening-feed refresh was executed
before the user's URL-first clarification; it is recorded for provenance and is
not a prerequisite or the default workflow for future research.

Provider settings come from `/home/ubuntu/.env` via `IDEATION_ENV_FILE`. No keys
are copied here. Environments are the repository's pinned research and Fathom
requirements. Model calls use the configured authenticated CLI without a model
override. Proposer and critic are separate calls, not independent human experts.

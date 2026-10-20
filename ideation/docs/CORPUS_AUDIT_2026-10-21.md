# PR and issue acquisition status — 21 October 2026

**Follow-up:** the subsequent [continuation scan](../runs/h200-continuation-001/FILTERING_AUDIT.md)
audited 8,908 local identities, retrieved/refreshed 2,202 opening records from
17 repositories, and exhausted DeepInfer's all-state feed at 95 PRs. Four other
feeds remain capped with saved continuation cursors. It uses an isolated corpus
copy in this worktree. The counts and remote-access findings below remain the
earlier audit snapshot; neither pass establishes an exhaustive discussion/diff
archive. See [DeepInfer findings](../runs/h200-continuation-001/DEEPINFER.md).

**Targeted cross-repository research completed; a complete bulk archive is not
established.** The later research workflow explicitly switched to URL/title
indexing and opening selected sources on demand. Its completion must not be
reported as downloading every PR, issue, discussion and diff.

This audit reads local artifacts and the local SQLite database without changing
the corpus. [Machine-readable receipt](corpus-audit-2026-10-21.json) records counts,
checkpoints, artifact hashes and the remote-access limitation.

## Completed, with retained files

The [fresh H200 research pass](../runs/h200-fresh-research-001/README.md) indexed
all **5,532 supplied URL/title identities across 13 repositories**, plus **74
supplemental leads**. The local catalog contains 5,606 entries. It retained
**108 selected primary PR/issue pages across 16 repositories and 69 patches**.
The audit checked the saved HTML, extracted text and available patch hashes
against the primary receipts. Acquisition does not imply equal-depth code review.

| Repository | Original URL/title entries | Selected primary pages | Patch snapshots |
| --- | ---: | ---: | ---: |
| vLLM | 4,209 | 39 | 37 |
| SGLang | Supplemental | 15 | 10 |
| DeepEP | 188 | 3 | 2 |
| DeepGEMM | 179 | 11 | 10 |
| Other repositories | 956 | 40 | 10 |
| **Total** | **5,532 original entries** | **108** | **69** |

Other repositories include FlashInfer, FlashMLA, DeepJIT, DeepSelect, DeepSpec,
TileKernels, Engram, recipes, InferenceX and Humming. The original URL totals do
not include the 74 supplemental leads. See the full
[repository breakdown](../runs/h200-fresh-research-001/REPOSITORY_COVERAGE.md).
These figures describe that retained research pass; they are not cumulative
counts across every overlapping research run.

The local corpus at `/home/ubuntu/AutoResearch-Inference/ideation/data/corpus.sqlite`
contains **5,584 PR opening records and 1,273 issue records**, alongside other
document kinds. It is a different database from the historical controller corpus.
Its newest document fetch is 20 October, 18:07:09 IST. Its recent-feed completion
checkpoints cover bounded discovery, not full historical collection. HTML-visible
discussion exists in the retained pages, but there are no separate comment,
formal-review or diff document rows in this local database.

## Incomplete or unverified

- The original controller's saved snapshot contains 42,601 vLLM PR records and
  19,138 issue records. Its separate PR metadata enumeration was still at next
  page 396; bulk discussion feeds had not begun. The snapshot is from 20 October,
  approximately 04:50 IST, and must not be presented as current collector state.
- The historical H200 audit later reports a 92,050-document controller corpus.
  That mixed document count supplies neither per-repository coverage nor proof
  of complete feeds. It cannot be added to the local counts as unique items.
- This node cannot resolve the documented `sofia-gpu-mumbai` SSH alias, and has
  no local `ideation-sync` service/timer. The collector's present state is
  **unverified**; absence of a service here does not prove the remote collector
  stopped.
- The checked-in sync service defaults to vLLM. The retained evidence does not
  establish an exhaustive scheduled backfill for SGLang, DeepEP or the other
  libraries. Selected patch failures and partial discussion capture remain
  recorded. Formal reviews and diffs were designed for on-demand hydration.

To close an exhaustive-download task, reconcile the intended repository/date/
content scope with the authoritative collector, then report per-repository feed
completion, failures and latest refresh time. Full opening-body coverage,
discussion coverage and patch coverage require separate receipts. The later
URL-first workflow remains the documented acquisition policy; this audit does
not start a new bulk download.

Evidence: [saved collector checkpoints](corpus-status-latest.json),
[historical state](CURRENT_STATE.md),
[fresh primary manifest](../runs/h200-fresh-research-001/primary-manifest.json),
and [configured sync service](../systemd/ideation-sync.service).

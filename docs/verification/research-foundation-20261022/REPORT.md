# Research foundation verification — 22 October 2026

## Delivered implementation

Worktree: `/Users/shreyas/workspace/AutoResearch-Inference`, branch `infra/research-foundation`, based on recovered commit `61ec1705bccb9812d8d7282b3774264b7411e0a0`.

Original `/Users/shreyas/workspace/skunk-work` remains intact. The canonical live state is `/Users/shreyas/.local/share/inference-autoresearch`, independent of the code checkout.

See [system architecture](../../RESEARCH_FOUNDATION.md), [installation](../../PORTABLE_SETUP.md) and [storage format](../../../ideation/docs/STORAGE.md).

## Real recovery, not a new empty database

Merged read-only inputs:

- Old `ideation/data/demo.sqlite`: 5,099 records.
- Old `ideation/data/corpus.sqlite`: 9 records, largely overlapping papers.
- Retained `h200-continuation-001/sources/feed-openings.jsonl.gz`: 2,202 records.

After identity deduplication, before new API calls: **7,305 records**, including **4,073 PRs**, **3,131 issues**, 58 paper records, 20 comments, 16 diffs, 5 full texts and 2 reviews. This is a partial recovered corpus, not every PR/issue in every configured repository. The imports preserve older revisions and conflicting checkpoints without overwriting a newer local projection. [Receipt](status-before-refresh.json).

Recovered memory: **97 hypothesis records**, of which **28** have original identities and **69** are explicitly marked artifact-scoped reconstructions. Archived **229 source artifacts**, retained **42 historical events**, and restored **8 verifiable planned tests**. Nine known identity mappings remain unresolved and are preserved as gaps. The old export reports global totals 157/414/8, but actually contains only 17 hypotheses/42 events/8 plans; the importer does not pretend the whole lost ledger was exported. [Detailed receipt](memory-import.json).

Separately restored three measured-attempt receipts:

| Attempt | Scope | Retained outcome |
|---|---|---|
| C25 component-002 | component | validated sampler component result |
| C24 short probe | component instrumentation | inconclusive |
| C25 native-003 | native | error/interrupted |

C26 remains a source-applicability rejection, not a fabricated failed GPU run. Local retained artifacts were checksum-verified before these imports. [Receipt](experiment-import.json).

## Live discovery and deeper reading

The bounded smoke configuration intentionally used two repositories, two exact arXiv seeds and one OpenAlex query. The production template retains all 20 keyword families and a configurable wider repository list.

| Check | Observed result |
|---|---|
| First refresh | 2 GitHub page calls, 3 paper queries, zero errors |
| Repeat refresh within freshness window | **0 GitHub pages, 0 paper searches, 0 citation calls** |
| Paid web search | No Serper calls in the smoke run |
| Distinct paper identity | `2610.20175v1` and `2609.22098v1` retained separately |
| Full texts | 93,904 and 72,784 extracted characters |
| Pinned implementation evidence | Actual `tree_speculative.py`, `cost_model.py`, `serving_sim.py` at commit `3894bcca5d096517816284bf2294f2540daf22cd` |
| Citation provider | Failed on these fresh IDs; failures retained, no fabricated citations |
| GPU work | None |

Receipts: [first refresh](live-refresh-1.json), [cached repeat](live-refresh-2.json), [first dossier](live-dossier.json), [reasoning run](live-reasoning.json).

The first dossier exposed a repository-selection defect: links from one paper consumed both slots. Fixed to prioritize explicit original-source links and allocate repository slots across selected papers. The original receipt remains unchanged as evidence of the defect; regression tests cover it. Citation failures now produce explicit failed receipts rather than empty apparent successes.

## Optional reasoning actually ran

Ran the existing evidence extraction → exact-quote validation → task rubric → proposal → critique flow, with pinned source files and `require_novelty:false`. It produced one proposal accepted **for test design**, score 71/100 under the frozen task policy. This score is a prioritization judgment, not a predicted gain.

The proposal is a bounded TreeSpark transfer diagnostic: first re-attest the deployment, check parent-conditioned draft scores/tree-mask interfaces, then measure exposed draft/verifier/sampling cost per accepted token against the strongest static budget. H200 and B200 decisions remain separate. A service pilot is conditional on compatibility and plausible ROI; no local speedup is claimed.

- [Decision](reasoning-decision.md)
- [Run manifest](reasoning-manifest.json)
- [Frozen rubric](reasoning-rubric.json)
- [Explicit brief](reasoning-brief.json)

This run demonstrates that retrieval, evidence validation, adaptive selection and persistent memory are connected. It does not establish that TreeSpark improves the user's deployment.

## Durability

User explicitly approved the private S3 bucket and uploads. Created `s3://autoresearch-641134885443-us-east-1/autoresearch/` with public access blocked, bucket-owner-enforced ownership, SSE-S3 encryption, TLS requirement, versioning and restricted HEAD-version lifecycle. [Provisioning receipt](s3-provision.json).

The existing `bitlane-host` instance role initially received 403. Added read-only access to this bucket's `autoresearch/` prefix for restore, without copying long-lived credentials or granting node publication rights. [Policy receipt](s3-node-reader-policy.json).

Research and experiment registries publish to independent heads. Configured automatic publication on the authoritative workstation after online mutations. Local snapshots survive failed publication; stale writers fail instead of overwriting another machine. Offline commands remain offline. Remote readers must explicitly take ownership before writing.

The first research snapshot was downloaded from S3 and restored into a fresh local directory, yielding **7,314 documents** with corpus integrity verification. This snapshot predates the later reasoning result; later publication retains that result. [Pull](restore-pull.json), [restore](restore-result.json), [status](restore-status.json).

The same first snapshot was also restored on `bitlane-b1` under `/home/ubuntu/.local/share/inference-autoresearch-foundation`; local search returned three matching records. The bootstrap installed the CPU research package and optional agent/storage dependencies on Python 3.12.3. Bitlane serving release `bdbc013` was untouched. [Node status](b200-restore-status.json).

Small experiment evidence was subsequently retained and published: six event references resolve to five unique JSON/Markdown artifacts (13,133 bytes), with unchanged original event receipts. [Artifact retention](experiment-artifact-retention.json).

The final committed installation was then restored on B200 at `/home/ubuntu/AutoResearch-Inference-foundation`, with live state at `/home/ubuntu/.local/share/inference-autoresearch`. It recovered **7,318 source records, 98 hypothesis records and all three experiment outcomes**. C25 evidence resolves to Linux-local paths and verifies against the original SHA-256 hashes. [Final node verification](b200-final-verification.json).

## Tests and boundaries

The research suite covers migration, revisions, independent recent/archive cursors, caching, budget limits, source identity, fulltext/code evidence selection, experiment scopes, immutable events, SQLite WAL capture, corrupted snapshots, unsafe paths, stale publication and clean restores. **143 research tests pass** at this checkpoint. See [latest test output](research-tests.txt).

A one-time full legacy-suite run reported **250 passed, 12 failed, 3 skipped**. Failures were in older AIPerf/tokenizer/model-fixture-dependent tests and a macOS path assertion. These are not a successful serving-harness validation; no GPU tests were executed. The research installation deliberately does not install model weights or the old campaign's pinned execution environment.

New scheduled jobs were not installed. Research runs refresh due feeds; periodic invocation remains an operator scheduling choice. OpenAlex/HF results are bounded, metadata rankings are heuristic, source fulltext extraction lacks OCR, and model review is fallible. Source snippets and author-reported speedups do not become locally validated outcomes.

Final local source count after the live read/reasoning run: **7,318 records**, including 63 paper records and 7 full texts. Hypothesis memory now includes the new test-design proposal in addition to the 97 reconstructed records. [Final status](final-status.json).

## Cost

Planning example: **6.45 GB retained + 10,000 PUT + 100,000 GET/HEAD per month ≈ $0.24/month**; 50 GB with the same requests ≈ $1.24/month. Rates: $0.023/GB-month, $0.005/1,000 PUT and $0.0004/1,000 GET/HEAD. [AWS S3 pricing](https://aws.amazon.com/s3/pricing/).

At the recorded final check, 219 current S3 objects occupied **72,392,344 bytes**, about **$0.001665/month for storage alone** at the stated rate. The bucket is verified nonpublic, encrypted and versioned. [Cloud inspection](cloud-status.json). Actual initial corpus storage is much smaller than the planning example. Immutable history grows with unique changed chunks; no garbage collector or hard dollar cap is installed. Internet/cross-region egress, taxes, additional traces and model reasoning are excluded. Bucket storage is not a promise of free model/API usage.

## Source publication status

Both workstation and B200 checkout failed GitHub `push --dry-run`: no HTTPS push credentials are configured. No branch on GitHub was overwritten. Implementation commit `471326ee7a78fb248d97522ed374cfe17da40e06` was published as a 142,481-byte Git bundle to the private bucket and checksum-verified while installing the branch on B200. [Initial code release](code-release.json). The S3 `autoresearch/code/LATEST.json` manifest identifies the latest bundle; later documentation-only delivery commits can advance that pointer. A pushed GitHub branch must not be claimed until authentication is available.

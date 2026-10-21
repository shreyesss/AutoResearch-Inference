# Chat research tools and resumable corpus collection

Date: 2026-10-22 (Asia/Kolkata). This is an implementation receipt, not a claim that research hypotheses were validated.

## Delivered

- Four repo-owned skills: discovery, research, critique and implementation. Skills direct the current chat; the downloader does not autonomously reason.
- `researchctl backfill start|status|stop`: singleton background collector, four-page fair batches, all-history scope validation, preserved previous window checkpoints, shared rate-limit cooldown, resumable cursors, hot reload of explicit GitHub token file, measured throughput estimate, periodic S3 snapshots. Full bodies/basic opening metadata only; no automatic all-thread hydration.
- `expand`: offline bounded query suggestions, taxonomy provenance, counterevidence queries, local/arXiv/OpenAlex formatting and explicit dates. It suggests; it does not silently consume search/API credits.
- `prescreen`: conditional gain accounting with explicit time units, component call counts, critical-path exposure, accepted output progress, task-specific worthwhile-gain threshold and tail guards. Unknowns remain unknown; no default novelty gate or numerical speedup assertion.
- `hypothesis record|recall`: chat-authored proposals and attributed dispositions in the existing graph, source quote checks, immutable-card revisions and retained prescreen rationale. Accepted selection remains untested.
- Invocation journal with starts/finishes/errors, restored-history merge and retained snapshot copy. No provider environment values or arbitrary query text recorded in this journal.
- `sync-replica` and `--replica search|show|status`: verified versioned research reads, separate from all canonical writer/experiment databases. Crash recovery checks existing restored bytes before publishing the pointer. Unchanged remote HEAD uses one small lookup.
- Optional user systemd timer under `infra/research-replica/` for ten-minute VM pulls; its installation/runtime receipt is recorded separately.

## Verification

- `python -m pytest ideation/tests -q`: **186 passed** at this implementation checkpoint.
- All four SKILL.md files pass skill-creator quick validation.
- Isolated CLI hypothesis round trip: init, add source fixture, record twice, recall, history. One immutable hypothesis, two lifecycle events, accepted remains untested, no publication.
- Local transport tests verify stale-writer protections, replica/writer separation, cross-node command-history preservation and replica restore/marker crash recovery.
- Existing GPU execution suite was not rerun; this change does not execute or alter serving workloads.

## Observed live collection

The source recovery had 7,318 records across papers/PRs/issues and retained auxiliary evidence. This was not full GitHub coverage. Started all-history collection for ten configured repositories. A user-supplied token was verified by live response headers granting 5,000 requests/hour; the token itself is never retained in this receipt. Initial authenticated page timing was about 2.1 seconds/page. Repository sequence upper bounds implied roughly 40–50 minutes for remaining fetching at that point, excluding publishing, pauses and failures. Use live `backfill status`, not this frozen estimate, for current progress.

Each opening record is upserted by original GitHub identity, preserving observed material revisions. Imported record counts are not treated as scanned coverage. Two TreeSpark repositories returned successful empty full-history scans; those are zero records, not missing pagination.

The workstation is the corpus writer and must remain running to download. Approved private S3 stores published checkpoints. The VM reads independently versioned snapshots; its own experiments are preserved. This delivery does not claim a hosted continuously running research agent, automatic GPU evaluator, universal paper access, or complete cleanup of the older benchmark execution code.

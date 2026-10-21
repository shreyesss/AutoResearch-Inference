---
name: inference-discovery
description: Find and refresh inference papers and GitHub issue/PR evidence, inspect local coverage and dated searches, and check research-state publication or recovery.
---

# Inference source discovery

Read `docs/CHAT_RESEARCH_WORKFLOW.md` for commands and `docs/RESEARCH_FOUNDATION.md` for retrieval semantics. Use the configured state root and repository list; the checkout's historical run folders are not the live database.

For a request to **find new work**, refresh due sources and search the combined corpus. For an explicitly local/offline inspection, search without network access. `researchctl search` itself never refreshes. `researchctl run` refreshes within configured budgets; it does not finish every feed or read every candidate. Report the scope actually searched and the last successful refresh, including unresolved pagination and provider failures.

Expand the user's mechanism into complementary queries: exact symbols/features, architectural aliases, bottleneck/work removed, alternative implementations and contrary evidence. Preserve requested model/hardware/date specificity but include transferable mechanisms when appropriate. Use the query expansion tool as a transparent suggestion generator; it does not itself discover or verify sources. Do not treat a configurable keyword directory as the full boundary of relevance.

Use `researchctl plan`, then bounded `refresh` or `run`; use `search --after ... --before ...` and `show ID --history` for inspection. Local `researchctl search` filters the stored `updated_at` field, with inclusive lower and exclusive upper bound; this is not necessarily a paper's publication date. Provider paper-discovery date filters have their own semantics. State the actual predicate when reporting a dated result. Inspect the full opening body before hydrating selected discussions/diffs or reading full text. Preserve source IDs, revisions, access dates and pinned code commits.

An all-history opening-record download includes bodies and basic metadata. It does not include every comment, review, diff or historical PR revision. A recent-window checkpoint and a record count do not prove full-history coverage; completion requires the archive cursor to exhaust at the requested scope. Use job/status receipts for ETA; never infer completion from the highest issue number. Respect API reset times, preserve cursors and retain cached responses.

Use arXiv, OpenAlex and Hugging Face discovery, then available lawful open full text and author/project code. Explicitly distinguish metadata-only, abstract, full text and inspected implementation. A citation edge to an unresolved paper is not evidence that the paper was read. Do not spend Serper budget for local searches or known-URL fetches, and do not use a model's recollection as a fetched source.

Before reporting S3/VM synchronization, inspect the publication receipt and destination state. Code Git history, S3 snapshot publication and a VM's restored database are different operations. Preserve one authoritative writer per lineage. Never reset local lineage to a newly observed remote head or replace a VM's unpublished work to make synchronization appear successful. See `ideation/docs/STORAGE.md` for recovery mechanics.

## Refined evidence-to-experiment tools

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for typed claims, `hypothesis propose/show`, hypothesis-linked `screen`, `eval-plan`, attributed `decide`, source-change alerts and MCP. Prefer these contracts for new work; legacy cards remain readable. A selection verdict from the older model workflow is not an executable evaluation-plan approval. The plan tool checks reproducibility and evaluator coverage; scientific applicability and execution authorization remain separate.

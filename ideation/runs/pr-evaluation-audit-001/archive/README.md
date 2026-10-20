# Archived audit evidence

These files are retained for traceability but are not the first place to read the experiment plan.

| Path | Contents | How to use it |
|---|---|---|
| [`evaluator-source-snapshot/`](evaluator-source-snapshot/) | Partial copy of 149 files from the inspected `Deepseek_serve` commit | Inspect exact source lines cited by [evaluation capabilities](../evaluation/EVALUATION_CAPABILITIES.md); verify bytes against [snapshot-manifest.json](../evaluation/snapshot-manifest.json). It is not a runnable serving tree. |
| [`evaluator-cli/`](evaluator-cli/) | CLI help, dry-run, `--plan` and search captures | Supports claims about commands that were inspected, not GPU execution. |
| [`memory/memory-before.sqlite`](memory/memory-before.sqlite) | SQLite database before registration of these plans | Historical backup, not the active ideation memory DB. |
| [`logs/kernel-upstream.log`](logs/kernel-upstream.log) | Specialist retrieval log | Raw provenance; use candidate JSON/reviews for decisions. |
| [`original-deliverable/deliverable-sha256.json`](original-deliverable/deliverable-sha256.json) | Hash list from the original audit delivery | **Stale for current docs**; retained only to explain the original delivery. Use `git` and the input/snapshot manifests for present files. |

The frozen catalog inputs remain in `../inputs/` because offline ledger regeneration and quote validation need them. No archived material was deleted.

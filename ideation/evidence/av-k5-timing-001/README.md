# AV-OFF k5 timing evidence

This archive preserves the one baseline diagnostic for [C24](../../hypotheses/C24.md): [report and verdict](../../runs/av-k5-timing-001/REPORT.md), [frozen contract](../../runs/av-k5-timing-001/EVALUATION_CONTRACT.md), [independent review](../../runs/av-k5-timing-001/EVALUATOR_REVIEW.md). Adaptive verification remained off. No full A/B attempt or speedup is claimed.

| Archive | Contents |
| --- | --- |
| `research-records.tar.zst` | Complete diagnostic record, raw startup/backend/router/client logs, all 16 worker traces, source identities, offline reader history and analysis. |
| `serving-results.tar.zst` | Complete AIPerf run and exports, request records, telemetry, metrics, command, manifest and score. |
| `implementation-evaluator.tar.zst` | Separate serving-worktree observation sources, evaluator/controller/readers, tests, launch renderer and exact input prefix. |

[ARCHIVES.json](ARCHIVES.json) records compressed hashes and sizes. Each `*.files.json` lists every workspace-relative path, byte count, SHA256 and source permission mode. Archives use Git LFS; readable conclusions and manifests use ordinary Git. Paths retain their original `AutoResearch-Inference-c03/` or `Deepseek_serve-c03/` prefix.

From this repository, run `git lfs pull`. Then restore into a **new** directory:

```bash
python3 ideation/evidence/av-k5-timing-001/restore.py --destination /tmp/av-k5-evidence
```

The script checks each archive and every restored file, preserves ordinary executable/read-only permissions, and refuses an existing destination, path traversal or non-regular members. Python3 and `zstd` are required. Original worktrees, environments, credentials and model weights are not overwritten or included. Raw records may contain synthetic workload text and generated output, so the report contains only measured summaries.

The research archive is the finalized run snapshot at publication; later corrections must be append-only follow-ups with their own evidence. [Restoration verification](restoration-verification.json) records the archive check. [Publication verification](publication.json) records the upstream content commit and a fresh remote download with all three archive hashes checked. This run's original environments and 30 pinned file checks passed after cleanup; all eight GPU allocations were released and monitoring remained running.

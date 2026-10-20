# C03 complete evidence archive

The readable [execution report](../../runs/c03-execution-001/REPORT.md), [plan](../../runs/c03-test-plan-001/EXECUTION_BRIEF.md) and [mechanism review](../../runs/c03-mechanism-review-001/REPORT.md) remain in ordinary Git. This directory preserves the larger supporting evidence from both local worktrees. Compressed archives use Git LFS so ordinary Git history contains small pointers.

| Archive | Original contents |
| --- | --- |
| `research-records.tar.zst` | All files from c03-test-plan-001, c03-execution-001 and c03-mechanism-review-001, including failed diagnostics, complete server logs, event history and final sealed receipts. |
| `serving-results.tar.zst` | All C03 serving result directories: raw AIPerf exports, telemetry, HTTP traces, server logs, metrics and run summaries for diagnostics and screens. |
| `implementation-evaluator.tar.zst` | The complete C03 source overlay, baseline/candidate manifests, patch, evaluator implementations, tests, fixtures and review handoffs. Python bytecode caches are excluded. |

[ARCHIVES.json](ARCHIVES.json) records compressed hashes and sizes; the three `*.files.json` manifests give every original workspace-relative path, byte count and SHA-256. [provenance.json](provenance.json) records repository bases. [serving-worktree.patch](serving-worktree.patch) and [serving-snapshot](serving-snapshot/) retain launcher changes and additional source-review/test files outside `c03/`. No environment directories or credential files are included. This is an exact historical snapshot: some implementation README files describe an earlier development stage; the final execution report and independent review establish the final state.

To recover the full evidence in a separate empty directory:

```bash
git lfs pull --include='ideation/evidence/c03-20261020/*.tar.zst'
python3 ideation/evidence/c03-20261020/restore.py --destination /tmp/c03-evidence
```

The restoration script verifies archive hashes, refuses unsafe paths and refuses to overwrite an existing destination. It extracts paths beginning with `AutoResearch-Inference-c03/` and `Deepseek_serve-c03/`, then verifies every restored file. Historical absolute links refer to `/home/ubuntu`; prepend the chosen restoration directory to the corresponding workspace-relative manifest path when browsing elsewhere. Original files and frozen hashes were not rewritten to make those links portable.

The Git checkout exposes concise documents and structured result receipts directly. Large `.log` files and repeated raw observation snapshots are recovered from these archives. The explicit manifests make this distinction inspectable; an omitted raw file in the ordinary tree is not missing evidence.

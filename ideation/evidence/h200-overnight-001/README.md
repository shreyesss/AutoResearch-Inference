# H200 overnight evidence

The [interim report](../../runs/h200-overnight-001/REPORT.md) summarizes completed C24/C25/C26 work. Native C25 execution is pending; this archive will receive a separate immutable group for that execution.

`completed-components.tar.zst` preserves all four bounded component/instrument allocations, including the failed checkpoint mount, raw traces, compiled caches, actual image source snapshots and complete historical trace audit. [ARCHIVES.json](ARCHIVES.json) binds archive hashes; `completed-components.files.json` lists 349 workspace-relative paths, sizes, modes and hashes. Readable reports, code and small receipts remain ordinary Git files; this archive uses Git LFS.

Run `git lfs pull`, then restore into a new directory:

```bash
python3 ideation/evidence/h200-overnight-001/restore.py --destination /tmp/h200-overnight-evidence
```

The restorer rejects existing destinations, unsafe paths and non-regular members, and verifies every restored byte. It preserves original `AutoResearch-Inference-c03/` paths without overwriting the research or serving worktrees. Model weights, environments and credentials are excluded. A local restore of all 349 files passed before native execution.

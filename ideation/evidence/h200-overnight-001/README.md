# H200 overnight evidence

The [interim report](../../runs/h200-overnight-001/REPORT.md) summarizes completed C24/C25/C26 work. Native C25 pair002 is running; completed allocation001 is preserved in its own immutable group.

`completed-components.tar.zst` preserves all four bounded component/instrument allocations, including the failed checkpoint mount, raw traces, compiled caches, actual image source snapshots and complete historical trace audit. [ARCHIVES.json](ARCHIVES.json) binds archive hashes; `completed-components.files.json` lists 349 workspace-relative paths, sizes, modes and hashes. Readable reports, code and small receipts remain ordinary Git files; this archive uses Git LFS.

Run `git lfs pull`, then restore into a new directory:

```bash
python3 ideation/evidence/h200-overnight-001/restore.py --destination /tmp/h200-overnight-evidence
```

The restorer rejects existing destinations, unsafe paths and non-regular members, and verifies every restored byte. It preserves original `AutoResearch-Inference-c03/` paths without overwriting the research or serving worktrees. Model weights, environments and credentials are excluded. A local restore of all 349 files passed before native execution.

`native-infrastructure-001.tar.zst` retains the failed first native allocation, all eight passed A native observation matrices, closed backend logs, exact executed root sources and independent failure review. Its 32 files (10,175,334 source bytes) are covered by `native-infrastructure-001.files.json`; generated Python caches are excluded. A combined restore verified all 381 archived files. The fresh pair002 will receive a separate archive after it closes.

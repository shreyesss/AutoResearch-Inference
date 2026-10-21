# H200 overnight evidence

The [interim report](../../runs/h200-overnight-001/REPORT.md) summarizes completed C24/C25/C26 work. The native campaign is closed with no candidate measurement; all three allocations are retained, together with the completed event-pool engineering check.

`completed-components.tar.zst` preserves all four bounded component/instrument allocations, including the failed checkpoint mount, raw traces, compiled caches, actual image source snapshots and complete historical trace audit. [ARCHIVES.json](ARCHIVES.json) binds archive hashes; `completed-components.files.json` lists 349 workspace-relative paths, sizes, modes and hashes. Readable reports, code and small receipts remain ordinary Git files; this archive uses Git LFS.

Run `git lfs pull`, then restore into a new directory:

```bash
python3 ideation/evidence/h200-overnight-001/restore.py --destination /tmp/h200-overnight-evidence
```

The restorer rejects existing destinations, unsafe paths and non-regular members, and verifies every restored byte. It preserves original `AutoResearch-Inference-c03/` paths without overwriting the research or serving worktrees. Model weights, environments and credentials are excluded. A local restore of all 349 files passed before native execution.

`native-infrastructure-001.tar.zst` retains the failed first native allocation, all eight passed A native observation matrices, closed backend logs, exact executed root sources and independent failure review. Its 32 files (10,175,334 source bytes) are covered by `native-infrastructure-001.files.json`; generated Python caches are excluded. A combined restore verified all 381 archived files. `native-baseline-002.tar.zst` retains all eight valid native A002 observations, ten exact request results, missing-gauge evidence, closed logs, exact root sources and independent failure review. Its41 files (11,088,654 source bytes) are checksummed; all422 files across the three current groups restored successfully. `native-interruption-003-and-event-pool-001.tar.zst` retains B003's interrupted startup and the successful small event-pool preflight, including exact executed root sources. Its 14 files contain 1,164,968 source bytes; the archive SHA256 is `1512a822c29611442fdeafc3648953d24d93c77cd3fe73110e8af7600e59178d`. Readable signal chronology, independent reviews and updated continuation decisions remain in ordinary Git.

A fresh combined restore at `/tmp/h200-overnight-evidence-check-004` verified **436 files across all four groups**. Remote publication verification is recorded separately from local restore.

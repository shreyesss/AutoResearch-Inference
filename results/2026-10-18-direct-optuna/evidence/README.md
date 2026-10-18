# Frozen raw evidence: direct Optuna v1

The completed local study is preserved as [study.tar.gz](study.tar.gz): **786 original files, 411,841,916 uncompressed bytes, 23,297,631 compressed bytes**. [manifest.json](manifest.json) records every member's size and SHA-256 plus the archive hash and phase completion receipts.

Includes exact frozen development/test inputs and warmups, native per-request GuideLLM JSON (including request bodies), Optuna SQLite databases, configuration/source-hash receipts, client commands, server metrics, GPU samples, lifecycle/server/client logs, failed preflights, the explicitly labelled mock client compatibility check, and the search-to-confirmation failure/recovery record. Mock/preflight data remain excluded from measured result tables. No model weights, environment or compile caches are bundled.

Readable copies of phase histories, protocols, resolved configurations, source hashes and frozen finalist selection are alongside the archive. The original [study manifest](../study-manifest.json), [model hashes](../model-manifest.json) and [workload card](../workload-card.json) provide the remaining experiment identity.

## Verify

From the repository root, Python 3.11+; no GPU required:

```bash
python3 infra/direct_optuna/archive.py --verify
```

This checks the archive SHA, all 786 member hashes/sizes, expected membership and path safety. The archive is immutable; the creation command refuses to overwrite it.

## Restore on a checkout without the local artifacts

For restoration, use the following guarded commands instead of merging into an existing study:

```bash
mkdir -p .artifacts
test ! -e .artifacts/optuna-direct-v1 && mkdir .artifacts/optuna-direct-v1 && tar -xzf results/2026-10-18-direct-optuna/evidence/study.tar.gz -C .artifacts/optuna-direct-v1
```

Then regenerate native-derived reports with `infra/direct_optuna/report.py`. Already-committed CSVs suffice for `compare.py` and `final_plots.py` without restoring the archive. Model and source absolute paths inside logs/receipts are historical provenance; restoring data alone does not recreate the GPU serving environment.

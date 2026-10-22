# Round 2 retention importer review

## Prepared and validated

`import_retention_packet.py` defaults to a newly created temporary state. It never calls a provider, model, GPU, serving endpoint or remote publication. `--apply` requires an explicit state directory; canonical path additionally requires `--allow-canonical-import`. `--defer-checkpoint` marks the checkpoint pending via the snapshot helper; it creates no snapshot and never publishes. The old `--local-snapshot` spelling remains a deprecated compatibility alias.

Executed twice against the **same isolated temporary state**: first the default validation, then retry with `--apply --state-dir <temporary-state>`. Both succeeded. Hypothesis IDs remained stable. No canonical writes were executed. Receipts are `isolated-readback-manifest.json` and `isolated-retry-readback.json`.

Validated through actual Store/ResearchFlow contracts:

- 12 embedded source documents retained; 13 claims checked against explicitly pinned source revisions.
- 7 proposal records representing 6 unique directions.
- Original R2-03 rejected decision preserved; revision uses a real parent ID with derived_from/revises edges. Original then receives an appended superseded decision.
- **R2-03 revision is deferred implementation**, with completed scoped CPU dependency audit. No accepted plan is invented; no eval_plan was submitted.
- Latest unique dispositions: **1 rejected, 5 deferred, 0 accepted, 0 service-qualified**.
- 3 retrospective CPU results, scoped separately: missing repeated-sync premise invalidated by source/AST; confidence lifecycle inconclusive for actual runtime removal; synthetic expert-set invariant validated only as set arithmetic.
- Readback checks each status and revision ancestry. Source, report, probe and review artifacts are copied into the destination research record tree; their hashes and archive mappings are in the manifest.
- Existing Gloo predecessor is linked only if it already exists in destination memory. Its absence in the empty validation state is recorded, with no fake placeholder node.

The importer overrides the earlier packet's provisional `accepted CPU diagnostic` label for the R2-03 revision. The packet remains preserved as the received draft; the importer and readback record the final conservative status. This distinction is intentional and should remain visible.

## Root execution command (not executed here)

```sh
/Users/shreyas/workspace/AutoResearch-Inference/.venv/bin/python \
  /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/round2-runtime/import_retention_packet.py \
  --apply \
  --state-dir /Users/shreyas/.local/share/inference-autoresearch \
  --allow-canonical-import \
  --output /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/round2-runtime/canonical-readback-manifest.json
```

The script uses `_locked` and journal start/finish. Root should run after its current publisher/snapshot finishes. Add `--defer-checkpoint` to mark the research state as awaiting a checkpoint. Root must separately create/publish the recovery snapshot. The script does not upload to S3 or commit Git. It is retry-safe for identical inputs; immutable-record conflicts stop rather than overwrite.

## Cumulative yield for these two batches only

Round 1 retained 11 unique directions: 2 accepted bounded CPU diagnostics (S01/M01), 5 deferred, 3 rejected, and 1 duplicate-existing direction. Round 2 contributes 6 unique directions: 0 accepted, 5 deferred, 1 rejected after treating R2-03 and its revision as one direction. Combined: **17 unique directions; 2 accepted diagnostics, 10 deferred, 4 rejected, 1 duplicate-existing; zero service-qualified improvements**. These counts describe reviewed selection, not experimental success, and exclude unrelated earlier repository hypotheses.

Round 2 improved precision by catching a wrong-runner false positive and repairing an overly broad paper rejection. The resulting confidence/cache dependency finding is useful even though it lowers immediate implementation readiness. No simulated work reduction, external paper percentage, or component microseconds have been relabeled as a measured target gain.

## Post-import documentation correction

Root completed the original canonical import before this correction. Its archived importer is the historical executed version; do not overwrite that artifact. The former `--local-snapshot` flag invoked `defer_snapshot=True` and only marked pending, despite misleading help. The revised flag is `--defer-checkpoint`, with the old spelling retained as an alias. This changes naming/help, not the snapshot behavior. Round 1 duplicate-existing is now counted separately from rejected ideas.

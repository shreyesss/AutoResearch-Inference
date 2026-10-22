# Round 2: exact runtime opportunity audit

2026-10-22. CPU-only. **0 new service-qualified hypotheses, 0 GPU calls, 0 serving changes.** Five concrete interventions triaged: two rejected for this target, three deferred. This is a useful negative-yield round: resolving the actual execution path prevented an attractive paper from becoming a false missing-feature claim.

## Discovery path

Two actual `researchctl paper-search` OpenAlex calls, June 1 inclusive to October 23 exclusive, limit12 each, isolated state, `--local-only --defer-snapshot`. Receipts: `search-runtime.json`, `search-metadata.json`. Broad runtime query returned mainly edge/WebGPU/co-serving work. Adapted metadata/synchronization query found Sep30 **Herschel** (2609.40247), then read primary full text and source references. Four read-only canonical PR FTS queries are in `pr-fts.json`; no refresh or canonical writes.

Followed October GraphTok's references to September Hopper utilization study and older Blink/CPU contention studies. Date preference was relaxed explicitly for mechanism dependencies, not represented as October discoveries. Feather was a separate broader-search lead outside preferred date range. Cached primary HTML and SHA256 manifest are in `sources/`.

## The strongest lead was partly already implemented

Herschel §9.2 moves necessary DP execution metadata agreement from Worker toward EngineCore before dispatch. This can remove an exposed target-to-draft interruption in the authors' Qwen hybrid attention stack. The first source search hit the legacy runner's `coordinate_batch_across_dp`, which made this look missing.

**Corrected audit:** exact DSpark speculator inherits DFlash (`gpu/spec_decode/dspark/speculator.py:39`). DFlash builds uniform draft `DPSyncState` from target agreement (`dflash/speculator.py:543–559`). `gpu/dp_utils.py:293–310` validates reuse and returns before a new collective. A CPU AST check confirms the reuse branch calls only `replace` and `torch.full_like`, then returns; it does not execute the fresh-sync function. This is source proof, not a loaded-runtime measurement. V1 configuration explicitly lists DSpark as unsupported (`config/vllm.py:3071–3074`), reinforcing why the legacy file is the wrong basis for this claim.

Consequently **RUNTIME-R2-01 is rejected as existing implementation**. No claim that the pin matches a current live image.

### Residual RUNTIME-R2-02: first target plan before Worker dispatch

One necessary CPU agreement remains in V2 `gpu/model_runner.py:1797`; `gpu/dp_utils.py:42–75` constructs six per-rank fields and calls `cpu_all_reduce_`. Moving that agreement earlier is a separate possible intervention, not removal of repeated draft coordination.

This remains **deferred**. The worker derives semantics from gathered request state, PCP token transforms, LoRA state, encoder inputs, captured graph support and ubatch eligibility. Scheduler token counts are not a sufficient replacement. Moving the same wait to EngineCore is not an improvement unless actual independent work overlaps it. The old H200 recursive-exchange proposal speeds the collective algorithm; this idea moves its dependency timing, so they are distinct but cannot be added arithmetically.

**Fastest CPU falsifier:** derive a field-provenance map showing when each six-field contribution and graph eligibility become known; require an exact immutable execution-plan contract, all-rank epoch/idle/restart/fallback semantics. If a necessary worker-only dependency cannot be known earlier, reject the corresponding hoist. No code patch is justified by current evidence alone.

**Future evaluation:** existing agent-p75 and Mooncake already provide decode and mixed arrivals. Preserve DP4/EP4, weights, graph shapes, actual draft count and all request results. Measure first-target versus draft collective counts, per-rank arrival skew, last-arrival-to-agreement time, dispatch delay, complete round milliseconds/committed tokens, TTFT/ITL tails, and exposed overlap. A shorter collective without shorter critical path fails the hypothesis. No new workload needed unless actual baseline omits a triggering case. No profiling was launched.

**No numerical ROI claim:** Herschel's 2.5–6% results use Qwen/XPU; their statistic is the mean of two maximum observed paired gains at C32/C128, not a generic paired mean, and does not estimate ours.

## Other dispositions

| ID | Intervention | Decision and decisive limitation |
|---|---|---|
| RUNTIME-R2-03 | Remove unused prefill speculation | Reject direct application: paper's Qwen P/D sequential MTP outputs have no downstream consumer; aggregated DSpark proposals do have a verifier consumer. Required prefix state cannot be deleted. |
| RUNTIME-R2-04 | Blink persistent device control + SmartNIC | Defer architecture change: no exact Flash1017/DEP4/Engram integration or hardware path established. Not a small runtime patch. |
| RUNTIME-R2-05 | Feather prefix-homogeneous smaller batches | Defer transfer: dense shared-prefix locality does not establish shared selected compressed-KV entries under CSA2. Withholding ready work can hurt MoE efficiency and tail latency. Eight-prefix agent-p75 is suitable eventually, but no index-overlap evidence exists. |

The September Hopper utilization paper also falsifies an easy but wrong ROI argument: low fragment fill or SM utilization is not recoverable latency. It studied single H100 NVL BF16, not our FP8/MXFP4 distributed path. Retain counter definitions as evaluation guidance; do not manufacture an optimization percentage.

## Tool improvement learned

Presence audits must resolve **model -> selected runner -> inherited proposer -> call-site -> active branch**, not just grep for a suspicious operation. Here legacy-source inspection would have accepted a duplicate. A tool should expose path confidence and unresolved runtime binding alongside matches. `researchctl source-audit --help` is not a valid CLI command in this checkout; that error is retained in the ledger. No tool implementation was changed in this worker.

Artifacts: `candidates.json` has full grounding, counterevidence, prior comparison, pin checks, CPU falsifier and future eval per intervention. `pinned-source-manifest.json` hashes inspected files. `tool-use-ledger.json` records declared decision actions (not every shell command). `cpu-ast-audit.json` is structural inspection, not an executed vLLM test. Isolated cache is not a new S3 recovery snapshot; root owns canonical import/publication.

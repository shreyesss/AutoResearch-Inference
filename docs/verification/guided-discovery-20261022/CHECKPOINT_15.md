# Checkpoint15 — selective transfer and honest full-text coverage

The guided discovery loop remains active. No GPU/device query, native tensor execution, serving change or training. **No measured inference improvement.**

## Science outcomes

| Screen | Evidence and actual conclusion | Disposition |
|---|---|---|
| [43: expert activation/weight sparsity](round43/REPORT.md) | Three full papers and actual MegaMoE source show element sparsity does not establish whole-tile work removal. Literal MMA-only skipping retains producer traffic and can mishandle accumulated state. Existing quantized zero tiles remain a separate component worth a bounded census. | Three intervention screens; no new qualified card. Direct ports rejected as scoped; exact-zero component deferred. [Independent review](round43/INDEPENDENT_REVIEW.md). |
| [44: KV memory placement](round44/REPORT.md) | BOOST's head-placement policy does not directly preserve its split with the target's single stored KV head and sparse gathers. Exact allocator reserves backing storage at startup, so per-request allocation-removal ROI is unsupported. Fresh PR60843 diff differs materially from its old opening description. | Zero new card; unsupported transfer parked. [Independent review](round44/INDEPENDENT_REVIEW.md). |
| [45: separate quantized DSpark output head](round45/REPORT.md) | An existing EAGLE/MTP derived-head helper is present; DSpark loader/config do not use it. HyCo's W8 post-training diagnostic can be separated from its W4 training treatment. SpecEdge's quantized-target/sequential-draft gains cannot be borrowed. Seven source checks and a two-token rational negative control ran. | QH45 is **provisional deferred**, independent review pending; no canonical card or execution qualification yet. |

QH45's core economic test is whether reduced complete-round time exceeds lost committed progress and memory-pressure cost. The target head stays resident; an extra draft copy costs capacity. Proposal sampling and rejection must use the same changed q. The small rational control exposes a stale-q error but does not validate the native block verifier. Existing Mooncake/agent75 workloads remain the eventual service tests; additional head/probability diagnostics answer questions they cannot resolve alone.

### Yield, without acceptance inflation

The canonical guided-card set through WP38 is **38 cards:2 accepted bounded CPU investigations,28 deferred,7 rejected,1 duplicate**. Acceptance means permission for the named CPU diagnostic, not a validated implementation or service gain. Rounds39–44 do not add cards for repeated families or parked components. Round45 is tracked separately until review. Canonical inventory across all historical campaigns is142 hypotheses,2392nodes,2971edges,902events and62 scoped tests at this checkpoint. Counts include historical/failed/inconclusive work, not successful performance experiments.

The discovery loop is narrowing plausible changes through source conflicts, not maximizing accepted-card count. PJ01, WP38, OP36 and graph-size applicability remain the previously documented investigation priorities; QH45 is not ranked above them by an invented gain estimate.

## Tool improvement driven by a real failed read

[Implementation report](oa-fulltext/REPORT.md), [independent review](oa-fulltext/INDEPENDENT_REVIEW.md), [validation](oa-fulltext/validation.json).

`investigate` now reads explicit open-access PDF locations from retained paper metadata through the existing cache and HTTP budget. Every selected paper has completed/skipped/failed full-text coverage. `dossier_ready` may still rely on abstracts and says so. DOI-only records are not silently treated as full-text reads, and the tool does not invent a PDF URL.

Review fixed two concrete defects: blank PDF page labels could satisfy the text threshold, and an unrelated URL containing an arXiv-looking path could acquire a false arXiv identity/immutable TTL. An observed Zenodo PDF used `application/octet-stream`; valid signature, actual parsing and extraction now handle that case while retaining the original MIME. The real DOI-only SpecEdge record still correctly skips automatic full text; its manual explicit-file retrieval is separately documented.

**Verification:** full research suite333tests+29subtests; focused46+5; independent34+5; diff check and bootstrap dry-run pass. Remote transport is mocked in regression tests; parser/cache/CLI/MCP execute. A separately retained real PDF replay succeeds without new network requests. This is a coverage/correctness improvement, not a measured increase in hypothesis quality.

## Memory, storage and operational boundary

Canonical imports now completed: WP38 (99artifacts,6claims,new deferred card); round39v5 (72artifacts,zero new card); rounds40/42v3 (49artifacts,zero new card). Original baselines/statuses remain intact. The older round39 operational-receipt history limitation documented in checkpoint14 remains; it is not retroactively repaired.

Round41 and rounds43/44 have independently validated production export/restore packets. Their155 artifact staging is queued under the canonical writer lock at checkpoint creation; corpus/import/artifact-index steps are **not yet claimed complete**. They retain searchable source/review evidence without invented typed hypothesis transitions.

Latest publisher lineage receipt is `f3e4ec86d7687d07d5498dec0555a03e79853da736edfafbee2369be9967e3a1`, published2026-10-22T04:20:16Z. This is a local successful publisher receipt, not a fresh remote GET/VM restore. Later canonical imports are pending checkpoint and cannot be claimed covered by this snapshot. GitHub backfill is still running; the last inspected batch completed at04:25:19Z. No completion ETA is inferred from download-only timing.

[Publication-lock audit](publication-lock/DESIGN.md) explains a real bottleneck: current publishing holds the global writer lock through serial network checks. For the observed snapshot the common-path model has2,310 HEAD calls,2 GETs and up to620 PUTs; these are source-derived logical counts, not a captured request trace. A two-phase publication design preserves remote checks/lineage while releasing the research writer during upload. **Design only; no live process change or implementation.**

## Next active work

Independent QH45 review; separate small-router and KV/indexer paper lanes; complete the queued canonical retention; retain every rejection and correction. No GPU escalation is authorized by this checkpoint.

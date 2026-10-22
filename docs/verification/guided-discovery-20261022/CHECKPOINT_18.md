# Checkpoint18 — adversarial discovery and live research-memory repair

## Result

The loop continues without GPU execution. Recent papers are being decomposed into transferable components, then checked against exact source paths and earlier work. None of the newly reviewed leads below is implementation-qualified or a measured inference gain.

| Pass | Actual finding | Disposition |
|---|---|---|
|51, projected Engram reuse|A new paper led back to an exact older WKV cache proposal. Its50KiB-per-entry arithmetic and missing trace were already known.|Zero new interventions. Preserve additional evidence and the explicit duplicate correction.|
|52, communication|Repeated expert input pulls exist, but a close H200 donor found negligible layer benefit. Early ready-source expert execution has a real scheduling dependency to replace.|Two deferred components. Dedup needs exposed-time evidence; ready-source execution is primarily a prefill/TTFT architecture lane.|
|53, compiler/runtime reuse|The paper's validity-pointer idea does not establish a missing full-history KV-copy operation in our V2 DSpark path.|Reject that direct-transfer premise; no new card. Independent review follows the actual V2 model-state hook.|
|Trace applicability|Existing output-token traces are artificially constrained, from an older runtime; their matching tokenizer hash does not make the workload representative.|Do not infer natural vocabulary locality or Engram tuple reuse from them. Scope is bounded local evidence, not all remote archives.|

FI6360 BF16 tuning has a separate frozen author audit under round54-bf16-tuning; its independent review is still in progress at this checkpoint. Default pinned CUDA auto uses F.linear. Explicit FI activation and tactic-ranking policy require separate controls. No target speedup is inferred from the donor's B300/GB300 results.

## Research tooling changed and verified

`Store(readonly=True)` now uses WAL-aware SQLite mode=ro. Explicit immutable reads remain for sealed replicas. A real open-writer regression failed before the fix and passed afterward. The two actual replica CLI callers were independently checked with a sealed backup, preserving replica files. Readonly access can still use SQLite shared-memory/locking bookkeeping.

The discovery skill now requires recall of prior reports as well as typed cards. When a known report is absent, check ingestion before changing ranking; use bounded campaign-directory lookup, import with provenance, then replay the same query. Novelty remains optional. This is a targeted repair demonstrated on a missed predecessor, not a validated universal increase in hypothesis quality.

Verification:361 research tests and29 subtests passed; bootstrap dry-run passed. Independent review reran the three readonly tests and exercised real replica search/status callers. Skill validation passed using temporary validator dependencies outside the project. Root verified158 listed source/review packet files and31 exact small delivery copies. No serving/native/model validation was run.

## Yield and priority

At the retained readback, canonical memory contained143 hypothesis records. The explicitly defined guided subset (run identifier contains guided) held40 records:29 deferred,8 rejected,2 accepted,1 superseded. This includes revisions and superseded identities, so it is not40 independent mechanisms. Standalone screened leads are not silently added to that denominator.

The two accepted historical records are bounded CPU diagnostics, not implementation promotions. Their [current priority re-audit](ACCEPTED_DIAGNOSTICS_REAUDIT.md) parks them pending representative evidence. New reviewed passes here add zero accepted implementations and zero measured service results. A fresh paper or new name does not count as a new mechanism.

## Durability and active work

Small reports, corrections and code are delivered in Git. The canonical source-only repair of two omitted predecessor reports is queued behind the existing publisher writer; isolated import/retry/restore checks passed. The separate50/51/53 retention package is prepared and validated but not yet reported as canonical completion. No new S3 coverage is claimed by this checkpoint. Publishing a Git report is not evidence that its full raw source packet reached S3.

The next paper-led exploration is running in a distinct execution-overlap/serving direction. Independent review of54 and canonical retention continue. The source baseline is a pinned plan, not a fresh live deployment attestation. No GPU experiments, model launches, serving changes or training are authorized by this work.

## Read the evidence

- [Round51 correction](round51/CORRECTION_AFTER_REVIEW.md), [WAL-aware diagnosis](round51/RETRIEVAL_RESOLUTION.md), [independent review](round51/INDEPENDENT_REVIEW.md).
- [Round52 mechanisms and controls](round52/REPORT.md), [independent review including threshold/multi-stream separation](round52/INDEPENDENT_REVIEW.md).
- [Round53 screen](round53/REPORT.md), [actual V2 source review](round53/INDEPENDENT_REVIEW.md).
- [Trace applicability](trace-applicability-5351/REPORT.md).
- [Readonly fix](live-readonly/REPORT.md), [independent verification](live-readonly/INDEPENDENT_REVIEW.md).
- [Defined yield readback](yield-readback-18.json), [copy manifest](source-copy-manifest-18.json), [packet verification](source-verification-18.json).

# Checkpoint 40 — conditional replica selection and a cache-allocation falsifier

22 October 2026. CPU research only. No model execution, GPU work, native correctness qualification or measured serving improvement.

## What the adversarial checks changed

| Investigation | Useful result | Disposition and next discriminator |
|---|---|---|
| [113: resident expert replica selection](round113/REPORT.md) | TEMPO's nonuniform invocation shares are absent from the pinned hash/modulo selector. Fused mapping/counting already exists. Concentrating cold experts can change per-copy work; donor DeepSeek-v3 results were negative/no-op-equivalent. | Parked component, no new formal card. First inspect effective physical maps and loaded duplicate weights. One copy gives no selector choice; adding copies is a separate memory/placement experiment. |
| [114: SP109 physical cache planning](round114/REPORT.md) | Prospective mixed SWA widths break grouping/partition in declared scalar scenarios. Preserving baseline groups passes partition checks but saves zero common-stride bytes in three controls. | SP109 remains deferred. Design a complete mixed-width partition and cost it before claiming capacity gains. Logical read-byte reduction remains a separate, unmeasured rationale. |

Independent reviews: [113](round113/INDEPENDENT_REVIEW.md), [114](round114/INDEPENDENT_REVIEW.md).

113's first gate is actual installed replicas, not the EPLB flag alone. The donor's uniform fallback and rebalance hook are useful details, but do not prove compatibility with this target's map/weight generation. Mathematical equality of logical expert choices is not a native bitwise guarantee after regrouping; declare the numerical contract.

114 executes six unchanged planner functions and eight metadata methods on scalar facades. Fifteen source files were checked against the pinned archive. The final inventory includes 54 managed specs, including three compressor rings; the superseded 51-spec draft is preserved. Twelve metadata scenarios and three manual partition controls are **not** runtime allocation tests. Its MXFP4 index-cache width is an explicit scenario assumption: pinned `indexer.py` resolves `auto` to **FP8**, and actual runtime settings remain unknown. B256 is conditional sensitivity, not an attested deployment configuration or measured waste.

## Yield and adaptive research

113: one dated online query, 12 returned papers screened at metadata/abstract level, one selected full text, four bounded PR searches, two PR bodies and six target/dependency source files. It retained one conditional component, zero formal hypotheses and zero measured wins. Reopening a previously seen abstract for full-text component extraction improved the decision detail; it is not a new independent paper discovery.

114: no new paper search; one existing hypothesis received a concrete allocator admission check. Failure and null results are retained rather than converted into an optimistic capacity estimate. The next ongoing branches concern sparse indexer scoring and Engram lookup; their unreviewed findings are not promoted here.

## Tool improvement and verification

The [initialization guidance](init-guidance/REPORT.md) addresses repeated operator errors: initialize a fresh isolated workspace without `--defer-snapshot`, check success, then apply batch flags. Restore-existing-state semantics remain explicit. An uninitialized-state error is not a failed provider search. No research Python implementation changed.

Verification subsequently completed: **408 tests and 29 subtests passed**, bootstrap dry-run passed, skill validator passed using the existing isolated PyYAML dependency, and whitespace checks passed. Actual isolated initialization plus deferred expansion completed without network access. The earlier frozen guidance report predates the full-suite run; [its verification addendum](init-guidance/VERIFICATION_ADDENDUM.md) records that chronology. These checks do not prove a behavioral search-quality or hypothesis-yield improvement.

## State delivery

[Combined 109–112 retention review](retention-40/109112_REVIEW.md) independently verified a fresh local restore, 228 artifact references, 102 exact source revisions, 29 quotations and the original SP109 deferred dossier. Its [count correction](retention-40/109112_COUNT_ADDENDUM.md) distinguishes 48 provenance rows from 24 unique query/paper pairs. Round112's first search successfully returned zero results; it was not a provider failure.

The approved canonical successor sequence remains serialized behind the existing controller. V4/V5 were prepared and approved; they were not yet launched at this checkpoint. Local restore proof and Git delivery do not certify a new S3 publication. No competing publisher was started. [Copy manifest](source-copy-manifest-40.json) records exact selected delivery files and frozen source packets.

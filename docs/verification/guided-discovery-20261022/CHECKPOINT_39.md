# Checkpoint39 — one new deferred precision direction and a concrete FV86 adapter

## What the loop produced

| Work | Result | Remaining decision |
|---|---|---|
| Recent MultiAlloc paper → target SWA precision | One distinct, independently reviewed **deferred** proposal | Physical layout, quality budget, codec/reader cost and actual service gain |
| FV86 full-pass residual shortcut | Existing-launch, existing-buffer interface with source ownership/fallback audit | Compiled predicate parity, native correctness and exposed time |
| Recovered historical timings | Eight native receipts verified; C025 timing units clarified | They do not supply current FV86/PJ01 exposure |
| TokenRouter re-reading | Scheduling component separated from cross-model semantics; zero new cards | Direct peer-return premise absent; generic admission remainder belongs to existing policy work |

No GPU/model/native execution or serving modification occurred. No implementation or service win has been qualified. “Deferred” preserves an investigable mechanism; it does not mean expected positive ROI.

## 1. New direction: selective target SWA precision

[Round109](round109/REPORT.md) and its [independent review](round109/INDEPENDENT_REVIEW.md) identify a real distinction: the inspected Mega path already supports compressed KV at288 bytes, while its sliding-window attention cache remains528 bytes. A static layer policy could put selected **target SWA** records in a new288-byte representation while retaining the existing compressed-cache policy.

The paper contributes offline budgeted precision selection. Its gradient calibration does not update weights, but still executes the model forward/backward and is outside the current task. A forward-only ablation is a different method; omitting token-level allocation also prevents inheriting the paper's joint results.

This is a coordinated extension, not a flag change. The SWA writer, original-cache FlashMLA specialization, scale/layout metadata and allocation identity must agree. The current API rejects original-cache FP4. The existing288-byte prefill gather can be reused, but chooses Triton where the FP8 path may use CuteDSL. Reduced storage can increase conversion or gather time.

The conditional128-SWA/512-compressed example saves1/7 of logical record payload. It does not measure HBM transactions, allocated capacity, bandwidth pressure or ITL. A retained older SGLang/H20 experiment reports more capacity with lower decode throughput; that is counterevidence to automatic speed claims, not a target result.

This intentionally changes target arithmetic. Structural correctness relative to the new representation and task quality relative to the original model are separate gates. There is no universal bitwise-output veto, and no invented acceptable degradation threshold. Shared K/V sensitivity, task-disjoint calibration, downstream routes/confidence/acceptance and actual generated outputs matter. Keeping another policy or weight fixed does not freeze its downstream values.

The [actual isolated typed workflow](round109/TYPED_WORKFLOW.md), independently [reviewed](round109/TYPED_INDEPENDENT_REVIEW.md), records SP109 as `hypothesis:e86671eb6fd6ca5a83ea84b5580f95c11f361174cc68d069676c264268bb9a54`:11 claims, a no-GPU screen, retrospective diagnostic plan and deferred decision. ROI stays null. `ready_for_review` is not scientific validation or execution authorization. Canonical import remains separately queued.

The next CPU/source task is the physical cache-spec plan. If padding removes capacity savings, that removes the capacity rationale for that configuration; it does not by itself resolve the separate traffic hypothesis. More byte-count examples cannot establish quality or performance.

## 2. FV86 now has a concrete integration contract

[Round110](round110/REPORT.md), its [patch contract](round110/PATCH_CONTRACT.md) and [independent review](round110/INDEPENDENT_REVIEW.md) resolve the flag-ownership question.

For each current request interval, the first row of the existing residual-mass buffer is unused by its native mass writer and reader. The proposed adapter stores a Boolean there, moves the same allocation before the cumulative-ratio launch, and resets every actual request's flag before any greedy early return. AV uses final device boundaries; chunked calls rebase starts consistently. This avoids a new persistent request flag, mapping array or extra kernel launch in the inspected scope.

A true flag must use the exact native terminal predicate: stored FP32 ratio, exponentiation, indexed seed/position and inclusive comparator. The rejection branch writes accepted draft IDs/counts and retains common logsumexp/bonus handling. False flags preserve the old path. Earlier residual work can then be skipped without its stale output being consumed.

Source ownership is not compiled equivalence. The additional scalar work and flag reads can cost time; failed terminal tests repeat a scalar calculation. Allocation lifetime/capture, generated arithmetic/RNG, poisoned skipped storage and all fallback paths remain native gates. Stop further symbolic proof expansion until those gates can be tested under separate authorization.

## 3. Historical timing evidence has a precise limit

[Round111](round111/REPORT.md), its [required correction](round111/CORRECTIONS.md) and [independent review](round111/INDEPENDENT_REVIEW.md) found eight recovered A002 native receipts:960 dummy samples each. These are repeated controlled cycles, not7,680 independent serving trials.

They explicitly exclude rejection, accepted-token progress, production context, queueing and ITL. They also belong to an older H200/model/image identity. C025 separately measures a complete five-step draft Markov sampling call for the entire batch. Its historical45–83µs small-shape savings cannot be multiplied by five again, interpreted per token, or used as FV86 residual exposure.

The correction matters: PJ01 removes unused Q output columns in a context-only **draft** projection. Retained KV normalization/cache work stays. Whole historical target-forward or draft-proposal spans do not isolate that operation. Current attributable bounds remain unknown.

## 4. A useful re-opening need not create another hypothesis

[Round112](round112/REPORT.md) and its [independent review](round112/INDEPENDENT_REVIEW.md) revisit TokenRouter, previously rejected at abstract level because it routes among different models. Fulltext reading shows that its delayed-batching policy can be considered separately from its token-choice semantics.

The direct benefit still needs irregular peer returns. Ordinary native RUNNING requests keep state across decode steps; they do not re-enter the frontend and redo initial prefix matching each token. The pinned fork also already has cadence controls with a capacity escape. Its upstream revert concerned a plugin interface; that does not erase code present in this exact fork.

PR evidence adds concrete liveness and saturation cautions. A policy may improve aggregate batching while worsening TTFT or starving admission. Generic admission changes therefore belong with existing R7b/H01/R4 comparators, whose exact identities are retained in the review. The standard workloads remain service comparators; attribution counters would be added only when execution is authorized. No new workload or synthetic case sweep is required now.

## Yield, prioritization and durability

Across109 and112: three dated online queries,24 returned abstract references, two selected fulltexts and nine selected PR bodies; no PR diffs were read. One new deferred hypothesis in isolated production memory, one existing FV86 adapter refinement, one historical evidence audit and one zero-card component screen. These counts do not measure literature recall or service-qualified yield, which remains zero.

The [independent priority audit](priority/AFTER_ROUND106.md) keeps FV86/PJ01 as bounded work-removal investigations without pretending to rank expected gain. AV68 is a smaller conditional metadata change. SL97 remains a local layout experiment with an uncertain performance premise; SN98 is a larger algorithmic path. The new SWA representation direction is useful to retain, but has more integration and quality uncertainty than those narrow source changes.

Research continues with a distinct expert-placement literature branch and the SWA physical-spec question. Original artifacts, negative findings and corrections are preserved. Git delivery is separate from canonical import and S3 publication. The older v2 canonical sequence completed and its FV86 readback was verified; approved v3 then started sequentially. This checkpoint does not claim every later packet is already canonical or remotely published.

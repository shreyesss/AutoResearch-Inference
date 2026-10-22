# DSpark budget discovery preflight — no new hypothesis

## Decision

Close before a new provider query. The requested component family is already represented in prior memory, including explicit load-dependent chain/K=0 support, calibrated verification cost, post-DP target/draft graph pricing, and TreeSpark transfer. This is a current source-presence check, not a new direction or acceptance. No round28 candidate is created and no prior decision is changed.

## Recall

Read complete compact inventory of 136 canonical hypothesis nodes, then exact relevant card fields. An initial verbose 136-record output exceeded the tool budget; it was replaced with a complete bounded compact listing, not silently treated as complete. Relevant full payloads/events retained in related-priors.json:

- e5416985…9676556fa6: conditional existing adaptive-verification activation.
- 35689a13…c646608933: scheduler-reachable mixed-prefill cost calibration.
- 2366143a…1938f5a199: C24 coupled post-DP target AND draft graph pricing; draft cost already included, request-count-only indexing is insufficient in some proposed cases. Prior instrumentation remains inconclusive.
- 766121e3…9ad3194bfc: load-dependent TreeSpark transfer, explicitly dependent on a new compatible tree verifier.
- 7a7523f7…30dcb2830c: inference-only chain/load budget and K=0 state synchronization; explicitly refuses an unsupported skip flag.

## Exact existing controls at c455786

| Source | Observed behavior | Consequence |
| --- | --- | --- |
| config/speculative.py 555 | enable_adaptive_verification exists for DSpark | Adaptive verification is an existing feature; active deployment status still needs attestation. |
| adaptive_verification.py 285–353 | CPU budget maximizes estimated committed progress divided by draft cost plus verification cost. Confidence survival products rank slots. | Generic acceptance-aware, load-priced verification already exists. Merely adding drafting cost is not a missing mechanism. |
| adaptive_verification.py 80–128, 189–254 | Cost curves account for captured-size plateaus; beyond-limit interpolation, startup profiling and separate graph-only draft samples exist. | Generic graph-aware cost is present. Specific joint-DP/mixed/context calibration remains the existing C24 family. |
| adaptive_verification.py 256–280, 410–445 | CPU selection uses buffered stale confidence; current GPU confidence reallocates a fixed admitted budget and updates query/logit offsets. | Any policy change must preserve current/device versus stale/host contracts; no free extra synchronous confidence read. |
| dspark/speculator.py 46–55, 106–112 | Native draft query width remains configured k (5 in target plan); trained confidence head selected when enabled/present. | Verification budget is not equivalent to reducing drafter block width or skipping drafter execution. |
| config/vllm.py 1084–1101 | Batch-size dynamic speculative-token schedule is disabled for DP>1 to avoid rank divergence/deadlocks. | Blind per-rank load-dependent k is not an eligible configuration in planned DEP4. |
| model_runner.py 2252–2288; dflash/speculator.py 435–468 | Speculator is called whenever configured; DFlash-derived native DSpark constructs query span from request count times native query width. | A zero verified-draft budget does not itself prove zero draft cost. The missing skip/resume state work was already explicitly retained. |
| rejection_sampler_utils.py 442–458 | Existing probabilistic block residual computation recognizes trimmed adaptive endpoints and placeholders. | Keep existing sampler/rollback contract. A tree or greedy-only donor cannot be substituted for temp1 block verification. Source support is not proof of distributional correctness for a modified policy. |

## Scoped future work

The useful next action in this family is the existing C24 diagnostic: reconstruct legal joint-rank budget states, resolve actual target/draft graph descriptors, and compare decisions under the same confidence evidence. No GPU measurements are available here, and the prior CPU synthetic decision sensitivity is not an observed service win. Existing Mooncake/agent-p75 evaluators are potentially appropriate after manifest/semantic qualification; no new evaluator is justified by this preflight.

This audit does not assert that all possible scheduling ideas are exhausted. A new paper is warranted only when it supplies a distinct missing component, such as a proven context-preserving skip/resume implementation under this exact DP and sampling contract. General dynamic-k, tree-budget and calibration queries would currently rediscover known cards. No new online search, GPU import, native model execution, source patch or canonical write was performed.

## Retrieval limitations

One convenience grep targeted an absent historical benchmark path and returned exit2; no benchmark interpretation was based on it. Planned temp1/top_p1 and DSpark5 context comes from the already-retained baseline, not a new node inspection. Initial broad source grep was truncated; focused exact files and ranges above were subsequently read and retained. Source pin establishes repository behavior, not the state of a currently running server.

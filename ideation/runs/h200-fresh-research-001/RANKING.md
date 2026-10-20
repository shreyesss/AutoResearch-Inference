# H200 research priority

This orders **conditional investigation**, not approved deployment or predicted speedup. No candidate has completed the required GPU correctness and activation checks. The frozen rubric remains unchanged; model deferrals are preserved. Start with the applicable G01–G05 and DeepGEMM correctness checks, then inspect H01–H03 eligibility.

| Rank | Mechanism | First decision | Model selection / score |
|---|---|---|---|
| 1 | [Humming backend and indexed/grouped comparison](experiments/H01.md) | Resolve actual W1/W2 schemas, GEMM type, EP4 AG/RS compatibility, target/drafter backend and graph coverage. Use shipped flags first; adapt only the missing behavior. | deferred / 76.0 |
| 2 | [Share compatible FlashMLA plans](experiments/H02.md) | Identify active metadata builder and group compatibility, all live fields and graph lifetime. Source application is not execution proof. | deferred / 76.0 |
| 3 | [SM90 small-row mHC launch tuning](experiments/H03.md) | Confirm hc_mult4, H5120, executed delayed kernel and actual padded row histogram. Check the executed TF32 prenorm implementation first. | deferred / 82.0 |
| 4 | [Use real request counts for draft sizing](experiments/H04.md) | Follow DSpark inheritance into the installed helper and compare logical, target-padded and draft-padded counts. Adapt exact final patch behavior; do not blindly cherry-pick. | deferred / 76.0 |
| 5 | [Small CPU DP reductions](experiments/H05.md) | Attest process-group backend, group-local ranks, tensor shape and invocation ordering; inspect fixed tags and fallback before adaptation. | deferred / 76.0 |
| 6 | [Candidate gather versus direct paged indexer scoring](experiments/H06.md) | Match FP8 cache layout, compressed row IDs, candidate selection semantics and dependencies to this model; preserve dense selection semantics before claiming a lossless port. | deferred / 72.0 |
| 7 | [Native DeepSelect SM90 integration](experiments/H07.md) | Pin/build native dependency, match FP32 logits, strides and row bounds, verify installed dispatcher and full-head kernel eligibility. | deferred / 74.0 |
| 8 | [Contiguous prefill MQA epilogue](experiments/H08.md) | Resolve include and JIT artifact, actual FP8/BF16 logit API and shape bands; source presence alone does not prove active dispatch. Preserve the saved CPU overflow counterexample. | deferred / 78.0 |
| 9 | [Shared prefix affinity at final DP rank](experiments/H09.md) | Inspect existing router and rank-selection behavior, prefix key/salt semantics and shared-state lifetime before implementation. | deferred / 76.0 |
| 10 | [Bounded coordinated prefill release](experiments/H10.md) | Inspect installed scheduler compatibility and exposed mixed-step interference; a per-step wall-clock check does not guarantee a hard waiting-time bound. | deferred / 72.0 |
| 11 | [Humming per-token FP8 activation arm](experiments/H11.md) | Require H01-compatible backend first; resolve named-format plumbing, W1/W2 scales, target/drafter inheritance and fallback. | deferred / 76.0 |
| 12 | [Native-MXFP4 SM90 MegaMoE adapter](experiments/H12.md) | Check E384/H5120/I2304/top6,96 local experts, clamp10, weight byte order, scale ranges, group semantics and installed FlashInfer0.7.0 API. Alignment alone is insufficient. | deferred / 63.0 |
| 13 | [Fuse top-k with physical KV mapping](experiments/H13.md) | Trace all consumers, native SM90 build, block64 mapping and raw-index requirements; inspect newest DeepSelect before custom work. | deferred / 76.0 |
| 14 | [DeepEP activation then triple-buffer dispatch](experiments/H14.md) | Pin adapter/API version, direct-NVLink eligibility, payload/scales, rank topology, shared-memory limit and workspace. Account for newer elastic API migration rather than mixing revisions. | deferred / 74.0 |
| 15 | [Opt-in mHC coefficient-stream overlap](experiments/H15.md) | Resolve executed JIT artifact and exact dependency schedule; qualify #448/#59129 if the affected path executes. Do not conflate TF32 overlap with compensated-BF16 math. | deferred / 67.0 |
| 16 | [Matched SGLang control and isolated group32 tuning](experiments/H16.md) | Match model/tokenizer revision, TP1/DP4/EP4, host Engram, FP8 KV, graph settings and real DSpark rejection semantics. Report any irreducible mismatch. | deferred / 68.0 |
| 17 | [Private-shard Engram allocation — inactive](experiments/H17.md) | Resolved dp_shared_memory=True is already established. Shared cuMem would require an independent FABRIC/export/NUMA capability probe and a new scoped card. | rejected / 37.0 |

## What is outside the first execution block

H09–H16 retain useful designs but require routing, precision, native integration or engine-parity work. H17 is excluded on the pinned shared-memory baseline. Compensated-BF16 mHC, MISA head pruning, DeepJIT cold-start changes, sequence-parallel TP paths and small-head attention are not silently folded into the top eight. Their scope and counterevidence are in the repository/literature reviews.

[Source research report](REPORT.md) · [Model decisions](MODEL_REVIEW.md) · [Evaluation contract](EVALUATION_PROTOCOL.md)

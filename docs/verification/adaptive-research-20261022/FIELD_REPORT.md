# Adaptive discovery field test: one narrowed Engram hypothesis

**Result: retain one source-grounded hypothesis for a bounded compatibility follow-up. No measured improvement, target ROI estimate, implementation or GPU experiment.** GPUs are occupied by another test. This run did not query GPU availability, profile, benchmark, launch a model, change a container or alter serving code. Remote operations read committed source and benchmark scripts only; all probes ran on the workstation CPU.

## A01 — Move the remaining Engram WKV projection ahead of its gate

The useful question is narrower than “enable Engram prefetch.” vLLM already prefetches embedding rows and has a packed DP exchange path. The remaining operation in inspected commit `c4557869393db4d75c483d92edd02a5125500883` is the WKV projection inside `Engram.forward`. Its direct input is the token-ID-derived prepared embedding; the evolving hidden state is consumed later by the gate.

**Hypothesis:** stage one eligible Engram layer's WKV projection during preceding attention work, retaining the existing lookup/transport and leaving the hidden-state gate at its original location. This may hide some exposed projection latency on long-output requests. Preserve frozen model weights, output semantics and current DSpark settings; this intervention does not change the speculative algorithm.

This is a possible cross-engine port, not a claim of novelty. It differs from prior E10 table allocation/packing and E15 gate/mHC fusion. Its scientific value is that a specific residual operation has been identified after subtracting work already optimized.

### Grounding and counterevidence

1. [Original Engram paper](https://arxiv.org/abs/2601.07372) separates static memory retrieval from dynamic hidden-state fusion. Its full text was retrieved; the HTML identifies v2. The retained text hash, rather than an unversioned URL alone, fixes what was read. This architectural fact motivates inspection; it does not prove V4.1 runtime compatibility.
2. [vLLM #59923](https://github.com/vllm-project/vllm/pull/59923), head `4f6745cd95e710360392079c0e997a0cf7ba38b7`, already packs/exchanges DP rows and prepares MXFP8 inputs. It explicitly leaves WKV in the layer forward. Its microbenchmark stops at WKV input, so that table supplies neither the cost of WKV nor the budget we can save.
3. Actual committed [Engram source](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/common/engram.py) has WKV calls at lines 1689 and 1691. `EngramBatch.prepare_embeddings` stages rows; `_start_prefetch` fetches rows; neither executes WKV. The gate follows those projections. The source audit retains exact bytes and hashes.
4. [SGLang #44028](https://github.com/sgl-project/sglang/pull/44028), inspected head `8a4d7060ae3420942087ba054013d6c15fda63e5`, supplies a concrete reference for moving lookup, exchange and projection earlier, including stream/graph tests. Its implementation needs a fence before MegaMoE and restricts backend/parallelism/mode combinations. It is open code, not proof of a working vLLM port.

**Strong counterevidence:** #59923 reports that Engram occupies under 1% of TPOT in its fixed-output-token, cache-resident decode scenario. The paper/PR's reported accounting does not isolate the WKV interval sufficiently to forecast our gain. Conversely #44028's reported 1 ms per forward / 4–8% TPOT gain is from a different SGLang disaggregated DEP4 setup with a long shared prompt and concurrency 96. Neither number transfers to aggregated original-Flash DP8, its B200 host topology, variable token IDs, graph choices or output-progress denominator. They are conditional observations, not two measurements of the same experiment.

### What the CPU check established

`cpu_source_audit.py` parses the retained **actual source**, finds both WKV calls, verifies their direct AST names are only `self` and `hash_ids`, and checks that existing batch/prefetch methods do not already execute WKV. It also verifies the hashes and analyzes the requested-length metadata in all three standard Mooncake traces. The script imports no GPU library.

This establishes a syntactic dependency boundary and retained workload exposure. It does **not** establish purity of custom GEMM implementations, workspace lifetime, CUDA stream safety, collective ordering, numerical equivalence, cache behavior or material latency savings.

### Applicability and implementation constraints

The installed original-Flash profile specifies model revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, image `sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`, TP1/DP8/EP, MegaMoE, CPU Engram offload and embedding across DP. **The inspected research-fork commit is not linked to that image.** Its dirty working files were not used: `git show <commit>:<path>` read only the committed objects. No claim is made about the currently running test's configuration.

Before a patch is justified:

- Resolve intended image/source membership; reject a direct port if equivalent WKV hoisting already exists.
- Resolve actual shared-table versus private-shard branch and WKV kernel. Retain its existing quantized layout; do not combine table-allocator changes with this intervention.
- Admit only side-stream-safe projection backends. Shared workspace mutation or lazy initialization can make an algebraically valid reorder unsafe.
- Use forward-local prepared buffers, a per-layer completion event and a join before its gate. Preserve liveness over graph replay and request/batch changes.
- Fence on the **actual MegaMoE launch stream** before its resident grid; joining only the caller stream is insufficient.
- Stage the next projection just before a legal attention interval. Launching all future projections upfront can force the first MoE fence to wait for all of them, erasing overlap or creating ordering hazards.
- Keep globally consistent mode/dispatch and idle-rank participation. Existing main-stream transport remains the initial control; moving collectives is an additional integration question.

## ROI: conditional accounting, not a golden score

For unchanged useful output progress, an optimistic per-step bound is:

`saved_time <= sum(min(exposed_WKV_time, legal_overlap_window)) - added_overhead - interference`

Real saving may be negative. Both layers' savings are not automatically additive if their work overlaps or competes. Divide actual critical-path savings by **committed useful output tokens** for amortized token time. Do not divide by configured K=5, and do not infer tail ITL, TTFT, goodput or dollars from this expression.

**All target timing inputs are unknown.** The typed screen therefore retains insufficient evidence and null target gain. The CPU plan is structurally `ready_for_review`; that status certifies neither scientific merit nor execution permission. The hypothesis remains deferred for serving implementation/qualification.

## Existing evaluator exposure, now checked against real trace files

All three JSONL files were fetched read-only from `s3://bitlane-641134885443/bench/traces/deepseek-serve/` and matched the installed workload YAML hashes. These are requested lengths, not completed-token measurements or live iteration shapes.

| Workload | Requests | Mean requested output | >=512 output: requests / output-token share | >=1024 output: requests / output-token share |
|---|---:|---:|---:|---:|
| Mooncake median | 4,004 | 178.00 | 383 / 36.63% | 22 / 4.47% |
| Mooncake burst | 4,220 | 180.84 | 390 / 34.52% | 21 / 4.31% |
| Mooncake cache-heavy | 4,053 | 187.77 | 409 / 38.34% | 37 / 7.38% |

Mooncake contains meaningful medium/long-output token volume, so it must not be dismissed as “only short output.” The >=1024-request cohort is small. Installed **agent-p75** fixes 8192 input, 6144 shared input and 1024 output tokens, making it a useful long-output control. Reuse both: agent-p75 for the frozen long-output objective, Mooncake for arrival mixtures, prefix reuse and tail guards. Do not pool them into one average that hides the tradeoff.

No new endpoint benchmark is needed for this hypothesis. Existing evaluators do not expose WKV event times or prove stream/cache correctness; that justifies a source probe now and a narrowly scoped correctness/instrumentation probe only when GPU work is separately authorized. Scored serving runs must remain unprofiled and compare equal prompts, token targets, arrivals, sampling and cache policy.

## How research adapted, and what was discarded

Five online provider queries ran: two arXiv failures (`TimeoutError`, then `HTTPError`), three successful OpenAlex searches. Failures are not empty evidence. OpenAlex's broad prefill query also returned a medical paper; the agent rejected that off-topic result. Two selected full texts were retrieved, with citation-expansion failures explicitly recorded. The Engram paper's multiple OpenAlex mirrors are one source family, not independent validation.

| Direction | Disposition and reason |
|---|---|
| Bounded replay | Prior DeepInfer N02 already recognized the disabled flag. Current PCP/H20/Flash-1017 PR does not solve original-profile quality/source questions. Retained old lead; not relabeled a new discovery. |
| P-PAS / SLOWeave | Prior frontier R2 already proposes adaptive prefill. No new target timing evidence resolves its main uncertainty; do not regenerate the card. |
| Gimbal coordinated MoE scheduling | New paper found and full text inspected. Backend pressure-aware routing is interesting, but overlaps earlier routing proposals and needs real queue/rank/cache traces. No new card in this batch. |
| Generic Engram lookup prefetch | Rejected as a duplicate of existing vLLM work. |
| Expert prediction/offload papers | Mostly address memory-constrained expert movement, not static Engram projection. Off-target for this narrowed decision. |
| WKV-only lookahead | Retained with source/branch/race constraints and unknown target gain. |

Six initial read-only canonical FTS searches, three later CLI local searches and exact source/diff reads were used. The selected direct GitHub adapter retrieved four PR bodies and two diff lists. Five committed source files were copied read-only from the node. No Serper or paid model calls were made by this field test. API billing is not measured here.

Query plans and observations are retained in `query-plan-1.json`, `query-plan-2.json` and their tool receipts. A real tool limitation appeared: Gimbal deep-read auto-selected a cited `deepseek-ai/EPLB` dependency and failed that repository stage; this is not evidence that the authors' implementation was inspected. The agent explicitly inspected the selected Engram reference diff instead.

## Reproducible artifacts and durable records

- `cpu_source_audit.py` / `cpu_source_audit.json`: actual CPU check and exact scope.
- `source-manifest.json`, `source-documents.json`, `source-revisions.json`: pinned source bytes/revisions and canonical-import material.
- `records/*-input.json`: five claims, hypothesis, unknown ROI screen, diagnostic plan, selection decision. The original invalid plan (`coverage=partial`) is preserved; v2 corrects the schema to `insufficient` and is review-ready.
- `persistent-ids.json`: typed IDs; hypothesis `hypothesis:36794075a7034c3f1ff100e73c1d8436a4606397c8e07766ed5388ef64b16646`.
- `INDEPENDENT_REVIEW.md`: separate scientific review; retain narrow candidate, no target ROI or service qualification.
- `field-test-state/`: isolated external research state. Its snapshot is local-only; canonical import/publication is a separate root action.

**Next cheapest useful action:** tie the intended image to source and inspect the exact WKV quantization/workspace implementation for a safe lookahead interval. If that mapping or stream-safety check fails, preserve the blocker. Further generic paper searches cannot answer those deployment-specific questions. **Zero GPU experiments; zero measured serving improvements in this run.**

# Round41 — graph padding: a conditional configuration lead

**Status:** source/CPU investigation; no new hypothesis card, no selection transition, no GPU execution. Retain this as a concrete extension of the existing graph-coverage family, with a distinct mechanism from C17's missing draft-boundary correction. No numerical service forecast.

Target source is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; planned target is frozen DeepSeek-V4.1-Flash, DSpark5, two TP1/DP4/EP4 groups on eight B200s. These are source/planned settings, not a fresh live deployment attestation.

## 1. Search and evidence actually read

- A bounded OpenAlex query, `CUDA graph padding LLM inference`, with publication dates August1 inclusive through October23 exclusive, returned10 abstracts. Every hit is classified in `paper-dispositions.json`. This was an online request, not just a corpus search.
- The complementary arXiv query failed with HTTP429. That is failed provider coverage, not zero papers. No repeated retry was made.
- Local PR searches used `capture sizes`, `graph padding`, and `graph bucket`, with `updated_at` in the same date interval and30 hits per query. Each result set reached its limit; the preserved results are not exhaustive discovery. Updated date is not publication date.
- CoRun and Herschel fulltexts were reused from retained exact revisions; original retrieval timestamps and body hashes are preserved. I read the relevant mechanism/comparator/ablation sections. This avoids another download and makes no freshness claim.
- Read PR62173 opening, actual current detail and both changed-file patches. Exact donor head: `938353862cd129d1921dd4144f4b47056499d600`. Read PR62525 and62441 opening records; their implementations were not qualified from those opening records alone. PR62040 was absent from the queried corpus; the retained historical C17 card is the available comparison, not a fresh upstream-status check.
- Existing memory inspection scanned141 hypotheses and returned all99 matches for the graph query. That is a bounded lexical inventory, not proof of semantic deduplication against every historical idea. C17 was separately read in full.

## 2. What the papers contribute

[CoRun](https://arxiv.org/abs/2608.14376) supports a specific caution: changing batch shapes can change floating-point reduction paths and therefore output trajectories. Its fixed-shape decode and isolated-prefill design targets determinism. Its large headline gains compare with a batch-invariant implementation, not our standard pinned deployment. Its padding ablation shows a cost when few real requests occupy a larger fixed shape. Disabling SplitKV also has a separate cost, especially for unequal context lengths. Consequently, importing CoRun wholesale is not justified by this objective; its shape/correctness analysis is useful to design this experiment.

[Herschel](https://arxiv.org/abs/2609.40247) motivates using measured workload exposure and targeted profiling. It does not supply our exposure measurement or permission to profile the occupied GPUs. Both papers were already retained, so these are revisited sources rather than two newly discovered papers.

The remaining abstract-level hits cover energy modeling, token scheduling, host tokenization, sparse-model/hardware co-design, unlearning, kernel verification, pruning and phase-specialized quantization. Their individual dispositions preserve potentially useful components without manufacturing an immediate graph-size candidate from an adjacent topic.

## 3. Mechanism: physical graph rows can exceed useful rows

[PR62173](https://github.com/vllm-project/vllm/pull/62173) changes the default small-request grid from1,2,4 to every count1..8, preserving the existing larger strides. That request grid is multiplied by the speculative query width. Explicit capture lists are not automatically rewritten.

The pinned target still has the older default request grid in `vllm/config/vllm.py`. The manager combines token sizes with other execution constraints, so copying the donor's K3 request-count table into our K5 setting would be wrong. Both token and request grids matter.

The donor's reported GLM/B300 and GLM/GB200 gains are not target estimates: its TP4, K3, synthetic acceptance, attention/quantization stack and workload differ. Its repeated AgentX comparison reports a small decode improvement with uncertain E2E change; its larger component results do not establish a comparable service win here.

### CPU evidence and the adversarial correction

`candidate_probe.py` executes unchanged AST-extracted pinned enum, descriptor, compatibility, candidate-generation and dispatch methods. It constructs a bounded configuration: cap1024, max128 requests, query width6, no LoRA/DBO/dynamic scheduling, and a stub saying graphs have been captured. No vLLM module/device backend is imported. The capture grid itself is a source-described fixture, not an observed launch configuration.

The first24 cases covered only uniform decode. An independent reviewer identified that `gpu/model_runner.py` sets `varlen_decode` when adaptive verification is active. The reviewer executed48 constructed cases covering both branches. The illustrative request totals are uniform in both branches; this is not a simulation of the actual adaptive scheduler's token distribution.

| Real requests, width6 | Uniform old → added grid | Varlen old → added grid |
|---|---:|---:|
|3|18 →18|24 →18|
|5|36 →30|32 →30|
|6|36 →36|40 →36|
|7|42 →42|48 →42|

Counts1,2,4,8 do not change in these fixtures. A dense1..32 token addition covers these uniform examples, but in the varlen fixture still leaves36/42 real tokens using40/48 slots. The initial “only five requests benefit” statement therefore applies solely to the uniform fixture and is not the final adaptive conclusion. Reviewer artifacts are separately frozen under `review/round41-agent/`.

**Important scope:** varlen descriptor `num_reqs` is capacity, not a measured number of scheduled requests. Actual adaptive mode resolution may choose a different graph mode. Explicit configured sizes, LoRA, DBO, caps, query-length bounds and mixed prefill can change selection. DP synchronization redispatches using the maximum padded token count and agreed query bound across ranks (`dp_utils.py`); a useful local shape reduction can disappear when another rank sets the common size. These must be checked before estimating exposure.

## 4. Why the Gemma padding result is not an absent target feature

[PR62525](https://github.com/vllm-project/vllm/pull/62525) reports a Gemma routing-padding improvement. Our pinned MegaMoE already conditionally reads the forward-context padding mask and passes it to preparation; preparation writes negative expert IDs and zero weights for padded rows. The inspected target therefore already contains the central unrouting mechanism. Its live enablement and mask population are not attested here.

This does not mean every operation on padded rows vanishes. Shared experts, attention, dense projections and preparation may still incur work. Reducing capture padding is a separate possible configuration improvement. It would be incorrect to use the donor's large routing gain as the ROI estimate for this change, or to infer all pad work is absent because routed experts can skip it.

[PR62441](https://github.com/vllm-project/vllm/pull/62441) concerns restoring captured routed-expert telemetry rows. The word “capture” in that opening is not evidence of a CUDA graph performance improvement.

## 5. Relation to existing ideas and rubric disposition

C17/E03/H14 concerns an unreachable draft graph bucket/boundary and possible eager fallback. This round concerns avoidable padding in a reachable graph. They share the graph-coverage exposure audit, but are not identical interventions. No old hypothesis is rewritten, and no duplicate rejection is assigned solely because both mention graphs.

- **Target applicability:** conditional; the changed default generator is absent, and an extracted manager selects smaller descriptors for concrete fixture inputs.
- **Existing implementation:** explicit graph configuration can express the smaller shapes already. This is initially a configuration experiment, not a new kernel project.
- **Evidence strength:** exact target source and donor diff plus CPU descriptor observations. No measured target frequency, graph memory or latency.
- **ROI:** unknown. If the affected synchronized shapes never occur, benefit is zero; if they occur, the removable exposed work remains to be measured. Row reduction alone is not latency reduction. Extra graphs also consume capture time and memory/KV capacity.
- **Novelty:** not a requirement. This remains worth retaining even though a public PR and an existing graph family exist.
- **Disposition:** park a bounded configuration/exposure lead; no new standalone card and no implementation/service qualification. Preserve the initial fixture and its correction as evidence of the review's effect.

## 6. Appropriate next experiment, when authorized

First obtain the effective model-runner version, adaptive-verification mode, capture list/cap, graph mode and padding flag from exact-baseline retained configuration or existing logs. Record real-token, selected-graph-token and query-bound histograms **after DP agreement**, plus mixed-prefill/eager fractions. If these records do not exist, later instrumentation is a separate permission-dependent activity; no occupied GPU was queried here.

Then compare current effective configuration with an explicit minimal added-size list derived from those exposed shapes. Preserve the same graph cap, decoding policy, weights, request stream, replica layout and other tuning. If the current list already contains all useful sizes, stop as a no-op. Avoid importing a broad donor configuration bundle or blindly increasing graph capacity.

The existing Mooncake and agent75 workload protocols are appropriate for the service question. No replacement synthetic evaluator is required. Later paired/interleaved A/B runs should report long-output ITL, its tail guards, TTFT, E2E, SLA goodput, throughput, failures, graph memory, available KV capacity and capture/startup time. Analyze affected-shape exposure as the mechanism check; do not silently replace the primary workload with a five-request toy that guarantees benefit. A small shape replay can be a labelled diagnostic, never the service qualification result.

Shape-dependent numerics require the existing correctness contract: fixed-seed/greedy differential checks where applicable, and the appropriate distribution/quality check for the temperature1 workload. CoRun's deterministic-runtime settings are not silently introduced into either arm. Promote only on a reproducible target improvement with guards satisfied; no invented percentage threshold or donor-gain extrapolation is used here.

## 7. Tool usefulness and yield

The online query contributed a comparator/correctness caution; PR search supplied the concrete missing default; pinned-code inspection narrowed it to actual dispatch rules; the independent reviewer changed the shape-exposure conclusion. Ten paper hits, two revisited fulltexts, three bounded local PR queries, one actual PR diff, zero new cards, zero qualified service wins.

This run also exposed a real tool failure: `investigate --deep-count 0 --code-source ...` skipped explicit code if no paper seed existed. The repaired path passed independent CLI/MCP/cache/budget tests and the real retained-cache replay now returns one pinned code document with zero HTTP budget/misses and no fabricated paper relationship. Before/after receipts are retained. The separate full test suite passed319 tests plus29 subtests; these are infrastructure tests, not inference validation.

Operational errors are preserved: unsupported `--defer-snapshot` on initial init was corrected; an attribute lookup after the first PR detail fetch failed, so the saved detail was reused rather than fetched again; the arXiv429 remained a reported failure. No GPU/model experiment was run. Tool model-call counts do not include the host agent's reasoning cost.

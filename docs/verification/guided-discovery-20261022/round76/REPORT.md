# Round76 — calibrate the proposal, preserve the target distribution

**Disposition: one deferred research proposal, PC76-01; no typed hypothesis creation, implementation promotion, GPU experiment or measured service win.** A positive draft-only temperature is an absent control in the inspected native DSpark path. It could increase committed progress per round while retaining the five-position drafter. It is not a safe configuration-only change: the current verifier reconstructs q using the target request temperature. Every consumer must receive the same actual proposal distribution.

This packet uses the planned Flash-1017/c455 TP1/DP4/EP4 baseline, not an attested live image. Unknown acceptance headroom does not refute the mechanism; it prevents a numerical gain forecast. The next implementation must preserve the original adaptive-verification policy in its primary comparison.

## 1. Discovery changed the decision

Read the complete compact inventory: **147 cards**, stable isolated backup inventory `f7c6c5c6194a10b40454b651dd6fad8268caae57fbaf0b76373f22f442e7eb5e`; selected 30 draft/calibration-related summaries and searched bounded campaign reports. Compact summaries may truncate: this is not a claim that every full dossier was read. A preliminary cross-query sparse-KV reuse idea was stopped as AT02/QUILT duplication before online queries.

Two real online paper searches covered August1 through October22 inclusive:

1. arXiv speculative decoding/sampling + temperature/calibration/proposal distribution: 12 hits. TreeSpark was already known; its acceptance scores are not a replacement q. ResiSpec concerns multiple alternative candidates at one position, unlike the current five-position Markov chain.
2. OpenAlex `speculative decoding draft temperature`: eight records, two overlapping paper identities. It added the directly relevant **Acceptance-Aware Draft Model Training** paper absent from the first bounded arXiv result set. This is actual added coverage in these receipts, not measured exhaustive recall improvement.

All **20 provider records / 18 paper identities** have dispositions. One selected primary full text was retrieved and read; the other papers were screened at abstract depth. DARTree, LiLiCorr, DCOCO, DBLAST and related trained mechanisms are not rejected wholesale: their available components were compared with the existing parent-conditioned DSpark path. No suitable untrained correction vectors or target-compatible tree verifier were established here. ReAnchor is an uninvestigated alternative, not a claimed result of this round.

Four retained-source queries then found the concrete implementation donor **SGLang#43052**. Actual opening metadata, all42 file patches and five selected exact-head source files were retained; four DSpark patches were read closely. Reading five files is not whole-PR validation. The generic `proposal calibration` local query also matched unrelated RFC text; it did not establish relevance. Both local broad queries were capped at15.

One operational error is preserved: `expand` ran before isolated initialization and returned `StateNotInitializedError`, explicitly without provider requests. Initialization was then awaited and a separately recorded retry succeeded. No tool change is indicated. An early informal source summary incorrectly said the cache contained scaled logits; reading the actual kernel corrected that before proposal formation.

## 2. A training paper supplies an inference-selection objective

[Acceptance-Aware Draft Model Training, 2609.24150v1](https://arxiv.org/html/2609.24150v1), September21, studies acceptance-oriented neural training. Its stochastic component relates ordinary single-token rejection acceptance to overlap, `sum min(p,q) = 1-TV(p,q)`, and uses a window objective emphasizing earlier positions. The target remains frozen while the paper updates draft neural weights.

We selectively reuse the **acceptance-oriented objective**, not its neural training, claimed gains or exact window formula as a native-verifier theorem. Our proposed adjustable parameter is initially one positive scalar draft temperature; no model weights change. Five depth-specific scalars are a later ablation only if one scalar helps held-out data.

The paper explicitly evaluates its window surrogate on common teacher-forced prefixes and invokes conditional independence given a prefix. Native DSpark draws parent-conditioned tokens sequentially, then uses block verification. A changed proposal changes sampled parents and which prefixes are reached. Therefore:

- Common-prefix overlap is a cheap screening statistic, not an estimate of online committed progress by itself.
- Multiplying overlaps from a baseline or teacher-forced trace does not prove the native block accepted-length distribution.
- Request-disjoint fitting is necessary but insufficient. Baseline logs do not contain target distributions for arbitrary counterfactual new-parent paths.
- Ultimately selected scalars require actual rollouts through the native verifier and unchanged recorded serving policy.

This limitation is part of the proposed experiment, not an excuse to call scalar fitting a proven improvement.

## 3. Exact native probability contract

Target source is [callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883](https://github.com/callgideon/vllm/tree/c4557869393db4d75c483d92edd02a5125500883). Five copied files were verified byte-for-byte against the retained source archive.

| Stage | Current source behavior | Required change or preserved boundary |
|---|---|---|
| Draft policy input | `DraftModelSpeculator._copy_request_inputs` copies request temperature into its persistent draft buffer. | Keep target temperature1; separate positive draft policy, with generation-to-verification ownership. |
| Markov proposal | `_sample_sequential` adds `base_logits[:,i] + bias` from the previously sampled parent, then samples. | Scale the **actual corrected conditional**, after the original addition/cast boundary. Scaling base or bias alone defines a different q. |
| Gumbel / cache | `gumbel_block_argmax` stores logits **before** temperature; selection divides in FP32. | Preserve raw cached dtype and reproduce the same FP32 division. Materializing scaled BF16 logits can introduce a different proposal through rounding. |
| Local normalizers | `_compute_local_logits_stats_kernel` loads cached q logits and divides by `temp`. | Use the proposal scale, keeping target logits and p unchanged. |
| Chosen-token probability | `_compute_global_logprobs_and_logsumexp` divides chosen draft logit by `temp`. | Same proposal scale and same normalizer, including cumulative block logic. |
| Residual recovery | `_resample_kernel` reloads cached draft logits, divides by `temp`, and combines q with the block target residual. | Same q; changing acceptance alone is insufficient. Preserve bonus, EOS, zero-residual and nonfinite behavior. |

The `_verify` caller supplies `sampling_states.temperature.gpu`, currently the **target** temperature. A draft-only override would silently violate this agreement. There is no supported native flag in the inspected path implementing the proposed calibration.

`contract_audit.py/json` checks11 exact AST/source fragments without importing or executing any target code. These checks establish source dependencies, not distributional correctness.

The parent supplied an independent exact-Fraction single-token control, retained with provenance. With target `(2/5,7/20,1/4)`, old q `(9,4,1)/14`, and temperature2 q `(3,2,1)/6`, using actual q for both acceptance and residual recovers p. Sampling new q but using old acceptance/residual gives TV distance `4/45`; updating only acceptance still gives `1/102`. These are synthetic algebraic counterexamples. They do not run or certify DSpark block rejection, native floating-point lowering or actual model quality.

## 4. The donor separates a cheap temperature arm from costly cutoffs

[SGLang#43052](https://github.com/sgl-project/sglang/pull/43052), inspected exact head **d618466dcc9d6d4792dc4bcd9e193e3d92bf881d**, is open and unmerged in the fetched metadata; its draft flag is false, although the opening text calls it a draft and reports GPU validation pending. We preserve that discrepancy and do not infer current GPU success from the flag.

The actual diff carries separate draft temperatures in `DraftParams`/`DraftBlockResult`, passes them into the fused `MarkovSampleStep`, reconstructs q in verification with `draft_block.temperatures`, and distinguishes target versus draft scales in its acceptance-observation path. That is concrete implementation precedent for the probability contract.

Its broader top-k/top-p controls require additional renormalization and redraw work. **Those controls are excluded from our initial arm.** We do not transplant the donor's kernel, graph classes or verifier wholesale. Native vLLM has a different raw-logit/rejection interface; its three q-scaling paths require a local adapter. The donor has a single temperature override, not evidence that five per-depth temperatures are profitable. Its claimed CPU test counts and unrun GPU tests are author reports, not tests reproduced here.

## 5. One bounded proposed intervention

**PC76-01:** fit and freeze one positive draft temperature for the existing native DSpark5 chain, retain target temp1/top_p1 and full vocabulary, and propagate the actual conditional scale to all native q consumers. Keep every target/drafter neural weight unchanged. No top-k cutoff, greedy override, tree, extra draft pass or wider window.

Initial scope is ordinary unwatermarked probabilistic requests without unsupported logit processors; other modes retain the baseline. Admission must be explicit, not assumed from benchmark defaults. Preserve seed domains, position/step counters, padded rows, request reuse, all-rank policy agreement and graph buffer addresses. A fixed scalar minimizes policy-buffer complexity; changing it between rounds cannot overwrite information still needed to verify earlier proposals. Any per-depth extension requires exact request/depth mapping.

Stochastic losslessness means preserving the target distribution, not preserving every output token at the same seed after changing q. Native numerical/distributional tests remain mandatory; a mathematically correct proposal family is not sufficient to certify the actual implementation. A same-temperature identity arm must reproduce the original code path before fitting anything.

### Confidence and adaptive verification are separate contracts

The learned confidence head receives parent embeddings derived from sampled tokens. `_maybe_predict_acceptance` also runs before Gumbel scaling; the online entropy estimator consumes temperature, while native DSpark disables it when a trained confidence head exists. A changed q therefore changes both conditional acceptance and potentially confidence reliability.

Five is the maximum number of drafted positions, **not** a guarantee that all five are verified under AV. The primary comparator must retain and record the original actual AV policy and budget. Do not silently disable AV to make a favorable fixed-five result. An AV-disabled or recalibrated diagnostic is a separately declared factorial arm, and cannot substitute for the serving baseline. No claim is made that the existing trained confidence head remains calibrated.

### Calibration and falsification

Use request/session-disjoint fit, validation and untouched test partitions, stratified by task, context and output entropy. Select one scalar on fit/validation only, include temperature1 as the mandatory null, and freeze before testing. Do not select from aggregate token-frequency traces or fit against benchmark test outputs. Common-prefix p/q observations can reject obviously poor temperatures, but actual alternative-parent rollouts are still required before estimating progress.

The campaign's trace-applicability and bounded exposure inventories did not recover exact-target conditional logits or representative native block rollout data. This round did not repeat remote searches or pretend that absence is global. No scalar has been fit and no target acceptance gain has been measured.

## 6. Benefit bound and evaluation priority

The potential benefit is algorithmic: more committed tokens for approximately the same target/draft work, rather than tiny metadata removal. Let original measured round time and progress be `T,G`, changed values `T+delta,G+g`. Progress/time improves only when `g/G > delta/T`. Every quantity is unknown here. Lower entropy is not automatically better overlap; the best scalar may be1 or may vary across domains.

A temperature-only implementation can reuse existing FP32 divisions and normalizer scans; it need not add a full-vocabulary softmax pass. It still adds policy plumbing and may alter AV shapes, parent-conditioned confidence, graph selection or request progress. No zero-cost assumption follows from the donor. C025 changes sampler cost; this proposal changes q. QH45/round49 change precision/support. Their benefits are not additive and must eventually be compared as separate arms.

The conditional maximum of six committed tokens for a five-token draft plus normal correction/bonus is only a ceiling under the actual EOS/termination convention, not observed available headroom. A baseline already near that ceiling could make calibration immaterial.

Fastest current falsifier was source inspection: the naive flag change is wrong. The independent scalar counterexample isolates why both acceptance and residual matter. Next meaningful evidence requires exact p/q/parent/AV traces and later authorized rollouts; more generic papers or synthetic acceptance examples would not estimate our headroom.

Future matched evaluation: original coupled temperature; one separate scalar with all q consumers repaired and original AV policy; optional five scalars only if justified. Record actual proposal scale, parent IDs, accepted/committed counts, AV width, target/draft/sampling time, DP/graph descriptors, queueing and memory. Use the standard Mooncake and agent-p75 service workloads for long-output client ITL plus separate TTFT/tail/error guards; add correctness and distributional cells for EOS, rare code/Unicode, padding, request reuse and graph replay. No numerical SLA threshold is invented here.

## 7. Yield and stop

Two dated provider queries;18 paper identities; one full text read; five exact donor source files and four relevant patches inspected; five target files checked; one source-backed deferred author proposal. **Zero typed identities, zero implementation/service qualifications, zero GPU runs.** The adaptive loop added evidence and rejected an unsafe apparent knob. It has not demonstrated improved hypothesis quality by a score or delivered a performance win.

Stop this branch for independent review. The next scientific decision is whether authorized exact-target data shows enough held-out acceptance headroom to justify the local verifier plumbing. Preserve the component even if the answer is negative.

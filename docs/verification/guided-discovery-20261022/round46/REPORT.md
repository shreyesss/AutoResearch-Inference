# Router projection → expert selection: recent-paper source screen

**Disposition: zero new hypothesis cards.** Retain a selective small-row fusion component as a research lead; implementation and service benefit are unqualified. No GPU, runtime import, serving traffic, allocator changes, model execution or canonical writes occurred.

## Question and source baseline

Can we eliminate the router-logit producer/selection boundary without changing learned routing, expert weights, or the planned Flash-1017 decoder? Source baseline is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; planned target is `DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`, B200 TP1/DP4/EP4. Loaded router weight dtype, branch occupancy and exposed time are not live-attested. This is not an assertion that arbitrary FP32-output gates have FP32 weights.

The full compact inventory contains 142 identities. Historical H03 router cards already require loaded-dtype, graph-row and active-branch evidence before applying Hopper BF16x3. Five exact matching cards and events are retained in `prior-router-full.json`; repeated briefs were excluded to avoid matching a card merely because its context quoted another idea. This screen targets a different producer/selection boundary, but difference alone does not justify another deferred card. Existing M01/WP38 concern expert scheduling/weight placement, and N03 covers resource allocation; those are not rediscovered here.

## Adaptive discovery actually run

1. Fresh isolated state; two-page compact recall from a read-only canonical memory copy.
2. Authored query plan initially failed because `observations` requires objects. Failure retained; corrected plan passed `researchctl expand`.
3. One actual arXiv paper-search, 2026-08-01 through exclusive 2026-10-23, requested ten results: router/routing + MoE + inference/latency + kernel/fusion/GPU. All ten abstracts screened; all dispositions retained.
4. Canonical source lookup found MegaFlux and Weave fulltexts already retained. Production selected-source import reused them and the round38 report, preserving revisions with no repeat HTTP. New MoRE fulltext was fetched through the existing Sources cache.
5. Exact target-source inspection found broad fusion already implemented. Three local FTS queries produced noisy full-body matches, so a bounded title query was the useful adaptation. Four selected PR records were imported with the production tool.
6. FI6129's exact current detail and changed-file patches were fetched (two cache misses), because its exact shape and reduction contract could change the decision. All 33 patches retained; host dispatch and selected numerical-reduction patches read. No claim of full generated-kernel audit.

This yielded ten paper dispositions, four selected PR records, six pinned target code files, one new fulltext, and zero qualified new interventions. Query receipts preserve source dates, provider results and failures. Reused fulltexts are retained for provenance; they were not re-read end-to-end. The broad local FTS hit lists and title screens are not complete PR reviews.

## Paper synthesis: use the component, preserve the model

[MoRE, arXiv2609.36301v1](https://arxiv.org/html/2609.36301v1) fuses low-rank projection with a running top-k buffer. Its fulltext explicitly allows a similar fusion for ordinary MoE and reports diminishing benefit as hidden width grows. Thus training is not a reason to discard the running-selection component.

However, replacing the frozen dense gate with learned low-rank factors would change the model. MoRE's inference pseudocode also uses softmax-derived top-k weights and a BF16 intermediate in the factorized projection. Those are not the target's sqrtsoftplus, correction-bias selection and unbiased-weight normalization semantics. Its large-expert prefill numbers are not measurements of our 384-expert, hidden5120, small-row router. The paper itself says MoE and MoRE have similar decoding speed.

Selective inference-only idea: produce dense-gate scores and maintain selected experts inside one kernel, avoiding a separate FP32 score tensor. Whether it is absent depends on the exact target branch.

## Exact pinned implementation already covers much of it

Retained files have exact blob URLs and SHA256 in `source-receipts.json`.

- V4.1 `nvidia/model.py:126–150` inherits the V4 MoE and supplies `num_hash_layers=0`; main target layers use learned routing. Draft-layer expert counts can differ, so main target geometry cannot be multiplied into all DSpark calls.
- V4 `nvidia/model.py:247–276` sets native-Mega eligibility and constructs GateLinear with FP32 **output**. It does not establish the loaded weight dtype.
- `model.py:449–520`: for the 384-expert target the small padded-row branch is `M<=16`, using `GateLinear` then `fused_topk_bias`. Above16 it already calls `bf16_mega_gate`, integrating projection/selection. A threshold is an existing performance choice, not evidence that the threshold is optimal or defective.
- `gate_linear.py:280–370`: eligible BF16 weights/activations use the existing low-latency CuTeDSL GEMM at<=16; other dtype/quantization/batch-invariance predicates choose other paths. The runtime is not necessarily using ordinary `torch.mm`.
- `fused_topk_bias_router.py:168–248` sends the eligible sqrtsoftplus, no-hash, top6 case to `dsv4_topk` before generic intermediate allocations.
- `dsv4_topk.py` already fuses activation, correction bias, six selections, tie ordering, normalization and scaling in one row kernel. It loads bias before PDL wait and launches dependents before final stores. Ties prefer the smaller expert index; selected weights come from unbiased scores. Padding has explicit zero-weight/-1-index semantics.

Consequently “fuse top-k and normalization” is already implemented, and “fuse GEMM+top-k” is already used for larger rows. The remaining small-row producer boundary is real, but its separate low-latency kernel may be faster than a larger fused kernel. Eliminating a launch does not settle that tradeoff.

## PR triangulation changes the comparator and correctness requirements

[FI6129](https://github.com/flashinfer-ai/flashinfer/pull/6129), observed merged head `a35b8b12790dbee96312266849e3505692036174`, implements exact main-target dimensions K5120/E384/top6. Selected diff inspection confirms a 16-way split-K cluster route for M1 and SM100 M2–4, plus compensated partial reduction. This is a concrete donor implementation rather than a paper-only sketch.

Its author benchmark compares against native DeepGEMM `39d8c4ca` **fused** gate. Our <=16 branch instead chooses GateLinear plus dsv4_topk. Therefore even its same-shape B200 figures do not establish a speedup over the target. The report also explicitly says changed-route normalized weights are not bit-identical. Better error against an FP64 reference and unchanged sampled top-k sets do not prove exact target routing/weights for near ties or all inputs. The kernel patch changes accumulation structure as claimed; we did not execute it.

FI6427's body describes a deterministic small-M schedule, but that is not automatically the target's numerical reference, and its head was not audited. FI5961 is a runtime-template refactor. PR61903 is the historical Hopper FP32-weight route and remains an existing family, not a new B200 intervention.

## Work bound, not a latency estimate

The removable score store+read is `2 * M * 384 * 4 = 3072*M` logical bytes: 3KiB at M1, 48KiB at M16. This does not mean that many bytes reach HBM. The dense BF16 gate weight payload would be 3,932,160 bytes; FP32 weights would be twice that, but actual dtype and cache residency are unverified. Fused selection can add synchronization/reduction pressure and alter the GEMM schedule. Existing PDL/graph behavior also makes a naive launch-count estimate misleading.

No synthetic timing or arbitrary percent threshold is introduced. A whole decoder gain needs eligible call frequency and exposed component time, neither established here. No new CPU fixture can manufacture that missing timing evidence.

## Decision and reopening conditions

**Park the small-row producer-selection component; do not create a new deferred card merely because it is structurally distinct.** Keep MoRE and FI6129 as selective source evidence. Do not reject the whole paper for its training component.

Reopen if retained target traces establish material small-row router time or an exact-reference donor supplies a credible matched baseline. Then first attest loaded gate dtype, actual rows/capture path and routing options; compare current GateLinear+dsv4_topk, native fused gate and the proposed fused gate under identical conditions. Keep routing identities, normalized weights, tie/NaN/infinity/padding rules, and unchanged model execution as explicit correctness contracts. Any changed-numerics relaxation would require separately declared scope; current source evidence does not grant it.

A future authorized evaluation would use standard Mooncake/agent-p75 service workloads plus an isolated component comparator for attribution. No custom service workload is justified yet. No server speedup, current service eligibility, model equality, or new accepted experiment is claimed.

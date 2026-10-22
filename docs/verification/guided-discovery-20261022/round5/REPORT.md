# Round 5 — roadmap → physical locality → target adapter audit

## Result

**Two distinct candidate interventions retained, neither service-qualified nor implementation-ready.** The stronger new decode direction is **RD01: physically localize MegaMoE weight slices inside a B200**, while retaining the domain-aware scheduler already present in the dependency. RD02, a host-side MXFP8 dispatch cache, remains deferred because CUDA graph replay may remove its entire critical-path exposure.

No GPU work, CUDA/MPS availability calls, model loads, server changes, or GPU experiments were performed. This audit uses pinned source and the planned Flash-1017 TP1/DP4/EP4 layout; it does not attest a live binary or environment.

## Adaptive route taken

1. Consulted the prior hypothesis index. Existing route-histogram tiles, SM allocation/Weave, EPLB placement, TopK and bounded-replay ideas were not relabeled.
2. Searched the local PR corpus first. DeepGEMM #462, DeepEP #763 and SGLang #44933 were present. Roadmaps #42170/#39700 were absent; fetched their primary GitHub bodies and a bounded selection of linked PR bodies/diffs. An isolated `researchctl show` initially failed with a missing-record KeyError; this was not a provider outage.
3. Roadmap details exposed an optional **physical weight localization** feature in DeepGEMM. The first online paper query found recent physical-topology and operand-locality literature; three full texts were read.
4. Followed the actual target allocation → loader → kernel argument → EPLB contracts. This changed the proposal from “enable a feature” to a specific adapter with lifecycle constraints.
5. A second narrower paper query rediscovered Weave and found VAMP. Its full text explicitly reports a TPOT penalty for a TTFT/cache-capacity objective. This prevented advancing it as a decode win. Its cost-comparison component remains useful to existing memory-policy work.
6. Independent review found a smaller EPLB repair: expose each contiguous domain slice as another expert-weight component. The CPU source diagnostic now includes that repair, rather than stopping at the first shape failure.

Receipts: `paper-search-01.json`, `paper-search-02.json`, `discovery-command-journal.json`, `tool-use.json`. Full source dispositions: `screening.json`. Two online provider calls succeeded; the second added useful contrary evidence, not a new decode candidate. Nineteen screening records are sources/lead dispositions, **not nineteen hypotheses**.

## RD01 — physically localize MegaMoE routed and shared weights

### Problem and proposed mechanism

B200 contains physical memory/cache locality domains. Logical GPU addresses do not guarantee that the SM doing a weight read is near that memory. Work that streams expert weights can incur remote traffic. Recent research characterizes chip-specific topology and the need to align data placement with persistent work assignment. This is a possible mechanism, not evidence that our decode step is currently limited by it. [Physical topology paper](https://arxiv.org/html/2609.24270v1), [operand access characterization](https://arxiv.org/html/2607.28824v1).

[DeepGEMM #462](https://github.com/deepseek-ai/DeepGEMM/pull/462) introduces optional physical weight localization. The selected dependency already has the scheduler, mapping discovery and localized MXFP4 weight interface. Pinned vLLM allocates ordinary tensors in `_register_weight`. **Only physical weight placement is the new delta.** The release's power/frequency observations do not establish target ITL or token throughput.

### Exact source path and proposed intervention

Pins: vLLM `c4557869393db4d75c483d92edd02a5125500883`; DeepGEMM source default `a7a927731b109fdfec770df7c2a5be5d7e2216b5`.

- V4.1 inherits native MoE setup from `vllm/models/deepseek_v4/nvidia/model.py`.
- `vllm/model_executor/layers/fused_moe/deep_gemm_mega_moe.py` allocates ordinary weights, loads checkpoint shards directly into kernel layout, and forwards those parameters to the dependency.
- DeepGEMM `locality_domain.py` transforms logical `(E,N,Kpacked)` into physical `(domains,E,N/domains,Kpacked)` by placing each leading slice in its memory domain.
- The ordinary MXFP4 kernel launch **already** calls `get_balanced_sm_locality_domains()`. The proposal does not add an allegedly missing scheduler or change router decisions.
- Localize already transformed routed L1/L2 and fused shared L1/L2 together, leaving scale tensors in their documented logical layout. Do this before graph capture, EPLB's weight-view capture and any communication registration.
- Preserve gate/up interleaving, packed values, lifetime ownership and weight reload semantics. Do not retain full ordinary and localized representations permanently without explicit capacity justification.

### A real blocker, and a narrower repair

A one-line replacement of the parameters breaks both loader indexing and EPLB: existing code expects the first dimension to be the local expert count; localized storage's first dimension is the domain count.

`layout_contract.py/json` executes the **actual extracted target EPLB view function** with shape-only CPU stubs. For both target packed projections, ordinary views pass and domain-first whole tensors fail. Symbolic naive flattening also mixes different experts.

The independent reviewer followed the consumer API further: EPLB accepts a list of expert-weight components. Each localized domain slice has shape `(E,N/domain,Kpacked)` and can independently supply a contiguous `(E,-1)` view. Moving every domain component for one expert, alongside its unchanged scales, preserves the logical expert. The revised CPU diagnostic passes the extracted view check for those slices and reconstructs a symbolic swapped expert.

This **does not** test actual tensor strides/padding, MLOPart allocation, NIXL registration, asynchronous distributed copies or numerical inference. It establishes that a small domain-wise adapter is plausible rather than requiring an EPLB rewrite. Source lifecycle boundary: `vllm/model_executor/models/interfaces.py:set_eplb_state` gathers expert views after loading/quant processing; `eplb_state.py` builds buffers from those views. Finalize localization before that capture. Keep baseline EPLB semantics intact.

### Eligibility and strongest contrary evidence

- Source dispatch uses architecture major 10, so the inspected API is not explicitly SM103-only. Actual B200 driver/container/MPS support remains unknown. A hardcoded two-domain constant is not a capability check.
- **Do not call `is_localization_available` during CPU research.** Its helper launches a private MPS process and initializes CUDA. Even `destroy_localizer` can trigger mapping probes. None were called.
- Mapping probes can fail and fall back to an even assignment; successful allocation alone is insufficient evidence of useful physical affinity.
- Routed and fused-shared tensors must agree on localization. The separate NVFP4 API does not establish the same support. This card applies to the audited MXFP4 path only.
- The selected heuristic requires the full GPU SM count; do not combine with unsupported SM-quota changes.
- Memory allocation/copy peaks, padding, and retained views need accounting. Installed dependency/image and baseline EPLB must be verified later.
- Decode can be limited by communication, attention, sampler or launch gaps. Heavy-workload clock improvement is not a valid ITL forecast.

Independent review: `../review/round5/LOCALIZATION_REVIEW.md`, `localization-review.json` and its domain-slice follow-up. **Disposition: retained, deferred for environment and adapter qualification.**

### Evaluation design

**Now, CPU/source only:** finalize exact post-load lifecycle; test packed-weight reconstruction and expert permutation/duplicate semantics across all domain slices and scales. Verify no stale ordinary buffers survive EPLB registration. Establish expected allocation footprint from actual parameter metadata. No allocator availability probe.

**Later, only when GPU work is authorized:** confirm physical allocation and useful SM-domain mapping, preserved packed weights, target output correctness and EPLB transitions; measure matched native MegaMoE calls before service benchmarking. Use the same standard Mooncake and agent-75 replay with fixed model/config/DSpark and comparable offered load. Track output-token throughput, ITL/TPOT distribution, TTFT and tail guards, errors, power/clocks and exposed MoE duration. The standard workloads suffice for service impact; they need additional mechanism instrumentation to attribute any change. No new workload is justified merely because the optimization is low-level.

No numeric gain forecast is justified yet. Amdahl's exposed-MoE fraction and actual locality improvement are both unknown.

## RD02 — cache repeated host MXFP8 dispatch bookkeeping

[SGLang #42156](https://github.com/sgl-project/sglang/pull/42156) contains an actual metadata/runner cache despite an unfilled PR description. It specializes CuTeDSL MXFP8 host dispatch and keys shapes, strides, dtypes, devices and scale layout; it does not cache model outputs. Donor head `6601ff2f4b244f86abb97ac11bed28d8d21886ad`.

Pinned vLLM's CuTeDSL linear implementation calls `vllm.utils.flashinfer.mm_mxfp8`, which forwards to the raw API. The wrapper does not contain the donor cache. However, installed FlashInfer may already cache internals, the backend may differ, and **full CUDA graph replay does not execute this Python factory/validation on every decode step**.

Therefore: first inspect saved graph coverage and the actual installed backend/version. If the call is capture-only, reject this candidate for steady-state decode. Only demonstrated uncaptured exposure warrants porting/testing the cache. Do not run redundant cache unit tests before answering that source-path question. No upstream or target speed evidence was established. **Disposition: deferred.**

## Negative results worth retaining

- SGLang #44933's TP4 attention/allreduce chain does not match TP1/DP4/EP4. Selective single-operator prefetch remains a possible separate question, not a claim from the full chain.
- #41660's compressor fusion is already present in target form. Its runtime ring/padding protocol is different; the target uses compile-time ring geometry in the inspected kernel. Direct port rejected.
- DeepEP #763 is not the native MegaMoE backend being executed. Generic overlap is already in prior hypotheses.
- Roadmap decode DP attention + MegaMoE is baseline. Bounded replay, MegaMHC and generic TopK are not new just because another repository links them.
- [NUNA](https://arxiv.org/html/2608.00867v1) provides topology-aware network concepts, but its simulator/AMD routing setup does not establish an available target NVLink/EP4 control interface.
- [VAMP](https://arxiv.org/html/2609.13537v1) dynamically exchanges expert residency for KV capacity. Its reported case improves TTFT while worsening TPOT by 31.1%. There is no evidence of the required capacity cliff here. Retain its three-way penalty comparison for existing memory-policy research; do not market it as a decode-latency improvement.

## Remaining decision gap

RD01 now has a concrete absent source delta and a plausible small adapter. The decisive next source question is lifecycle and expert-component ownership, followed by environment eligibility on an authorized idle machine. Until then it is a justified research direction, not a promised win. RD02 requires proof of uncaptured host work before implementation. No candidate was promoted to service-qualified improvement.

# Physical weight localization: independent source audit

## Disposition

**Retain a distinct decode-oriented candidate, deferred for environment eligibility and adapter design.** This is physical allocation of routed/shared weight shards into GPU locality domains. It is distinct from M01 route-histogram tile choice, EPLB inter-GPU expert placement, and earlier SM-share tuning. Domain-aware scheduling already exists in the selected dependency; do not count that as a new change.

Pins: target vLLM `c4557869393db4d75c483d92edd02a5125500883`; configured DeepGEMM source `a7a927731b109fdfec770df7c2a5be5d7e2216b5`. These are source defaults, not a measured live-binary fingerprint. Model config is Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, quant_method fp8, UE8M0, expert_dtype fp4. No GPU API, availability helper, CUDA import or daemon was executed.

## Positive transfer evidence

DeepGEMM test_mega_moe.py184–192 localizes transformed routed L1/L2 and shared L1/L2 weights, retaining original scale tensors. `locality_domain.py16–24` changes `(E,N,K)` to `(domains,E,N/domains,K)` and allocates each leading slice in its domain. Layout helpers recognize that representation and recover logical dimensions. MXFP4/FP8 MegaMoE C++317 and340–341 require consistent localization across routed/shared pairs. Dispatch at385 accepts architecture major10, so the selected source is not explicitly SM103-only. This is source eligibility for SM100, not proof that a particular B200 driver/MLOPart environment supports it.

Pinned vLLM `_register_weight`433–448 uses ordinary torch.zeros; `_kernel_weights`450 onward forwards these parameters. Therefore physical localization is absent at that allocation boundary. Meanwhile ordinary MXFP4 launch already passes `get_balanced_sm_locality_domains()` (DeepGEMM mega_moe.hpp395). Proposed delta must be weight placement, not adding an allegedly absent scheduler.

## Concrete adapter blockers

1. **Checkpoint loading assumes expert-first storage.** `deep_gemm_mega_moe.py491–500` writes `param.data[local_expert_id]`; `_load_weight`557 onward assumes a two-dimensional expert slice. A naive localized Parameter replacement adds a domain axis and changes this meaning. Load normally then perform an explicit final transformation, or implement a localized-aware loader. Preserve transformed gate/up row order and packed FP4 values.
2. **EPLB assumes contiguous complete expert views.** `get_expert_weights`683–704 asserts leading dimension equals num_local_experts and returns `(E,-1)` views. A localized expert is split across domains and may have allocation padding; it cannot be represented by that existing contiguous view. A fixed-placement, EPLB-disabled diagnostic lane is possible only if explicitly compatible with the tested baseline. A promising minimal repair exists: EPLB already accepts a list of `(E,-1)` components. Export each `localized[d].view(E,-1)` domain slice as a separate component, plus unchanged scale components. Individual domain slices are contiguous even when there is padding between domains. `rebalance_execute.py509–510,547–548` copies each component back into existing weight storage, and communicator339 onward checks each component separately. This can preserve physical allocation without a global gather/scatter rewrite. It still needs exact adapter tests, consistent component ordering across ranks/layers, synchronization and registration before EPLB captures views/NIXL registers addresses. Do not silently disable baseline EPLB to manufacture a win.
3. **Shared weights must change together.** C++ localization parity checks prevent localizing only routed matrices while fused shared experts remain ordinary. Packed scale tensors stay in original logical layout under the demonstrated MXFP4 API; indiscriminately localizing scale tensors changes a different contract.
4. **No blanket NVFP4 transfer.** Separate `nvfp4_mega_moe.hpp314–325` checks ordinary grouped layouts and contiguity; shared dimensions must be2 at360. Python shared shape checks likewise assume ordinary shapes. The MXFP4 path matches the model config, but an override to NVFP4 would need a separate adapter audit.
5. **Stable pointers and temporary memory.** Localization allocates and copies new weight storage. Perform before graph capture; establish parameter/buffer ownership and release original allocations if not needed. Retaining both full representations doubles affected weight storage temporarily or persistently. Do not assume HBM headroom from source alone. Weight reload and EPLB must not silently replace localized storage with ordinary tensors.

## Availability is an operational gate, not a cheap pure query

`is_localization_available` invokes the Python MLOPart helper. Its constructor spawns a subprocess; the script starts a private nvidia-cuda-mps-control daemon, requests `start_server ... -mlopart`, calls cuInit, and requires two exposed locality devices. Existing code comments state this IPC route is used before CUDA13.4; planned native locality APIs are TODOs. Driver/container permissions, MPS tooling, and actual target support remain unknown.

The allocator hardcodes two domains in this revision; that constant is not device capability evidence. Source launch uses architecture-major10 but does not provide an SM100-vsSM103 availability matrix. We have not run any availability probe. Even `destroy_localizer` reaches `get_balanced_sm_locality_domains` before release, which can initiate probing; it is not a harmless CPU-only cleanup call.

`get_sm_locality_domains` performs GPU pointer-chase probes, requiring a >=1.25 far/near latency ratio and TPC consistency. After five unsuccessful attempts it falls back to an even mapping. The helper may therefore allocate successfully without yielding a useful physical affinity map. A future experiment must record mapping/probe outcome; successful API return alone is insufficient. MegaMoE's selected heuristic additionally requires the full GPU SM count (mega_moe.hpp66–71), so do not combine this candidate with unsupported reduced-SM tuning.

## ROI and falsification

DeepGEMM #462 reports lower power and 5–10% higher frequency under heavy workloads. This is an upstream claim, not target token/sec or latency evidence. Physical locality could reduce cross-domain traffic and improve useful clocks in a bandwidth/power-limited decode regime; it can also provide little benefit when limited by communication, attention, sampling, light duty, or a poor affinity map. Do not equate clock percentage to ITL improvement.

CPU/source next step: define an adapter contract for post-load MXFP4 + fused-shared localization and domain-wise expert mutation, identify actual baseline EPLB and source-binary selection from saved manifests, and check memory arithmetic with actual tensor shapes. If EPLB is active and no safe adapter exists, keep deferred rather than switch it off. Future authorized GPU gate: exact output/weight reconstruction, localized allocation/mapping evidence, then paired steady-state MoE time/ITL and power/clock traces against unchanged best baseline. No GPU experiment is authorized now.

## Decision-changing checks

Searching only function names would falsely suggest a one-line activation. Following shape changes into the target checkpoint loader and EPLB API exposes the implementation work. Separating the MXFP4 and NVFP4 APIs prevents transferring an available feature into an unsupported variant. Reading the availability helper prevents an ostensibly read-only check from starting CUDA/MPS work while GPUs are reserved.

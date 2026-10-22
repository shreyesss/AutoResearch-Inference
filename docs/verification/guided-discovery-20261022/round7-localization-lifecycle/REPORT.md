# RD01 refinement — loader lifecycle, expert components and allocation ownership

**Scope:** CPU/source refinement of round5 RD01; no new intervention. No CUDA, MPS, PyTorch device imports or availability helper calls. Pinned vLLM `c4557869393db4d75c483d92edd02a5125500883`; selected DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`. Implementation remains deferred; no performance result.

## What changed after the earlier review

The existing EPLB interface can accept localized weights without a new transfer framework. Each domain slice is already contiguous in the dependency allocator; expose one `(E,-1)` component per routed matrix per domain, plus its unchanged scale component. All layers and ranks must use the same component count, shapes, dtypes and order. `EplbState.add_model` creates scratch buffers from the **first layer**; copy routines zip lists. Partial-layer localization with differing component counts can silently truncate copies. Normalize schemas across the model or reject that configuration before registration; do not localize an arbitrary subset while retaining ordinary component lists elsewhere. Shared weights are localized for kernel parity but are excluded from EPLB as before.

The source lifecycle is more constrained than “put it in post-load” suggests. The native model post-load method runs twice during ordinary loading, and hot reload invokes the old loader against existing parameter shapes. A safe implementation needs an explicit finalization stage and a reload policy.

## Exact call chain and smallest candidate hook

Runner selection is a source condition, not a live attestation: `gpu_worker.py:241` takes `vllm_config.use_v2_model_runner`; `_make_model_runner`567–583 chooses the V2 import when true. `config/vllm.py:705–741` honors explicit environment selection, then checks Triton and unsupported features before defaulting to V2. Record the actual selection before implementing; the audited V2 path below is primary, with the legacy boundary separately identified.

1. The selected V2 runner `vllm/v1/worker/gpu/model_runner.py:401` calls `model_loader.load_model` inside the model memory profiler and JIT warmup registry.
2. `model_loader/base_loader.py:88` calls the weight loader. Native `deepseek_v41/nvidia/model.py:1701–1704` streams weights through `AutoWeightsLoader`, then invokes `self.process_weights_after_loading()`.
3. Base loader later finalizes online quantization and calls `model_loader/utils.py:process_weights_after_loading`. This runs per-module quant transforms, deferred-attention transforms and then **again** the model-level post-load method at line210.
4. Base loader releases transient cached allocations and returns `model.eval()`.
5. V2 runner next wraps LoRA if configured (405), then loads its speculator and may register that model with EPLB (420–423). Main-model initialization follows; `maybe_register_model` at534 enters `gpu/eplb_utils.py:161–173`, which calls `EplbState.add_model`. The legacy runner has an analogous boundary at5025/5098, but is not the primary path evidence for V2.
6. `EplbState.add_model`486 calls `model.set_eplb_state`. `model_executor/models/interfaces.py:1111` obtains `layer.get_expert_weights()` views. State492 allocates component buffers and creates the communicator.
7. NIXL communicator stores tensor references, verifies contiguity and device, registers memory and exchanges pointers. Changing physical storage after this point leaves stale views and remote pointers.

**Smallest supported proposal:** an explicit optional finalizer immediately after the runner's `model_loader.load_model` has returned, before drafter binding and EPLB registration, still inside the load/profiling scope. It enumerates eligible native MegaMoE layers and transforms each completed weight parameter once. A model-specific final method may perform the work, but invoking the existing early post-load hook indiscriminately is unsafe. External preconstructed `model=` and alternative runner/loaders must be separately gated rather than assumed covered.

The finalizer must be idempotent and own a real layer state flag set only after all routed/shared tensors are finalized. Partial failure stops loading; it must not leave a mixture of localized and ordinary weights callable. The later normal kernel API has a strict parity check. Do not call a CUDA availability helper to implement the CPU audit.

## Parameter and EPLB representation

The target initially registers weights and attaches custom `weight_loader` attributes. The runtime `_kernel_weights` property fetches the current parameter rather than a captured constructor tuple. A proposed storage replacement must preserve parameter identity/attributes where valid or deliberately reinstall equivalent attributes; a new bare `nn.Parameter` silently discards the custom loader contract. Even preserved attributes cannot make the old expert-first loader understand domain-first shape.

DeepGEMM `empty_per_domain` allocates a padded span for each domain, then exposes a tensor with a padded leading-domain stride and contiguous strides *inside* each domain. This substantiates exporting `weight[d].view(E,-1)` per domain rather than flattening the entire tensor. Keep the localized tensor owner alive; domain views and registered pointers refer to that backing allocation.

The existing rebalancer iterates arbitrary component lists for staging, copy-back and duplicate propagation. All domain components and scales must participate. No whole-expert gather/scatter is required solely to satisfy this interface. Registration and per-component communication counts increase, while total useful expert bytes do not; no claim of zero EPLB overhead follows.

## CPU discriminator actually executed

`domain_components.py` uses packed byte payloads, simulated padded domain storage and writable byte views. It executes **102** deterministic permutations/duplicates/remote-source mappings. Every result reconstructs the expected expert payload and scale bytes. It also demonstrates five deliberate failures:

- Omitting one domain component corrupts reconstructed weights.
- Omitting a scale component leaves the wrong expert's scales.
- Naive in-place permutation without staged source buffers corrupts a swap.
- Views registered before relocation mutate old storage and do not update localized data.
- A six-component localized layer zipped against four ordinary scratch components processes only four entries; heterogeneous layer schemas must be rejected.

This is a representation/copy-semantics diagnostic for the proposed adapter. It does not execute vLLM communication, PyTorch tensor striding, actual allocator padding, GPU numerical kernels, asynchronous CUDA copies or NIXL registration. The existing exact-function shape diagnostic remains in frozen round5. Together they narrow an integration design; they do not prove deployment readiness.

## Hot reload, sleep and other unsupported paths

`model_loader/reload/inplace.py` calls `model.load_weights` for checkpoint-format reload. The native loader still indexes `param.data[local_expert_id]` and expects a two-dimensional expert shard. It will not correctly write a domain-first tensor. Kernel-format reload also assumes incoming shape matches the registered parameter. Therefore either:

- implement a domain-aware reload adapter that transforms each new checkpoint shard into the already-localized stable allocation, preserving registered pointers and scales; or
- for an initial static-weight diagnostic, explicitly reject reload **before any write** and document that scope, provided the experiment's unchanged baseline does not require reload.

The worker also has `start_weight_update` / `update_weights`; its source explicitly notes that weight transfer bypasses `GPUModelRunner.reload_weights` (gpu_worker.py1628). A static-weight guard must cover those entry points too; blocking only the reload method is insufficient.

Do not silently drop reload support or disable EPLB to manufacture a result. Do not relocate again after graph capture or communication registration. Sleep/offload, weight-cache IPC and alternative loaders are separate allocation-lifecycle integrations; no support is claimed. The direct external allocator is not automatically tracked by the existing sleep allocator.

## Allocation and peak-memory implications

`domain_components.json` computes one full target layer with 96 local routed experts (EP4, no extra replicas), hidden5120/intermediate2304, routed packed FP4 and fused shared FP8. This is metadata arithmetic, not observed tensor memory:

| Quantity | Bytes |
|---|---:|
| Routed L1 packed payload | 1,132,462,080 |
| Routed L2 packed payload | 566,231,040 |
| Shared L1+L2 FP8 payload | 35,389,440 |
| Unchanged scale tensors | 107,274,240 |
| Original layer payload+scales | 1,841,356,800 |

The new payload allocations overlap old storage while copying. Creating all four before releasing any old payload adds about1.73GB for this layer. Sequential replacement can lower the additional allocation to the largest single payload, about1.13GB, **only if** old references are gone, copies are complete and cached physical memory is actually released/reusable. These are conditions, not guaranteed observed peaks. Actual granularity is unknown; arithmetic scenarios of64KiB and2MiB yield0 and2,359,296bytes of extra per-layer padding. Do not infer all-model headroom from this one-layer example: DSpark dimensions, redundant experts, actual fusion and loader peak differ.

The ordinary `DeviceMemoryProfiler` uses CUDA platform `max_memory_allocated`, so raw CUDA/from_blob localization can reduce the reported PyTorch model-memory number without reducing physical usage. The later general memory profiler explicitly uses `mem_get_info` total consumption and tracks non-Torch memory. Thus the existing source is **not evidence of an inevitable KV budget bug**. Future validation must compare physical memory and allocator accounting; do not advertise the smaller PyTorch log as a memory saving.

## Disposition and next gate

**Retain RD01 as a concrete deferred integration proposal.** Source now supports a small finalizer plus domain-component EPLB adapter, with explicit unsupported lifecycle paths. The CPU tests falsify naive integration and support the narrower representation. Remaining gates are actual selected binary/MXFP4/shared fusion, MLOPart environment eligibility and useful affinity mapping, tensor/registration correctness, memory headroom, then authorized matched GPU/service evaluation. No numeric ITL/TPOT gain estimate is warranted.

## Independent review

`../review/round7/REVIEW.md` and `review.json` retain the candidate as deferred after checking V2 lifecycle, component schema and memory accounting. NIXL registration of raw localized allocations and remote indexed byte contracts remain runtime gates. Earlier report retained as `REPORT.pre-review.md`; this file is authoritative.

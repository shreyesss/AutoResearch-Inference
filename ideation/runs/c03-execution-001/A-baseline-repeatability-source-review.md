# Baseline A repeatability: read-only source review

The fixed-rank, no-cancellation control fails exact repeatability before any candidate deployment. Its cause remains unresolved. This review establishes source behavior and request provenance; it does not revise evaluator expectations, qualify B, or attribute the failure to numerical nondeterminism. No candidate/evaluator source, installed environment, service, GPU workload or runtime setting was changed during this investigation.

## Observed request evidence

Authoritative receipt: [service-rank-control-A.json](service-rank-control-A.json), status `fail_exact_repeatability`. Root reports all eight routing/drain attestations passed. Four pairs cover outer replicas0/1 and internal ranks0/2.

The existing [backend log](backend-a-exposure.log) independently records effective `SamplingParams(temperature=0.0, seed=731, max_tokens=64, ignore_eos=False)` for all eight requests. Parameter lines: **610062,610130,610187,610275,610330,610392,610463,610525**. Thus the available evidence does not support an API temperature/seed override as the explanation.

The prompt details and full prompt-token lists are byte-identical within each replica's four requests. Prompt-detail log lines are **610061,610129,610186,610274** for replica0 and **610329,610391,610462,610524** for replica1. SHA-256 of the literal logged `prompt_token_ids` list:

| Replica | SHA-256 |
|---|---|
| 0 | `dd484bb783aa7b47bbc9e86c1acc206c17d1697b013e1df58ad9d92aef9fc3ef` |
| 1 | `fed50ab56e370800525fed3a6e94bcf3247fe7afcfa35267559ca36f23910ea8` |

The replica-specific marker explains the expected difference between these two prompt hashes. Every request reports49 prompt tokens and `cached_tokens=0`, `created_cache_tokens=0`. Prefix caching is enabled in the profile, but these receipts do not show a prefix-cache hit.

Replica0 repeats already differ at the first emitted token:

| Internal rank | First request / log line / token | Repeat / log line / token |
|---|---|---|
| 0 | `chatcmpl-8e34ab94f8f7dd58` /610084 /671 (`The`) | `chatcmpl-8fff1a5d44f5d91e` /610151 /2581 (`We`) |
| 2 | `chatcmpl-9b48a156baee73d4` /610209 /671 (`The`) | `chatcmpl-a4e2aef96a6e331b` /610296 /2581 (`We`) |

This is a token difference, not merely stream-chunk grouping or final rendering. The receipt also records differing reasoning lengths and, for one bounded request, a length termination before final content. No candidate output is involved.

## Pinned sampler and state behavior

Local frozen source root: `/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/`. These files came from the unchanged pinned image `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`, vLLM `0.30.1rc1.dev493+gac9126e58`; hashes remain in `c03/source/snapshot-manifest.json`.

- [Sampling state](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/sample/states.py:42) stores the supplied temperature; lines54–58 store an explicit request seed directly, generating a random seed only when it is absent.
- [Request state](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/states.py:97) maps a request ID to a free slot; lines123–129 return that slot on removal. The examined seed path does not hash the request UUID. The request's actual slot index was not captured by this control, so identical rank does not attest identical slot/state contents.
- [DFlash preparation](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:739) propagates the request-state index; lines750–755 copy the corresponding temperature and seed. [DSpark sampling](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/spec_decode/dspark/speculator.py:138) keys sampling using seed and token position.
- [Gumbel sampling](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/sample/gumbel.py:181) adds temperature scaling/noise only when temperature is nonzero; the final reduction is argmax. For identical valid logits and correct state mapping, T0 therefore does not obtain a different draw merely because request UUID or seed differs.
- [Greedy verification](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py:549) accepts a draft iff it matches the target argmax in the active non-synthetic mode (lines570–590). Block probability-ratio randomness does not explain the greedy decision.
- [Target sampler dispatch](/home/ubuntu/Deepseek_serve-c03/c03/source/base/vllm/v1/worker/gpu/model_runner.py:1617) calls the ordinary target sampler when `num_draft_tokens==0`; otherwise it calls the rejection sampler. First-token divergence warrants inspecting target-side inputs/logits/state rather than assuming a later draft-block random draw caused it. The control does not directly record that first step's internal descriptor or logit tensor.

## Additional installed-source facts

The following files were read using standard-library filesystem operations inside the running baseline container `dsv41-h200-vllm-latency-2xdep4-sla-0`. Paths below are relative to its `/usr/local/lib/python3.12/dist-packages/vllm/`; no vLLM/Torch import or inference was performed.

- `entrypoints/openai/chat_completion/protocol.py:667–674,704` prioritizes an explicitly supplied temperature over defaults and forwards `seed`. SHA-256: `f23a9cb2ebc044fdfae3eef866ea7f8846d81d978f3f5303fa0d084fea97940e`.
- `v1/watermarking/gpu_sampler.py:42–46,63–75,112–114` explicitly bypasses watermarking for temperature zero and uses ordinary greedy sampling. SHA-256: `cb41d0e8a507af428bce714f4832b79520c966febb7433b09491892ba37a7255`. Draft counterpart `v1/watermarking/spec_decode.py:78` also disables watermarking at T0; SHA-256: `c2f7807bfbcea658c838c1fc39e35f734f258003880c98b644c4c2dd81ae90c5`.
- The container environment reported `VLLM_BATCH_INVARIANT` unset; `envs.py:634` defaults it to false. SHA-256: `efc45620a0e11d53040b8ac5019031408b21c5b30f0b605d03abbdd00586c064`. This was a container-exec environment read, not a dump of worker environments.
- `model_executor/layers/fused_moe/fused_moe.py:1118–1125,1305–1312` includes batch-dependent configuration selection and an optional fixed-tile/SPLIT_K1 mode. SHA-256: `21860340e4b409b01666e2ba0f0edae66b0f97b859756b174b573bab895cfaf7`. `model_executor/layers/fused_moe/router/fused_topk_bias_router.py:358–360` makes sorted top-k conditional on batch-invariant mode; SHA-256: `8cf50cf262bd0c2411fbcbf1d1ac47cfcf9320eefcb1e125f04ac27bdd432ba8`. These are source capabilities, not attestation that those exact branches executed for these requests.
- Model-specific `models/deepseek_v41/nvidia/model.py:175–178` selects deferred MoE finalization using token count; SHA-256: `1e73358b61b8135c11a5fcee9facbff33b438d6474d7436459b087a78f6e0a80`. `models/deepseek_v41/nvidia/flashmla.py:212–217` describes per-step planner metadata/num-splits and graph-reused allocations; SHA-256: `6bfcc91c278bae8f9c95d9ec4da12ef98112b9ccf9d22547743485759c258348`.

## Limits and handoff

Source offers mechanisms by which execution shape/state can matter and shows that an optional batch-invariance mode is not selected by the inspected launch environment. Neither observation proves the cause of these repeats. This control contains no paired logit tensors/top-two margins, request-state indices, per-layer numerical comparison, or complete per-request execution-shape identity. It cannot distinguish a baseline state/input defect from numerical or kernel execution effects. Absence of cached tokens also does not prove every internal buffer/cache was identical.

The established result is that exact prompt/seed/rank equality was insufficient for exact output repeatability on unchanged A. Request UUID randomness, watermark randomness, prefix-cache hits and “ordinary floating-point noise” must not be asserted as proven explanations. B remains frozen and unqualified; the independent evaluator owns any revised criterion and the diagnostic-first sequence. This source review makes no proposal to change the production environment, enable batch-invariant mode, loosen tensor assertions, or waive correctness.

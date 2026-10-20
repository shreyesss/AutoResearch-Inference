# Manual inspection

Local lexical ranking; dates are filters, not a scored recency bonus. BM25: lower is better. Top ten per query, not exhaustive.

## DeepSeek B200 fused_moe

Find model and device specific reports, configurations, and implementation references.

[Inspect interactively](http://localhost:8765/?q=DeepSeek+B200+fused_moe&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[Tracking] DeepGEMM SM 12.x kernel coverage gaps for DeepSeek-V4-Flash on consumer Blackwell (RTX 50 / GB10)](https://github.com/vllm-project/vllm/issues/41063) | open | 2026-09-24T16:30:07Z | -19.0850 |
| [[Bugfix] Disable FlashInfer autotune for trtllm_bf16_moe on SM100 during warmup to prevent TMA crash](https://github.com/vllm-project/vllm/pull/46238) | open | 2026-09-19T04:16:46Z | -18.6059 |
| [[Bug]: DeepGemm accuracy auto-disable (_DEEPGEMM_BLACKWELL_EXCLUDED_MODEL_TYPES) does not apply to the FP8 MoE path](https://github.com/vllm-project/vllm/issues/50332) | open | 2026-09-23T16:43:46Z | -18.1213 |
| [[Hardware][NVIDIA] Add GB10 fused-MoE fp8 tuning config (E=128, N=704 — Gemma 4 26B A4B)](https://github.com/vllm-project/vllm/pull/53394) | closed | 2026-09-09T15:25:20Z | -18.0619 |
| [[RFC]: support hopper FP8 MegaMoE backend for DeepSeek-V4](https://github.com/vllm-project/vllm/issues/42284) | closed | 2026-09-20T08:31:23Z | -16.3542 |
| [[Misc] Log FlashInfer JIT compilation on first kernel use](https://github.com/vllm-project/vllm/pull/54529) | closed | 2026-09-01T09:37:41Z | -14.0159 |
| [[Bugfix] Make Triton MoE reduction pad-aware under EP](https://github.com/vllm-project/vllm/pull/54083) | open | 2026-09-23T19:36:57Z | -13.9708 |
| [[Bugfix] DeepSeek-V4.1 VL: stream weights instead of sorting the iterator](https://github.com/vllm-project/vllm/pull/60291) | closed | 2026-10-06T22:26:21Z | -13.5925 |
| [[Model][Kernel] Nemotron-H Lightning NVFP4: batch-invariant serving aligned with training](https://github.com/vllm-project/vllm/pull/62017) | open | 2026-10-17T00:29:32Z | -13.1716 |
| [[Perf][SM120][MLA] Use compact FP8 KV rows for NoPE models](https://github.com/vllm-project/vllm/pull/58305) | open | 2026-10-19T17:41:12Z | -12.2405 |

## fused_moe grouped_gemm block_size_m

Locate low-M tile choices and grouped expert GEMM code.

[Inspect interactively](http://localhost:8765/?q=fused_moe+grouped_gemm+block_size_m&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[XPU] Add tuned int4_w4a16 fused-MoE config for Qwen3-30B-A3B-GPTQ-Int4 on Intel Arc Pro B70](https://github.com/vllm-project/vllm/pull/56788) | open | 2026-09-14T09:10:13Z | -19.2194 |

## fused_moe backend selection

Trace backend dispatch conditions and whether selection responds to runtime shape.

[Inspect interactively](http://localhost:8765/?q=fused_moe+backend+selection&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[Bugfix][LoRA] Respect moe_backend and guard fully-sharded LoRAs in MoE selection](https://github.com/vllm-project/vllm/pull/61301) | open | 2026-10-13T19:05:29Z | -15.6980 |
| [[Bug]: LoRA MoE backend selection ignores --moe-backend and the TRT-LLM LoRA path asserts with --fully-sharded-loras](https://github.com/vllm-project/vllm/issues/61286) | open | 2026-10-13T00:53:16Z | -15.5490 |
| [Refactor WNA16 MoE backend selection into oracle module](https://github.com/vllm-project/vllm/pull/39190) | closed | 2026-09-27T01:52:41Z | -15.0432 |
| [[MoE] Generalize unquantized backend fallback for all quantization-only backends (follow-up to #60219)         ](https://github.com/vllm-project/vllm/pull/56964) | open | 2026-10-15T06:10:31Z | -14.2126 |
| [[RFC]: Let Platforms customize fused MoE Router construction](https://github.com/vllm-project/vllm/issues/51005) | open | 2026-09-15T07:13:15Z | -13.9861 |
| [[Feature]: Consider B12X in automatic NVFP4 MoE backend selection on SM120/SM121 before the Marlin fallback](https://github.com/vllm-project/vllm/issues/54666) | open | 2026-09-01T02:02:35Z | -13.9243 |
| [[MoE][Quant] Consider B12X in automatic NVFP4 MoE backend selection](https://github.com/vllm-project/vllm/pull/54719) | open | 2026-09-02T03:09:10Z | -13.7785 |
| [[MoE] Allow a fused-MoE kernel to be rebuilt around resident weights](https://github.com/vllm-project/vllm/pull/57010) | open | 2026-09-17T09:39:41Z | -13.5665 |
| [[Quantization] Fix Humming MXFP4 activation selection for compressed tensors](https://github.com/vllm-project/vllm/pull/55963) | closed | 2026-10-05T14:47:52Z | -13.2948 |
| [[Kernel] Use FlashInfer CUDA BGMV MoE Kernel for Multi-LoRA MoE dispatch](https://github.com/vllm-project/vllm/pull/44147) | open | 2026-10-13T02:01:39Z | -12.8950 |

## MoE GEMM decode

Broader mechanism search for decode-specific expert matmul paths.

[Inspect interactively](http://localhost:8765/?q=MoE+GEMM+decode&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[Perf][DSv4.1] Keep activations MXFP8 between DeepGEMM kernels](https://github.com/vllm-project/vllm/pull/57977) | open | 2026-09-22T08:32:25Z | -22.4061 |
| [[Model][Experimental] DeepSeek V4 w4a4 MegaMoE support](https://github.com/vllm-project/vllm/pull/42844) | closed | 2026-09-26T01:50:26Z | -21.1630 |
| [[Perf] Warm up DeepGEMM MegaMoE kernels before serving](https://github.com/vllm-project/vllm/pull/60468) | merged | 2026-10-13T12:17:49Z | -20.8580 |
| [[Kernel] Integrate DeepGEMM NVFP4 MegaMoE with fused shared experts](https://github.com/vllm-project/vllm/pull/54520) | closed | 2026-10-09T09:56:03Z | -20.1796 |
| [[Model] Add Reflection Beam](https://github.com/vllm-project/vllm/pull/61978) | open | 2026-10-19T03:29:13Z | -20.0606 |
| [[Perf][DSV4.1] Prefer MegaMoE for supported local expert parallelism](https://github.com/vllm-project/vllm/pull/57220) | closed | 2026-09-21T08:18:50Z | -19.7937 |
| [[ROCm][DSv4] EPLB for the AITER MegaMoE backend](https://github.com/vllm-project/vllm/pull/61839) | open | 2026-10-18T14:57:31Z | -19.4174 |
| [[Perf][DSV4.1] Optimize MegaMoE staging and NVFP4 cache gathers](https://github.com/vllm-project/vllm/pull/57604) | merged | 2026-09-18T19:57:22Z | -19.1527 |
| [[Perf][DSV4.1] Pad shared experts for native MegaMoE fusion](https://github.com/vllm-project/vllm/pull/56568) | merged | 2026-09-16T09:08:43Z | -19.0687 |
| [[Perf][EPLB][DSv4] Add a symm_mem weight-migration backend and fuse MegaMoE replica mapping](https://github.com/vllm-project/vllm/pull/62009) | open | 2026-10-19T07:30:50Z | -19.0619 |

## DeepSeek TPOT B200

Find measurements tied to the target workload and hardware.

[Inspect interactively](http://localhost:8765/?q=DeepSeek+TPOT+B200&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[Kernel][Perf] Add H100 tuned configs for Llama-3.1-8B and Qwen3-8B to the batch-invariant matmul table](https://github.com/vllm-project/vllm/pull/62219) | open | 2026-10-19T15:39:41Z | -34.6871 |
| [[Hardware][NVIDIA] Add GB10 fused-MoE fp8 tuning config (E=128, N=704 — Gemma 4 26B A4B)](https://github.com/vllm-project/vllm/pull/53394) | closed | 2026-09-09T15:25:20Z | -24.2314 |
| [[Perf][DSV4.1] Enable the fused all-reduce + mHC boundary at TP2](https://github.com/vllm-project/vllm/pull/60355) | open | 2026-10-07T06:07:50Z | -23.0045 |
| [[DCP] Add FlashInfer fused A2A backend for decode context parallelism](https://github.com/vllm-project/vllm/pull/48248) | open | 2026-09-03T21:11:53Z | -22.7092 |
| [[Perf][DSv4.1] Restore the fused query RMSNorm + MXFP8 quantization path](https://github.com/vllm-project/vllm/pull/57679) | merged | 2026-09-25T01:39:04Z | -20.3887 |
| [[Bug]: DeepGemm accuracy auto-disable (_DEEPGEMM_BLACKWELL_EXCLUDED_MODEL_TYPES) does not apply to the FP8 MoE path](https://github.com/vllm-project/vllm/issues/50332) | open | 2026-09-23T16:43:46Z | -19.5746 |
| [[Perf][DSv4.1] Small-head sparse decode on SM90](https://github.com/vllm-project/vllm/pull/59418) | open | 2026-10-15T01:30:05Z | -19.4766 |
| [[Attention] Portable Triton sparse-MLA fallback for SM12x (consumer Blackwell)](https://github.com/vllm-project/vllm/pull/54929) | open | 2026-10-11T16:16:14Z | -19.1345 |
| [[Perf][DSv4.1] Gather the compressed KV once per KV-source group in prefill](https://github.com/vllm-project/vllm/pull/59131) | open | 2026-09-29T03:57:51Z | -18.8651 |
| [[Kernel] MXFP4 indexer cache for GLM-5.2 / DSA (glm_moe_dsa)](https://github.com/vllm-project/vllm/pull/48558) | open | 2026-10-12T20:37:31Z | -18.8205 |

## CUDA graph capture fused_moe

Inspect graph compatibility, capture boundaries, and replay behavior.

[Inspect interactively](http://localhost:8765/?q=CUDA+graph+capture+fused_moe&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [tests/kernels/moe/test_flashinfer_moe_ep.py](https://github.com/vllm-project/vllm/blob/86a5bbe75a7971275952477bb1ce03e715bcc339/tests%2Fkernels%2Fmoe%2Ftest_flashinfer_moe_ep.py) | None | 2026-10-19T20:28:36Z | -15.5951 |
| [[Bug]: Xid 31 MMU fault under load in multi-node Expert-Parallel (EP16) CUDA-graph replay (fused-MoE FP8 reduce_scatterv) — --enforce-eager clean](https://github.com/vllm-project/vllm/issues/59607) | open | 2026-10-01T13:57:34Z | -15.5475 |
| [[Elastic EP] Reuse CUDA graphs across reconfiguration](https://github.com/vllm-project/vllm/pull/54985) | merged | 2026-09-12T14:26:39Z | -14.6030 |
| [[Bugfix][LoRA] Fall back for high-rank MoE LoRA](https://github.com/vllm-project/vllm/pull/55161) | merged | 2026-10-02T11:17:12Z | -14.2082 |
| [[Bug]: CUDA graphs deadlock fully-sharded fused-MoE LoRA across TP ranks](https://github.com/vllm-project/vllm/issues/60845) | open | 2026-10-13T06:32:37Z | -13.8563 |
| [[Bugfix][LoRA] Disable shared-expert aux stream with fully-sharded LoRA](https://github.com/vllm-project/vllm/pull/61284) | open | 2026-10-17T22:53:11Z | -13.8094 |
| [fix(flashinfer): guard trtllm MoE behind x86_64 check](https://github.com/vllm-project/vllm/pull/46917) | open | 2026-09-29T01:54:58Z | -13.8043 |
| [[Bugfix][Hardware][AMD] Handle AITER unified-attention LDS overflow with Triton fallback](https://github.com/vllm-project/vllm/pull/49264) | open | 2026-10-15T02:21:39Z | -13.6376 |
| [[ROCm][Bugfix] Disable cudagraph for AITER MXFP4xMXFP4 MoE (graph-unsafe decode corruption)](https://github.com/vllm-project/vllm/pull/44988) | closed | 2026-09-15T00:17:44Z | -13.5986 |
| [[Test] Refactored the routed-experts replay tests](https://github.com/vllm-project/vllm/pull/52902) | open | 2026-10-01T11:01:28Z | -13.0116 |

## decode launch overhead MoE

Find evidence that per-step launches or dispatch contribute to latency.

[Inspect interactively](http://localhost:8765/?q=decode+launch+overhead+MoE&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[Perf][DSV4.1] Optimize MegaMoE staging and NVFP4 cache gathers](https://github.com/vllm-project/vllm/pull/57604) | merged | 2026-09-18T19:57:22Z | -23.8995 |
| [[MoE] Optimize fused MoE token alignment and adaptive block size for fine-grained experts](https://github.com/vllm-project/vllm/pull/55225) | closed | 2026-10-07T22:43:03Z | -19.5270 |
| [[Benchmark] Add vllm bench forward: exact-shape forward timing](https://github.com/vllm-project/vllm/pull/61339) | merged | 2026-10-14T17:52:30Z | -19.0895 |
| [optimized batched MoE token alignment kernel](https://github.com/vllm-project/vllm/pull/56383) | open | 2026-09-14T01:29:55Z | -15.9747 |
| [[ROCm] Optimize MiniMax-M3 SwiGLU activation with prefill-gated clamp…](https://github.com/vllm-project/vllm/pull/59760) | open | 2026-10-02T09:25:09Z | -15.0539 |
| [[ROCm][Perf][DSv4.1] Tune MoRI decode dispatch grid and MXFP8 block32 packed cutoff on MI355X](https://github.com/vllm-project/vllm/pull/62335) | closed | 2026-10-18T21:15:08Z | -14.8545 |
| [[Kernel] Add fused routing and scatter-reduce decode optimizations for BS<=64 for GPT-OSS](https://github.com/vllm-project/vllm/pull/39714) | closed | 2026-09-08T01:46:44Z | -14.7859 |
| [[ROCm][Perf][MiniMax-M3] Fused sparse-layer decode via AITER](https://github.com/vllm-project/vllm/pull/59653) | open | 2026-10-10T02:24:36Z | -14.6884 |
| [[Bug/Perf] DeepSeek-V4.1-Flash on SM120 (RTX PRO 6000 Blackwell, 8xTP): extremely low decode throughput with --enforce-eager; CUDA graphs unusable — please prioritize SM120 graph capture fix](https://github.com/vllm-project/vllm/issues/56892) | open | 2026-10-18T03:25:24Z | -14.6677 |
| [[Perf][Kernel] Integrate Mega-mHC from DeepGEMM for DeepSeek V4.1  (reopen of #56255)](https://github.com/vllm-project/vllm/pull/56962) | merged | 2026-09-15T17:35:11Z | -14.3670 |

## fused_moe fallback regression

Seek counterevidence: fallbacks, regressions, and cases where a faster kernel loses end-to-end.

[Inspect interactively](http://localhost:8765/?q=fused_moe+fallback+regression&match=all&after=2026-09-01)

| Source | State | Updated | BM25 |
|---|---|---|---|
| [[ROCm][Bugfix] add swiglustep triton fallback](https://github.com/vllm-project/vllm/pull/39436) | closed | 2026-09-27T01:52:11Z | -12.5832 |
| [[Feature]: [ROCm][AITER] Track relu2 (non-gated) MoE activation enablement (Tier 3, vLLM-side integration)](https://github.com/vllm-project/vllm/issues/59155) | open | 2026-09-29T07:08:35Z | -12.3908 |
| [[Bug]: MoE LoRA one-shot path rejects max_lora_rank=256 although LoRAConfig accepts it](https://github.com/vllm-project/vllm/issues/55158) | closed | 2026-10-02T10:59:30Z | -12.1703 |
| [[ModelOpt] Support fused MoE weight reload](https://github.com/vllm-project/vllm/pull/53741) | open | 2026-10-18T06:22:00Z | -12.0400 |
| [[Bug]: CPU MXFP4 MoE (gpt-oss) broken on AMD EPYC after AMX gate ](https://github.com/vllm-project/vllm/issues/61027) | open | 2026-10-10T20:20:13Z | -11.8359 |
| [[Bugfix][ROCm][MoE] Fix AITER MoE routing fallback to eager torch.topk for scoring_func=softmax](https://github.com/vllm-project/vllm/pull/57246) | open | 2026-09-17T07:31:04Z | -11.7592 |
| [[Bugfix][ROCm] Fix channelwise GPTQ MoE fallback](https://github.com/vllm-project/vllm/pull/58513) | open | 2026-09-24T06:16:12Z | -11.4665 |
| [[MoE] Optimize fused MoE token alignment and adaptive block size for fine-grained experts](https://github.com/vllm-project/vllm/pull/55225) | closed | 2026-10-07T22:43:03Z | -11.1781 |
| [[Test Coverage] Add tests for MoE dispatch and Triton qzeros reshape](https://github.com/vllm-project/vllm/pull/53643) | open | 2026-09-11T01:55:08Z | -11.1404 |
| [[Bugfix][Hardware][AMD] Handle AITER unified-attention LDS overflow with Triton fallback](https://github.com/vllm-project/vllm/pull/49264) | open | 2026-10-15T02:21:39Z | -10.9797 |

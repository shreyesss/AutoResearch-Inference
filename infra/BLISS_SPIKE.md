# BLIS feasibility spike — 18 October 2026

## Verdict

BLIS can replay the request timing and token counts from our AIPerf runs in milliseconds of CPU time. **It cannot yet predict our Qwen3.8-27B on RTX PRO 6000 Blackwell results.** The compatible BLIS catalog contains neither this model nor this GPU, and the fitted registry has no coefficients for this pair. A surrogate replay is a transport proof, not a calibrated performance result.

BLIS does not remove our measured ~22.5 minutes of four vLLM startups. Its standard serving simulation assumes deployed instances; BLIS's observation guide explicitly separates prewarming from measurement and excludes cold-start effects. We could avoid repeated startup by reusing a server for several workloads at one configuration, but that is a change to our real evaluator, not a benefit provided by BLIS. That change would need isolation checks for KV state, compilation, and order effects.

## What ran locally

- Cloned `inference-sim/inference-sim` at `63ffc02`, `blis-catalog` tag `0.2.1` at `28e82d4`, and `blis-registry` tag `v0.1.1` at `f7519b1` under ignored `.artifacts/blis-spike/`.
- Installed Go 1.24.10 locally under that ignored directory, verifying the official SHA-256. Built the BLIS executable and ran its example scenario successfully, CPU only.
- Converted all **307** completed OPS4 B0 chat requests from the existing `normalized-requests.jsonl` into a TraceV2 CSV. Preserved **actual AIPerf dispatch time**, **observed input tokens**, and **observed output tokens**, as well as observed first/last-token times for comparison. BLIS replay completed all 307 records with a Llama-3.1-70B/H200 **surrogate** scenario. Output: `.artifacts/blis-spike/ops4-chat-surrogate-replay.log`; source trace: `.artifacts/blis-spike/ops4-chat-trace.{yaml,csv}`.
- The surrogate printed 595.20 output tokens/s, TTFT p99 113.81 ms, ITL p99 37.81 ms. **Do not compare those values as predictions** against OPS4 Qwen B0 (564.39 output tokens/s, TTFT p99 310.07 ms, TPOT p99 55.01 ms): the model, GPU, tensor parallelism, precision, and serving settings differ. BLIS ITL also needs metric-definition alignment with our AIPerf TPOT.

## What parity would require

1. Add the **exact pinned Qwen/Qwen3.8-27B** architecture graph and the **RTX PRO 6000 Blackwell Server Edition** hardware facts to a pinned local BLIS catalog. The local model config reports `model_type: qwen3_5` with a hybrid architecture; reusing the catalog's Qwen3.5-397B MoE graph would be incorrect.
2. Add or fit the latency-kernel coefficients applicable to the GPU, precision, and vLLM path. A nearby B200 is not the same device. Set BLIS scenario settings to our vLLM 0.28.0, BF16, TP1, 40960-token context, batch limits, KV/cache settings, and MTP state where representable. The example scenario uses vLLM 0.29.0 and FP8 TP4.
3. Convert the **same frozen request stream** for each task. Use actual dispatch timestamps for descriptive replay and scheduled timestamps separately when asking whether the load generator introduced lag. Preserve actual token lengths. Do not use BLIS's synthetic arrivals when claiming AIPerf parity.
4. Compare per-request TTFT and E2E distributions, output throughput, completed counts, and queue/saturation behavior on at least B0 and one changed serving config. Check errors by workload and load, including long prompts and tail behavior. Only then consider BLIS as a negative screen; never let an uncalibrated simulator replace GPU confirmation.

## Sources

- [BLIS repository and current install/replay contract](https://github.com/inference-sim/inference-sim)
- [BLIS catalog](https://github.com/inference-sim/blis-catalog)
- [BLIS registry](https://github.com/inference-sim/blis-registry)
- [BLIS replay/observe documentation](https://inference-sim.github.io/inference-sim/latest/guide/observe-replay-calibrate/)

The local clone is more specific than the web documentation when versions differ. This spike uses the pinned repository versions above.

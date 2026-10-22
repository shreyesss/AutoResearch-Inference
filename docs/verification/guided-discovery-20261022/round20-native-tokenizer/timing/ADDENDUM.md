# Round20 addendum — bounded CPU headroom, not serving ROI

## Decision-changing result

**Incremental repair is useful only in some of the tested CPU routes.** For ordinary text, the already-available native full encoder beat this Python repair wrapper at every tested length. For long strict appends containing a recognized added token, native full encoding intentionally falls back to the reference across the whole text; repairing only the suffix avoids most of that work. Rendered rewrites provide no incremental win in this conservative wrapper.

Preserve S01 as the same bounded investigation. Do not promote a general session cache or infer an ITL improvement. The next practical gate is actual endpoint prefix reuse/added-token/fallback exposure and exact loader state, followed by the production native append/session boundary. A fast standalone native full encoder is a competing simpler intervention, subject to the same target admission requirements.

## Executed method

- Same exact ARM/macOS release binary and target artifact as frozen round20 correctness; no source/registry changes or GPU imports.
- 72 synthetic requests: four growing prefix character lengths × three workload categories × six distinct generated requests. Deterministic seed 201017. Prefix lengths are **characters, not model tokens**; observed tokens appear below.
- Every arm warmed twice per request; seven measured repeats with randomized arm order. Report request medians, then medians across six requests. Paired saving uses the mean of six request-median differences. CIs bootstrap those six request differences 2,000 times. These describe this small synthetic sample, not a deployment population or service forecast.
- `repair`: conservative adapter checks whether current rendered text begins with previous text, then calls unmodified Python repair using the native CPU suffix encoder. The adapter's prefix comparison, delta slicing, repair text/list construction and output materialization are timed.
- `repair_copy_inputs`: additionally copies the cached ID and span lists before repair. This is a sensitivity arm, **not evidence that the actual public session runtime makes these copies**. Existing output list reconstruction is already timed in the base arm.
- Full native and HF ID-only baselines return token IDs without offsets. Repair returns IDs **and** offsets and thus does more output work; this is a relevant simpler-baseline comparison, not matched-output kernel speedup. The retained `hf_full_offsets` arm provides a reference baseline returning both IDs and offsets.
- Current rendered string and valid previous state are prepared before all timers. First cache population, rendering, imports/build, session-store/persistence/lookup, request queueing and network are excluded. The experiment explicitly assumes a warm available prior state. It does not estimate cache-hit probability or cold cost.
- All measured outputs passed exact ID checks; all arms that return offsets passed exact offsets. No native session store/facade was instantiated. No CPU core affinity/frequency or host background-load control was applied.

## Measured milliseconds

Positive paired saving means repair is faster than native full encoding. All time columns are medians of request medians, whereas the final column is the mean paired difference with its bootstrap interval.

| Prefix chars | Workload | Median old tokens | Repair | Repair + input copy | Native full IDs | HF full IDs | Paired ms saved vs native [95% descriptive CI] |
|---:|---|---:|---:|---:|---:|---:|---|
| 1,024 | plain_append | 220 | 0.163 | 0.164 | 0.006 | 0.192 | -0.158 [-0.161, -0.154] |
| 1,024 | added_literal_append | 218 | 0.238 | 0.240 | 0.143 | 0.186 | -0.093 [-0.096, -0.090] |
| 1,024 | rendered_rewrite | 254 | 0.222 | 0.215 | 0.172 | 0.212 | -0.052 [-0.055, -0.049] |
| 8,192 | plain_append | 1730 | 0.240 | 0.248 | 0.039 | 1.421 | -0.201 [-0.207, -0.195] |
| 8,192 | added_literal_append | 1743 | 0.320 | 0.328 | 1.119 | 1.446 | +0.793 [+0.765, +0.822] |
| 8,192 | rendered_rewrite | 1780 | 1.527 | 1.506 | 1.149 | 1.479 | -0.372 [-0.397, -0.346] |
| 32,768 | plain_append | 6942 | 0.492 | 0.532 | 0.155 | 5.795 | -0.347 [-0.362, -0.335] |
| 32,768 | added_literal_append | 6936 | 0.602 | 0.603 | 4.478 | 5.745 | +3.877 [+3.838, +3.917] |
| 32,768 | rendered_rewrite | 7009 | 6.031 | 6.042 | 4.519 | 5.804 | -1.513 [-1.563, -1.472] |
| 131,072 | plain_append | 27700 | 1.551 | 1.712 | 0.670 | 24.730 | -0.897 [-0.947, -0.859] |
| 131,072 | added_literal_append | 27716 | 1.644 | 1.813 | 18.345 | 24.073 | +16.739 [+16.563, +16.929] |
| 131,072 | rendered_rewrite | 27928 | 25.449 | 25.437 | 18.561 | 24.519 | -6.855 [-7.014, -6.717] |

## Why these outcomes differ

- **Plain append:** every measured native suffix/full call used Gigatoken. At the largest size, native full encoding was ~0.67 ms while repair was ~1.55 ms. The Python algorithm scans prior spans in `_build_records` and reconstructs output lists (`gigatoken.py:214–238, 433–497`); this establishes linear wrapper work exists, not a measured attribution of all latency. A native Rust append path may behave differently and was not tested.
- **Added-literal append:** the delta completes `<｜System｜>`. Every measured native suffix and native full call intentionally used `hf_full_added_token`. Repair still saves work by limiting the reference call to a short suffix. At ~32k characters, paired saving versus native full was ~3.88 ms; at ~131k characters, ~16.74 ms. No case is presented as raw Gigatoken support for that literal.
- **Rendered rewrite:** the exact pinned renderer with `thinking_mode=thinking, drop_thinking=True` changes a previous suffix. The adapter correctly rejects append reuse and runs full HF reference, including offsets. It does not outperform whole native encoding, which also reference-falls back on rendered added tokens but uses its own ID-only path. That difference is not a tokenizer correctness regression.
- **Copy sensitivity:** at ~131k characters, explicit prior-list copying increased plain repair ~0.16 ms and added-token repair ~0.17 ms in this run. This cannot substitute for measuring the actual native session container and output-consumer API.

Each cell has 42 measured calls per arm. Native repair routes were 42 `gigatoken_full` for plain appends, 42 `hf_full_added_token` for added-token appends, and zero native calls for rendered-rewrite fallback. Full-native routes are retained separately in `timing.json`. Native reference fallbacks are never counted as native-core speedups.

## Reproduction and limits

```sh
../venv312/bin/python cpu_timing.py
```

`cpu_timing.py` executes only the initialization prefix of the frozen `native_probe.py`, whose SHA is recorded; it does not run or overwrite the correctness output. The native engine is passed directly to repair, avoiding the earlier per-window Python statistics wrapper in timed sections. Route counters are captured outside timers. `requests.json` retains exact generated inputs; `timing.json` retains every timing sample and route. The original correctness manifest remains unchanged.

This result justifies selective CPU follow-up on long, append-stable rendered input that triggers full reference fallback. It does **not** establish that agent-p75/Mooncake exposes such reusable sessions, that the deployed tokenizer uses this route, that the registry should admit the target, or that TTFT/ITL/goodput changes by the same number of milliseconds.

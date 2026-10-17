# Qwen serving autoresearch — executive summary

**Status, 17 October 2026:** B0 load calibration and a bounded manual serving-parameter comparison are complete. Two MTP settings showed repeatable decode/throughput gains with a TTFT cost. Real autonomous search is **not yet qualified**.

## Fixed evaluation

| Item | Locked value |
|---|---|
| Target | `Qwen/Qwen3.8-27B` revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`; one RTX PRO 6000 Blackwell; vLLM `0.28.0` image digest `sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14`; AIPerf `0.13.0` |
| Request policy | Streaming, non-thinking chat; temperature 0; 511–514 actual input tokens; forced 256 output tokens; independent synthetic text. **The mixed and bursty YAMLs were not evaluated here.** |
| Ordinary load | 154 fixed requests at **2.56 requests/s**, one every 390.625 ms over about 60 s |
| Busy load | 192 fixed requests at **3.2 requests/s**, one every 312.5 ms over about 60 s |
| Comparability | Exact prompt text, output controls and timestamps frozen in [input manifest](infra/b0-frozen-inputs-manifest.json); fresh server per configuration run; same disjoint three-request warmup and 2.56 → 3.2 cell order |

## Baseline and proposed search parameters

| Serving parameter | B0 resolved value | Handoff's proposed probes | Evaluated here |
|---|---:|---|---|
| `max_num_seqs` | **512** (1024 failed model boot) | 8, 16, 32, 64, 128 | 32, 128 |
| `max_num_batched_tokens` | 8192 | 2048, 4096, 8192, 16384 | B0 only |
| `gpu_memory_utilization` | **0.92** | 0.85, 0.90, 0.93 | B0 only |
| Prefix cache | On | Off, on | B0 only |
| MTP speculative depth | 0/off | 0, 1, 2, 3, 5 | 0, 1, 3 |
| CUDA graphs | On | Conditional, no frozen values | B0 only |

The numeric list is in the handoff [DECISIONS.md](inference-autoresearch-handoff/DECISIONS.md), **not** its README. It is a proposed probe list, not a validated active search space; it omits B0's sequence cap 512 and memory fraction 0.92. The engine must retain exact B0 and exclude or flag settings that cannot carry the fixed offered load. B0 ran up to 37/53 concurrent requests at the two loads, so cap 32 was predictably too low. On this short-chat card KV usage peaked around 22%/31% and prefix-cache hits were zero; memory-fraction and cache toggles have no demonstrated headroom here.

## Matched-load evaluations

Ranges span fresh-server runs. TTFT and TPOT columns are **p50 / observed sample p99**; times are ms and TPOT is ms/token. Output tokens/s includes drain. `Qmax` is the maximum server waiting queue. All **20 timed cells / 3,460 requests** returned HTTP 200 with complete exports; actual start offsets matched frozen schedules within 3 ms.

| Load | Configuration (runs) | TTFT p50 / p99 | TPOT p50 / p99 | Output tok/s | Qmax | Finding |
|---|---|---|---|---:|---:|---|
| 2.56 | **B0** (3) | 179–186 / 210–211 | 55.7–55.8 / 56.0–56.1 | 556.3–556.5 | 0 | Reference |
| 2.56 | Cap 32 (2) | 2367–2440 / 5273–5381 | 53.5–53.6 / 53.5–53.6 | 519.4–520.1 | 12–13 | Capacity queue; reject |
| 2.56 | Cap 128 (1) | 184 / 209 | 55.7 / 56.0 | 556.3 | 0 | Flat against B0 |
| 2.56 | MTP 1 (2) | 193–194 / 220 | 32.8 / 34.9–35.5 | 592.6–593.9 | 0 | Decode gain, TTFT cost |
| 2.56 | MTP 3 (2) | 210–211 / 240–252 | 25.0–25.2 / 29.1–29.2 | 604.5 | 0 | Larger decode gain, larger TTFT cost |
| 3.2 | **B0** (3) | 190–195 / 224–226 | 62.6–62.8 / 63.8–63.9 | 689.1–689.2 | 0 | Reference |
| 3.2 | Cap 32 (2) | 9189–9260 / 19113–19255 | 53.5–53.6 / 53.5–53.6 | 546.1–547.1 | 48 | Capacity queue; reject |
| 3.2 | Cap 128 (1) | 195 / 223 | 62.7 / 63.9 | 689.2 | 0 | Flat against B0 |
| 3.2 | MTP 1 (2) | 202 / 233 | 37.1–37.2 / 39.5–39.7 | 738.2–740.0 | 0 | Decode gain, TTFT cost |
| 3.2 | MTP 3 (2) | 222–223 / 258–261 | 28.3–28.5 / 32.4–32.9 | 757.5–758.4 | 0 | Larger decode gain, larger TTFT cost |

**Decision:** MTP 1 and 3 are repeatable point-estimate tradeoffs; neither improves all three objectives over B0. At 3.2 requests/s, MTP 1 reduced TPOT p50 about 41% and increased finite-run output rate about 7%; MTP 3 reduced TPOT about 55% and increased output rate about 10%. TTFT worsened in both. The 60-second samples do **not** certify p99 SLA, maximum sustainable capacity, answer quality, or production benefit. Forced-length synthetic chat must be followed by meaningful semantic, mixed, and session evaluations.

**Next checkpoint:** build the input and evaluation engines using the frozen workload hashes, exact B0/candidate settings, single-GPU lifecycle, raw request accounting, queue/overload labels, and matched-load objective vector. Keep autonomous search gated until representative workloads, semantic MTP checks, cache protocol, and tail precision are qualified. Detailed evidence: [B0 calibration](infra/B0_LOAD_CALIBRATION.md), [cap pilot](infra/SEQUENCE_CAP_SENSITIVITY_PILOT.md), [manual comparison](infra/MANUAL_SERVING_SEARCH.md), [cell results](infra/manual-serving-search-results.json).

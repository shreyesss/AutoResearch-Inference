# B0 diagnostic load calibration

Run date: 17 October 2026 UTC. This is a bounded, real Qwen/vLLM/AIPerf screen, not an SLA certification or a production traffic estimate. The exact commands and raw records are in `.artifacts/b0-load-curve/`; [b0-load-curve-summary.json](b0-load-curve-summary.json) hashes the raw and per-request exports. [b0-load-policy.json](b0-load-policy.json) records the provisional freeze decision.

## What was held fixed

B0 served pinned `Qwen/Qwen3.8-27B` revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` on one NVIDIA RTX PRO 6000 Blackwell Server Edition using `vllm/vllm-openai:v0.28.0` digest `sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14`. Explicit settings were TP1, BF16, `max_model_len=40960`, `max_num_seqs=512`, and Qwen3 reasoning parser. Resolved logs showed chunked prefill, `max_num_batched_tokens=8192`, prefix caching, CUDA graphs, and default GPU memory utilization 0.92. The default 1024 sequence cap had failed the prior boot on this hybrid Mamba model; 512 is the documented B0 feasibility override, not a setting chosen for performance.

The primary card used AIPerf 0.13.0 streaming chat, non-thinking Qwen template, temperature zero, `ignore_eos` plus 256 minimum output tokens, and constant open-loop arrivals. AIPerf input target 552 realized 511–514 server prompt tokens; all measured outputs were exactly 256 tokens. One disjoint three-request first-use warmup ran before timed cells. Each cell used a unique seed; all request bodies were unique within cells and no exact body hash overlapped across cells. The same server stayed up across cells, with no cache reset. Common template prefixes may still be warm. The client concurrency cap was 256 through 3.2 requests/s and 512 at 4.8/6.4; observed in-flight work stayed below those caps. Sending windows were about 60 seconds, with a 70-second benchmark-duration cap and 60-second drain grace.

## Observed curve

All cells had complete AIPerf artifacts, all planned records, HTTP 200, exact 256-token outputs, and p99 credit-to-dispatch lag below 1 ms. The table's latency p99 values are **observed sample quantiles**, not precision-qualified SLA estimates. Output tokens/s uses first planned dispatch through the last terminal response, including drain.

TPOT here is AIPerf's **per-request** inter-token latency. For every successful record, it matched `(request_latency - TTFT) / (server completion tokens - 1)` within numerical precision; the first streamed content chunk represented one token. This is a p99 across request-level decode averages, not a p99 of individual stream gaps. All failed/censored counts were zero in these cells, but the analyzer retains their accounting.

| Offered requests/s | Requests | TTFT p50 / observed p99 ms | TPOT p50 / observed p99 ms/token | Output tokens/s | Outstanding work in last three 10 s send bins |
|---:|---:|---:|---:|---:|---|
| 0.2 | 12 | 164 / 176 | 39.3 / 39.4 | 47 | 3, 2, 2 |
| 0.4 | 24 | 160 / 181 | 40.2 / 40.3 | 91 | 4, 4, 4 |
| 0.8 | 48 | 162 / 180 | 41.3 / 41.3 | 179 | 8, 8, 8 |
| 1.6 | 96 | 177 / 195 | 47.9 / 47.9 | 352 | 20, 20, 19 |
| **2.56** | **154** | **187 / 211** | **55.8 / 56.3** | **556** | **37, 38, 37** |
| **3.2** | **192** | **195 / 226** | **62.7 / 63.9** | **689** | **53, 53, 52** |
| **3.2 repeat** | **192** | **195 / 226** | **62.8 / 63.9** | **689** | **53, 52, 52** |
| 4.8 | 288 | 237 / 289 | 88.6 / 99.1 | 999 | 113, 120, 122 |
| 6.4 | 384 | 1603 / 13321 | 125.8 / 141.4 | 1100 | 201, 221, 231 |

The 3.2 requests/s point sustained matched starts and completions after fill in two separate windows with different prompt seeds. At 4.8, completions approached starts late but outstanding work still grew; this 60-second run does not prove long-run stability. At 6.4, backlog rose throughout and TTFT deteriorated sharply despite eventual HTTP 200 completion. Thus **3.2 requests/s is a conservative provisional B0 reference for this fixed card**, not a measured global capacity ceiling. More throughput at 4.8/6.4 includes work completed during drain and must not be mistaken for sustainable offered capacity.

The first proposed ordinary screen is **2.56 requests/s**, 80% of the provisional reference; its separate B0 cell completed and leveled near 37–38 outstanding. The handoff's initial finalist ladder would be **1.92, 2.56, 3.2, 3.84 requests/s** (60/80/100/120%). The 1.92 and 3.84 cells have not been materialized or measured; 3.84 is a stress side of the ladder, not certified sustainable. These numbers belong to this 512/256 card only. A 60-second run and these request counts cannot certify p99 tails, long-run stationarity, or a user SLA.

## Other input configurations checked

The [mixed-prefill-control.json](mixed-prefill-control.json) adapts the Deepseek_serve paired-length idea to Qwen as a **mechanism diagnostic**: intended 512/256, 2048/512, and 8192/512 prompt/output pairs with configured weights 60/25/15. The 0.5 requests/s, 30-request probe realized 20 short prompts at 511–513 tokens, six medium at 2048–2049, and four long at 8192. All 30 returned HTTP 200 and reached their requested 256/512 output lengths. Median TTFT by arm was approximately 174, 401, and 1350 ms. Those weights are design assumptions, not a source-derived deployment mixture; 30 requests do not establish mixed capacity or tails.

The earlier [WORKLOAD_CONTROL_MATRIX.md](WORKLOAD_CONTROL_MATRIX.md) already validated a four-turn TraceLab dependency replay, six three-turn Mooncake prefix/burst replay, and five SpecBench semantic prompts. They check input topology and meaning, but are too small or differently timed to substitute for this sustained independent-request load curve. The Deepseek_serve B200/DeepSeek thinking options, SLOs, and 45/20/15/20 mix were not adopted as Qwen production truth.

## Freeze boundary before autoresearch

The workload generation/shape policy, model/template, output behavior, arrival family, warm/cache protocol, metric definitions, and B0 serving settings were fixed before B0 calibration. Exact payloads for the selected loads were frozen afterward from the measured raw requests. **Absolute offered rates are chosen from B0 evidence and then frozen identically for B0 and every candidate.** Client request rate and concurrency are workload controls, not Codex serving-parameter proposals. Actual starts, completions, prompt/output tokens, and cache effects remain measured outcomes.

This checkpoint freezes a **provisional diagnostic load policy**, not a full search-ready suite. The measured 2.56 and 3.2 cells were materialized as [native single-turn assets](b0-frozen-inputs-manifest.json) with exact prompt text, output caps and fixed millisecond timestamps; their source raw-export hashes are recorded. A new B0 server replayed both assets after disjoint warmup. [Row-by-row validation](b0-frozen-replay-validation.json) found 154/154 and 192/192 HTTP 200; every actual prompt and output control matched its frozen row, target prompt counts remained 511–514, and maximum absolute start-offset errors were 2.173 and 2.262 ms. The frozen 2.56/3.2 runs repeated median TTFT of 183/195 ms, median TPOT of 55.8/62.7 ms/token, and finite-run output rates of 556/689 tokens/s. Their last three 10-second bins again held outstanding work near 37–38 and 52–53.

Before qualified candidate comparison, establish a matched repeated-window/cache preparation protocol and calibrate any mixed or session card separately. Representative mixture proportions, hybrid cache reset behavior, long-run/tail precision, and Qwen-specific SLA thresholds remain unresolved. The 1.92/3.84 finalist ladder assets are not yet materialized. Dependent sessions must be controlled by session-start rate or active population; their later turns naturally shift when target response times change.

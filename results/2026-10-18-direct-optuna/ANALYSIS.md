# Direct Optuna search: findings and confirmation status

[Side-by-side development, held-out and baseline comparison](comparison.html)

## Final held-out result — 19 October 2026, 01:43 IST

**Confirmation finished: 5/5 configurations, 15/15 points, 1,800/1,800 valid requests, zero failed trials.** Together with search: 7,800 measured requests (plus 168 calibration requests).

The 10% throughput gain for search trial 9 **did not reproduce** on held-out inputs. Search trial 10 is the strongest remaining latency lead.

At 32 concurrent clients, 120 held-out requests per run:

| Original search configuration | Output tokens/s | p90 TTFT seconds | p90 TPOT ms/token |
|---|---:|---:|---:|
| B0 before | 384.39 | 6.697 | 66.00 |
| Trial 9 | 383.86 | 6.759 | 68.53 |
| Trial 10 | 387.48 | 4.437 | 68.18 |
| Trial 24 | 273.43 | 27.292 | 52.76 |
| B0 after | 386.65 | 6.263 | 67.33 |

Trial 10 reduced p90 TTFT by **29–34% against both baseline runs**, with throughput within 1% and TPOT **1.3–3.3% worse**. It changed batched tokens 8192→4096, max sequences 512→64, GPU memory fraction .92→.95. All other settings matched B0. At 16 clients it also improved TTFT (2.456s vs B0 3.179/2.893s); at 64 clients the difference was smaller (13.523s vs 14.288/13.985s). This is evidence of a latency tradeoff that carries over to held-out prompts, not a universal win or proof of statistical significance. There was only one held-out run of each candidate and two B0 runs.

Trial 9 has essentially baseline throughput at 32 clients, worse TPOT, and no meaningful TTFT gain. At 64 its throughput is only 0.8–1.8% above the two baselines. The original +10% result should not be used as a claimed optimization win.

Trial 24 again buys faster decode with much worse queueing: p90 TTFT reaches 66.99s at 64 clients. It is unsuitable for the service goals.

## Graphs and data

- [Held-out operating curves](heldout-operating-curves.svg) and [held-out Pareto](heldout-pareto.svg): B0 before/after and the three frozen finalists, using original search labels.
- [Development TTFT–TPOT frontier](ttft-tpot-pareto.svg) and [p50/p90/p99](ttft-tpot-percentiles.svg): exploratory development observations, not the held-out frontier.
- [All point records](points.csv), [per-class records](class-points.csv), [side-by-side report](comparison.html).

Confirmation IDs map to original search IDs: 0=B0 before, 1=search 9, 2=search 10, 3=search 24, 4=B0 after.


## Exact serving settings

| Parameter | B0 | Trial 9 | Trial 10 | Trial 24 |
|---|---:|---:|---:|---:|
| `max_num_batched_tokens` | 8192 | 8192 | 4096 | 4096 |
| `max_num_seqs` | 512 | 64 | 64 | 16 |
| `gpu_memory_utilization` | 0.92 | 0.92 | 0.95 | 0.95 |
| `long_prefill_token_threshold` | 0 | 0 | 0 | 4096 |
| `async_scheduling` | true | true | true | true |
| `enforce_eager` | false | false | false | false |
| `max_cudagraph_capture_size` | 512 | 512 | 512 | 128 |
| `enable_prefix_caching` | true | true | true | true |

Model/GPU/precision/context are fixed; chunked prefill is enabled and MTP is off. [Full protocol and workload](../../infra/DIRECT_OPTUNA_RUN.md).

## Noise, mechanism and replication limits

- Development trials 10 and 11 repeated identical settings/inputs. Their p90 TTFT was 4.953s versus 5.668s (+14.4%), while throughput differed by 0.6%. Small development deltas should not be treated as stable improvements.
- Trial 9 changed only sequence cap 512→64. Both caps exceed 32 clients, so the development gain did not demonstrate that admission limiting removed a queue. Its proposed performance benefit failed held-out validation.
- Trial 24 admits 16 sequences with 32 clients outstanding. Exported development p90 waiting requests reached 16, consistent with its observed waiting/decode tradeoff. Multiple knobs changed, so this is not a full causal ablation.
- Every point has 120 requests, but class counts are only 54/24/24/18. Tail quantiles, especially p99, remain descriptive. Request latencies share server/queue conditions; request-level resampling is not a replacement for independent run repeats.
- The test compared the same synthetic distribution with unseen prompts, not a new production workload. Each candidate has one held-out run and B0 has two. The present test set is now exposed and must not be treated as sealed if used to guide further tuning.
- Research targets were diagnostics, not hard Optuna constraints. No development setting passed every class target at either tested load; this campaign does not establish maximum sustainable SLA capacity.

## Evidence and next checkpoint

[Raw requests, frozen inputs, logs, databases and receipts](evidence/README.md) are checksummed and committed. The search-to-confirmation handoff failure and recovery are preserved in that evidence and explained in [tracking](../../docs/TRACKING.md). Original chronological analysis remains in [history](../../docs/history/DIRECT_OPTUNA_ANALYSIS.md).

The next proposed checkpoint is a focused repeated B0/trial-10 comparison, with the primary metric, run order and acceptable TPOT tradeoff declared first. [Replication criteria](../../docs/REPLICATION.md). No additional GPU run is implied by this report.

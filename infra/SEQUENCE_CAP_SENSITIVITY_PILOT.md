# Sequence-cap sensitivity pilot

Run date: 17 October 2026 UTC. This is a bounded diagnostic contrast on the pinned Qwen/vLLM server, **not** a production performance claim or the full M5 scientific qualification gate. Machine-readable per-cell results and artifact hashes are in [sequence-cap-pilot-results.json](sequence-cap-pilot-results.json). Raw AIPerf and server exports, exact commands, and server logs are retained under ignored `.artifacts/sequence-cap-pilot/`.

## Question and fixed protocol

Can an allowed serving parameter create an observable, reproducible change under the exact frozen short-chat inputs? The only planned server-setting contrast was `--max-num-seqs 512` (B0 feasibility setting) versus `--max-num-seqs 32` (candidate). The model, pinned vLLM image, TP1, BF16, 40,960 context, parser, hardware, streaming request policy, tokenizer files, and two [frozen input schedules](b0-frozen-inputs-manifest.json) stayed the same. All pilot cells used AIPerf 0.13.0 with the same verified local tokenizer files; this avoided an AIPerf offline cache lookup failure before the first timed cell. That failed preflight sent no requests and is retained as `b0a-failed-tokenizer` in local artifacts.

Four fresh servers ran in `B0a → cap32a → B0b → cap32b` order. Each had the same disjoint three-request warmup, then the 154-request 2.56 requests/s fixed schedule, then the 192-request 3.2 requests/s fixed schedule. Warmup and startup are outside each timed cell. The second cell can see cache state left by the first; the order was identical in all four phases. Hybrid cache reset and representative burn-in are not yet qualified. Each cell sent for about 60 seconds; all responses finished within AIPerf's drain allowance. The maximum absolute deviation between actual request start offsets and the frozen schedule was below 3 ms in every cell. All 1,384 timed requests returned HTTP 200 with the frozen payload controls, 511–514 server prompt tokens, and exactly 256 completion tokens. All exports were complete.

## Result

TTFT and TPOT below are medians. TPOT is AIPerf's per-request decode average; it excludes time waiting for the first token. Output tokens/s spans first dispatch through final completion, including drain. The late outstanding column lists counts at the ends of the last three 10-second sending bins.

| Server | Load, requests/s | TTFT p50 | TPOT p50 | Output tokens/s | Peak server capacity wait | Late outstanding |
|---|---:|---:|---:|---:|---:|---|
| B0a, cap 512 | 2.56 | 179 ms | 55.71 ms/token | 556 | 0 | 37, 38, 37 |
| B0b, cap 512 | 2.56 | 184 ms | 55.70 ms/token | 557 | 0 | 37, 38, 37 |
| cap32a | 2.56 | 2,367 ms | 53.47 ms/token | 520 | 12 | 39, 42, 44 |
| cap32b | 2.56 | 2,440 ms | 53.57 ms/token | 519 | 13 | 39, 42, 45 |
| B0a, cap 512 | 3.2 | 190 ms | 62.62 ms/token | 689 | 0 | 53, 53, 52 |
| B0b, cap 512 | 3.2 | 192 ms | 62.62 ms/token | 689 | 0 | 53, 53, 52 |
| cap32a | 3.2 | 9,189 ms | 53.48 ms/token | 547 | 48 | 65, 69, 79 |
| cap32b | 3.2 | 9,260 ms | 53.58 ms/token | 546 | 48 | 65, 69, 80 |

The candidate reached exactly 32 running requests in both loads; the server attributed waiting requests to **capacity**, not deferred work. B0 reached 37 running requests at 2.56 and 53 at 3.2 without a waiting queue. The candidate's shorter per-request decode average reflects smaller concurrent batches, while requests waited much longer for a first token. In both candidate runs, unfinished work was still growing near the end of the sending window. Eventual HTTP 200 after drain does not make those offered rates sustainable for cap 32.

The repeated B0 results were close and the candidate effect was far larger than their observed difference. This is **measured-sensitive** for the sequence-cap axis on this diagnostic card, with a direct queueing mechanism. It is a regression/overload at the tested rates, not a useful optimization result. The 60-second windows and 154/192 requests per cell do not provide precision-qualified p99 SLA evidence or a candidate-specific sustainable capacity estimate. Candidate ranking must keep overload distinct from an ordinary valid performance tradeoff.

## Decision and next checkpoint

This pilot validates that a frozen AIPerf input can expose a reproducible vLLM parameter effect and that the evaluator must record offered load, actual starts, completions, queueing, and drain separately. It gives a **go-ahead to build the input and evaluation engine infrastructure** around this measured protocol and to exercise it with bounded investigator probes. It does **not** unlock real autonomous search under the handoff plan: the source-backed representative mixed/session cards, matched cache preparation, longer baseline repeats/tail precision, and a frozen search domain/suite revision are still required by M4/M5.

The next critical inspection is the engine contract: one immutable workload card and asset hash, one resolved server configuration, a single-GPU lease, a complete cell result with overload/censoring labels, and a B0-versus-candidate comparison that preserves raw records. The first engine build can use these exact pilot artifacts as a real fixture while source-backed cards are prepared in parallel. The autonomous proposer/search loop stays behind the scientific gate.

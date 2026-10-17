# V2 first real gate: mixed OPS36

Campaign: `qwen38-27b-eval-v2` on one RTX PRO 6000, pinned Qwen3.8-27B,
vLLM 0.28.0 and AIPerf 0.13.0. The frozen engineered workload has 36
independent requests at 0.0966339205 requests/s: 17 chat, 8 agent,
6 code and 5 document shapes. Both runs used the same payloads, arrival
schedule, cold-stream policy and `fresh-server-triage-v1` protocol.

| Setting | B0 | First Codex proposal |
| --- | ---: | ---: |
| `max_num_batched_tokens` | 8192 | 8192 |
| `long_prefill_token_threshold` | 0 | 2048 |
| `enforce_eager` | false | false |
| Completed / planned | 36 / 36 | 36 / 36 |
| Output tokens/s | 55.067 | 55.114 |
| TTFT p50 / p90 / p99, ms | 429 / 5689 / 8964 | 428 / 6081 / 9791 |
| TPOT p50 / p90 / p99, ms/token | 42.12 / 58.38 / 64.91 | 42.51 / 57.70 / 63.40 |
| Dispatch lag p99, ms | 1.07 | 0.91 |
| Queue peak | 1 | 0 |
| Total evaluation, seconds | 797.2 | 796.9 |

The real qualification report admitted this as an **exploratory fast gate**.
Both cells are valid/normal with no failed, timed-out, canceled, censored,
or undispatched requests. The change did not improve aggregate throughput
or aggregate TTFT in a meaningful way in this window.

## Shape diagnosis

These descriptive quantiles were calculated from the 36 `normalized-requests.jsonl`
records in each run. Shapes are identified by the pinned output cap and
server-reported input-token range: chat 256 output / 472–473 input; agent 1024 /
8152–8154; code 1024 / 2008–2009; document 512 / 32728–32729. The percentile
uses linear interpolation between adjacent ordered request values.

| Shape (n) | B0 TTFT p50 / p90, ms | Threshold 2048 TTFT p50 / p90, ms | Paired TTFT improvements |
| --- | ---: | ---: | ---: |
| Chat (17) | 156 / 1078 | 152 / 703 | 11 / 17 |
| Agent (8) | 1356 / 1847 | 1447 / 1980 | 0 / 8 |
| Code (6) | 419 / 442 | 415 / 428 | 6 / 6 |
| Document (5) | 5765 / 8931 | 6216 / 9791 | 0 / 5 |

The agent hypothesized that a 2048 long-prefill threshold would reduce chat
interference at a possible long-prefill cost. The observed direction matches
that hypothesis for this one frozen window, but the per-shape sample counts
are too small to establish a reliable p90 or claim a production win. No
per-request prefill chunk trace was exported, so the scheduler mechanism is
still an inference. The next decision requires independent repeats and a
separate development/test stream.

## Raw evidence

- B0: `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/qwen38-27b-eval-v2/eval-6145d5adcd8647b6a31e5530fb2a534a/`
- Candidate: `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/qwen38-27b-eval-v2/eval-f6a75cba60564b36b434f0b078f7606d/`
- Agent research, notes, cited evidence and exact proposal:
  `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/proposals/attempt-0001/`
- Qualification, ledger, Optuna study and reports:
  `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/`

The overnight Optuna study started at `2026-10-17T20:51:57Z`. Its first
trial was still running when this summary was written. After the serving
study finishes, the persistent session runs an exploratory AIPerf adaptive
rate pilot on B0. Neither an SLA nor a capacity boundary has been defined.

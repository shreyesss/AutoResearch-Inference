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

The first Codex research attempt recorded 567,741 input tokens (472,307
reported as cached) and 8,623 output tokens in its Codex event log. Its
tool reads included several large background files. The skill now instructs
later attempts to start from indexed summaries and selectively aggregate raw
records; this efficiency change has not yet been measured.

## Raw evidence

- B0: `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/qwen38-27b-eval-v2/eval-6145d5adcd8647b6a31e5530fb2a534a/`
- Candidate: `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/qwen38-27b-eval-v2/eval-f6a75cba60564b36b434f0b078f7606d/`
- First complete TPE trial: `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/qwen38-27b-eval-v2/eval-8d13c0e2621140b38c2007377c4c1b2f/`
- Agent research, notes, cited evidence and exact proposal:
  `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/proposals/attempt-0001/`
- Qualification, ledger, Optuna study and reports:
  `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/`

The overnight Optuna study started at `2026-10-17T20:51:57Z`. Its first
trial was falsely rejected by the old startup-log verifier at the pinned
2048 token budget. It was recorded as a failed trial, **not** a poor
performance measurement. The verifier was corrected and checked against the
actual saved startup log; the study resumed from its SQLite state at
`2026-10-17T20:58:49Z`. One just-started trial was interrupted and marked
failed during that correction. Its server log and the operator intervention
remain in the artifact ledger. After the serving study finishes, the persistent
session runs an exploratory AIPerf adaptive
rate pilot on B0. Neither an SLA nor a capacity boundary has been defined.

At `2026-10-17T21:12Z`, the first post-restart complete TPE trial,
`optuna-00004`, tested batch budget 16384, threshold 8192 and eager off.
It was valid/normal with 36/36 completions: 55.046 output tokens/s,
TTFT p90 5697.9 ms and TPOT p90 58.53 ms/token. Its Optuna objectives were
`[0.9996308 throughput ratio, 1.0025544 worst p90 latency ratio]` against B0.
The controller then started `optuna-00005` automatically. This is a loop-health
check and an exploratory point, not a confirmed gain.

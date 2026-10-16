# AIPerf input and request-simulation checkpoint

Run date: 17 October 2026 (Asia/Kolkata). This is a small functional check, not a representative dataset, capacity benchmark, SLA result, or serving-configuration comparison. Raw evidence is local under `.artifacts/capability-spike/`; this report and its small input recipe are tracked outside the rsynced handoff folder.

## Pinned execution

- GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition, UUID `GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83`.
- Model: `Qwen/Qwen3.8-27B` BF16 at `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.
- Server: `vllm/vllm-openai:v0.28.0`, digest `sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14`; TP1, `max_model_len=40960`, qwen3 reasoning parser. Stock diagnostic used `max_num_seqs=512`; the schedule check uses 128 for faster startup and is functional evidence only.
- Client: installed AIPerf `0.13.0`. All live checks used the actual model, streaming chat endpoint, local tokenizer, server token usage, raw export, and non-thinking requests.
- Model startup and optional GPU telemetry delays were excluded from request behavior conclusions. AIPerf's GPU telemetry worker missed heartbeats, but server metrics and request records were exported.

## What was verified on the GPU

| Input or facility | Observed behavior | Evidence path |
|---|---|---|
| SpecBench semantic prompts | AIPerf loaded 480 questions. The first three sent user messages exactly matching source `turns[0]` for question IDs 81–83; 3/3 HTTP 200 and 64 completion tokens each. This tests loader/body preservation on a small writing slice. | `specbench/` |
| TraceLab agent session | AIPerf loaded one complete two-turn source session. The second request carried user/assistant/user history, with the same `conversation_id`; 2/2 HTTP 200. Source token counts 3621/3828 became 3631/3849 server prompt tokens after reconstruction and chat formatting. Recorded delays were disabled for this body check. | `tracelab/` |
| Native agentic-code synthesis and replay | A 2-session/4-turn trace was generated and validated as Mooncake JSONL. Replay first failed because its 64-token hash blocks met AIPerf's 512-token default; `--isl-block-size 64` made all four turns succeed with matching session and turn IDs, 4/4 HTTP 200. Continuation `input_length` in the source is a delta; actual prompts contain accumulated history. | `agentic-synth/`, `agentic-replay/` (failure), `agentic-replay-64/` |
| Recorded session schedule | On the same four-turn trace, AIPerf started both sessions together. Continuation requests began 103 ms and 114 ms after their own prior responses ended, matching source delays of 102.3 ms and 112.8 ms within observed dispatch lag. All four requests returned HTTP 200. This verifies a tiny dependent schedule, not a representative arrival process. | `agentic-fixed-schedule/` |
| Rate sweep and repetition | Two client rates (0.5, 1 request/s) × two runs × two requests all completed. Raw records and aggregate JSON/CSV were exported. The same two prompt bodies recurred in all four cells, so this does not validate a cold-cache comparison. | `repetition-sweep/` |
| Native reports | AIPerf rendered a turn-message HTML view from TraceLab raw records and a speculative acceptance table from server metrics. | `tracelab-turns.html`, `mtp-accept-*.csv` |
| Native Pareto recipe | Its two tiny shape/concurrency cells completed and exported sweep files. The resulting `pareto_optimal` array was empty on this run, so the recipe did not supply a usable frontier here. It also targets client/workload axes and a different objective pair from this project. | `native-pareto/` |
| Native adaptive search | Three iterations completed with planner `bayesian`. Optional BoTorch was absent, so AIPerf warned and used Optuna TPE. All three trials selected client concurrency 2; this is interface execution, not a meaningful optimizer test. | `native-bo/` |

The original first diagnostic baseline in [FIRST_BASELINE_RESULT.md](FIRST_BASELINE_RESULT.md) already verified constant-rate dispatch and raw request exports on 12 synthetic requests. It remains separate from these source-input checks.

## Meaningful speculative-acceptance check

The model's MTP head loaded with `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'` on the pinned server. vLLM warned that three draft tokens reuse its one MTP layer through multiple forward passes, which can lower acceptance. AIPerf loaded the public MBPP code-task set and sent its first four tasks. All four returned HTTP 200 with 128 server-reported completion tokens. The prompts were actual Python programming tasks; output length was forced for this diagnostic.

The server's `/metrics` counters went from zero to 144 draft steps, 432 draft tokens and 372 accepted draft tokens. AIPerf's `speed-bench-report` read its saved server metrics and produced acceptance rate `0.86` and mean acceptance length `3.58` (`372/432` and `372/144 + 1`, respectively). These are aggregate numbers for four requests. The pinned vLLM API response did not expose per-request acceptance, and the AIPerf per-request export has no acceptance fields. Server metrics provide the supported run-level path; custom instrumentation is not needed for that result.

## Source identity and reproducibility

- SpecBench: [source file at commit `fd2c1cd`](https://raw.githubusercontent.com/hemingkx/Spec-Bench/fd2c1cd7d2201ef71db4c5f4e455008f017967bf/data/spec_bench/question.jsonl), SHA-256 `4b6d33e79484f9841c487ee87d1cf6aa8c6066f61d5d482ff09e5a007fafdf04`.
- TraceLab: [release `v0.0.1` asset](https://github.com/uw-syfi/TraceLab/releases/download/v0.0.1/syfi_coding_trace.jsonl.gz), SHA-256 `9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b`. [select-tracelab-spike.py](select-tracelab-spike.py) selects the first complete contiguous session with 2–5 turns and at most 6000 source input-plus-output tokens (group 868, two turns); sample SHA-256 `92c8897f98871971175a1c4e553381a0d981a6491506280e338fba7d239b3eca`. It checks that the session does not recur elsewhere in the source.
- Agentic-code: [spike-agentic-config.json](spike-agentic-config.json), seed 42, two sessions, 64-token blocks; generated `dataset.jsonl` SHA-256 `5519ee376f0c740080496435baa70739c66b65a2859bc4997046be004ad97b8a`. Its text and cache blocks are synthesized and do not recover original user semantics.
- MBPP: AIPerf's `spec-al-mbpp` loader used `google-research-datasets/mbpp`, `full` config, `test` split. A frozen source revision and license/access audit belong to dataset qualification; this four-request check is not that audit.

Run from the repository root with the server started via [first-baseline.sh](first-baseline.sh) for the stock checks. The common AIPerf flags in the successful source-input runs were:

```bash
COMMON=(--model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions --streaming --url 127.0.0.1:8000 --tokenizer .artifacts/models/Qwen3.8-27B --apply-chat-template --use-server-token-count --per-chunk-usage --export-level raw --export-http-trace --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0}')
.venv/bin/aiperf profile "${COMMON[@]}" --public-dataset spec-bench --dataset-sampling-strategy sequential --request-count 3 --concurrency 1 --request-rate 1 --request-rate-mode constant --prompt-output-tokens-mean 64 --prompt-output-tokens-stddev 0 --random-seed 42 --output-artifact-dir .artifacts/capability-spike/specbench
.venv/bin/aiperf profile "${COMMON[@]}" --custom-dataset-type tracelab --input-file .artifacts/capability-spike/tracelab-sample.jsonl --no-fixed-schedule --ignore-trace-delays --request-count 2 --concurrency 1 --request-rate 1 --request-rate-mode constant --prompt-output-tokens-mean 64 --prompt-output-tokens-stddev 0 --random-seed 42 --output-artifact-dir .artifacts/capability-spike/tracelab
.venv/bin/aiperf synthesize agentic-code --config infra/spike-agentic-config.json --num-sessions 2 --seed 42 --output .artifacts/capability-spike/agentic-synth
TRACE=$(find .artifacts/capability-spike/agentic-synth -name dataset.jsonl | head -1)
.venv/bin/aiperf profile "${COMMON[@]}" --custom-dataset-type mooncake-trace --input-file "$TRACE" --isl-block-size 64 --no-fixed-schedule --ignore-trace-delays --request-count 4 --concurrency 1 --request-rate 1 --request-rate-mode constant --random-seed 42 --output-artifact-dir .artifacts/capability-spike/agentic-replay-64
.venv/bin/aiperf profile "${COMMON[@]}" --custom-dataset-type mooncake-trace --input-file "$TRACE" --isl-block-size 64 --fixed-schedule --fixed-schedule-auto-offset --request-count 4 --random-seed 42 --output-artifact-dir .artifacts/capability-spike/agentic-fixed-schedule
```

The exact installed command and resolved inputs for every live cell are also in its local `profile_export_console.txt`, `inputs.json` when generated, and captured `*-console.log`. The stock, MTP and schedule server logs and argv are retained. The MTP server launch and measurement were:

```bash
docker run --pull never -d --name iar-m0-mtp --gpus all --ipc=host -p 127.0.0.1:8000:8000 -v "$PWD/.artifacts/models/Qwen3.8-27B:/models/Qwen3.8-27B:ro" vllm/vllm-openai:v0.28.0 /models/Qwen3.8-27B --served-model-name Qwen/Qwen3.8-27B --tensor-parallel-size 1 --dtype bfloat16 --max-model-len 40960 --max-num-seqs 512 --reasoning-parser qwen3 --speculative-config '{"method":"mtp","num_speculative_tokens":3}' --host 0.0.0.0 --port 8000
.venv/bin/aiperf profile --model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions --streaming --url 127.0.0.1:8000 --tokenizer .artifacts/models/Qwen3.8-27B --apply-chat-template --public-dataset spec-al-mbpp --dataset-sampling-strategy sequential --request-count 4 --concurrency 1 --request-rate 1 --request-rate-mode constant --prompt-output-tokens-mean 128 --prompt-output-tokens-stddev 0 --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":128}' --use-server-token-count --per-chunk-usage --random-seed 42 --export-level raw --export-http-trace --output-artifact-dir .artifacts/capability-spike/mtp-mbpp
```

The acceptance reports, using the saved AIPerf server metrics, were:

```bash
.venv/bin/aiperf speed-bench-report --paths .artifacts/capability-spike/mtp-mbpp --metric accept_rate --output .artifacts/capability-spike/mtp-accept-rate.csv
.venv/bin/aiperf speed-bench-report --paths .artifacts/capability-spike/mtp-mbpp --metric accept_length --output .artifacts/capability-spike/mtp-accept-length.csv
```

The other native facility probes used synthetic inputs solely to exercise the client interface:

```bash
SYN=(--model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions --streaming --url 127.0.0.1:8000 --tokenizer .artifacts/models/Qwen3.8-27B --apply-chat-template --use-server-token-count --export-level raw)
.venv/bin/aiperf profile "${SYN[@]}" --prompt-input-tokens-mean 128 --prompt-input-tokens-stddev 0 --prompt-output-tokens-mean 32 --prompt-output-tokens-stddev 0 --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":32}' --request-rate 0.5,1 --request-rate-mode constant --concurrency 1 --request-count 2 --num-profile-runs 2 --profile-run-cooldown-seconds 1 --parameter-sweep-same-seed --per-chunk-usage --random-seed 71 --export-http-trace --output-artifact-dir .artifacts/capability-spike/repetition-sweep
.venv/bin/aiperf profile "${SYN[@]}" --search-recipe pareto-sweep --isl-osl-pairs 64/32 --concurrency 1,2 --request-count 2 --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":32}' --random-seed 91 --output-artifact-dir .artifacts/capability-spike/native-pareto
.venv/bin/aiperf profile "${SYN[@]}" --prompt-input-tokens-mean 64 --prompt-input-tokens-stddev 0 --prompt-output-tokens-mean 16 --prompt-output-tokens-stddev 0 --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":16}' --request-count 1 --search-space phases.profiling.concurrency:1,3:int --search-metric output_token_throughput --search-direction maximize --search-max-iterations 3 --search-initial-points 1 --search-planner bayesian --search-random-seed 101 --random-seed 101 --output-artifact-dir .artifacts/capability-spike/native-bo
```

The schedule check used the MTP launch above with container name `iar-m0-schedule` and `--max-num-seqs 128`. It was a functional dependency check; it cannot be compared with the earlier 512-sequence server for performance.

## Reuse decision and remaining gaps

| Need | Decision from this spike |
|---|---|
| Semantic prompts, agentic trace loading, synthetic sessions | Reuse AIPerf's tested loaders and generator. A thin adapter can freeze source selections and record exact realized requests. |
| Client scheduling, repetition, metrics and reports | Reuse AIPerf's tested request-rate, tiny recorded dependent schedule, raw export, multi-run and report paths. Validate timing on selected real source sessions and define cache preparation before using them for comparisons. |
| Speculative acceptance | Reuse `/metrics` plus AIPerf's saved server metrics and acceptance report at run level. Per-request acceptance is unavailable on this pinned server. |
| Pareto and adaptive search | Native commands run, but their axes are client/workload settings; the tiny Pareto recipe exported an empty frontier and Bayesian mode fell back to TPE. The project still needs a serving-setting controller with frozen workloads, validity rules and its specified three-objective cross-configuration archive. |
| Trace semantics and dataset fidelity | TraceLab's textual payload and cache identities are reconstructed. Source versus target token counts and session timing need explicit validation. Do not call this two-turn sample representative. |

The next stage is **dataset qualification**: select documented source slices, audit revision/license/coverage, build source-backed mixed traffic and session cards, freeze a separate evaluation split, and compare scheduled versus actual traffic on Qwen. That stage's review checkpoint is the source audit, workload cards, immutable selections and actual replay checks. No SLA or performance gain is asserted here.

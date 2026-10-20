# Existing evaluation capabilities: source audit

## Audit identity and limits

Repository: `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/Deepseek_serve`, clean commit **`2e6fa287d90adf7318ad314de27aa2f595aac821`**. Relevant files are copied under [`../archive/evaluator-source-snapshot/`](../archive/evaluator-source-snapshot/); [the snapshot manifest](snapshot-manifest.json) records SHA-256 and source line counts. This audit reads code and runs help/dry-run paths only. No model, GPU benchmark, package installation, image build or serving change was executed.

The controller checkout has **no `.venv/bin/python`**. Its system `python3` successfully executes the AIPerf runner's help and both dry-runs; ideation's research venv lacks PyYAML. The code's configured `.venv-aiperf/bin/aiperf` and model datasets were not execution-tested. Consequently successful command generation is not a benchmark pass.

**GuideLLM is not present in this tracked checkout:** `git grep -n -i guidellm` returned no matches. The available drivers are native HTTP/SSE Python and AIPerf 0.13.0; no GuideLLM customization interface should be claimed.

## Identify the existing evaluations exactly

### E1: native controlled synthetic campaign

The historical `agent-f75` frontier uses the native `ops_latency` path, not AIPerf's superficially similar synthetic workload.

- `testing/workloads/latency-active-matrix.yaml:121`: 8,192 input, 1,024 min/max output tokens, thinking/high reasoning, tools enabled, Zipf prefix pool 64 with 6,144 shared-prefix tokens. Defaults at lines 5–13 include temperature 0 and `ignore_eos: true`.
- `ops_latency/run_concurrency_sweep.sh:23`: supports workload/case, concurrency list, duration, warmup, repetitions and seed namespace through `SWEEP_*`. It starts the server at lines 114–123, performs smoke at 128–133, and enables unique request enforcement at 113. **It is not just a client command against an arbitrary existing endpoint.**
- `ops_latency/run_2xdep4.sh:45`: convenience runner sets 8 client shards, c256/384/512, warmup120s, measurement150s. Its profile uses **seq64**, not measured R7b's seq128 override. Use the generic sweep with `lat-seqs-128` for an R7b-style comparison.
- `ops_latency/README.md`: native warmup and measured datasets use separate seeds; no full-prompt cycling in the latency protocol. Generic `testing/common/loadgen.py` can cycle its dataset, so its invocation alone does not inherit these safeguards.
- Per-request native records expose TTFT, TPOT, streamed chunk timing, queue delays, usage and metadata. `testing/common/loadgen.py:402` retains requested output/min-token conditions; 675 onwards checks fixed-output completion. `ops_latency/analyze_latency.py` applies campaign SLO tiers rather than simply sorting raw RPS.

**Existing reuse:** kernel/communication/backend/routing/scheduler throughput and tail comparisons, load ramps, cache-target changes, input/output shape changes, controlled concurrency. Extend existing workload YAML and parameters when necessary; do not write another load generator.

### E2: AIPerf Mooncake fixed-schedule replay

- `ops_aiperf/campaign.yaml:69`: source revision `d750cddafa4b62387ca135949595008c51e05815`, SHA `b434f1816a707f4bac697235588184ebc374c9907cb981bb65fb0643471fe711`; deterministic non-overlapping median/burst/cache-heavy windows of 600 seconds.
- `ops_aiperf/prepare_mooncake.py:317`: verifies source SHA and writes subset/source hashes and window metadata. Existing `--window-duration` and `--minimum-requests` can produce a separately labelled new subset; it is no longer the original historical cohort.
- `ops_aiperf/runner.py:329`: `mooncake_trace` loader, `--fixed-schedule`, 256 worker default, warmup duration. `--trace-speedup` scales timestamps only; token lengths/cache hash values stay unchanged. Do **not** substitute request-rate, concurrency or AIPerf replay-speedup for this path.
- `runner.py:190`: streaming, authoritative server token counts, per-chunk usage correction, record-level exports and 1/3/5 discovery/confirmation/final runs.
- `campaign.yaml:23`: completion ≥99.5%, error ≤0.1%, qualified fraction ≥95%, ≥100 requests, no degraded replay, lag p99≤500ms, server token usage required.
- `campaign.yaml:33`: output-speed gate applies ≥30 tokens/s to ≥95% of sufficiently long outputs (≥50 tokens). `analyze.py:500` computes custom qualified goodput; lines 652–654 preserve it separately from AIPerf goodput. They cannot be interchanged.
- Default TTFT threshold 4s, ITL 33.333ms and E2E75s; document/chat overrides and length-aware gating affect interpretation. `analyze.py:600` uses p99 latency gates, not an invented p95 production SLO.
- `analyze.py:569`: missing replay degradation or lag metrics fail closed. `analyze.py:622` computes cost using qualified goodput; node cost defaults to $36/hour, a scenario requiring explicit cost assumptions.

**Existing reuse:** realistic joint length/cache/arrival replay, burst/load scaling, scheduler and backend sensitivity, replay feasibility and SLO-qualified capacity. Mooncake preserves trace structure, not original application semantics or tool execution.

### Existing supporting evaluation, not a replacement for E1/E2

AIPerf synthetic `agent` is fixed 8K/1K with thinking enabled (`testing/workloads/aiperf/synthetic-agent.yaml`), but lacks native Zipf prefix construction. `runner.py:258` supports fixed lengths or sequence-distribution YAML; constant/Poisson/Gamma arrivals, concurrency/rate, duration and warmup already exist. Other existing cases: chat, code, document, mixed and mixed-bursty. Reuse this driver for broad shape/arrival sweeps while clearly distinguishing it from the historical native synthetic benchmark.

Existing session, prefix, ragged and multimodal workload generators and native session driver cover additional load shapes. They do not automatically supply semantic correctness or distributional equivalence tests.

## Match hypotheses to the smallest sufficient change

| Mechanism / claim | Existing sufficient load path | Additional work actually needed | Classification |
|---|---|---|---|
| MoE/GEMM/MLA kernel, FP8/FP4 backend, collective overlap | E1 for controlled shape; E2 for real load sensitivity | Exact active backend/precision/shape counters; existing Nsight after clean baseline; kernel numerical reference tests for altered math | Reuse + instrumentation; numerical fixture only for correctness |
| Logical vs padded drafter rows, sparse rank imbalance | E1 concurrency/shape sweep + E2 | Per-rank logical/padded counts and kernel dispatch; token acceptance/proposed counts if missing | Instrumentation, not new load harness |
| CUDA graph dispatch keyed by scheduled tokens | E1 at transition shapes, E2 ragged load | Actual captured/eager graph mode, scheduled/accepted token counts and padding histograms | Small workload parameter extension + instrumentation |
| Prefix hit source and per-turn retention | E1 existing prefix fractions, E2 cache-heavy; existing session driver | Label rank/frontend/turn and local/external hit source; report measured hits | Reuse + instrumentation; session replay is already available |
| Warm-hit routing escape / rank affinity | Existing prefix workloads + E2; native session driver supports `--dp-ranks` | Route-ID to final-rank trace, queue waits, cache-work accounting | Reuse + instrumentation |
| Scheduler/MBT/prefill pressure | E1 fixed/mixed shape, E2 median/burst/load scaling | Per-iteration prefill/decode/verification tokens, oldest waiting age, graph mode | Reuse + instrumentation |
| Idle/API2 burst resume | E2's natural gaps may test it if trace actually has the required idle interval | Inspect trace first; otherwise explicit idle-then-burst schedule fixture or repeated invocation of existing loadgen, without changing load transport | Small schedule fixture only; new benchmark unnecessary |
| Startup/compile/model-load latency | E1/E2 are warm and exclude startup | Existing launcher/readiness logs plus external monotonic timestamps and cache-state manifest | Lifecycle measurement wrapper; not new request generator |
| Cancellation/KV leak | Existing `ops_latency/cancellation_probe.py` and loadgen | Specific leak/abort assertions, post-abort metrics and bounded repetitions | Existing probe + assertions |
| Speculative sampling distribution equivalence | E1/E2 fixed lengths and performance records cannot establish distribution equality | Small seeded categorical/reference sampler tests across temperature/top-p/top-k and rejection/correction paths; enough samples and predefined statistical test | Targeted correctness fixture required; neither GSM8K nor NLL alone proves equivalence |
| Tool-turn encoding/token-cache correctness | Existing smoke sends a tool prompt, but does not assert tool schema/arguments; native session driver removes tools | Pinned tokenizer/chat-template reference fixtures for actual assistant/tool messages, tool-call IDs, arguments and incremental/full encoding equivalence | Targeted tokenizer/parser fixture required; keep E1/E2 for performance |
| Task quality from quantization / altered model math | Smoke arithmetic is one exact check; reasoning/image/tool outputs mostly recorded without semantic assertions | Held-out quality/reference-output evaluator appropriate to task; numerical tolerance tests for changed kernel | Additional correctness/quality evaluation justified; no new performance harness |
| Real agent/tool-execution success | AgentX/Exgentic replay LLM calls and recorded timing, not tools | An actual task environment and outcome evaluator, only if hypothesis claims task success | Genuinely different semantic evaluation; not needed for ordinary serving optimization |

### Concrete limitations of existing correctness paths

`testing/common/smoke.py:68` asserts `17*19 == 323`. Its tool request at 96–104 has no tool-call schema/argument assertion afterward; reasoning, long-context, prefix and image responses are saved, not comprehensive quality-tested. A smoke pass cannot certify a quantization/kernel/sampling change.

`testing/common/session_loadgen.py:140` removes `tools` and `tool_choice`; at 158–164 it appends assistant text plus generated tool-like text as a **user** message. This tests growing conversational prefixes, not the real tool-role encoder. It supports `X-Session-ID`, optional `X-data-parallel-rank`, turns, warmup, duration and per-turn cache counters (`:123`, `:242`). Do not claim it tests actual tool serialization without adding the narrow fixture above.

## Verified command forms

Run from the `Deepseek_serve` root on a provisioned benchmark host. Code and CLI verification do not establish GPU readiness. Use separate result directories per candidate; preserve actual image and workload hashes.

### Native R7b-style synthetic comparison (starts/restarts serving)

```bash
LATENCY_LOADGEN_SHARDS=8 \
SWEEP_CASES=agent-f75 \
SWEEP_CONCURRENCIES="256 384 512" \
SWEEP_DURATION_S=150 SWEEP_WARMUP_S=120 \
SWEEP_REPETITIONS=1 SWEEP_PHASE=discovery \
bash ops_latency/run_concurrency_sweep.sh \
  CANDIDATE-R7B latency-2xdep4-sla "lat-seqs-128" --no-sync
```

Supported settings verified in source; not executed. The convenience `bash ops_latency/run_2xdep4.sh --plan` was executed successfully and its seq64 output is archived in [`native-plan.txt`](../archive/evaluator-cli/native-plan.txt).

### Existing Mooncake, unchanged dataset and scaled arrival load

```bash
python3 -m ops_aiperf.runner \
  --suite production --workload mooncake-median \
  --candidate CANDIDATE --profile-label latency-2xdep4-sla \
  --profile-path serving/b200/vllm/profiles/latency-2xdep4-sla.yaml \
  --base-url http://127.0.0.1:8000 \
  --trace-speedup 2 --phase discovery \
  --dry-run --no-sync
```

Dry-run was executed successfully; see [`mooncake-dry-run.txt`](../archive/evaluator-cli/mooncake-dry-run.txt). Remove `--dry-run` only for a provisioned/authorized run. Repeat with `mooncake-burst` and `mooncake-cache-heavy`; speedups 1/1.25/1.5/2 are parameters, not new evaluations. `--duration` does not truncate the fixed-schedule Mooncake branch: prepare a separate labelled subset if a shorter trace is required.

### Existing AIPerf synthetic analog

```bash
python3 -m ops_aiperf.runner \
  --suite synthetic --workload agent --candidate CANDIDATE \
  --profile-label latency-2xdep4-sla \
  --concurrency 384 --duration 150 --warmup-duration 120 \
  --phase discovery --dry-run --no-sync
```

Executed successfully as dry-run; see [`synthetic-dry-run.txt`](../archive/evaluator-cli/synthetic-dry-run.txt). It does not reproduce E1's cache layout. These command forms are verified; no fabricated arbitrary tool/sampling flag is appended to this wrapper.

## Fork vLLM → build image → deploy → evaluate

1. **Pin the baseline correctly.** `serving/b200/vllm/images.yaml:2` default digest is `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`; source mapping at line4 is `ac9126e58aa7bbab1856ba6593ba4d5003fea516`. This is not evidence that the current live host is actually running that image. Inspect runtime digest/version before patch selection. B300/v0.32 claims from mined material are not baseline facts.
2. **Fork/cherry-pick against the actual source.** Check already-present changes, dependencies and architecture/backend support. Upstream issue or PR presence does not establish clean applicability to this older custom serving stack.
3. **Build an immutable candidate image.** This repository has a specialized `ops_latency/Dockerfile.nvfp4-moeep`, not a general audited vLLM fork build pipeline. Use the selected vLLM fork's actual Dockerfile/build instructions after checking its compatibility, and retain source commit, patch, dependency pins and resulting digest. No generic docker-build command is claimed verified here.
4. **Deploy through the existing override.** `lib/serve_recipe.py:108` reads `VLLM_IMAGE`; `:472` supports profile, repeated `--experiment`, dry-run and validate. After the image exists, the supported form is `VLLM_IMAGE=registry/image@sha256:DIGEST bash serving/b200/vllm/serve.sh --profile latency-2xdep4-sla --experiment lat-seqs-128 --dry-run`. Placeholder digest is a template, not an existing image. The launcher must be provisioned; the controller lacks its expected `.venv`.
5. **Preserve router settings too.** Latency helpers set bounded session hashing at 1.1× load, connection pool4096 and connector retry (`ops_latency/lib/common.sh:34`). Bare serving invocation does not inherit these latency overrides. `lib/router.py:68` already performs bounded **endpoint/session** hashing, so 'add bounded endpoint affinity' is not automatically a new improvement; final DP-rank locality remains a different question.
6. **Run correctness before capacity, then E1/E2.** Reuse the existing smoke and targeted source tests; add narrow correctness fixtures only for the unsupported claims in the table. Run performance without profilers. Existing profiling wrappers require a clean baseline and mark results nonpublishable as capacity (`testing/README.md`).
7. **Record evidence and judge the scoped claim.** `ops_aiperf/runner.py:440` hashes runner/analyzer/preparer/campaign/workload/profile and records repository dirty state and `VLLM_IMAGE`. Its image field is an environment value, not Docker runtime attestation. Record actual digest/source/config separately to close that gap. Do not silently call a missing image field verified.

## What is not established

No GPU results, sampling equivalence, fork build success or live configuration inventory were produced by this audit. No claim that all future hypotheses need a new harness is warranted: the two existing performance evaluations plus narrowly scoped instrumentation cover most serving changes.

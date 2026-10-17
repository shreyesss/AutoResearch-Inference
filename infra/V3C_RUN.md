# v3c overnight search: cost and evidence gates

## What is running

The existing input qualification, matched B0 evaluator, and B0 class-aware SLA profiler run independently of the candidate search. The v3b candidate watcher was retired before any proposal or candidate GPU run. The v3c watcher starts only after the B0 profiler produces a validated receipt and the GPU is idle. Two development inputs (seeds 1042 and 1043) are both development data; the sealed test is not in the candidate registry.

## Proposed v3c loop

1. The controller runs one fresh 36-request B0 screen on the mixed reference workload.
2. Codex `gpt-6-sol`, medium reasoning, proposes at most eight distinct serving configurations. Each gets one matched 36-request screen. The next proposal sees earlier screen results and the frozen B0 development/profile evidence. It does **not** see a previous candidate's long development evaluation, because those run after the proposal loop.
3. The short screen rejects invalid or conspicuously regressed candidates. Its p90 values and Pareto ordering are diagnostics only. The current automatic two-finalist selector takes the screened throughput extreme and a different balanced-latency extreme. This is a provisional allocation of the long-run budget, not statistical proof that other viable candidates are worse. The full screen table and raw outputs remain available for inspection.
4. Only those at most two provisional finalists run the two matched 240-request development windows. They are assessed by class against `configs/sla-policy-v3.json`. A finalist proceeds to a class-aware AIPerf load profile only if both windows are observed feasible. The profile stores every point and its assessment; its selected in-sample rate is not confirmed capacity.
5. Independent fixed-rate confirmation and sealed testing are separate future gates. The campaign does not claim SLA capacity or test-set success.

## Time budget and practical limit

One earlier 36-request mixed cell took about 800 seconds: 356 seconds server startup, 51 seconds warmup, and 392 seconds benchmark (`results/2026-10-17-ops4-first-search/candidate/evaluation-timings.json`). A fresh-screen-per-candidate campaign can therefore take roughly 13 minutes per proposal, plus one B0 screen, proposer time, two long finalist windows, and any finalist profiles. Eight candidate screens alone are roughly 1 hour 47 minutes at that observed pace. Actual times vary. This reduces repeated 240-request/profile work but does **not** remove vLLM startup or make the search fast. Two 240-request windows at the current 0.1 request/s schedule have at least 80 minutes of dispatch per finalist before startup/overhead. The adaptive profiler can add hours. The controller's search wall budget is 12 hours; its final reports may stop earlier or time out, and that is not an SLA result.

The 36-request screen has too few observations per class to estimate class p90 reliably. If the two selected finalists fail deeper testing, inspect the retained viable screen points before another versioned campaign. Do not call the short-screen selection a reliable global frontier.

## Search space and immutable inputs

`configs/search-domain-v3c.json` enables `max_num_batched_tokens`, `long_prefill_token_threshold`, `enforce_eager`, `max_num_seqs`, `gpu_memory_utilization`, `async_scheduling`, and `max_cudagraph_capture_size`. Sequence cap and memory fraction require queue and KV-pressure diagnostics for a mechanism claim. The graph cap is also a startup/memory contrast; its steady-state effect depends on covered batch sizes. Prefix caching stays on; MTP stays off until the workload and telemetry can validate their mechanisms. The model, GPU, vLLM image, 40,960-token context, mixed request bodies, arrival schedules and approved research targets stay pinned. See `infra/V3C_SEARCH_SPACE.md` for exact values.

## Inspect and launch

The watcher command below is one-shot. It checks the frozen study, matched B0 cells, B0 profile and idle GPU, then runs a GPU-free campaign preflight before starting candidate work. It refuses to overwrite an earlier status or rerun proposals.

```bash
tmux new-session -d -s iar-v3c-candidate-search 'cd /home/ubuntu/shreyas/skunk-work && PYTHONPATH=src .venv/bin/python infra/run_v3_candidate_search.py wait-run --wait-timeout-s 43200 > .artifacts/v3-independent-capture/candidate-search-v3c-watcher.log 2>&1'
```

```bash
cat .artifacts/v3-independent-capture/development-overnight-checkpoint.json
cat .artifacts/v3-independent-capture/matched-evaluator-b0-waiter-status.json
cat .artifacts/v3-independent-capture/candidate-search-v3c-status.json
tail -n 80 .artifacts/v3-independent-capture/candidate-search-v3c-console.log
cat .artifacts/autoresearch-codebase/qwen38-27b-sla-serving-v3c/real/screen-shortlist.json
cat .artifacts/autoresearch-codebase/qwen38-27b-sla-serving-v3c/real/sla-search-summary.json
```

Earlier v3b files and locks are historical evidence; the v3c watcher writes separate status, log, PID and campaign artifacts.

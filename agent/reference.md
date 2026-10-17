# Frozen reference packet v1

## Research workspace and memory

Each proposal attempt has a human-readable folder. `context.json` contains current campaign state, recent cell/feedback summaries, the active domain and remaining budget. `research-index.json` lists complete staged evidence files and prior attempt snapshots. `measurements-index.json` links staged, size-bounded raw files for non-heldout recent/frontier cells and explains omissions. Read relevant files on demand; the proposal prompt deliberately carries paths instead of their full contents. `workspace/notes.md` is writable campaign working memory for the next attempt. The controller snapshots it read-only under `history/attempt-*/notes.md`, together with validated prior proposals and receipts. Codex event JSONL, stderr, final JSON and validation receipts stay outside the notes and can be inspected by the operator. This memory is within one campaign; it is not a curated cross-campaign lesson store. The proposal agent cannot inspect arbitrary host paths or run its own GPU measurements.

## Scientific scope

The handoff contract is v0.2. Workload construction and sensitivity qualification precede real adaptive search. Supported vLLM serving settings are the initial intervention class. Workload traffic and evaluator policy stay frozen outside proposal authority. The campaign fixes model/tokenizer, runtime image, task/output mode, exact offered loads, cache preparation and scoring. New intervention families require a versioned contract.

Primary objective vector at an operating point: output tokens/s ↑, TTFT p99 ↓, TPOT p99 ↓. Report p50, completion/error/censoring, client lag, backlog, diagnostics and interval uncertainty. Conditional Pareto fronts use exact load and compatible protocol; a cross-load archive uses only an approved common ladder. An exact front does not certify a global optimum. No scalar objective is assumed.

## Initial observed evidence

The 17 October 2026 Qwen short-chat manual comparison used streaming, non-thinking, forced-256-token output, 511–514 prompt tokens and fixed 154 requests at 2.56 req/s plus 192 at 3.2 req/s. All 20 measured cells accounted for 3,460 successful requests. B0 sequence cap was 512; cap 32 queued badly (Qmax 48 at 3.2 req/s), while cap 128 was flat. MTP1 and MTP3 repeated a decode/throughput gain with TTFT cost. At 3.2 req/s, B0/MTP1/MTP3 TPOT p50 was about 62.7/37.2/28.4 ms/token, output rate about 689/739/758 tokens/s, and TTFT p50 about 193/202/223 ms. Short sample p99s are directional only. The mixed and bursty YAMLs were not part of that comparison. Short chat had zero prefix-cache hits and 22–31% peak KV usage, so cache/memory knobs did not have demonstrated headroom there.

## Qualification and costs

Real search requires a matching qualification report with representative workload provenance/realization, B0, repeatable parameter sensitivity and an active domain revision. It does not require a gain over B0. A failed gate produces a report and targeted next measurements, not an invented favorable result. Low-level pilot evaluation may run before the gate and remains explicitly labeled. Default initial bounds are about 12 distinct proposals, up to 3 expanded finalists, and a reserved confirmation/held-out budget. Short screens may be 60–120 seconds; final p99 conclusions require repeated, longer windows, sufficient eligible requests and an explicit uncertainty criterion. Workloads include diagnostic short chat, source-backed mixed/session families and meaningful semantic prompts for MTP. Stress traffic is labeled separately.

## Permitted source map

The controller may expose immutable evidence IDs for the handoff `DECISIONS.md`, `docs/INTERFACES.md`, `docs/IMPLEMENTATION.md`, `ACCEPTANCE.md`, local `EXECUTIVE_SUMMARY.md`, `infra/B0_LOAD_CALIBRATION.md`, `infra/SEQUENCE_CAP_SENSITIVITY_PILOT.md`, `infra/MANUAL_SERVING_SEARCH.md`, `infra/manual-serving-search-results.json`, capability and dataset audits, the frozen campaign/domain, workload cards, runtime capability reports, raw results and previous feedback. Each staged excerpt states its source hash and truncation. Only a listed evidence ID can be cited as retrieved in a proposal. Do not use held-out results or unversioned web claims.

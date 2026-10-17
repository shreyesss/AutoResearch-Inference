# Frozen reference packet v1

## Research workspace and memory

Each proposal attempt has a human-readable folder. `context.json` contains current campaign state, recent cell/feedback summaries, the active domain and remaining budget. `research-index.json` lists complete staged evidence files and prior attempt snapshots. `measurements-index.json` links staged, size-bounded raw files for non-heldout recent/frontier cells and explains omissions. Read relevant files on demand; the proposal prompt deliberately carries paths instead of their full contents. `workspace/notes.md` is writable campaign working memory for the next attempt. The controller snapshots it read-only under `history/attempt-*/notes.md`, together with validated prior proposals and receipts. Codex event JSONL, stderr, final JSON and validation receipts stay outside the notes and can be inspected by the operator. This memory is within one campaign; it is not a curated cross-campaign lesson store. The proposal agent cannot inspect arbitrary host paths or run its own GPU measurements.

## Scientific scope

The handoff contract is v0.2. This campaign begins after independent workload replay and four matched B0 cells qualify. The first candidate can test serving-parameter sensitivity. Supported vLLM serving settings are the initial intervention class. Workload traffic and evaluator policy stay frozen outside proposal authority. The campaign fixes model/tokenizer, runtime image, task/output mode, exact offered loads, cache preparation and scoring. New intervention families require a versioned contract.

Primary objective vector at an operating point: output tokens/s ↑, TTFT p99 ↓, TPOT p99 ↓. Report p50, completion/error/censoring, client lag, backlog, diagnostics and interval uncertainty. Conditional Pareto fronts use exact load and compatible protocol; a cross-load archive uses only an approved common ladder. An exact front does not certify a global optimum. No scalar objective is assumed.

## Initial observed evidence

Begin with the current campaign's four B0 cells and their raw request/server evidence. Earlier manual search results are not staged as a prior for this campaign. The four tasks exercise short decode, long thinking output, long prefill, and mixed prefill/decode contention. Their source mix is an engineered diagnostic, not a deployment distribution. A model-generated hypothesis remains unverified until an exact matched candidate cell tests it.

## Qualification and costs

This is a four-task **inference-metrics** campaign. It starts after the four exact schedules and B0 measurements are available and traffic-validated; first candidate proposals can test parameter sensitivity rather than assuming it. The current campaign budget is 8 distinct proposals and up to 3 expanded finalists; read the remaining budget from `context.json`. Finite screens and their p99s are provisional; confirmation needs repeated matched windows and a declared uncertainty rule. This campaign does not claim natural-answer quality or production representativeness.

## Permitted source map

The controller exposes immutable evidence IDs for this campaign's design, domain, four workload cards, B0 behavior, raw results and previous feedback. Each staged excerpt states its source hash and truncation. Only a listed evidence ID can be cited as retrieved local evidence. For internet research, record the URL, retrieval date and exact claim separately; external documentation cannot replace measured results. Do not use held-out results.

# Scheduling/host-runtime discovery — batch 001

## Result and scope

**One candidate advances to a bounded CPU compatibility diagnostic, not to implementation or a service-benefit claim:** exact rendered-prefix tokenization reuse for Flash-1017. The source reading and three CPU probes already eliminated two unsafe shortcuts and one ineffective drop-in. No GPU/model/HTTP serving calls were made; no serving source was changed. All artifacts here are research evidence.

Reference: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, intended Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`. Planned two DEP4 groups are not verified live configuration. CPU tokenizer costs do not depend directly on B200 versus H200; the service value depends on frontend exposure, workload and queueing.

## Adaptive discovery actually performed

1. An agent-authored expansion plan separated host dispatch and cache pressure. A fresh isolated state first failed with generic `ValueError`; `researchctl init` fixed the missing state. No API request was made by those failed commands.
2. `paper-search 'LLM serving CPU scheduling overhead' --provider openalex --after 2026-06-01 --before 2026-10-23 --limit 12` returned 12 retained abstracts with a cache miss, no provider errors. This found TokTier, alongside several unrelated or previously proposed directions.
3. Full-text cache research plus prior memory rejected a generic new eviction card. `When Fancy Eviction Fails` supplies counterevidence to complex replacement policies; previous ghost-admission hypothesis already covers quick demotion's central opportunity.
4. The next query changed mechanism: `paper-search 'incremental tokenization exact serving'` with the same dates and limit8 returned eight retained abstracts, including **October 14 Delta Tokenizer** and October9 GraphTok. TokTier overlaps, so these two calls returned **19 distinct explicit paper identities**. Neither call establishes exhaustive coverage.
5. The exact target tokenizer, a pinned TokTier repository and the pinned vLLM custom wrapper were inspected. This changed the proposal from installing a package into an exact-artifact compatibility task.
6. Three real CPU probes recorded source/configuration facts, counterexamples and renderer behavior. A revised expansion plan records the resulting decision gaps. Three read-only canonical FTS searches and selected PR body reads checked neighboring frontend changes. Broad `tokenizer AND cache` was noisy because issue bodies contain boilerplate; exact frontend filenames/IDs were more useful.

Receipts: `expand.json`, `search-host.json`, `search-tokenization.json`, `expand-v2.json`, `pr-fts.json`, `selected-pr-records.json`. External full texts and hashes: `sources/manifest.json`. No Serper/model calls; API billing not measured. Isolated state is local-only, not canonical/S3 published.

## Candidate S01: certified reuse of rendered tokenization state

### Mechanism and source synthesis

[TokTier](https://arxiv.org/html/2607.29678v1) retains prior token records and repairs a changing suffix only after finding a tokenizer-specific stable boundary; failed checks widen or use the reference encoder. Its CPU repair can be considered separately from its GPU full-encode path. [Delta Tokenizer](https://arxiv.org/html/2610.19801v1) extends this direction with safe full-request cuts and a CPU pool that schedules short updates between chunks. **Same authors and shared evidence: these are related work, not independent replications.** [GraphTok](https://arxiv.org/html/2610.13325v1) is a recent alternative for full encodes; its GPU route and large-context fleet results do not establish value on this eight-GPU deployment. Its discussion also supports retaining a strong fast-CPU comparator and accounting for complete returned-token materialization.

Our proposed intervention is narrower: after the existing V4.1 renderer has produced its exact text, retain versioned CPU token state keyed by isolated session identity and tokenizer/render options. Find the unchanged rendered prefix, preserve tokens only through a certified boundary, and re-encode the changed suffix. A changed template, tool schema, special-token policy, tokenizer revision or unsupported input falls back to the original whole-request encoder. The initial study does **not** change neural weights, KV semantics, model scheduling, GPU allocation or decoder outputs. Do not add the chunk pool until the simple reuse path is correct and its actual bottleneck warrants it.

### What the pinned code actually does

- `vllm/tokenizers/deepseek_v41.py` lines119–132 invokes `encode_messages(...)`, then `self.encode(prompt, add_special_tokens=False, ...)` on the whole rendered prompt.
- `vllm/tokenizers/hf.py:get_cached_tokenizer` lines106–166 caches vocabulary and tokenizer properties; it does not cache tokenized prompt prefixes.
- This establishes absence of the proposed state in this **inspected Python wrapper**, not across every possible frontend/gateway or current live image.
- `deepseek_v41_encoding.py` preprocesses tool merges/order and may drop prior thinking. Source hashes are retained in `sources/vllm-retrieval.json`.
- Prior E18 considered the generic HF tokenization cache PR#47583 and explicitly identified custom `deepseek_v41` bypass risk. S01's changed premise is a certified custom-path adaptation, not reenabling the old toggle. Current PR#62729/#62459/#62724 also make rendering/control-token distinctions relevant; their bodies are counterevidence to treating arbitrary raw-message append as exact rendered append. Those PRs are not assumed merged into the pinned source.

### Actual CPU evidence and adversarial outcomes

1. **Artifact audit:** fetched only tokenizer files from the exact Flash-1017 revision, no weights. `tokenizer.json` SHA256 `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b`. Against the certified V4 anchor `8f9f37ca37fdc4f5fd36d5cf4d3b0e8392edb4e894fd10cc0d70b4957c8633cf`, all non-added-token sections match. Nine added-token entries differ. No target entry has lstrip/rstrip/single_word absorption flags.
2. **No false drop-in claim:** `asu-idi/toktier@0591fe18235f3e64f0576fa7f77a0804af1ba5c2`, `docs/support-matrix.md:985`, explicitly identifies this exact target hash as examined but uncertified. The JSON registry and repair roster omit it. The source explains missing added-token evidence and cross-artifact certification machinery. This is not evidence that the repair algorithm is inherently incorrect; installing it unchanged would take a reference fallback rather than supply the proposed acceleration.
3. **Concrete wrong-shortcut probes:** with isolated `tokenizers==0.22.2`, encoding all18 old/new changed literals produces different IDs between target and anchor in18/18 cases. Concatenating independently encoded sides of those literals disagrees with target full encoding in254/300 split cases. These are targeted counterexamples, not a natural workload error rate and not tests of TokTier's certified repair.
4. **Renderer audit:** executed the pinned standard-library `encode_messages` on a constructed three-turn conversation with chat/thinking and drop-thinking controls. Six tested transitions were pure append; default thinking+drop-thinking rewrote the old trailing marker in two transitions, invalidating six old characters. Thus an append-only cache misses an important default path. Reuse must validate the rendered common prefix and repair edits, not trust message count or pre-render text identity. Common-prefix equality alone is still not a tokenizer splice certificate.

Scripts/results: `cpu_tokenizer_audit.*`, `cpu_tokenizer_counterexamples.*`, `cpu_render_prefix_audit.*`. These probes supply no throughput/TTFT evidence and do not exercise the deployed Transformers loader.

### Competing explanation and value pathway

The potential saving is CPU encode time and frontend queueing before model admission. It might improve TTFT and TTFT-limited goodput; it is not a direct per-token decode/ITL optimization. Whole-prompt rendering, serialization and Python list materialization remain costs even if BPE repair is cheap. Eight-thousand-token agent-p75 prompts may expose much less removable work than the papers' much longer contexts. If benchmark requests already contain token IDs, this stage is bypassed and **the hypothesis has no improvement pathway on that benchmark**. If the running Rust frontend or external gateway already provides equivalent caching, the Python-only delta is inactive. Unknown ROI remains unknown.

### Bounded CPU next diagnostic, with stop conditions

A. Source audit now resolves the standard runner to chat endpoints (see final benchmark section). Resolve actual serialized payload, live frontend and session identity from retained artifacts; no service call required. Retain session repair as a separately scoped exposure if fixed-prefix controls do not supply session continuations.

B. Bind the actual reference loader/version and exact tokenizer/render artifacts. Keep target added-token IDs and flags. Do not substitute the certified V4 tokenizer, merely add a registry allowlist entry, or weaken failure behavior.

C. Reuse the upstream certificate implementation only after enumerating its actual premises: Unicode tables, sequential split rules, deterministic BPE, added-token recognition, offset reconstruction, maximum literal lengths, postprocessing and truncation exactly once. Test every split of all18 changed literals, neighboring Unicode/whitespace/digit classes, partial special tokens, normalization, repeated substrings, cancellation/state eviction and tokenizer changes. Compare complete ordered IDs, not decoded text or token count.

D. Add exact pinned renderer fixtures for reasoning on/off, dropped thinking, tool-result reordering, tool-schema changes, continued assistant, system-only, text/image rejection and suffix edits. On any mismatch stop the adapter route, retain counterexample and use full reference encoding. A bounded pass is evidence for a next implementation review, not universal certification.

E. Once compatible, CPU-only replay of actual eligible rendered input can measure encode time, materialization, repair/fallback frequency, state memory and frontend queueing using held-out sessions. Compare original full encode, fast full encode with no state, and repaired state at equal CPU workers. No fabricated percentage target is supplied. Stop performance work if the actual standard benchmark bypasses the stage or reusable spans are absent.

### Future evaluation, not authorized execution

Keep Mooncake and agent-p75 as unchanged service controls if their actual HTTP payloads exercise this stage. Measure clientTTFT/p95/p99, successful request throughput, output token counts, error rates, end-to-end latency and decode ITL guardrails alongside CPU-stage timing and fallback counts. Fix rendered request bytes and verify both arms feed exactly the same token IDs. Pair request sequences/arrival schedule and separate warm-state/cold-state arms; report slow full-encode tails instead of hiding them in means.

If existing tests send token IDs or lack real session edits, they cannot validate exact incremental text handling. Then add a small **CPU renderer/tokenizer differential fixture and text HTTP session replay** while preserving both original service controls; state precisely that the added workload evaluates a new exposure. Do not replace current benchmark with a convenient100K-token regime and call that a win on agent-p75. A future GPU service comparison requires separate execution authorization.

## Other investigated interventions and dispositions

| Lead | Disposition | Reason / next useful evidence |
|---|---|---|
| Quick demotion of one-hit prefix blocks, 2609.28870 | Duplicate/refinement | Canonical H01 `4028a37…` already proposes ghost-hash probation plus ancestry-preserving admission. New negative-result paper strengthens caution about LFU/complex replacement; not a new card. |
| Compute-aware partial eviction keeping deep blocks, same paper | Defer integration | Needs reuse after earlier cache holes plus a target-specific sparse/CED recompute-cost model; quadratic dense-attention miss cost is not transferable. No direct-port claim. Existing contiguous-group safety must remain. |
| CacheScout2608.14624 transition-guided anchor retention | Defer workload | Distinct semantic transition signal, but current eight synthetic prefixes do not establish learnable agent transitions; no target session traces or agent identities. Exclude optional background warmup from any first experiment. |
| DRO output-length reservation2607.16892 | Reject direct application | Full text evaluates a simulatedA100/70B system and reservation-cost objective. Pinned scheduler allocates slots incrementally; paper's assumed per-request reservation/preemption mapping and cost coefficients are not current runtime evidence. Reopen only for observed preemption with calibrated growth, not its headline cost claim. |
| PersistentKV2606.26666 workqueue attention | Reject direct application | GQA/FP16 commodity-GPU mechanism; target CSA2/MLA/indexer path and B200 occupancy differ. This does not justify replacing target attention. Only abstract read. |
| GraphTok2610.13325 full GPU tokenization | Defer alternative | SharedGPU contention/correctness for exact target unknown; current GPU work prohibited, full encoder not needed for CPU repair diagnostic. Its recent full-text evidence supplies comparator/counterevidence, not target prediction. |

Seven unique interventions considered (CPU repair plus six rows); one advances to CPU compatibility, three defer, two reject direct application, one duplicate. **Zero accepted service improvements.** Related safe chunk-pool scheduling is kept inside S01's optional extension rather than inflated into a second idea. Outcome labels reflect this bounded investigation; they are not permanent blacklists.

### Resolved benchmark source check (after initial report)

The installed Bitlane sweep source was subsequently read. `bench/sweep.py:224–229` always constructs AIPerf with `--endpoint-type chat --streaming`, including both synthetic and trace modes; lines134–140 load the workload arguments. Therefore **the standard runner is configured for chat requests, not a token-ID completions benchmark**. This source check is not an HTTP capture or proof of which live frontend is running. AIPerf's own installed serializer and saved request artifact were not read in this lane.

`agent-p75.yaml` fixes 6144 shared +2048 unique input tokens,1024 output and eight prefixes. `mooncake-median.yaml` uses the hash-reuse trace and fixed arrival schedule. These exercise repeated prompt text/cache patterns but do not demonstrate same-session append chains or arbitrary renderer edits. An existing `multiturn.yaml` already supplies four growing turns (1024 new/256 output,1s gaps), so **reuse that installed evaluator** for the session-state path rather than adding a new harness. It still lacks the adversarial tokenizer/renderer exactness cases; those remain CPU fixtures. Session key/worker affinity must be explicitly checked: sweep.py only adds its x-session-id environment switch when a workload sets `session_header`, and this multiturn YAML does not set it. A stateful adapter must use a verified session identity or exact content-derived identity; it cannot assume correlation IDs reach the server.

The current agent-p75 opportunity for a *session-only* repair is unresolved despite text exposure. A separate shared-prefix cache could handle its eight prefixes, but that would revisit the older E18 family and is not silently counted as this new session adaptation. The selected next diagnostic tests compatibility and measures reachability, with zero current benchmark win claims.

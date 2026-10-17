# Bounded manual serving search on frozen short chat

Run date: 17 October 2026 UTC. This was a **manual, bounded comparison**, not the autonomous autoresearch engine or a production benchmark. Parallel read-only reviews chose plausible interventions; the one GPU ran all measurements serially. [manual-search-plan.json](manual-search-plan.json) records the candidate hypotheses and rules. [manual-serving-search-results.json](manual-serving-search-results.json) holds per-cell measurements, validation, acceptance counters and hashes. Raw AIPerf exports, server logs and exact commands remain under ignored `.artifacts/manual-serving-search-v1/`.

## Exact common traffic and B0

Every server received the same two immutable AIPerf single-turn assets from [b0-frozen-inputs-manifest.json](b0-frozen-inputs-manifest.json), after a separate three-request warmup:

| Cell | Offered arrivals | Exact schedule | Realized request shape |
|---|---:|---|---|
| Ordinary short chat | 154 requests at 2.56 requests/s | One every 390.625 ms over about 60 s | 511–514 Qwen prompt tokens, exactly 256 completion tokens |
| Busy short chat | 192 requests at 3.2 requests/s | One every 312.5 ms over about 60 s | Same shape; different frozen prompt texts |

All requests were independent, streaming, non-thinking chat requests with temperature 0 and `ignore_eos=true`, `min_tokens=256`. This is a **mechanical diagnostic** generated from the Deepseek_serve short-chat shape and adapted to Qwen; it is not a production traffic mix or semantic correctness task. The same pinned model revision, vLLM image digest, single RTX PRO 6000 Blackwell, TP1/BF16, 40,960 context and Qwen3 parser applied throughout. B0 used `max_num_seqs=512` (required feasibility override); resolved defaults included `max_num_batched_tokens=8192`, prefix caching on, GPU memory fraction 0.92 and CUDA graphs on. MTP was off in B0.

The earlier sensitivity pilot provided two fresh B0 repeats (`b0a`, `b0b`); this sequence added a third fresh B0 guard (`b0check`). Each candidate had a fresh server. The timed cell order was 2.56 then 3.2 requests/s for every server. The second cell can inherit cache state from the first; that order was held fixed. Hybrid cache reset and representative burn-in remain unqualified.

## What we tried

Only one serving setting changed per candidate. `cap128a` was a safe sequence-cap control; `mtp1a/b` and `mtp3a/b` tested speculative depths 1 and 3. The proposal order was MTP1, cap128, then MTP3 after MTP1 showed a signal, followed by a fresh B0 guard and repeats of both nondominated MTP candidates. Depth 3 was functionally supported by the earlier Qwen capability spike; this run provided the performance contrast.

Values below are ranges across fresh-server repeats, not confidence intervals. TTFT and TPOT are medians; output tokens/s counts all successful output tokens from first dispatch through final completion, including drain. Observed p99s are in the JSON and remain sample estimates from only 154/192 requests per cell.

| Setting | 2.56 requests/s: TTFT / TPOT / output tok/s | 3.2 requests/s: TTFT / TPOT / output tok/s | Server queue |
|---|---|---|---|
| **B0**, cap 512, MTP off (3 runs) | 179–186 ms / 55.7–55.8 ms/token / 556 | 190–195 ms / 62.6–62.8 ms/token / 689 | None |
| Cap 128, MTP off (1 run) | 184 ms / 55.7 ms/token / 556 | 195 ms / 62.7 ms/token / 689 | None; effectively B0-like |
| **MTP depth 1**, cap 512 (2 runs) | 193–194 ms / 32.8 ms/token / 593–594 | 202 ms / 37.1–37.2 ms/token / 738–740 | None |
| **MTP depth 3**, cap 512 (2 runs) | 210–211 ms / 25.0–25.2 ms/token / 604 | 222–223 ms / 28.3–28.5 ms/token / 758 | None |

All **2,076 new timed requests** returned HTTP 200 with the exact frozen payload controls, 511–514 server prompt tokens, 256 completion tokens, and nonempty visible assistant text. All AIPerf exports were complete. Maximum absolute actual-start error against each fixed schedule was below 3 ms. No new cell had a server waiting queue; late outstanding counts were level or falling. The B0 guard reproduced earlier B0 throughput and latency. The MTP depth-1 and depth-3 repeats closely reproduced their first runs. Server counters showed about 81–82% accepted draft tokens at depth 1 and 58–59% at depth 3; depth 3 still accepted more tokens per draft step and ran faster.

This is **real improvement on decode latency and finite-run completion rate**, with a **TTFT cost**. At 3.2 requests/s, MTP1 lowered median TPOT by about 41% and raised finite-run output tokens/s by about 7%; MTP3 lowered TPOT by about 55% and raised output tokens/s by about 10%, compared with B0. Median TTFT rose roughly 8–12 ms with MTP1 and 27–33 ms with MTP3. The same directional tradeoff appeared at 2.56. B0, MTP1 and MTP3 are distinct point-estimate tradeoffs; without a Qwen-specific TTFT requirement or uncertainty-qualified tails, this report does not name a single best configuration. The cap-128 probe was flat. The prior cap-32 probe was a predictable capacity-queue regression and is retained as a negative control, not an optimization candidate.

At fixed offered rates, finite-run tokens/s can rise because the same work finishes sooner and the drain is shorter. It is **not** a new maximum sustainable capacity estimate. The short windows and small request counts do not certify p99 SLA or production wins. Forced-length random synthetic text does not establish semantic quality or how MTP behaves on real code/agent/document requests. Exact generated text is not a correctness oracle here: even two B0 runs differed in many responses under concurrent GPU execution. The next content-sensitive check must use meaningful prompts and its own validity policy.

For visibility into the primary tail metrics, at 3.2 requests/s the **observed sample p99** TTFT was 224–226 ms for B0, 233 ms for MTP1, and 258–261 ms for MTP3. The corresponding request-level TPOT p99s were 63.8–63.9, 39.5–39.7, and 32.4–32.9 ms/token. These short-run sample quantiles are directional evidence, not precision-qualified p99 estimates.

## Search-space correction and next checkpoint

The handoff [README](../inference-autoresearch-handoff/README.md) describes the project but does not enumerate numeric search values. Its normative [DECISIONS.md](../inference-autoresearch-handoff/DECISIONS.md) proposes `max_num_seqs` 8/16/32/64/128, `max_num_batched_tokens` 2048/4096/8192/16384, GPU memory fraction .85/.90/.93, prefix cache off/on, and MTP depth 0/1/2/3/5. These are **proposed probes**, not a safe or complete active domain. Exact B0 values 512 and 0.92 are omitted from those lists and must be represented explicitly. On this chat load B0 already ran 37/53 requests at once; choosing cap 32 as a potential improvement was poor judgment because it was below observed demand. The evaluator should reject or label such a candidate against the common load before treating it as an ordinary performance comparison. This does not imply that one short-chat concurrency measurement defines feasibility for mixed/session loads.

The manual comparisons show a measurable, repeatable tradeoff, so the **input and evaluation engine infrastructure can proceed** with this fixed diagnostic as its first real fixture. The next inspection point is a workload asset/card plus hash, exact server configuration and resolved settings, single-GPU lease, validated per-request records, overload and censoring accounting, and a B0-versus-candidate comparison retaining all objective metrics. A real autonomous search remains gated on source-backed mixed/session inputs, semantic MTP validation, cache preparation, longer baseline/tail qualification, and a versioned active domain. Keep this handoff documentation in its original rsynced location; implementation belongs outside it.

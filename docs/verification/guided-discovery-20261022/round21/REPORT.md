# Round21 — output-side host work

## Decision

**OH21-01 is low-priority deferred. No implementation or service promotion.** A real repeated history copy exists in continuous reasoning-token usage bookkeeping, but its measured marginal CPU cost is small at the standard 1,024-output workload. Close this branch unless profiling establishes frontend CPU pressure at longer outputs or it becomes a cheap, safely guarded maintenance change.

## Discovery and adaptation

Three online arXiv searches used July1–October22 publication bounds. The first two returned12 references/11 unique papers, mostly security, input tokenization or unrelated KV/edge work. The third failed with TimeoutError; this is not a negative search result. `paper-dispositions.json` preserves every result and review depth. Floor-First Triage (arXiv2607.05876v2) was read in fulltext as methodological context only: estimate the residual before expensive profiling. Its resource model and suggested thresholds do not establish our output-path benefit.

Four read-only local PR searches found [vLLM62728](https://github.com/vllm-project/vllm/pull/62728), pinned head535e4be5c4a0b6b5b86e92cb8d78b76110812689. Its Muse/Glimmer incremental decoding change is not a direct DeepSeek port. Its synthetic parser timings are not our serving measurements. Full files and metadata are retained.

## Exact pinned implementation

At c4557869393db4d75c483d92edd02a5125500883, native DecodeStream already exists in detokenizer.py. The engine-based parser already consumes deltas and clears old StreamState history; DeepSeekV4.1 is routed through that engine adapter. Generic incremental detokenization or whole-parser rescanning proposals therefore fail the missing-component check.

A narrower residual remains in chat_completion/serving.py721–727: continuous reasoning usage calls `parser.count_reasoning_tokens(tuple(generated_token_ids[i]))`. The ready branch of ParserEngineReasoningAdapter delegates to an existing counter; ParserEngine returns `_engine.reasoning_token_count` without reading the supplied history. However, the false-ready branch decodes/reparses the full history. Blindly removing history is incorrect. A future implementation needs an explicit valid-counter capability and existing fallback, rather than changing all parser argument semantics.

Saved Bitlane sweep.py requests chat streaming and `--per-chunk-usage`, making the branch plausible. The actual AIPerf wire request and deployed parser/configuration are not attested. Thinking off or already-closed reasoning can exercise fallback paths. Existing S01 concerns input tokenization, so this residual is distinct; recall absence is not novelty proof.

## CPU diagnostic and limits

`cpu_bookkeeping.py` AST-extracts the actual source counter methods and serving call expression. It runs them with mocked parser state, not a complete parser or HTTP runtime. A poison-history object proves the ready branch ignores history. A negative case proves empty history changes the false-ready result. The diagnostic comparison removes tuple construction only; it is not a production patch or an all-parser-compatible proposal.

| Output tokens | Chunk tokens | Baseline ms/whole stream | No-tuple diagnostic ms | Median paired saving ms |
|---:|---:|---:|---:|---:|
|1,024|1|0.665|0.143|0.521|
|1,024|5|0.129|0.029|0.100|
|4,096|1|8.197|0.477|7.734|
|4,096|5|1.607|0.097|1.511|
|16,384|1|165.987|1.889|164.098|
|16,384|5|33.390|0.375|33.004|

One warmup and seven alternating repeated passes per synthetic trace; these are not seven independent service requests. At1,024 outputs/five-token chunks, the average saving is approximately0.49 microseconds per chunk. At16k outputs the quadratic copying becomes more visible, but neither CPU saturation nor a client ITL effect is established. No GPU calls, serving benchmarks or runtime patches occurred.

## Other exclusions

- `previous_texts += delta_text` appears needed only for optional full-output logging; its flag exposure and materiality are unverified. Keep as minor hygiene, not another promoted hypothesis.
- Pydantic `model_dump_json` is already used; “use faster JSON” lacks a demonstrated missing component.
- Stream intervals already exist; increasing them can worsen client-visible ITL and is not a free latency improvement.
- Donor Muse parser speedups, GPU-input tokenization and security papers cannot provide our ROI.

## Reopen and evaluation

First establish the actual parser readiness path, per-chunk usage options and frontend CPU share. Test reasoning on/off, preclosed reasoning, tools, and usage on/off against complete reference outputs and usage. If material, use existing agent-p75/Mooncake paired service workloads; add long-output cells only where existing lengths cannot expose the quadratic growth. Measure CPU allocation/copy time, client SSE gaps/ITL, throughput, TTFT and tail guards. No benefit threshold is inherited from an unrelated paper.

Source pins and hashes: `source-manifest.json`. Per-query evidence: paper/PR receipts and isolated command journal. Candidate and exact short source quotes: `candidates.json`. This is one deferred intervention, zero implementation/service promotions.

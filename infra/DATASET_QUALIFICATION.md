# Dataset qualification checkpoint (M3)

Run date: 17 October 2026 (Asia/Kolkata).

This checkpoint freezes a bounded source selection and validates AIPerf's native input paths on the pinned Qwen server. It does **not** establish a production traffic mix, SLA, p99, capacity, or search-qualified workload. The rsynced handoff remains untouched. The machine-readable selection and source statistics are in [qualification-source-audit.json](qualification-source-audit.json), and realized request checks are in [qualification-validation.json](qualification-validation.json). Raw source and replay exports stay in `.artifacts/dataset-qualification/`.

## Sources and rights

| Source | Pin and local identity | Coverage and limits |
|---|---|---|
| [SpecBench question file](https://raw.githubusercontent.com/hemingkx/Spec-Bench/fd2c1cd7d2201ef71db4c5f4e455008f017967bf/data/spec_bench/question.jsonl) | Commit `fd2c1cd7d2201ef71db4c5f4e455008f017967bf`, SHA-256 `4b6d33e79484f9841c487ee87d1cf6aa8c6066f61d5d482ff09e5a007fafdf04` | 480 unique questions, 13 categories. AIPerf's public loader sends only the first turn; 80 rows have a second user turn. The source has no response-length, arrival, or session-timing measurements. The [repository license](https://github.com/hemingkx/Spec-Bench/blob/fd2c1cd7d2201ef71db4c5f4e455008f017967bf/LICENSE) is Apache-2.0, but component prompts have upstream origins; the repo license is not asserted to cover all prompt text. |
| [TraceLab public release](https://github.com/uw-syfi/TraceLab/releases/tag/v0.0.1) | `v0.0.1` asset `syfi_coding_trace.jsonl.gz`, SHA-256 `9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b` | 357,161 rounds, 4,265 session IDs, 43 pseudonymous users; 16 IDs recur noncontiguously and are excluded from selection. The [public schema](https://github.com/uw-syfi/TraceLab/blob/v0.0.1/README.md) has token counts, timestamps, tool metadata and prefix counts, but original text was sanitized away. AIPerf reconstructs payload text and block identities. TraceLab (SyFI Lab, University of Washington) released the dataset under [CC BY 4.0](https://github.com/uw-syfi/TraceLab/blob/v0.0.1/LICENSE-DATASET.md); these selected extracts are adaptations. |
| MBPP | AIPerf's `spec-al-mbpp` alias points to `google-research-datasets/mbpp`, `full/test` without a revision pin. The local HF cache snapshot is `4bb6404fdc6cacfda99d4ac4205087b89d32030c`. | The earlier four-request MTP check is diagnostic. It is not part of the frozen M3 selection because the alias could fetch a later revision and the loader discards task IDs. |

## Frozen search and evaluation selections

`infra/qualify-datasets.py` is the reproducible selection recipe. It checks the pinned source hashes and writes selected native-loader files under `.artifacts/dataset-qualification/`; regenerate them from the pinned source files. The evaluation files are frozen and were not replayed in this checkpoint.

For a fresh checkout, place the pinned source files at `.artifacts/capability-spike/spec_bench_question.jsonl` and `.artifacts/capability-spike/syfi_coding_trace.jsonl.gz` using the exact links above. The selector rejects either file if its SHA-256 differs from the pins above. The selected payload files are intentionally kept local; the tracked audit gives their hashes and source IDs.

| Card | Search selection | Untouched evaluation selection | Role |
|---|---|---|---|
| Semantic first turns | 384 SpecBench IDs | 96 IDs | Category-stratified diagnostic for content-sensitive MTP. Within each category, hash-sort question IDs and reserve the first fifth for evaluation. Five search prompts, one each from writing, coding, summarization, RAG and math reasoning, are the transport replay. `output_length=128` is a target ceiling, not a source output observation. AIPerf's native `single-turn` file loader preserves exact prompt text and source IDs via the `session_id` field. |
| Agentic sessions | 29 complete TraceLab sessions / 84 rounds | 6 complete later sessions / 15 rounds | Source-derived session/reuse qualification. Of 4,265 source session IDs, 39 meet this conservative eligibility rule. Sessions are 2–5 rounds, with round indices 0..N−1, peak source input+output+reasoning ≤16,384, dated explicit user/tool input events, and each submission gap ≤30 s. Search ends before 2026-04-01 UTC. Evaluation starts after that date and excludes every search user; non-null project IDs are also disjoint. One two-round search session is the bounded replay. |
| Mixed short/long contention | Pending source-backed proportions | Pending | SpecBench has short and long prompts but no measured traffic shares or outputs. TraceLab includes only 45 inputs ≤2,048 tokens across 357,161 rounds, and the bounded session slice has none. A 50/50 cross-source mix would be an invented diagnostic, so no representative mixed card is frozen yet. AIPerf 0.13.0 accepts one dataset per profile; combining sources needs a narrow adapter or a single source that supplies the mix. |

The TraceLab search slice has median source input 8,886 tokens, median output 58, median source prefix fraction 0.777, median consecutive input growth 486 tokens and median submission gap 3.635 s. The later evaluation slice has median input 12,870, so the split is visibly shifted. Search includes 59 tool-emitting rounds; evaluation includes 11. Prefix fractions are source structural metadata, not achieved Qwen cache hits. Recorded submission gaps include original provider service and tool behavior; they are not isolated human think time. AIPerf reconstructs content, so Qwen semantic behavior on this session is not evidence about the original coding task.

Across the full TraceLab source, median input is 124,018 tokens, median output 214, and median prefix fraction 0.992. The full release substantially exceeds the target 40,960 context for many rounds; the bounded selection is a feasibility filter, not a random sample. Source arrival counts in the audit are counts in **occupied** 1 s, 10 s and 60 s UTC windows across the release; they are not an arrival process for this Qwen deployment. Genuine KV reuse distance/popularity and exact prefix hit rates are missing because the released block identities and payloads are not original Qwen data.

## Realization check

Run the pinned BF16 server with the exact launch in [CAPABILITY_SPIKE.md](CAPABILITY_SPIKE.md), omitting speculative configuration. Then:

```bash
.venv/bin/python infra/qualify-datasets.py
infra/replay-qualification.sh
.venv/bin/python infra/validate-qualification.py
```

The replay uses AIPerf 0.13.0's `single-turn` and `tracelab` loaders, streaming chat, non-thinking Qwen template, server token usage, raw request export and a fixed recorded schedule for the two-turn session. The five semantic prompts allow natural EOS up to 128 tokens, but all five reached that ceiling here, so natural EOS remains unobserved. The TraceLab loader uses recorded output lengths as target ceilings. Exact selected input JSONL SHA-256 values and per-session IDs are in the audit. Validation compares exact semantic prompt text, HTTP status, stream chunks, prompt/output usage, session history and recorded versus actual turn dispatch. The request records and `validation.json` are local in `.artifacts/dataset-qualification/`.

Observed on the pinned stock server: all **7/7 requests** returned HTTP 200 with streaming chunks and server-reported usage. The five semantic first-turn prompts matched frozen text exactly in request bodies. Their actual prompt tokens were 34, 38, 689, 655 and 67; all five completed at the 128-token ceiling with finish reason `length`. The two TraceLab rounds had source inputs 3,784/3,903 tokens and realized Qwen inputs 3,796/3,930, differences of +12/+27 after reconstructed content and chat formatting. The loader set output ceilings 35/22 from source, and both target responses reached those ceilings. The second request carried `user/assistant/user` history, and the source session ID mapped consistently to AIPerf's conversation ID. The recorded submission gap was 2,320 ms; actual start-to-start gap was 2,318.4 ms, with the second turn starting 448.1 ms after the first target response ended. These are transport and scheduling observations from one session.

AIPerf reported that vLLM did not expose `usage.prompt_tokens_details.cached_tokens`, so achieved prompt-cache hits were not measurable in this run. It also dropped its optional GPU telemetry worker after missed heartbeats; raw request and server metrics exports completed. The exact server command/state/log and AIPerf raw exports were saved locally, and the server was stopped after the replay (GPU memory returned to 0 MiB).

**Next inspection gate:** review this audit and actual replay differences. Before B0 calibration or adaptive search, obtain a defensible short/long traffic mix and operating-load basis, prepare a mixed contention card with source-derived proportions, and validate that pack on Qwen. If the intended deployment has no measured traffic, use an explicitly diagnostic mix and keep any performance conclusions scoped to that mix.

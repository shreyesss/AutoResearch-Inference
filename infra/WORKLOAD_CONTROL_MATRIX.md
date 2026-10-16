# AIPerf workload control checkpoint

Run date: 17 October 2026 (Asia/Kolkata). This inspection stage verifies how the pinned AIPerf 0.13.0 controls become actual Qwen requests. It is not B0 load calibration, a vLLM setting comparison, an SLA result or a production-representative traffic claim. The selected source audit is in [DATASET_QUALIFICATION.md](DATASET_QUALIFICATION.md). Generated payloads and full raw exports are local under `.artifacts/workload-controls/`; the tracked [workload-control-manifest.json](workload-control-manifest.json) records input hashes and intended scheduling.

## Three distinct workload cards

| Card | Frozen inputs and timing | What this card checks | What it cannot establish |
|---|---|---|---|
| SpecBench semantic | Five category-diverse first-turn prompts selected from the 384-search/96-evaluation split. AIPerf `single-turn`; one request/s diagnostic pacing; 128-token natural-EOS ceiling. | Exact meaningful prompt text, target tokenization, streamed usage. Previous pinned Qwen replay already validated 5/5 HTTP 200 and exact request text; the frozen asset hash is reused here. | Source arrival rates, source outputs, production mix, natural EOS frequency. All five prior responses hit the 128-token ceiling. |
| TraceLab recorded session | One complete four-turn search session `codex:1db326cd-3c43-ad82-b907-27bc1f12c287`, native `tracelab` loader, fixed schedule. Source submission offsets and source input/output counts are in the manifest. | Context growth, recorded within-session gaps, previous-response dependency and reconstructed prefix structure. | Original prompt semantics or cross-session arrivals. TraceLab omitted original text and native conversion resets **each** session's first timestamp to zero. |
| Mooncake diagnostic | `control-agentic-config.json`, seed 42, six sessions × three turns, native `synthesize agentic-code` to Mooncake JSONL, then native `mooncake-trace` fixed-schedule replay with 64-token blocks. | Controlled global/group/session prefix topology, incremental input growth, fast/slow continuation gaps and concurrent initial burst. | Measured human/tool gaps, actual production arrival shares or achieved KV-cache hits. All six first turns start at timestamp zero by generator design. |

The Mooncake control assumptions are explicit: max generated prompt 4,096 tokens; 256 global prefix tokens, 128 group-shared tokens, bounded session prefix sampled around 256/192 mean/median; two equally weighted groups; 64-token blocks; 64–256 new input tokens per later turn; 48–128 requested output tokens; 75% fast-gap component; exactly three turns; no probabilistic reset or restart. The JSONL continuation `input_length` is **incremental**, while actual chat requests accumulate history. Requested output length is a ceiling. `hash_ids` encode intended text sharing; target Qwen tokenization and cache reuse require separate measurement.

No cross-source mixed pack is called representative here. The TraceLab selection contains no observed concurrent source sessions and almost no short prompts. SpecBench has short and long semantic prompts but no measured arrival or output distribution. Joining them at an arbitrary ratio would be a diagnostic policy, not source-derived traffic.

## Execution and inspection

From repo root, with pinned stock Qwen server healthy at `127.0.0.1:8000`:

```bash
.venv/bin/aiperf synthesize agentic-code --config infra/control-agentic-config.json --num-sessions 6 --seed 42 --output .artifacts/workload-controls/agentic-synth
TRACE=$(find .artifacts/workload-controls/agentic-synth -path '*_6s_seed42_*/dataset.jsonl' | head -1)
.venv/bin/aiperf validate mooncake-trace --input "$TRACE"
.venv/bin/python infra/prepare-workload-controls.py --generated-trace "$TRACE"
infra/replay-workload-controls.sh
.venv/bin/python infra/validate-workload-controls.py
```

The replay reuses AIPerf's streaming chat endpoint, non-thinking Qwen template, server token counts, per-chunk usage and raw HTTP export. The pinned tokenizer is exposed to AIPerf's offline parallel workers through a repo-local Hugging Face cache by `prepare-aiperf-tokenizer-cache.sh`; that helper checks the tokenizer SHA-256 before creating the local snapshot link. The validation checks planned request count, session/turn IDs, source/output ceilings, actual prompt/output tokens, message-history growth, continuation dispatch after prior response, source versus target timing, first-turn burst spread and shared first-turn text. It records raw export SHA-256 values. The previous semantic validation is reused only because the asset SHA is identical; its raw evidence remains in `.artifacts/dataset-qualification/`.

## Findings from live replay

The four TraceLab requests and all 18 Mooncake requests returned HTTP 200 with streamed usage. TraceLab source input counts `[4131, 4276, 5498, 7212]` became `[4143, 4301, 5519, 7246]` Qwen prompt tokens: chat reconstruction added 12–34 tokens. Its source submission offsets were `[0, 1646, 4259, 5989]` ms, while actual offsets were `[0, 30986, 33035, 35984]` ms. AIPerf dispatched each continuation about 1 ms after the prior target response. The first target response took roughly 31 seconds, so a response-dependent replay cannot preserve the recorded absolute offsets when target latency differs.

Mooncake's six first turns started within **3.571 ms**. Its configured response-relative continuation delays were realized within **0.678–1.983 ms**. Source `hash_ids` share six 64-token blocks among same-group first turns and four among different-group turns. Actual first-turn request text shared 1,695–1,702 leading characters within groups versus 1,141 across groups; these are text-prefix checks, **not** measured server KV-cache hits. Target prompt counts exceeded planned cumulative synthetic tokens by 12–40 because chat formatting and history separators add tokens. Seventeen responses reached their requested output ceiling; one stopped naturally at 60 of 64 tokens. These measurements are in [workload-control-validation.json](workload-control-validation.json); full exports remain under `.artifacts/workload-controls/`.

The first two 18-row attempts failed during AIPerf input preparation, before sending requests. Its parallel decode worker could not load a local Qwen tokenizer path after forcing Hugging Face offline mode; both relative and absolute paths failed. The workaround exposes the pinned local tokenizer as its Hugging Face repository/revision inside a repo-local offline cache, verified in a direct 18-item parallel decode. A separate three-session/9-row replay succeeded. Failed logs remain local as `mooncake-first-attempt-console.log` and `mooncake-second-attempt-console.log`.

## Next inspection gate

Review the three card roles and all source-to-target differences. Then define an explicit load basis for M4: deployment traces if available, or a clearly labeled diagnostic mix and bounded load sweep. M4 will bracket sustainable B0 load with repeated windows and cache reset/burn-in rules. M5, after that, tests whether selected vLLM parameters have reproducible effects at ordinary and near-capacity load. Neither a synthetic burst nor this small transport check establishes parameter sensitivity.

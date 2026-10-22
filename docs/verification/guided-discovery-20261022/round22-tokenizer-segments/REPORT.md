# Round 22 — S01 full-chat added-token segmentation

## Decision

**Advance a bounded CPU integration investigation under existing S01; defer production integration and service qualification.** This is an existing donor component selected to avoid session-cache complexity, not a new algorithm or new hypothesis identity. No original checkout, registry, guard, serving deployment, model, GPU or canonical state was modified.

The exact target has an empty normalizer and a complete added-token table. The donor already provides an HF-backed splitter and an assembly helper. Sending only the intervening ordinary spans to the existing guarded native CPU encoder matched complete reference IDs on the finite test set and improved many longer synthetic full-chat encodes locally. It regressed on short marker-heavy prompts against the strongest available full-operation baseline.

**Primary-objective caveat:** prompt tokenization savings directly concern admission, TTFT and CPU capacity. The campaign's long-output ITL objective would require a demonstrated shared-host contention or streaming pathway. That is unknown; the local input-processing savings do not improve S01's ITL ranking by themselves.

## Existing implementation and exact change being considered

Pinned donor: `asu-idi/toktier@0591fe18235f3e64f0576fa7f77a0804af1ba5c2`. The existing [`AddedTokenRouter`](https://github.com/asu-idi/toktier/blob/0591fe18235f3e64f0576fa7f77a0804af1ba5c2/src/toktier/routing/added_route.py) explicitly documents two options: implemented whole-input reference routing, and the prior prototype's split-and-splice path. It says the conservative routing choice was deliberate; `plan_for` already exposes segments and `assemble` is already ported.

The existing [`AddedTokenFrontend`](https://github.com/asu-idi/toktier/blob/0591fe18235f3e64f0576fa7f77a0804af1ba5c2/src/toktier/frontend/added.py) delegates exact matching to HF's added vocabulary using a splitter-only WordLevel tokenizer. It handles the raw `normalized=False` phase first, then the normalized face on remaining spans. Matching flags and leftmost/longest behavior come from the oracle implementation rather than a new regex matcher. IDs are remapped from splitter-assigned values to the original artifact. An artifact hash binds the exported table.

The native [`guarded_full_with`](https://github.com/asu-idi/toktier/blob/0591fe18235f3e64f0576fa7f77a0804af1ba5c2/crates/toktier-routing-core/src/fast_cpu.rs) keeps its added-token gate, reference fallback and byte-closure guard. The experiment did **not** disable any gate. Each ordinary segment calls the original public native encoding method. Literal IDs come from the HF splitter. The native core contains added-token handling, but successful segmentation does not certify its raw added-token implementation or justify bypassing the guard.

Conceptual adapter, only after semantic admission:

```python
plan = frontend.scan(rendered_text)
ids = native.encode(rendered_text) if plan is None else assemble(plan, native.encode)
```

The source-plan vLLM wrapper [`deepseek_v41.py`](https://github.com/vllm-project/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/tokenizers/deepseek_v41.py) renders chat and calls `self.encode(prompt, add_special_tokens=False)`. This makes an ID-only full-rendered-text comparison relevant. It does not prove the live loader, sidecar state or tokenizer runtime options match these files.

## Semantic eligibility and fallback boundary

Target: `deepseek-ai/DeepSeek-V4.1-Flash-1017`, revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, tokenizer JSON SHA `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b`.

- Normalizer is an empty Sequence. All 1,283 added tokens have `single_word=False`, `lstrip=False`, `rstrip=False`.
- 1,229 are special/raw-face, 7 non-special/raw-face and 47 non-special/normalized-face. In particular ID 128799 `<｜System｜>` is **normalized=True, special=False**. Original insertion order, ID and every flag are retained.
- No actual target literal is a proper prefix of another. Longest-prefix behavior therefore receives a separately labeled synthetic control, not a fictitious target case.
- The donor refuses normalized-face tokens with a nonidentity normalizer by default; that refusal was exercised. No opt-in override was used.
- Ordinary spans continue through the original native guard; any native failure or added-token recognition keeps its existing reference fallback. Complete input should fall back to the normal full tokenizer when artifact/table mismatch, altered `split_special_tokens` semantics, unsupported normalizer, loader-added tokens, requested offsets, unhandled preprocessing/postprocessing, or another unsupported option is detected. These integration guards are proposed, **not implemented by this standalone probe**.
- The probe uses `add_special_tokens=False` on complete already-rendered text. It does not test offsets, truncation, padding, pair inputs, `add_special_tokens=True`, mutable tokenizer state, or the full production facade. It does not add BOS a second time; the renderer supplies its own markers.
- There is no prior session or prefix state to invalidate. Whole rendered text is reprocessed on every call. Renderer rewrites are therefore accepted as fresh inputs, rather than treated as appends.

## Executed finite correctness diagnostic

Unchanged donor Python components and the previously built pinned native CPU binary were used from `round20-native-tokenizer/venv312`, Python 3.12.15, HF `tokenizers==0.22.2`, Darwin arm64. No build or registry changes were needed. The binary SHA/build facts are recorded in `segment_probe.json`.

| Observation | Result | Scope |
|---|---:|---|
| Complete target ID matches | 5,429 / 5,429 | Finite cases, not independent serving traces |
| Plan reconstructs original text | 5,429 / 5,429 | Target identity normalizer and non-stripping flags |
| Ordinary-span native calls | 8,833 | All actual `gigatoken_full` routes |
| Ordinary-span HF/engine fallback calls | 0 / 0 | This diagnostic's denominator only |
| Exact target-renderer inputs | 8 | Full chat/thinking, drop-thinking choices |
| Unchanged native full-chat controls | 8 / 8 HF fallback | IDs still equal; default gate preserved |
| Synthetic flag/longest-prefix controls | 7 / 7 | HF splitter + HF ordinary spans; not native target tests |
| Nonidentity-normalized-face guard | Refused | Expected unsupported configuration |

Target cases comprise all 1,283 literals in four contexts (5,132), 28 partial-marker cases, 256 mixed/adjacent raw and normalized token cases, five boundaries and eight exact rendered inputs. This fixture spans **0–1,549 characters and 0–552 output tokens**, with at most eight ordinary segments. Unicode contexts include CJK, combining marks, emoji/ZWJ, controls and whitespace. This finite selection is not broad Unicode validation. Token ID equality does not imply offset equivalence; no offsets are claimed.

## Full-operation CPU comparison, including the stronger baseline

`timing_probe.py` compares three existing/candidate paths on the **same full rendered inputs**, without a session cache:

1. External HF Python `encode(...).ids`.
2. Unchanged native wrapper `encode` — all timed full-chat calls actually use its embedded HF reference.
3. Existing splitter + assembly + guarded native ordinary-segment calls.

Twenty-four synthetic requests: requested ordinary payload sizes 256 / 2,048 / 8,192 / 32,768 characters × 1 / 4 / 16 user turns × two deterministic content variants. Actual rendered inputs span **334–33,751 characters and 137–16,813 tokens**, with at most 32 ordinary segments. Each method gets two warmups and nine randomized-order paired repetitions per case. Setup, ID equality assertions and route counter reads are outside the timed interval. The prompts and warmed lexicon are reused; this is local warm CPU timing, not cold behavior, concurrent frontend capacity, Linux x86 deployment performance or real workload prevalence.

| Comparison | Winning case medians | Median of per-case latency ratios | Ratio range | Per-case saved-time range |
|---|---:|---:|---:|---:|
| Segmented / external full HF | 23 / 24 | 0.603 | 0.463–1.009 | −1.25 µs to +3,256.46 µs |
| **Segmented / unchanged guarded-native full operation** | **20 / 24** | **0.865** | **0.635–1.443** | **−45.17 µs to +1,668.12 µs** |

Timed route denominators: 216 calls per full-operation method. The guarded-native full baseline reports 216 `hf_full_added_token`; segmentation makes 3,024 `gigatoken_full` ordinary-segment calls. Neither is mislabeled as the other's engine path. The splitter remains HF work even though ordinary spans are native.

The stronger baseline materially reduces the apparent benefit. Four 256-character, 4/16-turn cases regress approximately 17–44% against it. These small cases favor avoiding splitter/per-segment overhead. The data support investigating longer inputs; they do **not** establish a production threshold. No confidence interval or tail/service gain is claimed from nine warm repetitions.

## Self-critique and next discriminator

The current `inference-critic` skill was read and applied. This is **self-review**, not a controlled evaluation of the skill. Its route-denominator and simpler-full-baseline guidance changed the conclusion: a large apparent HF-relative saving becomes a smaller conditional opportunity with explicit regressions against the stronger baseline.

Strongest support: existing semantic splitter, exact target finite ID agreement, no session identity requirement, and useful local longer-input CPU savings beyond unchanged guarded full encoding.

Strongest objection: actual host input-processing exposure is unknown; short marker-heavy prompts regress; sidecars/runtime tokenizer options and integration guards are unverified; an isolated ARM native build is not the deployed frontend. The frozen ITL metric may not benefit at all.

Next cheapest diagnostic is a CPU replay of exact serialized prompts and effective tokenizer configuration from retained serving input, if available, on the actual frontend CPU/binary, comparing **unchanged full operation** against this full-input path. Preserve IDs, runtime options, route counts, per-input lengths, marker counts, timings and errors. No session cache is needed. Stop if semantic state differs without a safe full-reference fallback, if source-equivalent replay mismatches, or if overhead removes the advantage on the relevant inputs. A live serving experiment remains deferred and requires separate authorization.

Existing Mooncake/agent-75 can later measure end-to-end TTFT/capacity effects if they send text through the same frontend. If they submit token IDs or bypass rendering/tokenization, they do not expose this change. The custom CPU diagnostic is justified because those serving metrics do not isolate exact added-token semantics or native/reference routes. ITL attribution additionally needs evidence of contention with decoding/streaming; no new GPU experiment is requested.

## Commands and retained evidence

```sh
round20-native-tokenizer/venv312/bin/python round22-tokenizer-segments/segment_probe.py
round20-native-tokenizer/venv312/bin/python round22-tokenizer-segments/timing_probe.py
round20-native-tokenizer/venv312/bin/python round22-tokenizer-segments/timing_analysis.py
```

`timing_probe.py` first reproduces the finite correctness fixture; that setup is excluded from measured time. `timing_analysis.py` only analyzes retained measurements. Original donor source copies, target table, exact source URLs/hashes and the skill version are retained. The exact target JSON and native binary remain pinned by their prior artifacts and hashes; this report does not imply binary upload, canonical import or S3 publication.

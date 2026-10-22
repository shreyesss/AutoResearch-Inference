# Source-only benchmark exposure check

## What the saved runner establishes

`bitlane/bench/sweep.py:225` launches AIPerf with `--endpoint-type chat --streaming`. The workload loader passes the selected YAML's AIPerf arguments and configured extra inputs. Saved `keyed.py` only injects the API key into AIPerf's own CLI; it is not a separate request renderer. No actual request payload or AIPerf internal chat-endpoint builder was retained in this source subset, so this audit does not assert an observed wire payload or exact runtime loader.

- **agent-p75:** the saved YAML defines 6,144 shared prefix tokens + 2,048 unique tokens, eight prefixes, 1,024 output tokens, thinking on/effort75. This is shared-prefix synthetic traffic, **not proof that one request is a strict append to a previous request from the same session**. Different unique suffixes can require splice replacement rather than append.
- **Mooncake median:** fixed-schedule `mooncake_trace`, preserved `hash_ids`, pinned median JSONL digest. Hash-prefix reuse establishes desired KV/workload structure, not string-level append continuity or tokenizer-cache identity. The saved runner preserves defaults for thinking/effort; the exact custom tokenizer defaults are shown below.
- **multiturn:** four-turn growing histories is configured as a separate workload, and is a better eventual diagnostic for append/session exposure. Its thinking-disabled setting changes renderer behavior relative to the two primary workloads.
- The runner enables `AIPERF_HTTP_X_SESSION_ID_FROM_CORRELATION_ID` only if `w.get('session_header')` is truthy. None of these three saved workload YAMLs contains that key. Inherited environment/another runtime override was not inspected, so this is **not proof that headers are absent on the wire**. It does mean these artifacts do not establish explicit per-conversation cache identity.

## Exact pinned renderer changes the interpretation of plain text timing

At vLLM `c4557869393db4d75c483d92edd02a5125500883`, `vllm/tokenizers/deepseek_v41.py:68–118` wraps chat-template application, invokes the custom renderer, defaults thinking to true and effort to high, and calls `self.encode(prompt, add_special_tokens=False)` on the serialized string. This source branch is the required route, not a live-attested invocation.

`deepseek_v41_encoding.py:545–565` defaults `add_default_bos_token=True` and starts a full conversation with `<｜begin▁of▁sentence｜>`. Role/system/assistant markers are also part of serialization. `add_special_tokens=False` does **not** remove literals already present in that serialized string.

The exact TokTier native `AddedTokenGate` recognizes target added literals and the `guarded_full_with` path uses native HF reference when a recognized added token is emitted. A bounded CPU demonstration (`route_check.py/json`) observed:

| Synthetic input | Native route |
|---|---|
| Plain body without rendered role markers | Gigatoken |
| Ordinary standalone suffix | Gigatoken |
| Suffix with User/Assistant added literals | HF added-token guard |
| Exact serialized one-user chat prompt | HF added-token guard |
| Exact serialized one-user thinking prompt | HF added-token guard |

All five native output-ID comparisons matched HF. These are illustrative source-derived inputs, **not captured benchmark requests or measured frequencies**.

Thus the timing table's very fast plain native-full baseline is not representative of a whole chat string that includes recognized BOS/role markers. A whole rendered chat prompt would follow the guarded-reference path under these premises; a repair suffix may use either native or guarded-reference encoding depending on which markers it contains. Even guarded suffix encoding can avoid re-encoding the whole prior prefix.

## Remaining blockers to a practical claim

The shared prefix/token length settings alone do not establish a persistent tokenizer session. A stateless chat API needs a correct, bounded identity/key and exact previous rendered state; gateway stickiness is insufficient. Renderer rewrites remain real: the timing's `thinking + drop_thinking=True` transitions changed previous text and correctly used full-reference fallback. Therefore neither primary benchmark should be assigned an assumed repair-hit rate.

Before a serving experiment, capture a bounded, explicitly permitted payload/renderer trace or replay the actual generator offline; measure exact prefix continuation, rewrites, added-token fallback and cache identity. Existing standard benchmarks can still test aggregate service effects after integration, but they cannot substitute for demonstrating that the optimization is exercised. No server, node probe or GPU experiment was run here.

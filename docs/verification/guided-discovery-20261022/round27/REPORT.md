# Round27 — bounded tokenizer version bridge

## Decision and scope

The frozen TokTier CPU package and its existing split/assemble components produced the same complete token IDs as the effective Transformers 5.16.1/tokenizers 0.23.2 loader on **74 reused fixture cases (70 distinct input strings)**. Both the original checkpoint JSON and the effective 0.23.2 serialization loaded successfully in the old native package. This closes the specific *finite test* gap left by round23; it does not prove general cross-version equivalence or deployment compatibility.

This is additional CPU evidence for existing **S01**, `hypothesis:a5d530ce5da737fb780bdd0aed42e9126ba955b1375307b0fe3592bbf63ad4ed`, on planned baseline `baseline:3b223afd8c30209a2c71d6f8cdd36e4da640b4bc67cdf331f108d2d2496131ca`. Its accepted status means bounded CPU investigation. Native integration and service promotion remain unqualified. No new hypothesis, registry admission, serving patch, native rebuild or canonical write was made.

## Exact comparison

Separate Python processes executed:

1. Frozen round20 `venv312`: Python tokenizers **0.22.2**, compiled TokTier CPU binary at donor commit `0591fe18235f3e64f0576fa7f77a0804af1ba5c2`. The pinned Cargo.lock also specifies Rust tokenizers **0.22.2**, so full HF fallback in the native binary is old-reference evidence, not native Gigatoken evidence.
2. Frozen round23 `venv`: Transformers **5.16.1**, tokenizers **0.23.2**; real `TokenizersBackend.from_pretrained` with local files only, trust_remote_code=False and truncation_side=left. No vLLM/model package was imported.

Target: `deepseek-ai/DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`. Raw tokenizer SHA is `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b`. Exact effective artifact and binary hashes are in the worker outputs and source manifest. The new loader's serialization equals round23's retained effective artifact structurally. All inputs remained byte-identical during each worker.

For both artifact byte representations, the native worker ran:

- Unchanged guarded full `CallbackEncoder.native_fast_cpu.encode`.
- Existing `AddedTokenFrontend.scan` and `assemble`, passing only ordinary spans to that same guarded native encoder. Literal recognition comes from the donor's HF splitter under Python tokenizers 0.22.2; this is not a newly native added-vocabulary implementation.
- Old Python tokenizers 0.22.2 whole-input reference, recorded separately.

The new reference worker independently encoded each complete input through raw JSON, effective JSON and the real loaded wrapper with `add_special_tokens=False`. Complete ID arrays are retained in both outputs; comparison did not use decoded text or just output counts.

## Results and actual routes

Counts below are **per artifact**; raw and effective repeat the same inputs and must not be presented as independent workloads.

| Check | Raw artifact | Effective artifact |
|---|---:|---:|
| Guarded full IDs equal loaded 0.23.2 | 74/74 | 74/74 |
| Full calls actually on Gigatoken | 12 | 12 |
| Full calls using HF added-token fallback | 62 | 62 |
| Segmented complete IDs equal loaded 0.23.2 | 74/74 | 74/74 |
| Ordinary segment calls actually on Gigatoken | 118/118 | 118/118 |
| Ordinary segment reference fallbacks | 0 | 0 |
| Old Python 0.22.2 reference IDs equal loaded 0.23.2 | 74/74 | 74/74 |
| Split plans reconstruct the complete text | 74/74 | 74/74 |

Raw and effective native outputs agree on all 74 full and all 74 segmented results. Raw and effective 0.23.2 references agree with the loaded wrapper on all 74. The 62 full fallback matches cannot establish native full-text added-token support; the 118 ordinary native calls plus complete assembled equality provide the narrower segmented-path evidence.

Fixtures are selected from the earlier round20/22 code: all changed target added-token IDs, representatives of all three actual flag classes, BOS/EOS, earlier Unicode/whitespace/partial-marker cases and the same eight exact rendered chat/thinking cases. They cover 0–1,549 characters and 0–552 output tokens. Four duplicate input strings remain because prior named fixtures overlap. This is a deliberate compatibility selection, not a random corpus or 74 independent production workloads. No thousands of near-identical cases were generated.

## Negative boundary and unsupported semantics

Changing only the loaded wrapper's `split_special_tokens=True` produces different complete IDs on **14/74** fixtures. The segmented default path matches default semantics and therefore disagrees with that override on those 14. These retained counterexamples show that artifact identity alone cannot authorize the adapter; runtime flags matter. There is no implemented production admission layer in this diagnostic, so this report does not claim the override now automatically falls back. A later adapter must reject or route unsupported options to the effective reference.

Still unsupported/unqualified: offsets; `add_special_tokens=True` and postprocessing; paired inputs; truncation/padding; mutable added vocabulary; nonidentity normalizer; arbitrary runtime changes; full facade/session lifecycle; certified family registration; all other dependency versions. No native binary was rebuilt against 0.23.2. No general Unicode/BPE equivalence proof follows from 70 strings.

## Source and import audit

Before execution, inspected pinned `fast_cpu.rs::guarded_full_with` (675–715), `AddedTokenFrontend.scan`/`assemble` (503–559), Cargo.lock and prior loader materialization code. Existing native added-token and byte-closure guards were left intact. Direct experimental construction does not change the normal facade's certification/registry policy. Installed selected donor Python files match pinned source bytes.

Both workers installed model/accelerator import guards and blocked socket connections before importing tokenizer packages. Actual worker receipts record **zero forbidden import attempts, zero forbidden modules loaded and zero network attempts**. Reference startup reported PyTorch unavailable; it was not loaded. No GPU, CUDA, MPS, model or serving command was issued. This is a diagnostic guard, not a claim of a general process security sandbox.

Source copies and original paths/hashes are retained in `source-manifest.json`; source pin and byte identities remain distinct from live deployment attestation.

## Next useful decision

This check found no version/serialization counterexample in the bounded selection. It justifies retaining S01's simpler full-input segmentation alternative for further controlled CPU work. It does not raise S01's primary service ranking: tokenization directly concerns admission, TTFT and CPU capacity. Frozen long-output ITL improvement still requires an observed contention/streaming pathway, which remains unknown. Earlier round22 timing was under 0.22.2; it is not a new 0.23.2 timing result.

Before implementation qualification, the remaining useful checks are exact runtime-option admission and a deployment-representative CPU/reference integration with the simplest full-operation baseline. No additional GPU experiment is requested or authorized here.

Self-review used the retained inference-critic skill's actual-route and simpler-baseline requirements. Field usefulness is evidenced by distinguishing 62 fallback calls and the 14 runtime-state counterexamples; this is not a controlled evaluation of skill quality.

## Reproduction

From this directory, using the existing frozen environments:

```sh
../round23-tokenizer-loader/venv/bin/python prepare_cases.py
../round20-native-tokenizer/venv312/bin/python worker.py native
../round23-tokenizer-loader/venv/bin/python worker.py reference
../round23-tokenizer-loader/venv/bin/python compare.py
```

`commands.json` records the actual commands and their tool-reported results. `comparison.json` retains all result counts and negative cases. These are diagnostics, not unit tests of an implemented serving adapter. Frozen earlier rounds remain unchanged.

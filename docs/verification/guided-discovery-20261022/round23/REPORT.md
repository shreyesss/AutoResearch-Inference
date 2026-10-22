# Round 23 — S01 exact tokenizer loader and sidecar gate

## Decision

**The default checkpoint-sidecar concern is resolved for one exact supported dependency combination; cross-version native compatibility and live admission remain open.** Keep S01 accepted for bounded CPU investigation. Do not revise round22's historical test scope or promote service readiness.

The exact pinned vLLM source requires a newer tokenizer than the donor tests used. Actual tokenizer-only materialization at the declared lower bounds succeeded without importing a model/backend accelerator or touching serving state. Although the sidecar's BOS/EOS flags initially looked inconsistent with raw JSON, the loader resolves named tokens from the raw added-token map. All 1,283 effective added-token entries, IDs and flags therefore match the raw artifact in this tested default load.

An explicit runtime option, `split_special_tokens=True`, changes output IDs while the checkpoint bytes remain the same. An adapter must bind runtime semantics as well as file hashes.

## Pins and dependency boundary

| Component | Inspected or executed identity | What this establishes |
|---|---|---|
| Target checkpoint tokenizer | `deepseek-ai/DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170` | Exact cached tokenizer/config bytes |
| Raw tokenizer SHA | `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b` | Same target used in earlier probes |
| Config SHA | `6ac8c8dc065ed118161d02dd532749ae3f52c243deac27872134fae2f50d8547` | Exact checkpoint sidecar |
| vLLM source | `c4557869393db4d75c483d92edd02a5125500883` | Source plan, not installed-image attestation |
| Declared dependencies | `transformers >=5.16.1,<5.20.0`; `tokenizers >=0.23.2` | The source requirement is a range, not a runtime lock |
| Executed combination | Transformers **5.16.1**, tokenizers **0.23.2**, Python 3.12 | One allowed lower-bound combination only |
| Earlier native/proxy probes | TokTier pinned native/reference **0.22.2** | Not automatically a test of declared vLLM dependencies |

Exact [`requirements/common.txt`](https://github.com/vllm-project/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/requirements/common.txt) was fetched with its commit and retained SHA. The pinned model's `special_tokens_map.json` URL returned **404**; that response is retained. No weights or model configuration were fetched. The existing exact tokenizer JSON/config were reused.

The isolated environment installed binary wheels for explicitly selected Transformers 5.16.1/tokenizers 0.23.2. `install-report.json` contains package versions, download URLs and archive hashes. No Torch distribution was installed. Fetched version-tag source files and actual installed files have matching SHA-256 for the loader, base class, import utilities and module initializer. This is a local CPU environment, not the serving node's installed wheel set.

## Exact loader chain and sidecar result

The vLLM [`DeepseekV41Tokenizer.from_pretrained`](https://github.com/vllm-project/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/tokenizers/deepseek_v41.py) directly constructs `TokenizersBackend.from_pretrained`, then applies the V4.1 prompt wrapper and cached metadata wrapper. The general registry passes tokenizer revision/configuration and defaults generation/draft truncation to the left. This probe called the actual Transformers loader with a local directory containing only the two exact tokenizer files, `local_files_only=True`, `trust_remote_code=False`, `truncation_side='left'`. It did **not** import or execute the vLLM package.

The sidecar sets BOS `<｜begin▁of▁sentence｜>` and EOS/pad `<｜end▁of▁sentence｜>` to `normalized=True`; raw added-token IDs 0/1 are `normalized=False, special=True`. This is a real input discrepancy, but not a demonstrated effective mismatch.

In [`tokenization_utils_base.py`](https://github.com/huggingface/transformers/blob/v5.16.1/src/transformers/tokenization_utils_base.py), the legacy-loading path extracts the raw `tokenizer.json` added-token map, converts sidecar values to `AddedToken`, and then replaces named special-token entries using `added_tokens_map.get(str(init_kwargs[key]), init_kwargs[key])`. The backend constructor preserves these entries rather than blindly replacing their flags with the sidecar's text.

**Executed observation:** zero differences across all 1,283 raw/effective added-token rows. The effective BOS/EOS rows retain `normalized=False, special=True`; `<｜System｜>` retains its distinct target `normalized=True, special=False` row. Normalizer, pre-tokenizer, post-processor, padding and truncation serialization sections are unchanged.

The model serialization differs in two ways: merge strings become explicit two-item arrays, and absent `ignore_merges` becomes `false`. `serialization_analysis.py` compares the complete lists/vocabulary and confirms exact data equality after those two representation/default normalizations. This is not a general proof of algorithm equivalence between tokenizers 0.22.2 and 0.23.2.

## Runtime semantics and executed controls

Default observed state:

| Setting | Value |
|---|---|
| `split_special_tokens` / backend `encode_special_tokens` | false / false |
| `add_bos_token` / `add_eos_token` | false / false |
| `model_max_length` | 1,048,576 |
| `truncation_side` / `padding_side` | left / right |

The vLLM source wrapper uses `encode(prompt, add_special_tokens=False)` for rendered chat and passes through explicit truncation/max length. Its prompt encoder supplies the markers itself. Model maximum length here is tokenizer metadata, **not an asserted deployed context limit**.

Seven bounded complete ID checks compare raw **0.23.2** against loaded **0.23.2**: markers, Unicode, empty input and four exact-renderer combinations. All match. This is a loader diagnostic, not another broad finite suite and not native execution.

The negative control loads the same files with `split_special_tokens=True`; the backend flag becomes true and marker-containing input yields different IDs. The adapter's raw artifact hash alone cannot protect this condition. Mutable runtime state, effective added vocabulary, normalizer, postprocessing, encoding options and tokenizer version must be captured or guarded at integration.

## CPU safety and import scope

Before materialization, the source import paths were inspected: Transformers advertises lazy/torch-free top-level import; tokenizer modules use optional Torch availability checks, and the isolated environment has no Torch. The probe additionally blocks imports of Torch/CUDA/CuPy/Triton/MLX/TensorFlow/JAX/vLLM and blocks socket connections. Actual counts: **zero forbidden import attempts, zero forbidden loaded modules, zero network attempts during materialization**. Transformers reported that only tokenizer/configuration/data utilities were available.

No model class was instantiated, no weights were loaded, no GPU/MPS/device helper was invoked, no native TokTier gate or registry was changed, and no serving or canonical state was written. Download/install activity is separately recorded; the zero-network statement applies to the local loader probe, not the earlier bounded source/package fetches.

## What remains unresolved and next useful step

1. **Live packages and overrides:** source dependency ranges do not identify the actual deployed Transformers/tokenizers versions, sidecars, added tokens or effective options. This remains an admission requirement.
2. **Cross-version native parity:** earlier native core and HF reference used 0.22.2. The observed effective-table equality does not prove that native results equal 0.23.2 on the whole target domain. A bounded bridge should compare the existing compiled native/segmentation path against the effective loaded target under the chosen version, without weakening the original default guards.
3. **Serialized identity:** a materialized backend can serialize differently despite equivalent data. Do not admit it through a raw-SHA registry or silently substitute the raw file. Any adapter needs an explicit effective-artifact/runtime identity and reviewed parity evidence.
4. **Service value:** the previous local warm CPU saving concerns input processing. Current long-output ITL benefit still requires shared-host contention/streaming evidence. No ITL/TTFT/throughput improvement is claimed by this loader test.

This closes a concrete source/loader uncertainty while retaining the version and runtime gates. It does not require another speculative paper search or a GPU experiment.

## Reproduce

```sh
round23-tokenizer-loader/venv/bin/python round23-tokenizer-loader/loader_probe.py
round23-tokenizer-loader/venv/bin/python round23-tokenizer-loader/serialization_analysis.py
```

The installation and source-fetch receipts, selected source copies, exact local input files, effective serialization, CPU script/results and manifest are retained. The environment directory itself is a convenience, not a portable/recoverable research artifact claim.

# Round83 — QuantMLA and the actual mixed cache format

## Decision

**Zero new hypothesis identities.** One previously unread paper was examined in fulltext, with five component dispositions below. Retain its function-aware quality diagnostic and a concrete correction to baseline cache-format interpretation. Stop the direct algorithm/kernel transfer at the source contract; do not manufacture a cache-format activation proposal without the resolved backend/configuration evidence.

No GPU, native kernel, model, serving process, compiler, canonical writer, or cloud action ran. The source plan remains `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, B200 TP1/DP4/EP4. Source support is not live selection.

## Retrieval and prior coverage

The retained OpenAlex work `W7214988073` is **QuantMLA: Function-Aligned Dual-Path Quantization for Low-Bit MLA KV Caching**, arXiv `2609.36760`: v1 submitted September 29 and v2 revised September 30, 2026. Round37 contained its title/metadata and explicitly marked it unread. This round used selected-source import and `investigate`, then explicitly fetched v2. The unversioned and v2 bodies are byte-identical in these receipts; both identities and their original version qualification remain preserved. The paper says code will be released upon acceptance; no implementation repository was inferred.

No new provider search was needed to resolve this selected lead. Actual compact recall covered all 105 literal `cache` matches in two pages, plus 44 `precision` matches, from a 149-card inventory. A first long literal query returned zero and was not treated as semantic absence. Read-only report search complemented cards. LC01/LC02 rejected particular claimed lossless resident ports; LC03 remains an exact-byte codec question, M04 a capacity/offload question, AT03 a prefill gather reuse question. None establishes that lossy cache quantization is impossible or useful here. AT02 and CR64 already cover sparse reuse/retention, so generic tile reuse is not new yield.

Read-only PR search found zero `QuantMLA` bodies, four `nvfp4_ds_mla` hits, and 289 `NVFP4`/`SWA` hits. Nine selected bodies were imported into the isolated corpus and searched through `pr-search`; this is bounded body inspection, not 289 implementation reviews. FlashInfer 5717 and vLLM 55449 corroborate existing NVFP4/layout work. The decisive implementation evidence is the pinned source, not PR body absence or merger status.

## Cache-format correction: generic FP8 is ambiguous

`attention.py:145–184` maps an unspecific `auto` or `fp8` to the selected packed backend's preferred record and writes that canonical value back to `cache_config`. Mega attention's `packed_kv_cache_dtype` returns **`nvfp4_ds_mla`**. On SM100, that means **528 B sliding-window rows and288 B compressed rows**. Explicit `fp8_ds_mla` keeps the compressed record FP8 as well. The FlashMLA fallback prefers `fp8_ds_mla`.

`nvidia/model.py:200–255` selects Mega by default only when its availability/topology checks pass; explicit backend selection and PCP can change this. Availability requires the sparse implementation, SM100 family, built Mega ops/weight-permutation ops, and supported head/group/TP geometry. H64 / groups8 / TP1 meets the arithmetic head-group condition; no device/library check was executed. The writer packs NVFP4 as256 B E2M1 payload plus32 E4M3 scales, distinct from the paper's affine INT4 format.

The exact resolver body ran in a stdlib AST harness with dtype/logger sentinels: nine cases covered generic/explicit packed formats, plain rows, config mutation and two incompatible inputs. This establishes host decision behavior only. It does not execute the constructor, select a real backend, or validate the packed writer/reader.

The campaign brief's “FP8 KV” label therefore does **not** prove all-FP8 compressed storage. `BASELINE_SCOPE_ADDENDUM.md` preserves original report hashes and exact passages for rounds 13/37/47/61/82. Earlier hypothetical 528 B codec arithmetic stays conditional; universal format wording is corrected. No frozen report or baseline was rewritten.

**Smallest missing artifact:** one exact-run configuration/startup receipt linking selected attention class, canonical cache dtype, SM/build and per-role slot sizes to the model/source revision. If it shows eligible Mega already using mixed storage, an “enable four-bit compressed cache” proposal has no delta. If it shows explicit all-FP8 on a compatible reader, a future controlled existing-format comparison may be useful; that is not established here.

## Paper components and actual target fit

| Component | Disposition and target boundary |
|---|---|
| Learned dual-path transforms and affine C4R4 packing | Reject direct transplantation in this frozen phase. Conventional MLA has 512 content plus 64 separate positional dimensions; the target uses a 512D shared K/V latent vector. Learned rotations/scales, compensated weights and packing cannot be inserted as a CLI switch. The paper's inference components are screened separately. |
| Fused unpack/dequant and reuse of reconstructed cache through QK/PV | Already present in the target reader. FlashMLA's `issue_qk` and `issue_sv` read the same shared-memory KV slot; SV completion releases that slot. Existing raw/scales/reconstructed buffers and barriers already separate staging and reuse. No new removed read/launch is established. |
| Protect first four and recent 128 tokens in BF16 while also writing packed copies | Retain the representation-selection principle, defer any target adaptation. The paper selects one representation per logical token in full-history attention. Target SWA and compressed selected occurrences are distinct model contributions, potentially with different representations; they cannot simply become mutually exclusive alternatives. Its learned attention sink is not a set of first-four protected tokens. Extra BF16 storage, ownership/aging and sparse readers would need a new contract. |
| Positional QK-error calibration/bound | Retain function-aware diagnostics, reject using the paper's value-fixed bound as a target quality certificate. Target rotary coordinates participate in the shared value vector as well as matching. |
| Activate native NVFP4 compressed storage | Existing capability, potentially already source-default selected. No new intervention until the resolved baseline distinguishes it from explicit all-FP8. Quality and mixed-reader admission still apply if precision actually changes. |

### A useful mathematical falsifier

The paper's positional bound explicitly holds values fixed. Target `issue_qk` and `issue_sv` use the same 512D slot; the output subsequently receives inverse RoPE. Changing rotary-cache coordinates can therefore perturb values too.

The exact-real CPU control uses one visible shared-KV vector, a finite zero-logit sink, and query `(1,0)`. Changing KV from `(0,1)` to `(0,2)` leaves the QK score unchanged at zero, but changes the attention output from `(0,1/2)` to `(0,1)`. Embed the two coordinates in 512D at position zero, where RoPE is identity. Thus zero QK error alone does not imply zero output error for shared K=V. This is a counterexample to a careless theorem transfer, **not** a refutation of the paper's stated theorem, a claim that these are an actual quantizer pair, or a target quality measurement.

The portable diagnostic is to evaluate both matching and value/output distortion under the actual reader, then downstream logits and task behavior. It is not enough to report cache MSE, QK MSE, or agreement against a reference consuming the same reconstructed cache.

## Benefit and evaluator limits

The paper's C4R4 record is 320 B/token/layer plus fixed BF16 protection and mapping storage, versus its 1152 B BF16 baseline. Target528 B/288 B records, shared source layers, compression ratios, sparse selection and separate SWA invalidate a direct compression-ratio transfer. Slot bytes do not establish allocated capacity, physical traffic, or exposed ITL.

Its 5.168× whole-job throughput example uses DeepSeek-R1-0528, attention TP8/DP1, MoE TP8, vLLM 0.10.2, five simultaneous 128K-input / 1K-output requests and a BF16 capacity just below their total requirement. BF16 preemption/recomputation is removed by C4R4; timing includes prefill/wait/recompute, with one recorded comparison and no repeated-run confidence interval. It is not a sparse Flash1017 decode or attention-kernel forecast.

Existing Mooncake and agent-p75 load/latency evaluation remains appropriate for any later benefit comparison; no new synthetic serving harness is justified. If a precision change is actually proposed, those benchmarks alone cannot certify quality. First compare cache writer/reconstructed-reference execution, source sharing and aging, selected-slot identity/multiplicity, sink normalization and mixed-reader outputs. Separately compare original-target layer/logit drift, output behavior and task-derived quality criteria before promotion. No tolerance, quality waiver, or expected gain is invented here. Native comparisons and GPU execution remain unauthorized.

## Search usefulness and next decision

The highest-value outcome is a source-grounded correction of what the baseline might already execute. Fulltext also prevented treating a value-fixed positional theorem or a capacity-driven BF16 result as target evidence. Broader synonym searches would not resolve the remaining configuration fact. The next action is the single resolved-format receipt above, not another quantization paper or toy trial. The quality diagnostic is retained for future cache work; there is no implementation-qualified proposal or new accepted hypothesis in this round.

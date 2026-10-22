# Independent round83 review

**Verdict: no blocking correction. Retain zero-new disposition and additive format clarification.** Reviewed frozen author manifest `6cc651ee85fdfcee2fcb5fdbdd6963a93079e610860f19b4d57d835bd2faa6d6`; all42 file hashes and nine exact source/revision quotes checked. No author files changed.

## Source and paper findings

- The V4.1 resolver really maps generic `auto`/`fp8` through `packed_kv_cache_dtype`, then writes the resolved format into the cache config. The Mega property returns `nvfp4_ds_mla`; explicit `fp8_ds_mla` remains explicit. I independently executed three extracted host controls with dtype/logger sentinels. These demonstrate the selection rule, not the constructor/backend/device selection.
- `_select_dsv4_attn_cls` has explicit-backend and PCP branches before the default availability check. Mega availability checks SM/build operations and head/group geometry. The report correctly preserves those conditions. Neither planned B200 nor a generic CLI label alone proves which implementation was loaded.
- Source slot accounting is528B SWA under the SM100 V4.1 record helper and288B compressed under the mixed format. The non-SM100 branch is different and mixed format rejects incompatible record support. The reported correction is conditional and does not rewrite immutable baselines or establish physical traffic/capacity savings.
- QuantMLA Proposition2 and AppendixC.3 explicitly fix values while varying the decoupled positional key. The target `issue_qk` and `issue_sv` read the same reconstructed shared-memory KV slot; SV releases it after consumption. A changed shared cache coordinate can change both matching and value output. The exact-real one-key/sink counterexample is valid, but it is not a demonstrated target quantizer pair or a numerical kernel failure. The paper's stated theorem remains intact.
- Learned content/RoPE transforms and compensated consumers are not a frozen-weight switch. Screening their inference components separately is appropriate. Native unpack/dequant and QK/SV tile reuse are already present. Keeping protected first/recent tokens in a separate representation could be an additional quality/cost policy, but target compressed/SWA occurrences and learned sink do not match the paper's one-representation-per-full-history-token semantics.
- The5.168x result is explicitly capacity/preemption-driven whole-job throughput in another architecture/runtime/workload, not a target sparse decode estimate. Reconstructed-cache reference correctness is distinct from original-model quality. The report preserves both limitations.

## Evidence and next action

`checks.py/json` independently verifies artifact integrity, immutable quoted revisions, three resolver cases and the simple exact-real output difference. This is deliberately not another native test campaign. I read the paper's component/bound/runtime evaluation passages and the target selector, availability, resolver/slot accounting and QK/SV ownership source. No paper/provider query, GPU/native import, serving action or canonical mutation occurred.

The proposed next evidence is appropriately small: an existing or future exact-run receipt tying model/source pin to selected class, canonical dtype and record geometry. Without that receipt, an "enable compressed FP4" proposal might merely enable what the source default already selects. Unknown live selection does not invalidate the bounded static source conclusion.

One provenance observation from this review was applied to my separate round84 packet: the correct existing FlashMLA repository identity is `vllm-project/FlashMLA`, not an inferred upstream repository name. Round83 uses the correct identity throughout.

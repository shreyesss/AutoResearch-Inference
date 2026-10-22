# Round119 format correction — SM100 packed MX scale slot

This addendum corrects one interpretation in the frozen round119 report. The original packet remains unchanged (manifest `5646bec2d9c653e1fd1b3f529340ee3158797842bd7654846a9e7b86e4a73828`; all30 artifact hashes checked).

**Correct wording:** on the exact pinned SM100 FP8 index-cache path, each128-value FP8 row has a four-byte scale slot containing **four repeated UE8M0 exponent bytes**, not a single FP32 scale bit pattern. The source representation remains128+4=132 bytes per logical row. Page organization still separates the block's values and scale plane; “per-row slot” does not imply a physically interleaved132-byte record.

The generic comment in `attention.py` describing “4 fp32 scale” is insufficient for this specialized path. The actual branch closure at `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883` is:

1. `indexer_k_store.py:117` passes `MX_SCALE=not use_fp4_cache and mqa_logits_use_mx_scales()`.
2. `deep_gemm.py:597–606` defines the SM100 predicate and describes packed UE8M0 K scales.
3. `indexer_k_store.py:248–267` quantizes the BF16-rounded row and stores `pack_ue8m0_x4(...)` through an int32 pointer when MX_SCALE is true. Only the alternative branch writes a float32 scale.
4. `v1/attention/ops/common.py:157–161` extracts the FP32 scale's exponent byte and multiplies by `0x01010101`, replicating it into all four bytes.

This agrees with the [round115 independent review](../review/round115-agent/REVIEW.md), copied here with its original manifest for portable provenance. Exact source copies and quotes are retained. No native code or target modules were imported or executed.

**Unchanged findings:**132-byte index width;8,704/16,896-byte index pages in the B128 metadata scenario;136,224-byte baseline common stride; mixed-group failures; zero stride savings for the three manual partition controls; all54 managed specs; unresolved live configuration/capacity/quality. No metadata rerun is needed for this wording-only correction. It does not certify a reader ABI or compiled numerical behavior.

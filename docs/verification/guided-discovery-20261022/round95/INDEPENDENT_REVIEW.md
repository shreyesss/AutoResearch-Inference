# Independent round95 review

**No blocker to the zero-card, no-qualified-improvement disposition.** I read the frozen report and selected TrainBridge mechanism/measurement passages, the retained target preparation and MegaAttention output paths, exact source claims and tool receipts. All37 manifest entries, eight exact revision quotations, and two target file copies matched their pinned local originals. Author files were not changed. Review used only Python stdlib and source reads; no GPU/model/native/backend import, compilation, provider query or runtime experiment.

## Selective paper transfer

TrainBridge's selected concrete example is an overlapping-slice KeyShift: half the key features shift one token along sequence. Its compiled counterpart avoids ViewCopy through functionalization/fusion. The source-comparison method is separable from its NPU training setting and is appropriately retained. The frozen target preparation inspected here has projection, normalization, RoPE and cache insertion, not this half-feature previous-token shift. This supports rejection of that direct operation transfer in the bounded path, not global absence of all view/mutation inefficiency.

The paper compares training programs on H100/Ascend910C, with its explicit validation-loss/accuracy admission criteria and excluded tuning time. These are not the target exact-output or decode-latency contract. The report does not transfer its speed numbers. Linked repositories were merely candidates in the dossier: repository_selection is empty, so no donor code/test qualification can be claimed. The author keeps that distinction.

## Target source qualifications

Eligible Q-latent normalization/quantization already has an explicit fused call. Packed-cache preparation likewise calls a fused operator. A naming precision matters: `fused_deepseek_v4_qnorm_rope_kv_rope_quant_insert` is called with `apply_q_norm=False` in this path, and MegaAttention's `accepts_unnormed_unroped_query` sends Q normalization/RoPE into the attention kernel. Thus the operation name does not mean every named sub-operation executes in this particular launch. The report's broader source-present conclusion survives: it identifies actual existing fusion, with backend eligibility conditional, rather than a missing generic normalization chain.

The Mega subclass allocates FP8 output plus packed scales and `_o_proj` consumes them in `fp8_einsum`; it explicitly documents in-attention inverse RoPE and FP8 conversion. WO-A still emits BF16 before WO-B, which is prior OP36 and not a new finding. No generic DeepSeekV2/TritonMLA PR body proves this Mega path has an extra attention-output quantization stage. Both selected PRs remain body-level evidence, not exact-diff verification.

## Retrieval and provenance

Receipts independently confirm two successful paper searches returning10 and5 provider IDs,15 dispositions covering all returned IDs, and one versioned TrainBridge fulltext with one logical cache miss. The export contains20 documents,21 exact revisions and94 edges. Distinct provider IDs alone are not a universal identity-dedup guarantee; the retained dispositions' explicit identities are the stated local accounting.

The journal confirms the second expansion failed, its search nevertheless ran, and the corrected expansion came afterward. The report admits that ordering; it must not be counted as successful pre-search planning. The initial wrong-option failure lacks a surviving original stdout receipt and is only retrospectively described, as the tool ledger itself states. Neither issue invalidates the actual returned source, but neither is evidence of improved planning quality. The reviewer initially assumed the alternative export key `revisions`; this packet uses `document_revisions` with serialized documents. That review-script KeyError was corrected before the successful checks; it did not mutate author data.

## Decision usefulness

This screen adds one previously unread method/example and prevents recycling generic compiler/manual fusion as an implementation opportunity. It establishes no measured critical-path gap, qualified runtime component, tooling improvement or service gain. The explicit stop/reopen condition—one actual target intermediate/operation and compatible transformed counterpart—is proportionate. Existing concrete dossiers outrank a further broad fusion search by actionability, not a predicted gain ranking. Zero new formal identities is justified.

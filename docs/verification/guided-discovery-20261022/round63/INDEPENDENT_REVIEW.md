# Independent round63 source review

**Verdict: retain LP63-01 as a deferred integration direction.** The direct PP-adapter and split-DeepEP ports are ineligible as inspected. A model-specific serialized continuation remains a meaningful partial reuse of the papers and implementation, with no measured gain or implementation qualification. The current source does not establish enabled scheduler controls, mixed-load exposure, or safe interruption.

## Direct control mismatch is real, but expression equality is not a forward test

Donor `layered_prefill.py:16–25,64–94` partitions the local range and temporarily narrows `start_layer/end_layer`, replacing global PP first/last flags. Exact donor config `vllm.py:1481–1526` rejects speculation, DP, DBO, EPLB, transfers and other paths, and disables compilation. It also rejects multimodal models. These checks are actual integration limits, not merely conservative flags to remove.

The pinned target constructor stores `decoder_replay_start` independently (`model.py:841–876`); `forward:1061–1096` uses it and the separate replay wrapper. Narrowing end_layer alone therefore does not narrow the early loop. No replay uses stored end40; an enabled cut20 uses stored20. The author's six cases evaluate exact range expressions and are correctly limited to that scope.

**Sharper negative:** an empty early range for a proposed start>=cut is not a successful forward. Current forward initializes residual/post/res to None, and `_run_layers:1184–1186` asserts them non-None after the loop. Empty-range `equal=true` cases in the fixture establish expression equality only. A future adapter must enter at a genuine resumable interface rather than rerun the existing full forward with modified PP flags.

## Shared index-buffer live ranges constrain legal cuts

The model allocates one reusable `topk_indices_buffer` and one candidate-block buffer (`model.py:747–766`), then passes the same objects to the layers (`:813–815`). Index source layers publish top-k indices for later consumers; source20 additionally publishes candidate blocks consumed by later indexers (`attention.py:469–489,1316–1329,1417–1457`). Both dense masked and opt-in sparse consumer branches receive that candidate buffer; the concern is not restricted to sparse-logits enablement.

The retained exact checkpoint's text_config declares index sources2/8/14/20/24/28/32/36, candidate source20 with2048 blocks, and Engram layers1/14. If a hypothetical prefill pauses after a producer and a full decode reuses these buffers, resuming a prefill consumer with the old row interpretation needs phase-owned saved values, recomputation under an explicit correct policy, or a boundary outside that live range. **Serializing completed MegaMoE calls alone does not preserve model-level scratch.** This is a source-derived proposed-interleaving counterexample, not an observed race in current serial execution.

A cheaper first design audit is the boundary immediately before source20, after early layers0–19: it precedes candidate production and the next top-k publication, so it may avoid carrying those two live scratch sets. It is a research design suggestion, not proof the boundary is legal. Earlier Engram/hash/prepared state may still be live, and the five mHC continuation tensors plus accumulated auxiliary values and original row/position/metadata identities must survive. Check actual flags before assuming bounded replay is selected.

## Auxiliary and replay ownership: distinguish proven sharing from unknown aliasing

`_run_layers:1164–1183` carries five values and accumulates previous_aux into a local dict. Engram's branch obtains it with mean(dim=1) (`model.py:568–570`); the ordinary mHC helper allocates an aux tensor with torch.empty (`kernels/mhc/tilelang.py:357–362`). I found **no source proof that every eager auxiliary output aliases a model-global buffer**. Keep those tensors alive, but do not invent an eager overwrite bug.

Concrete reusable state includes `_mtp_hidden_buffer`, filled at final forward (`model.py:917–923,1109–1114`), and `DecoderReplayLayers._break_outputs`, fixed outputs copied on repeated graph-break execution (`decoder_replay_layers.py:95–106`). The former is not automatically live at an early cut; its consumer timing matters. `replay_batch`, its selected rows and forward context are per-step mutable state (`:62–67,108–128`) that an intervening decode can replace. Captured-buffer alias safety and external workspace ownership remain unproved. The pending MoE-finalization branch is separately gated by supports_mhc_all_reduce; do not attribute that branch unconditionally to TP1.

Preserving mathematical layer order while changing boundary collapse, batch sizes or graph/tactic selection can change numerical behavior. No native equivalence is established by the range/key fixture.

## Collective order and allocator scope

The exact symmetric-buffer key (`deep_gemm_mega_moe.py:606–650`) includes group identity, device, maximum token capacity, expert/hidden/intermediate dimensions and formats. It contains no phase or layer key. Its input arrays are overwritten before one native invocation (`:790–854`). The author's equal-phase-key scalar test isolates that fact; supplied expert count256 is not a model-config attestation and is not needed to prove phase absence. Different buffers would not by themselves establish independent ring/counter/barrier progress.

The donor runner does clone intermediate tensors off reusable graph outputs and bounds in-flight ticks (`gpu/layered_prefill.py:96–101,146–155`); these are useful ownership components. Its global PP monkeypatch is not a concurrent per-phase context mechanism. The target's rank coordination must preserve the same collective sequence, including dummy/no-work ranks. Eager can retain local token counts; graph/ubatch paths agree on padding, so the quoted equality rule must not be generalized to every eager shape.

AInfer-PD's read §3 supplies a rank-shared turnstile and phase-owned split-DeepEP state, but its ATP/ADP crossed-collective problem does not establish a TP1 problem here. Whole-native-call serialized boundaries are a different, coarser adaptation. Full-SM progress and graph edges need evidence before a concurrent arm is considered.

## Prior work, claims and priority

The retained paginated inventory has143 unique cards. Its admission/chunk/cadence/CMR/resource-allocation entries change budgets, membership or release timing. None of those compact mechanisms establishes persistent partial-depth model continuation across full decode rounds. This bounded comparison supports a distinct integration direction; it is not an exhaustive novelty claim. Existing controls remain cheaper comparators. The independently read DLFP negative section confirms41.1→194.8ms P99 and5/12→4/12 SLO passes in its own setting, not a target forecast.

All five exact source quotations/revision fingerprints were checked against retained bodies. Their scope is source/control behavior, not runtime enablement. The target's local adaptive threshold/cadence code is present; no launch configuration was established. The prior workload counts and donor serving gains do not supply an exposed stall fraction or latency bound.

The next useful work is one boundary's explicit read/write/lifetime inventory plus compatible effective settings and mixed-step exposure. Do not add broad symbolic cases or count same equations twice as validation. Continue to rank this below simpler source-compatible arms by readiness/integration cost; no speed ranking is justified.

## Audit scope

Read exact selected caller/model/replay/allocator/DP/donor branches, the retained AInfer §3 and DLFP negative passage, and compact prior mechanisms. Verified frozen hashes and five quote fingerprints. No GPU, model/native import, network, canonical write, source mutation, timing or additional broad tests. The author fixture was inspected, not rerun as a purported independent execution. A broad grep output truncated before narrowing to exact ranges; an initial normalized-revision shape lookup expected a document wrapper and failed, then was corrected. Neither diagnostic failure supports a scientific conclusion. Original author packet is unchanged.

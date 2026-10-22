# Checkpoint 29 — a separable expert-return codec and a rejected-state follow-up

The guided discovery loop continues. This checkpoint adds one source-supported, deferred experiment, a deeper paper screen, and a tested provenance repair. **No GPU/native decoder execution or measured serving improvement.** Source compatibility still refers to planned Flash1017/c455/DeepGEMM a7a on two B200 EP4 groups, not fresh live-deployment attestation.

## EC79: FP8 expert-output combine, isolated from W4A4

The pinned MegaMoE path already quantizes input dispatch but returns **BF16 expert-output partials**. DeepGEMM #382, inspected at `edc5c10…`, has an independently selectable FP8 combine representation. Its FP8-activation arm supports the existing shared expert; the incompatible FP4-activation change is not required.

The proposed experiment ports only that return representation into the current scheduler:

1. Preserve the original BF16 rounding of each expert partial.
2. Encode E4M3 values and one UE8M0 scale per128 output columns.
3. Return payload and scales under the existing completion/lifetime protocol.
4. Reconstruct and accumulate in FP32 using the **current shared-first reduction order**, then produce the existing BF16 output.

Current vLLM lacks a combine-format argument and format-aware buffer ownership. The port needs consistent buffer/JIT keys and graph recapture when layout changes. The donor uses an older scheduler; transplanting its whole kernel would also replace current token-chunk traversal and per-peer readiness. Those unrelated changes are excluded.

At H5120, the logical representation is **10,240 bytes versus5,160 bytes per encoded partial**, before padding, transactions and signaling. At most six routed slots can be remote; the shared slot and locally routed slots still pay codec cost in the donor's all-slot mode. This is a payload comparison, **not a link-traffic or latency measurement**.

### The decisive qualification boundary

This codec changes target arithmetic. An exact scalar cancellation control shows BF16 partials `129/128` and `−1` combine to `1/128` originally but to zero after the proposed FP8 reconstruction. FP32 accumulation and unchanged weights do not restore lost information. The control is deliberately constructed; it does not estimate actual quality loss.

Mooncake and agent-p75 remain the service-benefit evaluators. They cannot alone qualify a numerical target change. A future authorized experiment therefore additionally needs representative paired numerical/generated-output checks and the applicable task-quality contract. No donor tolerance is adopted. A universally exact transformation requirement would rule out this direct lossy codec; finite prompt equality alone would not prove general equivalence.

The donor's published comparison also cannot establish the gain: **both compared revisions already use FP8 combine**, with other hardware/shapes/activation formats. The selected RAC paper contributes packed-cost and quality-accounting principles; its trained edge-network predictor is not a compatible native component. Its high-bandwidth crossover is relevant counterevidence to assuming compressed traffic always wins.

**Decision: retain EC79 for a conditional future experiment, with unknown ROI and explicit numerical admission.** It is distinct from input staging, weight packing and tactic tuning. [Mechanism, exact source and evaluation design](round79/REPORT.md), [independent review](round79/INDEPENDENT_REVIEW.md), [cancellation control](round79/cancellation-control.json).

## ReAnchor: stronger evidence, no shortcut to a native adapter

Following a known recent result to full text corrected the abstract-level picture: ReAnchor evaluates temperature1 and DSpark variants without mandatory neural training. It reuses rejected verifier features to generate shifted proposals, attaches continuations, and jointly verifies a trie under the new prefixes.

Its independent target-sample matching is a legitimate different acceptance design. It does not prove correctness of our native block-rejection path after proposal selection/attachment. The target explicitly invalidates rejected context rows, combines multiple auxiliary layers, and manages distinct draft KV groups. Flipping rejected rows valid or attaching a continuation after one token match would not establish correct feature, probability or cache ownership.

The paper also reports stochastic losses on several tasks and uses batch1 latency measurements; extra candidates may cost more at our serving load. A complete adapter and a credible native comparator are still missing. Preserve rejected-state feature reuse as a component, **without another implementation card or invented gain**. [Report](round78/REPORT.md), [independent review and counterevidence](round78/INDEPENDENT_REVIEW.md).

## Yield and tool reliability

Rounds78–79 added two dated provider queries,20 returned records/declared identities and two selected fulltext reads. Round78 reused a known discovery result and made no new discovery query. Round79 hydrated one PR's14 patches and read six exact-head files. One new author proposal survived as deferred; no original-round typed cards, implementation promotions or service wins. [Counts](yield-7879/counts.json).

A real historical source-hash mismatch exposed a claim-link bug. The repaired tool keeps the actual selected immutable revision key, refuses an unavailable revision, and compares source content rather than hash-format changes for dossier alerts. It does not migrate old data or repair earlier malformed claims. The regression failed before the fix;36 focused tests,385 research tests plus29 subtests, independent controls and bootstrap dry-run passed. Published code: `e78fddc`. [Repair and limits](legacy-claims/REPORT.md).

## Memory and publication

The isolated EM75/PC76 retention packet passed root review of234 artifact references,113 source revisions and both full deferred states after relocation. One historical revision preserves its diagnosed older hash formula and exact payload; no new claim uses that exception. Its22 normal replay commands are approved only after the existing serialized predecessor completes. This is **not a claim that queued cards are already canonical or published**. [Review](retention-29/REVIEW.md).

Local receipts at07:34 UTC show955 successful GitHub pages, last batch07:34 without errors, and research snapshot `1dd2460…966f` published at07:32 UTC. That snapshot predates later queued imports; no fresh remote/VM verification was performed. [Observation](retention-29/publication-observation.json), [delivery hashes](source-copy-manifest-29.json).

The next follow-up asks whether a recent mixed-precision calibration paper offers a valid quality diagnostic for EC79. Its weight-allocation objective cannot be assumed to measure activation-return error. This continues selective synthesis rather than creating an identity for every paper.

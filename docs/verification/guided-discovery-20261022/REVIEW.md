# Delegated adversarial review — guided batch 001

Reviewer: guided_adversary. Frozen criteria: RUBRIC.md. This is separate-agent source review with shared filesystem, not independent experimental replication. No GPU execution or serving changes. Accepted below always means a bounded next diagnostic, never a demonstrated service improvement.

## S01 — renderer-aware exact CPU tokenization reuse

**Verdict: advance to bounded CPU compatibility and exposure diagnostic.**

Strongest support: the pinned custom Python wrapper renders then encodes the complete prompt; inspected HF helper caches tokenizer properties, not tokenized session prefixes. Upstream repair is a separable CPU component. Exact target tokenizer has the same base pipeline but a finite changed added-token table, making a focused compatibility investigation plausible.

Strongest objections: exact Flash-1017 artifact is not certified in upstream TokTier; wrong anchor substitution fails all18 constructed differing-literal cases. Default thinking renderer rewrites a prior suffix, so raw append/session-length reuse is invalid. Tokenization savings affect frontend TTFT/queueing, not directly decode ITL. Existing chat-capable endpoint is not evidence of reusable session input or current frontend activation.

Checks reviewed: primary TokTier method/certificate appendix; pinned author support matrix985–1040; exact artifact comparison; constructed renderer8transition output; actual counterexample scripts. Prior E18 genericHF cache is not this custom-artifact renderer-aware repair. No live-image absence claim is warranted.

Repairs required before typed proposal finalization: put core TokTier CPU repair evidence in structured support, not only the optional Delta chunk-pool quote. Freeze exact reference loader/version and full encoder options. Keep tokenizer0.22.2 probe results scoped to that test environment. Resolve actual benchmark text/session payload from saved client source before claiming exposure.

Cheapest next discriminating test: exact-target added-token and post-render suffix differential fixture against the actual reference loader, with upstream stable-boundary certificate and safe full encode fallback. Test all changed literals across cuts, Unicode class edges, tool rewrites, reasoning changes and state invalidation. A mismatch disables only the proposed fast path. If source/trace shows token-ID bypass or no reusable rendered spans, defer benefit on current benchmarks without declaring the algorithm disproven.

Future evaluation: original Mooncake/agent-p75 remain controls; any session-edit fixture adds missing correctness/exposure, not replacement headline workload. Equal CPU workers, full token-array materialization, cold/warm state, fallback fraction, bounded memory and paired arrival order. Service metrics TTFT tails, goodput/errors, E2E and ITL guardrails. No numerical improvement forecast established.

S02 quick demotion: duplicate/refinement of canonical4028a37… ghost-admission mechanism. S03 retained-deep-block eviction and S04 transition-guided cache remain deferred integration/workload hypotheses. S05 reservation model and S06 commodity GQA workqueue are rejected as direct ports within this bounded review; S06 abstract-only triage does not reject every reusable idea in the paper. S07 GPU tokenizer is deferred and outside current execution authorization.

## M01 — distribution-conditioned MegaMoE tile choice

**Verdict: advance to bounded source/CPU diagnostic.** This is an adaptation of an existing technique, not a novelty claim or implementation approval.

Independently inspected pinned DeepGEMM `heuristics/mega_moe.hpp` and vLLM wrapper `get_block_m`. The heuristic uses expected tokens/expert and square-root margin, not actual routing histograms. The candidate holds SM allocation fixed and changes legal GEMM tile selection, distinct from prior N03 communication/compute resource split and generic backend selection. Default CMake pin does not prove the deployed binary lacks overrides.

The executed synthetic CPU work model demonstrates that equal token counts can hide different expert tile/padding tradeoffs. It does not show that any larger tile is faster. Source DA-MoE reports MoE graph timings, not client-visible gains, on a different kernel/format/model path. The card now preserves those limits and includes newer negative/neutral tactic-dispatch evidence.

Cheapest next discriminating action: inventory at least two legal full MegaMoE tile configurations, including symmetric-buffer/scale/ring compatibility and graph-capture identity; inspect any already-retained **physical receive** histograms by layer/rank. Existing logical pre-EPLB callback is not that evidence. If no retained histograms, do not collect GPU traces now; retain source-qualified proposal and defer quantitative selection. Do not generate a synthetic histogram and label it target exposure.

Future matched control: current heuristic and best fixed per-layer/bucket tactic before introducing runtime histogram selection. Dynamic dispatch must beat that strong fixed control after overhead. Hold routing/precision/placement/SM allocation constant, preserve rank consistency, and use existing workloads plus mechanism counters. Actual source-dependent legality remains unresolved; a patched override is required, not an existing enabling flag.

## M02 — HPC-Ops selector direct port

**Verdict: reject direct port as formulated; retain a narrowly scoped producer comparison only if new evidence warrants reopening.**

Author code explicitly uses nonsampled K512. Target has distinct K512 token selection and K2048 candidate-block selection. Existing vLLM sampled selector and valid-length DeepSelect already cover much of the general story. The source's long FP32 score-row performance does not transfer to target compressed BF16/block-score rows. Exact TopK's arbitrary tie contract does not itself guarantee identical downstream KV membership. No new accepted mechanism merely by changing libraries.

## M03 — all-candidates producer bypass

**Verdict: revise/defer semantics.** No implementation should follow the unconditional enumeration idea.

Independent pure-CPU counterexample retained in `candidate_bypass_counterexample.py/.json`: fallback excludes a valid all-minus-infinity producer block; enumeration reintroduces it and can change a later consumer's selected token. This is an arithmetic falsifier of an unconditional claim, not evidence such rows occur in live traffic. DeepSelect branch has a separate unverified short-row contract. Eligibility depends on compressed/packed bounds, row-repeat, newest-block pinning and sentinels, not raw request length.

Further source inspection **resolved** an earlier reviewer objection: sparse consumer `_expand_candidates_kernel` sorts ascending candidates, so input order alone is not a correctness objection when membership matches. Keep this correction in review history. Preserve producer tokenTopK and all later indexers. Next source/CPU check should prove a restricted invariant or preserve membership cheaply; if it requires comparable scoring work, the proposed saving may disappear. No current estimate establishes meaningful service headroom at the single producer layer.

## M04 — HiSparse integration

**Verdict: reject low-change flag activation; defer actual target integration.**

Author identifies exact source chain: V4.1 attention reports a V4 model version that HiSparse layout rejects. Removing that check is not a correctness port. Sparse compressed/source-shared KV, CED/SWA/DSpark ownership and host Engram contention need explicit compatibility and pressure evidence. Existing generic HiSparse code is not target support; the old backlog already includes KV-offload lanes. Reopen on actual cache-group bytes/ownership and retained capacity-pressure evidence. No GPU data collection now.

## Batch yield and review limits

Across author tables:11 considered interventions;2 advance to bounded CPU/source diagnostics (S01,M01),1 duplicate/refinement,3 reject direct ports (S05,S06,M02),4 deferred integration/workload/alternative (S03,S04,S07,M04),1 revise/defer semantics (M03). M04 also rejects its flag-only formulation but is counted once under integration deferral. **Zero service-qualified improvements.**

The reviewer independently inspected the strongest two proposals and the decisive M02/M03 source mechanisms; lower-priority S03–S07/M04 dispositions use author evidence plus historical compatibility review, not an independent full-paper replication of every item. These counts are triage yield, not probabilities or proof of research quality.

## Tool checks that changed decisions

- Read-only canonical memory and selected historical indices prevented duplicate cache/SM/routing cards.
- Primary TokTier certificate + exact author support matrix changed package installation into exact-artifact compatibility; CPU counterexamples changed raw append into post-render suffix repair.
- HPC source K512 branch rejected a superficially matching direct port; target producer/consumer split kept a narrower possible avenue alive.
- Candidate fallback source and independently executed CPU falsifier blocked an unsafe all-block shortcut.
- Sparse consumer canonical sort removed an overbroad reviewer objection.
- Pinned DeepGEMM heuristic established a concrete count-only dispatch delta; CPU synthetic work showed information loss but left speed unknown.

All reviewed acceptance is for bounded investigation. Typed plans, canonical memory and S3 publication remain the parent's responsibility; these Markdown files alone do not persist lifecycle state.


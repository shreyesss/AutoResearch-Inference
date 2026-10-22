# Checkpoint 22 — distinguish a new mechanism from a useful refinement

The CPU-only guided discovery loop continues. No GPU experiments, model launches, serving changes or measured inference gains occurred.

## RM61: active request ownership, deferred

Two paper queries returned 16 distinct papers; two selected fulltexts supplied migration protocol and copy-versus-recomputation ideas. The source audit adapted the protocol to moving an ongoing request **within one shared EP4 group**, rather than treating independent serving engines as equivalent.

A profitable move would need to reduce repeated rank-local critical-path work or an actual common graph bucket. It does not remove aggregate routed expert work. The current client pins an in-flight request to its owner, and normal remote-decode cache matching stops at its original prompt length. Eight CPU observations from extracted target methods disprove a simple reroute-and-resume shortcut.

The independent audit adds a specific requirement: `seed=None` is replaced by a generated effective seed during request setup. Recreating the same original request parameters would change that seed. Preserve effective seed and eligibility flags, committed token accounting, mutable cache groups, original stream/stop state and collective participation. Exact copying still does not prove identical numerical behavior after changing batch geometry.

**Disposition: one deferred research candidate; not implementation-ready.** It is lower readiness than a narrow work-removal or scheduling change such as PJ01 or CF59. First replay compatible retained per-rank scheduling metadata against the real descriptor selector. If there is no eligible persistent imbalance or bucket reduction, park it before implementing transfer. No suitable trace or profitable move has yet been established. Existing Mooncake/agent-p75 remain the eventual service evaluators, with migration pauses and affected-request coverage reported explicitly. [Experiment design](round61/REPORT.md), [independent adversarial review](round61/INDEPENDENT_REVIEW.md).

Typed proposal/screen/deferred-decision execution is a separate isolated step in progress at this checkpoint; the author report is not represented as a completed canonical card.

## Round62: two useful paper components, no new routing card

A query with an ambiguous “tactic” branch produced mostly unrelated results. The agent corrected the Boolean branches using the existing discovery skill. Across both queries there were 29 hit references, 28 distinct papers and two selected fulltexts.

The reusable components are static hardware-behavior features for candidate ranking and pruning candidates against explicitly chosen reference arithmetic. Their demonstrated dense-Hopper training/checker settings do not certify B200 FP8/FP4 persistent MegaMoE. The actual FlashInfer PR inspected changes a TRTLLM-gen sparse-MLA route that our pinned FlashMLA Mega path does not call; its batch-dependent head branches also do not cover the planned 64-head case.

**Zero new cards.** The findings refine existing tuning investigations. They do not revive M01's refuted padded-MAC premise or establish a trained target selector. A scalar binary32 counterexample demonstrates why equal dtype/algebra alone is insufficient; no native tactic was executed. [Report](round62/REPORT.md), [root review](round62/INDEPENDENT_REVIEW.md).

## CF59: optional work must be part of admission

The context-overlap candidate remains deferred. A further source check found optional prompt-logprob callbacks that can invoke the target LM head after sampling, before output-copy enqueue. Starting the side stream after the first LM-head call therefore does not prove no other GEMM overlaps it.

Both callback implementations can return early for ordinary completed-prompt decode. The retained standard benchmark builders omit those request fields, but that is not wire-level or mixed-batch attestation. Require an explicit current-batch eligibility check or independently safe scratch ownership. The original report/card remain intact; this is an additive refinement, not an observed race or rejection. [Source finding](round59/PROMPT_LOGPROB_REFINEMENT.md), [benchmark/default review](round59/PROMPT_LOGPROB_REVIEW.md), [callback review](round59/PROMPT_LOGPROB_CALLBACK_REVIEW.md).

## Observed tool failure → small skill change

An agent unnecessarily parsed already-extracted paper text as HTML. In one selected paper, 96,822 characters became 76,525, deleting equation inequalities and C++ syntax. The second also lost template arguments. The corrected final files exactly match the retained source bodies. These counts describe this transformation, not a general semantic-error rate.

The deep-research skill now says to inspect the returned representation, preserve the authoritative body/revision, and label any cleanup as derived. A `/html` URL or local `.html` extension does not establish that the tool returned HTML. Skill validation passed; independent source review confirmed the reader can return extracted text while retaining that URL. This is a concrete instruction repair, not a measured increase in agent reasoning quality. The preceding code test result remains 365 tests and 29 subtests; no new runtime code changed here.

## Yield and retention

This slice adds **one deferred research candidate and two supporting paper components**, with zero implementation-qualified candidates and zero measured improvements. Counting supporting components as separate new hypotheses would inflate yield. Neither round establishes exhaustive PR or paper coverage.

The frozen retention58/59/60 plan passed normal isolated import, typed replay, idempotent retry and default snapshot/relocated restore. Root independently checked 255 artifact hashes, 171 source revision fingerprints and exact CF59 identity/card/brief/baseline/status. The restored ledger contains only CF59, not a wholesale copy of prior memory. The canonical application has been authorized and launched once; it is waiting for the normal writer lock at this checkpoint. **Completion and cloud publication are not claimed.** [Retention review](retention-22/ROOT_REVIEW.md), [typed verification](retention-22/typed-validation.json).

[Packet verification](source-verification-22.json) and [delivery copy hashes](source-copy-manifest-22.json) retain provenance. Raw evidence remains external to Git. A new lane is examining mixed-prefill/decode interference against existing scheduling work; prior decisions and contrary evidence remain part of the search.

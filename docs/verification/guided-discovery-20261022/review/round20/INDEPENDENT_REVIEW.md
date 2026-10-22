# Independent round20 native CPU receipt review

**Verdict:** supports a bounded refinement of S01 CPU compatibility evidence. No blocker to retaining this result with its stated limits; no certification, serving implementation, Linux deployment or speed claim follows. I read the probe and Rust fallback branch, checked source/binary hashes and recomputed receipt totals. I did not rebuild or rerun the 2,818-transition corpus.

## What genuinely changed from round18

Round18 used a HuggingFace suffix-encoder proxy. Round20 calls the compiled pinned `toktier._native.CallbackEncoder.native_fast_cpu`, built for aarch64-apple-darwin with Rust1.93.1. Installed `repair/gigatoken.py`, `repair/registry.py` and `facade/api.py` are byte-identical to retained build source. All15 source-manifest hashes and the native binary hash match. This addresses the prior proxy-only gap for the observed native branches.

The driver remains the unmodified **Python GigatokenRepair** calling native full encodes on its suffix windows. Native Rust append/session repair is not executed: `native_stats.window_calls=0` is consistent with this, not evidence of a missing Python window operation.

## Counts and shared-reference limits

- 2,710 independent probe cases +100 stateful append steps +8 rendered transitions =2,818. All reported IDs and offsets match the HF0.22.2 oracle.
- Python repair performs3,423 window attempts (retries count separately):1,809 native Gigatoken and1,614 native HF added-token fallbacks. These are calls, not3,423 independent requests.
- Separate full-string differential checks are2,710:1,194 Gigatoken and1,516 HF added-token fallback. Their counts plus window counts exactly reconstruct native totals3,003 Gigatoken +3,130 HF fallback.
- The Rust `guarded_full_with` checks added-token matches and routes them to its reference encoder. Added-literal agreement in that branch proves guarded behavior, not that Gigatoken itself handles those literals. Comparing Rust HF fallback to Python HF is less independent than comparing the Gigatoken route to the oracle; both depend on the same tokenizer artifact.
- 2,813 transitions take the repair path; short-input/invalid-prior/noop and two default-thinking renderer rewrites use explicitly recorded fallback/noop. The rewrite cases preserve correctness by full reference encoding, not by a newly certified local repair.

The tested default target artifact guard remains closed (`artifact_not_in_certified_repair_roster`). The probe explicitly replaces anchor family metadata in its private constructor; this is transparent experimental admission, not a production registry change. Importing the facade class and exercising `_repair_callback` via `__new__` does not construct or test the complete public facade/session store.

## Remaining falsifiable work

The remaining gaps are session fingerprint/invalidation and renderer lifecycle, real deployment platform/build, target request distribution and latency, race/worker ownership and bounded repair certification. Correct prior IDs/offsets remain a precondition: prior round18 demonstrated same-length corrupted cached IDs outside the overlap can survive. This probe's100-step valid chain is useful but does not remove that cache-integrity requirement. The manually copied margin/window parameters and target added-token flags still require justified admission criteria beyond this finite corpus.

No GPU/provider call or canonical write was made during this review. The CPU backend build may link optional crate surfaces, but this review neither probes devices nor claims absence of all native driver code from a module-import list alone. The exercised source constructor and call graph are explicitly CPU; module lists alone are not an accelerator audit.

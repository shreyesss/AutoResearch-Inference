# Round16 runtime scout — bounded negative result

**Outcome: zero new qualified or deferred implementation hypotheses; one concrete direct-transfer proposal rejected with source evidence (RT16-01).** No GPU execution, serving changes, model calls, Serper, canonical writes or publication. All local discoveries/receipts remain in this isolated state.

## Executed search and adaptation

- Used repository inference-discovery skill and actual `researchctl expand`, `paper-search`, `investigate` commands. Five bounded paper searches: two arXiv requests failed with HTTPError; three OpenAlex searches completed with22 returned records/21 unique identities. DatesJune1–Oct23 exclusive, lastquery narrowedAug1–Oct23. Failed arXiv calls are not empty-result coverage.
- Broad metadata search produced hardware offload/runtime replacement material and existing tokenizer directions. Refined toward CUDA graph host synchronization; selected SiFAR for full text because it named an exact synchronization mechanism. Further narrowed recent staging search yielded no new eligible host component.
- One selected investigate retrieved82,871 characters in one logical cache miss, citations0, repositories0. SourceURL is unversioned; preserve observed bytes/hash rather than pretend a version pin.
- Read-only prior memory scanned133 hypotheses; first text filter accidentally included briefs and was overly broad, then narrowed to card fields. Canonical CLI recall waited behind writer activity and was terminated; readonly SQLite was used. No recalled empty output is treated as absent prior work.
- Read-only local PR triangulation: SiFAR none; speculative reduction returned FlashInfer5201 sampling residual work, an unrelated lexical hit; dual buffering+all reduce none in bounded retained opening records. No exhaustive all-GitHub claim.
- Two supplemental web batches had noisy secondary results and older work; none supplied retained scientific support or selected a candidate. The actual retained source decision uses OpenAlex metadata, primary arXiv fulltext and pinned target source.

## Decision-changing fulltext finding

SiFAR removes bottom barriers via dual buffering and top barriers via speculative reduction/flag verification. Its primary experimental path is a full-model Megakernel with TP, FP8models and mostlybatch1; it is not evidence for current vLLMDEP4 performance.

More importantly, §8.1 explicitly describes a correctness caveat: a reader may load stale peer payload, stall while the peer catches up, then read a valid current flag. Relative-progress monotonicity is assumed to rule this out. A100,000-iteration empirical match does not prove the assumption for our asynchronous, expert-routed, possibly microbatched target. `flag_validation_counterexample.json` preserves that exact symbolic interleaving; no device reproduction is claimed. **Do not relabel flag validation as unconditional lossless synchronization removal.**

The planned target isTP1/DP4/EP4. `distributed/parallel_state.py:740` bypasses allreduce atworld_size1. `deepseek_v41/nvidia/ops/mhc.py:59–72` permits custom fused mHC reduction onlyTP4 withEPdisabled. Expert dispatch/combine is not interchangeable with this TPAllReduce. Embedding can use a different parallel group and may stillreduce; this review does not claim the whole model contains no reductions. Its frequency/payload/protocol would need separate evidence.

Therefore reject the direct repeated-TP-barrier port. Selective future reuse of dual-buffer storage could be valid if an actual collective and rigorous lifetime/order contract are demonstrated; it is not a newly accepted hypothesis.

## Other discovered directions

All21 identities and reasons are in`paper-dispositions.json`. Existing TokTier/GraphTok directions were not regenerated. Other results require changed learned weights, CXL/offload hardware, CUDA remoting, model routing, fine-tuning co-serving, or solve recovery/simulation rather than an absent steady-state host operation. They remain source records, not fabricated candidates.

## Limits and tool usefulness

This is a bounded development search, not exhaustive recent-literature coverage. Search hitcount does not measure useful yield. The valuable action was fulltext reading that exposed the exact correctness assumption, followed by pinned target collective gating. No candidate numericalROI or service uplift was inferred. Stop because no additional retrieved mechanism establishes a compatible absent component; new traffic/kernel evidence could justify reopening.

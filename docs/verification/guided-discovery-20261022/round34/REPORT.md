# Round34: supplementary Top-K literature triage

**Zero new hypotheses; no reopening of M02 from title similarity alone.** This was a bounded supplementary web/source pass while the main agent ran recent online paper discovery. Full paper/code evaluation was not completed; the query ledger records exact read depth and operational errors.

## Selective mechanism and counterevidence

[Guess-Verify-Refine (April2026)](https://arxiv.org/html/2604.22312v1) uses previous selections to estimate a threshold, validates the candidate count, then refines exact Top-K. Its conditional guarantee requires K≤count(scores≥T)≤capacity; temporal prediction does not itself certify completeness. This is an older potentially reusable component, not a recent discovery win. Reported DeepSeek-V3.2/TensorRT results are not target forecasts.

At the pinned c455 target, dense indexer auto-selection already prefers cooperative Top-K through64rows, then persistent. DeepSelect is optional there; sparse candidate-logit consumers explicitly use DeepSelect. Existing sampled_topk already implements threshold estimation plus exact fallback. Prior M02 rejected direct HPC-Ops transfer because donor K2048/long-row conditions and generic mechanism did not establish a missing K512 optimization here.

A temporal predictor would differ from uniform sample selection, but introduces persistent per-request/per-layer state and speculative-row ownership. A correct implementation must score the predicted indices using current logits, preserve valid row bounds, and retain a complete exact fallback. Prior accepted output tokens, rejected speculative branches, request compaction and layer reuse cannot be treated as one stable row ID. Better guesses change cost, not which positions are legal.

## Cheap mathematical falsifier

For an all-equal row with N>capacity≥K, every value threshold selects either N positions or zero. No value threshold satisfies the required candidate-count interval. Therefore this predictor/refinement component needs a tie-capable exact fallback; calling its normal path exact does not establish universal termination or bounded scratch safety. This is a mathematical constructed case, not a reproduced donor failure. Matching values also need not match a specific backend's boundary-tie membership/order.

## Target relevance and stop rule

Raw context length is not indexer row width: compression, source/consumer role and optional candidate filtering intervene. Token selection K512 differs from candidate-block production K2048. Saved agent-p75 input8192 does not establish the paper's100K score-row regime. The target's existing cooperative selector is the relevant comparator, not the paper's radix baseline or torch.topk.

No proposal is promoted without retained actual row widths, selected backend and exposed selection cost, followed by a source-backed K512-compatible predictor/fallback design. If those show meaningful headroom, reopen a narrowly distinguished temporal-selector investigation linked to M02; do not relabel generic sampled Top-K as new. Existing agent-p75/Mooncake can supply future service comparisons if their rows expose the path. No new GPU workload, model run, numerical speedup or canonical mutation was performed.

HiSparse also reappeared in search and maps to existing memory; it was not counted as a new candidate. Other returned titles were not promoted without primary-source/component reading. The selected paper sections and exact target source copies are retained with hashes.

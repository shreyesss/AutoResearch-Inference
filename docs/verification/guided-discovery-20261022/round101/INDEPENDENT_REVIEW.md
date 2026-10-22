# Independent round101 review

**Verdict: no blocking correction.** Retain this as the existing SN98 refinement, deferred. The source establishes a useful single-chain implementation precedent and a concrete reason to exclude the donor multi-draft rejection branch. It establishes neither native correctness nor a serving improvement.

## Evidence checked

Verified the author manifest (`ce232eef…`), journal manifest and clarification manifest: 43 listed files total, including all 38 author files. Checked all 12 quotes against the exact immutable revision bodies. Both retained target Python files are byte-identical to the corresponding c455 files. Read the donor generator, single/multi verification paths, helper, test entry point, selected paper algorithm/limitations sections and target sampler/speculator branches. Read depths remain bounded; this is not a whole-repository audit.

Executed only `python3 review/round101-agent/check.py` plus a stdlib byte comparison of the target files. The script imports neither author controls nor donor modules. It performs hash/quote checks, an independently derived rational calculation and read-only SQLite comparisons. It does not rerun or add to the author's test counts.

## Fresh redraw: independent derivation

Let each draft use independent E0k,E1k ~ Exp(1), obtained as −log(U). Gumbel-max is exponential-race sampling; taking max U across candidates is exactly taking min E in ideal arithmetic. With target p=(4/5,1/5), proposal q=(1/5,4/5), set a=q0/q1=1/4 and b=p0/p1=4. At depth zero all target rows have the same actual prefix, hence the same p.

Order E11=t≤E12=s and multiply by symmetry factor two. The event all drafts choose token 1 and target chooses token 1 requires E01>b*t and E02>max(a*s,b*t). Its probability is

`2 ∫_0∞ exp(-(1+b)t) [∫_t^(bt/a) exp(-s-bt) ds + ∫_(bt/a)∞ exp(-(1+a)s) ds] dt`.

Integrating the two regions gives `1/5 − 2/25 + 8/125 = 23/125`. Therefore the no-match mass is `(4/5)^2 − 23/125 = 57/125`. The reverse no-match event is impossible: at the smallest E1, a draft choosing token 0 implies E0<a*minE1<b*minE1, contradicting target token 1. Preserving the already drawn target token yields p; independently redrawing p on no-match yields token-0 mass `4/5 − (57/125)(1/5) = 443/625`, TV `57/625`.

The actual `InvariantMultiDraftStrategy.verify_draft` uses `gumbel_sample(logits[alive_group_id, depth])` without supplied noise. At root all-rejection, alive_group_id remains zero, and its target prefix is the same as every other row. Thus row selection does not defeat this counterexample. `InvariantSingleDraftStrategy` instead returns the already computed `target_ids[0, depth]`. Paper Algorithm 2 likewise returns the previously selected Y when the viable set becomes empty. This is a donor-branch discrepancy, not a refutation of the paper algorithm.

This calculation concerns a binary full-support ideal continuous law. It is not a measured defect frequency, a test of finite torch PRNG/clamps or a reproduction of the top-50 benchmark. The zero-support and K1 controls are supplementary, not needed to establish the K2 result. Independent redraw after a noise-dependent rejection is unsafe; static pre-draw eligibility and same-tape target-only fallback are separate questions.

## Support, persistence and native fit

The retained donor test calls do not override top_k. `InvariantGenerator` defaults to 50, and `LogitsProcessor` masks other coordinates to −infinity before temperature scaling; stored top_p is unused. Full-width tensor allocation is not full-support sampling. The paper's main-text vocabulary-width statement must therefore stay separate from its appendix top-50 setting and inspected code. The selected v3 header is dated 11 January 2026; describing the work as originating in 2025 should not obscure that version date.

The single-chain positional tape is real: one allocation, absolute committed position indexing, shared draft/target slices and a coupled correction/bonus. It is useful precedent but not a proof for native Markov proposals, AV, heterogeneous rows, early stops, cache commits or seed replay. The target still salts draft positions and incorporates speculative step into seeds; `draft_logits=None` takes a greedy branch. Removing the probability buffer or salt alone is not an implementation.

The reported resident tape byte arithmetic is correct under the stated float32 assumption. It is not total memory: the multi class also owns an initial randomness allocation, and repeated candidate caches/logits remain. No stateless keyed equivalent or its cost is demonstrated. Timing starts before tape allocation, but source `perf_counter` placement is not synchronized GPU latency evidence. Categorical marginal correctness also does not imply equality to this target's finite Murmur/Gumbel implementation. The head and dense logits remain, and acceptance loss competes with any probability-cache saving.

## Journal correction

Read the authoritative round98 `state/commands.sqlite` through SQLite `mode=ro`. All ten completed original rows match the round101 projection, and the parsed argument objects match the normal `history` output. Its eleventh item is its own in-progress history entry. The original frozen mirror contained only the init row; it was not a complete command history.

`CLARIFICATION.md` resolves the older README/receipt phrase “full argument projection”: the retained fields are normalized, allowlisted/redacted journal arguments, not original raw argv. The review records counts and equality, not another copy of argument values. No canonical or original state was mutated.

## Strongest remaining gate

SN98 still needs an explicit native mode/seed/row/fallback contract preserving full target support and a suitable lossless reference. A common-tape CPU reference can test the adaptation contract; it cannot certify native numerical equality or cost. Keep native execution and performance measurement separately unauthorized. No new hypothesis identity or performance claim follows from this review.

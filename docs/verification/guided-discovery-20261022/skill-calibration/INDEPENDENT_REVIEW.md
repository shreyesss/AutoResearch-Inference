# Independent review: selective policy-calibration guidance

**Verdict: no blocker.** This is a bounded reasoning aid supported by round76; it is not a validated universal optimization recipe or an empirical improvement in skill quality.

## Correctness and evidence

- The training paper supplies an acceptance-overlap objective while updating neural weights. Its window derivation and teacher-forced evaluation do not establish native parent-conditioned block progress. The guidance correctly permits a separately justified frozen-weight scalar adaptation without transferring trained gains or the window theorem.
- Native DSpark samples sequential parent-conditioned logits, so a changed policy changes later inputs and reached states. Request-disjoint data splitting addresses leakage; it does not supply missing counterfactual conditional distributions. The guidance asks for the coverage rather than mandating a new fixed workflow.
- The native Gumbel path caches pre-temperature values; the rejection path reconstructs q using scale, normalizers and residual recovery. The warning about changing acceptance alone is supported by both source and the transparently shared single-token rational counterexample. That counterexample is not native block-verifier certification, and the paragraph does not claim otherwise.
- Explicit support and confidence/scheduling policy boundaries reflect reviewer findings about argmax mode, top-k/reduced-vocabulary branches and parent-conditioned confidence. A changed q may preserve the target distribution without preserving same-seed token identities. Retaining actual EOS/length rules and completed-output accounting avoids claiming a service gain from accepted length alone.

## Scope and discoverability

The paragraph starts conditionally with proposal-distribution or policy calibration, uses permitted scalar parameters, and explicitly calls PC76 deferred. It does not require calibration for unrelated ideas or authorize training, implementation or GPU work. The surrounding reference says these are reasoning aids rather than a checklist. The entry skill routes partial-fit/source-combination tasks to this reference, and the relative PC76 report link resolves to the repository delivery copy. No additional skill routing or broad rewrite is needed.

The paragraph is appropriately concise for the reference. Full admission details, such as probabilistic drafting activation and every block residual call chain, belong in the linked report and independent review rather than being copied into general skill guidance.

## Limits

This review checks source grounding, scope and link discoverability. It did not run a controlled agent evaluation or show better hypothesis yield, native distributional correctness, or serving performance. Source snippets were read, not imported or executed. No repository or canonical state was changed.

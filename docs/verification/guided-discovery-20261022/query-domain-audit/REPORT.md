# Query ambiguity field check

**One development case; no new serving hypothesis or measured improvement.** All work was CPU/network only. The historical query was already seen before this check, so this is not a held-out retrieval evaluation.

## Decision-changing search repair

Historical arXiv query:

```
all:"programmatic dependent launch" OR
(all:"kernel" AND all:"dependency" AND all:"inference")
```

The second branch admitted operating-system and statistical meanings of kernel. Revised query added `all:"GPU" AND (...)` around the whole expression, preserving the same June1–October23exclusive date interval and eight-result cap. It made one provider attempt, with no hidden relaxation. Fulltext reads of two selected papers made two further cache misses, with citations explicitly disabled. Original receipts remain unchanged.

Before the new search, PROTOCOL.json froze abstract-level categories: A is a potentially transferable GPU execution mechanism, B is systems background without an established dependency mechanism, C is off-domain or an inseparable learned architecture change. The independent reviewer classified:

| Returned set | A: mechanism lead | B: background | C: off-domain/inseparable |
|---|---:|---:|---:|
| Historical ambiguous query |0|2|6|
| Explicit GPU-domain query |3|5|0|

The N:M sparse paper is borderline B; assigning it A would change both rows equally. A does not mean compatible with our target or useful in our service. This case supports reduced domain ambiguity, not better corpus recall, general skill quality or a service win. The skill now advises inspecting ambiguous Boolean branches, preserving deliberate cross-domain searches separately, and comparing useful next actions rather than celebrating smaller result sets.

## Full-text follow-through prevented two unsupported conclusions

### CoRun: useful scheduling evidence, wrong performance comparator for a direct claim

[CoRun2608.14376v1](https://arxiv.org/html/2608.14376v1) achieves reproducibility through isolated prefill, one fixed padded decode shape, constrained reductions/Split-KV and request-bound sampling. Its large headline gains compare primarily with batch-invariant deterministic execution. SectionV reports standard scheduling faster overall in a presented mixed workload, and the one-request padding study loses throughput as capture size grows. SectionVII explicitly limits variable-concurrency online use.

Our source profile already has graph paths; the task has not requested deterministic outputs across changing batch shapes. A fixed-shape deterministic workload is not established, and native DSpark multiple query tokens differ from the paper's one-query-token decode explanation. Preserve scheduling and comparator evidence; do not promote a blanket fixed-shape padding port for our stochastic long-output objective. If a future task explicitly needs cross-batch determinism, revisit the whole numerical/sampling contract and its cost. No claim that this paper proves incompatibility with every speculative engine.

### TileSight: analysis ideas, not a turnkey source of missing ROI measurements

[TileSight2607.22432v1](https://arxiv.org/html/2607.22432v1) models tile resource use, dependency ordering, overlap and placement. Section4/Table3 requires vendor specifications plus per-architecture microbenchmark calibration. The text says code will be released upon publication; this read does not establish an available implementation. No independent repository search was performed.

Section7 excludes highly irregular/data-dependent behavior and warns that latency-bound small-batch attention and B200 SM-to-HBM affinity need finer parameters. Those are directly material to our proposed experiments. Reported aggregate prediction error is neither a target-specific error bound nor sufficient evidence for a tiny speedup claim. Table5's large address/layout gains mostly concern MI210 kernels; they cannot be transferred to our native SM100 path.

Reuse the conceptual decomposition of memory, compute and legal overlap when writing a diagnostic. Do not substitute theoretical arithmetic or a paper's aggregate accuracy for the missing component exposure, kernel layout, calibration and target measurements. No simulator, model weights or GPU workload ran.

## Honest tool result

The revised query found more mechanism-relevant abstracts and led to two useful exclusions/narrowings. It did not produce a new implementation-qualified idea. The original8 and revised8 hits have separate receipts; two fulltexts are retained in the isolated source database with revisions. Metadata-only leads remain labeled as such. Current source/read artifacts are external; canonical import and S3 publication of this field check are pending.

A first `init` invocation with `--defer-snapshot` failed because initialization requires an immediate local checkpoint. The retry removed that unsupported flag and succeeded. Both receipts are retained; this was a command error, not a provider or scientific failure. Skill syntax validation initially lacked PyYAML in existing interpreters; it subsequently passed using a temporary isolated validation environment without changing the research environment.

[Independent classifications](review/REVIEW.md). This case adds no cards to the hypothesis yield denominator.

## Independent forward planning check

A separate agent received a fresh KV-movement search scenario and the updated discovery skill, without the root field-audit outputs. It produced two bounded queries (reversible representation and contingent movement avoidance), preserved exactness as a qualification constraint, and successfully executed `expand` in a fresh isolated state with zero network/model calls and zero warnings. This checks planning usability only; no retrieval or serving result was generated. Original scenario, rationale, plan and receipt are retained externally under `skill-forward-discovery-001/` and copied into the field study's source records.

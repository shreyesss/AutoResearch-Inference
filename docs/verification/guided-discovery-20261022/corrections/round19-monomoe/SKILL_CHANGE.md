# Critic instruction repair

Observed failure: the original round19 summary conflated a positive local-operator TP8 comparison with a separate EP collective-fusion parity result. The exact retained source and numerical correction are in [ADDENDUM.md](ADDENDUM.md) and [checks.json](checks.json).

The `inference-critic` skill now asks the reviewer to identify the treatment, control, metric, measured boundary and hardware/workload before using a loss/parity result to reject a proposal. It requires checking actual table values when the summary determines the verdict, and appending corrections without reversing unrelated decisions. It does not impose a new numerical gate or require a table for every search result.

Validation: the existing four-point arithmetic check supports the corrected reading; the skill frontmatter validator passed. This is a narrow repair motivated by a real source-reading error. The author and reviewers had already seen this case, so it is **not a blind skill evaluation** and does not establish generalized hypothesis quality improvement. No new model API, provider or GPU call was used for the instruction edit.

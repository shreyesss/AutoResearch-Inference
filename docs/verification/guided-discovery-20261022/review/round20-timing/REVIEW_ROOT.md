# Independent timing and workload-exposure review

Read the executed timing script, receipt, source-exposure report and prior native
compatibility review. Recomputed all 12 cell medians and paired mean differences
from the raw samples. Each cell contains six generated requests, each measured
seven times; those repeats are not 42 independent workload samples. All
recomputed quantities agree. No timing rerun or GPU action was performed.

The experiment changes the decision: plain native full encoding beats the Python
incremental wrapper, whereas long added-literal strict appends can save CPU time
by narrowing an otherwise whole-input HF fallback. Input-copy sensitivity and
rewrite fallback are disclosed. Keeping a fast full-operation baseline prevents
incorrectly attributing HF-versus-native differences to incremental repair.

The script times outputs with unequal requirements: full ID-only versus repair
IDs plus offsets. It also retains a full-reference offsets baseline. This is
appropriate for choosing between practical alternatives, but not an equal-work
kernel-speedup comparison. Prior state and rendered strings are prepared before
timing. Native route counters are read outside the timed interval.

Scope remains narrow: a warm ARM/macOS process, repeated vocabulary in generated
prefixes, no CPU affinity/frequency control, and no deployment request sample.
The descriptive bootstrap intervals do not estimate a real serving population.
There is no evidence here for cache-hit rate, cold initialization amortization,
session-store overhead, native Rust append cost or reduced client ITL.

The exact renderer adds recognized BOS/role literals even when encode receives
`add_special_tokens=False`; that argument does not strip existing text. The
source-derived route probe correctly distinguishes this from plain text. Saved
agent-p75 shared prefixes and Mooncake hashes do not establish strict appends or
tokenizer state identity. The reported lack of an explicit YAML session setting
does not prove absence on the actual wire.

Decision: retain this as same-S01 CPU evidence. Next compare the donor's existing
added-token segmentation components as a full-input alternative, before assuming
a persistent incremental session cache is required. Preserve the default guard
until an explicitly scoped adapter passes its own semantic checks. This next
question is under investigation; no result or implementation promotion is claimed.

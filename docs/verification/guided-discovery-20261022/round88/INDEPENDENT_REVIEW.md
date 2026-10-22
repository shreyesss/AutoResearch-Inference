# Independent root review — transport and readiness

No blocker to the author's **zero new performance hypotheses** disposition.
The useful output is a conditional correctness prerequisite, not proof of a
failure in our deployment or an accepted patch.

Read the actual three-file PR451 diff, exact donor and target FP8/FP4 readiness
publication/wait paths, layout, relevant adapter buffer ownership and selected
SigmaTrace passages. Verified the frozen46-file packet, source revisions and
six exact quote anchors. The donor reset is inside the single-SM dispatch branch,
for each peer slot, before the actual pull-barrier call. The target's wait uses
system-acquire equality with its own grid index; the donor uses system-release
zero stores, not merely a comment change. No native code was executed.

The strongest support is the precise conditional mechanism: if a tag is reused
while the prior completion remains in the persistent workspace, the equality
predicate cannot distinguish old from current completion. An earlier reset and
correctly ordered barrier can separate the epochs. The strongest objection is
that reuse and this failure have not been observed on the actual pinned target
runtime; the B300 report belongs to the PR author. Fresh tags or an equivalent
external reset could make the proposed fix unnecessary on a given deployment.

The root independently opened the current official PTX gridid section. It
describes a temporal per-grid identifier and its debugging purpose, but the
inspected section does not explicitly specify CUDA-graph replay reuse. It does
not independently validate the PR author's graph observation. Source:
https://docs.nvidia.com/cuda/parallel-thread-execution/#special-registers-gridid

Scalar equality cases confirm only the assumed-tag predicate. They cannot prove
system memory ordering, barrier correctness, absence of delayed prior writes,
zero-token-rank behavior or safe workspace aliasing. Preserve those native gates.
Repeated changed-input graph replay versus eager/reference is a targeted future
correctness diagnostic; the ordinary latency suite cannot substitute for it.
No device diagnostic is authorized by this review. A shared correctness fix must
be held constant across subsequent performance arms.

SigmaTrace intercepts NIC doorbell pages. The inspected MegaMoE data-plane writes
peer mappings and uses an NVLink barrier, so merely using expert parallelism does
not provide that instrumentation interface. Its host-NCCL multi-node MoE imbalance
is not a native MegaMoE speedup. Keep possible other process/NIC traffic and a
future changed multi-node baseline separate from this precise mismatch.

This is a useful recent-paper-to-PR triangulation outcome despite zero new
performance identities. Retain it as a dependency for affected MegaMoE studies;
do not label those scientific ideas refuted or count the correctness concern as
a measured frontier improvement.

Reviewer tooling note: the first checker assumed wrapped/SQLite-encoded revision
rows; this export contains decoded document rows. After adapting that reader,
all31 revision fingerprints passed. No source or author packet was changed.

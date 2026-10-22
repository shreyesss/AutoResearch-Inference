# Independent review: two prefetch premises already implemented

Agree with both scoped dispositions. The native a7a kernel assigns separate
warps to activation/SFA and weight/SFB TMA. Activation readiness polling occurs
inside the former, while the latter can progress independently once its task and
stage are available. Both still wait for a reusable operand stage; MMA requires
the complete operands. This source proves a separate producer, not unlimited
prefetch or a measured overlap duration.

The native kernel also dedicates a leader-CTA warp to `scheduler.mainloop`.
The scheduler has two metadata slots, full/empty barriers and explicit
wait/claim/publish ordering. Consumers obtain task metadata and advance their
slot index; release occurs after UMMA arrival with the CTA memory fence. Shared
expert work and routed task admission remain distinct. A generic new metadata
producer/queue is therefore redundant. This does not prove that its queue depth,
task ordering, locality policy or cross-rank admission is optimal.

The recent FlashMask-3 component was appropriately decomposed: forward index
generation and producer separation were assessed even though much of the paper
concerns training. Mask intervals, attention context-parallel collectives and
expert task identities are different objects; porting the entire paper's
mechanism without identifying missing target work would be unsupported.

The three PRs were opening-record reads, not complete diff inspections. Their
prefetch exclusions, different architecture and stream-liveness cautions do not
establish a target bug. Exact native code already settles the two proposed
additions, so avoiding unnecessary donor hydration or GPU diagnostics is sound.
The negative result does not reject all future prefetch policies.

## Useful next question

If investigating multiple M tasks sharing an expert/K/N weight tile, identify
an actual missing reuse operation and buffer/task-order contract first. Logical
reloads are not HBM traffic: cache residency and existing locality matter. The
physical expert-row distribution and number of M blocks cannot be inferred
from user concurrency alone. That would be a separately scoped investigation,
not a reinterpretation of this already-implemented result.

## Scope of this review

Read the author report and exact kernel producer sections, dedicated scheduler
role, epilogue metadata release, scheduler consumer/publication and shared-work
sections. Verified31 author files, seven exact revision quotations and four
copied code artifacts against their retained original files. Source integrity
does not establish a running deployment. No new query, native execution,
compiled resource inspection or performance experiment was run.

The first verification attempt expected the previous packet's
`document_revisions` export key; this packet uses `revisions`. It failed before
checking quotes, was corrected against the actual schema, and then passed.
No original source or author evidence was changed.

# Independent review: weight reuse requires a different design

Agree with the bounded result. The native weight TMA loop repeats per task, with
expert/N/K determining the weights and M selecting independent token work. The
existing heuristic explicitly tries to reduce M-block count. Its heuristic cost
is not a measured traffic model. The current normal eviction hint and existing
locality prevent equating logical loads with HBM transactions.

The scheduler creates M-major/N-minor task indices and its L2 admission uses
an M-prefix threshold on each locality queue. For the control's M=4,N=9,
the first nine N-major claims contain only (M0,N0..2), leaving six required
first-M tasks unclaimed when the unchanged threshold passes. That is a valid
counterexample to the metadata implication. The original threshold tracks
claims, not completed GEMM work; the separate readiness waits still matter.
Neither this witness nor the source review reproduces a native deadlock or
proves all alternative schedules unsafe.

The second construction is also appropriately conditional.32 unique-top6
token rows can touch192 distinct experts once or the same six experts32 times.
At BLOCK_M16, those cases have zero versus six extra M blocks. It demonstrates
missing histogram information, not typical routing skew or the chosen tactic.
Physical mapping, valid/captured rows and each layer's route distribution still
need to match before using such a count for eligibility.

The source caps the current operand pipeline at32 stages, below gate/up's40
K tiles. This rules out simply assuming every gate/up weight stage remains
resident across a complete task. It does not establish a lower bound on every
possible cache/reuse design, and does not apply the same40-tile argument to
down projection's18 tiles. A true K-outer multi-M design needs live accumulators,
activation descriptors, stage ownership and release conditions. The existing
two accumulator stages already serve epilogue overlap. Packed FP4 external
bytes cannot be used directly as expanded shared-memory capacity.

Disposition remains no new card: generic tile selection overlaps M01, while
reordering alone does not remove the TMA loop. A concrete future multi-M design
may still be worth investigating when eligibility is established. Keeping that
question parked is more precise than declaring all weight reuse impossible.
No new paper query or native experiment was needed for these source facts.

Reviewed bounded scheduler enumeration/admission, heuristic selection, weight
producer, accumulator/stage definitions and TMA hint helper sections. Read both
stdlib controls and independently checked their integer constructions without
rerunning them.24 frozen author files, six revision quotations and six source
artifacts verified; four artifacts also match retained prior copies. No GPU,
model import, compilation, native timing or canonical mutation.

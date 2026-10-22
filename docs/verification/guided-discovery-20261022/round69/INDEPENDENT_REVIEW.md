# Independent source critique — round69

**Verdict: no blocking factual correction for the stated deferred N03-family refinement. Zero new card and no implementation promotion are appropriate.** The report preserves the useful paper component while identifying a substantial missing implementation contract. Read the frozen report, selected paper sections, original N03 card, actual donor role dispatch/header and target role/barrier/scheduler excerpts. Independently verified all50 author artifact hashes and seven exact quotes. No native/GPU/build execution, additional queries or original edits.

## Paper versus released implementation

The paper expressly describes a shared target checked between tasks and cost/progress-based updates within an invocation. Its controller is more specific than a launch-time allocation heuristic; the selective component is real. The inspected Blackwell donor, however, partitions CTAs once by `blockIdx.x < G.num_dispatch_sms`, uses a fixed dispatch stride and launches the fixed sum of dispatch/GEMM CTAs. The standard donor similarly partitions fixed send/copy/dispatch/compute ranges. These bodies do not show the adaptive controller. The report correctly limits this conclusion to inspected files, not the entire repository.

BF16 activations and weights are enforced by the Blackwell wrapper. Replacing it wholesale is not just enabling an allocation knob on the target's quantized routed/shared two-layer pipeline. Preserving the paper's inference-only control idea does not require transplanting that arithmetic/API. No numerical headline or BF16 port is justified here.

## Target role boundaries are not interchangeable workers

The pinned MegaMoE implementation has dispatch warp groups, activation/scale and weight producers, MMA/scheduler work and epilogue groups within a CTA. Register budgets differ by role; thread counts enter static resource constraints and barrier initialization. The source's whole-GPU heuristic assertion and locality distribution prevent treating an unlaunched spare SM as an existing controller reservation.

A particularly important blocked transition is the activation producer: it can be waiting for a specific generation's L1 token count or L2 dependency while its consumers wait on shared-stage barriers. Reassigning that producer merely because it is currently idle can remove the only participant that makes progress. A “tile boundary” is not automatically a quiescent pipeline boundary. Similarly, dispatch/epilogue fixed-count barriers and the epilogue grid synchronization must still receive all required arrivals even when local remaining work is zero. A safe design must specify task ownership transfer, completion accounting and ring generation before any participant disappears from its role.

The report correctly recognizes existing phase reuse: epilogue threads already transition to combine after L2 completion and grid readiness publication. This refutes a missing-combine-worker story, not every possible dynamic resource policy. Keeping the same participants while changing a legal task queue might be a narrower future design, but the packet has not established such a queue or legal transition. I do not promote that speculative alternative.

## Numerical and benefit boundaries

The donor's adaptive illustration uses128K total MoE tokens and intra-node H100 experiments. It does not establish enough phase duration to amortize counters/controller updates in target small-row decode. The EFA headline includes grouped-expert organization absent from its baseline; the report correctly avoids assigning it to the controller.

Even a safe scheduler must preserve exact work ownership and the intended output arithmetic. Changed arrival/task order cannot be silently assumed to preserve numerical reductions, determinism or stochastic serving outputs. The current report asks for a protocol and later controlled comparison, so this is a remaining gate rather than a factual defect. Source-level waiting branches prove dependency constraints, not measured idle time or recoverable slack.

## Identity and readiness

Original N03 is `hypothesis:8357ac76a236b1a020bb729b91f0f774a779b5740d334b313f299fd54a86d30f`, baseline `1267ac65dc4f2f8fd4af62851edd567cf10ad58e206487c21ab8caa495d5387c`, with an older original-Flash profile. Its exact text proposes routing-known launch-time allocation. The new within-invocation timescale is a useful family refinement, but the report does not rewrite that immutable old baseline into an attested Flash1017 deployment. Keep this explicit during retention; an applicability note is sufficient. No duplicate card is warranted.

## Next useful action; no new paper query now

The next decision is **whether any implementable task-claim/role-transition protocol exists**, not whether adaptive scheduling has been published. The cheapest useful follow-up is to locate the paper's actual adaptive controller implementation in its pinned source tree or explicitly linked artifact, then map one complete transition to the target's existing participants. The packet already retains the tree/commit and paper. Start there; a new generic warp-specialization paper search would likely repeat the principle without resolving the missing protocol.

A new paper query becomes justified only if a named target transition remains unresolved and the desired evidence is precise—for example, a compatible persistent-kernel role migration protocol that preserves fixed named-barrier participants and register allocations. No such follow-up query was run in this review. If the released controller cannot be located or no legal target boundary emerges, keep the refinement parked rather than build an idealized simulator that assumes the answer.

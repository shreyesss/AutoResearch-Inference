# Round102: multi-task expert-weight reuse

## Decision

**Zero new hypotheses; retain a source constraint on future weight-reuse designs.** Weight tiles are logically loaded again for each expert M-block, but the native tile heuristic already attempts to reduce this cost. A task-order change does not itself remove those TMA instructions, and a naive N-major reorder breaks a dependency invariant. Actual on-chip reuse across M-tasks remains a larger, unspecified accumulator/pipeline design, not a ready optimization or a blanket impossibility.

This is the planned Flash1017/c455 + DeepGEMM a7a927 source baseline, TP1 DP4 EP4. No active binary or routing trace was attested. Only source reads, isolated research-tool code retrieval, and stdlib integer/collection checks ran. No model/native/GPU imports, compilation, serving or canonical changes.

## What the source actually does

`target-scheduler.cuh:353–364` claims N-cluster tasks inside each pooled M-block: `m = task / local_N_clusters`, with N varying fastest. The pooled M index maps to an expert and per-expert block using actual cached receive counts. The two cooperating CTAs select adjacent weight-N blocks and operate on the same dynamically sized token dimension; this is not two independent M tiles available for free multicast reuse.

`target-kernel.cuh:753–823` loads weights and scale words for every K block of every task. These loads depend on expert, N-pair and K coordinates, not the task's M index. Thus the same expert/N/K bytes can be requested by several M tasks. This is a **logical load repetition**, not proof of repeated HBM transactions: the exact `common/tma_copy.cuh` default is EVICT_NORMAL, and L2 reuse and physical placement may already serve those accesses. The helper's SM100 two-CTA operation is also not a generic broadcast to arbitrary later M tasks.

The existing heuristic explicitly accounts for reloading weights across M-blocks and selects the fewest estimated blocks and smallest covering tile. The expected count uses local physical token rows × ranks × top-k / experts, with a square-root margin. Its cost comment is an engineering heuristic, not a measured target traffic or latency model. Changing this tile choice using actual histograms is already M01; changing byte packets/cache priority is WP38; physical locality is RD01. None is new under a weight-reuse label.

The MMA instruction's token extent is already aligned from live `valid_m` to16. Round56 established that fact. A larger BLOCK_M does not imply that all padded rows execute as matrix arithmetic, although staging/task/scale/occupancy costs remain. This round does not repeat the disproven coarse-padding forecast.

## Why sorting tasks is not yet a reuse implementation

A pure order change leaves the per-task weight TMA loop intact. It may change L2 residency, reuse distance or contention, which requires a cache-specific hypothesis rather than an assertion of removed loads.

More importantly, routed L2 admission assumes that reaching `(pool_block + 1) * local_L1_N_clusters` claimed L1 tasks means the entire required M-prefix has been issued. The warmup-wave and ring-capacity reasoning use the same ordering. N-major enumeration across M-blocks invalidates that premise. Individual L2 K-block waits remain, but they do not restore the scheduler's proof of forward progress or the ring capacity bound automatically. This is a repairable integration issue for a redesigned schedule, not evidence that all task reorderings must deadlock.

The stdlib discriminator uses four M-blocks and nine local L1 N-pairs, the latter matching18 total target N-pairs split over two locality domains. After nine claims the original order has issued all nine first-M tasks. The naive N-major order has issued only three of them; six are missing while the unchanged counter threshold passes. This demonstrates a failed metadata invariant. It does not run the native scheduler, reproduce an actual deadlock, or claim that every physical scheduling interleaving reaches the witness.

## What actual direct reuse would require

Keeping a weight stage resident while applying it to several M blocks changes the loop nest: process multiple independent token tiles for a K tile before advancing K. That requires multiple live accumulators or an explicit spill/reload, per-M activation/scale descriptors, retained weight and SFB ownership, and barriers that release the shared stage only after every intended consumer. It also needs correct partial-row dimensions, L1-to-L2 readiness, ring generations, shared-expert path and terminal drains.

The present mainloop finishes all K tiles for one task before advancing. Operand stages are reused cyclically. Gate/up has5120/128=40 K tiles, while the source caps the pipeline at32 stages. Therefore even the maximum declared stage count cannot preserve every gate/up weight tile from one complete task for free reuse by the next task. This is a source capacity observation, not a hardware memory estimate; down projection has2304/128=18 K tiles and must not inherit the same40>32 argument.

Two TMEM accumulator stages currently overlap independent task epilogues. Reusing them as simultaneous multi-M accumulators could sacrifice existing overlap; assuming extra accumulators fit is unjustified. FP4 weights are unpacked into the SMEM representation, so their packed HBM byte size is not a valid SMEM capacity estimate. Changing the cluster from its two-CTA N-pair mapping likewise needs a new MMA/TMA ownership contract. No such adapter was specified or implemented here.

## Eligibility: what is known and missing

For routed expert e, define `b_e = ceil(n_e / BLOCK_M)`, where `n_e` is the **physical expert's valid received route count for this layer/invocation**. Cross-M reuse requires `b_e >= 2`. If top-k IDs are unique within each valid token, `n_e` cannot exceed the total valid token rows across ranks. Padded/captured rows, AV compaction, EPLB physical mapping and the selected native tactic must be resolved before applying that bound. The same request concurrency or average expert load does not supply these values.

A second stdlib control constructs two legal unique-top6 assignments for the same32 global token rows, E384/EP4, conditional BLOCK_M16. Spread routing touches192 experts once and has no multiple-M expert. Routing every token to the same six distinct experts yields32 rows per hot expert and six extra M-blocks. Neither is a workload prediction. They demonstrate why the same request/config metadata can support opposite eligibility conclusions.

The retained agent-p75 YAML specifies8192 input/1024 output tokens and eight shared prefixes, not per-layer routed counts or actual captured rows. Retained Mooncake metadata contains request arrivals/input/output/hash IDs, not layer/tactic/physical-receive events. These assets can evaluate service performance of a future concrete implementation but cannot determine this component's multiplicity or cache-hit behavior. No uniform-routing or Zipf model is substituted for the missing trace.

## Stop and reopen

Stop the generic additions before a paper search:

- Fewer M-blocks through tile selection: existing heuristic/M01 question.
- N-major task sorting as claimed load elimination: no loads removed; unchanged readiness proof fails.
- K-outer multi-M on-chip reuse: possible architectural direction, but no bounded target adapter or eligible operating region established here. Park the question without creating a card.

A useful reopening artifact would be an exact native per-layer physical receive histogram and selected BLOCK_M showing material multiple-M eligibility, followed by a concrete loop/barrier/accumulator design that preserves the target contract. A histogram alone does not establish exposed weight traffic. A future performance study must compare the strongest native tactic, account for activation reloads/spills/lost overlap and unchanged routed outputs, and then use existing agent-p75/Mooncake ITL/throughput guards. No GPU work is authorized by this report.

The new information changes the design boundary: it rules out a cheap reorder-only patch and identifies the required M-prefix proof and per-expert multiplicity. It does not change M01/WP38/RD01 status, promote a new hypothesis, or estimate a percentage improvement.

## Evidence accounting

Zero paper queries or new papers. One normal `investigate` call fetched two exact pinned helper files to resolve cache defaults; four target source files were reused. Selected prior100/38/56/M01 parameter-flow material supplied comparison. Two finite stdlib controls ran: a task-prefix invariant witness and same-shape routing multiplicity contrast. No timing or synthetic service simulator.

Exact code quotes, source hashes, raw tool receipt, command journal, source export and read-after-commit verification are retained. The source-first gate prevented spending on another broad weight-reuse query with no defined missing adapter.

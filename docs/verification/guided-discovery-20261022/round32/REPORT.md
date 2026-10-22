# Round32 — replica allocation and placement: test the transfer assumptions

**Preflight result: zero new qualified hypotheses; two retained component leads, neither promoted to implementation.** No model, GPU, device query, serving patch, training, donor module import or cloud publication. Source and scalar CPU work only. Prior guided-card count is unchanged.

## Adaptive search and provenance

Root inspected the full138-card compact inventory across five pages with one stable inventory hash. Targeted CRAFT, replica, replication, rebalancing and H02 recall is retained in `prior-recall.json`. Existing H02 proposals cover payback/pressure-aware placement commits; this inquiry tests which replicas to allocate across layers and what placement changes actually remove. It is not a second copy of those migration policies.

A supplementary web search surfaced CRAFT as an older foundational lead. Its v2 text and released code were then fetched through our cached Sources API, pinned to `Accelsnow/CRAFT_core@968ecd9882d020e7c36471ff51368a9862aab2c0`. This is explicit seed follow-up, not independent discovery by paper-search. The newer June1–October23 search first failed on arXiv429; it was not retried. OpenAlex with the same dates returned eight records. All received abstract dispositions; CAP was selected for full-text mechanism/experimental-section inspection. The retrospective query plan records the provider change and reason for following a different component.

Four local opening-record searches returned0/0/12/25 bounded hits for coactivation/co-activation/replica allocation/expert placement. Four bodies were read closely; the remaining hits received title-level relevance triage. This is not exhaustive PR coverage or diff review. Existing mechanisms were inspected in pinned code separately.

## Lead A: CRAFT allocation across layers

[CRAFT v2](https://arxiv.org/html/2603.28768v2) allocates replicas by per-layer estimated benefit under memory constraints; its released [CPU planning artifact](https://github.com/Accelsnow/CRAFT_core/tree/968ecd9882d020e7c36471ff51368a9862aab2c0) replays expert-load data. This preserves expert identities and is potentially separable from online migration. Its reported large-cluster result does not establish EP4 Flash1017 latency benefit.

### Target ABI is not a configurable per-layer plan

Pinned v4.1 inherits the V4 MoE construction. The native constructor reads one `eplb_config.num_redundant_experts`; the Mega path requires physical expert count divisible by EP size and derives equal per-rank counts. V4.1 extracts one example layer's count into model-wide metadata; `update_physical_experts_metadata` writes the same count to every MoE layer. EPLB uses rectangular layer×physical-expert maps and assumes consistent capacity. A layer-specific variable plan therefore needs a loader/allocator/state/kernel integration change, not merely a new placement JSON or flipping EPLB on.

The default redundant count is zero; **the effective deployment count is unknown**. The two four-GPU groups are separate EP domains. The artifact CLI computes `num_gpus=nodes*8`, so using its one-node default would model the wrong EP domain. Programmatic core parameters may accept4, but that is not an integration test. No actual model weights or routing histogram were loaded.

### Executed scalar falsifier: replay drops remainder work

`craft_core.py` computes `loc_load = idist_slice // logcnt_slice.unsqueeze(0)`, then assigns that quotient to every copy. Remainders disappear. Its balancedness adds the same epsilon to mean and maximum, making all-zero replay load score1.0.

`replica_integer_probe.py` extracts the exact FloorDiv AST and evaluates scalar counts0..64 and copies1..4:123/260 combinations lose at least one invocation. A one-invocation expert with two copies is replayed as zero work; its four-rank balance becomes1.0, while a conserving assignment [1,0,0,0] gives approximately0.2500075 under the same epsilon formula. The latter is a conservation control, not a claim about target assignment policy. No full donor tensor replay or optimizer was executed.

This specifically prevents trusting unmodified CRAFT replay as a small-batch qualification tool. It does not disprove replication or all published results. Reopen only with integer-conserving replay of actual target per-step logical assignments, exact physical remapping policy, held-out workload windows, and a bounded capacity integration design. Average load balancedness is still not latency.

## Lead B: retain CAP placement, omit pruning—but inspect communication

[CAP](https://arxiv.org/html/2607.05116) separates co-activation grouping and load-balance adjustment from optional lossy pruning. The placement-only component is the eligible idea. Its headline endpoint comparisons include pruning; they cannot be quoted as placement-only gains. The text assumes token payload is sent once per visited device and expert outputs are locally combined there.

Our pinned `DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5` differs:

- Dispatch enumerates token/top-k assignments, then processes per-expert receive slots. Source token index is recovered from the token/top-k index.
- Each expert's pool slot issues TMA input loads into its ring buffer, including scale staging. Co-locating two selected experts does not by itself merge these logical pulls.
- Expert epilogue writes into `combine_token_buffer[dst_topk_idx][dst_token_idx]`. Source-rank combination subsequently accumulates the selected top-k slots. It is not the paper's one locally aggregated output per destination device.

Therefore reducing unique destination count is not, by itself, a proof of fewer payload operations in this backend. Source-local accesses, cache reuse, locality and contention can still change physical NVLink traffic; **we did not measure those bytes and do not claim unchanged traffic**. A new backend aggregation/reuse design would be a separate intervention with ownership, exact reduction order and lifetime gates. The narrow placement-only transfer is not qualified from the current surrogate.

Related retained opening records provide useful limits:

- vLLM34811 proposes a custom placement-file adapter for generic FusedMoE, not proof it covers this native Mega path.
- SGLang19772 targets cross-node replica locality; our EP4 group is intra-node. Its traffic and endpoint numbers are distinct outcomes.
- SGLang36820 reports better destination/load metrics without lower actual bytes or latency under a different all-reduce backend. This is contrary engineering evidence about surrogate metrics, not an independent measurement of MegaMoE.
- DeepInfer191 addresses tied-load replica allocation in a different policy. No identical target bug is established.

## Evaluation and stop rule

For a future exact placement investigation, begin with existing per-token logical expert sets plus source rank and the actual physical map. Per-expert totals alone cannot reconstruct co-activation. Replay capacity-constrained placements and compare integer per-rank work, active destinations and backend-specific logical accesses. Do not invent a target histogram. Only an exposed-work argument can justify later implementation.

Existing agent-p75/Mooncake could test endpoint ITL, tails and goodput after qualification. They do not currently supply the required route/physical-map/communication attribution; add those observables rather than a new workload. No numeric SLA or benefit threshold is inherited from either paper.

The best next step today is retain these objections and continue another mechanism. No further synthetic balancedness or destination-count optimization is justified without the missing target data and backend model. This stop is scoped to these direct transfers; it is not a claim that expert placement is globally exhausted.

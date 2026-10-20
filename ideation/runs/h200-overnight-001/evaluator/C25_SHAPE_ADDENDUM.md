# Prospective native-shape clarification for C25

This addendum is written before candidate GPU compilation, correctness outputs
or component timing. It supersedes only the shape selection and component
advance rule in `C25_COMPONENT_CONTRACT.md`; all exact correctness, ownership,
resource, graph-mode, statistical and service gates remain unchanged.

Root's `../native-shape-context.json` summarizes the retained historical C03
baseline exposure snapshots, counting rank 0 once per replica/DP step and
checking all four common-event digests. Among 31,424 online submitted steps,
FULL draft capacities 1, 2, 4 and 7 jointly account for 92.79%. These are
historical warmup-plus-profiling submissions including dummy cooperation, not
current execution-time weights or a latency opportunity estimate. The evidence
arrived before any C25 result and is used to select relevant component sizes.

The component correctness and timing shape set is now
**1, 2, 4, 5, 7, 16, 32, 64**. Preserve the declared tests at the original sizes,
and cover the newly included shapes with the same real-weight finite sequence,
state/temperature/precision and graph replay gates. Do not pool sizes into a
traffic-weighted claim.

For advancing to integration design, require a positive lower 95% paired gain
bound at **each of 1, 2, 4 and 7**, with no observed mean regression above 3%
at **5, 16, 32 or 64**. This replaces the initial 5/16/32 positive-bound rule,
whose larger sizes were not selected using actual historical dispatch evidence.
Mixed outcomes remain inconclusive for this broad seq64 component proposal;
retain all shape results. The actual FULL-graph exposure and primary service
2% materiality gate remain unqualified by these component measurements.

One arithmetic clarification is also frozen before implementation: the real
installed `UnquantizedEmbeddingMethod.apply` dispatches through
`dispatch_unquantized_gemm`, with a separate environment-controlled batch-
invariant path. Use that installed operation in both arms, or establish exact
dispatch equivalence before substituting a direct PyTorch linear call. Record
the relevant environment/configuration and Gumbel precision. The source's
unquantized/BF16 label alone is not proof of a particular backend.

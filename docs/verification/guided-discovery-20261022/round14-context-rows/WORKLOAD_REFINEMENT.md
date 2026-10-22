# TR01 workload refinement — same direction, lower expected warm-single exposure

Append-only refinement of frozen round14 TR01. Original science remains unchanged. Status remains **deferred/low priority**; no new hypothesis or GPU execution.

## Exact threshold versus standard agent-p75

Copied exact workload YAML specifies8192input tokens =6144shared prefix +2048unique, eight prefixes,1024output tokens. A shared prefix does not guarantee a target prefix-cache hit; cache placement, eviction, actual encoding and engine state determine the computed target span. Prefix replay and scheduler chunking also change that span.

The donor's actual predicate, extracted from its pinned Python AST, is:

```
not dummy_run and num_target_tokens > 2048
sum(query_lens - min(query_lens, 133)) >= 2048
```

The second condition is **batch aggregate**, not per request. Its outer comparison is strict `>`, inner comparison inclusive `>=`.

| Conditional current target spans | Donor omitted rows | Donor trigger | Initial graph-prefix-preserving saved rows |
|---|---:|---|---:|
| One warm2048unique span; G6 |1915|No|1909|
| Two warm2048spans in one step; G12 |3830|Yes|3818|
| One cold8192span; G6 |8059|Yes|8053|
| One1024chunk; G6 |891|No|885|
| Two1024chunks in one step; G12 |1782|No|1770|
| Three1024chunks in one step; G18 |2673|Yes|2655|
| Warm2048 + hypothetical128replay rows; G6 |2043|No|2037|

These are row-count scenarios, not measurements of our actual scheduler. One request requires at least2181current rows to meet the donor's2048-drop rule. Preserving an additional six-row captured prefix raises that corresponding threshold to2187 for the narrower initial arm. The proposed adapter should threshold **actual saved eager rows**, not copy the donor predicate when its row set differs.

A large decode-only batch can exceed2048total rows but still drops zero because each request is shorter than133. It therefore remains unchanged. For agent-p75, a single fully warm request can see no effect, while cold prefixes or multiple eligible prefills in one step might activate the path. This further weakens a claim of general long-output ITL benefit. Mixed-load effects require actual eligibility/row telemetry later.

## Ragged-row packing is not free

Do not implement three projections **per request**. Keep at most the same one eager projection per draft layer over a packed eligible row batch; captured-prefix projections stay unchanged. A single contiguous tail may use views. Multiple disjoint request tails require index gathering of hidden rows, positions and each cache group's slot mapping into **separate reusable context workspace**. Original hidden_states, anchors, query_start_loc and captured-prefix indexing remain intact.

Host-known bounds avoid reading rejection counts back from GPU, but they do not eliminate gather kernels, copies, index transfer, scratch memory, launch overhead or potential allocation/graph constraints. Count those costs. Leave full main_proj/hidden combination unchanged in this arm, so donor component timing cannot be transferred. If gathering costs exceed saved projection work, keep baseline. A threshold must eventually be calibrated on actual hardware;2048 is only a donor heuristic.

## Executed evidence

`python3 threshold_audit.py` evaluates the actual donor outer/inner predicate AST with standard-library row-sum stubs over ten scenarios and a dummy-path check. It also checks proposed interval-union counts, including the donor-versus-initial-arm threshold mismatch. Result is **inconclusive for runtime performance/correctness**. No tensors, GPU, cache-hit measurement or serving workload ran.

Retain this report, source-hashed fixture and exact workload YAML alongside original TR01. Future evaluation should stratify cold/warm prefix and actual per-step computed/retained row counts in existing agent-p75/Mooncake; no new service evaluator is needed.

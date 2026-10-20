# Independent review of the fresh H200 run

Reviewed 20 October 2026. Scope: frozen source evidence, runtime snapshots, cards and evaluation contracts; no GPU experiment, server modification or Git operation. This review leaves the three original research runs unchanged.

## Conclusions

The fresh run is a useful second investigation, not independent experimental confirmation. It expands primary-source acquisition from the first H200 run, adds implementation-conflict checks, and produces several genuinely different interventions. Both H200 runs converge on Humming, actual-versus-padded drafter rows, CPU DP synchronization, Hopper candidate scoring and SM90 selection. Their agreement increases confidence that the mechanisms deserve investigation; it does not increase a measured speedup estimate, because neither measured one.

My recommended first **inspection** order is: (1) Humming eligibility and matched backend comparison, (2) FlashMLA plan sharing, (3) drafter padding exposure, (4) CPU DP critical-path cost, then (5) conditional small-row mHC. For maximum capacity under sustained concurrency, mHC should move below mechanisms with broad exposure unless its eligible-row histogram proves otherwise. The fresh ranking's third place is reasonable for a cheap low-load diagnostic, not established as third-best deployment-wide ROI.

The strongest new low-integration candidate is FlashMLA plan sharing. The strongest important negative result is rejection of **private** Engram allocation on a baseline that resolves shared DP storage. The most promising new integration lanes are native MXFP4 FlashInfer, fusion of top-k with page mapping, and DeepEP; all require materially more engineering than the first inspection block.

Evidence: [fresh report](../../h200-fresh-research-001/REPORT.md), [fresh ranking](../../h200-fresh-research-001/RANKING.md), [first H200 index](../../h200-pr-evaluation-audit-001/EXPERIMENT_INDEX.md), [B200 index](../../pr-evaluation-audit-001/EXPERIMENT_INDEX.md).

## 1. Are the two H200 baselines actually comparable?

The frozen inventories agree on image digest `3d17635c…71c`, model revision `2cba9e42…a027`, two TP1/DP4/EP4 groups, API2, seq64, MBT16384, graph cap512, FP8 KV/block64, fixed DSpark k5 with adaptive verification off. This is a strong configuration match. It does not make the hosts interchangeable benchmark replicates.

The fresh run records serving checkout `11c249d28b2962f7384b4ab1fd7c1664704e7524`; the earlier audit's serving snapshot is `2e6fa287d90adf7318ad314de27aa2f595aac821`. Router source/settings, workload client, affinity and environment therefore need their own equality checks. Fresh health checks were successful in its frozen snapshot; the earlier H200 snapshot was taken while loading. Do not infer that the earlier host remains unhealthy or treat those observations as conflicting performance evidence.

Fresh runtime acquisition is more informative about selected branches: Marlin, allgather/reducescatter, and shared DP Engram storage are recorded. The same package version or source text does not prove execution of a specific JIT artifact. Neither snapshot proves an application bottleneck.

Sources: [fresh inventory](../../h200-fresh-research-001/baseline/runtime-inventory.json), [fresh dependency versions](../../h200-fresh-research-001/baseline/dependency-versions.json), [dispatch excerpts](../../h200-fresh-research-001/baseline/dispatch-log-excerpts.txt), [replica 1 excerpts](../../h200-fresh-research-001/baseline/replica1-dispatch.txt), [earlier inventory](../../h200-pr-evaluation-audit-001/evaluation/runtime-inventory.json).

### A material geometry refinement

Fresh dispatch logs contain both of these configurations:

| Recorded geometry | Experts | Top-k experts | Local experts at EP4 | Hidden / intermediate | Clamp |
|---|---:|---:|---:|---|---:|
| First large-model configuration | 384 | 6 | 96 | 5120 / 2304 | 10 |
| Later configuration | 128 | 3 | 32 | 5120 / 2304 | 10 |

The second is consistent with the drafter, but role-tagged call tracing must confirm ownership. Lines 12 onward and 346–370 of the dispatch excerpt respectively establish these two geometries. **Testing only E384/top6/local96 is insufficient for a backend change that also propagates into the drafter.** Humming, FP8 activation and native MXFP4 adapters need both fixture families, or an explicit unchanged-drafter policy. This is a concrete refinement beyond the fresh cards' high-level requirement to check target/drafter parity.

## 2. Crosswalk: avoid counting the same mechanism twice

IDs are local to a run. For example, fresh H02 means plan sharing, while earlier H200 H02 means drafter sizing.

| Fresh card | Earlier H200 equivalent | B200 equivalent | Comparison verdict |
|---|---|---|---|
| H01 Humming backend/indexed-v-grouped | H01 + H07 | E18 broad backend alternatives | Merge at mechanism level; retain staged backend and indexed comparisons. |
| H02 FlashMLA plan sharing | No dedicated card | No dedicated card | Useful new low-integration candidate. |
| H03 small-row mHC | H06 | No dedicated card | Same guarded SM90 mechanism; fresh adds source-application check. |
| H04 logical drafter sizing | H02 | E02 | Same mechanism; fresh documents patch conflicts and acceptance confounding. |
| H05 CPU DP reduction | H03 | E04 | Same mechanism; real group and arrival-skew measurements still missing. |
| H06 gather/direct candidate scoring | H08 | Related E01/E06, not identical | Both H200 runs consider the same alternative implementations; do not stack them. |
| H07 SM90 DeepSelect | H09 | E01/E06 | Related selector family; SM90 native integration is an extra dependency. |
| H08 contiguous MQA epilogue | H16 | No dedicated card | Same prefill mechanism; fresh adds an arithmetic counterexample. |
| H09 final-DP-rank prefix affinity | H12 | E14 | Same routing mechanism. |
| H10 coordinated prefill | H11 | E13 | Same scheduling mechanism. |
| H11 Humming per-token FP8 | Conditional precision scope around H07 | E18 | Distinct arm after H01, not an independent backend win. |
| H12 native MXFP4 MegaMoE | X02 | E18 broad family | Fresh brings a more specific FlashInfer EP4 implementation lead. |
| H13 top-k plus physical mapping | No dedicated card; related H09 | Related E06 | New fusion delta; compare against selector-only, not Torch chain. |
| H14 DeepEP activation/triple buffering | No dedicated card | No dedicated card | New two-stage communication integration lane. |
| H15 mHC stream overlap | X01 | No direct SM90 card | Same conditional Hopper port. |
| H16 SGLang matched control/group32 | No dedicated card | No dedicated card | New engine comparison; engine gap cannot identify an individual kernel. |
| H17 private Engram allocation | Part of broader H10 | Part of E10 | Private branch inactive; shared-placement inquiry remains separate. |

Fresh research does not replace earlier H200 H04 prefix/draft correctness, H05 scheduler bookkeeping, H13 reservation removal, H14 graph coverage, H15 bounded drafter context, X03 KV offload or T01–T03 alternate topology designs. Preserve these as conditional backlog and gates. A fresh shortlist's omission is not rejection.

## 3. Feasibility and the decisive first measurement

### A. Humming: highest practical option value, not proven faster

Problem: Marlin may spend more time in expert gather/permutation and GEMM work for the current routed-token distribution. The proposed solution is first explicit Humming at unchanged activation semantics, then indexed versus grouped Humming. Those are two contrasts; precision changes belong to a third experiment.

Fresh evidence improves this design: installed 0.1.16 has a reported schema mismatch, broad PR #59488 does not apply cleanly, and a separate Humming issue warns about group-scale synchronization. Do not promise a flag-only successful launch merely because the package exists. Establish W1/W2 schema, transport, clamping and both model geometries first.

Minimal decisive evaluation: kernel correctness and activation → unprofiled Marlin versus fixed Humming variants → end-to-end expert spans including gather/scatter and reduction. Existing E1/Mooncake assess service value; only a component fixture and selected-backend counters are additional. If package adaptation is required, keep the required compatibility repair identical across Humming arms.

Sources: [H01](../../h200-fresh-research-001/experiments/H01.md), [H11](../../h200-fresh-research-001/experiments/H11.md), [patch checks](../../h200-fresh-research-001/baseline/patch-application-checks.json).

### B. FlashMLA plan sharing: new, narrow, attractive to inspect

Problem: compatible attention groups may independently build equivalent planning metadata within a pass. Solution: share the holder across genuinely compatible groups and preserve its lifetime/invalidation contract. This can reduce planning overhead without changing attention arithmetic or requiring small local-head counts.

The Python hunks of #58818 apply to a disposable copy; that is useful integration evidence. It does not establish duplicate work on this runner or legal sharing when live lengths/masks differ. A matching tensor shape alone is insufficient. Count planner builds before and after and prove live-value invariants without adding synchronizing device-to-host checks in production. Graph replay may change the visible savings.

Minimal decisive evaluation: changed-length, mask and graph-lifetime fixtures plus planner-call counters; E1/Mooncake can test the service result. Expect a possible small effect and use full-run uncertainty. The H20 author's synthetic acceptance results are not a prediction for real DSpark on H200.

Source: [H02](../../h200-fresh-research-001/experiments/H02.md).

### C. Drafter sizing: plausible broad value if actual padding exists

Problem: target graph capacity can be mistaken for the number of real requests, causing dummy draft rows. Solution: propagate the DP-wide logical maximum separately while retaining target padding and coherent dummy-rank behavior.

This is independent of increasing graph capacity: 64×6 target rows fit cap512. It also depends on graph rounding—fewer logical rows do not guarantee a smaller selected draft graph. First log logical count, target capacity, selected draft bucket and executed rows on balanced and ragged loads. The source patch conflicts with this image, so port final semantics rather than cherry-picking all commits blindly.

Minimal decisive evaluation: ragged/idle rank stimulus (only if fixed E1/Mooncake fail to produce it), distribution/KV/graph fixtures and unchanged real-rejection A/B. A throughput improvement accompanied by unexplained acceptance changes is confounded.

Source: [H04](../../h200-fresh-research-001/experiments/H04.md).

### D. CPU DP reduction: profile exposure before replacing a collective

Problem: small CPU metadata collectives may delay GPU dispatch. Solution: a guarded alternative reduction can lower communication overhead. The observed elapsed collective also includes late arrivals; replacing transport cannot remove that skew.

DP4 permits two recursive-doubling rounds, but this arithmetic is not a speed estimate. Confirm process group, local rank mapping, dtype/op and fixed-tag ordering. Compare matched affinity and host contention, including both replicas. The source patch conflicts with the installed branch.

Minimal decisive evaluation: all-rank entry/exit timestamps and CPU dispatch critical path; E1/Mooncake for service value. Test idle/pause/overlapping collective liveness separately. Keep worker and engine-state changes attributable.

Source: [H05](../../h200-fresh-research-001/experiments/H05.md).

### E. Small-row mHC: cheap inspection; narrower outcome

Problem: existing launch choices may be poor for Hopper's small row counts. Solution: guarded tile/thread/split choice for the delayed mHC kernel. At one k5 request, six logical verification rows can fit its 1–8 band; actual graph/DP padding may leave the band.

The source hunk applies, but E1's sustained concurrency may provide few eligible calls. Inspect actual padded rows and kernel variant before calling this a capacity improvement. Check zero-row handling and the 8/9 boundary. Correctness repair of the affected TF32 path, if needed, must be identical in both timed arms.

Minimal decisive evaluation: independent operator reference and low-load shape sweep only when native workloads lack exposure; retain E1/Mooncake to prove or bound deployment value. A small low-load win can be useful without being a throughput-frontier win.

Source: [H03](../../h200-fresh-research-001/experiments/H03.md).

### F. Candidate-only indexer: long-context opportunity with a real crossover

Problem: Hopper can score the full compressed context before masking away noncandidate positions. Solution A gathers candidate K then scores; solution B reads candidate K through page tables. They remove the same work and should be competing arms.

The retained candidate capacity is 2048×8=16384 compressed positions. Compare this against **actual compressed live width**, not raw prompt length or configured maximum. At short contexts, gather/irregular access can cost more than dense scoring; one source already reports a single-request regression. Both implementation patches conflict with the installed source.

Minimal decisive evaluation: exact cache-layout/causal/remapping fixtures, full-indexer timing and shape-stratified exposure. Use existing Mooncake if its frozen windows contain adequate long contexts; otherwise add one fixed long-context matrix, preserving native short E1 and single-request negative controls. Do not force a host-side shape branch into captured execution without graph-safe design.

Source: [H06](../../h200-fresh-research-001/experiments/H06.md), earlier [H08](../../h200-pr-evaluation-audit-001/experiments/H08.md).

### G. DeepSelect and fused mapping: dependencies before composition

SM90 DeepSelect needs actual extension/build and FP32 input support; the H20 BF16 headline does not settle this. Compare with the existing optimized selector, not just torch.topk. Only after selector eligibility is established should fusion with physical page mapping be tested against the same selector plus separate mapping. Some consumers require raw logical indices and must keep a fallback. Candidate scoring reduces selector width, so gains from these interventions cannot be summed.

Sources: [H07](../../h200-fresh-research-001/experiments/H07.md), [H13](../../h200-fresh-research-001/experiments/H13.md).

### H. MQA epilogue: actual H200 evidence, narrow arithmetic gate

The contiguous prefill epilogue substitutes an add/absolute-value expression with compensated scales. It does not accelerate paged decode. Source inspection shows the old expression; executed include/JIT identity and workload exposure remain unknown. The stored CPU counterexample correctly refutes universal finite-float equivalence; it does not show reachable model failure. Numerical bounds, real-input testing and top-k stability are required. Warm prefix hits can remove most eligible prefill work, limiting E1 benefit.

Sources: [H08](../../h200-fresh-research-001/experiments/H08.md), [numeric counterexample](../../h200-fresh-research-001/prefill-mqa/numeric-claim-check.json).

### I. Integration lanes: preserve but budget separately

- Native MXFP4 FlashInfer: promising EP4 lead, but verify both expert geometries, byte layout, scales, clamp, symmetric workspace and actual API version. A block-FP8 vLLM adapter is not interchangeable with native MXFP4. Include memory/KV loss, not kernel time alone. [H12](../../h200-fresh-research-001/experiments/H12.md).
- DeepEP: current AG/RS never exercises the target dispatch kernel. Compare AG/RS → unchanged compatible DeepEP → patched DeepEP separately. A faster patched DeepEP that still loses to AG/RS is not a deployment improvement. API generation, Marlin payload and graph workspace must match. [H14](../../h200-fresh-research-001/experiments/H14.md).
- SGLang: valuable as a matched service-gap control, but engine migration bundles changes. Keep real rejection, model revision, FP8 KV, host Engram, topology and precision aligned; report irreducible differences. Only then isolate group32 tuning. [H16](../../h200-fresh-research-001/experiments/H16.md).
- mHC overlap: qualifies only after affected operand-lifetime correctness and an exposed synchronous segment. Do not mix overlap with BF16 arithmetic substitutions. [H15](../../h200-fresh-research-001/experiments/H15.md).

## 4. What should explicitly stay out of the first block?

1. **Private Engram registration:** ineligible on the captured shared-storage branch. Do not disable sharing to manufacture applicability. Shared backing, NUMA placement or THP are separate hypotheses with their own exposure checks. Fresh H17's prose retains a generic GPU budget even though its root disposition correctly says no test: the disposition controls. [H17](../../h200-fresh-research-001/experiments/H17.md).
2. **Small-head TP4/TP8 attention and TP sharding:** TP1 has 64 local attention heads and no TP redundancy to remove. These are alternate topology experiments, not live-layout patches.
3. **Marlin 128→64 intermediate padding:** width2304 is already divisible by128 in TP1/EP4; the TP4 width576 benefit does not transfer.
4. **B200 full-graph diagnosis:** the seq128×6=768 argument does not hold at seq64/cap512. Inspect actual rounded misses rather than increasing cap by habit.
5. **SM100-specific kernels:** architectural support needs a real Hopper implementation, not only changed availability checks.
6. **Reported kernel percentages as service predictions:** none of the reviewed cards establishes a measured H200 cost/throughput improvement.

## 5. Evaluation gaps to close before execution

The fresh contract is substantially better than a generic latency benchmark: it separates applicability, activation, correctness, mechanism, service value and integration cost; keeps profiling outside the frontier; uses all-rank counters and paired full runs; and treats acceptance as a diagnostic rather than proof of sampling correctness. Retain these parts.

Concrete remaining gaps:

1. **Freeze an H200 load-discovery rule.** Fresh E1 retains c256/384/512 while the first H200 audit starts lower and brackets capacity. Preserve the original high-load points as historical anchors, but calibrate at lower loads before the candidate, then freeze identical A/B points. Seq64 across eight DP ranks is a scheduler bound, not a proof of feasible memory or sustainable client concurrency. Mooncake may need timestamp slowdown below1x to bracket a passing baseline; retain every failed point and do not relax the scorer.
2. **Resolve SLO and practical-effect policy.** Fresh uses provisional 2% improvement/3% regression language; the earlier H200 protocol uses a different policy. Neither is a production requirement. Select one preregistered decision rule before comparing results, retain old rules as provenance, and avoid declaring a 2% effect simply because five paired blocks ran. Number of repeats does not guarantee resolving power.
3. **Convert generic correctness references into executable mappings.** Several cards say to obtain or map G01–G05 later. The definitions are already in the older audit. Each chosen experiment needs actual fixture names/inputs/tolerances and pass conditions before execution; these are not finished test implementations.
4. **Preserve target/draft distinction.** Source logs reveal different expert counts/top-k. All-rank counters must also identify model role; otherwise a target speedup and drafter regression can disappear inside an aggregate.
5. **Separate cache hits from routing changes.** Native E1's shared prefixes are useful, but final-rank joins and cache salt/state must be frozen. Humming, planner and scheduler comparisons should not accidentally improve prefix locality through changed request placement.
6. **AIPerf version gap:** the fresh report records local0.11.0 versus planned0.13.0 features. Use an isolated pinned client environment and verify registry/export behavior; the installed client cannot be assumed to expose the documented newer diagnostics.
7. **Host/configuration equality:** reattest serving Git SHA, router source, affinity, clocks/power, competing activity and workload hashes. Two different H200 machines are blocks requiring their own paired control, not interchangeable A/B arms.
8. **Do not read token ITL from speculative SSE chunks.** Retain request TPOT using exact output-token count, plus TTFT, completion/drain and raw failures. Token latency and acceptance metrics require actual accounting.
9. **No one-size-fits-all extra evaluator.** Existing E1/Mooncake remain service anchors. Add only the smallest missing stimulus or correctness fixture: ragged/idle ranks, long compressed contexts, 1–8 rows, changed graph inputs, or component references. A new full load generator is not justified by these cards.

Sources: [fresh evaluation protocol](../../h200-fresh-research-001/EVALUATION_PROTOCOL.md), [frozen contract](../../h200-fresh-research-001/evalset-contract.json), [earlier H200 protocol](../../h200-pr-evaluation-audit-001/PROTOCOL.md), [B200 protocol](../../pr-evaluation-audit-001/PROTOCOL.md).

## 6. Process limitations relevant to interpreting the ranking

- Fresh's 108 primary snapshots and 69 patches are acquisition counts, not comprehensive line-by-line validation. Its 16 deferred cards and one inactive rejection are consistent with missing runtime tests. Scores are a proposal rubric, not measured feasibility probabilities or expected speedups.
- Frozen `brief.json` still contains a B200 query string and `nvfp4` among starter queries despite the H200 target. The report documents wider H200/SM90/live discovery, so this is a stale-template provenance concern, not evidence that the research only searched B200. Future runs should generate the initial query set from the actual target and retain the produced queries.
- H01/H02/H03 receive the same generic two-hour inspection and twenty-minute component budget as much larger native integrations. Treat these as stop limits for eligibility checks, not completion estimates for backend adapters or five-pair E1/E2 confirmation.
- The direct patch checks exclude tests/native build/CMake. Success means applicable Python source hunks; failure means an adaptation is required, not automatic scientific invalidity.

## Recommended synthesis

Preserve all original runs as immutable evidence. Build one cross-run mechanism registry with links to each source card, then rank **investigation actions** by current applicability, exposure, expected engineering cost and discriminating power. Use no novelty veto. Start with four source/activation checks—Humming, plan sharing, draft padding and CPU synchronization—because each can cheaply fail or reveal a clear next experiment. Keep small-row mHC as a separate low-load lane and candidate scoring as a separate long-context lane. Promote a combined configuration only after isolated wins and an interaction test; none of the individual gains are additive by assumption.

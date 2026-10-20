# Mechanism cards for E01–E18 and G01–G05

**How to read:** “Source” describes a claim made by the linked PR or issue, not a verified defect in our live B200 image. “Agent hypothesis” is our proposed serving benefit or extension and is deliberately separate. Each card has a falsifiable activation signal. The experiment files retain isolated arms, dependencies and source caveats. An upstream paper's benchmark numbers or a PR's different-hardware numbers are motivation, not our measured outcome.

**Paper-level context, with a narrower claim than the PRs:** [Leviathan et al.](https://proceedings.mlr.press/v202/leviathan23a.html) motivate speculative verification by accepting multiple draft tokens while preserving the target distribution under their algorithm; that is why G01 tests sampling and why E02/E17 measure *useful* accepted work rather than draft throughput alone. The [SPEED-Bench paper](https://arxiv.org/abs/2604.09557) motivates acceptance measurements across domains and serving regimes, rather than only one easy prompt set. The [Mooncake paper](https://arxiv.org/abs/2407.00079) motivates treating cache capacity/reuse and request timing as workload variables. None of these papers proves an individual vLLM/FlashMLA PR is active or beneficial in this pinned deployment.

## Compute, graphs and scheduler

### [E01](../experiments/E01.md) — decode indexer length

- **Source inefficiency and fix:** [vLLM #61039](https://github.com/vllm-project/vllm/pull/61039) describes an indexer scoring work region sized by allocated `max_model_len` even when each row has a shorter live context. It passes per-row ends to DeepSelect so masked, unused positions do not drive work. Its BF16/shape constraints remain eligibility checks.
- **Agent hypothesis:** The 1M maximum context makes this particularly wasteful on 8K and mixed short requests *if the affected indexer path executes*. Savings in indexer time may translate to TPOT/capacity; this is an inference, not a B200 result.
- **Activation/evidence:** Record live length, allocated length, indexed positions and chosen kernel per row; compare indexer GPU time by length with the same output work. Require reference top-k/index correctness and no output regression.

### [E02](../experiments/E02.md) — DSpark drafter padding

- **Source inefficiency and fix:** [vLLM #58984](https://github.com/vllm-project/vllm/pull/58984) says the target FULL graph's padded `DPSyncState.num_reqs` can be mistaken for logical requests in draft dispatch. Its fix uses logical count, avoiding draft rows for graph-only padding; related #61806/#61807 must be reviewed as a bundle.
- **Agent hypothesis:** Even with adaptive verification OFF, target graph padding may leak to DSpark and waste draft launches. The source's reported H20/DP8 adaptive-ON result does not establish this.
- **Activation/evidence:** On every DP rank, correlate scheduled logical requests, target graph capacity, draft logical/padded rows, draft GPU time and accepted tokens. If rows never exceed logical work, close as inactive.

### [E03](../experiments/E03.md) — reachable FULL graphs

- **Source inefficiency and fix:** [vLLM #62040](https://github.com/vllm-project/vllm/pull/62040) addresses a largest uniform draft batch that can miss a FULL graph and fall back to eager/other dispatch. [InferenceX #3095](https://github.com/SemiAnalysisAI/InferenceX/pull/3095) supplies a separate low-load capture-size recipe clue.
- **Agent hypothesis:** With k5, cap512 and the actual seq128 override, graph-bucket gaps may impose launch overhead at frequent batch sizes. An extra bucket also consumes graph memory and may reduce KV capacity.
- **Activation/evidence:** Histogram scheduled tokens, request count, draft/verify shape, selected FULL/PIECEWISE/eager mode and graph miss reason; compare launch gaps, HBM and KV blocks at matched load. Test changed-input replay, especially mixed prefill (G02).

### [E04](../experiments/E04.md) — CPU DP metadata

- **Source inefficiency and fix:** [vLLM #61767](https://github.com/vllm-project/vllm/pull/61767) proposes a faster path for small CPU collectives carrying DP scheduling metadata.
- **Agent hypothesis:** A replicated per-step collective can become a dispatch gap even when GPU kernels are fast. Multi-node improvement claims cannot be transferred to this single-node DP4 deployment.
- **Activation/evidence:** Rank-aligned per-step CPU spans for pack, collective wait/unpack and GPU launch; wait skew and queue age. A CPU-sampling/context-switch Nsight mode or equivalent spans is needed; the current wrapper disables both.

### [E05](../experiments/E05.md) — first-use compilation

- **Source inefficiency and fix:** [#60468](https://github.com/vllm-project/vllm/pull/60468), [#57843](https://github.com/vllm-project/vllm/pull/57843), [#58559](https://github.com/vllm-project/vllm/pull/58559) and conditional [#54345](https://github.com/vllm-project/vllm/pull/54345) describe MegaMoE/MegaGate/mHC/sparse-TopK/metadata variants first compiled after readiness. Proposed fixes precompile the eligible variants.
- **Agent hypothesis:** Cold starts or newly encountered shapes may have severe isolated TTFT stalls; moving compilation to startup trades readiness time and disk/cache size for first-request latency. Warm frontier gain is not assumed.
- **Activation/evidence:** Pin cold/warm compile cache state; log specialization key, compile start/end, readiness, first request TTFT, first-new-shape TTFT, memory/disk footprint and restart time. Do not mix cold measurements into E1/E2 warm capacity.

### [E06](../experiments/E06.md) — sparse top-k route

- **Source inefficiency and fix:** [vLLM #60802](https://github.com/vllm-project/vllm/pull/60802) routes eligible large verification batches to DeepSelect instead of persistent TopK. [#59922](https://github.com/vllm-project/vllm/pull/59922) is a distinct exact BF16 top512 path with metadata reuse.
- **Agent hypothesis:** The preferred kernel can change with batch size, dtype and next-n; use separate arms, not a combined “top-k upgrade.” A launch improvement only matters if this route is hot in the actual service.
- **Activation/evidence:** Log selected implementation, dtype, `k`, next-n, active rows, indexer/logits shape and per-kernel duration; compare outputs to a reference including ties, infinities and boundary tails (G02).

### [E07](../experiments/E07.md) — scheduler draft reservation

- **Source inefficiency and fix:** [vLLM #59468](https://github.com/vllm-project/vllm/pull/59468) removes separate draft work from target scheduler token-budget accounting where that work should not consume target capacity.
- **Agent hypothesis:** With MBT16384, false K−1 reservation may leave prefill/decode budget idle, especially near a boundary; the effect may be negligible away from saturation.
- **Activation/evidence:** Per iteration log target budget, reserved draft slots, actual target tokens, remaining budget, waiting prefill/decode tokens and deferrals; compare queue age and TTFT at matched offered load.

### [E08](../experiments/E08.md) — repacking and repeated casts

- **Source inefficiency and fix:** [vLLM #57977](https://github.com/vllm-project/vllm/pull/57977) retains MXFP8 activations/scales across mHC, projection and MoE consumers instead of repeatedly converting. [#61971](https://github.com/vllm-project/vllm/pull/61971) shares one int32 RoPE-position conversion across layers in a full graph.
- **Agent hypothesis:** Repeated conversions cause kernel launches and memory traffic for no new model information; the two PRs affect different chains and should be isolated.
- **Activation/evidence:** Count active conversion kernels and bytes, trace producer→consumer chain, graph mode and per-layer frequency; check dtype/layout numerical tolerance and changed shapes.

### [E09](../experiments/E09.md) — B200 FlashMLA pipeline

- **Source inefficiency and fix:** [FlashMLA #227](https://github.com/deepseek-ai/FlashMLA/pull/227) changes the B200 fused attention pipeline to overlap KV prefetch/conversion, release TMEM earlier and reduce repeated mask work. This is a kernel design claim, not an end-to-end B200 V4.1 measurement here.
- **Agent hypothesis:** If the pinned `FLASHMLA_MEGA_ATTN_DSV41` call reaches that exact kernel/shape, lower attention time may improve TPOT. A dependency upgrade or new KV layout can change the baseline, so isolate it.
- **Activation/evidence:** Resolve actual FlashMLA version, symbol and dispatch; capture shape, KV format, attention GPU time, memory traffic/TMEM and end-to-end decode contribution. Compare attention outputs to reference across short/long, ragged and graph replay cases.

### [E12](../experiments/E12.md) — scheduler Python path

- **Source inefficiency and fix:** [vLLM #61724](https://github.com/vllm-project/vllm/pull/61724) skips a null SWA block-table head; [#51333](https://github.com/vllm-project/vllm/pull/51333) targets a separate fine-grained full-attention partial-tail path.
- **Agent hypothesis:** Less Python/block-table work helps only if these precise paths are frequent enough to delay GPU launches, likely under long context/high turnover more than 8K steady state.
- **Activation/evidence:** Count affected table traversals/tail cases, measure scheduler CPU time, run queue and GPU idle gaps. Retain block-table correctness under cancellation and cache churn.

### [E13](../experiments/E13.md) — DP prefill coordination

- **Source inefficiency and fix:** [vLLM #51199](https://github.com/vllm-project/vllm/pull/51199) proposes asynchronous coordination when one DP/EP rank's long prefill delays decoding ranks. [#61834](https://github.com/vllm-project/vllm/pull/61834) instead aligns steps synchronously and protects decode steps, adding per-step collective cost.
- **Agent hypothesis:** Coordinating rank schedules can improve mixed-load tails if cross-rank EP work truly couples progress; either design can hurt throughput through coordination overhead.
- **Activation/evidence:** Rank-synchronized per-step prefill/decode token counts, earliest/latest rank start/end, collective wait, oldest request age and TTFT/TPOT tails during mixed long prefill. Compare alternatives independently.

### [E15](../experiments/E15.md) — Engram/mHC fusion

- **Source inefficiency and fix:** [vLLM #60938](https://github.com/vllm-project/vllm/pull/60938) fuses Engram gate/residual work with the following delayed mHC collapse/normalization when the TP1 path is eligible.
- **Agent hypothesis:** Fusion saves launches and intermediate traffic if the normal host-Engram path reaches it; this does not address host lookup latency itself.
- **Activation/evidence:** Verify TP1 dispatch and tensor shapes, count old kernels/intermediate bytes, fused time, Engram total time and numerical deltas; confirm no hidden graph or HBM regression.

### [E17](../experiments/E17.md) — drafter context bound

- **Source inefficiency and fix:** [vLLM #61261](https://github.com/vllm-project/vllm/pull/61261) bounds draft context when acceptance degrades beyond a drafter's trained range; the source motivation is another model/hardware. [#54077](https://github.com/vllm-project/vllm/pull/54077) concerns adaptive mixed-tail profiling and is deferred while adaptive verification is OFF.
- **Agent hypothesis:** A DeepSeek long-context cliff might make shorter drafting cheaper or improve useful acceptance. It may instead lose context needed by this drafter, so first measure the cliff.
- **Activation/evidence:** By context-length band, collect draft proposals, accepted draft tokens, verify steps, draft cost, TPOT and output quality; compare identical prompt/content and k5 policy.

## Memory, cache, routing and alternative lanes

### [E10](../experiments/E10.md) — host Engram backing

- **Source inefficiency and fix:** [#62359](https://github.com/vllm-project/vllm/pull/62359) proposes NUMA-aware host cuMem backing to reduce GPU translation overhead; [#59849](https://github.com/vllm-project/vllm/pull/59849) registers exact table size; [#62269](https://github.com/vllm-project/vllm/pull/62269) unifies exchange-buffer allocation. [#59327](https://github.com/vllm-project/vllm/pull/59327) changes lookup scheduling. [#59923](https://github.com/vllm-project/vllm/pull/59923) is a distinct sharded/packed exchange design, not the same backing fix.
- **Agent hypothesis:** On two DP4/EP4 replicas, host placement and sharing can reduce lookup stalls and duplicated memory, but a NUMA miss or larger pinned footprint can reverse the gain.
- **Activation/evidence:** Per replica/rank table mapping, NUMA node, pinned bytes, host→GPU/exchange bytes, lookup sizes and latency, fault/miss counters, GPU translation evidence if available, and TTFT/TPOT. Treat allocation variants as separate arms.

### [E11](../experiments/E11.md) — DSpark prefix retention

- **Source inefficiency and fix:** [#48459](https://github.com/vllm-project/vllm/pull/48459) prevents a draft group's zero hit from vetoing target GPU reuse; [#47926](https://github.com/vllm-project/vllm/pull/47926) hides restored-but-unwritten draft context; [#61455](https://github.com/vllm-project/vllm/pull/61455) clarifies draft-layer ownership. [#62278](https://github.com/vllm-project/vllm/pull/62278), [#57110](https://github.com/vllm-project/vllm/pull/57110) and narrower [#62206](https://github.com/vllm-project/vllm/pull/62206) address shared-prefix junction/tail retention cases.
- **Agent hypothesis:** Once E14's placement is stable, group-level vetoes or tail drops may still force redundant prefill. These fixes overlap; select a symptom and isolate the relevant patch.
- **Activation/evidence:** Per turn, rank, cache group and layer record queried/hit blocks, junction/tail decisions, restored bytes, actual prefill tokens and output correctness under pressure. Distinguish placement miss from retention miss.

### [E14](../experiments/E14.md) — final DP-rank affinity

- **Source inefficiency and fix:** [vLLM #52464](https://github.com/vllm-project/vllm/pull/52464) addresses rotating internal DP tie-breaks that can send a repeated prefix to a different rank. It remembers a frontend-local prefix key and prefers its rank **only on equal load score**. With API2, each frontend has its own affinity map; high-load cases can still route elsewhere. The PR reports mixed results on a different model/H100.
- **Agent hypothesis:** Existing external bounded endpoint hashing does not guarantee final-rank reuse. Prefix-aware rank affinity may lower repeated prefill at low/moderate load if same-session calls reach the same frontend.
- **Activation/evidence:** Trace session/prefix key→external replica→API PID→final DP rank, tie/load scores, rank-local hit blocks and prefill tokens. Stratify by cross-frontend and load; keep cache salt/LoRA isolation.

### [E16](../experiments/E16.md) — optional KV offload lane

- **Source inefficiency and fix:** [#47891](https://github.com/vllm-project/vllm/pull/47891) addresses connector prefix veto; [#62041](https://github.com/vllm-project/vllm/pull/62041) collects transfers before drafting; [#59096](https://github.com/vllm-project/vllm/pull/59096) fixes disconnect/load race; [#59140](https://github.com/vllm-project/vllm/pull/59140) fixes secondary-tier drop fraction; [#61375](https://github.com/vllm-project/vllm/pull/61375) preserves partial-tail loads; [#61961](https://github.com/vllm-project/vllm/pull/61961) tries synchronous small CPU-tier hits.
- **Agent hypothesis:** Offload could expand effective reuse under an oversized working set, but currently HICache is OFF. Connector, capacity and transfer policy form a separate configuration lane with correctness and tail risks; no default-lane gain is assumed.
- **Activation/evidence:** First prove offload enabled and actual tier hits/evictions; record local/external hits, transferred bytes, latency/overlap, connector waits, dropped stores, KV pressure, preemptions and post-failure recovery.

### [E18](../experiments/E18.md) — alternative precision/layout/kernel routes

- **Source inefficiency and fixes:** [#62011](https://github.com/vllm-project/vllm/pull/62011) enables an FP8 indexer cache route; [FlashInfer #5523](https://github.com/flashinfer-ai/flashinfer/pull/5523) offers generated SM100a kernels; [DeepGEMM #394](https://github.com/deepseek-ai/DeepGEMM/pull/394), [#404](https://github.com/deepseek-ai/DeepGEMM/pull/404), [#436](https://github.com/deepseek-ai/DeepGEMM/pull/436) change weight layout, cache hint or MQA cleanup. [vLLM #61371](https://github.com/vllm-project/vllm/pull/61371) and [#61149](https://github.com/vllm-project/vllm/pull/61149) are dependency/API integration routes; [recipes #1002](https://github.com/vllm-project/recipes/pull/1002) is a TP2 topology comparator. The [experiment file](../experiments/E18.md) records additional conditional branches.
- **Agent hypothesis:** One branch at a time may shift the cost/TTFT/TPOT frontier; each has different eligibility, numerics, HBM and integration risks. A grouped E18 score would be uninterpretable.
- **Activation/evidence:** Pin full dependency/layout and backend dispatch; for each branch report active shape/kernel, precision and reference error, load-time/HBM/KV effect, kernel duration and whole-service qualified frontier. Do not attribute an integrated dependency upgrade to a single leaf PR.

## Correctness and reliability gates

### [G01](../experiments/G01.md) — sampler distribution

- **Source inefficiency/fix:** [vLLM #61161](https://github.com/vllm-project/vllm/pull/61161) reports random draws reused across block-verification rounds, potentially biasing speculative sampling; it requires fresh draws per relevant round.
- **Agent hypothesis:** A performance win is invalid if DSpark changes the target sampling law. Greedy exact-output comparisons cannot detect this class of stochastic error.
- **Activation/evidence:** Seeded categorical reference fixtures across temperature/top-p/top-k, rejection/correction and multiple rounds; preregister tolerance, sample count and multiple-test handling. Compare probability distributions, not sequence equality.

### [G02](../experiments/G02.md) — graph/SWA/index memory safety

- **Source inefficiency/fix:** [#62535](https://github.com/vllm-project/vllm/pull/62535) and [#59986](https://github.com/vllm-project/vllm/pull/59986) constrain graph use around mixed prefill; [#61174](https://github.com/vllm-project/vllm/pull/61174) clears stale block-table rows; [#60767](https://github.com/vllm-project/vllm/pull/60767) masks freed SWA pages; [#60613](https://github.com/vllm-project/vllm/pull/60613) initializes sparse-index sentinel tails; [#62467](https://github.com/vllm-project/vllm/pull/62467) excludes invalid float4 lanes.
- **Agent hypothesis:** Enlarging graph coverage or changing top-k (E03/E06) can expose latent stale-data/invalid-lane paths.
- **Activation/evidence:** Replay changing batch size, mixed prefill/decode, cache eviction/reuse and invalid tails; compare reference outputs, NaN/Inf counts, memory errors and graph mode. Pin tolerances.

### [G03](../experiments/G03.md) — persistent synchronization

- **Source inefficiency/fix:** [DeepGEMM #478](https://github.com/deepseek-ai/DeepGEMM/pull/478) uses execution epochs rather than reused graph grid IDs for mHC split barriers; [#451](https://github.com/deepseek-ai/DeepGEMM/pull/451) resets stale MegaMoE peer readiness.
- **Agent hypothesis:** Repeated graph replay and changing shapes may reveal hangs or stale data that a short steady benchmark misses.
- **Activation/evidence:** Repeated capture/replay with watchdogs, changed inputs and shapes, all-rank progress counters, timeouts and numerical reference checks. A bounded pass is evidence only for exercised schedules.

### [G04](../experiments/G04.md) — real tool-turn semantics

- **Source inefficiency/fix:** [vLLM #62199](https://github.com/vllm-project/vllm/pull/62199) corrects DeepSeek V4.1 tool-result turn encoding/reasoning preservation; [#62259](https://github.com/vllm-project/vllm/pull/62259) targets truncated DSML JSON and incremental argument streaming. The [DeepSeek encoding reference](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/tree/main/encoding) is the tokenizer oracle to pin.
- **Agent hypothesis:** Correct token-level turns and parser events are prerequisites for claiming agent utility; native `agent-f75` prompts alone do not test tool execution or tool-role serialization.
- **Activation/evidence:** Reference token IDs for assistant/tool messages, tool-call ID/arguments, incremental vs full encode equivalence, valid parsed partial/final arguments and reasoning preservation.

### [G05](../experiments/G05.md) — idle/API2/restart

- **Source inefficiency/fix:** [vLLM #59559](https://github.com/vllm-project/vllm/pull/59559) addresses an API2/DP wake-up race after idle/paused ranks; [#62062](https://github.com/vllm-project/vllm/pull/62062) separates draft compile-cache identity between replicas.
- **Agent hypothesis:** Natural Mooncake gaps may be too short to exercise wake-up; explicit idle→burst and warm-restart cases are needed before liveness can be claimed.
- **Activation/evidence:** Record actual idle duration, rank sleep/wake events, first-token delay, stuck requests, watchdog timeouts, compile-cache path/identity and restart result for each replica.

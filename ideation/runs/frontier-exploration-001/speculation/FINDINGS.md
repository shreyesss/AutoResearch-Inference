# Speculation and verification: counterexample-first exploration

**Design outputs, not GPU results.** This branch operated the actual local-corpus/research/evidence/hypothesis tools on the VM. Source dates and states below are stored snapshots from October 19–20, 2026; open PR claims have not been reproduced.

## What changed our thinking

The useful starting point is not “enable speculation.” R7b's checked-in profile already requests DSpark k5 and disables adaptive verification. Its seq64 default is overridden by `lat-seqs-128` for the named experiment. CSV `dspark_config=off` conflicts with the profile, so obtaining the resolved launch configuration is the first gate. Different topology/load observations do **not** prove k5 versus k2 causality.

Two directions survived investigation as **testable leads**, subject to the model decisions saved separately:

1. **Safety-qualified adaptive verification:** keep the existing k5 drafter, vary how many draft positions are verified, and isolate graph safety changes from the adaptive switch. This is an engineering activation candidate, with strong negative evidence; it is not a claimed improvement.
2. **Fix the cost model before inventing a new allocator:** profile schedulable mixed decode/prefill shapes, then test whether a small workload-stratified cost lookup improves budget decisions. The historical source already performs confidence-ranked allocation and graph-padding-aware cost lookup. Reimplementing those would duplicate existing code.

## Search method and coverage

`searches.json` preserves complete bounded results, filters and ordering. Seed **2026102003** shuffles six relevant query combinations; this randomizes traversal order, not PR relevance or model temperature. Each query uses all-token matching, updated date after 2026-08-01 and at most seven hits:

- `speculative dynamic`
- `DSpark adaptive`
- `speculative data parallel`
- `speculative graph overhead`
- `speculative verification prefill`
- `DSpark acceptance`

All six returned hits; no empty local query in this batch. Follow-up `github.get` reads included both the requested seeds and specific contrary evidence, without a date cutoff. Opening records are not complete issue discussions. This is a bounded search, not an exhaustive review.

Two cached OpenAlex searches, each five results after 2025-01-01, were run: `adaptive speculative decoding serving load` and `speculative decoding dynamic verification throughput`. Two web searches identified primary paper URLs. Three paper full texts were fetched through `research.read`. **Zero Serper calls** were used in this branch. Existing on-demand HTTP caches were used. Model stages are fresh calls, not claimed cache hits.

## Grounding and contrary evidence

| Source | What it establishes | Limitation / effect on design |
|---|---|---|
| [#62541](https://github.com/vllm-project/vllm/pull/62541), open, updated Oct 19 | Qualified B200 recipe explicitly keeps full five-token verification | Adaptive off is a deliberate comparator; doc PR is not proof of our deployed flags |
| [#59970](https://github.com/vllm-project/vllm/issues/59970) | Reporter saw DSV4.1 adaptive + FULL_AND_PIECEWISE mixed-prefill illegal access on 2×B300; decode-only graph workaround stable | Reporter also saw adaptive versus off throughput within noise. No assumed win |
| [#59986](https://github.com/vllm-project/vllm/pull/59986), open | Proposed DSV4.1 metadata capability restriction retains decode graphs and excludes mixed/prefill FULL graphs | CPU tests reported; B300 end-to-end reproducer explicitly not run. Requires review and stress test |
| [#52783](https://github.com/vllm-project/vllm/pull/52783), merged Aug 25 | Generic SM100 sparse-MLA support derives request mappings from device boundaries | Evidence is GLM-5.2 on B300, not proof of DeepSeek/B200 support or effect size |
| [#54046](https://github.com/vllm-project/vllm/issues/54046) | **2×B200** report: profiling above seq128 × (1+k7) as uniform decode creates unschedulable shapes | k7 example is not our k5; analogous decode ceiling is seq128 ×6 =768 only if those are actual per-engine limits |
| [#54077](https://github.com/vllm-project/vllm/pull/54077), open | Proposed schedulable mixed-tail profiling; explicit decode/prefill split | RTX5090 regressions, no full DSpark model-serving evaluation |
| [#45963](https://github.com/vllm-project/vllm/pull/45963) | Rank-local dynamic draft K can disagree across DP collectives; disabled when DP>1 | Reject blind batch-local dynamic K on DEP4. Adaptive verification is a distinct mechanism whose collective safety still needs inspection |
| [EVICT, May 2026; revised Sep 5](https://arxiv.org/abs/2605.00342) | Cost-aware prefix retention motivated by expanding expert union in MoE verification | Tree verification, SGLang and other models; does not establish B200 DSpark gains |
| [DScale, Sep 29, 2026](https://arxiv.org/abs/2609.37532) | Variable verification lengths with persistent workspaces can preserve graph reuse | A100/Qwen3 dense experiments, not a ready DeepSeek/B200 port. Additional trained predictor is outside minimal first experiment |
| [Performance or Illusion, revised Mar 18](https://arxiv.org/abs/2601.11580) | Production vLLM study motivates measuring verification cost and request-dependent acceptance | General empirical mechanism, no transfer of speedup numbers |

### Exact grounding excerpts

Short excerpts, verified against saved source bodies:

- #62541: “On B200, DSpark verifies the full 5-token block”
- #59970: “Throughput was the same within noise”
- #54077: “This change profiles tail samples as schedulable mixed decode/prefill batches.”
- #45963: “With DP, ranks can choose different K values”
- EVICT: “retaining only the cost-effective prefix”
- DScale: “Fixed-address workspaces propagate changing boundaries through verification and acceptance while reusing captured graphs.”

`source-*.json` preserve full opening records and separately available children. `model-run/evidence/packet.json` freezes the ten-source, ten-claim extraction and quote validation.

## Exact-source inspection after evidence extraction

[Historical adaptive_verification.py](https://github.com/vllm-project/vllm/blob/ac9126e58aa7bbab1856ba6593ba4d5003fea516/vllm/v1/worker/gpu/spec_decode/adaptive_verification.py) was fetched with `github.code`; source ID and downloaded copy are in `pinned-code.json` and `baseline-adaptive-verification.py.txt`. This file was inspected **after** the ten-source evidence packet was built, so it is an explicitly separate supplement, not silently claimed as model input.

Observed in that pinned file:

- Lines 85–120 already price graph padding discontinuities.
- Lines 188–211 generate profiling samples from token count plus one context length; there is no explicit schedulable request split in that method.
- Lines 223–233 group draft cost by request count and verify cost by target-token count.
- Lines 324–344 choose the draft budget using estimated accepted tokens divided by cost.

Therefore SPEC-2 must add valid mixed shapes and, only if useful, additional mix/context strata. It must not claim a new graph-aware allocator. The historical pin may differ from the benchmark's dirty runtime; source inclusion remains a preflight requirement.

## Experiment contract

The machine-readable design is [experiments.json](experiments.json). Both designs are **planned**, with no test started. Each records the baseline delta, cheap inspection, controls, treatment, ablations, primary and diagnostic metrics, quality checks, held-out workloads, acceptance/rejection/inconclusive rules and budget.

### SPEC-1: adaptive verification with graph safety held constant

- **Control:** fixed k5 on the exact reconstructed R7b setup. Also run a safety-patched adaptive-off arm, so a graph-mode change cannot masquerade as the adaptive benefit. Best static k2 and true no-spec comparisons use the same topology and implementation when supported.
- **Treatment:** fixed k5 drafting, adaptive verification enabled; safe mixed-prefill handling. Do not vary draft K independently on DP ranks.
- **Mechanism:** discarded low-survival candidates save target work; compete against extra compaction, confidence and communication overhead.
- **Stress first:** concurrent prefills, cancellation, EOS, batch drain and variable contexts. Any illegal access, deadlock or unexplained output discrepancy stops the experiment.
- **Discriminator:** compare accepted tokens per full step millisecond, then end-to-end goodput. More accepted tokens per verification call alone is insufficient.

### SPEC-2: schedulable and workload-stratified profiling

- **Stage A:** if absent, port only valid mixed-tail profiling; retain the existing allocator/confidence estimates.
- **Stage B:** only if timing residuals remain correlated with mix/context, profile a bounded lookup over graph mode, prefill fraction `{0, (0,.25], (.25,1]}` and context `{≤8K, 8K–32K, >32K}`. Freeze buckets before held-out testing; do not add a hot-path GPU-to-CPU sync.
- **Controls:** stock table, valid tails only, valid tails plus strata. Offline oracle timing is diagnostic, never presented as deployable performance.
- **Early falsifier:** if the deployed implementation already profiles valid shapes, no mixed steps occur, or timing errors do not change chosen budgets, stop before a large serving sweep.

### Common measurement rules

At fixed 1× replay, R7b is already close to the offered-rate ceiling; seek lower tails there. Capacity improvement requires an arrival-rate sweep with stable queue length, frozen SLO predicates, and matched eight-GPU cost. Preserve both custom length-aware and AIPerf scores, token timestamps and output-length cohorts; speculative streaming bursts can distort ITL.

Proposed engineering advancement threshold: ≥5% capacity-goodput improvement over the strongest matched static control, paired confidence interval excluding zero, with quality and tails protected. This threshold is a design choice, not an expected gain. Use paired randomized AB/BA repeats, a separate held-out trace, and stop on correctness failure or sustained backlog growth. Budget cap per candidate: 60 node-minutes screening plus 90 node-minutes confirmation, including warmup/startup; no execution authorized by registering a plan.

## Deprioritized directions

- Blind “dynamic K by local batch size”: collective-divergence evidence on DP makes this a poor first experiment.
- Async speculative-speculative drafting from #36037: additional coordination and spare-compute assumptions are unmeasured; existing DSpark drafting may already be cheap relative to verification. Measure phase costs before committing implementation effort.
- Copy DScale's advertised speedup or add its predictor immediately: hardware/model mismatch and training dependency exceed the minimal falsifiable first step.
- Treat lower k or adaptive-on as universally better: both B200 qualified settings and explicit contrary reports oppose that inference.

## Actual model decisions and durable memory

The first full tool run generated two proposals and selected zero. The integrity gate correctly rejected the activation card because it cited an unavailable `brief:baseline` source identifier. Its quoted text was present in the original brief, but that brief was not a source in the frozen evidence packet. This was a provenance failure, not a measured failure of adaptive verification.

A **new** `supplemental-packet.json` captures the original brief verbatim as explicit task context, with hash and an unverified-context label, and adds the separately fetched pinned source file. It changes no prior claim or quote. The original packet and rejection remain untouched. `hypothesis.run(revisit=...)` re-reviewed both existing cards under the **same rubric**; no threshold or safety gate was relaxed.

| Design | Latest global hypothesis ID | Decision | Next action |
|---|---|---|---|
| SPEC-1 | `hypothesis:c04f9b8d2efc09f88b48cb83fad06df092ce9ad8ca6e7cd3cd73bdb928dc7f6b` | **Deferred, 76/100** | Resolve runtime and B200 concurrent-prefill correctness/safety; high score cannot override this gate |
| SPEC-2 | `hypothesis:c021e734349347e1c9c3a46e9b5691ef7412fd36272d377b1fc1b0ea3590b5d5` | **Deferred, 64/100** | Establish deployed profiling mismatch and adaptive safety before performance work |

These are credible conditional experiment designs, **not accepted optimizations or validated gains**. The richer stratified-table Stage B in SPEC-2 is an analyst-authored extension of the reviewed mixed-tail card; it has not received its own proposal/critic pass. Parent coordination will register scoped diagnostic plans. This branch registered no tests, executed no GPUs and reported no experimental outcomes.

## Randomized pair search follow-up: useful additional failures

A second search actually samples keyword pairs, rather than only shuffling query order: seed **2026102004**, eight pairs without replacement from `{DSpark, speculative, verification}` × `{padding, prefill, collective, acceptance, latency, budget}`. Complete results are in `randomized-keyword-searches.json`. All eight returned hits. This found two relevant additional records after model review; they are **not** silently included in that review's evidence:

- [#61806](https://github.com/vllm-project/vllm/issues/61806): on DeepSeek-V4-Flash with DP4, target graph padding is reported to leak into the DSpark draft DP sync state. A logical single-request seven-token draft becomes a much larger padded replay. **Add logical-vs-padded draft request counts and draft graph selection to SPEC-1 preflight.** This is closer to DEP4 than the earlier generic DP warning, but model revision/k7 differ and a complete fix was not inspected.
- [#59468](https://github.com/vllm-project/vllm/pull/59468), following [#52922](https://github.com/vllm-project/vllm/issues/52922): separate draft and target passes can be overcharged in one scheduler budget. The proposed port removes unnecessary target-budget charges while retaining a separate draft-buffer request cap. **A follow-up diagnostic:** log charged draft slots and admission-limited steps, first at the actual 16K budget; only then test a constrained-budget lane if the mechanism is active. Its large author-reported result used GB300, TP4, budget512, no prefix cache and short random prompts, so importing that gain into R7b would be unjustified. At a 16K budget this bottleneck may be negligible. This is a documented lead, not a third model-reviewed hypothesis.

The final number is **14 bounded local searches**, two OpenAlex searches, two primary-literature web discovery searches, three full-text paper downloads, one pinned code-file retrieval, one full evidence/rubric/proposal/critic run, and one same-policy critique revisit. No Serper requests and no GPU measurements.

### Explicit dependency for SPEC-2

The inspected table is consumed inside `AdaptiveVerification` draft-budget selection. The checked-in baseline disables adaptive verification; if that manager is inactive, changing its table cannot improve serving. Confirm manager creation and budget-selection invocation in the resolved runtime before proceeding. Both calibration A/B arms must share the **same already safety-qualified adaptive-on build, graph mode and k5 drafter**. Adaptive-off remains a separate deployment comparator. Never credit adaptive activation gains to cost calibration.

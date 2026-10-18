# Research method and experiment rubric

Use this with the inference-research skill. Its purpose is to produce useful, distinct ideas and rapidly test the strongest ones. It does not require a paper-writing pipeline.

## 1. Discover opportunities beyond the current configuration

Use both starting points:

- **Evidence-led:** inspect frontier tradeoffs, queue/cache/acceptance counters and available traces; investigate plausible causes of observed behavior.
- **Opportunity-led:** read inference systems research and implementations for mechanisms that could improve the target, including capabilities not currently enabled. State the conditions under which the idea could help and the evidence needed to check them.

Explore relevant directions such as prefill/decode scheduling, dynamic speculation, sparse attention/indexing, KV allocation/reuse/offload, cache-aware routing, MoE dispatch/overlap, graph/compilation behavior, host overhead and topology changes. These are a search map, not required deliverables or proof of bottlenecks. Include online policies that adapt to queue state, request lengths, cache pressure or acceptance rates when appropriate.

## 2. Find and read papers

1. Turn a direction into mechanism-specific queries. For example `LLM serving speculative decoding adaptive draft length load`, `prefix aware routing cache load imbalance`, or `expert parallel communication computation overlap inference`. Add the model/architecture only when it matters; searching only its exact name can miss transferable work.
2. Search scholarly indexes and primary venues: arXiv, proceedings from systems/architecture/ML conferences, official project publications and author repositories. Search engines and aggregators are discovery tools. Cite the actual paper or implementation.
3. Read the method, assumptions and evaluation sections of the most relevant papers, not just abstracts. Follow references for the underlying technique and citing work for extensions, failures and newer alternatives. Search explicitly for limitations and negative findings.
4. Extract a compact note: problem, mechanism, assumptions, hardware/workload, baselines, reported outcome, cost, limitations, available code and transfer to our setting. Record whether full text/code was read; don't imply it when inaccessible.
5. Compare at least competing approaches for a promising direction when sources exist. Synthesize an adaptation or combination with a concrete mechanism; explain what is new relative to our baseline and previous batches. Distinguish original proposal, cross-system adaptation, upstream port and feature activation.

No fixed paper count proves diligence. The deliverable is a defensible opportunity map and source-backed ideas. If one literature cluster produces no viable idea, change direction rather than polishing empty cards.

## 3. Research PRs and code

Search open, merged and closed/rejected work in the target library and relevant implementations (for example vLLM, SGLang, TensorRT-LLM, Dynamo, DeepEP/DeepGEMM, FlashInfer or cache systems as applicable). Inspect:

- Issue motivation, final diff, review discussion, tests and benchmark conditions.
- Access date, PR state, base/head/merge commits and dependency changes.
- Whether our deployed version contains it, whether enabling it changes semantics, and compatibility with the proposed target build.
- Why a rejected/stalled PR failed: correctness, portability, maintenance cost or weak performance may identify either a blocker or a new research question.

A missing dependency becomes an integration step and cost. An existing implementation is evidence and reusable code. A claimed speedup elsewhere is a hypothesis in our setting. Do not infer applicability from a title or copy headline gains.

## 4. Delegate useful work

For a broad batch, assign a few agents distinct mechanism questions, each combining literature and implementation checks. Avoid having every agent repeat the same repository tour. Example assignments: scheduling/speculation; attention/KV; communication/routing. Tailor them to the question instead of always spawning these exact roles.

Each assignment includes target workload/hardware, existing evidence/pins, relevant prior rejected ideas, requested candidate count, time budget if supplied, permitted actions and a note output path. Ask for counterevidence and cheapest tests, not just supporting citations. Subagents write separate notes and return findings; the lead deduplicates, resolves conflicts and owns the final N cards. A skeptical pass can be delegated or done by the lead. Record which occurred.

## 5. Critique, revise and select

Apply the following rubric with a short evidence-based judgment per dimension. Use strong / plausible / unresolved / contradicted where helpful; these labels are judgments, not measurements.

| Dimension | Required question |
|---|---|
| Value | Which useful operating region or service outcome could improve? What is the expected tradeoff? |
| Mechanism | What work, waiting, movement or resource contention changes? What competing explanation exists? |
| Evidence | What supports the idea, what contradicts it, and what remains a prediction? |
| Integration | Is it active today, activatable, or a new integration? What source/settings/dependencies must change? |
| Correctness | Which semantic, numerical, cache or synchronization behavior could change, and how is it checked? |
| Experiment | What is the cheapest test that can meaningfully change our belief? What are the control and rejection conditions? |
| Cost | What are build/startup/hardware and measurement costs separately? Is a simpler idea likely to deliver similar value? |
| Distinctness | Is this a materially different mechanism from the other cards and prior batches? |

After critique, revise, combine duplicates or replace weak proposals. Do not terminate discovery merely because several initially found PRs fail the frozen baseline's settings. Keep an exploration table showing directions considered and the reasons for selection/rejection. Give the requested number of plausible ideas, with confidence/readiness labels; distinguish ideas worth investigating from those ready to implement. If constraints prevent this, state the shortfall and evidence rather than inventing confidence.

## 6. Smallest useful experiment, then serving point

| Change | First test | Boundary of the result |
|---|---|---|
| Kernel/indexer | Correctness and timing on representative shapes/values/strides; actual target hardware | Operation benefit only; often no model weights needed |
| Communication | Representative messages/routing on required topology with correctness check | Communication benefit; overlaps and serving impact still open |
| Scheduler/cache/router | Component or trace replay with representative state; serving screen if feedback is essential | Replay fidelity must be stated; model-free timings are not serving latency |
| Feature/backend/system integration | Compatibility/correctness smoke and one matched serving point | Integrated system result; causal attribution may need later ablations |

Choose a representative operating point from the applicable baseline. Compare candidate against a contemporaneous unchanged parent using the same service contract, request source, token lengths, arrival/concurrency mode, cache preparation and hardware budget. Candidate settings/backends may change when integral to the idea; record every delta. A patch-only causal test can freeze unrelated settings, but that is not a universal research restriction.

Measure throughput, request-level TTFT/TPOT distributions, failures, quality checks and mechanism counters. Keep short profiler windows separate from scored traffic. Record actual elapsed measurement, startup, compilation and drain time. Use the existing evaluator where suitable; don't invent an evaluator for each idea.

Reject obvious failures cheaply. Repeat uncertain/promising points, then add neighboring loads while the server is loaded and confirm selected results on distinct inputs. An operating curve needs multiple loads; a single measurement is one provisional point. Compare frontiers within the same service contract and resource basis. If quality, workload or hardware changes, label a separate comparison or explicitly include those dimensions. Never hide a quality loss as a latency improvement.

Example budget from the current B200 proposal: two arms × (120 s warmup + 150 s measurement) = 9 minutes scheduled traffic, plus setup/startup/drain; this is not a universal protocol or validated runtime guarantee. Choose duration/sample size using traffic, effect size and observed stability, not arbitrary fixed floors. Reuse a baseline across a nearby batch only with drift checks and clearly stated comparability.

# Round112 — revisit TokenRouter at component level

## Outcome

Zero new hypotheses. A previously abstract-screened paper received a full mechanism read rather than a blanket cross-model rejection. Its delayed-batching idea is separable from token-choice semantics, but the direct benefit depends on repeated irregular model handoffs absent from the declared ordinary single-target serving path. The generic admission-policy remainder belongs beside existing R7b/H01/R4 work; it is not a new missing operation merely because this paper is newer.

No GPU/model/native execution, serving change, canonical write, training or measured gain. Planned Flash1017/c455 remains a source baseline, not a live image attestation.

## Adaptive discovery actually run

The first August1–October22 arXiv query anchored exact serving/host-overhead phrases and returned zero successfully. The next retained the language-model inference/date constraints but broadened CPU/asynchronous vocabulary, returning12 abstracts. These are bounded relevance-ranked results, not recall or novelty evidence. Both calls were cache misses. One selected fulltext, TokenRouter2610.12242v1, was read through the existing investigator; it used two logical HTTP misses within a four-call limit. No automatic reasoning/model call was requested.

Canonical readonly source lookup found prior round16 abstract screening via OpenAlex and the exact title/identifier. Bounded report lookup also found an unrelated AddedTokenRouter symbol in round22; that lexical collision is not prior coverage of this paper. Original round16 dispositions are copied without alteration. Fulltext here is a new reading depth, not a newly discovered paper to count again.

Root made two operator errors: applying interactive-only defer-snapshot to init, then supplying based_on as a string instead of a list. Both failed before provider work; fixes and exact plan versions are retained. No production code change was needed. Four readonly PR searches then selected five existing opening bodies; no PR diff or new GitHub refresh was performed.

## What the paper changes

TokenRouter hosts separate cooperating models with independent schedulers and exchanges peer requests after token-level routing decisions. Requests can return at irregular times. Eagerly executing an early small return batch makes a slightly later arrival wait an entire model step; delaying until a threshold can amortize a wider batch. Its model uses routing probabilities, commit counts and per-model step latencies to optimize aggregate throughput. This does not establish an ITL-optimal threshold under our service guards.

A useful separation is possible: choosing the target model/token semantics is one component; scheduling requests that are already ready for the same model is another. Therefore the prior whole-paper semantic objection was too coarse to settle the scheduler component. After inspecting that component, however, the target exposure premise is still missing.

## Pinned target comparison

Two scheduler files match exact bytes in the retained c455 archive. The native scheduler retains running requests, computed-token progress, speculative tokens and output placeholders. It schedules these running requests before admitting waiting ones. Ordinary decode does not recreate a frontend request and redo prefix matching after every token. The paper's repeated-handoff prefix/cache maintenance times therefore do not estimate our per-token overhead.

The pin already has local prefill cadence and DP prefill throttling, with a capacity-bound escape. This is not the same algorithm as TokenRouter's threshold. It is an existing comparator that a generic batching proposal must beat, rather than assume immediate admission is the only baseline. Existing R7b/H01/R4 cover admission/budget/coordinated-release ideas; LP63's partial-depth continuation is a different, larger intervention and must not be collapsed into this threshold.

As a limited logical check, a steady closed batch on one model with no arrivals or departures has no irregular peer-return stream to accumulate: thresholds at or below the ready batch count do not create the donor's benefit; a threshold above that count stalls absent an escape. This is not a simulation of our arrivals, variable step costs, DSpark progress or DP coupling. With external arrivals, a bounded admission delay could change batching and tails; it requires actual traces and belongs to the existing policy family.

The paper also preserves KV state while a request is pending at another model, captures common extend shapes and colocates routing. Ordinary native running requests already preserve their state. The pinned scheduler additionally recognizes streaming-input requests that retain slots/KV, but that does not prove a complete inter-model handoff implementation. Standard agent-p75 request/response streaming is not automatically input-streaming or inter-model routing. No port is qualified from matching words.

## PR triangulation and strongest contrary evidence

- SGLang29898 reports a delay branch that could starve all ranks under a persistent slot condition; its described repair adds a bounded wait and decays a high-water statistic. This is a donor PR body, not a reproduced target failure.
- SGLang28104 describes an opt-in min-batch prefill trigger and wall-clock escape. Its five-second default backup is not a suitable target latency allowance to copy silently.
- vLLM44558 describes cadence benefits in a different DeepSeekR1/GB200 setup, and explicitly reports TTFT regressions near saturation/prefill-heavy loads. Its percentages are not target ROI.
- vLLM45882 explains an upstream revert due to a scheduler-plugin interface test. The feature is visibly present in our exact fork; upstream revert status cannot override pinned source presence.
- vLLM42500 concerns repeated validation for streaming-input chunks. That does not imply repeated validation per ordinary output token, and it is not evidence that our current load exercises the path.

The paper's model-routing gains and donor cadence results cannot be added. Existing policies need their activation/settings and load region established. A new minimum-batch gate can add queue delay or starvation, including while aggregate throughput improves.

## Evaluation decision and tool usefulness

No new custom benchmark is justified. Future policy comparisons can use the same frozen Mooncake and agent-p75 workloads, preserving offered-load/concurrency profiles, TTFT and ITL tails, completion/error rate and output length. If existing logs lack ready/admission/launch boundaries, instrument those boundaries in the same workloads when GPU execution is separately authorized. The needed addition is attribution, not a different user workload. Do not tune a throughput threshold without the frozen service/tail guards.

Useful commands changed decisions: query refinement exposed a prior-screened source; prior lookup prevented counting it as new; fulltext separated a reusable scheduling component from cross-model semantics; target source showed why the direct overhead denominator is absent; PR search supplied liveness and saturation counterevidence. The resulting zero-card outcome is informative, but it does not measure improved recall, saved service time or a validated hypothesis generator. Raw source IDs/revisions, queries, errors and individual dispositions remain retained.

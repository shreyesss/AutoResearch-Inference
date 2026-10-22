# Round 39 — Preserve the verifier contract before fusing the vocabulary head

## Decision

**Zero new hypotheses. Park LS39-01 as a screened component: target-head normalization partials. No implementation or service qualification.** Direct FlashSampling replacement, greedy head fusion and vocabulary pruning do not satisfy the saved DSpark5/temp1 target. The useful component is smaller: compute normalization statistics while producing the same target logits, then avoid the corresponding downstream target-stat read. It has a concrete October implementation donor, but numerical compatibility and net small-row performance remain unresolved.

This is not C025's five-step draft Markov sampler fusion. All 139 compact prior records were read in two pages with the same inventory hash. Round25 already ruled out greedy-only substitution and found the no-processing logits fast path. Neither is recounted as new. Screen metadata records an exact C025 prior ID and the pinned baseline. This component is not merged into C025, because it changes a different producer/consumer interface; it is retained without allocating another hypothesis identity.

**Scope:** planned Flash-1017 at vLLM `c4557869393db4d75c483d92edd02a5125500883`, H=5120, V=129280, B200 SM100, TP1 within DP/EP groups. No runtime attestation was performed. Saved temp1/top_p1 does not prove the absence of grammar, penalties, forced-token or other logit mutations.

## Actual adaptive discovery

1. Canonical recall waited on the writer lock and was interrupted before operation. A read-only hypotheses backup seeded an isolated state. The initial limit200 command failed; limit100 pagination then returned the complete 139-record inventory. Failed operations remain in journals.
2. Read-only retained-source queries searched sampling/fusion/logits, vocabulary/projection/materialization and then LM-head/Gumbel details. These were bounded FTS results, not exhaustive full-corpus coverage. Six exact selected PR records and their history were imported through `import-corpus` without collection cursors or refresh.
3. A dated **2026-08-01 inclusive through 2026-10-23 exclusive** arXiv query returned 12 papers. Every title/abstract received a disposition. Most were training/application uses of ambiguous sampling/fusion vocabulary. Softmax output-head quantization changes the frozen numerical model; CutBCE's tiled loss aggregation is selectively useful conceptually, not a serving decoder.
4. The next query anchored GPU and logits/softmax to remove those unrelated meanings. It failed with `TimeoutError`. It produced no successful additional paper coverage and was not silently relaxed. The validated v2 expansion plan records this adaptive narrowing. The initial expansion plan failed validation; its empty receipt is retained, not represented as a successful plan.
5. A labelled web supplement located March FlashSampling. Retained-source lookup found its reference in FlashInfer #1035, but no retained paper body, so the exact v1 primary full text was fetched through cached Sources. March is an explicit older exception to resolve a specific consumer-contract question; the dated pass happened first.
6. The operation-level PR search found **FlashInfer #5752**, merged October 1. Its actual diff, JIT map, fixed geometry, backend, generated SM100 kernel and binding were inspected. This recent source provides a more suitable component than either entire training system or complete fused sampler.

Receipts, all 12 paper dispositions, six PR dispositions, full source records/revisions/edges and command journals are retained. No new provider query is needed to decide this stage. Neither paper metadata search nor source inspection proves service relevance.

## What the current target actually consumes

```text
sample_hidden_states = hidden_states[logits_indices]
  -> target ParallelLMHead -> materialized logits
  -> optional grammar mutation
  -> sampler processors / temperature / truncation (or existing no-op return)
  -> DSpark verifier
       target + draft local max/sumexp over 8192-vocabulary blocks
       cumulative target/draft ratios
       full-distribution residual-mass pass
       accept/reject + recovery/bonus sampling
```

Pinned sources are copied under `sources/target__*`, with blob URLs and SHA256 in `target-source-manifest.json`:

- `nvidia/model.py:1612,1648`: target ParallelLMHead and compute_logits.
- `gpu/model_runner.py:1604+`: sampled hidden-row selection, head dispatch and subsequent grammar mutation.
- `sample/sampler.py:226+`: existing `needs_logits_processing` early return. Otherwise logits become FP32 and processors modify them.
- `spec_decode/rejection_sampler.py:246+`: normalization consumes **processed** logits.
- `rejection_sampler_utils.py:208–315,1104+`: the same local-stat kernel scans target and draft distributions. Bonus rows return before statistics. In block mode, cumulative-ratio and residual-mass stages require more than one sampled target token; recovery later rereads logits.

The producer is therefore upstream of an eligibility boundary. Even temp1/top_p1 is insufficient unless all intervening mutation is excluded or exactly incorporated. A first implementation should refuse unsupported processing and use the existing path. Logprobs, masks, row mapping, vocabulary padding and draft-width/bonus semantics must stay valid.

## Why direct FlashSampling is rejected for this deployment

Primary paper: [FlashSampling v1](https://arxiv.org/html/2603.15854v1). Code pinned independently at `6e376af5184d9d3a572755b5260c9c4368562828`. The March v1 and later repository advertise different benchmark summaries; neither speedup is transferred here.

The fused kernel in retained `core.py:480+` accumulates matmul in FP32, divides by temperature and adds Gumbel noise without first rounding logits to BF16. This can be mathematically correct sampling from its own logits while changing the distribution relative to a BF16 materialized reference. The optional returned-logits path does not magically restore the reference rounding or eliminate materialization.

More fundamentally, one target sample does not implement DSpark's rejection correction from target and draft probabilities. An optional LSE epilogue mentioned in the paper still does not supply the complete residual consumer. Recomputing logits, streaming residual statistics or changing verifier scheduling would be a larger separate design; no such implementation is established by this donor.

`consumer_contract.py/json` executes two stdlib counterexamples: FP32 logits `[1.001,1]` round to equal BF16 values and can change both probability and fixed-noise winner; ordinary rejection with p=[.6,.4], q=[.9,.1] needs residual [0,1], not a sample from p. The ordinary case disproves generic replacement, but is not an execution/model of the actual block-verification kernel.

Greedy sharded PR #62604 is likewise ineligible at temp1/TP1 and repeats round25. FlashInfer #1035 and SGLang #38117 concern softmax-free sampling/CPU dispatch already addressed in vLLM. #61869 is the C025 family.

## Selective reuse: LS39-01

Donor [FlashInfer #5752](https://github.com/flashinfer-ai/flashinfer/pull/5752), exact head `67155685cf5f706bd2652edc150cf079c18bed7d`, implements training LM-head/loss machinery. **Retain only the producer-statistics component.** Its generated SM100 logits kernel:

1. Receives FP32 matmul accumulators.
2. Converts each accumulator to BF16 and back to FP32 before deriving local statistics (`kernel.cu:828–841`).
3. Stores the BF16 logits (`852+`).
4. Emits per-row, per-256-column max/sumexp (`877–879`).

This is materially closer to the target contract than sampling raw FP32 accumulators. It demonstrates that retaining logits and producing statistics together is implemented, not merely a diagram.

It is **not a direct port**. The donor has H6144, V154880, 605 vocabulary tiles, 128-row tiles and a two-CTA schedule. The target has H5120, V129280, 505 tiles at width256. Its current verifier uses 16 blocks of width8192. The hardcoded strides/grid must change, and a small-row head backend must be competitive. Global normalization still needs a compatible reduction adapter. The donor's sequential expf recurrence differs from the target Triton reduction; matching BF16 inputs alone does not establish identical LSE, accept/reject decisions or categorical probabilities. A new GEMM can also change the rounded logits themselves.

The required numerical contract must be explicit. For an exact reference contract, refuse the optimization unless required logits/statistics and subsequent decisions match under the declared reference. If a different floating reduction is considered acceptable, assess distributional consequences and record that contract change; do not call greedy equality or a mathematical softmax identity proof of the current stochastic implementation.

## Work removed and competing explanations

For BF16 logits one eliminated target scan is at most **258,560 logical bytes per eligible nonbonus row**. The full BF16 head weight payload is 1,323,827,200 bytes; the scan-to-one-weight-read ratio for M rows is M/5120. This is arithmetic context only, not a roofline or latency forecast. Weight caching, logit caching, launch overhead and overlap are unknown.

The target-logit store remains. Draft-stat scans remain. Block residual and recovery rereads remain. The current target/draft statistic kernel therefore does not disappear wholesale. Producer partial buffers and their reduction add traffic. A custom epilogue can increase registers/latency or make the head GEMM slower; 128-row donor tiling is particularly poor evidence for tiny decode groups. Computing unnecessary bonus statistics is overhead unless skipped safely.

The component is consequently low priority without exposed stage timing. Distinctness alone is not enough to create another deferred hypothesis. A further CPU layout exercise would not resolve the decisive performance uncertainty, so PJ01/WP38 remain stronger next-investigation choices. The separate C025 microbenchmark savings cannot be reused as this component's prediction.

## Bounded evaluation plan, not executed

**CPU/source admission:** resolve actual installed head dtype/backend and all post-head mutation gates from approved manifests; design exact row/vocabulary/statistic interfaces, tail masks and fallback. Current finite CPU diagnostics are **inconclusive for implementation correctness and gain**.

**Later authorized component controls:** A=current head and verifier; B=adapted head retaining logits, original statistic consumer; C=same adapted head plus producer partials and draft-only local-stat branch. This isolates head replacement from the claimed fusion. Check logits rounding, per-row/global LSE, cumulative ratios, residual masses, accepted counts, recovery distribution, RNG consumption and close-threshold cases. Include masks, mixed processed/unprocessed batches, bonus-only rows, EOS, padded/empty rows and fallback.

**Later service evaluation:** unchanged agent-p75 and Mooncake exercise the intended DSpark/temp1 path. Add instrumentation, not a new workload: real nonbonus row counts, processor eligibility, head/stat/adapter times and exposed decode-round critical path. Correctness fixtures are an additional gate. Compare primary long-output ITL/goodput with existing tail/stability guards; no arbitrary inherited speed threshold and no guaranteed improvement.

## Yield and stopping condition

- 12 recent abstracts classified; one failed second provider attempt.
- One older primary paper with code inspected, and one recent donor component traced to actual generated code.
- Zero new hypothesis identities. One screened component retained with exact source evidence and reopening criteria; zero implementation-ready, tested-on-GPU or service-improving claims.
- Direct sample replacement and existing/unsupported mechanisms are screen dispositions, not additional hypothesis identities.

Stop this branch until backend eligibility or exposed-time evidence changes the decision. State is isolated and pending canonical import/publication; retained receipts do not imply S3 synchronization.

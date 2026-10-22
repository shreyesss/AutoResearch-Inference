# Round85 — selectively reuse an offline evaluator from a training paper

**Disposition: retain an evaluation-method refinement for PC76 and related draft-policy comparisons; zero new optimization identities, zero native implementation qualifications or measured serving gains.** No GPU, model, donor package or target runtime was imported/executed. The new computation is a standard-library exact-probability control.

## What the search changed

The initial question was whether recent parallel/Markov sampling work could remove sequential DSpark proposal work beyond C025. A bounded arXiv query, August1 inclusive through October23 exclusive, returned12 records. It found an unexpected useful component: [Training Parallel Speculative Draft Models by Directly Minimizing Expected Decoding Rounds, 2610.10411v1](https://arxiv.org/html/2610.10411v1), October7. Its training algorithm is outside this task; its offline evaluator is independently useful.

The complete isolated compact recall contained149 cards with inventory `c543328973294852aa37233bfbec2144a5a970e9e8d0c7f90d6f05b5d6eea809`. A bounded scan of direct campaign reports additionally found the unregistered/current refinements PC76 and ReAnchor, plus prior42's block-residual objection. Compact recall alone would have missed that recent work while canonical retention waits. Prior frozen reports are unchanged.

Only this selected paper received a full-text read, focused on §§2–3.5 and the conditional-transition proof. All12 results have abstract-level dispositions. We did not establish a new parallel sampler. Local PR queries returned0 exact EDR phrase matches,107 offline+acceptance matches and634 block+verification matches; only the first five of each nonempty result were retained and selected excerpts inspected. These are bounded lexical results, not exhaustive implementation coverage. The local queries ran before the second expansion receipt; that receipt records the resulting revision rather than a fictitious pre-search plan.

## What can transfer without training

The evaluator conditions on a complete target-distributed output sequence. Its state `(n,t)` records the round-start position and current token. For the paper's **ordinary sequential rejection** law, conditional acceptance is

```
A(n,t | committed x) = min(1, q(n,t,x[t]) / p(t,x[t]))
```

This reverses the familiar forward proposal test because it conditions on the committed target token. Propagate state occupancy along acceptance; move to a new round after rejection or the forced bonus boundary. Summing round-start occupancy gives expected rounds conditional on that output. Average across independently sampled target outputs. The round-count estimate is unbiased under the stated assumptions; the ratio used for mean committed length is consistent, not generally an unbiased finite-sample ratio.

This addresses a real limitation of PC76's teacher-forced overlap surrogate: reachability of each round start matters. It does not require changing neural weights. It also does not prove that all offline evaluation is invalid merely because teacher-forced overlap can rank policies incorrectly.

Required inputs are substantial: actual target-output probabilities and normalized candidate draft probabilities for every relevant start/position on those outputs, under the same tokenization, truncation, stopping and sampling law. A baseline trace containing only the starts it happened to visit is insufficient for arbitrary new policies. An arbitrary text corpus is not automatically a sample from the target distribution. The recurrence can be CPU arithmetic once valid inputs exist; producing missing logits or all-anchor draft scores can require model inference. No such target dataset was recovered or generated here.

## Pinned donor code, not a turnkey CLI claim

Read selected functions from [AngelSpec-EDR@0a31a8774a1484ed4af2aeb5ee70c77a4d026360](https://github.com/y-x-zhao/AngelSpec-EDR/tree/0a31a8774a1484ed4af2aeb5ee70c77a4d026360): `angelspec/models/ops/edr.py` contains probability statistics, CPU recurrence and tensor wrappers; `tests/test_edr_cpu_coefficients.py` is donor test source. Neither module nor test was run. The separately retrieved `tools/eval_accept_rate.py` sends requests to a running server; despite its name it is not this CPU offline estimator and was not executed. Three fetched files are not a whole-repository audit.

The donor recurrence has explicit horizon, acceptance and cost inputs. Using that existing implementation later is preferable to creating another full evaluator, after its input law and stopping semantics are qualified. The small Fraction control here is an independent check of the scientific recurrence, not a production replacement.

## Why direct native qualification fails

Pinned [c455 rejection sampler](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py) contains distinct ordinary and block branches. The ordinary branch stops verifying after a failure. The block branch computes clipped cumulative ratios, uses the next-position residual mass, and keeps the latest passing prefix. A later pass can supersede an earlier failure. The paper's two-transition first-rejection MRP cannot simply be labeled exact for that process.

Native adaptive verification can also change admitted draft lengths using batch-level state. A fixed-B independent-request estimator does not automatically model that scheduling policy. Do not disable block rejection or AV in the main comparison merely to make this evaluator applicable. A fixed-B ordinary-policy arm is only a separately named diagnostic. Agent-p75's saved `ignore_eos` and output cap additionally require the real termination contract; blindly adding the paper's terminal EOS changes the experiment.

Retained SGLang42297/43012 opening records corroborate that block and ordinary rules can produce different accepted prefixes. Their author-reported tests and percentages were not reproduced. The source question also exposed a distinct possible lazy residual-scan component in42297, delegated for separate round86 head/code review; it is not accepted by this round.

## Executed controls and falsifiers

`occupancy_control.py` implements two independent finite calculations: enumerate ordinary acceptance/residual event mass; and apply conditional occupancy recursion to each complete target output. Across36 combinations of length, block size and synthetic parent/anchor-dependent proposal law, all270 conditional sequence comparisons match exactly as rational numbers. Output mass also equals the specified target law.

Replacing the posterior ratio with the forward `p/q` ratio fails in all36 configured cases. A separate illustrative `[fail, pass]` control distinguishes first-failure from latest-passing stopping; it is not a model-derived block probability or native RNG fixture. No claim covers real floating arithmetic, native DSpark block verification, AV, target acceptance prevalence or latency.

The independent [preflight review](../review/round85-preflight/REVIEW.md) supplies a stronger discriminator: integrating all four draft paths of one rational two-token model gives expected accepted drafts23/20 for the source block equations versus28/25 for ordinary rejection. This establishes a difference between those ideal transition laws; it is not a native execution or a full-horizon EDR test. Its frozen manifest is `8f67c006d0f7f232abfd80d2f7c950b3c7fbed7c30e0016bb0bfa41721cee3a2`.

## Updated evaluation design and decision

1. Preserve PC76's original target/draft probability contract and baseline. Keep the new evaluator component as linked research, not a new optimization card or promotion event.
2. For an ordinary fixed-policy diagnostic, require target-distributed request/session-disjoint trajectories and normalized all-anchor q for every compared policy. Pair comparisons on the same outputs; freeze scalar selection before held-out evaluation.
3. Before claiming native qualification, derive and independently check the actual block-rule transition kernel and effective AV state. Enumerate tiny complete joint models against a separate forward process; test stopping/bonus/cutoff contracts. A successful ordinary control cannot stand in for this adapter.
4. Use round counts only as algorithmic progress evidence. Native round cost, confidence/AV behavior, graph choices, contention and queueing still determine long-output ITL and separate TTFT/tails on Mooncake/agent-p75. No conversion to percent speedup is justified here.
5. Stop this branch until either the native transition derivation or valid retained target inputs can change the decision. No new model runs are authorized. The candidate remains useful as a selectively borrowed evaluator even though the direct native estimator is unqualified.

One online query,12 paper identities, one full text, three donor files and a retained target file; three local PR queries and ten selected records; one independent exact scalar experiment. **Zero new hypotheses, zero GPU experiments, zero service wins.** The successful output is a more precise evaluation contract, not a favorable self-score.

# Round 66 — What an exact vocabulary reduction actually preserves

## Decision

**Zero new hypothesis identities; no implementation or service promotion.** The recent Pruned CTC paper provides an exact selected-class representation, but its sufficient statistics do not satisfy the native DSpark block verifier. Retain its normalization/numerator separation as additional background for existing **LS39**, not a new proposal. Reject only the scoped transfer that would replace full per-token verifier information with selected-token logits plus one aggregate “other” class.

This round also found an **agent process failure**: compact typed recall was performed, but the available standalone report search was delayed until after one online query. Rounds25 and39 were already indexed and would have prevented treating output-head fusion as an unexplored lane. The normal tool replay now demonstrates this; no retrieval-tool defect or new tooling patch is justified.

## 1. Starting operation and invariant

Frozen source: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, planned Flash-1017/B200 TP1/DP4/EP4 with native DSpark. This is not a live deployment audit.

The concrete operation is the full-vocabulary head projection and materialized target logits:

1. `nvidia/model.py:1648–1659` dispatches `LogitsProcessor` for the target head.
2. `logits_processor.py:_apply_head` applies the full vocabulary weight matrix, with explicit head dtype handling.
3. `rejection_sampler.py:246–287` applies sampling parameters before native verification.
4. `rejection_sampler_utils.py:490–494` computes a per-token positive residual and sums it; `:871–893` needs the individual residual values again for recovery sampling.

**Invariant:** preserve processed target probabilities, cached draft probabilities, block residual mass and recovery token support, not merely the greedy winner or probability of the proposed token. Later processors, normalization and native rounding remain part of the contract. Current weight/head timing and critical-path exposure are unknown; no arithmetic-to-ITL forecast is made.

Two earlier source choices were stopped before paper retrieval: exact Engram row dedup is already EG02, and compressor ratio 1 already constructs no gate/no pooling (`compressor.py:245–305`). They are retained as negative screens, not new opportunities.

## 2. Actual retrieval and the recall mistake

The compact inventory was read in all pages with a stable inventory hash. It exposed C025 sampling, QH45 draft precision and CF59 overlap, but compact typed cards are not a full-text index of every screened report.

One OpenAlex query, August 1 through October 23 exclusive, returned **8 paper identities**: `LLM inference output projection vocabulary pruning exact sampling logits`. All abstracts received dispositions. Pruned CTC, arXiv2609.33645, was selected because it explicitly promises an exact vocabulary reduction while retaining normalization. Other hits concern precision divergence, learned image-token compression, trained early exits, fine-tuned multilingual vocabulary pruning, diffusion decoding, data optimization and structural pruning. Their whole packages do not preserve this target contract; none was promoted or claimed fully read.

Before fetching the selected fulltext, exact canonical source-ID lookup found no retained paper/fulltext under its known IDs. The actual `investigate` tool fetched one unversioned arXiv HTML body and retained its exact revision. Selected sections 3.1–3.4 and Algorithm 1 were read; no author implementation or training experiment was run.

A bounded `rg` search then exposed standalone rounds 25/39. This was **too late**. Read-only canonical report FTS found both reports, including the exact query `verifier fusing head` returning round 39. Selected import of round 25, round 39 and retained FlashInfer#5752 into the isolated state succeeded. Normal-tool `search 'FlashSampling' --kind report --explain` returned no reports before import and the round 39 report afterward. `search 'vocabulary boundary' --match all --kind report` also found the imported predecessors. Before-import absence described the isolated state's coverage, not missing canonical indexing. Receipts preserve the before/after distinction.

Round39 already rejects direct FlashSampling substitution for native block verification and retains target-head normalization partials as LS39. Its October donor#5752 and consumer contracts remain applicable. The actual local `pr-search` over the selected subset retrieved that opening record; this is not a fresh GitHub search, code re-audit or expanded PR coverage.

**Research decision:** no second paper query is warranted. The selected paper allows one additional precise representation check; further broad output-head search would duplicate the earlier unresolved performance question.

## 3. Selective component from Pruned CTC

The paper's exactness depends on a known transcript: valid CTC alignments visit only transcript labels and blank. Other classes still contribute to the denominator. Selected sections describe chunked projection over the full vocabulary with online normalization, followed by selected-class logits and an alignment dynamic program; training backward recomputes chunks. The method reduces activation storage, not the need to account for all vocabulary scores.

That is a useful decomposition even though the complete paper trains an ASR system. We do **not** discard it merely because training is present. The separable inference-relevant component is: retain selected numerators and exact total normalization while discarding individual complement logits when the downstream consumer needs only those summaries.

The native target consumer violates that last precondition. It needs `max(alpha * target_probability[token] - draft_probability[token], 0)` for omitted tokens and later needs their identities for recovery. Neither a selected probability nor the total probability mass of “other” determines this positive-part expression. A richer streamed residual/sampling implementation could in principle retain more information or recompute it, but that is a different design; this paper and the current round do not implement it. Its memory reduction or ASR speedup cannot be transferred to our ITL objective.

Chunked full-vocabulary normalization therefore provides background for LS39, whose producer-statistics/numerical/backend gates remain unresolved. It does not establish a new source absence or remove the already documented target-head/rejection bottleneck.

## 4. Bounded falsifier actually executed

`other_bucket_counterexample.py` uses exact `Fraction` arithmetic, no tensors or native libraries. Select token0 and let target probabilities be `[2/5, 1/2, 1/10]`, with cumulative factor `alpha=4/5`. Three draft distributions all have the same selected probability `2/5` and the same complement mass `3/5`:

| Draft distribution | Positive residual vector | Residual mass | Recovery support |
|---|---|---|---|
| `[2/5,1/10,1/2]` | `[0,3/10,0]` | `3/10` | token1 |
| `[2/5,3/10,3/10]` | `[0,1/10,0]` | `1/10` | token1 |
| `[2/5,11/20,1/20]` | `[0,0,3/100]` | `3/100` | token2 |

Thus identical selected-plus-other summaries can correspond to different native-required residual masses and even different recovery support. This is an information-loss counterexample to the scoped representation, not a failure of Pruned CTC's theorem. It executes the relevant real-arithmetic expression, **not** the Triton verifier, BF16 rounding, a model workload or a latency benchmark.

No redundant toy GEMM/traffic model was run. It would not settle the remaining head-backend or service exposure question.

## 5. Evaluation and stopping condition

Existing agent-p75/Mooncake remain the service evaluation context for any later compatible output-head component. Their saved temperature 1 / top_p 1 settings do not certify absence of grammar or other processing. A new component must preserve full native verification/probability/RNG and logprob contracts before service measurement. C025 component savings cannot be reused as a target-head estimate.

The scoped selected-plus-other replacement is rejected because it lacks required information. LS39 is unchanged and can reopen only with a concrete compatible producer/consumer implementation or exposure evidence that changes its priority. A richer streaming design is not ruled out, but no new implementation hypothesis is manufactured from its possibility.

## 6. Honest yield and tool lesson

- 1 dated online query, 8 returned paper identities, 1 selected fulltext.
- 3 source-level candidate screens: existing Engram dedup; already-eliminated ratio 1 gate; insufficient selected-plus-other verifier representation.
- 1 existing component, LS39, receives an additional applicability boundary; no new hypothesis identity.
- 1 exact-rational counterexample with 3 cases; zero GPU/native/model/build work.
- No canonical, serving, cloud or Git mutations. Local source export and command journal do not imply S3 publication.

The tool lesson is procedural and already documented in the skill: **search available standalone reports before an online retrieval when claiming a mechanism is underexplored.** Compact recall worked within its intended typed-card scope, report search found indexed evidence, and selected import made it available to the isolated agent. This round is not evidence that a new tool improves discovery quality.

# Round78 — ReAnchor: useful proposal features, incompatible direct verifier transfer

**Disposition: zero new hypothesis identities.** Retain one paper's selective feature-reuse component for follow-up. A direct native Flash1017 DSpark port is unsupported by the inspected contracts; this is not a rejection of the paper or of using rejected states as proposal features. No decoder, model, native extension or GPU was run. No canonical/cloud state changed.

## Why this follow-up was worth doing

Round76's dated arXiv search already found ReAnchor (`arxiv:2610.26531`). This round reused that source identity, then read versioned full text §§2.2–3.2, stochastic results, and implementation appendix. **The full text corrects an incomplete abstract-level screen: ReAnchor evaluates temperature1 and DSpark variants on Qwen targets.** It is not a greedy-only or mandatory-training method. The original round76 packet remains unchanged; this report supplies the stronger read depth and correction.

The published mechanism reuses hidden states already produced over a previously rejected suffix. Multiple shifted anchors feed the same frozen drafter, each with its own context and native block length. Baseline and shifted drafts run as independent, batched drafter calls. A shifted anchor token is matched to the baseline and its continuation attached. A token trie is then verified with tree attention under the new attached prefixes. No rejected states are retained after a fully accepted previous block.

Primary paper: [ReAnchor v1](https://arxiv.org/html/2610.26531v1). Exact body and revision-specific quotes are retained in `sources/paper-2610.26531v1.txt`, `claims.json` and `source-export.json`. Reported results belong to its BF16 Transformers/SDPA implementations and Qwen/other evaluated targets, not Flash1017 or our native distributed block verifier. Main-method earliest-token attachment and appendix's “longest matching prefix” description are not identical; unavailable released code prevents resolving that implementation detail here.

## The decisive separation: features, proposal law, acceptance and committed state

| Component | What the paper supplies | Exact native boundary | Disposition |
|---|---|---|---|
| Rejected hidden features | Frozen drafter can condition on imperfect prior verifier states | Native staging still contains current target rows, but source marks rejected rows invalid for ordinary context KV | Potential proposal feature, not automatically invalid |
| Shifted block attachment | Match anchor token, attach continuation, merge trie | Native sequential Markov proposals use a parent-conditioned distribution and cached raw logits | Selection/attachment changes the effective proposal law; cached source-block q is not automatically the correct law |
| Verification | Independently draw target token and accept while it matches a proposed token; no q needed by its stated rule | Native probabilistic path reconstructs q and uses rejection/residual correction, optionally block verification | Paper's losslessness argument does not establish native block correctness |
| Cache commit | Joint target tree verification evaluates each continuation under the attached prefix | Current accepted context excludes the rejected suffix; draft groups and graph buffers have fixed ownership/indexing | Matching one token cannot authorize hidden/KV reuse as committed state |

An imperfect or stale feature can be an arbitrary input to a proposer. It does not need to equal the target's hidden state under the eventual accepted prefix **if** the verifier evaluates the true target distribution and the actual conditional proposal law is handled correctly. That useful principle survives this screen. It does not permit retaining invalid target cache state or applying native p/q correction with unrelated probabilities.

The paper's sample-wise acceptance is a legitimate different design to evaluate, not a transparent replacement for our stronger native probabilistic/block comparator. Tree traversal must also preserve correct target sampling and prefix conditioning. This round did not execute or prove that algorithm, and cannot infer native losslessness from the paper's statement.

## Exact c455 source cross-check

Target sources are from `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, byte-checked against the retained source archive. Standard existing corpus identities were imported into isolated state; no round-specific replacement identities were invented.

1. `target-dflash.py::_store_hidden_states` stages current target auxiliary rows, combines them through the model, and partitions a captured FULL prefix from the eager tail. This provides a potential raw feature source. It does not provide persistent, independently owned shifted-anchor context snapshots across future rejections, request-slot reuse or graph replay.
2. `_prepare_input_kernel` computes `valid_ctx_end = ctx_end - num_rejected`. Invalid rows receive position0 and `PAD_SLOT_ID`; comments explicitly say they write no draft KV and remain fully initialized for graph safety. Reversing this mask would change accepted context, not implement safe side proposals.
3. `target-model-dspark.py::combine_hidden_states` projects the concatenated selected target auxiliary states, followed by `main_norm`. `precompute_and_store_context_kv` applies each draft layer's own projection, norm, RoPE/quant and slot insertion. A generic single last-layer hidden tensor is not automatically the exact native feature contract. Shifted contexts need independent positions, cache groups, ownership and SW state.
4. `target-dspark.py` distinguishes native anchor-as-first prediction (`N` query slots) from DFlash's `1+N` layout. At each native step `logits_i = base_logits[:, i] + bias`, where `bias` depends on the previous sampled token. ReAnchor's paper convention `B = anchor + B−1 drafts` must not be copied as native query geometry or as a depth16 assumption. Planned native maximum remains five drafts; actual AV may verify fewer positions. Only actually computed target rows are reusable evidence.
5. Native `_sample_logits` stores per-position logits through the Gumbel path; `target-rejection-utils.py` reconstructs q from pre-temperature cache and performs normalization and residual processing. `target-rejection.py::_verify` takes a chain of draft samples plus cumulative request logits and the native block flag. No compatible trie/ancestor/cache adapter was established in this call path. This is a scoped missing integration proof, not a claim no tree implementation could ever support the architecture.
6. Confidence features depend on sampled Markov parents. Any changed proposal path also changes the confidence/AV distribution. Preserve the actual baseline AV policy as a comparator; silently disabling it would confound the intervention.

## Prior comparisons and exact stop decision

The copied compact inventory contains147 prior cards. Literal selected fields and bounded standalone reports found no exact ReAnchor intervention. Full dossiers were read for two historical asynchronous draft-cache proposals and TR01; the existing TreeSpark transfer diagnostic was then opened explicitly. The historical cache ideas prepare bounded continuations during verification and invalidate stale state; ReAnchor instead uses previously rejected verifier features and attaches shifted blocks. TR01 removes context projection rows, not proposal work reuse. The TreeSpark diagnostic already owns the broad target-compatible tree-verifier uncertainty. Prior accepted diagnostic status is not an implemented tree verifier.

This is sufficient to retain a distinct **paper component**, but insufficient to create another implementation card: the inspected direct route needs a new trie verifier/cache protocol and an acceptance algorithm change; the smaller chain-only alternative lacks an explicit proposal selection law and pinned released implementation. Inventing an arbitrary mixture simply to generate a card would not close those gaps. Nothing here changes prior hypothesis status or promotes a serving implementation.

### Fastest useful falsifier / reopen conditions

The source inspection already falsifies “flip rejected rows valid and reuse the continuation after a token match” as a supported direct adapter. It crosses an explicit invalid-context mask and lacks evaluation under the newly attached prefix.

Reopen only with a concrete bounded adapter specifying: (a) exact shifted auxiliary feature/position ownership while preserving ordinary accepted KV, (b) either native-compatible conditional q for every selection/attachment decision, including normalizers and residuals, or a separately justified target-sample/tree verifier, and (c) graph/rank/cache/EOS lifecycle semantics. A source-level reconstruction of the released matching and tree traversal would be the cheapest next action if that repository becomes readable. A deliberately smaller chain-only arm must first define its real proposal distribution rather than borrow the unselected source block's logits. Existing round76 wrong-q scalar controls illustrate why this matters, but are not a proof or new test of ReAnchor.

After those contracts, a tiny real-decoder differential/distributional test would be required before timing; it has not been authorized or run here. Preserve the best native block-rejection baseline, actual AV policy, prompt/output lengths and stopping behavior. Do not compare only against the paper's sample-matching baseline.

## Materiality: possible, currently unmeasured

Extra shifted anchors incur independent drafter calls, Markov/head work, context ownership/packing, trie construction, additional target nodes and cache handling. Reusing already computed verifier states avoids repeating those old target computations, but does not make the rest free. The paper explicitly batches `1+|D|` draft calls and has no additional anchors after complete prior acceptance. Native5, actual AV and actual prior rejection distribution bound exposure; a paper block16 histogram cannot supply it.

Let original measured round cost/progress be `T,G`, and changed cost/progress `T+ΔT,G+ΔG`. Improvement requires `ΔG/G > ΔT/T`, including verifier packing, all extra calls and actual streaming/queueing effects. None of these target quantities is measured here. No percentage forecast, speedup extrapolation or additive gain with PJ01/CF59/PC76 is assigned.

## Adaptive tools, failures and yield

- No new online discovery query: followed one known result from round76's dated arXiv search. One new versioned full text was retrieved and read; the next investigation reused it from cache.
- Two `investigate` commands produced two logical cache misses total: successful paper retrieval and failed selected repository metadata stage. The repository `cvlab-kaist/ReAnchor` returned `HTTPError`; the receipt exposes no status code. No commit or donor file was retrieved. Do not infer the repository is absent or claim its code was inspected. Logical misses are not a physical HTTP retry count.
- Read-only canonical PR search `ReAnchor` returned zero. Broader `rejected hidden` returned222 lexical matches, of which the first10 titles were screened; no selected adapter. This is bounded coverage, not absence proof. Exact queries, filters and returned rows remain in two receipts. No PR diff was read in this round.
- Seven source documents and20 revisions are exported: one known paper identity, its versioned fulltext and five pinned target files. Nine exact revision-grounded quotations were checked. The initial source-retention pass and its extension are both present in command history; this is provenance work, not added scientific yield.
- **One new fulltext read, two component dispositions, zero new formal hypotheses, zero implementation/service qualifications, zero GPU/native experiments.** No synthetic case-count test was added because it would not close the current integration gap.

## Rubric outcome

| Criterion | Outcome |
|---|---|
| Primary source mechanism | Pass at paper fulltext depth; donor repository retrieval failed |
| Distinct selective component | Rejected-state proposal features differ from existing work elimination/cache scheduling; broader tree integration overlaps prior diagnostic |
| Exact target applicability | Features potentially accessible; native anchor/Markov/AV/cache and trie integration unresolved |
| Correctness contract | Direct shortcut unsupported; paper sample-matching proof is not native block proof |
| Exposed-cost case | Potential extra committed progress, with extra calls/nodes and unknown eligible frequency |
| Cheapest next action | Inspect released matching/traversal and specify one complete adapter, not more generic literature search |
| Decision | Park component and reject unsupported direct transfer; no new card or status changes |

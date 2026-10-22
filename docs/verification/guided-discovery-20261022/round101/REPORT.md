# Round101 — challenge and implementation triangulation for SN98

## Decision

**Keep the existing SN98 experiment deferred; create no new hypothesis.** Two cited 2025 primary papers strengthen the acceptance-versus-cost objection. A pinned author implementation also supplies positive evidence: its single-draft path already uses a persistent output-position noise tape and commits the coupled target sample. Thus positional persistence has an implementation precedent; our proposed stateless keyed regeneration and native Flash1017 adaptation remain unimplemented.

No inspected component gives a free support-preserving increase in single-chain matching. The list-coupling improvement uses more draft candidates and target evaluations. A separate released multi-draft branch redraws the terminal token after rejection, differing from the paper algorithm; a source-matched exact countercontrol prevents borrowing that branch as a correction. This does not reject the paper theorem or the useful single-draft path.

Baseline remains `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, planned Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, TP1/DP4/EP4, DSpark5, target temperature1/top_p1, baseline d464. No live configuration, GPU, model or native execution was obtained.

## Why these two sources

This is a citation follow-up to frozen round98, not another broad discovery lane. Its complete153 prior inventory and comparisons to C025, FV86,39/42/45/49, ReAnchor and87/89 remain applicable. Exact-title/body lookup in the canonical corpus found neither selected source; no existing paper was needlessly re-fetched. The new isolated `expand` plan explicitly relaxes September–October2026 to the cited 2025 primary methods. One arXiv title query returned exactly two identities, and `investigate` retrieved their versioned fulltexts:

| Source | Read scope | Decision contribution |
|---|---|---|
| Kobus–Gündüz, *Speculative Sampling via Exponential Races*,2504.15475v1 | Simple ERSD algorithm, first-token bound, tree/sequence distinctions, experiments and limitations | Single-chain acceptance is a real drawback; large-tree/asymptotic progress cannot establish native depth5 speed |
| Rowan et al., *List-Level Distribution Coupling…*,2506.05632v3 | GLS construction, algorithms1/2, invariance definitions, memory limits, experimental appendix, released sampling path | More matching requires list candidates; single-chain implementation already retains positional noise; reported support and implementation must be inspected |

No third paper or second broad query was needed. The linked author repository was pinned to observed HEAD `a9d042912b42e5b2b0ea48d650f1b2e8f05af68a`, then five exact files were fetched through the ordinary code-source tool. This is the observed repository revision, not proof it produced the paper's reported tables. Read only: `strategy.py` selected invariant classes, `generator.py`, `utils.py`, benchmark routing in `test.py`, and `qwen2_std.json`. No package was imported or executed.

## What the papers establish—and what they do not

ERSD's simple algorithm samples both distributions with the same exponential variables, commits the target winner, and continues if it matches. The paper upper-bounds first-token matching by maximal rejection acceptance. Its own sequence-drafting experiment reports lower progress than greedy rejection. Much of its stated “speed-up” is expected tokens per target evaluation, rather than synchronized end-to-end latency. The large-tree/Tunstall analysis and batch gains do not transfer to a fixed native five-position single chain. These are useful counterweights to the attractive removal of residual scans.

GLS uses K independent candidate tapes; its target winner uses the minimum exponential clock across active drafts. K is draft count, not native lookahead depth. Extra matching is purchased with multiple proposals, conditional target contexts, random arrays and reductions. The paper itself warns about oversubscription. K=1 reduces to the same exponential/Gumbel coupling, not a stronger free correction. No source read here proves an impossibility theorem for every possible correction; it simply supplies no cheaper single-chain correction that we can presently transfer.

The GLS main text says its experiments use the full Qwen vocabulary of151,936 possible tokens. Its experimental appendix explicitly states top-k=50. These statements must not be read as evidence of an untruncated target law: the code allocates full-width tensors, then masks all but top50 scores. `test.py` passes temperature and generation length but no top-k override; the generator default is50. `LogitsProcessor.__call__` calls `torch.topk`, scatters those values into an otherwise negative-infinity tensor, then divides by temperature. Its stored top_p field is not used in that method. Full tensor width and full probability support are different facts. Native target support stays unchanged in SN98; donor measurements do not establish its full-support cost.

## Useful implementation precedent: persistent single-chain tape

`InvariantGenerator` allocates `[max_new_tokens + draft_len + 1, K, vocab]` randomness once before its generation loop. Each round computes `position = input_ids.size(-1) - input_len`. `InvariantSingleDraftStrategy` slices the same absolute-output-position interval for draft and target Gumbel calls. Target verification computes all admitted row samples, takes the first mismatch or bonus, commits that already-selected target token, and crops the conventional cache. It returns no draft-probability cache.

This closes an important source-evidence gap in round98: persistent position noise is not a newly invented ingredient. It does **not** certify the native integration. The donor asserts batch size1, uses conventional DynamicCache and fixed draft length, performs Python branching over tensor results, and materializes its tape. It does not implement native DSpark's parent-conditioned Markov outputs, AV compaction, packed cache, rank collectives, streaming/stop bookkeeping or seed lifecycle. The target source still salts draft noise and mixes speculative step; `draft_logits=None` still means greedy selection. Those differences require an explicit new mode, not copying the donor or deleting the cache pointer.

Logical tape storage, assuming the donor's default float32 allocation:

| Geometry | Bytes | MiB |
|---|---:|---:|
| Donor output128, depth4, K1, vocab151936 |80,829,952|77.09|
| Same, K8 |646,639,616|616.68|
| Illustrative target output1024, depth5, K1, vocab129280 |532,633,600|507.96|
| Same, K8 |4,261,068,800|4063.67|

These are resident array sizes, not measured HBM traffic or latency. Full preallocation is inappropriate to assume free at serving concurrency. Stable-coordinate regeneration can avoid storing the whole tape, but its PRF, precision, ties and counters must match the declared target-only oracle. The donor's `gumbel_noise` clamps uniforms/log inputs; its random sequence and arithmetic are not automatically interchangeable with native Murmur-based sampling. Timing starts before donor tape allocation, but source inspection alone does not establish device-synchronized measurement or predict native cost.

## Do not transfer the multi-draft fresh-redraw branch

Paper Algorithm2 returns the sampled target token when the viable candidate set becomes empty. The pinned `InvariantMultiDraftStrategy.verify_draft` instead ends with `gumbel_sample(logits[alive_group_id, depth])`, without passing the previously shared noise. The noise-preserving call is commented out. This is a different branch from `InvariantSingleDraftStrategy`, which commits `target_ids[0, depth]`.

`source_controls.py` parses these actual methods without importing tensor code and retains three exact ideal-law controls:

1. **K1 full-support control:** p=(4/5,1/5), q=(1/5,4/5). Shared exponential matching masses are(1/5,1/5), and rejection mass3/5. Redrawing independent p after mismatch emits(17/25,8/25), not p; TV=3/25. The class supports K1, but this is not the configured multi-draft benchmark.
2. **K2 boundary control:** q=(0,1), two identical-support draft draws, target p as above. The target winner0 makes both candidates reject. A fresh target redraw gives output0=(4/5)^2=16/25. This is a zero-proposal-mass sanity control, not observed logits.
3. **K2 full-support branch control:** same positive p,q as control1. At depth0 both target rows have the same actual prefix. Write a=q0/q1=1/4, b=p0/p1=4 and independent Exp(1) clocks E0k,E1k. Conditioning on min(E11,E12)=t gives

   `P(all X=1, Y=1) = 2 ∫ exp(-(1+b)t) [exp(-(1+b)t) - a/(1+a) exp(-(b+b/a)t)] dt = 23/125`.

   Therefore the no-match mass is `(4/5)^2 - 23/125 = 57/125`. Y1 necessarily has a matching draft, so the matching diagonal is(43/125,25/125). In the all-rejected branch `alive_group_id` stays0; its row still has target p. Fresh redrawing produces output0=443/625=.7088 instead of.8, TV57/625. This directly addresses K2's branch rather than extrapolating K1.

These establish non-equivalence for the ideal arithmetic branch being inspected, not measured error in the paper's tables or finite native code. No inference is made that the paper theorem is wrong, that native DSpark has this branch, or that every other donor strategy was audited. The safe single-chain reuse is the coupled target sample. A valid correction could exist under another derived conditional law; unconditional fresh p after a noise-dependent mismatch is not one.

## Updated SN98 gates and comparison

The independent round98 review adds the same requirement to native fallback: a late decision based on sampled drafts/noise cannot silently discard the tape and switch to independent native sampling. Target-only fallback at the current actual prefix with the **same** tape stays inside the pathwise proof. Static eligibility selected before future draws is a different case; any other switch needs a valid conditional-law argument. This packet references the independent review rather than modifying frozen98.

Keep the target-only functional oracle and full support. Preserve actual AV policy, sampled-parent confidence inputs, EOS/stop/logprob semantics and seed state. The paper's context-independent-clock theorem is not the proof for our position-tape adaptation. The donor source supports feasibility of the ingredient; the separate pathwise argument supports the proposed adapter mathematically, with native tests still missing.

Let g be actual committed progress and C complete round cost. Improvement requires `C_new/C_old < g_new/g_old`, measured under the same workload and policy. The round98 B1 example gives53/56 and thus requires more than5.357% whole-round cost savings; that remains a hypothetical one-draft discriminator, not native block5 data. Current native block selection, C025 fusion and FV86 where compatible are the strong comparator. Head computation and dense logits remain; new per-row target Gumbel work and lower acceptance may outweigh removed probability/residual work. The ordinary/block offline estimator cannot be fed marginal acceptance values and called an SN98 prediction.

The cheapest next useful work is a source-level mode/seed/row-map/fallback admission table and, if later authorized, a minimal native reference-oracle parity implementation. Further generic papers cannot establish current exposed verifier time. No new offline synthetic case count or broad benchmark harness is required before that gate. Retain SN98 as a larger deferred experiment with stronger source support and sharper null conditions; do not promote it over narrower candidates based on paper headlines.

## Evidence and yield

One citation title query, two returned identities, two versioned fulltexts selectively read, one pinned donor repository/five source files, two reused native source files, three scoped exact controls. No new hypothesis identity, implementation, service acceptance or GPU action. Search and fulltext receipts report one plus two logical cache misses; code investigation reports five, and direct GitHub pin/tree lookup used two additional read-only HTTP requests. These are logical retrieval counts, not billing or guaranteed wire-attempt totals. No provider error or relaxation occurred. Some broad grep output was truncated; decisive algorithm/source sections were subsequently read directly. Isolated evidence persists; snapshots/S3 remain deferred. `source-export.json`, `claims.json`, source hashes, actual command journal and the frozen manifest preserve the result.

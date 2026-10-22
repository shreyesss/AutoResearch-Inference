# Round47 — exact indexer block geometry, with negative screens retained

## Outcome

**No new implementation-qualified hypothesis.** Two recent papers supply a useful optional refinement of the existing AT01 certificate family: cache conservative key-block geometry and use it to reject blocks before evaluating all 32 indexer heads for every key. This is deferred, with neither target numerical admission nor pruning/latency evidence. The papers' actual approximate policies are rejected **only as direct replacements for the frozen exact selector**; their reusable mathematical component is retained.

This is a source-plan audit of `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, Flash-1017 config revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, not a live deployment attestation. No GPU, model/runtime imports, serving change, benchmark or canonical state mutation occurred.

## Discovery and yield accounting

- Read current discovery/critic skills and all **142 compact prior cards** in two pages with matching inventory hash. Linked prior AT01/AT02/M02/M03/MP17 mechanisms constrain interpretation; title absence is not proof of novelty.
- Two successful online OpenAlex searches, August1–October22 window, **20 hit references / 20 paper identities**. All are retained in `paper-dispositions.json`, including unrelated results. No third broad query.
- Two complete extracted fulltexts inspected: RBS-Attention (2609.20971) and Elastic Threshold Attention (2609.20888). Both were obtained from **unversioned HTML locators**; fetched content hashes are retained, but neither is falsely described as an arXiv revision pin. Exact-title/identifier retained-source lookup found no prior fulltext before fetching.
- Read-only local corpus queries `centroid`, `radius indexer`, `geometric attention`, `Quest attention`, `upper bound indexer`, limited12 each. Four opening PR bodies were imported to isolated state and inspected with actual `pr-search`. This is a selected four-record replay, not a claim of complete PR diff coverage.
- Two direct paper policies and one direct LiteTopK transplant rejected as scoped; one existing hypothesis family refinement deferred; two additional PR branches remain unqualified and one PDL branch is an unresolved source question. These screens are retained in `screened-interventions.json`. **Zero new formal hypothesis identities**, not zero screened interventions.
- Initial query2 expansion used unsupported observation status `partly_relevant`; corrected to `useful`. Search happened after the failed expansion before repaired expansion, as command journal records. No claim of a successful planner before that query. Additional local command/path mistakes are retained in `tool-errors.json`.

## What the papers really contribute

### RBS-Attention: exact geometry, approximate deployed selection

Source: <https://arxiv.org/html/2609.20971>, extracted text §2.4 (around lines308–323), §3 radius modulation (around437). For keys in a block with centroid c and maximum radius r:

`q·k <= q·c + ||q|| r`.

This full-radius expression is a conservative real-arithmetic upper bound. The deployed radius contribution is attenuated (beta<1), then combined with thresholds/rescue rules. That policy is explicitly empirical; it is not an exact maximum certificate. Fulltext explains that large radii may be loose under query/deviation misalignment. Its H100/Qwen prefill results do not establish benefit on the target.

**Executed counterexample:** scalar keys{0,2},c=1,r=1,q=1,beta=.2 yields score1.2 while true maximum2. A threshold1.5 wrongly prunes the winner. This rejects an attenuated-bound substitution, not the unattenuated component.

### ETA: cached summaries do not make the learned score an exact bound

Source: <https://arxiv.org/html/2609.20888>, §3.1 around535–580. Retains centroid, coordinate standard deviations and maximum norm, combining a Gaussian-style score and spherical bound using `min`. Thresholds/activation assumptions involve training and altered attention. A probabilistic term remains probabilistic even when minimized with a safe spherical term.

**Executed counterexample:**64 scalar keys comprising63zeros and1one; q=1,z=2.3. Gaussian score=.300870..., spherical upper=1, their minimum=.300870... although true max=1. A threshold.5 discards the winner. We do not infer all ETA's empirical policies are useless; they are ineligible as exact frozen-selector replacements.

Neither fetched fulltext supplied an author implementation repository that we inspected. Author kernel correctness or availability is not claimed.

## Selective adaptation: AT01 block geometry option

The target's indexer combines32 head terms with learned signed weights:

`S(k) = sum_h w_h ReLU(q_h·k)`.

For a key block centered at c with radius r, define:

```
L_h = max(0, q_h·c - ||q_h|| r)
U_h = max(0, q_h·c + ||q_h|| r)
U_score = sum_{w_h>=0} w_h U_h + sum_{w_h<0} w_h L_h
```

Multiplying every upper term by a negative weight is unsafe. The signed formula supplies a real-arithmetic bound. A block may be skipped only if its **conservative target-reference upper bound is strictly below** a proven current-query Top512 threshold. Equality cannot be pruned without preserving the precise tie identity contract.

This is an alternative block-level first stage within AT01, which already studies certified work elimination. It differs in mechanism from DoSA's partial-head evaluation: geometry is maintained across queries on key blocks, then used before per-key scoring. It does not become a separate novel card just because it comes from another paper.

### Exact source applicability and first useful consumer

Copied source and hashes are in `source-manifest.json`:

- `deepseek_v41/attention.py:101–109`: indexer key format is68bytes for MXFP4 or132bytes for FP8; this is not the528byte attention KV cache.
- `attention.py:1417–1440`: consumer sparse scoring is opt-in, requires candidate buffers, excludes candidate-producing layers, and requires MXFP4. Source availability does not prove runtime flag activation.
- `attention.py:1465+`: key production runs learned projection, normalization, RoPE and quantized cache store. Non-boundary compressed rows are not valid new keys. Conservative summaries must describe the **stored dequantized post-RoPE values**, not an earlier projection. Summary ownership is per actual key-cache identity/version; shared candidate indices or schedules do not prove key bytes or summaries can be shared across layers.
- `sparse_mqa_logits.py:312+ /401+`: sparse prefill and paged decode consume quantized keys, BF16 weights, candidate visibility and DeepGEMM logits, then exact-selection machinery. There is no centered-radius metadata in the inspected interfaces.
- `sparse_attn_indexer.py:880–955`: producer path also emits candidate-block selection and tokenTop512. A token winner certificate alone cannot justify removing producer work required by blockTop2048. Initial adaptation is **consumer-only**.
- `sparse_indexer.py:44–46` and `sparse_mqa_indexer.py:165–207`: expanded candidate indices/end and schedule metadata are already reused by later consumer layers. Do not count these existing savings again.

First useful consumer: the native sparse-logits computation over the already-visible candidate domain. A useful certificate would avoid some actual key/head loads and arithmetic while retaining original selected token identities. The exact output still needs the original score/quantization and TopK contract for all surviving candidates.

### Unresolved correctness and cost gates

1. Summaries must have conservative rounding, valid cache generation/slot identity, tail-block update rules and graph-safe ownership. A centroid/radius computed before key quantization is not automatically a bound for stored keys. Quantized reference accumulation and BF16 output rounding require an outward numerical envelope; real arithmetic alone is insufficient.
2. The64-key geometry block used in byte arithmetic is a proposal, not the native candidate-block size. Bounds over a superset of visible keys remain conservative but may be looser; no excluded key may enter the actual candidate output. Seed threshold must come from at least512 eligible scores in the same visible/causal domain (unless the whole domain is smaller, in which case screening has no value). Overflow/uncertainty requires full-domain recovery. Native DSpark may have variable per-row context and verification count; no fixed5-row assumption.
3. Preserve signed weights, padding/sentinels, ties and exceptional numeric values. NaN/inf/overflow require explicitly conservative fallback until proven.
4. Summary writes, radius computation, allocation and bound evaluation add work. Radius may be loose; all32 head-bound evaluations can cost more than a highly optimized native score kernel at small candidate counts. No useful reject fraction is known.
5. Hypothetical BF16 centroid128 + FP32 radius uses260bytes/block before safe-rounding overhead/alignment; at an assumed64keys this is4.0625bytes/key, about5.97% of68byte MXFP4 index keys. This is **representation arithmetic**, not measured memory traffic or a chosen implementation format.

## PR triangulation and stopping decisions

- **FlashInfer#6224** dense fused metadata: opening body explicitly leaves paged schedules unchanged. Target decode consumes paged metadata, and consumer schedules are already reused across layers. A per-layer decode launch-saving forecast would be false. Read depth: opening body; no diff inspected. Stop direct decode port.
- **FlashInfer#6429** paged metadata→logits PDL and K-conditioned evict-first: relevant component question, but this round only inspected the opening description. Its different DeepGEMM baseline, cold-L2 chain timing, source trigger/wait lifetimes and target schedule reuse prohibit copying reported percentages. No claim this is absent from the target dependency. Keep as source question, not a generated hypothesis.
- **SGLang#32094** LiteTopK: FP8/H32D128 prefill donor, target's relevant consumer is MXFP4 and a compact visibility domain. Tie-tolerant1e-3 correctness is not exact token identity; candidate overflow needs a defined recovery. Existing M02/AT01 already cover selection fusion/certification. Stop direct transplant without saying no exact fused selector is possible.
- **SGLang#30277** Quest runtime: eager FA3 with separate metadata/graph/retrieval work and changed support. Retain its metadata ownership lesson, reject a turnkey native CED/indexer interpretation.

All four source IDs, fetched revisions and provenance edges are in the isolated corpus export. PR body benchmarks remain donor-reported, not reproduced.

## Executed CPU work and falsifiable next step

Command: repo `.venv/bin/python round47-kv-selection/geometry_contract.py` (absolute artifact path in actual invocation).

- Two direct-policy counterexamples above.
- Negative-weight counterexample: multiplying upper2 by weight-1 yields-2 while true maximum is0; signed lower-bound branch fixes it.
-500 finite synthetic signed-weight cases,32heads,8dimensions,16keys: no real-arithmetic bound violation within diagnostic tolerance. These are not500target workloads, not native arithmetic and not pruning-rate evidence.
- Exact-tie control documents why strict inequality is necessary.

Fastest **decision-changing** follow-up is a CPU replay on already-retained real indexer Q/K/weight/scale/visibility traces, if any exist. No such tensor trace was retrieved in this round; this is not an exhaustive archive search. The earlier bounded round10 exposure audit also found no compatible measured component exposure for its three investigated mechanisms, but that audit does not establish that no indexer trace exists anywhere. We did not manufacture exposure. If none are retained, leave deferred until a later authorized capture. Measure bound rejection and maintenance work proxies first, with the exact native reference rounding and quantized values; reject this option if almost no blocks can be safely eliminated. Another random geometry sweep would not establish usefulness.

## Future evaluation mapping — no GPU authorization

Existing Mooncake and agent75 request workloads remain service tests; retain identical target outputs, TTFT, long-output ITL, tail guards, throughput/goodput and failures. This refinement targets consumer indexer decode and prefill, but its benefit depends on actual candidate counts and safe rejection rate. Context length alone is not exposure.

Additional diagnostic instrumentation is justified because those two end-to-end evaluators cannot explain certificate efficacy: per-row candidate-domain size, seed cost, blocks safely rejected, full-domain fallbacks, summary update bytes/time, bound time and surviving-logit time. A future controlled native A/B must preserve exact output/token identities before measuring service impact. No target fraction or latency/ROI is estimated here.

## Tool usefulness and remaining limits

Online paper discovery worked and surfaced two new fulltexts. Exact retained-source lookup avoided redownloading existing DoSA/HPC-Ops/MonoMoE. Query2 mostly rediscovered prior work; we stopped instead of treating hits as new ideas. Compact recall helped prevent renaming AT01. PR subset search exposed source contradictions (paged route unchanged, metadata reuse) but did not inspect diffs. The rejected plan status and unsupported export command are genuine operator/API friction, not scientific progress. Source exports and command journals make the failed branches reviewable. No skill-quality improvement has been demonstrated by this single round.

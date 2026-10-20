# Comparing both H200 investigations with the B200 plan

**Recommendation:** start with Humming eligibility, FlashMLA plan sharing, actual-versus-padded drafting, and CPU DP synchronization. Keep small-row mHC as a low-load lane and candidate-only scoring as a long-context lane. The fresh run improves the evidence and adds useful mechanisms; it does not invalidate the earlier backlog or establish any speedup.

This comparison maps **all 66 original cards into 33 mechanism/qualification families**:26 earlier H200 cards, 17 fresh H200 cards and 23 B200 cards.23 families have a conditional inspection priority; six are inactive/different-path scopes and four are correctness gates. No original folder, card or verdict was overwritten. No inference, GPU benchmark, image build or deployment was performed for this comparison.

## 1. Identify the three investigations correctly

| Name here | Original run | Main strength | Practical limit |
|---|---|---|---|
| **B** | [B200 PR audit](../pr-evaluation-audit-001/REPORT.md) | Full5532-row triage, broad cache/scheduler/routing/correctness coverage and existing workload audit | B200 configured baseline; many SM100/backend and seq128 assumptions do not transfer to H200 |
| **A** | [Earlier H200 audit on Sofia](../h200-pr-evaluation-audit-001/REPORT.md) | Reassesses B200 mechanisms for live219 TP1/DP4/EP4, filters TP-only/Blackwell paths and preserves full ledger |73 refreshed primary snapshots/27 changed-file lists; targeted source review, not every implementation; several source memberships unresolved |
| **F** | [Fresh H200 research on 223](../h200-fresh-research-001/REPORT.md) | Broader independent discovery:108 selected primary snapshots/69 patches, cross-engine/literature evidence, implementation conflicts and model critique |17 cards,16 deferred and one inactive rejection; eight conditional diagnostic plans; none GPU-qualified |

The runs use overlapping public evidence and the same basic model/image. Agreement between their agents is **corroboration of an investigation lead**, not independent empirical replication. Do not add source-count totals as unique evidence without deduplicating IDs; do not average fresh critic scores with earlier engineering ranks.

Both H200 snapshots match eight H200s, two TP1/DP4/EP4 groups, API2, seq64, MBT16384, cap512, FP8 KV/block64, DSpark k5 and adaptive verification off. They concern different hosts:219 versus 223. Their serving checkout/router provenance differs. Same GPU and image do not make a cross-host A/B automatically controlled. See [evaluation reconciliation](EVALUATION_RECONCILIATION.md).

Read-only checks at **19:23 IST on 20 October 2026** found eight H200s on each host and HTTP200 on both serving ports of both hosts. This supersedes the older loading/readiness observation, not the frozen research evidence. The bounded log tail did not include Engram startup lines; shared-mode evidence remains the fresh223 startup snapshot, not a new attestation of219's resolved branch.

## 2. What changed after combining the evidence

### A. Fresh adds a useful narrow experiment: FlashMLA plan sharing

[#58818](https://github.com/vllm-project/vllm/pull/58818) shares planning state across compatible attention groups within one metadata-building pass. It attacks repeated planning, not attention arithmetic or small-head padding. It can therefore be relevant at TP1 with 64 heads.

Its vLLM source hunks apply to the captured installed code. First prove duplicate active planner work and live-field compatibility, then test changed lengths/masks and graph lifetimes. A matching shape is not enough. This is [C02](families/C02.md), ranked second because it offers a narrow, interpretable first investigation. Author H20 synthetic-acceptance results are not a H200 serving prediction.

### B. Humming stays first, but becomes a properly separated comparison

The actual baseline selects Marlin. Compare **Marlin → Humming grouped → Humming indexed**, all with matched BF16 activation semantics. Precision is another experiment, C13. This separates backend selection from indexed preference.

Fresh adds concrete schema counterevidence: installed Humming0.1.16 can reject advertised block-FP8 combinations or fall back to a different format. A closed upstream issue does not upgrade our package. [Issue60600](https://github.com/vllm-project/vllm/issues/60600). The broad #59488 patch also conflicts with this source revision, so use supported existing controls before adapting it.

A new review detail matters: logs contain **two expert geometries**, E384/top6/local96 and E128/top3/local32, both hidden5120/intermediate2304/clamp10. The latter is consistent with the drafter but role-tagged tracing must confirm it. A backend/precision change that propagates into both must qualify both; a target-only fixture is insufficient. [C01](families/C01.md).

### C. Several “easy cherry-picks” are actually ports

Fresh's disposable-source checks show:

| PR | Source hunks apply? | Meaning |
|---|---|---|
|58818 plan sharing | Yes | Promising narrow port; live compatibility and tests still required |
|61461 small-row mHC | Yes | Source integration appears small; eligible rows and numerical behavior untested |
|59204 SM90 DeepSelect | Yes, vLLM source scope only | Native build/dependencies were excluded; not a ready selector |
|58984 draft sizing | No | Adapt exact final behavior to installed helper/inheritance |
|61767 CPU metadata reduction | No | Resolve source/group/API differences |
|59488 Humming schema/selection | No | Prefer existing controls for the first comparison |
|62000 /62463 candidate scoring | No | Explicit source/backend/layout integration required |

A failed textual patch is not proof of a bad mechanism. A successful textual patch is not proof of a correct running implementation. [Saved patch checks](../h200-fresh-research-001/baseline/patch-application-checks.json).

### D. The private Engram allocation proposal is inactive

Fresh logs resolve shared DP Engram storage on both 223 replicas. Its H17 private-allocation candidate is correctly rejected **as scoped**. Earlier A:H10 was broader: it included private allocation, NUMA placement and lookup tuning. Remove the private arm for this shared baseline; preserve a separately scoped shared-placement investigation [C15](families/C15.md). Shared mode alone does not prove backing type, NUMA locality, translation cost or FABRIC/export support.

### E. Numerical counterevidence improves the prefill hypothesis

DeepGEMM452 replaces part of the contiguous MQA epilogue with `x+abs(x)` and compensates scales. Fresh's CPU example shows that doubling a large finite float can overflow before compensation. That refutes universal finite-input equivalence; it does not demonstrate a real model failure. Require an enforceable input/scale domain or fallback, then compare selected logits/tokens and quality. Paged decode is outside this change. [C12](families/C12.md).

## 3. Consolidated order and what each test would teach us

| Order | Family | First question | What a successful result means |
|---|---|---|---|
|1 | [C01 Humming](families/C01.md) | Can installed controls execute matched legal schemas for both expert geometries? | A specific static backend/GEMM arm beats Marlin under unchanged semantics |
|2 | [C02 plan sharing](families/C02.md) | Are compatible planner calls actually duplicated? | Removing redundant planning improves service without stale metadata |
|3 | [C03 real draft counts](families/C03.md) | Do padded target counts select larger draft work? | Less draft work yields useful service gain without changing rejection behavior |
|4 | [C04 CPU DP sync](families/C04.md) | Is transport cost exposed after separating rank arrival skew? | Faster metadata transport brings forward useful GPU work |
|5, low-load | [C05 small-row mHC](families/C05.md) | Do executed kernels land in the 1–8-row band? | Better low-load latency, not an assumed saturation-capacity gain |
|6 | [C06 prefix/draft fixes](families/C06.md) | Is there hit-dependent acceptance loss or target-hit veto? | A diagnosed cache defect is repaired with valid draft state |
|7 | [C07 scheduler work](families/C07.md) | Are null-head scans or repeated registrations on the CPU critical path? | CPU savings survive as useful server improvement |
|8 | [C08 selector/valid lengths](families/C08.md) | Is SM90 FP32 selector integration legal and padded selection work substantial? | Selector replacement and length-awareness show separately attributable value |
|9, long-context | [C09 candidate scoring](families/C09.md) | Does avoided dense work exceed gather/page overhead? | Long-context benefit survives C1/short-context countercontrols |
|10–12 | [Affinity](families/C10.md), [prefill coordination](families/C11.md), [MQA epilogue](families/C12.md) | Is the particular routing, interference or numerical path eligible? | Scoped gains without load imbalance, starvation or math regression |
|13–18 | Precision, fused mapping, shared Engram, scheduler budget, graph boundary, draft context | Does their additional eligibility gate pass? | A separately attributable improvement; no bundled changes |
|19–23 | Native FP4 fusion, DeepEP, mHC overlap, KV offload, matched SGLang | Is the larger integration justified by an exposed bottleneck? | New qualified backend/feature/engine evidence, followed by isolated attribution |

Full step-by-step explanations for every family are in [RANKING.md](RANKING.md): underlying problem → proposed solution → combined evidence → cheapest check → evaluation → stopping rule → B200 transfer. [CROSSWALK.csv](CROSSWALK.csv) maps every original ID, including multiple arms of a broad card. **A:H02 is draft padding; F:H02 is plan sharing. Always namespace IDs.** The crosswalk labels broad umbrella/related-family links separately from direct mechanism correspondence; it includes original global hypothesis IDs without merging live memory databases.

This is inspection priority, not predicted percentage benefit. For a pure saturated-throughput objective, demote low-exposure small-row mHC until its row histogram proves relevance. For interactive low-load latency, C05 can be one of the cheapest useful experiments. No popularity/novelty requirement is added.

## 4. What the B200 plan still contributes

Keep its stronger explicit coverage of prefix/draft interactions, scheduler bookkeeping, budget reservations, graph reachability, bounded drafter context, offload and semantic/lifecycle gates. Their absence from fresh's 17-card shortlist is not rejection.

Do not carry over these B200 conclusions:

- B200-specific FlashMLA pipelines, MegaMoE warmup/repacking and Blackwell-only Engram/mHC fusion need actual Hopper equivalents before any recommendation.
- TP1 has64 local heads and 2304-wide experts. TP4 small-head and padding remedies are different-topology designs, not current DP4 improvements.
- Seq128 graph/budget pressure does not describe seq64; target384/draft320 fit nominal cap512, though intermediate bucket reachability still needs inspection.
- GB200 host-memory behavior does not predict H200 Engram NUMA/page behavior.
- B200 timing, capacity and $36/hour cost assumptions are not H200 measurements or prices.

The qualification families Q01–Q04 retain sampling, index/graph/lifetime, lifecycle and tool/quality checks. Relevant Hopper WGMMA lifetime checks are not the same as B200-only mega_mhc barrier fixes. They are prerequisites for affected paths, not performance rankings.

## 5. Reconcile evaluation before executing

There are real differences, not merely wording:

- Earlier H200 starts capacity calibration low; fresh retains c256/384/512. Use low-to-high discovery, retain feasible historical points, then freeze identical A/B confirmation loads.
- Earlier proposed3% capacity/5% latency; fresh uses a provisional2% pilot threshold. Select and freeze one useful-effect rule per test; never choose it after seeing results.
- Fresh identifies AIPerf0.11 installed versus 0.13 documentation. Verify an isolated client environment instead of assuming every catalog feature works.
- Use server-token TPOT, not SSE-chunk gaps; speculative decoding may emit multiple tokens in one chunk.
- Five paired600s Mooncake measurements already require100 minutes, excluding overhead. The 20-minute diagnostic budget is not a confirmation budget.
- Match host/router/client and use within-host pairs or balanced crossovers; a one-shot219-versus 223 comparison is confounded.

See [EVALUATION_RECONCILIATION.md](EVALUATION_RECONCILIATION.md) for exact six-stage verdicts, minimal extra tests, cost denominators and persistence rules.

## 6. Files, provenance and Git

Originals remain separate folders. The comparison lives only in `h200-cross-audit-comparison-001`, with input hashes, a complete crosswalk and an independent technical review. No SQLite database was merged or copied over another memory graph.

Git synchronization is delegated and documented in [GIT_SYNC.md](GIT_SYNC.md). It uses isolated worktrees, explicit paths, ordinary push/fast-forward pull and checks of pre-existing dirty file hashes. Independent research content is preserved; SQLite backups and Python cache are kept off Git. The uncommitted evaluator/code work on 223 and unrelated Sofia work remain untouched.

## Evidence and verification

- [Input hashes](input-manifest.json), [mapping coverage](coverage.json), [machine-readable comparison](comparison.json).
- [Independent technical review](reviews/fresh-feasibility.md), including dual MoE geometry and per-card caveats.
- [Current read-only host snapshots](evidence/) supplement the frozen originals; they do not measure throughput.
- Source quote/schema/GPU test claims in original reports remain their historical claims. This comparison validates mapping/link integrity and Git preservation; it does not rerun those original model loops or GPU correctness tests.

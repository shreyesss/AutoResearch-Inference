# Decision — five new mechanisms; one-idea shortfall

Requested **six source-research ideas**. Five distinct conditional mechanisms survived; **shortfall: one**. Existing activations/unchanged ports are useful comparators below and do not fill the quota. No improvement is measured and no experiment was launched. [Brief](brief.md) · [sources](sources.md) · [self-review](review.md) · [matched experiment contract](notes/experiment-contract.md).

The strongest next research screen is **H04's exposed metadata cost versus simple fusion**; H01 is the smaller scheduler prototype if its precise alignment-blocking pattern occurs. **No candidate is currently ready to promise a correct implementation and matched serving result overnight.** H01 is the only plausible single-evening prototype (estimated4–8h) after its incidence gate; the other source implementations are day-scale. A cheap relevance screen is available tonight, but its setup estimate is not measured GPU duration. The other mechanisms need prerequisites or appreciably more engineering. Ranking combines relevance, falsifiability and total cost, separately from source novelty.

| Rank/card | New behavior and intended c32 effect | Evidence / decisive unknown | Cheapest isolated test → matched point | Cost and eligibility |
|---|---|---|---|---|
|1 [H04 persistent GDN descriptors](hypotheses/H04.md)|Retain unchanged state mappings across decode steps; potential TPOT/output-rate gain, possible invalidation overhead.|Exact image rebuilds descriptors; ordinary decode is active. Unknown exposed critical-path time after async and simple fusion.|Short c32 profile plus stock/fused/reuse metadata sequence; stop if fusion removes headroom. Then same trial10 c32 three-arm comparison.|Screen setup0.5–1day; prototype1–3days; capture/start separately; ~6min first three-arm point wall time+prep. **Cheap screen eligible; implementation conditional.**|
|2 [H01 alignment-fit bypass](hypotheses/H01.md)|Use leftover token budget for fitting tails after alignment-zero head; potential TTFT/capacity gain, TPOT/long-head regression possible.|Exact waiting-loop break; seq64/c32 does not prove waiting+stranded-budget+fitting-follower coincidence.|CPU branch/progress cases and short original c32 incidence diagnostic. Then parent/static2048/candidate c32.|Prototype estimate4–8h, not a readiness promise; Python source helper insertion needed. ~6min point wall time+starts/prep. **CPU test eligible; serving only if incidence.**|
|3 [H03 selected interior checkpoints](hypotheses/H03.md)|Materialize demanded sub-page GDN+conv+attention checkpoint without whole-model split; potential prefill/TTFT saving, export/memory cost.|Image tail-only boundary gap and Marconi/PR evidence; warmup+fine matching may already cover useful prefixes.|CPU exact token/checkpoint join against fine matching. If incremental reuse exists, isolated continuation oracle. Then fine-match parent/exporter c32.|Gate0.5–1day; prototype3–7days/integration1–2weeks; JIT/build separate. **CPU gate eligible; no overnight implementation.**|
|4 [H02 committed-prefix followers](hypotheses/H02.md)|Suppress duplicate in-flight prefill using producer-completion/generation dependency; possible compute saving, deliberate wait risk.|SGLang heuristic exists, event-safe hybrid adaptation new. Frozen64-prefix warmup may eliminate opportunity.|CPU residual-prefix join, then simultaneous sibling-miss incidence. Parent/heuristic/candidate only if useful.|Gate1–3h; implementation1–3days; normal startup; pair~4min+prep. **CPU gate eligible; low exact-workload confidence.**|
|5 [H05 ragged GDN MTP verification](hypotheses/H05.md)|Per-request verify budgets plus coherent device hybrid commit; possible TPOT/output gain, backend/draft/state overhead.|Real metadata/FA2 gap; safe MTP and useful c32 heterogeneity unproven.|Safe fixed-MTP acceptance/physical-bucket cost diagnostic, optimistic bound, component state/graph test. Same-stack fixed/ragged c32 plus original anchor.|4–8engineering days or more; backend/MRV2/capture startup substantial. **Diagnostic conditional on MTP safety; no overnight implementation.**|

Times are estimates. Historical c32 point was~117–120s, excluding server setup and cache preparation; startup/compile/drain are additional and must be timed. A single matched point is provisional. Original BF16 model, workload bodies, forced lengths, warmup, streaming/API, concurrency and request-level scorer remain the route to comparable p90TTFT/p90TPOT/output-rate points. No cold, low-concurrency or operation-only result substitutes. Repeats/order/drift, neighboring loads and a distinct final split follow only promising results.

## Useful upgrades and controls — excluded from five

| Existing solution | Role |
|---|---|
|Fine-prefix matching activation|Strongest H03 control; may remove all justification for new snapshots. Previous batch H01 remains a cheap deployment experiment after checkpoint/quality gate.|
|Fused align metadata gather, PR38020/SGLang-style refresh|Strongest H04 control and potentially simpler useful upgrade. Closed PR requires compatibility qualification; unchanged port is not source novelty.|
|Safe fixed native MTP, uniform adaptive depth, eligible runner/attention backend|H05 prerequisites/controls; prior activation is not re-counted.|
|Static2048 prefill cap and ordinary shortest-residual ordering|H01 practical controls; prior pressure-prefill policy remains historical, not forced into this round.|
|Regular all-mode checkpoint export / FlashInfer prefill / fused ordinary GDN / FP8|Existing ports/activations remain alternative deployment investigations; precision change needs its own quality dimension.|

## Exploration and why a sixth did not survive

| Direction | Outcome |
|---|---|
|Queue fit/fairness|H01 new narrow legal-work bypass; generic cache affinity discarded after correct-async null result; output-length pairing has irrelevant capacity assumptions and negative real-EOS evidence.|
|In-flight prefix reuse / stateless compute dedup|H02 completion-aware adaptation retained conditionally. Hybrid RadixMLP costs more and shares the unproven cold-duplicate opportunity; not padded into another slot.|
|Hybrid state materialization|H03 selective export retained; raw fine-match/all-mode activation/port excluded. No generic eviction claim with zero recorded c32 preemptions.|
|Host/GPU metadata|H04 reuse/invalidation retained. Raw gather fusion excluded as unchanged solution.|
|Speculative verification|H05 coherent ragged integration retained conditionally. Native MTP, batch-only adaptiveK, ReplaySSM/TreeWY ports excluded as repeats/prerequisites.|
|Multi-step execution|Two-step decode lease discarded: no exposed-gap evidence beyond existing async and MRV2, while admission/cancellation/graph work is substantial.|
|Allocator/precision/communication|Allocator prototype evidence does not establish runtime value here; precision flags repeat prior batch; dense TP1 has no MoE inter-GPU communication opportunity.|

Review was lead **self-review** with delegated research, not independent approval. Recommendations to coordinator: preserve source-novelty and exact-workload-value as separate judgments; save null activation/comparator outcomes, and require current-image traces before escalating a helper operation into a serving claim. No skills, prior batches, serving code or dependencies were changed by this worker; no GPU was launched. Human selection remains the next stage.

# Checkpoint 10 — finish useful diagnostics and expose their conclusions

**Guided yield remains34 reviewed cards:2 accepted bounded CPU investigations,24 deferred,7 rejected,1 duplicate. Zero implementation/service qualifications.** This checkpoint refines existing A01/S01/M01 identities; it creates no new hypothesis. The four accepted records in the entire database include two older, differently scoped R1/TreeSpark design investigations. They are not four implementation-ready wins.

## Current work priority

| Existing idea | New evidence | Current action |
|---|---|---|
| S01 tokenizer path |74 named fixtures/70 distinct strings match loaded0.23.2 using frozen native0.22.2;14 runtime-option counterexamples |Finite CPU compatibility phase complete. Park further optimization until real input-path exposure and relevance to the service objective are established. |
| M01 MoE tile choice |52 retained local metadata/manifest files checked; no eligible per-layer/rank physical receive histogram |Park quantitative ROI/tactic work. Logical pre-remap IDs and cumulative totals do not substitute for physical per-step data. |
| A01 Engram WKV lookahead |Shared-stream FIFO can place early WKV behind the later layer's lookup; moving it earlier delays that lookup |Keep deferred. Need exact backend ownership, legal overlap window and exposed cost. |

These are work-priority recommendations attached to preserved historical selections, not claims that any idea is scientifically disproven. The [accepted-priority audit](priority/PRIORITIZATION.md) provides stop/reopen conditions. The [M01 inventory](priority/M01_RETAINED_INVENTORY.md) establishes bounded local coverage only, not absence from every remote S3 object.

## S01 finite cross-version bridge

[Round27](round27/REPORT.md) reuses bounded prior inputs and compares complete IDs against the actual locally loaded Transformers5.16.1/tokenizers0.23.2 target. Both raw and effective serialized artifacts are exercised. Per artifact, full-input execution consists of **12 Gigatoken calls and62 internal HF fallbacks**; segmentation executes **118 ordinary native calls with zero segment fallbacks**. Those denominators prevent counting HF fallback as native proof. The 14 split_special_tokens=true mismatches remain an unsupported semantic boundary.

[Independent review](round27/INDEPENDENT_REVIEW.md) verifies fixtures, binary/source identities and route counts. No timing was repeated or upgraded, no admission guard changed, and finite equality does not establish complete runtime compatibility. Input work primarily concerns TTFT/frontend cost; long-output ITL coupling remains unproven.

## A01 dependency refinement

[Round26](round26/REPORT.md) establishes that WKV inputs are n-gram lookup rows and fixed weights; hidden state enters the later gate. There is a genuine dependency opportunity, but the schedule matters. Two lookups are queued on one shared stream before decoder execution. A late append of WKV1 waits behind lookup14; insertion before lookup14 delays its readiness. A separate projection stream removes that FIFO dependency but can contend with attention and needs a resource fence before persistent MoE.

There are **two logical6144→25600 projections**, at layers1 and14—not a40-layer or nominal-draft-depth multiplier. The symbolic scheduler uses invented dimensionless durations and demonstrates both a possible saving and a contention regression. It measures no runtime gain or actual scratch alias. Independent source review confirms the bounded claims. A01 retains its original historical baseline; no live deployment attestation is inferred.

## Memory tool fix validated on real retained states

The previous hypothesis dossier omitted linked investigation/evidence-bundle nodes. For real S01 states it returned72–96k characters yet omitted later conclusions. The additive fix exposes `linked_research` first, retaining original conclusions, false qualification flags and explicit artifact counts. Default lists show four pointers; `--include-artifacts` / MCP `include_artifacts=true` returns all references.

[Independent replay](dossier/INDEPENDENT_REVIEW.md) shows the missing nodes now appear. Existing dossier fields and selection status are unchanged; no hypothesis-ledger writes occur. Full-reference mode reconstructs original linked records. Default added payload is approximately4.6–5.1k characters versus50–70k for complete linked details. This is a read projection, not source execution, fresh hash/availability verification or a global response budget.

Verification: **287 tests and25 subtests passed**, bootstrap dry-run, skill validator and diff checks passed. The earlier compact-recall change was pushed as `5e52ed2fc1f2e4ff480e7563d9118614f8943e92`; this checkpoint's dossier change is a subsequent commit.

## Persistence and one import failure

- Published research lineage advanced to `532cb45daeada1624c98219d0307f7ef1bc189a5cf3dece66af4b9d08bf02dde` at02:57:34UTC. Its hash-verified local manifest includes15–18 cohort records and the117-entry historical text-retention index. It predates19/20/22 and21/23/24/25. No S3 download or VM restore was performed here.
- Additional15–18 text retention completed:48 mappings added/hash-verified; historical events unchanged. Its revised explicit-reviewed request is recorded. Publication of these later mappings is not yet claimed.
- Canonical19/20/22 import completed:173 artifacts,11 exact MF19 typed records and7 scoped inconclusive CPU records. MF19 remains deferred; original S01 node/baseline/accepted selection unchanged. Local mutation is not a new recovery snapshot.
- Canonical21/23/24/25 imported its science records but failed a final bookkeeping assertion: the starting hypothesis count was read before waiting on the writer lock, so an unrelated preceding import's new hypothesis entered the delta. Frozen packet/archive hashes and the exact deferred OH21 identity survived. There is no completion receipt yet. A separately reviewed resume importer moves the count baseline under the lock and reuses immutable IDs. A real two-process test reproduced the failure and verified corrected accounting; replaying a copy of actual partial state added zero hypotheses/events/tests. Canonical retry has been launched and is awaiting completion. The failure journal is preserved; no rollback or successful-completion claim is made.
- Retention26/27 and priority notes passed an isolated restore, but root preflight then detected that the selected OPERATIONS.md had changed after packet generation. Canonical apply was stopped; the failed freeze is preserved and the packet is being regenerated and revalidated. No canonical or S3 coverage is claimed yet.

GPU experiments/model launches/serving changes/training remain zero. Tool-triggered model calls are zero in these probes; host-agent reasoning cost is unmetered.

# Round113 — activation-aware dispatch over existing expert replicas

## Outcome

**One distinct conditional component retained; zero new formal hypothesis cards and zero implementation-qualified proposals.** Replace uniform-like hash selection among already resident physical copies of a logical expert with regime-aware dispatch shares. Concentrate cold experts when opening extra copies costs more than the balance it provides; permit splitting hot experts. This changes invocation assignment, not the neural router's logical top-k or expert weights.

The source gap is concrete. Its current exposure is not: source defaults disable EPLB and allocate zero redundant experts, while the effective planned deployment map is unknown. With one copy of every logical expert, this selector has no choice and removes no work. The component remains eligible if existing copies are established. Enabling new replicas is a separate intervention with extra weights/HBM, initialization, placement and remapping controls; it is not silently included here.

Source/AST and existing records only. No GPU, native imports, model, build, serving change, weight update or canonical/cloud mutation. No arithmetic/service forecast is assigned.

## Adaptive discovery and overlap

The isolated ledger copy was recalled in two complete compact pages:154 records with a stable inventory. These are records, not154 distinct mechanisms. Relevant cards and standalone rounds32/52/56/100/102 were inspected. CRAFT variable layer capacity, CAP coactivation placement, H02 commit timing, M01 tactic choice, RD01 memory-domain placement, M05 routing across independent EP groups, RM61 request ownership, A52/D52 readiness/deduplication, and existing prefetch all concern different or already covered levers.

One OpenAlex query, `mixture of experts inference replica locality scheduling`, dated August1 through October22, returned12 identities. All abstracts were inspected. TEMPO2608.13057 had been abstract-screened in round56, not read in full. Its selected fulltext was obtained through `investigate` with two-call budget, no citation expansion and no automatic repository reads. The request was unversioned; the returned body explicitly declares **arXiv2608.13057v2,14August2026**. Retained hashes identify exactly this body, not an assertion of latest version.

The query began with local-copy dispatch. Reading changed the question: the paper's same-node pairing is unhelpful as a distinct inter-node lever for our single-node EP4, while activation-aware shares are independent of that topology extension. No second paper query was necessary.

Canonical read-only FTS covered the exact title/identity and replica-selection phrases. The title produced unrelated observability “Tempo” hits; these are not implementation evidence. Two selected PR opening records were copied into the isolated state and inspected through actual `pr-search`; this replay searches the selected subset, not the whole corpus anew. Source absence below is established from pinned code, not PR bodies.

## Paper component and limitations

[TEMPO v2](https://arxiv.org/html/2608.13057v2) models per-rank MoE time using activated physical copies, token work and communication. Its solver initially assigns a cold expert's invocations as a whole, then rebalances and allows partial splits when worthwhile. The deployed implementation uses previous-window counts and published probability tables, rather than the theoretical current-batch optimum. Sections4.1–4.4,5.5–5.12 and AppendicesC/D were inspected; no claim of reading every figure or reproducing results.

Useful components are separable:

- A dispatch objective that prices activating another copy, instead of minimizing only token-count imbalance.
- A table-based selector with frozen valid physical support, keeping a slow planner outside the graph.
- Uniform-table and frozen-table controls that distinguish useful policy from dispatch/host overhead.

Binding contrary evidence:

- The donor cost fit is pipeline-specific. Its fixed128-row padding assumptions cannot replace this target's dynamically aligned live16-row MMA extent.
- Its DeepSeek-V3 serving result shows approximately2–3% degradation, indistinguishable from the no-op control. Its Qwen result is not a target gain.
- Previous-window counts can miss the current routing mix. A modeled optimal split is not an exact realized split under probabilistic assignment.
- The theorem's full-replication assumptions do not automatically cover a sparse physical map.
- The artifact link and hardware labels are anonymized in the retained version. Linked DeepEP/EPLB repositories are dependencies, not proof of released TEMPO source. We did not fetch or claim a donor implementation.
- The paper's claim that a racing share-table copy remains valid relies on unchanged valid replica support. It is not a target guarantee across an EPLB weight/map commit.

## Exact target path and missing part

The source baseline is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883` plus `DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`, planned frozen Flash1017 on B200 TP1/DP4/EP4. This is source applicability, not live dispatch attestation.

`DeepGEMMMegaMoE.forward` applies `eplb_map_to_physical_and_record` only when its layer's logical-to-physical map is installed. The [pinned mapper](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/model_executor/layers/fused_moe/router/base_router.py) computes:

```text
token_idx = offs // num_active_experts
hashed = (token_idx * 2654435769) & 0xFFFFFFFF
replica_idx = hashed % replica_count
physical_id = logical_to_physical[logical_expert, replica_idx]
```

Its interface has no source-rank or nonuniform-share input. Mapping and optional count recording are already fused into one kernel. Padding-aware recording already exists. Therefore “fuse mapping/counting” is a duplicate, whereas changing the selection policy is absent in this inspected branch. The current hash is not newly identified as a bug: vLLM#40810's opening record describes repairing replica-selection bias in another baseline, and the exact target already uses Knuth hashing. That PR's B200 metrics are not our measurements.

The native scheduler reads physical per-expert receive counts and creates `ceil(count/BLOCK_M)` task blocks; absent physical experts have no blocks. Thus changing which existing copies receive work can change active-expert/task distribution without changing the logical router. This is a source mechanism, not proof of lower physical HBM/NVLink bytes or service time. Source-local assignment can trade communication against rank skew. Numerical effects from different grouped shapes/tactics still need target admission despite identical logical expert weights.

## Minimal adapter contract, not a patch

For eligible resident copies only, attach validated per-layer shares to the existing fused mapper. Keep logical top-k positions and routing weights, invalid/padded IDs, count accounting, per-ubatch shape, destination physical IDs and shared-expert path intact. Define assignment randomness/determinism explicitly; do not consume a model-sampling RNG stream or silently inherit a donor seed policy. Preserve each replica's complete packed weights/scales.

The share table must belong to the same physical-map generation as the loaded weights. Pinned `_move_to_workspace` moves buffered weights, commits the physical/logical/count maps, then acknowledges the result. A table with nonzero entries for an old map can select a different logical expert after a commit. The donor's torn-update argument for a fixed support set does not resolve this. A safe generation-bound publication/fallback is required; no race is asserted to exist in current code.

SGLang#45363's opening record describes an independently useful warning: narrowing dispatch candidates must not narrow loader enumeration and leave duplicate slots unwritten. We read the body, not its diff, and do not claim the same bug in vLLM. The proposed selector must leave loader ownership unchanged and verify every selectable slot actually holds the expected expert.

Do not transplant the paper's background process and counters wholesale. The target already has load recording and map lifecycles; first establish whether their available window/count semantics can supply the needed observations without new host synchronization or collective work. A future fixed-table control can test selector overhead before any adaptive service runs.

## Cheapest discriminator and bounded evaluation

The first useful check is a retained effective EPLB configuration plus layer physical maps/replica counts and corresponding loaded-weight identity. It needs no new GPU experiment if these artifacts exist. If no logical expert has more than one physical copy, close this existing-replica arm immediately. Source default zero is not evidence of the effective setting. This round does not expand into another deployment-wide inventory search.

If copies exist, the next informative replay needs actual per-step logical assignments/source rank, existing physical map and actual backend/task geometry. Per-expert totals alone do not establish source locality. No synthetic skew distribution here estimates useful exposure. The paper's fit/thresholds are not substituted for target measurements.

A later authorized comparison would separate current hash mapping, uniform-share mapper with the same copies, and a frozen nonuniform policy before adding delayed adaptation. Hold placement/weights/tactic constant for this first question. If additional replicas are required, account for their memory and compare against the best compatible static/EPLB placement at equal capacity; do not credit their effect entirely to selection.

Required correctness checks include exact logical coverage, no dropped/duplicated token-expert invocation, valid map generation, padding, deterministic assignment policy, shared slots, and target numerical/output admission across changed grouping. Current source/AST checks certify none of the compiled behavior.

Existing Mooncake and agent-p75 can measure long-output ITL, tails and goodput. They do not currently expose the needed replica/task/communication attribution. Add that attribution to a future matched comparison, not a new synthetic benchmark family. Reject promotion if the baseline/uniform control ties or wins, extra scheduling or data-path overhead erases saved exposed work, or correctness/quality guards fail. No donor1% tolerance or headline gain becomes a target success threshold.

## Accounting and stop

One dated query,12 abstract identities, one selected primary fulltext, four bounded PR FTS lookups, two selected PR opening bodies, six pinned target/dependency files, ten exact quotes. One parked conditional selection component; duplicate fused-counting and inactive inter-node pairing components closed separately. No formal new card, no accepted implementation, no target timings or ROI.

The source-only AST check confirms the existing hash expression/interface; the single-replica no-choice result is a mathematical implication, not a kernel experiment. Four vLLM files match the retained exact archive byte for byte; two DeepGEMM files match prior pinned hashes. Source export was explicitly committed and reopened read-only:21documents,22revisions,140edges. Failed initialization with deferred snapshots, the consequent uninitialized operations, wrong-directory/source lookup attempts, truncated console reads and an initial archive-member assumption are retained as limits/errors. Retried successful reads are the evidence used. No provider failure was hidden and no extra paper query was issued.

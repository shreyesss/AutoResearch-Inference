# Independent review — round113 resident replica selection

## Verdict

Retain the distinct conditional selector as parked source evidence. No blocker to that disposition; no current exposure, implementation qualification or service improvement is established. The first useful discriminator is the effective per-layer resident physical map, replica counts and corresponding loaded-weight identity. A map with one copy per logical expert gives this selector no choice. Neither the `enable_eplb` flag alone nor its source default settles that question.

I verified all 43 frozen author artifacts, 22 exact revision fingerprints, ten quoted anchors, four vLLM archive byte equalities and two DeepGEMM prior-copy equalities. `checks.json` records source hashes and line anchors. This review reads the specific mapper, call gate, map commit, task geometry and paper passages below; it is not an independent replication of the entire discovery search or donor evaluation. No model, GPU, native kernel, backend import or canonical mutation was used.

## Target delta and eligibility

At `base_router.py:18–93`, the selector uses token index, Knuth hashing and modulo replica count. The interface supplies neither nonuniform shares nor source rank. Load counting and padding masking are already fused. `deep_gemm_mega_moe.py:767–784` enters that mapper when the logical-to-physical map is installed and uses the current microbatch's count boundary. Thus a validated share selector is absent in this branch; adding another count/mapping launch is not the claimed opportunity.

Source defaults (`parallel.py:77,206`) are zero redundant experts and EPLB disabled. They are not effective deployment evidence. Conversely, EPLB enabled does not establish more than one usable copy. The useful evidence must identify actual valid slots and complete packed weights/scales, not merely configured capacity or a future placement plan. Adding replicas is a separate memory/placement arm.

## Ownership and reusable donor details

`eplb_state.py:1426–1452` moves buffered expert weights, commits maps/counts, then releases the pending result. A proposed share table must select the same loaded experts under the same map generation. Static tables over frozen support can avoid introducing the donor's adaptive host machinery. Adaptive updates need a publication/stream/capture contract; this is not evidence of an existing target race.

TEMPO §4.4 expressly handles torn all-zero rows with uniform fallback over valid replicas; it does not simply divide by a potentially zero sum. Appendix D also names an EPLB-rebalance hook reinitializing solvers, and §5.8 reports correct generations. These are selectively useful design details. The report should not be read as claiming the donor ignores rebalancing. They remain descriptions without inspected donor code and do not establish compatibility with this target's weight/map commit order. Fixed-support torn-update validity alone is insufficient across changing support.

The existing counter path does not by itself prove availability of per-step, per-source-rank observations or bounded-window statistics. Aggregate counts cannot establish locality, and logical repeated loads do not determine NVLink bytes. A uniform-table control is necessary to separate selector data-path cost from policy value.

## Work and numerical limits

`target-scheduler.cuh:128,278,324–338` uses physical expert counts, per-expert task blocks and 16-aligned live rows. Concentrating tokens across fewer copies can change the sum of per-copy task counts and 16-rounded extents. This does not contradict M01's fixed-per-expert-count invariant when only BLOCK_M changes. It also does not establish a gain: maximum-rank skew, task/weight staging, communication and occupancy can dominate. Shared-expert work is not eliminated by this selector.

Keeping logical expert IDs, weights and routing positions fixed is a mathematical equivalence premise, not a guarantee of bitwise equality after changed grouping or tactics. A future test needs the declared numerical/quality contract. This is neither an automatic quality failure nor permission to claim exact native arithmetic. Preserve invalid/padded IDs, all token-expert occurrences, shared slots and assignment RNG separation.

## Prior identity and contrary evidence

This is distinct from:

- M01 `hypothesis:7deeaba77bd1290ce3850134faa175d3b7b38a877efb126357a4feab8364baf0`: tactics for existing expert work.
- H02 `hypothesis:dfbc7da6a19c00ded8f00ffd18d62bcf4ed519bea4f05921ba73506c4d416bb9` and `hypothesis:2a01cc66f6436d32c60ac5afb9d37b0062d97765c214a220456ef187d1387cbe`: placement commit policy/timing. Their generation ownership interacts with this selector.
- M05 `hypothesis:16afdd0252fff1fd053fa91c480ae3cf24576b4684176969ac1a898f356231d9`: request assignment across independent EP groups.

TEMPO §5.10's DSv3 result is negative by approximately 2–3% and indistinguishable from its no-op control. That is substantive opposing evidence, not a proof of target futility. Its Qwen results and 128-row cost model do not supply B200/EP4 target ROI. The reported Qwen split between uniform-path and solver gains reinforces separate controls. Hardware and artifact anonymization limit portability claims.

## Stop and reopen

Keep parked until retained effective maps establish selectable resident replicas. If none exist, close the existing-replica arm without silently adding weights. If eligible, require source-rank/assignment exposure and a compatible cost/quality contract before implementation priority. Do not start another synthetic skew campaign merely to populate evidence.

Apply the report's comparison rule carefully: a sufficiently resolved baseline/uniform tie or win can reject promotion for a tested policy. Noisy or inadequate measurements remain inconclusive, not an equivalence or performance-refutation result. No card/status transition or forecast follows from this review.

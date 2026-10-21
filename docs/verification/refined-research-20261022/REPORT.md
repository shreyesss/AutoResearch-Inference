# Refined research integration — 22 October 2026 (India)

## Real-source use, rather than a claimed serving win

Question: when can a zero-speculation step skip draft work, and what transfers to the historical H200 DP4/EP4 DSpark-k5 deployment?

A bounded investigation read the retained [vLLM PR #53426](https://github.com/vllm-project/vllm/pull/53426), twelve retained discussion comments, and cached versioned full text of [TreeSpark, arXiv:2609.22098v1](https://arxiv.org/html/2609.22098v1). Four logical HTTP cache misses were used; no model or GPU call was made. Hydration and citation expansion each recorded a RuntimeError within that budget: this is **partial retrieval**, not complete diff/review/citation coverage. The full text was available and relevant passages were inspected; this is not a reproduced paper experiment.

### Engineering outcome

1. **Reject a direct flag transfer.** The PR describes skipping draft KV synchronization on K=0 steps, but explicitly refuses DSpark because its proposer implementation does not contain the skip. Its performance examples concern other model/drafter combinations on RTX 5090 hardware. They do not establish a target H200/B200 benefit.
2. **Preserve the useful mechanism.** TreeSpark describes reducing verification-tree size with load when extra draft coverage becomes too expensive. This motivates inspecting our accepted progress and exposed draft/verification time by load; it does not establish that our fixed-k5 deployment can accept the same controller.
3. **Retain a falsifiable diagnostic hypothesis.** A calibrated, supported speculation budget may reduce exposed decode cost versus historical fixed k5. First pin the deployed DSpark code and determine which budgets and state transitions are supported. Stop if source inspection disproves the proposed path. Then use actual target timing and committed-token progress to bound benefit, including acceptance loss and resume cost.
4. **Use existing workloads first.** Agent-75 remains the long-output service test; Mooncake provides the retained trace mix. Verify their current commands/data and whether the replay exercises low-high-low load during the same requests. Add a small transition probe/counters only if that stimulus or observability is absent. Profile separately from scored runs. Keep TTFT, ITL tails, E2E, correctness, errors and output-token counts as explicit guards.
5. **Disposition: deferred.** No current image/model/source pins or target trace were available for this demonstration. Numerical target gain is null, the screen is insufficient, and the evaluation plan is blocked. Reopen after source applicability and target timing/acceptance evidence are supplied. This is a useful diagnostic direction, not an accepted implementation or measured speedup.

### Retained trace

- Investigation: `20261021T204928-849480c3`
- Typed-flow records: `research/records/refined-real-transfer-20261022/` under the external state root.
- Hypothesis: `hypothesis:7a7523f77054a0d42b2cdee16cd566c532e88898fa620cb337865930dcb2830c`
- Atomic claims: `claim:68c15f93d49081aabf1ef6ae46b58b07b17f78d512d38bdf6a3cd60f15b1cab8`, `claim:7412b3b045e66f5a9419123ac60217a48d44d9101271443fc787cd52e0098085`
- Screen: `screening:725f0176bec4edd28162b6ea2571033ecd1beeacc6bd8810863d46369869784b`
- Plan: `eval_plan:2d322a549564ac41de5827ada8e04699014b223ecc1fd737991907fc2cd489cf`
- Decision: `decision:f955591bb8f98880ba2b821c643bd1e8d3fddddfacb4256fe7b2f5c6f8295e7b`

These records were created while developing the changes, before their final Git commit. Source revisions and evidence hashes are retained independently. The historical hardware description is not a refreshed live inventory.

## Acceptance evidence

Verification: **200 research tests passed**, including a snapshot/restore of the typed claim/screen/decision trace. All six repository skills passed skill validation; bootstrap `--dry-run --mcp` passed.

- Research test suite includes exact-quote/source-revision retention, immutable claims, target-prediction separation, source-change alerts, contradictory evidence, cold-start decisions, plan pins and evaluator gaps, unknown ROI, novelty default, optional-model packet linking and qualification rejection after insufficient screening.
- MCP tests include in-process tool calls and a real stdio subprocess handshake. Network-disabled mode rejects live discovery; responses include structured content. The host chat client has not been configured to use MCP.
- `scripts/demo_research_flow.py` completed the full offline fixture trace in a fresh state directory. Its deliberately fictional author result remained separate from a null target prediction and an untested, deferred hypothesis.
- No GPU benchmark or serving change was performed. Provider billing totals are unsupported, not asserted zero. This demonstration made no LLM call.

The [implementation guide](../../RESEARCH_TO_IMPLEMENTATION.md) describes operating commands and remaining boundaries. Git/VM delivery receipts are recorded separately after publication.

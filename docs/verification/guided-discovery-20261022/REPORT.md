# Guided discovery — checkpoint 1, 22 October 2026

**11 interventions examined; 2 selected for bounded CPU/source diagnosis; zero measured serving improvements. The discovery goal remains active.** No GPU experiment, model launch, serving-code patch or container change occurred. CPU probes, paper discovery, source reads and research-tool changes ran.

## What survives and why

| Priority / scope | Candidate | Concrete gap in inspected code | Current decision |
|---|---|---|---|
| Decode/ITL research | **M01: distribution-informed MegaMoE tiles** | Default DeepGEMM chooses tile M from expected tokens/expert, not actual per-layer physical distribution. Same count can conceal different tiling/padding tradeoffs. | Advance source/CPU diagnostic. First consider a fixed layer/batch-size table; dynamic selection must beat that control including overhead. No profitable tile identified. |
| Frontend/TTFT research | **S01: exact rendered-prefix tokenization repair** | Custom V4.1 Python wrapper renders and encodes the entire prompt; existing HF property caching is different. | Advance exact-artifact compatibility diagnostic. TokTier does not certify our artifact; unchanged installation will not deliver this acceleration. No repair implementation validated. |
| Correctness unresolved | **M03: bypass unnecessary candidate-block ranking** | Producer still ranks blocks when their count fits its budget. | Revise/defer. Unconditional enumeration changes sentinel membership and can change later-layer selection. |

These are useful next investigations, not accepted performance wins. The typed `accepted` status for S01/M01 is explicitly limited to a reproducible CPU/source diagnostic plan. The remaining implementation, exactness, workload-exposure and value questions are preserved.

### M01 — what the paper contributes, what we can actually reuse

[DA-MoE](https://arxiv.org/html/2607.23099v1) motivates choosing kernels using routed expert distributions. Our adaptation keeps MegaMoE, expert IDs/weights, quantization, placement and SM allocation fixed. It investigates tile configuration, rather than importing the paper's different backend or headline gains.

Pinned vLLM `c4557869393db4d75c483d92edd02a5125500883` defaults to DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`. The CPU arithmetic probe constructs two feasible histograms with the same total work count: the heuristic chooses the same tile, while tile counts and padding differ. **That establishes missing information, not which tile is faster.** No physical target histogram or exposed-time estimate is available.

The second source pass improved feasibility: common ring/scale-buffer capacity already spans candidate tiles. But the scale-packing getter and kernel launch derive their configurations separately. A valid override must reach both and derive their coupled parameters consistently. Selected static checks reject two entries in the global tile list; passing the others is not compilation or correctness proof. See [the parameter-flow audit](M01_PARAMETER_FLOW.md).

This ordinary MegaMoE path is Blackwell-specific; this is **not an H200 recommendation**. Before future timing, tie the actual dependency binary to the source pin, inventory legal configurations and seek already-retained physical receive histograms. Do not collect new GPU traces under current authorization. Compare against the best fixed layer/batch-size tactic before considering a dynamic selector.

### S01 — partial reuse rather than accepting or rejecting a whole paper

[TokTier](https://arxiv.org/html/2607.29678v1) and [October Delta Tokenizer](https://arxiv.org/html/2610.19801v1) provide CPU stable-boundary repair ideas. They share authors/evidence; they are not independent replications. We retain the CPU repair component and omit optional GPU tokenization. Reuse must happen after the exact renderer and tolerate changed suffixes.

The exact Flash-1017 tokenizer differs from the certified anchor in nine added-token entries. CPU checks show all 18 old/new literals distinguish the two artifacts, and naive independent prefix/suffix encoding fails 254 of 300 deliberately adversarial split cases. The pinned default thinking renderer also rewrites earlier suffixes. These results invalidate shortcuts; **they do not validate TokTier repair or represent a production error rate**.

Standard Bitlane sweep source uses chat endpoints. Existing `multiturn.yaml` can supply growing-history stimulus; fixed-prefix agent-p75 alone does not establish session reuse. Reuse existing loads, add only CPU differential cases for token/renderer exactness, and resolve session identity and the actual reference loader. Possible value is frontend encode/queue time and TTFT, not a direct decode ITL reduction.

## Adversarial outcomes that prevented wrong experiments

- **HPC-Ops sampled Top-K:** author K512 path is not sampled; our pinned tree already contains sampled selection, while candidate-producer K2048 is a separate path. A generic replacement claim was rejected.
- **M03 candidate bypass:** an independent CPU example shows an all-`-inf` producer block omitted by fallback becomes included by enumeration and changes a later consumer's top choice. Conversely, an ordering objection was withdrawn after finding that the sparse consumer sorts candidates. Keep both the counterexample and resolved objection.
- **HiSparse flag:** pinned layout explicitly rejects DeepSeek V4. [October Adaptive DHiSparse](https://arxiv.org/html/2610.13708v1) improves the evidence for a future integration, but its long-context/high-concurrency regime does not establish value for our 8K control. Existing flag activation remains invalid.
- **One-hit cache demotion:** prior ghost-admission hypothesis already covers the central intervention. Recent negative evidence is attached as a refinement, not counted as a new proposal.
- **Second-round Herschel synchronization idea:** the initially inspected legacy runner was wrong for DSpark. The actual V2 path already passes target DP state into drafting and avoids that repeated synchronization. Residual first-target metadata preplanning needs a different dependency/overlap argument. See [the source review](HERSCHEL_DP_REVIEW.md).

## Yield and what was really measured

| Checkpoint-1 outcome | Interventions |
|---|---:|
| Advance to bounded diagnostic | 2 |
| Duplicate of prior work | 1 |
| Reject direct application | 3 |
| Defer | 4 |
| Revise/defer | 1 |
| **Total** | **11** |
| **Measured service improvements** | **0** |

Diagnostic selection yield is **2/11 (18.2%)**, not a performance success rate. Source variants and related papers do not inflate the denominator. The first cohort used five online paper-search invocations through our tools, with retained abstracts/receipts, followed by selected full texts, canonical PR searches and pinned source reads. Later queries belong to round two. Full texts and implementation links are evidence to inspect, not automatic independent corroboration.

Six CPU checks are retained in [cpu-checks/](cpu-checks/): tokenizer artifact comparison, shortcut counterexamples, renderer transitions, synthetic expert-work accounting, candidate-membership counterexample and static tile constraints. They have different scopes; none executes a proposed GPU optimization. The reviewer directly audited contested/shortlisted mechanisms, not every discarded full text. This is an actual-use case study, not a controlled proof that skills improve discovery in general.

## Research-tool improvements verified in this run

1. **Explicit deep-read repository selection:** `investigate --repository owner/project` replaces heuristic README selection and retains the discovered alternatives. It avoids spending a bounded budget on an incidental cited dependency.
2. **Pinned files available directly from CLI and MCP:** repeatable `--code-source` JSON or MCP `code_sources`, with exact commit/path validation. Explicit selections exceeding their budget fail rather than silently disappear.
3. **Actionable uninitialized-state errors:** both interfaces now tell the agent to initialize the selected state directory. Provider exception text remains suppressed to avoid disclosing credential-bearing URLs.
4. **Real tool checks:** one exact candidate-block source read used one HTTP cache miss; its repeated read succeeded with a zero-call budget and zero misses. Explicit HPC-Ops selection read that repository with four misses, no fallback to the cited dependency. These checks prove tool behavior, not paper authorship or scientific validity.

Verification: **248 research tests passed**, bootstrap dry-run passed, PR research skill validator passed. No serving/GPU suite was run. See [tool-verification.json](tool-verification.json) and [the workflow](../../CHAT_RESEARCH_WORKFLOW.md).

## Baseline, memory and continuation

Source reference and exact Flash-1017 model revision are pinned in [BRIEF.md](BRIEF.md). The two-DEP4 B200 layout is a task-plan reference, not an attestation of the currently running image. Older unsuffixed Flash/H200 results are not merged into this baseline.

Frozen proposals, decisions, source hashes and probe results are retained. [persistent-ids.json](persistent-ids.json) maps all 11 cards; [proposals.json](proposals.json) and [decisions.json](decisions.json) preserve the typed inputs. Source/decision refinements append to memory rather than erasing the earlier failed hypothesis. Canonical import and S3 publication have separate receipts; a local proposal file alone does not establish either. See `STATE.md` for the verified checkpoint state.

The next round is active: continue paper-led discovery, check the actual dispatched path early, and follow the surviving MoE parameter-flow question. Do not generate another copy of an already implemented synchronization optimization. Reports: [scheduling](SCHEDULING.md), [MoE/attention](MOE.md), [delegated review](REVIEW.md).

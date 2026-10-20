# H200 research continuation 001

Start with the [report](REPORT.md): a deeper PR/issue scan, history-aware
hypothesis regeneration, cheap applicability checks and a resumable next state.
No serving/GPU experiment was launched; both remaining full attempts are intact.

| Read this | For |
| --- | --- |
| [Intervention plans](INTERVENTIONS.md) | C24 coupled target/draft cost investigation, C25 conditional sampler fusion and C26 router eligibility hold; cost caps and test/stop rules |
| [Filtering audit](FILTERING_AUDIT.md) | Earlier rules/caps, 8,908 local identities, 2,202 fetched/refreshed openings, unmatched audit and unfinished feeds |
| [DeepInfer review](DEEPINFER.md) | Released mechanisms versus proposed Hopper/host/Engram/correctness changes; 95 PR openings, 14 deeper reviews |
| [Cheap checks](ELIGIBILITY_CHECKS.md) | Synthetic AV cost counterexample, BF16 checkpoint metadata and sampler watermark/source gates |
| [Current dispositions](dispositions.json) | One current decision per mechanism, immutable hypothesis IDs and unresolved conditions |
| [Final eligibility review](eligibility-followup/decision.md) | Reassessment using the new evidence; research eligibility is not a service result |
| [Research validation](RESEARCH_VALIDATION.md) | What 58 software tests and this run establish, and the limits of AI-research claims |
| [System upgrade plan](SYSTEM_UPGRADE_PLAN.md) | Implemented continuation/selection fixes and the next retrieval/calibration evaluation |
| [Validation receipt](validation.json) | Source/archive hashes, quotes, software tests and continuation integrity |

The original [two-round generation](hypotheses/decision.md) preserves six
proposal instances and all critiques, including the rejected citation and the
old runner's duplicate-parent shortlist. The separate follow-up reviews one
latest revision per mechanism. Use the dispositions above for current work.

The new rubric is in both [generation guidance](../../docs/HYPOTHESIS_ROI.md) and
the [agent workflow](../../docs/AGENT_WORKFLOW.md). This run's
[frozen rubric](policy-current/rubric.json) is retained alongside the
[input correction](policy-input-correction.md); initial inputs were not erased.

## Resume

Use [handoff-003](handoff-003/continuation.json), containing all 36 current family
states and explicit next actions. Earlier handoffs remain intact and detect the
later register changes as stale. Follow the [continuation CLI guide](../../docs/CONTINUATION.md):
when results/evidence change, prepare a new output with `previous` pointing to
this handoff; do not overwrite it or restart from an empty hypothesis list.

The isolated local databases are `ideation/data/corpus.sqlite` and
`ideation/data/hypotheses.sqlite` in this worktree. They are ignored by Git;
retained source snapshots, model outputs, memory IDs and the
[cheap-test outcome links](cheap-check-memory.json) provide the reviewable record.
[Nine exported proposal records](memory-records.json) preserve their reviews,
lineage and scoped outcomes. [Provider usage counters](research-model-usage.json)
record nine completed research-model calls; no monetary cost is inferred.
Original corpus and serving environments were not replaced.

`scripts/collect.py resume` advances each unfinished opening feed by up to two
pages and saves the previous receipt. `collect` reuses existing receipts;
`scan` scans the local corpus without network calls. These commands update this
working acquisition state: archive a final receipt set before starting a later
collection period. Counts describe the saved interval, not perpetual completeness.

To reproduce the CPU probe with a Python environment containing NumPy:

```bash
python scripts/av_cost_probe.py --output /tmp/av-cost-new-receipt.json
```

The script defaults to the retained installed source, executes only its
extracted budget method, imports no Torch/CUDA and refuses to overwrite a receipt.
The [reproduction result](av-cost-reproduction.json) matches the original on every
non-path field. Its costs are synthetic, not measured milliseconds. From the
original workspace, `python scripts/validate_run.py` verifies the retained run;
continuation path checks intentionally require the referenced current inputs.

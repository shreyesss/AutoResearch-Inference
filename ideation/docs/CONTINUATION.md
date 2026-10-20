# Continue research from evidence and outcomes

The continuation tool joins the complete Markdown family register with the
existing hypothesis database. It preserves old decisions, records explicit holds
and next actions, and freezes the source artifacts used to decide what to do next.
It launches no experiments.

From `ideation/`, using the research Python environment:

```bash
python -m ideation tool hypothesis.continue --args '{"brief":"runs/my-run/brief.json","output":"runs/my-run/handoff-001","register":"hypotheses","state":"runs/my-run/state.json","artifacts":["runs/my-run/policy/rubric.json"]}'
python -m ideation tool hypothesis.continuation_check --args '{"path":"runs/my-run/handoff-001/continuation.json"}'
python -m ideation tool hypothesis.run --args '{"brief":"runs/my-run/brief.json","packet":"runs/my-run/evidence/packet.json","policy":"runs/my-run/policy/rubric.json","continuation":"runs/my-run/handoff-001/continuation.json","output":"runs/my-run/hypotheses-001","rounds":1}'
```

`state.json` contains `decisions` and `next_actions`. Each decision names a real
`family_id`, an action (`hold`, `await_result`, `investigate`, or `reopen`), a
`reason`, and optional local `artifacts` and `reopen_when`. Explicit reopening
also requires `new_evidence` and `scope_delta`. These are reviewable assertions;
the tool does not decide whether they scientifically justify reopening.

The handoff freezes every linked family card, the register, brief, referenced
prior decisions and explicit artifacts with SHA-256 hashes. It also retains
bounded database recall separately. Family labels such as C24 are distinct from
immutable database hypothesis IDs; the generator must not invent parent IDs.
The generator and critic receive every family's indexed state plus the explicit
decisions and next actions. Full card snapshots remain available for detailed
inspection; compact context is not a claim to include every historical artifact.

Before generation and after each critique, the runner checks that the frozen
inputs still match the current files. Changed experiment results cause a stale
handoff error rather than publishing an assessment under obsolete evidence.
Generated proposals remain in memory if a later stage fails. Historical accepted
ideas remain accepted under their historical policies, never silently upgraded
to experimentally validated outcomes.

When evidence changes, prepare a **new output directory**, passing
`previous:"runs/my-run/handoff-001/continuation.json"`. The next handoff records
added, changed and removed input paths. Use a new hypothesis output directory
and the existing `revisit` interface where appropriate. Old handoffs and failed
runs remain immutable. A new rubric alone does not invalidate an unfavorable
service screen or authorize a repeat.

The [H200 continuation run](../runs/h200-continuation-001/README.md) exercises this
workflow. Its acquisition script also records full per-repository continuation
URLs and supports an explicit bounded `resume` pass, preserving prior receipts.
The topic ledger retains unmatched sources; source acquisition, semantic review,
pilot readiness and service readiness are separate counts and decisions.

Apply the [ROI rubric](HYPOTHESIS_ROI.md) at both generation and pilot selection.
Validate source claims, applicability, measurement adequacy and correctness
before allocating an expensive run. Software checks and synthetic CPU probes
can demonstrate that the research process discriminates between cases; only
matched service experiments can establish optimization value.

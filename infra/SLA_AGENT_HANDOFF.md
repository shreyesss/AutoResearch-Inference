# v3 agent-controlled serving search handoff

The approved research policy is `configs/sla-policy-v3.json`. The active v3
study record is `configs/sla-study-v3.template.json`. The B0-only campaign at
`configs/campaign-sla-b0-v3.json` produces matched development CellResults; it
has a zero proposal budget and cannot start serving search. The stopped v2
Optuna campaign is not the v3 SLA search.

## Required evidence before the first agent proposal

1. Freeze and qualify both 240-request development windows, including their
   class sidecars and disjoint arrivals.
2. Run the separate B0 campaign's matched evaluator cells and place their
   `cell-result.json` project-relative paths in the study's
   `adaptive_development.baseline_cell_paths`.
3. Run the class-aware SLA profiler on B0 using the approved policy. For each
   B0 profile to expose to the agent, add an entry to
   `baseline_adaptive_run_paths`: `{ "source_path": "<project-relative path to
   sla-profile-points.json>", "source_sha256": "<file SHA-256>" }`. Do not use
   sealed-test paths. The profile must contain at least one qualified
   four-class assessment. Every sampled rate and invalid point remains in the
   source file.
4. Run the study readiness audit. It reports input readiness only; neither a
   passing audit nor an adaptive best point confirms capacity.

## New serving campaign

Create a distinct versioned campaign after the evidence above is pinned. It
must include `sla_study_path: "configs/sla-study-v3.template.json"`, a distinct
campaign ID and output directory, the pinned runtime and model, and a qualified
registry/protocol covering its development screens. Run its qualification
command before `iar search --backend real`. The CLI requires the Codex proposer
for any campaign with `sla_study_path`; Optuna or mock cannot silently replace
the agent. The proposer fails before producing a proposal if the study has no
hash-checked approved policy or class-assessed B0 adaptive profile.

The proposer gets a read-only `sla-study-index.json`, approved policy, all B0
profile points, and bounded copies of native request exports. It may research
and propose serving settings only. The controller owns server deployment,
traffic, evaluation, promotion and sealed-test access. A separate evaluator
integration and independent confirmation protocol are still needed to score
candidate SLA capacity; the current search controller's fast screen is only a
regression gate. Do not label its result an SLA frontier or confirmed capacity.

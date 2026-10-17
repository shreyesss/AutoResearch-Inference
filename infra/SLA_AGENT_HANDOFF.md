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

`configs/campaign-sla-serving-v3.json` is the separate bounded Codex search
campaign. It points at the activated study artifact, uses only the 36-request
screen and the two development windows in its registry, and pins four agent
proposals with at most two development finalists. Run it only after inspecting
the B0 SLA profile:

```bash
.venv/bin/iar sla-search --backend real --campaign configs/campaign-sla-serving-v3.json
```

The controller checks the active study, approved policy hash, both matched B0
CellResults and their raw records, and at least one class-assessed B0 profile
before starting a server. It locks the active study SHA in the ledger and
rejects changes during search. The CLI requires real Codex; Optuna and mock
cannot silently replace the agent. The search batch refuses a second run after
proposals exist, so inspect the ledger before launching another campaign.

Each proposal gets a fresh 36-request screen. The screen rejects incomplete or
non-normal cells and predeclared, conspicuous regressions: throughput below
half of B0, or aggregate p90 TTFT/TPOT over twice B0. This is a coarse cost
guard, not a confidence statement. At most two nondominated screen candidates
then receive both independent 240-request development evaluations. Their
native request exports are scored against the approved four-class policy and
paired with the matched B0 cells. Only candidates observed feasible on both
development windows enter the class-aware adaptive rate profiler. All screen,
development and profile outputs go to the append-only ledger and run folders.
Sealed-test scenarios are absent from this campaign registry.

The proposer gets a read-only `sla-study-index.json`, approved policy, two
matched B0 windows, all B0 profile points, and bounded copies of native
request exports. It may research and propose serving settings only. The
controller owns server deployment, traffic, evaluation and promotion. The
adaptive points remain development observations. A later frozen-rate repeat
and sealed-test protocol are required before claiming an SLA-capacity frontier.

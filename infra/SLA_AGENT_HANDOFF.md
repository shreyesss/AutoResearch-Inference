# v3 agent-controlled serving search handoff

**Historical v3b design.** Its candidate watcher was retired before any
proposal. The revised `gpt-6-sol` campaign, cost gates, commands and current
status are in `infra/V3C_RUN.md` and `configs/campaign-sla-serving-v3c.json`.
Do not use the v3b commands below for the current run.

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

`configs/campaign-sla-serving-v3b.json` is the separate bounded Codex search
campaign. It points at the activated study artifact, uses only the 36-request
screen and the two development windows in its registry, and pins four agent
proposals. Every proposal passing the gross-regression screen gets both
development windows. Run it only after inspecting
the B0 SLA profile:

The earlier `qwen38-27b-sla-serving-v3` artifact directory contains only a
GPU-free preflight lock from before the sequential feedback change. The v3b
campaign uses a new ID and artifact directory so that lock remains auditable.

The two frozen windows use independent development seeds 1042 and 1043. Both
are development data. Neither is the sealed test set.

```bash
docker exec deploy-controller-1 iar sla-search --backend real --campaign configs/campaign-sla-serving-v3b.json
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
guard, not a confidence statement. All screen candidates that pass the guard
then receive both independent 240-request development evaluations. The
36-request Pareto view is diagnostic and cannot eliminate a candidate. Their
native request exports are scored against the approved four-class policy and
paired with the matched B0 cells. Only candidates observed feasible on both
development windows enter the class-aware adaptive rate profiler. All screen,
development and profile outputs go to the append-only ledger and run folders.
Sealed-test scenarios are absent from this campaign registry.

The proposer gets a read-only `sla-study-index.json`, approved policy, two
matched B0 windows, all B0 profile points, and bounded copies of native
request exports. Search is sequential: each candidate that passes the 36-request
screen gets both development cells and, if observed feasible in both, an adaptive
profile **before** the next proposal. The next proposal sees those development
cells, per-class assessments and the candidate profile points. It may research
and propose serving settings only. The controller owns server deployment,
traffic, evaluation and promotion. The adaptive points remain development
observations. A later frozen-rate repeat and sealed-test protocol are required
before claiming an SLA-capacity frontier.

## One-shot overnight candidate watcher

`infra/run_v3_candidate_search.py wait-run` waits for the separate
`iar-v3-sla-profiler` tmux to exit with a successful B0 profile receipt. It
verifies the approved policy, hash-pinned profile with at least one valid
four-class point, both matched B0 cells, and idle GPU. It then runs the
GPU-free `sla-search --check` preflight before the serving search. The watcher
stops on an invalid or missing upstream receipt, failed preflight, or existing
proposals. It never reruns automatically. The search can consume many hours;
it ends at development observations and does not run sealed test.

Launch only one watcher session:

```bash
tmux new-session -d -s iar-v3-candidate-search 'cd /home/ubuntu/shreyas/skunk-work && PYTHONPATH=src .venv/bin/python infra/run_v3_candidate_search.py wait-run --wait-timeout-s 43200 > .artifacts/v3-independent-capture/candidate-search-watcher.log 2>&1'
```

Inspect progress and terminal status:

```bash
tmux has-session -t iar-v3-candidate-search
cat .artifacts/v3-independent-capture/candidate-search-status.json
tail -n 80 .artifacts/v3-independent-capture/candidate-search-watcher.log
tail -n 80 .artifacts/v3-independent-capture/candidate-search-console.log
```

The status JSON records stages, exit code, and errors. `candidate-search-console.log`
and `candidate-search-console.stderr.log` are live logs; the campaign ledger
and run folders retain individual proposals and evaluations. If status is
`blocked`, inspect the named gate and artifacts. A restart requires a separate
manual review of the ledger and status file; the watcher refuses to overwrite
either a previous status or existing proposals. For a GPU-free readiness check
after the profiler finishes:

```bash
PYTHONPATH=src .venv/bin/python infra/run_v3_candidate_search.py check
docker exec deploy-controller-1 iar sla-search --backend real --campaign configs/campaign-sla-serving-v3b.json --check
```

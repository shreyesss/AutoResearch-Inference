# Development input qualification overnight

**Scope:** two development input windows only. This launcher does not run an
adaptive rate search, a serving configuration search, or sealed test. Passing
this checkpoint does not establish SLA capacity or a matched evaluator B0 cell.

The existing `iar-v3-dev-1042` tmux job owns the first source capture and
stops its `iar-b0` container when it exits. Start the overnight waiter once:

```bash
cd /home/ubuntu/shreyas/skunk-work
tmux new-session -d -s iar-v3-dev-overnight \
  'PYTHONPATH=src .venv/bin/python infra/run_v3_development_overnight.py > .artifacts/v3-independent-capture/development-overnight.log 2>&1'
```

It waits for the first job to finish and **starts no GPU work while that job is
running**. It refuses an existing checkpoint, overlapping B0 container, or
another GPU compute process. The sequence is:

1. Require first capture exit code 0, complete 240/240 HTTP 200 accounting,
   the predeclared source hash/seed, a frozen manifest and exact request-class
   sidecar with at least 30 of each class. Stop on any failed check.
2. Restart pinned B0, replay **only 1042** with fixed request bodies and
   arrivals, and require complete replay validation. Stop on failure.
3. Capture and freeze the independent 1043 development window. Apply the same
   accounting, hash and class-quota checks before replay.
4. Replay 1043, promote both manifests only after both replays pass, then run
   the cross-window content, schedule, seed, class and hash audit. Stop B0.

Inspect progress without changing the run:

```bash
cat .artifacts/v3-independent-capture/development-overnight-checkpoint.json
tail -50 .artifacts/v3-independent-capture/development-overnight.log
tmux ls
```

Each source and replay has its own console log under
`.artifacts/v3-independent-capture/`. The stage replay report is
`.artifacts/v2-independent-validation/development_replication/validation-report.json`.
The final input audit, if passed, is
`.artifacts/v3-independent-capture/development-input-audit.json`.
`status: blocked` in the checkpoint means **no later stage was authorized**.
Do not delete or rerun a partially completed checkpoint automatically; inspect
the named log and determine whether a versioned restart is needed.

The next gate after `development_inputs_qualified` is to register the two
validated windows in a new campaign and run actual evaluator B0 `CellResult`
measurements with matched schedules. Independent input replay happens on B0,
but its validation report is **not** a `CellResult` and cannot fill
`baseline_cell_paths` in the SLA study. A class-aware adaptive profile and
independent finalist confirmation remain subsequent gates. No sealed-test
request body or result is staged for the proposer by this workflow.

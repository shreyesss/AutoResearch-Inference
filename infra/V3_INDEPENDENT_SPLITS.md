# Independent v3 split plan for the v2 evaluator

This is a **prepared protocol**, not an SLA finding. It leaves the active v2
campaign and overnight search unchanged.

`configs/evaluation-splits-v3.json` predeclares two development windows and two
sealed test windows from the same OPS synthetic mixed recipe as the 36-request
screen. Every window uses a different content/Poisson-arrival seed and contains
240 requests at the 0.1 requests/s reference rate. Each stage therefore has
480 planned requests. The input audit requires at least 30 realized requests in
each chat, agent, code and document class **within each window**. The source
weights make this plausible, but do not guarantee it. If a seed draw
misses that condition, the stage blocks and the split plan needs a versioned
revision; it is never silently relaxed.

Generate the four exact capture commands without running a benchmark:

```bash
PYTHONPATH=src .venv/bin/python infra/plan-v3-independent-splits.py
```

The default capture directory is `.artifacts/v3-independent-capture`.

Each command uses the existing `run-ops-b0.py` wrapper with a distinct seed.
It requires a pinned healthy `iar-b0` server. Captures produce raw AIPerf
requests and summaries. Freeze each capture using its printed command. The
frozen card and manifest initially have `readiness: prepared`.
For mixed workloads, freezing also writes a hashed `*.classes.json` sidecar
mapping each exact `session_id` to `chat`, `agent`, `code`, or `document`. This
metadata stays outside the native AIPerf JSONL. The registry checks that the
sidecar hash, request IDs, output caps, and per-class counts match the frozen
payload, card, and manifest.

Validate a stage by independently replaying its fixed requests and arrivals on
B0, then promote it only after request bodies, output caps, completion count,
and credit/dispatch timing match:

```bash
PYTHONPATH=src .venv/bin/python infra/validate-ops4-frozen.py replay --split-plan configs/evaluation-splits-v3.json --split-stage development_replication
PYTHONPATH=src .venv/bin/python infra/validate-ops4-frozen.py promote --split-plan configs/evaluation-splits-v3.json --split-stage development_replication
```

Repeat for `sealed_test` only when the finalist and decision rule have been
locked. The proposer container receives staged development evidence only;
sealed inputs and outcomes are not in its staged research context. The split
auditor (`evaluation.split_v2.audit_frozen_splits`) checks source hash, seeds,
distinct complete request bodies and schedules, class counts and validated
manifest hashes. Audit `development_replication` first; it can pass while the
sealed test remains uncaptured. The sealed-test audit includes development
assets so cross-split content reuse cannot pass. `audit_confirmation_pairs` then requires valid, normal,
complete matched B0/candidate cells for every window before passing data to
SLA scoring. It makes no SLA claim itself.

At 0.1 requests/s, each 240-request window takes roughly 40 minutes to
dispatch, plus startup, response drain, and an independent replay. This is a
finalist gate, not an iteration-time screen. AIPerf adaptive rate search and
the numeric application SLO still need to be fixed before capacity can be
declared. The 0.1 requests/s windows only confirm the reference-load behavior.

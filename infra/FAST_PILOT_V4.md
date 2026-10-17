# Fast serving pilot (v4)

## Why this run exists

The v3c gate would repeat two 240-request baseline runs and then search the
load curve before the first serving proposal. At 0.1 requests/s, dispatching
those two windows alone takes at least 80 minutes. The completed 1042 capture
and exact-input replay already show provisional B0 latency misses at that load.
The incomplete 1043 capture is preserved as partial evidence and is not used
as a qualified independent window.

## Active exploratory protocol

- **Agent:** isolated Codex `gpt-6-sol`, medium reasoning, live web access,
  at most eight proposal attempts. It reads the skill, domain, provisional B0
  report, native AIPerf summaries, per-request metrics, and prior screens.
- **Search domain:** the seven typed v3c serving controls in
  `configs/search-domain-v3c.json`. The model, hardware, workload and SLA
  research targets stay fixed.
- **Screen:** one fresh B0 and one fresh server run per valid proposal, each
  using the frozen 36-request OPS mixed reference at 0.4 offered requests/s.
  The request bodies and Poisson seed match. Actual arrivals are stochastic,
  so this is a diagnostic comparison rather than an exact arrival replay.
- **Artifacts:** `.artifacts/fast-pilot-v4/run-status.json`, `console.log`,
  `ledger.sqlite`, proposal files, every CellResult and native AIPerf export,
  `all-screen-points.csv`, the provisional plot, and a hash-pinned shortlist.
- **Interpretation:** 36 requests cannot establish per-class p90, p99, SLA
  capacity, or a robust Pareto frontier. The screen rejects obvious failures
  and identifies configurations worth longer independent comparisons. The
  approved p90 TTFT/TPOT limits remain research targets, not product SLOs.

After the pilot, a separate gate repeats B0 and up to two finalists on the
same **144-request development subset** of the frozen 1042 input: 54 chat and
30 each of agent, code and document. The 30-request floor follows the approved
per-class p90 policy. It is a same-source development comparison, so the p90
estimates and operator plot remain provisional. The full 240-request 1042
source is **not** a held-out test after this subset is used.

An independent 240-request test input is still required for a declared
finalist. The existing v3 sealed-test plan has two 240-request windows at 0.1
requests/s and is too slow for this pilot; it has not been run. Until a faster
versioned test protocol is qualified, this pilot and the 144-request gate do
not establish SLA capacity or independent validation.

## Inspect or check

```bash
PYTHONPATH=src .venv/bin/python infra/run_fast_pilot_v4.py check
tmux has-session -t iar-v4-fast-pilot
cat .artifacts/fast-pilot-v4/run-status.json
tail -40 .artifacts/fast-pilot-v4/console.log
```

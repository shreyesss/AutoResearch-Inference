# Fast pilot v4: latency curves and observed Pareto points

Regenerate with `MPLCONFIGDIR=/tmp/iar-plot-mpl .venv/bin/python infra/plot_fast_pilot_v4.py`.
The script reads immutable completed artifacts under `.artifacts/fast-pilot-v4/`,
checks all nine three-rate trials, and publishes the CSV, JSON, and SVG files
here. PNG versions are also in `.artifacts/fast-pilot-v4/analysis/`.

## Plots

- [TTFT p50/p90/p99 load curves](operator-ttft-p50-p90-p99.svg)
- [TPOT p50/p90/p99 load curves](operator-tpot-p50-p90-p99.svg)
- [Per-class p90 TTFT and TPOT curves](operator-class-p90-ttft-tpot.svg)
- [All eight proposals plus B0 at the single 36-request load](screen-all-configs-p50-p90-p99.svg)
- [Three-rate observed Pareto plot](operator-pareto-p90.svg)
- [Single-load observed Pareto plot](screen-pareto-p90.svg)
- [All three-rate quantiles and frontier flags](operator-pareto-p90.csv)
- [All single-load quantiles and frontier flags](screen-pareto-p90.csv)
- [Pareto definition and exact selected points](pareto-summary.json)

## Interpretation

The mathematical Pareto calculation maximizes measured output tokens/s and
minimizes measured **p90 TTFT** and **p90 TPOT**. It uses point estimates only;
p50 and p99 are plotted as diagnostics. At the 0.4 configured requests/s
three-rate point, B0 dominates both tested candidates on all three objectives.
At 0.8, B0 has the highest output throughput and lowest p90 TTFT. The other
two have slightly lower p90 TPOT in that sample, so they remain on the
*rate-matched* three-objective frontier; both are globally dominated by B0's
0.4 point. At 0.2, the three configurations differ by roughly 0.06 output
tokens/s, and exact Pareto membership is driven by differences too small to
interpret as optimization.

Only B0, batch-token budget 4096, and GPU memory utilization 0.85 received
three-rate measurements. The other six proposals have one 36-request screen
point each and therefore have no measured load curve. Each three-rate point
has 32 requests (eight per class); each screen point has 36 requests. The
percentiles, especially p99 and per-class p90, are descriptive. There are no
repeated windows, adaptive load search, independent test, or confirmed SLA
capacity in this result.

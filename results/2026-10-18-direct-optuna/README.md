# Direct Optuna study

[Live report](index.html) · [All points](points.csv) · [Per-class metrics](class-points.csv)

[Search analysis](ANALYSIS.md) · [p90 TTFT–TPOT frontier](ttft-tpot-pareto.svg) · [p50/p90/p99 TTFT–TPOT](ttft-tpot-percentiles.svg)

[Side-by-side development and held-out comparison](comparison.html)

[Study manifest](study-manifest.json) · [Workload hashes](workload-card.json) · [Model hashes](model-manifest.json)

Source: `.artifacts/optuna-direct-v1/`. Native GuideLLM exports and exact commands are preserved. Calibration uses 8 requests at concurrency 1 and 40 at other points; search uses 120 requests per point. Prefix warmup is separate and excluded; all measured requests complete or invalidate the point. Compare candidates with search/trial_0, the matched B0. A star denotes three-objective point-estimate Pareto membership at the common anchor, not proof of a repeatable improvement. Class target passes are observations, not statistically confirmed SLO attainment.

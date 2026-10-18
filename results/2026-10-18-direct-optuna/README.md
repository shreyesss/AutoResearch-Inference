# Direct Optuna study

[Report](index.html) · [All points](points.csv) · [Per-class metrics](class-points.csv)

Search configurations evaluated: 25. Completed held-out points: 15. Held-out campaign finished: True.

[Protocol](../../infra/DIRECT_OPTUNA_RUN.md) · [Replication criteria](../../docs/REPLICATION.md) · [Raw evidence and logs](evidence/README.md)

[Held-out operating curves](heldout-operating-curves.svg) · [Held-out Pareto](heldout-pareto.svg)

[Search analysis](ANALYSIS.md) · [p90 TTFT–TPOT frontier](ttft-tpot-pareto.svg) · [p50/p90/p99 TTFT–TPOT](ttft-tpot-percentiles.svg)

[Side-by-side development and held-out comparison](comparison.html)

[Study manifest](study-manifest.json) · [Workload hashes](workload-card.json) · [Model hashes](model-manifest.json)

Source: `.artifacts/optuna-direct-v1/`, also preserved in the committed evidence archive. Native GuideLLM exports and exact commands are preserved. Calibration uses 8 requests at concurrency 1 and 40 at other points; search uses 120 requests per point. Prefix warmup is separate and excluded; all measured requests complete or invalidate the point. Compare development candidates with search/trial_0; compare held-out candidates with confirmation/trial_0 and trial_4. Confirmation trials 1/2/3 correspond to original search trials 9/10/24. A star denotes three-objective point-estimate Pareto membership at the common anchor, not proof of a repeatable improvement. Class target passes are observations, not statistically confirmed SLO attainment.

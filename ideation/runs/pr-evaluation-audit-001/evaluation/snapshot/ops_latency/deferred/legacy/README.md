# Deferred broad latency campaign

This directory preserves the original, unrun LAT-01 through LAT-12 campaign.
It is excluded from the active 48-hour topology-selection flow.

Use these scripts only after an explicit plan update:

```bash
bash ops_latency/deferred/legacy/run_all_legacy.sh --plan
bash ops_latency/deferred/legacy/run_all_legacy.sh --only LAT-08
```

Results still use the isolated latency-campaign result root and retain the
same report/S3 delivery behavior. The active campaign is defined only by
`ops_latency/campaign.yaml` under `experiments`; these legacy rows live under
`deferred_experiments`.

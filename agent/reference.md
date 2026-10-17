# Serving research reference

## Workspace map

- `../context.json`: active campaign, domain, B0 settings, recent cells, frontier, qualification and remaining budget.
- `../research-index.json`: paths and prior attempt snapshots.
- `../measurements-index.json`: staged run files with checksums and explicit size omissions.
- `../evaluation-index.json`, when present: gate, configuration, matched B0, evidence grade, validity and raw-file links. Its `adaptive_studies` list contains every visible B0/finalist sampled load trial, including invalid points, with configured/realized rates, counts, metrics and source SHA-256. Matching offline SLA assessment files appear in each study's `sla_assessments`; they identify the policy and observed per-class checks but do not certify capacity. Verify each linked digest before relying on it.
- `../sla-study-index.json`, when listed by `research-index.json`: approved research policy file and B0 adaptive profile with hashes, all sampled points, per-class assessments, invalid reasons and raw artifact references. Its `capacity_confirmed` field remains false during proposal search. Verify the policy and source hashes. A missing index means the v3 SLA study was not supplied to this attempt.
- `../evidence/`: versioned protocol/domain/workload cards and prior measured background. Respect each file's source and protocol.
- `../history/`: previous proposal, receipt and notes. `notes.md` in the current workspace is the only writable research memory.

Read selective files with shell tools. Full Codex events, normalized proposal, receipts and evaluator logs remain in the attempt folder for an operator. Files omitted by staging limits are omissions, not evidence that a counter or request did not exist. The controller never stages held-out payloads or results while proposals are open.

## Interpretation

The active campaign decides which workloads and gates exist. For fixed-four v1, a complete suite is four matched fresh-server cells. For evaluation v2, the ordinary development task is the frozen mixed workload; independent development windows and shape-specific diagnostic tasks support promotion. Never pool v1 B0 with v2 cells. The synthetic proportions are engineered and do not establish production frequencies.

At a fixed operating point, report output tokens/s, TTFT and per-request TPOT. p50/p90/p95/p99 and request counts remain visible by class, load and repeat; the approved research policy drives the v3 study, while a product SLA would require separate ownership. TPOT is a per-request average decode interval, not aggregate output throughput. Adaptive AIPerf points change offered load, so plot a load curve and compare server configurations at matched load. A short trial, a chosen in-sample best point, or an observed B0 percentile is not an SLA capacity finding.

For each conclusion, include configuration ID, gate, workload and content/schedule hash, offered/realized rate, valid request count, repeat/window ID, evidence grade, and raw evidence path. Missing counters are unavailable. State whether a result is a screen, a repeated development observation, an exploratory capacity point or a sealed-test conclusion. A failure with missing requests or distorted dispatch is still useful evidence about validity and cost.

## Scope and memory

The controller owns deployment, GPU lease, workload selection, adaptive load search, gate promotion and final test. Propose serving settings only from the active typed domain. Prefix-cache and MTP variations require qualified mechanism-specific counters and, for MTP, semantic validation. Keep notes short: mechanism, supporting and contradicting cell IDs, unresolved issue, source URL/date and next comparison. There is no hidden vector memory or cross-campaign transfer claim.

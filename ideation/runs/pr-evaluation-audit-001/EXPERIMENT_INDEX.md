# Experiment index

All plans are untested and conditional on actual runtime/source eligibility. See [protocol](PROTOCOL.md).

For each experiment, [mechanism cards](evaluation/MECHANISM_CARDS.md) separate the upstream inefficiency and fix from our own hypothesis. The [evaluator reconciliation](evaluation/EVALUATOR_RECONCILIATION.md) critiques the suggested tooling changes; the [evaluation plan](evaluation/EVALUATION_PLAN.md) defines activation gates, internal measurements, integrations and the fixed enhanced evalset.

| ID | Priority | Experiment | Source records |
|---|---:|---|---:|
| E01 | 1 | [Length-aware decode indexer](experiments/E01.md) | 1 |
| E02 | 2 | [Remove unnecessary DSpark drafter padding](experiments/E02.md) | 1 |
| E03 | 3 | [Make full decode graph buckets reachable](experiments/E03.md) | 2 |
| E04 | 4 | [Lower CPU DP metadata collective overhead](experiments/E04.md) | 1 |
| E05 | 5 | [Compile relevant MegaMoE shapes before readiness](experiments/E05.md) | 4 |
| E06 | 6 | [Select an appropriate top-k implementation](experiments/E06.md) | 2 |
| E07 | 7 | [Recover scheduler budget reserved for parallel drafts](experiments/E07.md) | 1 |
| E08 | 8 | [Avoid repeated activation repacking](experiments/E08.md) | 2 |
| E09 | 9 | [Use the B200-specific FlashMLA pipeline](experiments/E09.md) | 1 |
| E10 | 10 | [Share and place host Engram backing correctly](experiments/E10.md) | 5 |
| E11 | 11 | [Fix observed DSpark prefix-hit loss](experiments/E11.md) | 6 |
| E12 | 12 | [Reduce scheduler CPU cost only where observed](experiments/E12.md) | 2 |
| E13 | 13 | [Coordinate prefill across DP ranks](experiments/E13.md) | 2 |
| E14 | 14 | [Preserve prefix locality at the final DP rank](experiments/E14.md) | 1 |
| E15 | 15 | [Fuse eligible Engram/mHC work at TP1](experiments/E15.md) | 1 |
| E16 | 16 | [Activate KV offload only as a separate configuration lane](experiments/E16.md) | 6 |
| E17 | 17 | [Limit drafter context only if long-context degradation appears](experiments/E17.md) | 2 |
| E18 | 18 | [Evaluate alternative precision/layout/kernel routes](experiments/E18.md) | 11 |
| G01 | gate | [Qualify speculative sampling semantics](experiments/G01.md) | 1 |
| G02 | gate | [Qualify graph, SWA and sparse-index memory safety](experiments/G02.md) | 6 |
| G03 | gate | [Qualify persistent-kernel synchronization](experiments/G03.md) | 2 |
| G04 | gate | [Qualify actual tool-turn encoding and parser semantics](experiments/G04.md) | 2 |
| G05 | gate | [Qualify idle/API2 liveness and restart state](experiments/G05.md) | 2 |

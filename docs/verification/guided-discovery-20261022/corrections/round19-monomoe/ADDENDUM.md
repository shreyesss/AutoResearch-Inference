# Correction: MonoMoE TP8 serving results in round19

The frozen round19 report, line 33, incorrectly says the reported TP8 DeepSeek TPOT results span a regression through a modest gain. That was a source-reading error. The retained full text (SHA256 `76ad98739b5183afbef2abb8ee24844621480fe66a8af43dfd7eaf2b3040416a`), section 4.4, reports **improvement at all four DeepSeek-V3.1 TP8 points**:

| Decode tokens | MonoMoE TPOT (ms) | Grouped GEMM TPOT (ms) | Reduction |
|---|---:|---:|---:|
| 1 | 8.98 | 10.3 | 12.8% |
| 2 | 10.00 | 10.9 | 8.3% |
| 4 | 10.96 | 11.5 | 4.7% |
| 8 | 13.90 | 14.4 | 3.5% |

These are author-reported serving results, not our reproduction. `checks.json` independently calculates the four reductions from the retained numbers. The original report and source remain unchanged.

The separate section 5.2 observation remains valid: its **fused EP dispatch/combine** using symmetric peer memory performed at parity in the reported regime. That result does not refute the positive TP8 improvements from the local fused expert operator. They are different comparisons and must not be combined into a blanket negative assessment of MonoMoE.

Our exact target still differs: the paper's H200 FP8-block128 DeepSeek-V3.1/TP8 study is not the Flash-1017 B200 TP1/DP4/EP4 MXFP4-weight/group32-activation MegaMoE baseline. Whole-kernel admission remains unqualified. Selective reuse of its low-token tensor-core mapping remains a legitimate source-audit question; positive author results justify examining the component, not predicting a target service gain. No hypothesis status, baseline, test outcome or performance forecast is changed by this correction.

Primary source: [MonoMoE](https://arxiv.org/abs/2609.04244), retained sections 4.4 and 5.2. No new provider call or GPU operation was made for this correction.

# C25 component result: independent review

2026-10-20 UTC. Evaluator-owned review of the prospectively frozen component experiment. Verdict: **exact component correctness passed, component acceleration measured, advance to a separately scoped native integration pilot**. No service or native full-model gain is claimed by this result.

The successful execution is `executions/sampler-component-002`. Its result SHA256 is `03a949483045915500eeda3a5504db70617860bf0ca07a3b557f9d1ed0e33b8d`; execution receipt SHA256 is `7d8552518edecb25ecf5f1e149150e803315e29ad4f7e2251c53b3086a00bbaf`. The executed harness is `7de227dafd67e555155166aa14d8c069e8f010d77750bcd6d5eceea8a7f46019`, candidate `7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`.

## Evidence and independent arithmetic

All 108 fixture receipts passed, including exact real-checkpoint BF16 cache/token/next-embedding comparisons, finite ordinary fixtures, both Gumbel precision modes, dense/permuted/padded request states, temperatures, ties and BF16 rounding, zero rows, persistent reuse, and 2,560 fixed/changed native graph replay checks. All six deliberately wrong controls were rejected. The ordinary reference calls the installed Gumbel sampler and installed unquantized embedding dispatch; the actual environment reports default_unquantized_gemm, batch-invariant false, and BF16 checkpoint weights. This supports the tested domain, not all model/configuration combinations.

I independently recomputed every raw 30-block AB/BA order, mean, paired percent gain, absolute saving, and 10,000-draw NumPy bootstrap interval from retained timing observations; all matched the frozen output. Timing buffers have native contiguous cache shape [64,5,129280], strides [646400,129280,1], and token shape [64,5], strides [5,1]. The extra sentinel layout is confined to correctness fixtures.

| Executed request rows | Baseline us/call | Candidate us/call | Saved us/call | Component gain |
|---|---:|---:|---:|---:|
| 1 | 181.480 | 136.135 | 45.346 | 24.99% |
| 2 | 206.086 | 138.961 | 67.125 | 32.57% |
| 4 | 215.749 | 145.294 | 70.455 | 32.66% |
| 5 | 226.090 | 149.538 | 76.553 | 33.86% |
| 7 | 239.984 | 156.740 | 83.244 | 34.69% |
| 16 | 309.809 | 186.735 | 123.074 | 39.73% |
| 32 | 331.703 | 227.966 | 103.736 | 31.27% |
| 64 | 484.137 | 330.474 | 153.662 | 31.74% |

Each call includes all five unchanged Markov bias GEMMs plus the sampler work. The prospective 1/2/4/7 lower-interval positivity and other-shape regression guards pass. These intervals describe paired replay precision in one isolated component allocation, not independent service launches.

## Cost, failure, and progression

Allocation 001 remains an infrastructure error: a checkpoint symlink escaped the mount, before any tensor fixture or candidate execution. It consumed 9.492 seconds of one visible GPU. The separately reviewed regular-blob bind repaired only the mount; allocation 002 consumed 29.901 seconds, 0.008306 visible GPU-hours. Source hashes stayed unchanged and all eight GPUs were idle after cleanup. Both allocations remain in the ledger; neither consumed a full service attempt.

The measured dominant-shape savings, approximately 45–83 microseconds per five-step call, are a useful native-integration signal. Dividing by historical 35.9 ms ITL with an assumed one sampler call per output gives only a direct additive scenario around 0.13–0.23%, not a hard service bound. Historical waiting gauges are small on average and GPU utilization is high, but neither establishes a queue-amplification model. No fivefold or eightfold multiplier is justified.

The old C03 confirmed service threshold of 2% remains unchanged for that endpoint. It is not a universal minimum for a new controlled native-stage result. The next justified expenditure is guarded actual-model/FULL-graph integration and controlled lifecycle correctness under a separate prospective contract. Real service improvement remains unresolved; no old verdict or full-attempt count is changed.

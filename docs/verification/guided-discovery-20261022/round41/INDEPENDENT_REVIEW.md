# Independent round41 graph-padding source review

Outcome: useful same-family C17 source refinement, no new hypothesis or measured gain. Original uniform fixture preserved. The requested independent varlen counter-fixture establishes why actual mode must precede applicability claims.

## Executed counter-fixture

`varlen_probe.py` extracts unchanged CUDAGraphMode, descriptor, compatibility, candidate-construction and dispatch code from the pinned sources. It constructs the same cap1024/max128-request/q6 grids as the original author diagnostic, toggles varlen, and supplies max_query_len6 for varlen. LoRA, DBO, dynamic scheduling and actual graph capture are stubbed. All rows are uniform six-token inputs even on the varlen-capable branch; this is not an adaptive schedule replay.

| Real requests | Uniform default → extra request sizes | Varlen default → extra request sizes |
|---|---|---|
| 1 | 6 → 6 | 6 → 6 |
| 2 | 12 → 12 | 12 → 12 |
| 3 | 18 → 18 | 24 → 18 |
| 4 | 24 → 24 | 24 → 24 |
| 5 | 36 → 30 | 32 → 30 |
| 6 | 36 → 36 | 40 → 36 |
| 7 | 42 → 42 | 48 → 42 |
| 8 | 48 → 48 | 48 → 48 |

48 constructed dispatch checks ran (2 modes × 8 request counts × 3 grids). Dense interactivity sizes1..32 cover the small uniform cases in the author fixture; on the varlen branch they still leave 36/42-token inputs padded to40/48. Descriptor request capacity differs from actual request count in varlen graphs; it is not valid to interpret padded descriptor num_reqs as real serving concurrency.

An initial reviewer expectation was [3,5,7] for changed varlen counts. The extracted source assertion falsified it with [3,5,6,7]; the corrected expectation and final output are retained. This was a diagnostic expectation error, not a target failure.

## Source gates and limits

Pinned V2 model_runner.py733–761 resolves graph mode for adaptive verification and explicitly passes `varlen_decode=self.adaptive_verification is not None`. The uniform-only fixture therefore cannot settle the adaptive native path. Dynamic schedule tiers, exact capture lists/caps, mixed prefill, FULL eligibility, draft-vs-target manager and custom configuration still require exact retained deployment evidence.

Pinned dp_utils.py157–209 chooses the minimum common graph mode and maximum padded token count across ranks before final dispatch. A local eligible request count is insufficient to establish an EP4 critical-path change. Another rank's larger batch or eager requirement can erase the local graph-grid difference. The probe does not execute this collective or attest any rank distribution.

These are shape-selection facts, not linear work/latency predictions. Padded rows may affect GEMM, routing, communication and attention differently; additional graph variants consume capture time and memory and may reduce KV capacity. Do not convert36→30 into a16.7% service gain. Existing interactivity/custom grids may already remove the gap. Capture-only changes can interact with quantization dispatch and existing shape-specific variants; savings are not additive with NQ33/PJ01/MF19 without a joint control.

C17 already covers capture-ladder exposure and padding. PR62173 is a concrete known donor; GLM TP4 K3/B300–GB200 measurements, fixed synthetic acceptance and reported0.54% AgentX decode effect cannot be transplanted to Flash1017 EP4 DSpark5. The first useful reopening record is actual target/draft graph descriptors selected per DP step together with graph mode and real/padded tokens, from existing logs if available. No missing changed descriptor means no-op. No such live record was obtained in this review; no GPU or provider call occurred.

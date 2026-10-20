# Independent timing verdict

**`instrumentation_inconclusive`. No AV-on qualification or rerun is authorized by this result.** The workload completed correctly enough for this diagnostic, but the frozen all-rank timing-adequacy gate did not pass. Both remaining full hypothesis attempts are preserved.

The986-request prefix completed986/986 with zero errors, profiling replay p99 **4.6538368ms**, and replay-degraded false. The later console warning of107615ms exactly matches the saved **55-request warmup** p99 of107614.99131904ms, not the profiling phase. The server-metrics relay timeout was followed by a completed3,105,464-row Parquet export and “All results received”; aggregate/profile exports are complete and not cancelled. Ordinary runner exit1 reflects service SLO ineligibility, which this timing study does not change.

The NOTICE anchor differs from final exact lifecycle start by−46,323ns. All four actual backend start dispatches were within0.326–4.844ms of the exact planned offsets. Both control episodes returned200 on both backends. Independently checked all18 collected file hashes, all16 trace PID/rank/container/physical-GPU bindings, and their CPU scope times against actual control intervals and the profiling phase. Startup/final runtime identities agree, and sources remained baseline k5 with AV off.

An initial offline reader defect mixed CPU annotations with Torch's mirrored GPU annotations. The original reader and first-trace failure are preserved. A separately reviewed v2 changes only two category filters to select CPU annotation parents, as the original attribution design intended. It adds no runtime work and changes no adequacy threshold; see [the schema addendum](READER_SCHEMA_ADDENDUM.md).

After that correction, two substantive limitations remain:

- Replica1/rank2 in the+90s episode contains26 target/proposal/execution scopes but only8 native execute annotations. Only **4 complete eligible decode cycles** can be joined, below the predeclared10. Nineteen target positions lack an unambiguous native/proposal join; two are mixed/prefill or have no generation, and one is the final incomplete boundary. These are observed coverage counts. Why the annotations have this mismatch is not established; extra scopes cannot be promoted into eligible cycles by assumption.
- Five rank/episode cells contain **647 GPU activities whose recorded end precedes the associated CPU launch start**. Their timing/correlation is unresolved and remains unclassified. It might involve clock or correlation behavior, but the saved evidence does not establish a cause. No timestamp shift, heuristic reassignment or threshold relaxation was applied.

Eleven cells satisfy parser-level timing adequacy. In those cells, target-attributed occupied GPU intervals account for **80.2–97.1%** of their complete-cycle spans; draft proposal accounts for **1.8–8.2%**. This is useful direction, not an all-rank result or proof of removable verification cost. Target ownership includes communication/waiting: the saved traces include target-owned NCCL AllGather kernels lasting about40–58ms. Neither target GPU occupancy nor a graph's elapsed span is automatically exposed client latency or compute AV can remove.

| Episode offset | Replica/rank | Eligible cycles | Target occupied / cycle | Draft proposal / cycle | Adequacy |
|---|---|---:|---:|---:|---|
|90s|0/0|19|86.8%|7.0%|Parser pass|
|90s|0/1|19|86.7%|7.0%|Parser pass|
|90s|0/2|19|86.8%|6.8%|Parser pass|
|90s|0/3|19|86.6%|7.0%|Parser pass|
|90s|1/0|16|96.1%|2.0%|Chronology unresolved|
|90s|1/1|19|80.2%|8.2%|Parser pass|
|90s|1/2|4|39.6%|0.4%|Insufficient cycles; chronology unresolved|
|90s|1/3|19|80.1%|8.1%|Chronology unresolved|
|210s|0/0|17|97.1%|1.8%|Parser pass|
|210s|0/1|15|90.5%|5.9%|Parser pass|
|210s|0/2|15|90.3%|5.8%|Parser pass|
|210s|0/3|18|97.1%|1.8%|Parser pass|
|210s|1/0|19|87.6%|6.5%|Chronology unresolved|
|210s|1/1|19|87.6%|6.5%|Parser pass|
|210s|1/2|19|87.6%|6.5%|Parser pass|
|210s|1/3|19|88.0%|6.4%|Chronology unresolved|

Fractions in failed cells are retained descriptive outputs, not qualified estimates. Each fraction is a within-cell sum of clipped interval unions divided by its complete-cycle spans; these numbers are not summed across GPUs, and no rank/window was selected to rescue the overall result.

Capture behavior was uneven. Replica1's+90s CPU-scope spans were roughly8.33/0.33/16.72/2.74s across ranks. The explicit stop/export control extended into the predeclared110–130s inactive context bracket, ending at phase113.651s; that bracket is contaminated and was not shifted. Other predeclared brackets do not overlap control calls. These facts, different request/shape mixtures and profiling/export overhead prevent treating the short recorded windows as an unbiased unprofiled cost model. They do not establish that the profiler alone caused the asymmetry. Ordinary replay fidelity passing does not prove low instrumentation overhead.

The contract required adequate evidence on every rank in both windows before applying its20% conditional materiality heuristic. That prerequisite failed, so **conditional materiality remains inconclusive despite the large target fractions**. AV was never enabled. Its budget selection, actual target/draft graph sizes after DP padding, controller overhead, accepted-token progress, correctness and service effect remain unmeasured. The source-reviewed possibility that variable target request capacity could enlarge draft execution is another reason not to equate a large target share with an AV win.

Root archived the evidence, obtained three consecutive zero-inflight/zero-running/zero-waiting samples across router/all8 engines, and stopped task-owned backends/router. Cleanup records ports8000/8100/8101 closed and all eight GPUs at0MiB; unrelated monitoring remained available. The machine is not left in profiling mode.

Machine-readable evidence and exact hashes are in [FINAL_VERDICT.json](FINAL_VERDICT.json); review provenance is in [EVALUATOR_REVIEW.md](EVALUATOR_REVIEW.md).

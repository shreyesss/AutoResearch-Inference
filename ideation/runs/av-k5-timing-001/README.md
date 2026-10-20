# Adaptive k5 timing qualification

Purpose: measure the current AV-OFF k5 baseline before deciding whether adaptive target verification merits a full hypothesis attempt. This is diagnostic preparation for [C24](../../hypotheses/C24.md), not an A/B performance result. The user authorized this diagnostic on 2026-10-21 (Asia/Calcutta), after the [C03 mechanism review](../c03-mechanism-review-001/REPORT.md).

**Completed: instrumentation inconclusive.** [Report and timing table](REPORT.md), [independent verdict](FINAL_VERDICT.md), [all logs/traces and restoration](../../evidence/av-k5-timing-001/README.md). Traffic passed (986/986 successes, replay p99 4.65ms), but the required all-rank timing coverage and association checks failed. AV remains unqualified; both full attempts remain. Original environments are unchanged and the node is idle.

The original `latency-2xdep4-sla` profile, local H200 node, pinned image/model, two TP1/DP4/EP4 replicas, DSpark k5, FP8 KV and Mooncake 0.5x remain the baseline. Original environments and installed source are preserved. Observation labels live in the isolated `/home/ubuntu/Deepseek_serve-c03/av-k5/` tree, mounted read-only into diagnostic containers. The rejected C03 optimization is absent.

| Responsibility | Agent | Boundary |
| --- | --- | --- |
| Evaluator design and independent interpretation | c03_evaluator | Defines timing validity, attribution limits and decision; does not implement collector or optimization. |
| Evaluator tooling | c03_evaluator_builder_review | Builds observation scopes, bounded control and trace reader; does not develop adaptive verification. |
| Runtime/source feasibility and launch rendering | c03_dev_review | Reviews installed support and renders baseline diagnostic launch; does not implement evaluator. |
| Runtime, evidence preservation and publication | root | Owns containers, clients, cleanup, integrity checks and upstream push. |

See [source/launch feasibility](IMPLEMENTATION_FEASIBILITY.md). The evaluator contract, startup receipts, trace/control artifacts, result analysis and independent review are recorded alongside this file as they complete. Measurement must distinguish CPU submission, GPU occupied time and causally exposed time. Missing attribution is an inconclusive measurement, never evidence of a cheap or expensive bottleneck.

Initial source attestation found that the installed `model_state.py` contains additional decoder replay graph code compared with the nominal upstream revision; the exact image file and diff are retained under `source/`. The profiler files and the two baseline files used for observation scopes match. The installed image remains authoritative and is not replaced by upstream source.

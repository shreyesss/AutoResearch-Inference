# Saved C24 trace audit

The saved evidence does not justify a retrospective timing repair. The original `instrumentation_inconclusive` result remains unchanged. A fresh diagnostic-only reader checked all 16 trace SHA256 values and retained all 647 anomalies with exact raw event indices and CPU/GPU records; no event was reassigned, no clock shifted, and no eligibility threshold changed. Six CPU negative-control tests pass (including duplicate runtime/driver records, reused correlation across CPU processes, missing correlations, mirrored annotations and conflicting correlation fields).

All 647 activities have exactly one runtime/driver record for the correlation ID in their saved worker trace. Across all 16 traces there are no duplicated runtime correlation IDs or GPU events lacking a unique runtime correlation. External IDs independently agree for 460 anomalies; the other 187 omit the field on both records, all from driver launches. There are no conflicting present External IDs. The diagnostic JSON field `external_id_present_and_equal=false` means absence here, not disagreement; the receipt states that distinction explicitly.

| Episode | Replica/rank | Negative chronology records | GPU end minus CPU launch start, microseconds | Graph records |
|---|---|---:|---|---:|
|90s|1/0|53|−7.991 to −0.017|0|
|90s|1/2|406|−488.717 to −0.118|19 (graph 14009)|
|90s|1/3|43|−2.305 to −0.094|0|
|210s|1/0|91|−14.259 to −1.381|0|
|210s|1/3|54|−2.671 to −0.080|0|

These are contradictions in the recorded CPU/GPU chronology under the original assertion. Unique IDs make a duplicate-ID parsing defect unlikely in this dataset, but do not prove a clock-calibration cause. The offsets vary; fitting a shift or dropping the chronology check would not resolve their provenance. The other 11 cells have zero such anomalies.

A separate source-level blind spot explains why native annotations need not cover all target scopes. The attested `gpu_worker.py` implementation calls `annotate_profile` (and therefore `profiler.step`) only from `execute_model`. `execute_dummy_batch` calls `model_runner._dummy_run` directly; `_dummy_run` calls the instrumented `model_runner.execute_model(..., dummy_run=True)` and its draft path. Such dummy work can create target/proposal/execution scopes while neither creating a native context/generation annotation nor advancing the profiler schedule. This is a demonstrated reachable source path, not proof that every uncovered saved scope took it.

The saved replica1/rank2/+90s trace has exactly eight `ProfilerStep#` intervals and eight native execute ranges, with 26 target scopes: seven targets are inside a native range, 19 are outside. Profiler step 3 lasts 2.726 seconds even though its native zero-generation range lasts only 235 microseconds; step 7 lasts 7.183 seconds. Thus the mismatch is not merely failure to parse a second spelling of the native annotation. No saved dummy identity permits relabeling those 19 scopes or creating missing real decode counts. Replica1/rank0/+90s also has six uncovered targets; rank3 has two. All other cells have 20 targets inside 20 native ranges.

The immediate discriminating next experiment is a fixed synthetic single-H200 calibration of the installed profiler and same-device CUDA events, before another 26-minute model startup. Its independent contract and implementation must preserve causal launch identities, inspect graph and eager paths, and compare recorded GPU spans with event intervals without fitted offsets. A negative result must remain negative rather than trigger repeat-until-pass.

Any later service instrumentation needs explicit dummy-versus-real identity, scheduler context/generation counts and profiler-step identity at the common executed path. It also needs a capture design that bounds and records per-rank stop/export behavior without pretending idle ranks contribute real decode samples. Merely lengthening the old native-step schedule does not address either demonstrated limitation. Source annotations alone do not repair CPU/GPU chronology. No new service capture is qualified by this audit.

Artifacts: `saved-trace-audit.json` retains all anomalies and target/native/ProfilerStep records; `saved-trace-audit-receipt.json` binds code/output/test hashes. Source references: old pinned `vllm/v1/worker/gpu_worker.py:1132,1303,1390` and observation `vllm/v1/worker/gpu/model_runner.py:798,873`; the old installed-source attestation governs source equivalence. No GPU, container, service or environment mutation was performed for this audit.

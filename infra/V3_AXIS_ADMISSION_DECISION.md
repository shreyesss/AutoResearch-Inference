# V3 serving-axis admission decision

**Decision, 18 October 2026 IST:** keep the active v2 serving domain unchanged
until the class-aware B0 load profile identifies a binding server mechanism.
This is an evidence gate, not a claim that the listed controls cannot help.
The first OPS36 B0 completed 36/36 with queue peak 1, so it cannot identify a
sequence-cap, KV-pressure or admission-control effect. The approved research
SLA profiler is the next source of rate, queue, KV and per-class latency data.

| Candidate control | Why it is not admitted now | What would admit it |
| --- | --- | --- |
| `max_num_seqs` | Current active demand is well below B0's 512 cap on OPS36. Smaller caps can create queueing by construction. | At a qualified SLA rate, observe peak active sequences near the chosen cap, then compare an explicit bounded cap with matched B0 arrivals and class latency. |
| `gpu_memory_utilization`, `--watermark`, `--scheduler-reserve-full-isl` | No qualified observation of KV occupancy, preemption or cache scarcity. Changing these without pressure samples an idle mechanism. | Record KV occupancy and preemptions near the SLA boundary; boot a versioned contrast and verify the effective launch setting and matched result. |
| `--max-num-scheduled-tokens` | With MTP fixed off it may simply lower the same token budget as `max_num_batched_tokens`. | Show a distinct resolved cap and scheduler saturation while holding the batch-token cap fixed. |
| `enable_chunked_prefill=false` | The current search allows 2,048–16,384 batch tokens against a 40,960-token context. Disabling chunking may make long requests unservable or fail startup; the current 240-request workload has not yet been validated under that contrast. | First prove a bootable compatible token budget and complete mixed workload, then compare prefill/decode interference under matched traffic. |
| `--compilation-config`, `--enable-dbo` | Model-specific boot, graph coverage or overlapping-batch capability remains unmeasured. | Run a bounded capability boot, confirm startup receipt, then match steady-state class latency separately from boot time. |

Prefix caching and MTP remain outside the active domain until token-exact
reuse/cache-hit evidence and accepted-token plus semantic-quality evidence are
available. The active v2 `max_num_batched_tokens`,
`long_prefill_token_threshold` and `enforce_eager` already give three genuine
mechanism contrasts. After the B0 SLA profile, promote only controls whose
mechanism was observed, to a new versioned domain and campaign. Do not mutate
the v2 campaign or the rsynced handoff.

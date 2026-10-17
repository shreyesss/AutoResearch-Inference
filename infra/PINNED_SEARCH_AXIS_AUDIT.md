# Pinned vLLM serving-axis audit for the next campaign

**Status:** capability audit, not an active search-domain revision. The running
`qwen38-27b-eval-v2` campaign and its configuration identity are unchanged.
The evidence below is the local pinned
`vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14`
image's `vllm serve --help=all`, inspected on 17 October 2026. A CLI flag
existing does not prove that it boots with Qwen3.8-27B or improves this task.

## Admission criterion

Add an axis to a new, versioned domain only after the pinned server accepts
it, the startup receipt confirms its effective value, and a matched B0 and
candidate run show the mechanism can bind on a qualified workload. An axis
whose intended bottleneck is absent should remain a targeted capability
probe, not be sampled by the optimizer. The present OPS36 B0 had 36/36
completions and queue peak 1; it does not establish KV-cache pressure,
preemption, or high-concurrency admission behavior.

| Pinned CLI control | Pinned help semantics | Evidence required before search admission |
| --- | --- | --- |
| `--max-num-scheduled-tokens` | Defaults to `max_num_batched_tokens`; a smaller limit is especially relevant when the model appends tokens, such as speculative decoding. | Show an effective cap distinct from the batch-token cap and measured scheduler saturation. With MTP fixed off, first check whether it is merely a second way to lower the same effective budget. Do not add a redundant Cartesian axis. |
| `--scheduler-reserve-full-isl` / `--no-scheduler-reserve-full-isl` | Default true; reserves enough KV space for the full input before admitting a chunked-prefill request. | Observe waiting/preempted requests, cache pressure or thrashing at the intended SLO load. Confirm the resolved setting and compare full-input reservation under the same arrivals. |
| `--watermark` | Fraction of KV blocks kept free at admission; default 0.0, valid range `[0, 1)`. | Observe cache scarcity and preemptions, then test bounded fractions with measured throughput, tail latency, queue and memory. A low-pressure contrast is unlikely to identify a useful setting. |
| `--compilation-config` | Structured torch-compile and CUDA-graph configuration. | First bound modes/capture sizes compatible with this hybrid model; boot each candidate, confirm resolved graph settings, and compare startup, graph coverage, VRAM and steady-state latency separately. Do not expose free-form JSON from the proposer. |
| `--enable-dbo` | Dual batch overlap switch. | Separate model-specific capability boot and correctness check, then a load that actually has overlapping batches. No blind search admission. |

The current active controls (`max_num_batched_tokens`,
`long_prefill_token_threshold`, `enforce_eager`) remain the only admitted v2
axes. `max_num_seqs` and GPU memory fraction become relevant when a load
actually reaches the sequence limit or produces KV pressure. Prefix caching
and MTP remain excluded until token-exact reuse/cache-hit and
accepted-token/semantic-quality evidence, respectively, are available.

**Next search-space checkpoint:** run the SLO-directed adaptive load pilot,
inspect realized rate, queue, KV occupancy, preemptions, and class latency,
then choose one binding admission or graph axis for a versioned boot and
matched-B0 contrast. AIPerf's traffic search supplies the load at which a
server control may matter; it does not turn server flags into an optimizer
automatically.

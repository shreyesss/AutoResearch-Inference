# Independent source review of the live proposal endpoint

Design/source review only; no GPU allocation release. The primary cohort remains actual real requests with FULL target and FULL draft execution, as defined by the prospective live-stage contract.

The installed DFlash propose path prepares inputs/context, builds draft metadata, invokes `query_cudagraph_manager.run_fullgraph(batch_desc)` in its FULL branch, then returns a draft-token view. No separate explicit side-stream launch appears in that outer proposal routine. The manager first synchronizes prior offloader onload work, then calls the captured graph's replay. Thus the proposed event span includes real preparation, any included offloader wait and graph completion; it is not a pure kernel-time sum. AsyncOutput's separate output-copy work begins before this call and is outside the declared proposal endpoint.

CUDA graph launch streams order graphs with other asynchronous work without restricting internal parallelism; captured side streams must rejoin the origin stream or capture fails. This supports same-stream outer events for the captured FULL graph, without claiming global completion of unrelated device work. [NVIDIA CUDA graph execution and capture semantics](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html#using-graph-apis).

Eager, mixed and prefill observations remain secondary main-stream proposal spans. No broader assertion about every unrelated serving subsystem or device stream is needed for the primary claim. Actual runtime stream/descriptor identity, finite durations and raw coverage remain required by the contract.

Bound installed source hashes:

- DFlash speculator: `e7950d0bbdb3f982890689268eafc1a9d46d97335487e3c5c624945e3312afc6`.
- CUDA graph manager: `cc090e6749029baaa5055135215acc112ce034a32fc1e886f0f02054ad488b58`.

Final overlay review must verify that the observer preserves these operations and event boundaries. Source support is not a numerical or performance result.

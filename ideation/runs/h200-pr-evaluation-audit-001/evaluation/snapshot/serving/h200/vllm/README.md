# vLLM on 8× H200

This recipe serves `deepseek-ai/DeepSeek-V4.1-Flash` on one eight-H200
NVLink/NVSwitch node. It uses the model revision
`2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, the `deepseek_v41`
tokenizer/reasoning/tool parsers, FP8 KV cache, chunked prefill, and host-backed
Engram. See the [official model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
and [vLLM V4.1 recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash).

## Immutable pins

`images.yaml` defines two complete image/source pairs:

- Default:
  `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`,
  built from vLLM commit
  `ac9126e58aa7bbab1856ba6593ba4d5003fea516`.
- Reference:
  `vllm/vllm-openai@sha256:20a52b807cef7a3be15d2174d293b5642d437615b20b5930d78a927e709e6bb6`,
  built from commit
  `cd10ed6f9f6b37a8ace9cf380007e66fe12ec0c3`.

The launcher uses the default. `VLLM_IMAGE` can override it, but an override is
not a qualified run unless it is also an immutable digest with a recorded
source commit.

## Profiles and topology

Every profile exposes the native 1,048,576-token context, enables prefix
caching with SHA-256 keys, disables output-changing SWA bounded replay, and
uses Engram CPU offload. Multi-replica profiles start backends on ports
8100/8101 and the local router on `PORT` (8000 by default).

| Profile | Eight-GPU layout | Max sequences | Batched tokens | CUDA graph cap | Distinguishing setting |
| --- | --- | ---: | ---: | ---: | --- |
| `low-latency` | one TP8, port 8000 | 8 | 4,096 | 64 | DSpark, block rejection; adaptive verification off |
| `balanced` | two TP4 replicas, ports 8100/8101 | 64/replica | 4,096 | 64 | target-only mixed traffic |
| `throughput` | two TP4 replicas, ports 8100/8101 | 128/replica | 4,096 | 128 | larger decode batches |
| `long-context` | one TP8, port 8000 | 16 | 4,096 | 32 | reduced concurrency |
| `prefix-heavy` | two TP4 replicas, ports 8100/8101 | 64/replica | 4,096 | 64 | repeated-prefix traffic |
| `multimodal-heavy` | one TP8, port 8000 | 16 | 4,096 | 64 | 16 GiB multimodal processor cache |

Capabilities additionally label DEP8 experimental; no shipped profile selects
it. The supported profile topologies are TP8 and two independent TP4 replicas.

## Launch and render

From the repository root:

```bash
# Make: serve
PROFILE=balanced make serve-h200-vllm

# Bash: serve
bash serving/h200/vllm/serve.sh --profile balanced

# Make: render the exact Docker/router commands without starting containers
DRY_RUN=1 PROFILE=balanced make serve-h200-vllm

# Bash: render
bash serving/h200/vllm/serve.sh --profile balanced --dry-run
```

The first load may take substantial time for the roughly 500 GB checkpoint,
Engram placement, memory profiling, JIT work, and CUDA graph capture. For a
two-replica profile, both backends must become ready before the router starts.

## Experiments

Select experiments with
`EXPERIMENTS="prefix-off eager" make serve-h200-vllm`, or repeat
`--experiment` with the Bash launcher.

| Experiment | Classification | Semantics and risk |
| --- | --- | --- |
| `adaptive-dspark` | workload-conditioned | Enables five-token probabilistic DSpark with block rejection and adaptive verification; qualify graph fit, acceptance, latency, and correctness on production prompts. |
| `bounded-replay` | output-changing | Enables SWA bounded replay. It can accelerate cache hits but is not the strict cold-prefill semantic baseline. |
| `prefix-off` | workload-conditioned | Disables prefix caching; useful for unique-prompt baselines and cache-benefit attribution. |
| `eager` | diagnostic | Disables CUDA graphs; use to isolate graph failures, not for capacity claims. |
| `higher-memory-utilization` | workload-conditioned | Raises GPU memory utilization from 0.90 to 0.95; increases usable KV space and OOM risk. |

`output-changing` arms must never be reported as equivalent to the strict
baseline. Keep diagnostic and workload-conditioned arms separate in result
manifests.

## Context, images, and compatibility

- Full context is a configuration guarantee: every profile passes
  `--max-model-len 1048576`. It is not a guarantee that many simultaneous
  million-token requests fit or meet an SLO; qualify with the near-1M cases in
  `testing/workloads/text-grid.yaml`.
- Image serving remains enabled in every profile. vLLM uses data-parallel
  multimodal encoding and shared-memory processor caching; only
  `multimodal-heavy` raises that cache to 16 GiB. Published capacity is mostly
  text-only, so run the image smoke test and `testing/workloads/multimodal.yaml`
  before claiming multimodal capacity.
- Eight H200s with fast peer-to-peer connectivity are assumed. TP4 Engram host
  offload is required for practical KV headroom; provision host RAM and
  unlimited memlock.
- Adaptive DSpark verification is deliberately disabled in the H200 base.
  Do not infer Blackwell DSpark behavior from this path.
- Do not force Blackwell-only `FLASHINFER_MLA_SPARSE_DSV41`, MXFP4 indexer, or
  sparse-logit settings on H200. The launcher intentionally lets vLLM select
  its SM90/Hopper V4.1 sparse-attention implementation and uses 64-token FP8
  KV blocks.

## Startup verification

Before load testing, inspect all backend logs and verify:

1. Eight H200/SM90 devices are visible and the requested TP8 or two-TP4 layout
   and ports were created.
2. The pinned V4.1 revision loaded with the `deepseek_v41` tokenizer,
   reasoning parser, and tool parser.
3. The selected attention path is the Hopper V4.1 sparse/FlashMLA path, not
   `FLASHINFER_MLA_SPARSE_DSV41`; KV cache is FP8 with block size 64.
4. Engram reports CPU offload, prefix caching reports SHA-256 hashing, chunked
   prefill is enabled, and CUDA graphs captured through the profile's cap.
5. `low-latency` reports DSpark with five draft tokens, probabilistic sampling,
   and block rejection, with adaptive verification false.
6. No kernel fallback, OOM, graph-capture, NCCL, or parser warning occurred,
   and `GET /v1/models` succeeds on every backend and on the public endpoint.

Run the repository smoke and capacity suite only after these checks; see
`testing/README.md`.

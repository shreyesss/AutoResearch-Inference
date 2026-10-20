# vLLM on 8× B200

This recipe serves `deepseek-ai/DeepSeek-V4.1-Flash` on one eight-B200
NVLink/NVSwitch node. It pins model revision
`2cba9e42aa026125f3ed06c6d98c1db82f7ca027` and uses different Blackwell
attention/MoE stacks for TP and DEP profiles. References:
[vLLM V4.1 recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash),
[official model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash),
and [technical report](https://arxiv.org/abs/2609.19969).

## Immutable pins

`images.yaml` defines one image/source pair:

- `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`
- vLLM source commit
  `ac9126e58aa7bbab1856ba6593ba4d5003fea516`

The digest is the default. `VLLM_IMAGE` overrides it, but an override is not a
qualified result unless it is another immutable digest with a recorded source
revision.

## Profiles and topology

Every profile exposes 1,048,576 tokens, uses FP8 KV, host-backed Engram,
chunked prefill, SHA-256 prefix caching, and strict
`--no-swa-bounded-replay`. Two-replica profiles use ports 8100/8101 and a
local router on `PORT` (8000 by default).

| Profile | Eight-GPU layout | Max sequences | Batched tokens | CUDA graph cap | Distinguishing setting |
| --- | --- | ---: | ---: | ---: | --- |
| `low-latency` | two TP4 replicas | 8/replica | 4,096 | 64 | real DSpark with adaptive verification |
| `balanced` | two TP4 replicas | 64/replica | 4,096 | 64 | target-only mixed traffic |
| `throughput` | one DP8/EP8, TP1 replica | 128 | 8,192 | 128 | Mega-Attention + MegaMoE |
| `latency-dep8-sla` | one DP8/EP8, TP1 replica | 64 | 16,384 | 512 | R7 DSpark-k5 latency winner |
| `latency-2xdep4-sla` | two DP4/EP4, TP1 replicas | 64/rank (256/replica) | 16,384 | 512 | R7 knobs, API2/replica, unique DP RPC ports |
| `long-context` | one DP8/EP8, TP1 replica | 16 | 4,096 | 32 | DEP8 at reduced concurrency |
| `prefix-heavy` | two TP4 replicas | 64/replica | 4,096 | 64 | repeated-prefix traffic |
| `multimodal-heavy` | two TP4 replicas | 16/replica | 4,096 | 64 | 16 GiB processor cache/replica |

Two TP4 and DEP8 are supported. The real same-node two-DEP4 profile is
experimental and must pass `ops_latency/run_2xdep4_smoke.sh` before measured
traffic. Capabilities also list four TP2 replicas and one TP8 replica as
experimental.

## Launch and render

From the repository root:

```bash
# Make: serve
PROFILE=balanced make serve-b200-vllm

# Bash: serve
bash serving/b200/vllm/serve.sh --profile balanced

# Make: render both backend and router commands without starting containers
DRY_RUN=1 PROFILE=balanced make serve-b200-vllm

# Bash: render
bash serving/b200/vllm/serve.sh --profile balanced --dry-run
```

For DEP8, substitute `PROFILE=throughput` or `PROFILE=long-context`.
For the routed comparison endpoint, use `PROFILE=latency-2xdep4-sla`; this
starts DP4 engines on 8100/8101 and the local router on 8000.

## Experiments

Use `EXPERIMENTS="prefix-off eager" make serve-b200-vllm`, or repeat
`--experiment` with the Bash launcher.

| Experiment | Classification | Semantics and risk |
| --- | --- | --- |
| `dspark-off` | workload-conditioned | Currently has no args or environment changes, so it is a no-op. It does **not** disable DSpark in `low-latency`; use a target-only profile for a real control. |
| `bounded-replay` | output-changing | Enables SWA bounded replay; potentially faster cache hits, but not strict cold-prefill semantics. |
| `prefix-off` | workload-conditioned | Disables prefix caching for unique-prompt controls and cache attribution. |
| `eager` | diagnostic | Disables CUDA graphs to diagnose capture/runtime failures; not a capacity configuration. |
| `utilization-095` | workload-conditioned | Raises memory utilization from 0.90 to 0.95; more KV headroom with higher OOM risk. |
| `utilization-097` | benchmark-only | Raises utilization to 0.97; a stress arm with little allocator/workspace margin, not a production default. |

Keep output-changing, diagnostic, and benchmark-only arms distinct in labels
and manifests. The launcher warns for output-changing and benchmark-only
classes.

## Context, images, and compatibility

- All profiles pass `--max-model-len 1048576`. This is an API/configuration
  guarantee, not a guarantee that concurrent full-context requests fit or meet
  an SLO. Use the near-1M text-grid cases for qualification.
- Image support is retained in every profile with data-parallel multimodal
  encoding and shared-memory processor caching. Only `multimodal-heavy`
  raises the cache to 16 GiB. Public sweeps are mostly text-only; image smoke
  and multimodal capacity tests are required locally.
- TP profiles use `FLASHINFER_MLA_SPARSE_DSV41`, MXFP4 indexer KV, sparse
  logits, and FlashInfer autotuning. DEP8 profiles instead use
  `FLASHMLA_MEGA_ATTN_DSV41` and `deep_gemm_mega_moe`; compare them as
  whole-system topologies, not as a one-flag kernel ablation.
- DEP8 distributes Engram embeddings across DP ranks. Two TP4 replicas
  independently load host-resident Engram state, so size host RAM and NUMA
  bandwidth for duplication.
- Use eight B200/SM100 GPUs in one fast fabric. These Blackwell backend choices
  are not H200-compatible.

## Startup verification

Before sending benchmark traffic, verify in every backend log:

1. Eight B200/SM100 devices are visible and the requested layout is either two
   TP4 replicas or one TP1/DP8/EP8 replica, with the expected ports/router.
2. The pinned V4.1 revision loaded with `deepseek_v41` tokenizer, reasoning,
   and tool parsers; the v2 model runner and Rust frontend initialized.
3. TP4 reports `FLASHINFER_MLA_SPARSE_DSV41`; DEP8 reports
   `FLASHMLA_MEGA_ATTN_DSV41` plus `deep_gemm_mega_moe`. Both report MXFP4
   indexer KV, sparse logits, FP8 KV, and FlashInfer autotuning where
   configured.
4. Engram CPU offload is active, and DEP8 additionally reports distribution
   across DP ranks.
5. Prefix caching, chunked prefill, and CUDA graphs initialized at the profile
   limits. `low-latency` reports five-token probabilistic DSpark, block
   rejection, and adaptive verification.
6. No generic-kernel fallback, graph/OOM, NCCL, parser, or model-revision
   warning occurred, and `/v1/models` succeeds on every backend and the public
   endpoint.

Continue with the smoke and capacity procedure in `testing/README.md`.

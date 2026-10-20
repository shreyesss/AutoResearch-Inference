# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""DSpark speculator: semi-autoregressive parallel drafting.

DSpark drafts a block of ``num_speculative_tokens`` tokens in one parallel pass
(reusing the DFlash machinery: context-KV precompute + a query-block forward),
then injects intra-block dependency with a lightweight sequential Markov head.

Differences from DFlash:
  * Anchor-as-first-prediction: each request emits exactly ``N =
    num_speculative_tokens`` query tokens (anchor + N-1 noise), NOT ``1 + N``.
    Every query position is a prediction (the anchor predicts the first draft
    token), so we sample at all N positions and ``sample_pos = query_pos + 1``
    (standard next-token), whereas DFlash's masks sit AT the predicted position.
    This is the ``sample_from_anchor`` path in the shared prepare-inputs kernel.
    Speculators-format checkpoints instead use the DFlash ``1 + N`` fill-in
    layout (anchor is the bonus token).
  * Sequential Markov sampling: instead of DFlash's single parallel sample, we
    sample left-to-right, adding a prefix-dependent Markov bias derived from the
    previously sampled token at each step.

CUDA graphs (FULL, mirroring DFlash) cover the whole draft step: the parallel
backbone forward AND the sequential Markov sampling.
"""

from typing import Any

import json

import torch

from vllm.config import VllmConfig
from vllm.config.compilation import CUDAGraphMode
from vllm.logger import init_logger
from vllm.platforms import current_platform
from vllm.v1.worker.gpu.sample.gumbel import gumbel_sample
from vllm.v1.worker.gpu.spec_decode.dflash.speculator import DFlashSpeculator
from vllm.v1.worker.gpu.spec_decode.dspark.utils import load_dspark_model
from vllm.v1.worker.gpu.spec_decode.dspark.c25_adapter import eligible_markov_embedding
from vllm.v1.worker.gpu.spec_decode.dspark.c25_fused_sampler import DSparkFusedMarkovSampler

logger = init_logger(__name__)


class DSparkSpeculator(DFlashSpeculator):
    _speculator_name = "DSpark"

    def __init__(self, vllm_config: VllmConfig, device: torch.device):
        super().__init__(vllm_config, device)

        # Whether to sample from the anchor position. When True, uses anchor-as-first
        # (N slots, each position predicts the next token). When False, uses 1+N
        # fill-in block (anchor is a bonus token).
        self.sample_from_anchor = getattr(
            self.draft_model_config.hf_config, "sample_from_anchor", True
        )
        if self.sample_from_anchor:
            self.num_query_per_req = self.num_speculative_steps
        else:
            self.num_query_per_req = 1 + self.num_speculative_steps

        # DSpark consumes mean-pooled target aux hidden states at the target
        # layers, combined to hidden_size via main_proj. Store that combined
        # main_x (hidden_size wide). DSpark does not use the same pre-allocated buffer
        # that DeepSeek-V4's MTP uses.
        draft_hidden = self.draft_model_config.get_hidden_size()
        self.hidden_states = torch.zeros(
            self.max_num_tokens, draft_hidden, dtype=self.dtype, device=device
        )

        self._step_cols = torch.arange(
            self.num_speculative_steps, dtype=torch.int32, device=device
        )

        self._anchor_idx = (
            torch.arange(self.max_num_reqs, dtype=torch.int64, device=device)
            * self.num_query_per_req
        )

        # Reduced-vocab probabilistic drafting only; set in load_draft_model.
        self._d2t_scatter_index: torch.Tensor | None = None
        self._draft_scatter_buf: torch.Tensor | None = None
        self._draft_topk: int | None = getattr(
            self.draft_model_config.hf_config, "dspark_draft_topk", None
        )

        self.use_confidence_head: bool = False
        self._c25_fused_sampler: DSparkFusedMarkovSampler | None = None
        self._c25_activation: dict[str, Any] = {"active": False, "reason": "not_loaded"}

    def load_model(self, target_model: torch.nn.Module) -> None:
        # Base load_model assigns self.model only after load_draft_model returns.
        # Initialize the persistent sampler here, before profiling/capture.
        super().load_model(target_model)
        target_tp = self.vllm_config.parallel_config.tensor_parallel_size
        draft_tp = self.speculative_config.draft_parallel_config.tensor_parallel_size
        model_type = type(self.model)
        outer_eligible = (
            target_tp == 1
            and draft_tp == 1
            and self.vllm_config.watermark_config is None
            and self.vllm_config.lora_config is None
            and current_platform.is_device_capability((9, 0))
            and model_type.__module__ == "vllm.models.deepseek_v41.nvidia.dspark"
            and model_type.__name__ == "DSparkDeepseekV4ForCausalLM"
            and self.sample_from_anchor
            and self.num_query_per_req == 5
            and self.acceptance_estimator is None
            and not self.use_confidence_head
        )
        weight = (
            eligible_markov_embedding(self, tensor_parallel_size=draft_tp)
            if outer_eligible else None
        )
        if weight is not None:
            self._c25_fused_sampler = DSparkFusedMarkovSampler(
                self.max_num_reqs,
                self.vocab_size,
                weight,
                self.use_fp64_gumbel,
            )
        self._c25_activation = {
            "active": self._c25_fused_sampler is not None,
            "outer_eligible": outer_eligible,
            "dp_rank": self.dp_rank,
            "target_tp": target_tp,
            "draft_tp": draft_tp,
            "model_class": model_type.__module__ + "." + model_type.__name__,
            "sample_from_anchor": bool(self.sample_from_anchor),
            "query_width": self.num_query_per_req,
            "num_speculative_steps": self.num_speculative_steps,
            "vocab_size": self.vocab_size,
            "adaptive_verification": self.enable_adaptive_verification,
            "engine_watermark_absent": self.vllm_config.watermark_config is None,
            "draft_watermarker_absent": self.draft_watermarker is None,
            "draft_topk": self._draft_topk,
            "use_fp64_gumbel": self.use_fp64_gumbel,
            "embedding_shape": list(weight.shape) if weight is not None else None,
            "cache_shape": list(self.draft_logits.shape) if self.draft_logits is not None else None,
            "cache_dtype": str(self.draft_logits.dtype) if self.draft_logits is not None else None,
            "max_num_reqs": self.max_num_reqs,
        }
        logger.info("C25_NATIVE_ACTIVATION %s", json.dumps(self._c25_activation, sort_keys=True))

    def load_draft_model(
        self,
        target_model: torch.nn.Module,
        target_attn_layer_names: set[str],
    ) -> torch.nn.Module:
        model = load_dspark_model(target_model, self.vllm_config)
        # Reduced draft vocab: probabilistic rejection sampling indexes draft
        # logits by target id, so precompute the draft->target column map and a
        # scratch buffer to scatter logits into target vocab before sampling.
        if self.draft_logits is not None and model.draft_id_to_target_id is not None:
            d2t = model.draft_id_to_target_id
            self._d2t_scatter_index = (
                torch.arange(d2t.shape[0], device=d2t.device) + d2t
            )
            # -inf once; the per-step scatter overwrites the draft->target
            # columns. Kept separate from draft_logits to avoid aliasing.
            self._draft_scatter_buf = torch.full(
                (self.max_num_reqs, self.vocab_size),
                float("-inf"),
                dtype=self.draft_logits.dtype,
                device=self.device,
            )
        self.use_confidence_head = (
            self.enable_adaptive_verification
            and model.model.confidence_head is not None
        )
        if self.use_confidence_head:
            # The acceptance estimator is not needed when a trained confidence head
            # is available.
            self.use_acceptance_estimator = False
        return model

    def _sample_logits(
        self,
        logits: torch.Tensor,
        idx_map: torch.Tensor,
        sample_pos: torch.Tensor,
        step: int,
    ) -> torch.Tensor:
        self._maybe_predict_acceptance(logits, idx_map, self._step_cols[step])
        if self.draft_logits is None:
            draft_ids = logits.argmax(dim=-1)
            return self.model.map_draft_to_target(draft_ids)

        # Probabilistic sampling and rejection operate in target-vocabulary
        # space. A reduced draft vocabulary is scattered into its target rows.
        if self._d2t_scatter_index is not None:
            assert self._draft_scatter_buf is not None
            buf = self._draft_scatter_buf[: logits.shape[0]]
            buf.index_copy_(1, self._d2t_scatter_index, logits.to(buf.dtype))
            logits = buf

        # sample_pos is the predicted token's position P. Sampling keys a draw
        # by the position before the sampled token, P-1.
        sampler = (
            gumbel_sample
            if self.draft_watermarker is None
            else self.draft_watermarker.sample
        )
        return sampler(
            logits,
            idx_map,
            self.temperature,
            self.seeds,
            sample_pos - 1,
            apply_temperature=True,
            is_drafting=True,
            logits_cache=self.draft_logits,
            logits_cache_col=self._step_cols[step],
            use_fp64=self.use_fp64_gumbel,
        )

    def _sample_sequential(self, num_reqs: int, head_hidden: torch.Tensor) -> None:
        if self._c25_fused_sampler is not None:
            self._sample_sequential_c25(num_reqs, head_hidden)
            return
        if self._draft_topk is not None:
            self._sample_sequential_topk(num_reqs, head_hidden)
            return

        # Sequential Markov sampling over the backbone's output hidden states.
        n_spec = self.num_speculative_steps
        num_sample = num_reqs * n_spec
        # Per-(req, position) head hidden, ordered (req, step).
        sample_hidden = head_hidden[self.sample_indices[:num_sample]]
        # Draft-vocab logits; sampled ids are remapped to target vocab below.
        base_logits = self.model.compute_draft_logits(sample_hidden)
        vocab_size = base_logits.shape[-1]
        base_logits = base_logits.view(num_reqs, n_spec, vocab_size)

        idx_map = self.sample_idx_mapping[:num_sample].view(num_reqs, n_spec)
        sample_pos = self.sample_pos[:num_sample].view(num_reqs, n_spec)
        confidence_markov_embeds = []

        # Anchor (bonus) token per request = the input id at query offset 0,
        # read via the precomputed persistent index (fixed buffer for capture).
        prev = self.input_buffers.input_ids[self._anchor_idx[:num_reqs]]

        for i in range(n_spec):
            # Sequential stage: Markov bias from the previously sampled token.
            markov_embed = self.model.markov_embed(prev)
            if self.use_confidence_head:
                confidence_markov_embeds.append(markov_embed)
            bias = self.model.markov_bias(markov_embed)
            logits_i = base_logits[:, i] + bias
            draft_sampled_i = self._sample_logits(
                logits_i, idx_map[:, i], sample_pos[:, i], i
            )
            self.draft_tokens[:num_reqs, i] = draft_sampled_i
            prev = draft_sampled_i

        if self.use_confidence_head:
            confidence = self.model.compute_confidence(
                sample_hidden,
                torch.stack(confidence_markov_embeds, dim=1).flatten(0, 1),
            )
            self.draft_token_confidence_probs[:num_reqs] = confidence.view(
                num_reqs, n_spec
            )

    def _sample_sequential_c25(self, num_reqs: int, head_hidden: torch.Tensor) -> None:
        sampler = self._c25_fused_sampler
        assert sampler is not None and self.draft_logits is not None
        if num_reqs == 0:
            return
        n_spec = self.num_speculative_steps
        num_sample = num_reqs * n_spec
        # Keep the installed gather and full-vocabulary base projection.
        sample_hidden = head_hidden[self.sample_indices[:num_sample]]
        base_logits = self.model.compute_draft_logits(sample_hidden)
        base_logits = base_logits.view(num_reqs, n_spec, base_logits.shape[-1])
        idx_mapping = self.sample_idx_mapping[:num_sample]
        sample_pos = self.sample_pos[:num_sample]
        embed = sampler.embed_anchor(
            self.input_buffers.input_ids, self.num_query_per_req, num_reqs
        )
        for step in range(n_spec):
            # The installed model owns the unchanged bias GEMM/logits processor.
            bias = self.model.markov_bias(embed)
            sampler.sample_step(
                base_logits,
                bias,
                step,
                idx_mapping,
                sample_pos,
                self.temperature,
                self.seeds,
                self.draft_logits,
                self.draft_tokens,
            )

    def _sample_sequential_topk(self, num_reqs: int, head_hidden: torch.Tensor) -> None:
        """Apply the sequential Markov head only to top-k base-logit candidates.

        Candidate selection is done once for all draft positions. At each
        sequential step, the selected logits are corrected in place and every
        other entry is set to ``-inf``. The normal dense sampling and rejection
        paths then consume that truncated distribution unchanged.
        """
        assert self._draft_topk is not None
        n_spec = self.num_speculative_steps
        num_sample = num_reqs * n_spec
        sample_hidden = head_hidden[self.sample_indices[:num_sample]]
        base_logits = self.model.compute_draft_logits(sample_hidden)
        base_logits = base_logits.view(num_reqs, n_spec, -1)
        base_values, draft_indices = base_logits.topk(self._draft_topk, dim=-1)
        # Reuse the dense backbone output as the normal sampler's input. Fill
        # once for all positions, then scatter only the corrected candidates
        # during the sequential loop.
        base_logits.fill_(float("-inf"))
        idx_map = self.sample_idx_mapping[:num_sample].view(num_reqs, n_spec)
        sample_pos = self.sample_pos[:num_sample].view(num_reqs, n_spec)
        confidence_markov_embeds = []
        prev = self.input_buffers.input_ids[self._anchor_idx[:num_reqs]]

        for i in range(n_spec):
            markov_embed = self.model.markov_embed(prev)
            if self.use_confidence_head:
                confidence_markov_embeds.append(markov_embed)
            logits_i = self.model.apply_markov_bias_gathered(
                markov_embed,
                base_logits[:, i],
                base_values[:, i],
                draft_indices[:, i],
            )
            draft_sampled_i = self._sample_logits(
                logits_i, idx_map[:, i], sample_pos[:, i], i
            )
            self.draft_tokens[:num_reqs, i] = draft_sampled_i
            prev = draft_sampled_i

        if self.use_confidence_head:
            confidence = self.model.compute_confidence(
                sample_hidden,
                torch.stack(confidence_markov_embeds, dim=1).flatten(0, 1),
            )
            self.draft_token_confidence_probs[:num_reqs] = confidence.view(
                num_reqs, n_spec
            )

    def _generate_draft(
        self,
        num_reqs: int,
        num_tokens_padded: int,
        attn_metadata: dict[str, Any] | None,
        slot_mappings: dict[str, torch.Tensor] | None,
        num_tokens_across_dp: torch.Tensor | None,
        cudagraph_runtime_mode: CUDAGraphMode = CUDAGraphMode.NONE,
    ) -> None:
        # Full draft step (captured under CUDA graph): parallel backbone forward
        # then sequential Markov sampling over its hidden state outputs.
        head_hidden = self._run_model(
            num_tokens_padded,
            attn_metadata,
            slot_mappings,
            num_tokens_across_dp,
            cudagraph_runtime_mode,
        )
        self._sample_sequential(num_reqs, head_hidden)

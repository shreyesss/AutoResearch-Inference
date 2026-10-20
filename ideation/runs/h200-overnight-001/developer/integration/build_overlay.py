"""Build the narrow C25 native overlay from retained installed sources.

No imports of vLLM/Torch, GPU execution, or mutation of original serving files.
The existing qualified sampler and generic accessor are copied byte-for-byte.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEV = HERE.parent
REL = Path('vllm/v1/worker/gpu/spec_decode/dspark')
BASE = DEV / 'source' / REL / 'speculator.py'
QUALIFIED = DEV / 'candidate'
OUT = HERE / 'overlay'
SAMPLER_SHA = '7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9'
HELPER_SHA = '56d4be2b3e65ea93124f5e3edf0479054b966eeae0858a2b057a406678cc1de2'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new, 1)


original = BASE.read_text()
source = once(original, 'from typing import Any\n', 'from typing import Any\n\nimport json\n')
source = once(source, 'from vllm.logger import init_logger\n',
              'from vllm.logger import init_logger\nfrom vllm.platforms import current_platform\n')
source = once(source,
    'from vllm.v1.worker.gpu.spec_decode.dspark.utils import load_dspark_model\n',
    'from vllm.v1.worker.gpu.spec_decode.dspark.utils import load_dspark_model\n'
    'from vllm.v1.worker.gpu.spec_decode.dspark.c25_adapter import eligible_markov_embedding\n'
    'from vllm.v1.worker.gpu.spec_decode.dspark.c25_fused_sampler import DSparkFusedMarkovSampler\n')
source = once(source,
    '        self.use_confidence_head: bool = False\n',
    '        self.use_confidence_head: bool = False\n'
    '        self._c25_fused_sampler: DSparkFusedMarkovSampler | None = None\n'
    '        self._c25_activation: dict[str, Any] = {"active": False, "reason": "not_loaded"}\n')
load_override = '''    def load_model(self, target_model: torch.nn.Module) -> None:
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

'''
source = once(source, '    def load_draft_model(\n', load_override + '    def load_draft_model(\n')
source = once(source,
    '    def _sample_sequential(self, num_reqs: int, head_hidden: torch.Tensor) -> None:\n',
    '    def _sample_sequential(self, num_reqs: int, head_hidden: torch.Tensor) -> None:\n'
    '        if self._c25_fused_sampler is not None:\n'
    '            self._sample_sequential_c25(num_reqs, head_hidden)\n'
    '            return\n')
fused_wrapper = '''    def _sample_sequential_c25(self, num_reqs: int, head_hidden: torch.Tensor) -> None:
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

'''
source = once(source, '    def _sample_sequential_topk(', fused_wrapper + '    def _sample_sequential_topk(')

(OUT / REL).mkdir(parents=True, exist_ok=True)
(OUT / REL / 'speculator.py').write_text(source)
for filename, target, expected in [
    ('fused_sampler.py', 'c25_fused_sampler.py', SAMPLER_SHA),
    ('adapter.py', 'c25_adapter.py', HELPER_SHA),
]:
    content = (QUALIFIED / filename).read_bytes()
    assert sha(content) == expected
    (OUT / REL / target).write_bytes(content)

files = []
for p in sorted(OUT.rglob('*.py')):
    ast.parse(p.read_text())
    rel = p.relative_to(OUT)
    files.append({'path': str(rel), 'source': str(p),
                  'destination': '/usr/local/lib/python3.12/dist-packages/' + str(rel),
                  'sha256': sha(p.read_bytes()), 'readonly': True,
                  'base_sha256': sha(BASE.read_bytes()) if p.name == 'speculator.py' else None})
(HERE/'integration.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), source.splitlines(True),
    fromfile='installed/' + str(REL/'speculator.py'),
    tofile='overlay/' + str(REL/'speculator.py'))))
(HERE/'manifest.json').write_text(json.dumps({
    'scope': 'C25 native integration overlay only; no service launch',
    'qualified_sampler_sha256': SAMPLER_SHA, 'qualified_helper_sha256': HELPER_SHA,
    'base_image': 'vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c',
    'files': files, 'static_validation': 'All Python files AST parse; no runtime/GPU validation claimed',
}, indent=2)+'\n')
print(json.dumps({'files': files, 'static_validation': 'AST parses'}, indent=2))

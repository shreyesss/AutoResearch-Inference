"""Guarded generic table accessor; no specialized decoder dependency.

This is a proposed service integration boundary, not mounted into the service.
The component harness directly supplies the attested real checkpoint table.
"""
import torch
from vllm.model_executor.layers.vocab_parallel_embedding import UnquantizedEmbeddingMethod


def eligible_markov_embedding(speculator, *, tensor_parallel_size: int):
    """Return existing embedding storage only for the qualified narrow path.

    Returning None means run the unchanged installed sampling loop. Guards are
    metadata-only and perform no device synchronization or copy.
    """
    if tensor_parallel_size != 1 or speculator.num_speculative_steps != 5:
        return None
    if speculator.enable_adaptive_verification:
        return None
    if speculator.draft_watermarker is not None or speculator._draft_topk is not None:
        return None
    if speculator._d2t_scatter_index is not None or speculator.draft_logits is None:
        return None
    model = speculator.model
    if getattr(model, 'draft_id_to_target_id', None) is not None:
        return None
    markov = getattr(getattr(model, 'model', None), 'markov_head', None)
    embedding = getattr(markov, 'markov_w1', None)
    if not isinstance(embedding, torch.nn.Embedding):
        return None
    weight = embedding.weight
    if not weight.is_cuda or weight.dtype != torch.bfloat16 or weight.ndim != 2:
        return None
    vocab_size = speculator.vocab_size
    if weight.shape[0] != vocab_size or weight.stride(1) != 1:
        return None
    head = getattr(markov, "markov_w2", None)
    if not isinstance(getattr(head, "quant_method", None), UnquantizedEmbeddingMethod):
        return None
    if head.weight.dtype != torch.bfloat16 or head.weight.shape != weight.shape:
        return None
    cache = speculator.draft_logits
    if cache.shape[-1] != vocab_size or cache.dtype != torch.bfloat16:
        return None
    processor = getattr(model, 'logits_processor', None)
    if processor is None or processor.scale != 1.0 or processor.soft_cap is not None:
        return None
    if processor.logits_as_input or processor.org_vocab_size != vocab_size:
        return None
    if processor.head_dtype != torch.bfloat16:
        return None
    return weight

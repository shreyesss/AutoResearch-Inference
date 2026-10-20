"""Independent C25 native proposal observer; imported identically by both arms.

Only Python metadata is added during capture. The bounded startup fixture uses
installed dummy execution, installed CUDA-event collection, and an independently
mounted installed sampler function. No trace-clock inference or service claim.
"""
from __future__ import annotations
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time

LOGICAL = (1, 2, 4, 5)
EXPECTED_DRAFT = (1, 2, 4, 7)
ANCHORS = (671, 2581, 3967, 10059, 678)
REFERENCE_SHA256 = '97bcfaa655c6d4a5ecdfb17ab87b80547e8216b9d15a91c341798ebbb558f146'
_CAPTURE = {}
_CAPTURE_ENABLED = False


def enabled():
    return bool(os.environ.get('C25_NATIVE_RUN_ID'))


def disable_capture():
    global _CAPTURE_ENABLED
    _CAPTURE_ENABLED = False
    _CAPTURE.clear()


def begin_capture(runner, *, profile_only):
    global _CAPTURE_ENABLED
    _CAPTURE_ENABLED = enabled() and not profile_only
    _CAPTURE.clear()


def descriptor(desc):
    result = dataclasses.asdict(desc)
    result['cg_mode'] = desc.cg_mode.name
    return result


def tensor_info(value):
    return {'shape': list(value.shape), 'dtype': str(value.dtype),
            'device': str(value.device), 'data_ptr': value.data_ptr()}


@contextlib.contextmanager
def observe_sampling(spec, num_reqs, num_tokens, head_hidden):
    """Witness actual five sampler calls in the captured function, not eligibility."""
    import torch
    if not _CAPTURE_ENABLED or not torch.cuda.is_current_stream_capturing():
        yield
        return
    fused = getattr(spec, '_c25_fused_sampler', None)
    owner, name, step_index = (fused, 'sample_step', 2) if fused is not None else (spec, '_sample_logits', 3)
    had_instance = name in vars(owner)
    old_instance = vars(owner).get(name)
    original = getattr(owner, name)
    steps = []
    def witnessed(*args, **kwargs):
        step = kwargs['step'] if 'step' in kwargs else args[step_index]
        steps.append(int(step))
        return original(*args, **kwargs)
    setattr(owner, name, witnessed)
    try:
        yield
    finally:
        if had_instance:
            setattr(owner, name, old_instance)
        else:
            delattr(owner, name)
    record = {'num_reqs': int(num_reqs), 'num_tokens': int(num_tokens),
              'head': head_hidden, 'head_info': tensor_info(head_hidden),
              'branch': 'fused' if fused is not None else 'installed',
              'sample_steps': steps, 'sampler_object_id': id(owner),
              'capturing': True}
    key = (int(num_reqs), int(num_tokens))
    records = _CAPTURE.setdefault(id(spec), {})
    if key in records:
        raise AssertionError('ambiguous captured head reference for request/token shape')
    records[key] = record


def _atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def _bytes_equal(a, b):
    import torch
    return torch.equal(a.contiguous().view(torch.uint8), b.contiguous().view(torch.uint8))


def _original_sampler():
    path = Path('/opt/c25-native/reference_dspark.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != REFERENCE_SHA256:
        raise AssertionError('original installed sampler source hash mismatch')
    module_spec = importlib.util.spec_from_file_location('_c25_original_dspark', path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module.DSparkSpeculator._sample_sequential


def _guard(runner, spec, arm):
    import torch
    from vllm.model_executor.layers.vocab_parallel_embedding import UnquantizedEmbeddingMethod
    model_type = type(spec.model)
    markov = spec.model.model.markov_head
    embedding = markov.markov_w1
    head = markov.markov_w2
    processor = spec.model.logits_processor
    checks = {
        'class': model_type.__module__ == 'vllm.models.deepseek_v41.nvidia.dspark' and model_type.__name__ == 'DSparkDeepseekV4ForCausalLM',
        'sm90': torch.cuda.get_device_capability(runner.device) == (9, 0),
        'target_tp1': spec.vllm_config.parallel_config.tensor_parallel_size == 1,
        'draft_tp1': spec.speculative_config.draft_parallel_config.tensor_parallel_size == 1,
        'k5_anchor5': spec.num_speculative_steps == 5 and spec.num_query_per_req == 5 and spec.sample_from_anchor,
        'watermark_absent': spec.vllm_config.watermark_config is None and spec.draft_watermarker is None,
        'ordinary': spec._draft_topk is None and spec._d2t_scatter_index is None and spec.model.draft_id_to_target_id is None,
        'no_av': runner.adaptive_verification is None and not spec.enable_adaptive_verification and spec.acceptance_estimator is None and not spec.use_confidence_head,
        'no_lora': spec.vllm_config.lora_config is None,
        'cache': spec.draft_logits is not None and spec.draft_logits.dtype == torch.bfloat16 and tuple(spec.draft_logits.shape) == (64, 5, 129280),
        'markov_embedding': isinstance(embedding, torch.nn.Embedding) and tuple(embedding.weight.shape) == (129280,256) and embedding.weight.dtype == torch.bfloat16,
        'markov_projection': isinstance(head.quant_method, UnquantizedEmbeddingMethod) and head.weight.dtype == torch.bfloat16 and tuple(head.weight.shape) == (129280,256),
        'logits_processor': processor.scale == 1.0 and processor.soft_cap is None and not processor.logits_as_input and processor.org_vocab_size == 129280 and processor.head_dtype == torch.bfloat16,
        'capacity64': runner.max_num_reqs == spec.max_num_reqs == 64,
        'no_requests': not runner.req_states.req_id_to_index,
        'collector_inactive': not runner.step_timing._collecting and not runner.step_timing._timed and runner.step_timing._step is None,
        'branch': (getattr(spec, '_c25_fused_sampler', None) is not None) == (arm == 'B'),
    }
    if not all(checks.values()):
        raise AssertionError(f'native applicability failed: {checks}')
    return checks


def run_native(runner):
    global _CAPTURE_ENABLED
    if not enabled():
        return
    import numpy as np
    import torch
    from vllm.v1.worker.workspace import use_workspace_lane
    # Import location is verified against the mounted model_runner source by builder.
    spec = runner.speculator
    arm = os.environ['C25_NATIVE_ARM']
    replica = int(os.environ['C25_NATIVE_REPLICA'])
    rank = int(spec.dp_rank)
    path = Path(os.environ['C25_NATIVE_OUTPUT']) / f'replica{replica}' / f'rank{rank}.json'
    if path.exists():
        raise AssertionError('refusing to overwrite native rank evidence')
    started = time.monotonic()
    receipt = {'schema_version': 1, 'run_id': os.environ['C25_NATIVE_RUN_ID'],
               'arm': arm, 'replica': replica, 'rank': rank, 'status': 'running',
               'restored': False, 'native_oracle_passed': False,
               'capture_attestation_passed': False, 'timed_samples': 0,
               'started_unix_s': time.time(), 'pid': os.getpid(),
               'pid_start_ticks': int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]),
               'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'reference_sha256': REFERENCE_SHA256, 'oracles': [], 'samples': [],
               'scope': 'controlled padded native draft-proposal proxy; excludes rejection, accepted-token progress, production context, queueing and ITL'}
    _atomic(path.with_name(f'rank{rank}.started.json'), {k: receipt[k] for k in ('schema_version', 'run_id', 'arm', 'replica', 'rank', 'started_unix_s', 'pid', 'pid_start_ticks')})
    saved_tensors, saved_uva, wrappers = [], [], []
    original_collector_batch = runner.step_timing._batch
    try:
        with torch.inference_mode():
            receipt['guards'] = _guard(runner, spec, arm)
            receipt['activation'] = getattr(spec, '_c25_activation', {'active': False, 'branch': 'installed'})
            receipt['device'] = {'name': torch.cuda.get_device_name(runner.device),
                                 'index': torch.cuda.current_device(),
                                 'uuid': str(torch.cuda.get_device_properties(runner.device).uuid),
                                 'stream': torch.cuda.current_stream().cuda_stream}
            receipt['gpu_uuid'] = receipt['device']['uuid']
            receipt['use_fp64_gumbel'] = spec.use_fp64_gumbel
            receipt['cache'] = tensor_info(spec.draft_logits)
            receipt['embedding'] = tensor_info(spec.model.model.markov_head.markov_w1.weight)
            receipt['projection'] = tensor_info(spec.model.model.markov_head.markov_w2.weight)
            receipt['gemm_environment'] = {k: os.environ.get(k) for k in ('VLLM_BATCH_INVARIANT', 'VLLM_UNQUANTIZED_GEMM_BACKEND')}
            original = _original_sampler()
            captures = _CAPTURE.get(id(spec), {})
            receipt['captures'] = []
            capture_by_graph = {}
            for desc, graph in spec.query_cudagraph_manager.graphs.items():
                key = (desc.num_reqs, desc.num_tokens)
                if key not in captures:
                    raise AssertionError(f'captured graph lacks sampler witness: {desc}')
                cap = captures[key]
                if cap['sample_steps'] != list(range(5)) or cap['branch'] != ('fused' if arm == 'B' else 'installed'):
                    raise AssertionError('captured branch or five-call witness mismatch')
                if key in capture_by_graph:
                    raise AssertionError('multiple graph descriptors share ambiguous head reference')
                capture_by_graph[key] = (desc, graph, cap)
                receipt['captures'].append(dict(descriptor=descriptor(desc), graph_object_id=id(graph),
                    **{k: v for k, v in cap.items() if k != 'head'}))
            receipt['capture_attestation_passed'] = bool(capture_by_graph)
            seen = set()
            def save_tensor(label, tensor):
                if isinstance(tensor, torch.Tensor) and id(tensor) not in seen:
                    seen.add(id(tensor)); saved_tensors.append((label, tensor, tensor.clone()))
            # Persistent state explicitly touched by setup or the native sampler.
            for label in ('last_sampled_tokens', 'next_prefill_tokens'):
                save_tensor('requests.' + label, getattr(runner.req_states, label))
            for label in ('temperature', 'seeds'):
                uva = getattr(runner.sampler.sampling_states, label)
                saved_uva.append((label, uva, uva.np.copy()))
            for label in ('draft_logits', 'draft_tokens', 'temperature', 'seeds', 'sample_indices', 'sample_pos', 'sample_idx_mapping'):
                save_tensor('speculator.' + label, getattr(spec, label))
            for prefix, buffers in (('target', runner.input_buffers), ('draft', spec.input_buffers)):
                for label, value in vars(buffers).items():
                    if isinstance(value, torch.Tensor):
                        save_tensor(prefix + '.' + label, value)
            if getattr(spec, '_c25_fused_sampler', None) is not None:
                for label in ('markov_embed', 'partial_max', 'partial_idx', 'counter'):
                    save_tensor('fused.' + label, getattr(spec._c25_fused_sampler, label))
            receipt['restoration_inventory'] = [x[0] for x in saved_tensors] + ['sampling_uva.' + x[0] for x in saved_uva]
            state = runner.sampler.sampling_states
            state.temperature.np.fill(1.0)
            state.seeds.np[:] = np.arange(64, dtype=np.int64) + 731
            state.temperature.copy_to_uva(); state.seeds.copy_to_uva()
            anchors = torch.tensor([ANCHORS[i % len(ANCHORS)] for i in range(64)], device=runner.device, dtype=runner.req_states.last_sampled_tokens.dtype)
            runner.req_states.last_sampled_tokens.copy_(anchors[:, None])
            runner.req_states.next_prefill_tokens.copy_(anchors)
            observed = {}
            for role, manager in (('target', runner.cudagraph_manager), ('draft', spec.query_cudagraph_manager)):
                had_instance = 'run_fullgraph' in vars(manager)
                old_instance = vars(manager).get('run_fullgraph')
                old_method = manager.run_fullgraph
                def wrapped(desc, *args, _role=role, _manager=manager, _old=old_method, **kwargs):
                    observed[_role] = {'descriptor': descriptor(desc), 'graph_object_id': id(_manager.graphs[desc])}
                    return _old(desc, *args, **kwargs)
                manager.run_fullgraph = wrapped
                wrappers.append((manager, had_instance, old_instance))
            def cycle(n):
                if time.monotonic() - started > 480:
                    raise TimeoutError('native collection exceeded eight-minute cap')
                observed.clear()
                runner._dummy_run(num_tokens=n * 6, uniform_decode=True, context_len=0,
                    is_profile=False, skip_attn=False, valid_dummy_state_slots=True)
                if set(observed) != {'target', 'draft'} or any(v['descriptor']['cg_mode'] != 'FULL' for v in observed.values()):
                    raise AssertionError('native cycle did not replay both FULL graphs')
                return json.loads(json.dumps(observed))
            def oracle(n, phase):
                # Sentinel writes are outside timing. Finite active writes and bytewise
                # inactive preservation distinguish a replay from stale output reuse.
                spec.draft_logits.fill_(float('nan'))
                spec.draft_tokens.fill_(-919191)
                before_cache = spec.draft_logits.clone()
                before_tokens = spec.draft_tokens.clone()
                dispatch = cycle(n)
                torch.cuda.synchronize()
                dd = dispatch['draft']['descriptor']
                count = dd['num_reqs']; key = (count, dd['num_tokens'])
                desc, graph, cap = capture_by_graph[key]
                if descriptor(desc) != dd or id(graph) != dispatch['draft']['graph_object_id']:
                    raise AssertionError('native replay graph differs from captured witness')
                mapping = spec.sample_idx_mapping[:count*5].reshape(count, 5)
                pos = spec.sample_pos[:count*5].reshape(count, 5)
                indices = spec.sample_indices[:count*5]
                valid = mapping[:, 0] >= 0
                if not torch.equal(mapping, mapping[:, :1].expand_as(mapping)):
                    raise AssertionError('state mapping changes across five steps')
                active = mapping[valid, 0].long()
                if active.numel() != dispatch['target']['descriptor']['num_reqs'] or active.unique().numel() != active.numel() or bool((active >= 64).any()):
                    raise AssertionError('actual mapping does not identify unique rounded target rows')
                if not torch.equal(active, torch.arange(active.numel(), device=active.device)):
                    raise AssertionError('dummy mapping is not the installed dense order')
                if not bool((spec.temperature[active] == 1).all()) or not torch.equal(spec.seeds[active], active + 731):
                    raise AssertionError('prepared temperature/seeds mismatch')
                if not torch.equal(spec.input_buffers.input_ids[spec._anchor_idx[:count]][valid], anchors[active]):
                    raise AssertionError('prepared anchors mismatch')
                native_cache = spec.draft_logits.clone(); native_tokens = spec.draft_tokens.clone()
                inactive = torch.ones(64, dtype=torch.bool, device=runner.device); inactive[active] = False
                if not bool(torch.isfinite(native_cache[active]).all()) or not _bytes_equal(native_cache[inactive], before_cache[inactive]):
                    raise AssertionError('nonfinite active cache or inactive cache mutation')
                if not _bytes_equal(native_tokens[count:], before_tokens[count:]):
                    raise AssertionError('out-of-batch draft-token mutation')
                ids = native_tokens[:count][valid]
                if not bool(((ids >= 0) & (ids < spec.vocab_size)).all()):
                    raise AssertionError('invalid native active token IDs')
                for repeat in range(2):
                    with use_workspace_lane(runner._draft_workspace_lane):
                        original(spec, count, cap['head'])
                    torch.cuda.synchronize()
                    if not torch.equal(spec.draft_tokens[:count][valid], ids) or not torch.equal(spec.draft_logits[active], native_cache[active]):
                        raise AssertionError(f'exact original-reference mismatch at repeat {repeat}')
                    if not _bytes_equal(spec.draft_logits[inactive], native_cache[inactive]):
                        raise AssertionError('original reference altered inactive rows')
                fused = getattr(spec, '_c25_fused_sampler', None)
                if fused is not None and bool((fused.counter != 0).any()):
                    raise AssertionError('fused scratch counter leaked')
                spec.draft_logits.copy_(native_cache); spec.draft_tokens.copy_(native_tokens)
                row = {'phase': phase, 'logical_requests': n, 'dispatch': dispatch,
                       'active_state_rows': active.cpu().tolist(), 'mapping': mapping.cpu().tolist(),
                       'sample_positions': pos.cpu().tolist(), 'sample_indices': indices.cpu().tolist(),
                       'temperature': spec.temperature[active].cpu().tolist(), 'seeds': spec.seeds[active].cpu().tolist(),
                       'tokens': ids.cpu().tolist(), 'head': cap['head_info'],
                       'exact_tokens': True, 'exact_finite_cache': True, 'reference_repeat': True,
                       'inactive_rows_preserved': True, 'counters_zero': True,
                       'active_cache_write_witness': 'NaN sentinel replaced by finite native cache',
                       'intended_shape_covered': count == EXPECTED_DRAFT[LOGICAL.index(n)]}
                receipt['oracles'].append(row)
            for n in LOGICAL:
                oracle(n, 'before')
                for _ in range(8): cycle(n)
            for round_index in range(30):
                order = list(LOGICAL[round_index % 4:] + LOGICAL[:round_index % 4])
                if round_index % 2: order.reverse()
                for n in order:
                    dispatches = []
                    with runner.step_timing.collect() as times:
                        for _ in range(8): dispatches.append(cycle(n))
                    if len(times) != 8:
                        raise AssertionError('missing native timing samples')
                    for cycle_index, (timing, dispatch) in enumerate(zip(times, dispatches)):
                        row = dataclasses.asdict(timing)
                        if not row['full_cudagraph'] or any(not math.isfinite(row[k]) or row[k] <= 0 for k in ('forward_ms', 'drafter_ms')):
                            raise AssertionError('invalid native event duration or graph mode')
                        receipt['samples'].append(dict(round=round_index, logical_requests=n, cycle=cycle_index,
                            dispatch=dispatch, stream=torch.cuda.current_stream().cuda_stream, **row))
            for n in LOGICAL: oracle(n, 'after')
            receipt['native_oracle_passed'] = len(receipt['oracles']) == 8
            receipt['timed_samples'] = len(receipt['samples'])
            if receipt['timed_samples'] != 960:
                raise AssertionError('fixed timing inventory incomplete')
            receipt['status'] = 'passed'
    except BaseException as exc:
        receipt.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            with torch.inference_mode():
                for manager, had_instance, old_instance in reversed(wrappers):
                    if had_instance: manager.run_fullgraph = old_instance
                    else: delattr(manager, 'run_fullgraph')
                for _, tensor, backup in reversed(saved_tensors): tensor.copy_(backup)
                for _, uva, backup in saved_uva:
                    uva.np[:] = backup; uva.copy_to_uva()
                # Original warmup initialization: null state block is zeroed; normal
                # request allocation initializes newly admitted state blocks itself.
                if runner.kv_block_zeroer is not None:
                    runner.kv_block_zeroer.zero_block_ids([0])
                torch.cuda.synchronize()
                checks = {label: _bytes_equal(tensor, backup) for label, tensor, backup in saved_tensors}
                checks.update({'uva.' + label: uva.np.tobytes() == backup.tobytes() for label, uva, backup in saved_uva})
                checks['no_registered_requests'] = not runner.req_states.req_id_to_index
                runner.step_timing._batch = original_collector_batch
                checks['collector_inactive'] = not runner.step_timing._collecting and not runner.step_timing._timed and runner.step_timing._step is None
                checks['no_execute_state'] = runner.execute_model_state is None
                receipt['restore_checks'] = checks
                receipt['restored'] = all(checks.values())
                if not receipt['restored']:
                    receipt.update(status='failed', restoration_error='persistent state restoration check failed')
        except BaseException as exc:
            receipt.update(status='failed', restored=False, restoration_error=f'{type(exc).__name__}: {exc}')
        receipt['elapsed_s'] = time.monotonic() - started
        receipt['ended_unix_s'] = time.time()
        disable_capture()
        _atomic(path, receipt)
        if receipt['status'] != 'passed' or not receipt['restored']:
            raise RuntimeError(f'C25 native fixture failed; retained receipt {path}')

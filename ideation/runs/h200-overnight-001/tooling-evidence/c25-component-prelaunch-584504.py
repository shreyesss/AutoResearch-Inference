#!/usr/bin/env python3
"""Independent real-weight C25 reference, adversarial fixtures, paired graph timing."""
import argparse
import hashlib
import importlib.util
import inspect
import json
import math
import os
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

SIZES = [1, 2, 4, 5, 7, 16, 32, 64]
STEPS, STATES, MAX_BATCH, VOCAB, RANK = 5, 72, 64, 129280, 256
SEED = 20261020


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--model', type=Path, default=Path('/model'))
    ap.add_argument('--candidate', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'running', 'start_ns': time.time_ns(), 'script_sha256': sha(__file__),
        'candidate_sha256': sha(args.candidate), 'fixtures': [], 'negative_controls': [], 'timing': []}
    def save():
        (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    save()
    try:
        import numpy as np
        import torch
        import triton
        from safetensors import safe_open
        from vllm import envs
        from vllm.model_executor.layers.vocab_parallel_embedding import UnquantizedEmbeddingMethod
        from vllm.model_executor.layers.utils import dispatch_unquantized_gemm
        from vllm.v1.worker.gpu.sample.gumbel import gumbel_sample
        if torch.cuda.device_count() != 1:
            raise RuntimeError('exactly one visible CUDA device required')
        if envs.VLLM_BATCH_INVARIANT:
            raise RuntimeError('unexpected batch-invariant mode')
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        torch.set_grad_enabled(False)
        spec = importlib.util.spec_from_file_location('c25_candidate', args.candidate)
        candidate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate_module)
        sampler_class = candidate_module.DSparkFusedMarkovSampler
        source_functions = [gumbel_sample, UnquantizedEmbeddingMethod.apply, dispatch_unquantized_gemm]
        result['environment'] = {'torch': str(torch.__version__), 'cuda': torch.version.cuda, 'triton': str(triton.__version__),
            'gpu_name': torch.cuda.get_device_name(0), 'gpu_uuid': str(getattr(torch.cuda.get_device_properties(0), 'uuid', 'not_exposed')),
            'batch_invariant': envs.VLLM_BATCH_INVARIANT, 'gemm_dispatch': dispatch_unquantized_gemm().__name__,
            'float32_matmul_precision': torch.get_float32_matmul_precision(), 'allow_tf32': torch.backends.cuda.matmul.allow_tf32,
            'installed_sources': [{'path': inspect.getfile(f), 'sha256': sha(inspect.getfile(f))} for f in source_functions]}
        shard = args.model / 'model-00046-of-00048.safetensors'
        with shard.open('rb') as f:
            header_size = int.from_bytes(f.read(8), 'little'); header = f.read(header_size)
        keys = ['mtp.2.markov_head.embed.weight', 'mtp.2.markov_head.head.weight']
        weights = []
        result['weights'] = []
        with safe_open(str(shard), framework='pt', device='cpu') as f:
            for key in keys:
                tensor = f.get_tensor(key)
                if tensor.shape != (VOCAB, RANK) or tensor.dtype != torch.bfloat16 or not torch.isfinite(tensor).all().item():
                    raise RuntimeError('unexpected checkpoint Markov weight')
                result['weights'].append({'key': key, 'shape': list(tensor.shape), 'dtype': str(tensor.dtype),
                    'tensor_bytes_sha256': hashlib.sha256(tensor.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()})
                weights.append(tensor)
        result['checkpoint_header_sha256'] = hashlib.sha256(header).hexdigest()
        stream = torch.cuda.Stream()
        with torch.cuda.stream(stream):
            embed_weight, head_weight = [w.cuda() for w in weights]
            layer = SimpleNamespace(weight=head_weight)
            projection = UnquantizedEmbeddingMethod()
            cols = torch.arange(STEPS, dtype=torch.int32, device='cuda')
            anchor_indices = torch.arange(MAX_BATCH, dtype=torch.int64, device='cuda') * STEPS
            scratch = {fp: sampler_class(MAX_BATCH, VOCAB, embed_weight, fp) for fp in (False, True)}
            def exact(a, b, label):
                if a.shape != b.shape or a.dtype != b.dtype:
                    raise AssertionError(f'{label}: shape/dtype mismatch {a.shape}/{a.dtype} vs {b.shape}/{b.dtype}')
                equal = (a == b)
                if a.is_floating_point():
                    equal = equal | (torch.isnan(a) & torch.isnan(b))
                if not bool(equal.all().item()):
                    index = tuple(int(x) for x in (~equal).nonzero()[0].tolist())
                    raise AssertionError(f'{label}: first mismatch {index}; observed={a[index].item()} expected={b[index].item()}')
            def assert_zero(s):
                if bool((s.counter != 0).any().item()):
                    raise AssertionError('nonzero arrival counter; no candidate launch permitted')
            def buffers(native_layout=False):
                if native_layout:
                    return {'cache': torch.full((MAX_BATCH, STEPS, VOCAB), -123, dtype=torch.bfloat16, device='cuda'),
                        'tokens': torch.full((MAX_BATCH, STEPS), -777, dtype=torch.int64, device='cuda')}
                return {'cache': torch.full((STATES, STEPS + 1, VOCAB + 7), -123, dtype=torch.bfloat16, device='cuda'),
                    'tokens': torch.full((MAX_BATCH + 2, STEPS + 1), -777, dtype=torch.int64, device='cuda')}
            def make_inputs(n, mapping='dense', temp=1.0):
                base = torch.randn((n, STEPS, VOCAB), device='cuda', dtype=torch.float32).to(torch.bfloat16)
                anchors = torch.randint(VOCAB, (MAX_BATCH * STEPS,), dtype=torch.int64, device='cuda')
                known = torch.tensor([0, VOCAB - 1, 1023, 1024, 2047, 2048, 129024], dtype=torch.int64, device='cuda')
                anchors[torch.arange(min(n, len(known)), device='cuda') * STEPS] = known[:min(n, len(known))]
                state = torch.arange(n, dtype=torch.int32, device='cuda')
                if mapping != 'dense':
                    state = (state * 17 + 3) % STATES
                if mapping == 'padded':
                    state[torch.arange(n, device='cuda') % 3 == 0] = -1
                idx = state[:, None].expand(n, STEPS).clone().reshape(-1)
                pos = torch.tensor([1, 128, 8192, 32], dtype=torch.int64, device='cuda').repeat((n + 3) // 4)[:n, None]
                pos = (pos + torch.arange(STEPS, device='cuda')).reshape(-1)
                temperatures = torch.full((STATES,), temp, dtype=torch.float32, device='cuda')
                if n > 1 and temp == -1:
                    temperatures.copy_(torch.tensor([0., .7, 1., 1.3], device='cuda').repeat(STATES // 4))
                seeds = torch.tensor([0, 1, (1 << 32) + 19, -7], dtype=torch.int64, device='cuda').repeat(STATES // 4)
                return dict(n=n, base=base, anchors=anchors, idx=idx, pos=pos, temperatures=temperatures, seeds=seeds)
            def reference(x, out, fp, changed_seed=False, collect_embeds=False):
                n = x['n']
                if not n:
                    return []
                prev = x['anchors'][anchor_indices[:n]]
                embeds = []
                idx, pos = x['idx'].view(n, STEPS), x['pos'].view(n, STEPS)
                for step in range(STEPS):
                    embedding = torch.nn.functional.embedding(prev, embed_weight)
                    bias = projection.apply(layer, embedding)
                    logits = x['base'][:, step] + bias
                    seeds = x['seeds'] + step * 104729 if changed_seed and step else x['seeds']
                    prev = gumbel_sample(logits, idx[:, step], x['temperatures'], seeds, pos[:, step] - 1,
                        apply_temperature=True, is_drafting=True, logits_cache=out['cache'], logits_cache_col=cols[step], use_fp64=fp)
                    out['tokens'][:n, step] = prev
                    if collect_embeds:
                        embeds.append(torch.nn.functional.embedding(prev, embed_weight))
                return embeds
            def candidate(x, out, fp, check_steps=False, expected_embeds=None):
                n, s = x['n'], scratch[fp]
                if not n:
                    s.embed_anchor(x['anchors'], STEPS, 0)
                    return
                embedding = s.embed_anchor(x['anchors'], STEPS, n)
                for step in range(STEPS):
                    bias = projection.apply(layer, embedding)
                    s.sample_step(x['base'], bias, step, x['idx'], x['pos'], x['temperatures'], x['seeds'], out['cache'], out['tokens'])
                    embedding = s.markov_embed[:n]
                    if check_steps:
                        assert_zero(s)
                        if step + 1 < STEPS:
                            exact(embedding, expected_embeds[step], f'next embedding at step {step}')
            def compare(actual, expected, label):
                exact(actual['tokens'], expected['tokens'], label + ' tokens and sentinels')
                exact(actual['cache'], expected['cache'], label + ' cache and sentinels')
            def run_case(label, x, fp):
                expected, repeat, actual = buffers(), buffers(), buffers()
                embeds = reference(x, expected, fp, collect_embeds=True)
                reference(x, repeat, fp)
                compare(repeat, expected, label + ' baseline repeat')
                assert_zero(scratch[fp])
                candidate(x, actual, fp, True, embeds)
                compare(actual, expected, label)
                result['fixtures'].append({'label': label, 'n': x['n'], 'use_fp64': fp, 'status': 'pass', 'exact_tokens_cache_embeddings_sentinels': True})
                save()
                return expected
            # Full-vocabulary real-weight five-step fixtures, including native and guard shapes.
            for fp in (False, True):
                for n in SIZES:
                    for mapping in ('dense', 'permuted', 'padded'):
                        for temp in ([0., .7, 1., 1.3] if n == 1 else [-1.]):
                            x = make_inputs(n, mapping, temp)
                            run_case(f'real_weight_b{n}_{mapping}_temp{temp}_fp64{fp}', x, fp)
                x = make_inputs(0)
                before, after = buffers(), buffers()
                candidate(x, after, fp)
                compare(after, before, 'zero-active no-op')
                assert_zero(scratch[fp])
                result['fixtures'].append({'label': f'zero_active_fp64{fp}', 'status': 'pass'})
            # Low-level arithmetic/argmax stress independently controls base and bias.
            for fp in (False, True):
                s = scratch[fp]
                for case in ('all_equal', 'tie_inside_block', 'tie_across_blocks', 'last_valid', 'round_boundary', 'nan_early', 'nan_late'):
                    x = make_inputs(1, 'permuted', 0.)
                    x['base'].fill_(-100.)
                    bias = torch.zeros((1, VOCAB), dtype=torch.bfloat16, device='cuda')
                    forced = None
                    if case == 'all_equal': x['base'].zero_(); forced = 0
                    if case == 'tie_inside_block': x['base'][0, 0, [7, 19]] = 10.; forced = 7
                    if case == 'tie_across_blocks': x['base'][0, 0, [1023, 1024]] = 10.; forced = 1023
                    if case == 'last_valid': x['base'][0, 0, VOCAB - 1] = 10.; forced = VOCAB - 1
                    if case == 'round_boundary':
                        x['base'][0, 0, 1023] = 1.; bias[0, 1023] = 0.00390625
                        x['base'][0, 0, 1024] = 1.; bias[0, 1024] = 0.0078125
                        forced = 1024
                    if case == 'nan_early': x['base'][0, 0, 7] = float('nan')
                    if case == 'nan_late': x['base'][0, 0, VOCAB - 1] = float('nan')
                    expected, actual = buffers(), buffers()
                    logits = x['base'][:, 0] + bias
                    token = gumbel_sample(logits, x['idx'].view(1, STEPS)[:, 0], x['temperatures'], x['seeds'], x['pos'].view(1, STEPS)[:, 0] - 1,
                        apply_temperature=True, is_drafting=True, logits_cache=expected['cache'], logits_cache_col=cols[0], use_fp64=fp)
                    expected['tokens'][0, 0] = token[0]
                    if forced is not None and int(token.item()) != forced:
                        raise AssertionError(f'independent greedy oracle {case} disagrees with baseline')
                    s.sample_step(x['base'], bias, 0, x['idx'], x['pos'], x['temperatures'], x['seeds'], actual['cache'], actual['tokens'])
                    compare(actual, expected, case)
                    exact(s.markov_embed[:1], embed_weight[token], case + ' embedding')
                    assert_zero(s)
                    result['fixtures'].append({'label': case, 'use_fp64': fp, 'nonfinite_stress': case.startswith('nan'), 'status': 'pass'})
                    save()
            # Mutants are evaluator controls, isolated from normal results and timing.
            def rejected(name, fn):
                try: fn()
                except AssertionError as exc:
                    result['negative_controls'].append({'name': name, 'rejected': True, 'reason': str(exc)})
                    save(); return
                raise AssertionError('negative control was not rejected: ' + name)
            x = make_inputs(5, 'permuted', 1.)
            good, wrong = buffers(), buffers()
            reference(x, good, False); reference(x, wrong, False, changed_seed=True)
            rejected('changed_seed_after_step_zero', lambda: compare(wrong, good, 'wrong step seed'))
            wrong = {k: v.clone() for k, v in good.items()}; wrong['cache'].copy_(good['cache'].roll(1, 0))
            rejected('wrong_cache_state_row', lambda: compare(wrong, good, 'wrong cache row'))
            a = torch.tensor([1.], dtype=torch.bfloat16, device='cuda'); b = torch.tensor([.00390625], dtype=torch.bfloat16, device='cuda')
            rejected('missing_bf16_round_before_cache', lambda: exact(a.float() + b.float(), (a + b).float(), 'unrounded sum'))
            scratch[False].counter[0] = 1
            rejected('stale_arrival_counter_before_launch', lambda: assert_zero(scratch[False]))
            scratch[False].counter[0] = 0  # Explicit restoration after rejected invariant; no candidate launch occurred.
            wrong = {k: v.clone() for k, v in good.items()}; wrong['tokens'][0, 0] += 1
            rejected('corrupt_sampled_token', lambda: compare(wrong, good, 'corrupt token'))
            wrong = {k: v.clone() for k, v in good.items()}; wrong['cache'][3, 0, 0] = 999
            rejected('corrupt_cache_value', lambda: compare(wrong, good, 'corrupt cache'))
            # Capture reuse and live input updates; each precision has persistent scratch.
            for fp in (False, True):
                for reuse_size in SIZES:
                    x = make_inputs(reuse_size, 'dense', 1.)
                    expected, actual = buffers(), buffers()
                    reference(x, expected, fp); candidate(x, actual, fp)
                    stream.synchronize()
                    graph = torch.cuda.CUDAGraph()
                    with torch.cuda.graph(graph, stream=stream): candidate(x, actual, fp)
                    for i in range(128):
                        graph.replay(); assert_zero(scratch[fp]); compare(actual, expected, f'unchanged replay {i}')
                    for i in range(32):
                        x['anchors'].add_(1).remainder_(VOCAB); x['seeds'].add_(17); x['pos'].add_(1)
                        x['idx'].add_(1).remainder_(STATES); x['base'].add_(0.015625)
                        expected['cache'].fill_(-123); expected['tokens'].fill_(-777)
                        actual['cache'].fill_(-123); actual['tokens'].fill_(-777)
                        reference(x, expected, fp); graph.replay(); assert_zero(scratch[fp])
                        compare(actual, expected, f'changed replay {i}')
                    result['fixtures'].append({'label': 'graph_replay_reuse', 'n': reuse_size, 'use_fp64': fp, 'unchanged_replays': 128, 'changed_replays': 32, 'status': 'pass'})
                    del graph
                for n in [64, 1, 32, 5, 64]:
                    run_case(f'persistent_scratch_shape_reuse_{n}_fp64{fp}', make_inputs(n, 'permuted', 1.), fp)
            result['correctness'] = 'pass'
            save()
            # Fixed graph-vs-graph component timing. Primary installed precision is FP32 Gumbel.
            for n in SIZES:
                x = make_inputs(n, 'dense', 1.)
                a_out, b_out = buffers(native_layout=True), buffers(native_layout=True)
                reference(x, a_out, False); candidate(x, b_out, False)
                compare(b_out, a_out, 'pre-timing')
                stream.synchronize()
                graphs = {}
                for name, fn in [('A', lambda: reference(x, a_out, False)), ('B', lambda: candidate(x, b_out, False))]:
                    graph = torch.cuda.CUDAGraph()
                    with torch.cuda.graph(graph, stream=stream): fn()
                    graphs[name] = graph
                for _ in range(20):
                    graphs['A'].replay(); graphs['B'].replay()
                stream.synchronize()
                pairs = []
                start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                start.record(stream); end.record(stream); stream.synchronize()
                for block in range(30):
                    order = ['A', 'B'] if block % 2 == 0 else ['B', 'A']
                    times = {}
                    for name in order:
                        start.record(stream)
                        for _ in range(100): graphs[name].replay()
                        end.record(stream); end.synchronize()
                        times[name] = start.elapsed_time(end) * 1000 / 100
                    pairs.append({'block': block, 'order': order, 'microseconds_per_call': times})
                compare(b_out, a_out, 'post-timing'); assert_zero(scratch[False])
                baseline = np.array([p['microseconds_per_call']['A'] for p in pairs])
                treatment = np.array([p['microseconds_per_call']['B'] for p in pairs])
                gains = (baseline - treatment) / baseline * 100
                savings = baseline - treatment
                rng = np.random.default_rng(SEED)
                bootstrap_idx = rng.integers(0, 30, size=(10000, 30))
                row = {'batch_size': n, 'pairs': pairs, 'mean_baseline_us': float(baseline.mean()), 'mean_candidate_us': float(treatment.mean()),
                    'cache_shape': list(a_out['cache'].shape), 'cache_stride': list(a_out['cache'].stride()),
                    'token_shape': list(a_out['tokens'].shape), 'token_stride': list(a_out['tokens'].stride()),
                    'mean_paired_gain_percent': float(gains.mean()), 'gain_percent_95pct_interval': np.percentile(gains[bootstrap_idx].mean(1), [2.5, 97.5], method='linear').tolist(),
                    'mean_paired_saving_us': float(savings.mean()), 'saving_us_95pct_interval': np.percentile(savings[bootstrap_idx].mean(1), [2.5, 97.5], method='linear').tolist()}
                result['timing'].append(row); save()
                del graphs
            by_size = {r['batch_size']: r for r in result['timing']}
            result['component_savings_gate'] = all(by_size[n]['gain_percent_95pct_interval'][0] > 0 for n in [1, 2, 4, 7]) and all(by_size[n]['mean_paired_gain_percent'] >= -3 for n in [5, 16, 32, 64])
            result['status'] = 'component_complete_integration_not_qualified'
    except BaseException:
        result['status'] = 'failed_or_inconclusive'
        result['exception'] = traceback.format_exc()
        save()
        raise
    finally:
        result['end_ns'] = time.time_ns(); result['wall_seconds'] = (result['end_ns'] - result['start_ns']) / 1e9
        save()
    print(json.dumps({'status': result['status'], 'correctness': result.get('correctness'), 'component_savings_gate': result.get('component_savings_gate')}))


if __name__ == '__main__':
    main()

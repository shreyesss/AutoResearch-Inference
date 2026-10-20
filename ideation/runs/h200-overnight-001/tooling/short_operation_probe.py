#!/usr/bin/env python3
"""Fixed implicated-device short-operation chronology diagnostic; root executes."""
import argparse
import hashlib
import json
import time
import traceback
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = {'start_ns': time.time_ns(), 'script_sha256': sha(__file__), 'status': 'running', 'epochs': []}
    def save():
        (args.output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    save()
    try:
        import torch
        if torch.cuda.device_count() != 1:
            raise RuntimeError('exactly one visible CUDA device required')
        props = torch.cuda.get_device_properties(0)
        uuid = str(getattr(props, 'uuid', '')).removeprefix('GPU-')
        if uuid != '63d6a52f-f4e3-722c-2821-4b411f9e2ec8':
            raise RuntimeError('unexpected physical GPU UUID')
        result['environment'] = {'torch': str(torch.__version__), 'cuda': torch.version.cuda,
            'gpu_name': props.name, 'gpu_uuid': uuid, 'visible_device_count': 1}
        torch.manual_seed(20261020); torch.cuda.manual_seed_all(20261020); torch.set_grad_enabled(False)
        stream = torch.cuda.Stream()
        with torch.cuda.stream(stream):
            a = torch.randn(4096, dtype=torch.float32, device='cuda')
            b = torch.randn(4096, dtype=torch.float32, device='cuda')
            add_output, copy_output = torch.empty_like(a), torch.empty_like(a)
            # CPU reference is independent of the timed GPU implementation.
            a_cpu, b_cpu = a.cpu(), b.cpu()
            expected_add, expected_copy = a_cpu + b_cpu, a_cpu.clone()
            result['input_checks'] = {'finite': bool(torch.isfinite(a_cpu).all().item() and torch.isfinite(b_cpu).all().item()),
                'checksum_fp64': [a_cpu.double().sum().item(), b_cpu.double().sum().item()]}
            if not result['input_checks']['finite']:
                raise RuntimeError('nonfinite input')
            eager_add = lambda: torch.add(a, b, out=add_output)
            eager_copy = lambda: copy_output.copy_(a)
            for _ in range(16): eager_add(); eager_copy()
            stream.synchronize()
            graphs = {}
            for op, fn in [('add', eager_add), ('copy', eager_copy)]:
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph, stream=stream): fn()
                graphs[op] = graph
            modes = [('eager_add', eager_add), ('graph_add', graphs['add'].replay),
                     ('eager_copy', eager_copy), ('graph_copy', graphs['copy'].replay)]
            event_pairs = [(torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)) for _ in range(128)]
            for start, end in event_pairs: start.record(stream); end.record(stream)
            for _, fn in modes:
                for _ in range(16): fn()
            stream.synchronize()
            result['preparation'] = {'shape': [4096], 'dtype': 'float32', 'seed': 20261020,
                'current_stream_cuda_handle': stream.cuda_stream, 'initial_eager_warmups': 16,
                'warmups_each_mode': 16, 'event_pairs_initialized': 128,
                'graph_semantics': 'one ordinary operation on the same current nondefault stream'}
            save()
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
                    record_shapes=False, profile_memory=False, with_stack=False, with_flops=False) as profiler:
                recording_start = time.perf_counter()
                result['recording_start_epoch_ns'] = time.time_ns()
                for epoch, offset in enumerate((0, 20, 40)):
                    deadline = recording_start + offset
                    remaining = deadline - time.perf_counter()
                    if remaining > 0: time.sleep(min(remaining, 20.0))
                    actual = time.perf_counter() - recording_start
                    row = {'epoch': epoch, 'planned_offset_s': offset, 'actual_offset_s': actual,
                        'lateness_s': actual - offset, 'modes': []}
                    for mode, fn in modes:
                        mode_start_ns = time.time_ns()
                        for iteration, (begin, end) in enumerate(event_pairs):
                            begin.record(stream)
                            with torch.profiler.record_function(f'overnight_short.epoch{epoch}.{mode}.iteration{iteration}'):
                                fn()
                            end.record(stream)
                            end.synchronize()
                        durations = [begin.elapsed_time(end) for begin, end in event_pairs]
                        if not all(0 < value < float('inf') for value in durations):
                            raise RuntimeError('nonfinite or nonpositive CUDA event interval')
                        row['modes'].append({'mode': mode, 'start_ns': mode_start_ns, 'end_ns': time.time_ns(),
                            'cuda_event_elapsed_ms': durations})
                    result['epochs'].append(row)
                    save()
                stream.synchronize()
            trace = args.output / 'short-operations.trace.json'
            profiler.export_chrome_trace(str(trace))
            result['trace'] = str(trace); result['trace_sha256'] = sha(trace)
            result['output_checks'] = {'finite': bool(torch.isfinite(add_output).all().item() and torch.isfinite(copy_output).all().item()),
                'add_exact_cpu_reference': bool(torch.equal(add_output.cpu(), expected_add)),
                'copy_exact_cpu_reference': bool(torch.equal(copy_output.cpu(), expected_copy)),
                'checksum_fp64': [add_output.double().sum().item(), copy_output.double().sum().item()]}
            if not all(result['output_checks'][k] for k in ('finite', 'add_exact_cpu_reference', 'copy_exact_cpu_reference')):
                raise RuntimeError('output sanity failed')
        result['status'] = 'execution_completed_analysis_pending'
    except BaseException:
        result['status'] = 'execution_failed'; result['exception'] = traceback.format_exc()
        raise
    finally:
        result['end_ns'] = time.time_ns(); result['wall_seconds'] = (result['end_ns'] - result['start_ns']) / 1e9
        save()
    print(json.dumps({'status': result['status'], 'receipt': str(args.output / 'receipt.json')}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Fixed evaluator-only one-GPU profiler calibration. Root owns execution."""
import argparse
import hashlib
import json
import math
import platform
import time
import traceback
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.time_ns()
    receipt = {'script_sha256': sha(__file__), 'seed': 20261020, 'start_ns': started,
               'status': 'running', 'episodes': [], 'synchronization': 'before capture, before profiling, once after all64 iterations each episode'}
    def save():
        (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    try:
        import torch
        receipt['environment'] = {'python': platform.python_version(), 'torch': str(torch.__version__),
            'torch_cuda': torch.version.cuda, 'torch_path': torch.__file__,
            'kineto_available': torch.autograd.kineto_available(),
            'visible_device_count': torch.cuda.device_count()}
        if torch.cuda.device_count() != 1:
            raise RuntimeError('exactly one visible CUDA device required')
        device = torch.device('cuda:0')
        props = torch.cuda.get_device_properties(device)
        receipt['device'] = {'name': props.name, 'major': props.major, 'minor': props.minor,
            'total_memory': props.total_memory, 'uuid': str(getattr(props, 'uuid', 'not_exposed'))}
        torch.manual_seed(20261020)
        torch.cuda.manual_seed_all(20261020)
        torch.set_grad_enabled(False)
        stream = torch.cuda.Stream(device=device)
        with torch.cuda.stream(stream):
            a = torch.randn((1024, 1024), dtype=torch.float32, device=device)
            b = torch.randn((1024, 1024), dtype=torch.float32, device=device)
            outputs = [torch.empty_like(a) for _ in range(8)]
            for _ in range(8):
                torch.mm(a, b, out=outputs[0])
            stream.synchronize()
            graph_single = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph_single, stream=stream):
                torch.mm(a, b, out=outputs[0])
            stream.synchronize()
            graph_eight = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph_eight, stream=stream):
                for out in outputs:
                    torch.mm(a, b, out=out)
            stream.synchronize()
            modes = [('eager', lambda: torch.mm(a, b, out=outputs[0]), 1),
                     ('graph_single', graph_single.replay, 1), ('graph_eight', graph_eight.replay, 8)]
            # Initialize every event before profiling; CUDA event allocation is lazy.
            events = [(torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)) for _ in range(64)]
            for start, end in events:
                start.record(stream)
                end.record(stream)
            for _, op, _ in modes:
                for _ in range(8):
                    op()
            stream.synchronize()
            receipt['preparation'] = {'shape': [1024, 1024], 'dtype': 'float32', 'input_count': 2,
                'output_count': 8, 'graph_eight_semantics': 'eight ordered same-stream independent matrix multiplications into separate outputs', 'initial_matmul_warmups': 8, 'warmups_per_mode': 8,
                'event_pairs_initialized': 64, 'stream_cuda_handle': stream.cuda_stream,
                'allow_tf32': torch.backends.cuda.matmul.allow_tf32,
                'float32_matmul_precision': torch.get_float32_matmul_precision()}
            save()
            for mode, operation, matmuls in modes:
                for episode in range(2):
                    trace_path = args.output / f'{mode}-{episode}.trace.json'
                    episode_start = time.time_ns()
                    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
                            record_shapes=False, profile_memory=False, with_stack=False, with_flops=False) as profiler:
                        for iteration, (begin, end) in enumerate(events):
                            begin.record(stream)
                            with torch.profiler.record_function(f'overnight_probe.{mode}.episode{episode}.iteration{iteration}'):
                                operation()
                            end.record(stream)
                        stream.synchronize()
                    durations = [begin.elapsed_time(end) for begin, end in events]
                    profiler.export_chrome_trace(str(trace_path))
                    row = {'mode': mode, 'episode': episode, 'iterations': 64,
                        'matmuls_per_iteration': matmuls, 'start_ns': episode_start, 'end_ns': time.time_ns(),
                        'trace': str(trace_path), 'trace_sha256': sha(trace_path), 'cuda_event_elapsed_ms': durations,
                        'finite_positive_event_intervals': all(math.isfinite(x) and x > 0 for x in durations)}
                    receipt['episodes'].append(row)
                    save()
                    if not row['finite_positive_event_intervals']:
                        raise RuntimeError('nonfinite or nonpositive CUDA event interval')
            receipt['sanity'] = {'inputs_finite': bool(torch.isfinite(a).all().item() and torch.isfinite(b).all().item()),
                'outputs_finite': [bool(torch.isfinite(out).all().item()) for out in outputs],
                'input_checksums_fp64': [a.double().sum().item(), b.double().sum().item()],
                'output_checksums_fp64': [out.double().sum().item() for out in outputs]}
        if not receipt['sanity']['inputs_finite'] or not all(receipt['sanity']['outputs_finite']):
            raise RuntimeError('nonfinite sanity tensor')
        receipt['status'] = 'execution_completed_analysis_pending'
    except BaseException:
        receipt['status'] = 'execution_failed'
        receipt['exception'] = traceback.format_exc()
        raise
    finally:
        receipt['end_ns'] = time.time_ns()
        receipt['wall_seconds'] = (receipt['end_ns'] - started) / 1e9
        save()
    print(json.dumps({'status': receipt['status'], 'episodes': len(receipt['episodes']), 'receipt': str(args.output / 'receipt.json')}))


if __name__ == '__main__':
    main()

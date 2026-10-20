#!/usr/bin/env python3
"""Read-only diagnostic audit; does not assign disputed GPU activity or issue verdicts."""
import argparse
import collections
import gzip
import hashlib
import json
import re
from pathlib import Path

SCOPES = {'avk5.target_forward', 'avk5.draft_propose', 'avk5.draft_execution'}
GPU = {'kernel', 'gpu_memcpy', 'gpu_memset'}
RUNTIME = {'cuda_runtime', 'cuda_driver'}
NATIVE = re.compile(r'^execute_context_(\d+)\((\d+)\)_generation_(\d+)\((\d+)\)$')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def corr(event):
    values = {str(event.get('args', {})[key]) for key in ('correlation', 'correlation_id', 'Correlation id') if key in event.get('args', {})}
    if len(values) > 1:
        raise ValueError('conflicting correlation fields')
    return next(iter(values), None)


def contains(parent, child):
    return (parent.get('pid'), parent.get('tid')) == (child.get('pid'), child.get('tid')) and parent['ts'] <= child['ts'] and child['ts'] + child['dur'] <= parent['ts'] + parent['dur']


def compact(index, event):
    return {'trace_event_index': index, **{k: event[k] for k in ('cat', 'name', 'pid', 'tid', 'ts', 'dur', 'args') if k in event}}


def audit(trace):
    indexed = [(i, e) for i, e in enumerate(trace['traceEvents']) if e.get('ph') == 'X']
    cpu = [(i, e) for i, e in indexed if e.get('cat') == 'user_annotation']
    scopes = [(i, e) for i, e in cpu if e.get('name') in SCOPES]
    native = [(i, e) for i, e in cpu if NATIVE.match(e.get('name', ''))]
    runtime = collections.defaultdict(list)
    for i, e in indexed:
        if e.get('cat') in RUNTIME and corr(e) is not None:
            runtime[corr(e)].append((i, e))
    anomalies, ambiguous = [], []
    for i, e in indexed:
        if e.get('cat') not in GPU:
            continue
        matches = runtime.get(corr(e), [])
        if len(matches) != 1:
            ambiguous.append({'gpu_event_index': i, 'correlation': corr(e), 'runtime_matches': len(matches)})
            continue
        ri, launch = matches[0]
        delta = e['ts'] + e['dur'] - launch['ts']
        if delta < 0:
            ext_gpu, ext_cpu = e.get('args', {}).get('External id'), launch.get('args', {}).get('External id')
            parents = [(si, s) for si, s in scopes if contains(s, launch)]
            anomalies.append({'gpu': compact(i, e), 'runtime': compact(ri, launch),
                'gpu_end_minus_cpu_launch_start_us': delta,
                'external_id_present_and_equal': ext_gpu is not None and ext_gpu == ext_cpu,
                'cpu_scope_parents': [{'trace_event_index': si, 'name': s['name']} for si, s in parents],
                'disposition': 'unresolved; retain original unattributed status'})
    targets = []
    for i, e in scopes:
        if e['name'] != 'avk5.target_forward':
            continue
        parents = [(ni, n) for ni, n in native if contains(n, e)]
        targets.append({'target': compact(i, e), 'native_parent_count': len(parents),
            'native_parents': [compact(ni, n) for ni, n in parents],
            'outside_native_is_dummy': 'not established from saved annotations' if not parents else None})
    return {'trace_id': trace.get('trace_id'), 'baseTimeNanoseconds': trace.get('baseTimeNanoseconds'),
        'category_counts': dict(collections.Counter(e.get('cat') for _, e in indexed)),
        'runtime_correlations_with_multiple_records': {k: len(v) for k, v in runtime.items() if len(v) > 1},
        'gpu_events_without_unique_runtime': ambiguous,
        'negative_chronology_count': len(anomalies),
        'negative_chronology_by_gpu_category': dict(collections.Counter(a['gpu']['cat'] for a in anomalies)),
        'negative_chronology_by_graph_id': dict(collections.Counter(str(a['gpu'].get('args', {}).get('graph id')) for a in anomalies)),
        'all_anomaly_external_ids_present_and_equal': all(a['external_id_present_and_equal'] for a in anomalies) if anomalies else None,
        'negative_chronology_delta_range_us': [min(a['gpu_end_minus_cpu_launch_start_us'] for a in anomalies), max(a['gpu_end_minus_cpu_launch_start_us'] for a in anomalies)] if anomalies else None,
        'negative_chronology': anomalies,
        'native_ranges': [compact(i, e) for i, e in native],
        'profiler_steps': [compact(i, e) for i, e in cpu if e.get('name', '').startswith('ProfilerStep#')],
        'targets': targets,
        'target_native_parent_count_distribution': dict(collections.Counter(str(t['native_parent_count']) for t in targets)),
        'changed_attribution': False, 'clock_correction_applied': False,
        'eligible_cycle_count_recomputed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refuse to overwrite existing output')
    manifest = json.loads(args.manifest.read_text())
    result = {'tool_sha256': sha(__file__), 'manifest_sha256': sha(args.manifest), 'traces': []}
    for row in manifest['traces']:
        if sha(row['path']) != row['sha256']:
            raise ValueError(f"trace hash mismatch: {row['path']}")
        with gzip.open(row['path'], 'rt') as f:
            trace = json.load(f)
        result['traces'].append({**row, 'audit': audit(trace)})
    result['total_negative_chronology'] = sum(r['audit']['negative_chronology_count'] for r in result['traces'])
    result['status'] = 'diagnostic_only_original_verdict_preserved'
    with args.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'output': str(args.output), 'sha256': sha(args.output), 'traces': len(result['traces']), 'negative_chronology': result['total_negative_chronology']}))


if __name__ == '__main__':
    main()

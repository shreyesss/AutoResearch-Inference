#!/usr/bin/env python3
"""Strict explicit-identity diagnostics; no cross-domain clock correction."""
import argparse
import collections
import json
import math
import re
from pathlib import Path
from audit_saved_trace import compact, contains, corr, sha

SCOPE = re.compile(r'^overnight_probe\.(eager|graph_single|graph_eight)\.episode([01])\.iteration(\d+)$')
GPU = {'kernel', 'gpu_memcpy', 'gpu_memset'}
RUNTIME = {'cuda_runtime', 'cuda_driver'}


def union_duration(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return sum(b - a for a, b in merged)


def analyze(trace, mode, episode, iterations=64):
    events = list(enumerate(trace['traceEvents']))
    complete = [(i, e) for i, e in events if e.get('ph') == 'X']
    for _, e in complete:
        if not all(isinstance(e.get(k), (int, float)) and math.isfinite(e[k]) for k in ('ts', 'dur')) or e['dur'] < 0:
            raise ValueError('invalid complete event interval')
    scopes = [(i, e) for i, e in complete if e.get('cat') == 'user_annotation' and SCOPE.match(e.get('name', ''))]
    expected_names = {f'overnight_probe.{mode}.episode{episode}.iteration{i}' for i in range(iterations)}
    problems = []
    if len(scopes) != iterations or {e['name'] for _, e in scopes} != expected_names:
        problems.append('scope_count_or_identity_mismatch')
    runtimes = collections.defaultdict(list)
    for i, e in complete:
        if e.get('cat') in RUNTIME and corr(e) is not None:
            runtimes[corr(e)].append((i, e))
    associations, unassociated = [], []
    by_scope = collections.defaultdict(list)
    for i, e in complete:
        if e.get('cat') not in GPU:
            continue
        matches = runtimes.get(corr(e), [])
        if len(matches) != 1:
            unassociated.append({'gpu': compact(i, e), 'runtime_candidates': [compact(ri, r) for ri, r in matches]})
            continue
        ri, launch = matches[0]
        parents = [(si, s) for si, s in scopes if contains(s, launch)]
        if len(parents) > 1:
            problems.append('ambiguous_cpu_scope_parent')
        ext_g, ext_r = e.get('args', {}).get('External id'), launch.get('args', {}).get('External id')
        if ext_g is not None and ext_r is not None and ext_g != ext_r:
            problems.append('conflicting_external_ids')
        row = {'gpu': compact(i, e), 'runtime': compact(ri, launch),
            'cpu_scope_indices': [si for si, _ in parents],
            'cpu_scope_names': [s['name'] for _, s in parents],
            'external_id_status': 'equal' if ext_g is not None and ext_g == ext_r else 'absent' if ext_g is None or ext_r is None else 'conflicting',
            'gpu_start_minus_cpu_start_us': e['ts'] - launch['ts'],
            'gpu_end_minus_cpu_start_us': e['ts'] + e['dur'] - launch['ts']}
        associations.append(row)
        if len(parents) == 1:
            by_scope[parents[0][1]['name']].append(row)
    if unassociated:
        problems.append('missing_or_ambiguous_runtime_association')
    summaries = []
    for _, scope in scopes:
        rows = by_scope[scope['name']]
        if not rows:
            problems.append('required_scope_without_gpu_work')
        devices = {str(r['gpu']['args'].get('device')) for r in rows}
        if len(devices) != 1 or 'None' in devices:
            problems.append('scope_device_identity_invalid')
        spans = [(r['gpu']['ts'], r['gpu']['ts'] + r['gpu']['dur']) for r in rows]
        launches = [(i, e) for i, e in complete if e.get('cat') in RUNTIME and contains(scope, e)]
        graph_launches = [(i, e) for i, e in launches if 'GraphLaunch' in e.get('name', '')]
        if mode.startswith('graph') and len(graph_launches) != 1:
            problems.append('graph_scope_without_exactly_one_graph_launch')
        if mode.startswith('graph') and any(not any(r['runtime']['trace_event_index'] == gi for r in rows) for gi, _ in graph_launches):
            problems.append('graph_launch_without_explicit_gpu_association')
        summaries.append({'scope_name': scope['name'], 'gpu_activity_count': len(rows),
            'gpu_activity_union_us': union_duration(spans),
            'gpu_activity_span_us': max(b for a, b in spans) - min(a for a, b in spans) if spans else None,
            'device_ids': sorted(devices), 'graph_launch_count': len(graph_launches)})
    return {'trace_id': trace.get('trace_id'), 'association_domain': 'one worker process trace; correlation required unique across runtime and driver records; CPU scope parent additionally requires same pid/tid containment',
        'category_counts': dict(collections.Counter(e.get('cat') for _, e in complete)),
        'scopes': [compact(i, e) for i, e in scopes],
        'cpu_launch_records': [compact(i, e) for _, v in runtimes.items() for i, e in v],
        'associations': associations, 'unassociated': unassociated,
        'flow_records': [compact(i, e) | {'ph': e.get('ph'), 'id': e.get('id'), 'bp': e.get('bp')} for i, e in events if e.get('ph') in {'s', 't', 'f'}],
        'negative_end_before_cpu_start_count': sum(r['gpu_end_minus_cpu_start_us'] < 0 for r in associations),
        'negative_start_before_cpu_start_count': sum(r['gpu_start_minus_cpu_start_us'] < 0 for r in associations),
        'scope_summaries': summaries, 'problems': sorted(set(problems)),
        'warnings_require_root_log_review': True, 'clock_correction_applied': False}


def cross_mode_checks(episodes):
    problems = []
    counts = collections.defaultdict(list)
    device_stream = set()
    graph_ids_absent = 0
    for episode in episodes:
        mode = episode['mode']
        analysis = episode['analysis']
        per_scope = collections.Counter()
        for row in analysis['associations']:
            if row['gpu']['cat'] != 'kernel' or len(row['cpu_scope_names']) != 1:
                continue
            per_scope[row['cpu_scope_names'][0]] += 1
            args = row['gpu'].get('args', {})
            device_stream.add((str(args.get('device')), str(args.get('stream'))))
            if mode.startswith('graph') and (not args.get('graph id') or not args.get('graph node id')):
                graph_ids_absent += 1
        counts[mode].extend(per_scope[s['scope_name']] for s in analysis['scope_summaries'])
    if len(device_stream) != 1 or any('None' in pair for pair in device_stream):
        problems.append('inconsistent_device_or_stream')
    one, eight = counts['graph_single'], counts['graph_eight']
    if not one or min(one) <= 0 or len(set(one)) != 1:
        problems.append('graph_single_kernel_multiplicity_inconsistent')
    elif not eight or any(count != 8 * one[0] for count in eight):
        problems.append('graph_eight_kernel_multiplicity_not_eightfold')
    if graph_ids_absent:
        problems.append('graph_or_node_identity_absent')
    return {'kernel_counts_by_mode': dict(counts), 'device_stream_pairs': sorted(device_stream),
            'graph_kernel_records_without_graph_or_node_id': graph_ids_absent, 'problems': problems}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('refuse to overwrite existing output')
    receipt = json.loads(args.receipt.read_text())
    result = {'parser_sha256': sha(__file__), 'receipt_sha256': sha(args.receipt), 'episodes': []}
    expected = {(m, e) for m in ('eager', 'graph_single', 'graph_eight') for e in range(2)}
    actual = [(r['mode'], r['episode']) for r in receipt['episodes']]
    if len(actual) != 6 or set(actual) != expected or receipt['status'] != 'execution_completed_analysis_pending':
        raise ValueError('execution receipt incomplete')
    sanity = receipt.get('sanity', {})
    if sanity.get('inputs_finite') is not True or len(sanity.get('outputs_finite', [])) != 8 or not all(sanity['outputs_finite']):
        raise ValueError('sanity tensor check absent or failed')
    for row in receipt['episodes']:
        path = Path(row['trace'])
        if not path.exists():
            path = args.receipt.parent / path.name
        if sha(path) != row['trace_sha256']:
            raise ValueError('trace hash mismatch')
        if len(row['cuda_event_elapsed_ms']) != 64 or not all(math.isfinite(x) and x > 0 for x in row['cuda_event_elapsed_ms']):
            raise ValueError('CUDA event intervals invalid')
        result['episodes'].append({'mode': row['mode'], 'episode': row['episode'],
            'trace_sha256': row['trace_sha256'], 'cuda_event_elapsed_ms': row['cuda_event_elapsed_ms'],
            'analysis': analyze(json.loads(path.read_text()), row['mode'], row['episode'])})
    result['cross_mode_checks'] = cross_mode_checks(result['episodes'])
    result['status'] = 'instrumentation_inconclusive' if result['cross_mode_checks']['problems'] or any(r['analysis']['problems'] for r in result['episodes']) else 'structural_checks_pass_warning_review_required'
    result['negative_end_before_cpu_start_count'] = sum(r['analysis']['negative_end_before_cpu_start_count'] for r in result['episodes'])
    result['historical_timing_verdict_changed'] = False
    with args.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'episodes'}))


if __name__ == '__main__':
    main()

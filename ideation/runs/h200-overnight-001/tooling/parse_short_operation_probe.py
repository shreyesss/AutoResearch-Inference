#!/usr/bin/env python3
"""Explicit-identity parser for the separately frozen short-operation probe."""
import argparse
import collections
import json
import math
import re
from pathlib import Path
from audit_saved_trace import compact, contains, corr, sha

MODES = ('eager_add', 'graph_add', 'eager_copy', 'graph_copy')
GPU = {'kernel', 'gpu_memcpy', 'gpu_memset'}
RUNTIME = {'cuda_runtime', 'cuda_driver'}
SCOPE = re.compile(r'^overnight_short\.epoch([0-2])\.(eager_add|graph_add|eager_copy|graph_copy)\.iteration(\d+)$')


def analyze(trace, epochs=3, iterations=128):
    indexed = list(enumerate(trace['traceEvents']))
    events = [(i, e) for i, e in indexed if e.get('ph') == 'X']
    for _, e in events:
        if not all(isinstance(e.get(k), (int, float)) and math.isfinite(e[k]) for k in ('ts', 'dur')) or e['dur'] < 0:
            raise ValueError('invalid complete event interval')
    scopes = [(i, e) for i, e in events if e.get('cat') == 'user_annotation' and SCOPE.match(e.get('name', ''))]
    expected = {f'overnight_short.epoch{epoch}.{mode}.iteration{i}' for epoch in range(epochs) for mode in MODES for i in range(iterations)}
    problems = []
    if len(scopes) != len(expected) or {e['name'] for _, e in scopes} != expected:
        problems.append('incorrect_scope_inventory')
    runtimes = collections.defaultdict(list)
    for i, e in events:
        if e.get('cat') in RUNTIME and corr(e) is not None:
            runtimes[corr(e)].append((i, e))
    associations, missing = [], []
    grouped = collections.defaultdict(list)
    for i, e in events:
        if e.get('cat') not in GPU: continue
        matches = runtimes.get(corr(e), [])
        if len(matches) != 1:
            missing.append({'gpu': compact(i, e), 'runtime_candidates': [compact(ri, r) for ri, r in matches]})
            continue
        ri, launch = matches[0]
        parents = [(si, s) for si, s in scopes if contains(s, launch)]
        if len(parents) > 1: problems.append('ambiguous_cpu_scope_parent')
        a, b = e.get('args', {}).get('External id'), launch.get('args', {}).get('External id')
        if a is not None and b is not None and a != b: problems.append('conflicting_external_ids')
        row = {'gpu': compact(i, e), 'runtime': compact(ri, launch), 'cpu_scope_indices': [si for si, _ in parents],
            'cpu_scope_names': [s['name'] for _, s in parents],
            'external_id_status': 'equal' if a is not None and a == b else 'absent' if a is None or b is None else 'conflicting',
            'gpu_start_minus_cpu_start_us': e['ts'] - launch['ts'], 'gpu_end_minus_cpu_start_us': e['ts'] + e['dur'] - launch['ts']}
        associations.append(row)
        if len(parents) == 1: grouped[parents[0][1]['name']].append(row)
    if missing: problems.append('missing_or_ambiguous_runtime_association')
    summary, counts, devices_streams = [], collections.defaultdict(list), set()
    missing_graph_metadata = []
    for si, scope in scopes:
        match = SCOPE.match(scope['name']); epoch, mode, iteration = int(match[1]), match[2], int(match[3])
        rows = grouped[scope['name']]
        if not rows: problems.append('required_scope_without_gpu_activity')
        counts[mode].append(len(rows))
        for row in rows:
            args = row['gpu'].get('args', {})
            devices_streams.add((str(args.get('device')), str(args.get('stream'))))
            if mode.startswith('graph') and (not args.get('graph id') or not args.get('graph node id')):
                missing_graph_metadata.append(row['gpu']['trace_event_index'])
        graphs = [(i, e) for i, e in events if e.get('cat') in RUNTIME and contains(scope, e) and 'GraphLaunch' in e.get('name', '')]
        if mode.startswith('graph'):
            if len(graphs) != 1 or not any(r['runtime']['trace_event_index'] == graphs[0][0] for r in rows):
                problems.append('missing_explicit_graph_launch_association')
        summary.append({'epoch': epoch, 'mode': mode, 'iteration': iteration, 'scope_event_index': si,
            'activity_count': len(rows), 'activity_categories': dict(collections.Counter(r['gpu']['cat'] for r in rows)),
            'activity_durations_us': [r['gpu']['dur'] for r in rows],
            'negative_end_before_cpu_start_count': sum(r['gpu_end_minus_cpu_start_us'] < 0 for r in rows)})
    for operation in ('add', 'copy'):
        values = counts['eager_' + operation] + counts['graph_' + operation]
        if not values or min(values) <= 0 or len(set(values)) != 1:
            problems.append('inconsistent_' + operation + '_activity_multiplicity')
    if len(devices_streams) != 1 or any('None' in pair for pair in devices_streams): problems.append('inconsistent_device_or_stream')
    return {'trace_id': trace.get('trace_id'), 'association_domain': 'single process trace; runtime and driver correlation ID must be unique; CPU parent requires same pid/tid containment',
        'scope_count': len(scopes), 'scopes': [compact(i, e) for i, e in scopes],
        'cpu_launch_records': [compact(i, e) for items in runtimes.values() for i, e in items],
        'associations': associations, 'missing_or_ambiguous': missing, 'scope_summary': summary,
        'flow_records': [compact(i, e) | {'ph': e.get('ph'), 'id': e.get('id'), 'bp': e.get('bp')} for i, e in indexed if e.get('ph') in {'s', 't', 'f'}],
        'negative_end_before_cpu_start_count': sum(r['gpu_end_minus_cpu_start_us'] < 0 for r in associations),
        'negative_start_before_cpu_start_count': sum(r['gpu_start_minus_cpu_start_us'] < 0 for r in associations),
        'graph_activities_without_graph_node_metadata': missing_graph_metadata,
        'complete_graph_node_accounting_qualified': not missing_graph_metadata,
        'device_stream_pairs': sorted(devices_streams), 'problems': sorted(set(problems)),
        'clock_correction_applied': False, 'warnings_require_root_log_review': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', required=True, type=Path); p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if args.output.exists(): p.error('refuse to overwrite output')
    receipt = json.loads(args.receipt.read_text())
    if receipt['status'] != 'execution_completed_analysis_pending' or len(receipt['epochs']) != 3:
        raise ValueError('incomplete execution')
    for epoch, row in enumerate(receipt['epochs']):
        if row['epoch'] != epoch or row['planned_offset_s'] != epoch * 20 or row['actual_offset_s'] < epoch * 20 or [m['mode'] for m in row['modes']] != list(MODES):
            raise ValueError('epoch schedule mismatch')
        for mode in row['modes']:
            values = mode['cuda_event_elapsed_ms']
            if len(values) != 128 or not all(math.isfinite(v) and v > 0 for v in values): raise ValueError('invalid event intervals')
    if not receipt['input_checks']['finite'] or not all(receipt['output_checks'][k] for k in ('finite', 'add_exact_cpu_reference', 'copy_exact_cpu_reference')):
        raise ValueError('finite exact output check failed')
    path = Path(receipt['trace'])
    if not path.exists(): path = args.receipt.parent / path.name
    if sha(path) != receipt['trace_sha256']: raise ValueError('trace hash mismatch')
    result = {'parser_sha256': sha(__file__), 'receipt_sha256': sha(args.receipt), 'trace_sha256': sha(path),
        'epochs': receipt['epochs'], 'analysis': analyze(json.loads(path.read_text())), 'historical_timing_verdict_changed': False}
    result['status'] = 'instrumentation_inconclusive' if result['analysis']['problems'] else 'structural_checks_pass_warning_review_required'
    with args.output.open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({'status': result['status'], 'negative_chronology': result['analysis']['negative_end_before_cpu_start_count'], 'problems': result['analysis']['problems']}))


if __name__ == '__main__': main()

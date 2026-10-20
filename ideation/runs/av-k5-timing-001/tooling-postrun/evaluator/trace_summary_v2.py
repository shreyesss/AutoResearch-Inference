#!/usr/bin/env python3
"""Conservative per-device CUDA occupied intervals from explicit scope/launch links.

This is not an exposed-critical-path estimator. Kernel names never assign roles.
"""
import argparse
import collections
import gzip
import hashlib
import json
import math
import re
from pathlib import Path

SCOPES = {'avk5.target_forward': 'target', 'avk5.draft_propose': 'draft',
          'avk5.draft_execution': 'draft_execution'}
GPU_CATEGORIES = {'kernel', 'gpu_memcpy', 'gpu_memset'}
RUNTIME_CATEGORIES = {'cuda_runtime', 'cuda_driver'}
EXECUTE = re.compile(r'^execute_context_(\d+)\((\d+)\)_generation_(\d+)\((\d+)\)$')


def sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def interval(event):
    a, duration = event.get('ts'), event.get('dur')
    if not isinstance(a, (int, float)) or not isinstance(duration, (int, float)) or not math.isfinite(a) or not math.isfinite(duration) or duration < 0:
        raise ValueError('invalid complete event timestamp/duration')
    return a, a + duration


def union(items):
    merged = []
    for start, end in sorted(items):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def length(items):
    return sum(end - start for start, end in union(items))


def overlap(first, second):
    return length(first) + length(second) - length(first + second)


def clipped(items, start, end):
    return [(max(a, start), min(b, end)) for a, b in items if a < end and b > start]


def occupancy(records, start, end):
    by_role = collections.defaultdict(list)
    by_kind = collections.defaultdict(list)
    for record in records:
        spans = clipped([interval(record['event'])], start, end)
        by_role[record['role']].extend(spans)
        by_kind[record['event']['cat']].extend(spans)
    target = by_role['target']
    draft = by_role['draft'] + by_role['draft_execution']
    all_spans = [span for spans in by_role.values() for span in spans]
    busy = length(all_spans)
    return {'cycle_wall_span_us': end - start, 'all_activity_union_us': busy,
            'idle_without_observed_gpu_activity_us': end - start - busy,
            'target_union_us': length(target), 'draft_total_union_us': length(draft),
            'draft_execution_union_us': length(by_role['draft_execution']),
            'draft_outside_execution_union_us': length(draft) - length(by_role['draft_execution']),
            'other_correlated_union_us': length(by_role['other_correlated_work']),
            'unattributed_union_us': length(by_role['unattributed']),
            'target_draft_overlap_us': overlap(target, draft),
            'kernel_union_us': length(by_kind['kernel']),
            'memcpy_union_us': length(by_kind['gpu_memcpy']),
            'memset_union_us': length(by_kind['gpu_memset']),
            'target_occupied_share_of_cycle_span': length(target) / (end-start),
            'assigned_share_of_all_busy_union': length(target + draft + by_role['other_correlated_work']) / busy if busy else None}


def correlation(event):
    args = event.get('args', {})
    values = {str(args[key]) for key in ('correlation', 'correlation_id', 'Correlation id') if key in args}
    if len(values) > 1:
        raise ValueError('conflicting correlation fields')
    return next(iter(values), None)


def contains(parent, child):
    a, b = interval(parent)
    x, y = interval(child)
    return parent.get('pid') == child.get('pid') and parent.get('tid') == child.get('tid') and a <= x and y <= b


def summarize(trace):
    events = [event for event in trace.get('traceEvents', []) if event.get('ph') == 'X']
    scopes = [event for event in events if event.get('cat') == 'user_annotation' and event.get('name') in SCOPES]
    runtimes = [event for event in events if event.get('cat') in RUNTIME_CATEGORIES]
    gpu = [event for event in events if event.get('cat') in GPU_CATEGORIES]
    native = [event for event in events if event.get('cat') == 'user_annotation' and EXECUTE.match(event.get('name', ''))]
    problems = []
    if not scopes or not gpu:
        problems.append('missing_scope_or_gpu_activity')
    if len({event.get('pid') for event in scopes}) != 1:
        problems.append('scope_process_identity_not_unique')
    launch_by_correlation = collections.defaultdict(list)
    for runtime in runtimes:
        key = correlation(runtime)
        if key is not None:
            launch_by_correlation[key].append(runtime)
    attributed = []
    unclassified_reasons = collections.Counter()
    for event in gpu:
        # A unique runtime correlation is required even if a kernel name is familiar.
        matches = launch_by_correlation.get(correlation(event), [])
        record = {'event': event, 'role': 'unattributed', 'scope': None, 'launch': None}
        if len(matches) != 1:
            unclassified_reasons['missing_or_ambiguous_runtime_correlation'] += 1
        else:
            launch = matches[0]
            record['launch'] = launch
            if interval(event)[1] < interval(launch)[0]:
                unclassified_reasons['gpu_activity_precedes_correlated_launch'] += 1
                attributed.append(record)
                continue
            candidates = [scope for scope in scopes if contains(scope, launch)]
            if candidates:
                chosen = min(candidates, key=lambda item: item['dur'])
                record.update(scope=chosen, role=SCOPES[chosen['name']])
            else:
                record['role'] = 'other_correlated_work'
        attributed.append(record)
    devices = collections.defaultdict(list)
    for record in attributed:
        args = record['event'].get('args', {})
        device = args.get('device')
        if device is None:
            problems.append('missing_gpu_device_field')
            device = 'unknown'
        devices[str(device)].append(record)
    summaries = []
    for device, records in sorted(devices.items()):
        by_role = collections.defaultdict(list)
        by_kind = collections.defaultdict(list)
        for record in records:
            span = interval(record['event'])
            by_role[record['role']].append(span)
            by_kind[record['event']['cat']].append(span)
        target = by_role['target']
        draft = by_role['draft'] + by_role['draft_execution']
        all_spans = [interval(record['event']) for record in records]
        all_busy = length(all_spans)
        summaries.append({'device': device, 'gpu_events': len(records),
                          'observed_span_us': max(b for a, b in all_spans) - min(a for a, b in all_spans),
                          'all_activity_union_us': all_busy,
                          'kernel_union_us': length(by_kind['kernel']),
                          'memcpy_union_us': length(by_kind['gpu_memcpy']),
                          'memset_union_us': length(by_kind['gpu_memset']),
                          'target_union_us': length(target), 'draft_total_union_us': length(draft),
                          'draft_execution_union_us': length(by_role['draft_execution']),
                          'draft_outside_execution_union_us': length(draft) - length(by_role['draft_execution']),
                          'target_draft_overlap_us': overlap(target, draft),
                          'target_share_of_all_occupied_union': length(target) / all_busy if all_busy else None,
                          'draft_share_of_all_occupied_union': length(draft) / all_busy if all_busy else None,
                          'other_correlated_union_us': length(by_role['other_correlated_work']),
                          'unattributed_union_us': length(by_role['unattributed']),
                          'stream_ids': sorted({str(record['event'].get('args', {}).get('stream', 'unknown')) for record in records})})
    if len(devices) != 1:
        problems.append('expected_one_device_per_worker_trace')
    # Complete CPU ranges plus attributable GPU work; no assumption 20 requested ==20 observed.
    targets = sorted((scope for scope in scopes if scope['name'] == 'avk5.target_forward'), key=lambda item: item['ts'])
    proposals = [scope for scope in scopes if scope['name'] == 'avk5.draft_propose']
    cycles = []
    exclusions = collections.Counter()
    for i, target in enumerate(targets):
        if i + 1 == len(targets):
            exclusions['last_target_without_following_target'] += 1
            continue
        following = targets[i + 1]
        end_limit = following['ts']
        execute = [item for item in native if contains(item, target)]
        drafts = [item for item in proposals if item.get('pid') == target.get('pid') and item.get('tid') == target.get('tid') and interval(target)[1] <= item['ts'] and interval(item)[1] <= end_limit]
        if len(execute) != 1 or len(drafts) != 1:
            exclusions['missing_or_ambiguous_native_or_draft_range'] += 1
            continue
        match = EXECUTE.match(execute[0]['name'])
        if int(match.group(1)) != 0 or int(match.group(3)) <= 0:
            exclusions['mixed_prefill_or_no_generation'] += 1
            continue
        draft = drafts[0]
        execution = [scope for scope in scopes if scope['name'] == 'avk5.draft_execution' and contains(draft, scope)]
        if len(execution) != 1:
            exclusions['missing_or_ambiguous_draft_execution'] += 1
            continue
        target_records = [record for record in attributed if record['scope'] is target]
        draft_records = [record for record in attributed if record['scope'] is draft or record['scope'] is execution[0]]
        following_records = [record for record in attributed if record['scope'] is following]
        if not target_records or not draft_records or not following_records:
            exclusions['missing_target_draft_or_following_target_gpu_activity'] += 1
            continue
        cycle_devices = {str(record['event'].get('args', {}).get('device', 'unknown')) for record in target_records + draft_records + following_records}
        if len(cycle_devices) != 1 or 'unknown' in cycle_devices:
            exclusions['ambiguous_same_device_cycle'] += 1
            continue
        cycle_device = next(iter(cycle_devices))
        graph_counts = {}
        for name, scope in [('target', target), ('draft_execution', execution[0])]:
            launches = [runtime for runtime in runtimes if contains(scope, runtime) and 'GraphLaunch' in runtime.get('name', '')]
            linked = sum(any(record['launch'] is runtime for record in attributed) for runtime in launches)
            graph_counts[name] = {'launches': len(launches), 'launches_with_gpu_events': linked}
        if any(row['launches'] != row['launches_with_gpu_events'] for row in graph_counts.values()):
            problems.append('graph_launch_without_linked_gpu_activity')
            continue
        start = min(interval(record['event'])[0] for record in target_records)
        end = min(interval(record['event'])[0] for record in following_records)
        if end <= start:
            exclusions['nonincreasing_gpu_cycle_boundary'] += 1
            problems.append('nonincreasing_gpu_cycle_boundary')
            continue
        cycle = {'cpu_target_start_us': target['ts'], 'cpu_draft_end_us': interval(draft)[1],
                       'cpu_next_target_start_us': following['ts'],
                       'cpu_target_range_duration_us': target['dur'],
                       'cpu_draft_propose_range_duration_us': draft['dur'],
                       'gpu_cycle_start_us': start, 'gpu_cycle_end_us': end,
                       'generation_requests': int(match.group(3)), 'generation_tokens': int(match.group(4)),
                       'graph_launches': graph_counts,
                       'execution_mode': 'not_observed', 'graph_descriptor': None,
                       'scope_target_gpu_first_to_last_span_us': max(interval(record['event'])[1] for record in target_records) - start,
                       'scope_draft_gpu_first_to_last_span_us': max(interval(record['event'])[1] for record in draft_records) - min(interval(record['event'])[0] for record in draft_records)}
        cycle['device'] = cycle_device
        cycle.update(occupancy(devices[cycle_device], start, end))
        cycles.append(cycle)
    if unclassified_reasons:
        problems.append('unattributed_gpu_activity_graph_coverage_unknown')
    if len(cycles) < 10:
        problems.append('fewer_than_10_complete_eligible_decode_cycles')
    return {'scope_process_ids': sorted({str(event.get('pid')) for event in scopes}),
            'scope_counts': dict(collections.Counter(event['name'] for event in scopes)),
            'native_execute_range_count': len(native), 'runtime_count': len(runtimes),
            'gpu_event_count': len(gpu), 'unclassified_reasons': dict(unclassified_reasons),
            'devices': summaries, 'complete_eligible_decode_cycles': cycles,
            'cycle_exclusion_counts': dict(exclusions),
            'external_review_required': ['runtime/source/phase and physical GPU identity', 'episode control/trace alignment', 'dropped-activity and truncation warnings in worker/profiler logs'],
            'adequacy_problems': sorted(set(problems)),
            'descriptive_occupied_time_adequate': not problems,
            'exposed_critical_path_established': False,
            'clock_scope': 'per-worker trace, same-device only; no cross-device timeline alignment inferred'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    result = {'schema_version': 1, 'source_sha256': sha(Path(__file__)), 'manifest_sha256': sha(args.manifest),
              'traces': [], 'status': 'extracting', 'exposed_critical_path_established': False}
    try:
        manifest = json.loads(args.manifest.read_text())
        expected = {(offset, replica, rank) for offset in (90, 210) for replica in range(2) for rank in range(4)}
        rows = manifest['traces']
        actual = [(row['offset_s'], row['replica'], row['rank']) for row in rows]
        if len(actual) != len(expected) or set(actual) != expected:
            raise ValueError('exactly16 traces, two episodes × two replicas × four ranks required')
        identity = Path(manifest['identity_receipt'])
        if sha(identity) != manifest['identity_sha256']:
            raise ValueError('identity receipt hash mismatch')
        bound_artifacts = {}
        for name in ('phase_receipt', 'control_receipt', 'observation_manifest'):
            path = Path(manifest[name])
            if sha(path) != manifest[name + '_sha256']:
                raise ValueError(f'{name} hash mismatch')
            bound_artifacts[name] = {'path': str(path.resolve()), 'sha256': sha(path)}
        control = json.loads(Path(manifest['control_receipt']).read_text())
        if control['profiling_start_ns'] != manifest['profiling_start_ns']:
            raise ValueError('control profiling-start mismatch')
        if control['status'] != 'control_completed_trace_adequacy_pending':
            raise ValueError('profile controller did not complete both fixed episodes')
        if [episode['offset_s'] for episode in control['episodes']] != [90, 210]:
            raise ValueError('control episodes differ from fixed schedule')
        for episode in control['episodes']:
            if any(len(episode[action]) != 2 or not all(row['ok'] for row in episode[action]) for action in ('start', 'stop')):
                raise ValueError('failed or incomplete control operations')
        result['bound_artifacts'] = bound_artifacts
        result['identity_binding'] = 'external root/reviewer must verify worker PID, container, device UUID and source mounts'
        seen_paths = set()
        for row in rows:
            path = Path(row['path']).resolve()
            if path in seen_paths:
                raise ValueError('duplicate trace file')
            seen_paths.add(path)
            if sha(path) != row['sha256']:
                raise ValueError(f'trace hash mismatch: {path}')
            for key in ('worker_pid', 'gpu_uuid', 'container_id'):
                if not row.get(key):
                    raise ValueError(f'missing external trace identity {key}')
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rb') as stream:
                raw = stream.read(512 * 1024 * 1024 + 1)
            if len(raw) > 512 * 1024 * 1024:
                raise ValueError('trace exceeds512MiB decompressed bound; no silent truncation')
            summary = summarize(json.loads(raw))
            if summary['scope_process_ids'] != [str(row['worker_pid'])]:
                summary['adequacy_problems'].append('worker_pid_not_bound_to_scope_process')
                summary['descriptive_occupied_time_adequate'] = False
            result['traces'].append({'identity': row, 'summary': summary})
        result['status'] = 'occupied_measurements_ready_external_review_pending' if all(row['summary']['descriptive_occupied_time_adequate'] for row in result['traces']) else 'inconclusive_trace_adequacy'
        result['timing_qualification'] = 'pending external identity, phase, warning and attribution review; parser does not issue AV verdict'
    except Exception as exc:
        result.update(status='extraction_failed', error=f'{type(exc).__name__}: {exc}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'receipt': str(args.output)}))
    return 0 if result['status'] != 'extraction_failed' else 1

if __name__ == '__main__':
    raise SystemExit(main())

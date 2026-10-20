"""Narrow fresh-start exception; all post-traffic drain gauges remain strict."""
import math
from service_rank_control import FINISH_REASONS, success_values


def initial_values(router, backends, model):
    gauges = {}
    counts = {str(r): None for r in range(2)}
    for name, labels, value in router:
        if name == 'dsv41_router_in_flight':
            key = labels.get('backend')
            if key not in {'0', '1'} or key in gauges or value != 0:
                raise AssertionError('fresh router not exclusively idle')
            gauges[key] = value
        if name == 'dsv41_router_requests_total':
            kind = labels.get('kind', '')
            if kind.startswith('requests_backend_'):
                key = kind.rsplit('_', 1)[1]
                if key not in counts or counts[key] is not None or value != 0:
                    raise AssertionError('fresh router already received traffic')
                counts[key] = value
            elif value != 0:
                raise AssertionError('fresh router has nonzero prior request/error counters')
    if set(gauges) != {'0', '1'}:
        raise AssertionError('missing fresh router activity gauges')
    engines = {}
    for replica, rows in enumerate(backends):
        for metric in ('vllm:num_requests_running', 'vllm:num_requests_waiting'):
            values = {str(rank): None for rank in range(4)}
            found = set()
            for name, labels, value in rows:
                if name != metric: continue
                rank = labels.get('engine')
                if labels.get('model_name') != model or rank not in values or rank in found or value != 0:
                    raise AssertionError('unexpected initial engine identity/activity')
                found.add(rank); values[rank] = value
            engines[f'{replica}:{metric}'] = values
    counters = success_values(backends, model)
    if any(v not in (None, 0) for r in counters.values() for e in r.values() for v in e.values()):
        raise AssertionError('fresh engine already completed traffic')
    return {'router': gauges, 'engines': engines, 'request_counts': counts,
            'zero': False, 'initial_absence_policy': 'unknown; fresh exclusive root ownership permits fixed first fixtures'}


def attest_initial_counts(after):
    if after['request_counts'] != {'0': 8, '1': 8} or not after['zero']:
        raise AssertionError('sixteen initialization requests have not strictly drained with router8each')
    for replica in range(2):
        for rank in range(4):
            for reason in FINISH_REASONS:
                expected = (5 if rank == 0 else 1) if reason == 'length' else 0
                if after['success_counts'][str(replica)][str(rank)][reason] != expected:
                    raise AssertionError('initial actual engine completion count or routing mismatch')
    return {'passed': True, 'length_completions_per_replica': [5,1,1,1],
            'router_completions': [8,8], 'all_terminal_counters_observed': True,
            'scope': 'original ten rank0 requests plus six fixed rank1/2/3 primers; no missing-as-zero'}


def validate_observed_metrics(router, backends, model):
    seen = set()
    for name, labels, value in router:
        if name not in ('dsv41_router_in_flight', 'dsv41_router_requests_total'): continue
        key = (name, tuple(sorted(labels.items())))
        if key in seen or not math.isfinite(value) or value < 0 or not value.is_integer():
            raise AssertionError('invalid or duplicate router gauge/counter')
        seen.add(key)
    for rows in backends:
        seen = set()
        for name, labels, value in rows:
            if name not in ('vllm:num_requests_running', 'vllm:num_requests_waiting'): continue
            key = (name, labels.get('engine'))
            if (key in seen or labels.get('model_name') != model or labels.get('engine') not in {'0','1','2','3'}
                    or not math.isfinite(value) or value < 0 or not value.is_integer()):
                raise AssertionError('invalid or duplicate engine activity gauge')
            seen.add(key)

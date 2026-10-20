"""Independent native proposal reader: fixed inventory, all ranks, paired rounds."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

LOGICAL = (1, 2, 4, 5)
EXPECTED_DRAFT = {1: 1, 2: 2, 4: 4, 5: 7}


def validate_rank(value, arm, replica, rank, observer_sha, reference_sha):
    identity = {'arm': arm, 'replica': replica, 'rank': rank, 'status': 'passed',
                'restored': True, 'native_oracle_passed': True,
                'capture_attestation_passed': True, 'timed_samples': 960,
                'observer_sha256': observer_sha, 'reference_sha256': reference_sha}
    if any(value.get(k) != v for k, v in identity.items()):
        raise ValueError('native receipt identity/status/source mismatch')
    if not value.get('run_id') or not value.get('gpu_uuid') or not value.get('pid_start_ticks'):
        raise ValueError('missing native process/device binding')
    if not value.get('guards') or not all(value['guards'].values()) or not value.get('restore_checks') or not all(value['restore_checks'].values()):
        raise ValueError('native guard or restoration failed')
    captures = {}
    for c in value['captures']:
        key = c['graph_object_id']
        if key in captures or c['sample_steps'] != [0,1,2,3,4] or c['branch'] != ('fused' if arm == 'B' else 'installed') or c['capturing'] is not True:
            raise ValueError('invalid capture witness')
        captures[key] = c
    oracles = {}
    descriptors = {}
    for o in value['oracles']:
        key = o['phase'], o['logical_requests']
        if key in oracles or key[0] not in ('before', 'after') or key[1] not in LOGICAL:
            raise ValueError('duplicate or unplanned oracle')
        flags = ('exact_tokens','exact_finite_cache','reference_repeat','inactive_rows_preserved','counters_zero')
        if any(o.get(flag) is not True for flag in flags):
            raise ValueError('native exact oracle failed')
        target = o['dispatch']['target']; draft = o['dispatch']['draft']
        if target['descriptor']['cg_mode'] != 'FULL' or draft['descriptor']['cg_mode'] != 'FULL':
            raise ValueError('oracle did not execute FULL graphs')
        cap = captures.get(draft['graph_object_id'])
        if cap is None or cap['descriptor'] != draft['descriptor'] or cap['head_info'] != o['head']:
            raise ValueError('native replay not bound to captured graph/head')
        active = o['active_state_rows']
        if active != list(range(target['descriptor']['num_reqs'])):
            raise ValueError('active rows differ from actual target descriptor')
        if o['temperature'] != [1.0] * len(active) or o['seeds'] != [731+i for i in active]:
            raise ValueError('native setup mismatch')
        if len(o['mapping']) != draft['descriptor']['num_reqs']:
            raise ValueError('draft mapping shape mismatch')
        expected_mapping = [[i] * 5 for i in active] + [[-1] * 5 for _ in range(len(o['mapping'])-len(active))]
        if o['mapping'] != expected_mapping:
            raise ValueError('unexpected padded/valid state mapping')
        if len(o['tokens']) != len(active) or any(len(row) != 5 or any(type(x) is not int or not 0 <= x < 129280 for x in row) for row in o['tokens']):
            raise ValueError('native token oracle shape/range invalid')
        if o['logical_requests'] in descriptors and descriptors[o['logical_requests']] != o['dispatch']:
            raise ValueError('before/after graph descriptor drift')
        descriptors[o['logical_requests']] = o['dispatch']
        oracles[key] = o
    if set(oracles) != {(phase, n) for phase in ('before','after') for n in LOGICAL}:
        raise ValueError('missing required before/after native oracle')
    samples = {}
    for sample in value['samples']:
        key = sample['round'], sample['logical_requests'], sample['cycle']
        if key in samples or not (0 <= key[0] < 30 and key[1] in LOGICAL and 0 <= key[2] < 8):
            raise ValueError('duplicate or unplanned timing cell')
        if sample['dispatch'] != descriptors[key[1]] or sample['stream'] != value['device']['stream'] or not sample['full_cudagraph']:
            raise ValueError('timed graph descriptor/stream differs from oracle')
        td = sample['dispatch']['target']['descriptor']
        if sample['num_reqs'] != td['num_reqs'] or sample['num_target_tokens'] != td['num_tokens']:
            raise ValueError('collector batch differs from native FULL descriptor')
        if any(not math.isfinite(sample[k]) or sample[k] <= 0 for k in ('forward_ms','drafter_ms')):
            raise ValueError('invalid native event duration')
        samples[key] = sample
    if len(samples) != 960:
        raise ValueError('incomplete fixed timing inventory')
    expected_order = []
    for rd in range(30):
        order = list(LOGICAL[rd % 4:] + LOGICAL[:rd % 4])
        if rd % 2: order.reverse()
        expected_order.extend((rd,n,cy) for n in order for cy in range(8))
    if list(samples) != expected_order:
        raise ValueError('fixed rotating/reversing sample order violated')
    return {'samples': samples, 'descriptors': descriptors,
            'intended_shape_coverage': {str(n): descriptors[n]['draft']['descriptor']['num_reqs'] == EXPECTED_DRAFT[n] for n in LOGICAL}}


def bootstrap(a, b):
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    indices = np.random.default_rng(20261020).integers(0, 30, size=(10000,30))
    aa, bb = a[indices].mean(axis=1), b[indices].mean(axis=1)
    return {'baseline_mean_us': float(a.mean()*1000), 'candidate_mean_us': float(b.mean()*1000),
            'saved_us': float((a.mean()-b.mean())*1000),
            'gain_percent': float((a.mean()-b.mean())/a.mean()*100),
            'saved_us_ci95': (np.percentile((aa-bb)*1000,[2.5,97.5])).tolist(),
            'gain_percent_ci95': np.percentile((aa-bb)/aa*100,[2.5,97.5]).tolist()}


def validate_bindings(loaded, launch=None):
    import uuid
    run_ids = {v['run_id'] for v in loaded.values()}
    if len(run_ids) != 1:
        raise ValueError('native receipts mix run IDs')
    def normalized(value): return str(uuid.UUID(value.removeprefix('GPU-')))
    by_key = {key: normalized(v['gpu_uuid']) for key,v in loaded.items()}
    for arm in ('A','B'):
        values = [value for (a,_,_),value in by_key.items() if a == arm]
        if len(values) != 8 or len(set(values)) != 8:
            raise ValueError('each arm requires eight unique GPU UUIDs')
    for replica in range(2):
        for rank in range(4):
            if by_key['A',replica,rank] != by_key['B',replica,rank]:
                raise ValueError('A/B rank GPU UUID mismatch')
    if launch is not None:
        if run_ids != {launch['run_id']}:
            raise ValueError('native run differs from launch manifest')
        inventory = {}
        for line in launch['gpu_inventory'].splitlines():
            fields = [x.strip() for x in line.split(',')]
            inventory[int(fields[0])] = normalized(fields[1])
        for (arm,replica,rank), value in by_key.items():
            if inventory[replica*4+rank] != value:
                raise ValueError('native UUID differs from pinned launch inventory')
    return True


def analyze(a_dir, b_dir, manifest, launch=None):
    import numpy as np
    observer = next(x['sha256'] for x in manifest['files'] if x['destination'].endswith('/c25_native_observer.py'))
    reference = next(x['sha256'] for x in manifest['files'] if x['destination'].endswith('/reference_dspark.py'))
    loaded, validated, artifacts, errors = {}, {}, [], []
    for arm, directory in (('A',a_dir),('B',b_dir)):
        for replica in range(2):
            for rank in range(4):
                key = arm, replica, rank
                path = directory / f'replica{replica}' / f'rank{rank}.json'
                try:
                    data = path.read_bytes(); value = json.loads(data)
                    loaded[key] = value
                    validated[key] = validate_rank(value, *key, observer, reference)
                    artifacts.append({'arm':arm,'replica':replica,'rank':rank,'path':str(path),'sha256':hashlib.sha256(data).hexdigest()})
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    errors.append({'arm':arm,'replica':replica,'rank':rank,'error':f'{type(exc).__name__}: {exc}'})
    if not errors:
        try: validate_bindings(loaded, launch)
        except (ValueError, KeyError, TypeError) as exc: errors.append({'binding_error':str(exc)})
    result = {'schema_version':1,'status':'incomplete' if errors else 'valid', 'errors':errors,
              'rank_artifacts':artifacts,'cells':[],
              'scope':'exploratory controlled padded native proposal proxy; within-start per-cell intervals, no familywise or confirmed service/ITL claim',
              'startup_order':['A','B'],'bootstrap_seed':20261020,'bootstrap_draws':10000}
    for replica in range(2):
        for n in LOGICAL:
            if any((arm,replica,rank) not in validated for arm in ('A','B') for rank in range(4)): continue
            rows = {'replica':replica,'logical_requests':n,'ranks':{}}
            stage = {}
            for endpoint in ('drafter_ms','forward_ms'):
                for arm in ('A','B'):
                    array = np.array([[[validated[arm,replica,rank]['samples'][rd,n,cy][endpoint] for cy in range(8)] for rank in range(4)] for rd in range(30)])
                    stage[arm] = array.mean(axis=2).max(axis=1)
                    rows['ranks'].setdefault(arm,{})[endpoint] = {'rank_mean_us':(array.mean(axis=(0,2))*1000).tolist(),
                        'rank_p50_us':(np.median(array,axis=(0,2))*1000).tolist(),
                        'rank_p95_us':(np.percentile(array,95,axis=(0,2))*1000).tolist(),
                        'coordinated_round_mean_us':(stage[arm]*1000).tolist()}
                rows[endpoint] = bootstrap(stage['A'],stage['B'])
            descriptors = [validated[arm,replica,rank]['descriptors'][n] for arm in ('A','B') for rank in range(4)]
            normalized = [{role: value['descriptor'] for role,value in desc.items()} for desc in descriptors]
            rows['all_rank_arm_descriptor_match'] = all(x == normalized[0] for x in normalized)
            rows['descriptors'] = normalized[0]
            rows['intended_shape_covered'] = all(validated[arm,replica,rank]['intended_shape_coverage'][str(n)] for arm in ('A','B') for rank in range(4))
            rows['positive_within_start_signal'] = rows['all_rank_arm_descriptor_match'] and rows['intended_shape_covered'] and rows['drafter_ms']['gain_percent'] > 0 and rows['drafter_ms']['gain_percent_ci95'][0] > 0
            rows['target_control_absolute_change_at_least_draft_saving'] = abs(rows['forward_ms']['saved_us']) >= abs(rows['drafter_ms']['saved_us'])
            rows['target_control_percent_change_at_least_draft_gain'] = abs(rows['forward_ms']['gain_percent']) >= abs(rows['drafter_ms']['gain_percent'])
            rows['control_interpretation'] = 'absolute and percent drift diagnostics only; unequal stage lengths and startup order require independent attribution review; no subtraction'
            result['cells'].append(rows)
    result['any_exploratory_positive_cell'] = not errors and any(x['positive_within_start_signal'] for x in result['cells'])
    result['control_absolute_change_flagged_cells'] = [[x['replica'],x['logical_requests']] for x in result['cells'] if x['target_control_absolute_change_at_least_draft_saving']]
    result['attribution'] = 'requires independent review of both drift diagnostics, telemetry and startup order'
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--arm-a',type=Path,required=True)
    parser.add_argument('--arm-b',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=Path(__file__).with_name('manifest.json'))
    parser.add_argument('--launch-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('refusing to overwrite analysis')
    result=analyze(args.arm_a,args.arm_b,json.loads(args.manifest.read_text()),json.loads(args.launch_manifest.read_text()))
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'cells':len(result['cells']),'any_exploratory_positive_cell':result['any_exploratory_positive_cell']}))
    raise SystemExit(0 if result['status']=='valid' else 2)

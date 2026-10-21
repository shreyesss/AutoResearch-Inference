"""Readiness checks for a controlled experiment, without executing its commands."""
import math
import re


def qualify_plan(manifest, hypothesis):
    if not isinstance(manifest, dict):
        raise ValueError('Evaluation manifest must be an object')
    gaps = []
    if manifest.get('purpose') not in ('diagnostic', 'qualification'):
        gaps.append('Specify purpose diagnostic or qualification')
    if manifest.get('scope') not in ('component', 'native', 'service'):
        gaps.append('Specify component/native/service scope')
    def field(path):
        value = manifest
        for key in path.split('.'):
            value = value.get(key) if isinstance(value, dict) else None
        if value is None or value == '' or value == [] or value == {} or isinstance(value, str) and value.lower() in {'unknown', 'unset', 'tbd'}:
            gaps.append('Missing ' + path)
        return value
    def pin(path, length):
        value = field(path)
        if value is not None and not re.fullmatch('[0-9a-f]{' + str(length) + '}', str(value)):
            gaps.append('Not an exact hash: ' + path)
    for path in ('baseline.git_sha', 'candidate.parent_git_sha'):
        pin(path, 40)
    for path in ('candidate.patch_sha256', 'workload.sha256'):
        pin(path, 64)
    for path in ('baseline.image_digest', 'baseline.model.id', 'baseline.model.revision', 'baseline.tokenizer.id', 'baseline.tokenizer.revision',
                 'baseline.runtime.driver', 'baseline.runtime.cuda', 'baseline.runtime.engine_version',
                 'baseline.hardware.gpu_type', 'baseline.hardware.gpu_count', 'baseline.hardware.topology',
                 'baseline.parallelism.tp', 'baseline.parallelism.dp', 'baseline.parallelism.ep', 'baseline.serving', 'baseline.quantization',
                 'candidate.description', 'workload.id', 'workload.seed', 'workload.arrival', 'workload.concurrency',
                 'workload.prompt_output_distribution', 'workload.cache_policy', 'objective.metric', 'objective.unit',
                 'objective.aggregation', 'objective.direction', 'objective.min_relative_gain', 'objective.tail_guards',
                 'correctness.oracle', 'correctness.tolerance', 'correctness.failure_policy', 'design.paired_order',
                 'design.replicates', 'design.profiler_separate', 'budget.gpu_minutes', 'budget.wall_minutes', 'budget.max_attempts', 'stop_rules'):
        field(path)
    baseline = manifest.get('baseline', {})
    if baseline.get('id') != hypothesis['baseline']:
        gaps.append('baseline.id must match the immutable hypothesis baseline')
    if manifest.get('candidate', {}).get('parent_git_sha') != baseline.get('git_sha'):
        gaps.append('Candidate parent must be the control git SHA')
    def compare_known(expected, actual, prefix):
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key not in {'id', 'unknown', 'notes'}:
                    compare_known(value, actual.get(key) if isinstance(actual, dict) else None, prefix + '.' + key)
        elif expected not in (None, '', 'unknown') and expected != actual:
            gaps.append('Plan conflicts with pinned hypothesis ' + prefix)
    compare_known(hypothesis['brief']['baseline'], baseline, 'baseline')
    for key in ('image_digest',):
        value = baseline.get(key)
        if value and not re.fullmatch(r'sha256:[0-9a-f]{64}', value):
            gaps.append('Container requires an immutable sha256 digest')
    for key in ('model', 'tokenizer'):
        value = baseline.get(key, {}).get('revision')
        if value and not re.fullmatch(r'(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})', value):
            gaps.append(key + ' revision must be a commit or sha256 digest')
    for path in ('baseline.hardware.gpu_count', 'baseline.parallelism.tp', 'baseline.parallelism.dp', 'baseline.parallelism.ep',
                 'design.replicates', 'budget.max_attempts'):
        value = field(path)
        if value is not None and (type(value) is not int or value < 1):
            gaps.append('Positive integer required: ' + path)
    for path in ('budget.gpu_minutes', 'budget.wall_minutes'):
        value = field(path)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0):
            gaps.append('Positive bounded budget required: ' + path)
    if manifest.get('design', {}).get('profiler_separate') is not True:
        gaps.append('Profiling must be separate from scored runs')
    objective = manifest.get('objective', {})
    if objective.get('direction') not in ('lower', 'higher'):
        gaps.append('Objective direction must be lower or higher')
    gain = objective.get('min_relative_gain')
    if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not math.isfinite(gain) or gain < 0:
        gaps.append('Minimum worthwhile gain must be an explicit nonnegative finite fraction')
    guards = objective.get('tail_guards', [])
    if not isinstance(guards, list) or any(not isinstance(g, dict) or not all(g.get(k) is not None for k in ('metric', 'unit', 'limit')) for g in guards):
        gaps.append('Tail guards need explicit metric/unit/limit')
    elif any(isinstance(g['limit'], bool) or not isinstance(g['limit'], (int, float)) or not math.isfinite(g['limit']) or g['limit'] < 0 for g in guards):
        gaps.append('Tail guard limits must be nonnegative finite values')
    # Existing evaluators must be assessed before another custom harness is added.
    evaluation = manifest.get('evaluation', {})
    existing = evaluation.get('existing', [])
    if not existing:
        gaps.append('Document existing evaluator coverage before proposing another evaluator')
    shortfalls = set()
    for evaluator in existing:
        if not all(evaluator.get(k) for k in ('name', 'stimuli', 'observables', 'reason')) or evaluator.get('coverage') not in ('sufficient', 'insufficient'):
            gaps.append('Evaluator needs named stimulus, observables and coverage justification')
        if evaluator.get('coverage') == 'insufficient':
            shortfalls.add(evaluator.get('name'))
        command = evaluator.get('command_argv')
        if not isinstance(command, list) or not command or any(not isinstance(v, str) for v in command):
            gaps.append('Evaluator command must be explicit argv; never executed by plan tool')
    addressed = set()
    for addition in evaluation.get('additions', []):
        if not addition.get('reason') or not set(addition.get('fills_gaps_in', [])) & shortfalls:
            gaps.append('Custom evaluator requires a specific gap in existing evaluators')
        else:
            addressed.update(set(addition['fills_gaps_in']) & shortfalls)
    if shortfalls - addressed:
        gaps.append('Existing evaluator shortfall has no proposed resolution')
    return {'blocking_gaps': list(dict.fromkeys(gaps)), 'readiness': 'blocked' if gaps else 'ready_for_review',
            'quality_gate_version': 'controlled-serving-plan-v1', 'scope': manifest.get('scope', 'service'),
            'execution_authorized': False, 'gpu_calls': 0,
            'meaning': 'Manifest completeness and consistency, not verified applicability or GPU approval'}

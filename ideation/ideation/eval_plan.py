"""Readiness checks for a controlled experiment, without executing its commands."""
import math
import re


def qualify_plan(manifest, hypothesis):
    if not isinstance(manifest, dict):
        raise ValueError('Evaluation manifest must be an object')
    if manifest.get('execution_kind') == 'cpu':
        return _qualify_cpu_diagnostic(manifest, hypothesis)
    gaps = []
    if manifest.get('execution_kind', 'serving') != 'serving':
        gaps.append('execution_kind must be cpu or serving')
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
            'scientific_validity': 'unverified', 'review_questions': _review_questions(),
            'meaning': 'Manifest completeness and consistency, not verified applicability or GPU approval'}



def _review_questions():
    return [
        'Does pinned implementation evidence show this mechanism can affect the target path?',
        'What current-baseline gap remains after checking existing code and previous attempts?',
        'Does the proposed stimulus expose the mechanism and the observable discriminate alternatives?',
        'Which finding changes the decision, and what remains unproven about service benefit?',
        'Are numerical bounds conditional on supported units, frequency, overlap and workload exposure?',
    ]


def _qualify_cpu_diagnostic(manifest, hypothesis):
    """Permit cheap source/replay checks without inventing a serving environment.

    This checks a plan, never executes argv or attests to artifact availability.
    A CPU diagnostic can resolve applicability or inputs to ROI; it cannot qualify
    target serving performance, even if all fields are filled.
    """
    gaps = []
    manifest = dict(manifest)
    for section in ('baseline', 'probe', 'diagnostic', 'evaluation', 'budget'):
        if not isinstance(manifest.get(section), dict):
            gaps.append(section + ' must be an object')
            manifest[section] = {}

    def required(path, allow_unknown=False):
        value = manifest
        for key in path.split('.'):
            value = value.get(key) if isinstance(value, dict) else None
        if value is None or value == '' or value == [] or value == {} or isinstance(value, str) and value.strip().lower() in ({'unset', 'tbd'} if allow_unknown else {'unknown', 'unset', 'tbd'}):
            gaps.append('Missing ' + path)
        return value

    def exact_hash(path, size):
        value = required(path)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{' + str(size) + '}', value):
            gaps.append('Not an exact hash: ' + path)

    if manifest.get('purpose') != 'diagnostic':
        gaps.append('CPU checks permit diagnostic purpose only, not serving qualification')
    if manifest.get('scope') not in ('component', 'native'):
        gaps.append('CPU diagnostic scope must be component or native; service benefit stays unverified')
    if required('baseline.id') != hypothesis['baseline']:
        gaps.append('baseline.id must match the immutable hypothesis baseline')
    # The baseline may be incompletely known; freezing the question does not
    # magically supply a container, GPU measurement, or implementation patch.
    supplied = manifest.get('baseline', {})
    pinned = hypothesis['brief']['baseline']

    def compare_supplied(actual, expected, prefix):
        if isinstance(actual, dict) and isinstance(expected, dict):
            for key, value in actual.items():
                if key not in {'id', 'unknown', 'notes'} and key in expected:
                    compare_supplied(value, expected[key], prefix + '.' + key)
        elif expected not in (None, '', 'unknown') and actual != expected:
            gaps.append('Plan conflicts with pinned hypothesis ' + prefix)

    compare_supplied(supplied, pinned, 'baseline')
    exact_hash('probe.git_sha', 40)
    for path in ('probe.description', 'probe.environment', 'probe.read_only',
                 'diagnostic.question', 'diagnostic.mechanism', 'diagnostic.target_code_path',
                 'diagnostic.observable', 'diagnostic.supports_if', 'diagnostic.refutes_if',
                 'diagnostic.inconclusive_if', 'diagnostic.limitations', 'stop_rules'):
        required(path)
    if manifest.get('probe', {}).get('read_only') is not True:
        gaps.append('CPU diagnostic must declare read_only=true for the serving deployment')
    argv = required('probe.command_argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(v, str) or not v.strip() for v in argv):
        gaps.append('Probe command must be explicit nonempty argv; plan tool never executes it')
    inputs = required('probe.inputs')
    if not isinstance(inputs, list) or not inputs:
        gaps.append('Pin at least one inspected source, fixture or replay input')
    else:
        for item in inputs:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ('id', 'role')) or not re.fullmatch(r'[0-9a-f]{64}', str(item.get('sha256', ''))):
                gaps.append('Each probe input needs id, role and exact sha256')
    status = required('diagnostic.target_path_status', allow_unknown=True)
    if status not in ('observed', 'configured', 'unknown', 'proposed'):
        gaps.append('target_path_status must distinguish observed/configured/unknown/proposed applicability')
    existing = manifest.get('evaluation', {}).get('existing', [])
    if not isinstance(existing, list) or not existing:
        gaps.append('Document existing evaluator coverage before proposing a CPU probe')
    else:
        for evaluator in existing:
            if not isinstance(evaluator, dict) or not evaluator.get('name') or not evaluator.get('reason') or evaluator.get('coverage') not in ('sufficient', 'insufficient', 'not_applicable'):
                gaps.append('Existing evaluator needs name, coverage and question-specific reason')
    gpu = required('budget.gpu_minutes')
    if isinstance(gpu, bool) or not isinstance(gpu, (int, float)) or gpu != 0:
        gaps.append('CPU diagnostic requires budget.gpu_minutes=0')
    wall = required('budget.wall_minutes')
    if isinstance(wall, bool) or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall <= 0:
        gaps.append('Positive bounded budget required: budget.wall_minutes')
    attempts = required('budget.max_attempts')
    if type(attempts) is not int or attempts < 1:
        gaps.append('Positive integer required: budget.max_attempts')
    return {'blocking_gaps': list(dict.fromkeys(gaps)), 'readiness': 'blocked' if gaps else 'ready_for_review',
            'quality_gate_version': 'cpu-diagnostic-plan-v1', 'scope': manifest.get('scope'),
            'execution_kind': 'cpu', 'execution_authorized': False, 'gpu_calls': 0,
            'scientific_validity': 'unverified', 'target_relative_gain': None,
            'review_questions': _review_questions(),
            'meaning': 'Pinned bounded diagnostic plan only; no proof of applicability, service gain or execution approval'}

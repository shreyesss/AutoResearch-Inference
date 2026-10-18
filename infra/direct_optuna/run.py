"""Thin study adapter around the pinned InseeFrLab auto-tuning-vllm controller.

Upstream owns Optuna ask/tell, trial lifecycle, vLLM processes and persistence.
This adapter specifies our mixed input, two independent GuideLLM windows,
conditional graph setting, sampler seed, and evidence validation.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import logging
import math
import os
import sys
import time
from pathlib import Path

import optuna
import numpy as np
from auto_tune_vllm.benchmarks.providers import GuideLLMBenchmark
from auto_tune_vllm.core.config import StudyConfig
from auto_tune_vllm.core.study_controller import StudyController
from auto_tune_vllm.execution.backends import LocalExecutionBackend
from auto_tune_vllm.execution import trial_controller

STUDY = Path('/study')
PROTOCOL = {}


def write(path, data):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


class MixedGuideLLMBenchmark(GuideLLMBenchmark):
    def _get_results_file_path(self):
        root = STUDY / PROTOCOL['phase'] / self._trial_context['trial_id']
        root.mkdir(parents=True)
        return str(root / 'native.json')

    def _build_guidellm_command(self, model_url, config, results_file):
        spec = dict(PROTOCOL, model=config.model, url=model_url, output=results_file,
                    benchmark_started_unix=time.time())
        path = Path(results_file).with_name('measurement-spec.json')
        write(path, spec)
        return [sys.executable, '/code/measure.py', str(path)]

    def _parse_guidellm_results(self, data):
        benchmarks = data['benchmarks']
        if len(benchmarks) != len(PROTOCOL['streams']):
            raise ValueError('Missing benchmark windows')
        audit = []
        for b in benchmarks:
            counts = b['scheduler_metrics']['requests_made']
            if counts['errored'] or counts['incomplete'] or not counts['successful']:
                raise ValueError(f'Non-complete request accounting: {counts}')
            rows = b['requests']['successful']
            seen = set()
            for r in rows:
                body = json.loads(r['request_args'])['body']
                planned = body.get('max_completion_tokens', body.get('max_tokens'))
                if r['output_tokens'] != planned:
                    raise ValueError(f'Output cap mismatch {r["output_tokens"]} != {planned}')
                key = json.dumps(body['messages'], sort_keys=True)
                if key in seen:
                    raise ValueError('Repeated full prompt within measurement window')
                seen.add(key)
            audit.append({'counts': counts, 'stored_successful_requests': len(rows),
                          'unique_full_prompts': len(seen)})
        # Evaluate the same predeclared anchor in every candidate. Keep all other
        # points as native results, never select a candidate's best rate afterward.
        index = PROTOCOL['streams'].index(PROTOCOL['objective_concurrency'])
        values = super()._parse_guidellm_results({'benchmarks': [benchmarks[index]]})
        # GuideLLM weights aggregate ITL by output-token count. Our objective is
        # the percentile across users/requests, with one vote per request.
        measured = benchmarks[index]['requests']['successful']
        for metric in ('time_to_first_token_ms', 'inter_token_latency_ms'):
            samples = [r[metric] for r in measured]
            if any(v is None or not math.isfinite(v) or v <= 0 for v in samples):
                raise ValueError(f'Invalid per-request {metric}')
            values[f'{metric}_native_p90'] = values[f'{metric}_p90']
            for p in (50, 90, 99):
                values[f'{metric}_p{p}'] = float(np.percentile(samples, p))
            values[f'{metric}_median'] = values[f'{metric}_p50']
        for name in ('output_tokens_per_second_mean', 'time_to_first_token_ms_p90',
                     'inter_token_latency_ms_p90'):
            if not math.isfinite(values[name]) or values[name] <= 0:
                raise ValueError(f'Invalid objective {name}: {values.get(name)}')
        write(Path(self._results_file).with_name('validation.json'), audit)
        return values


class MixedStudyController(StudyController):
    @staticmethod
    def _create_sampler(config):
        return optuna.samplers.TPESampler(seed=20261018,
            n_startup_trials=config.optimization.n_startup_trials,
            multivariate=True, group=True)

    def _build_trial_config(self, trial):
        # Upstream samples each configured parameter. Temporarily exclude the
        # graph cap when eager is chosen; retain upstream's TrialConfig builder.
        if 'enforce_eager' in self.config.parameters:
            self.config.parameters['enforce_eager'].generate_optuna_suggest(trial)
        graph = None
        if trial.params.get('enforce_eager'):
            graph = self.config.parameters.pop('max_cudagraph_capture_size', None)
        try:
            config = super()._build_trial_config(trial)
        finally:
            if graph is not None:
                self.config.parameters['max_cudagraph_capture_size'] = graph
        if config.parameters.get('enforce_eager'):
            config.parameters.pop('max_cudagraph_capture_size', None)
        trial.set_user_attr('resolved_parameters', config.parameters)
        return config

    def _collect_completed_trials(self):
        n = super()._collect_completed_trials()
        trials = self.study.get_trials(deepcopy=False)
        if n:
            history = [{'number': t.number, 'state': t.state.name,
                'params': t.params, 'values': t.values, 'attrs': t.user_attrs,
                'started': t.datetime_start, 'finished': t.datetime_complete,
                'total_wall_seconds': t.duration.total_seconds() if t.duration else None} for t in trials]
            write(STUDY / 'trials.json', history)
            write(STUDY / f'{PROTOCOL["phase"]}-trials.json', history)
            if trials[0].state == optuna.trial.TrialState.FAIL:
                raise RuntimeError('Matched baseline failed; stopping before candidate comparisons')
            if len(trials) >= 3 and all(t.state == optuna.trial.TrialState.FAIL for t in trials[-3:]):
                raise RuntimeError('Three consecutive failed trials; stopping for inspection')
        write(STUDY / 'status.json', {'phase': PROTOCOL['phase'], 'updated_unix': time.time(),
            'completed': sum(t.state == optuna.trial.TrialState.COMPLETE for t in trials),
            'failed': sum(t.state == optuna.trial.TrialState.FAIL for t in trials),
            'running': [t.number for t in trials if t.state == optuna.trial.TrialState.RUNNING],
            'study_name': self.study.study_name, 'protocol': PROTOCOL})
        return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['calibration', 'search', 'confirmation'])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    lock = open('/locks/GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83.lock', 'a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    raw = json.loads(Path('/config/study.json').read_text())
    phase = args.phase
    write(STUDY / f'{phase}-source-hashes.json', {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [*Path('/code').glob('*.py'), Path('/config/study.json')]})
    if phase == 'calibration':
        PROTOCOL.update(phase=phase, streams=[1, 4, 8, 16, 32], requests=[8, 40, 40, 40, 40],
                        point_timeout_seconds=600, objective_concurrency=8, split_prefix='dev')
        raw['optimization']['n_trials'] = 1
        raw['optimization']['n_startup_trials'] = 0
        raw['parameters'] = {'max_num_seqs': {'enabled': True, 'options': [512]}}
    elif phase == 'search':
        calibration = json.loads((STUDY / 'calibration/trial_0/native.json').read_text())
        if not (STUDY / 'calibration/trial_0/validation.json').exists():
            raise RuntimeError('Calibration has no successful validation receipt')
        points = []
        for c, b in zip([1, 4, 8, 16, 32], calibration['benchmarks'], strict=True):
            points.append((c, b['metrics']['output_tokens_per_second']['total']['mean']))
        peak = max(v for _, v in points)
        high = next(c for c, v in points if c >= 4 and v >= 0.9 * peak)
        low = max(1, high // 2)
        PROTOCOL.update(phase=phase, streams=[low, high], requests=[120, 120],
                        point_timeout_seconds=600, objective_concurrency=high, split_prefix='dev')
        write(STUDY / 'anchor-selection.json', {'points': points, 'low': low, 'high': high,
            'rule': 'first tested concurrency >=4 reaching 90% of observed maximum throughput',
            'capacity_claim': False})
    else:
        selection = json.loads((STUDY / 'confirmation-selection.json').read_text())
        anchors = json.loads((STUDY / 'anchor-selection.json').read_text())
        high = anchors['high']
        PROTOCOL.update(phase=phase, streams=[anchors['low'], high, high * 2],
                        requests=[120, 120, 120], point_timeout_seconds=600,
                        objective_concurrency=high, split_prefix='test')
        raw['optimization']['n_trials'] = len(selection['sequence'])
        raw['optimization']['n_startup_trials'] = 0
    raw['study']['name'] = 'qwen-direct-optuna-v1-' + phase
    raw['study']['storage_file'] = f'/study/{phase}.sqlite3'
    # This field is upstream's whole-worker watchdog budget. Individual native
    # GuideLLM fixed cohort and point watchdog are specified in PROTOCOL.
    raw['benchmark']['max_seconds'] = len(PROTOCOL['streams']) * 690
    raw['benchmark']['rate'] = PROTOCOL['objective_concurrency']
    config_path = STUDY / f'{phase}-resolved-config.json'
    write(config_path, raw)
    write(STUDY / f'{phase}-protocol.json', PROTOCOL)
    config = StudyConfig.from_file(str(config_path), vllm_version='0.28.0')
    trial_controller.GuideLLMBenchmark = MixedGuideLLMBenchmark
    controller = MixedStudyController.create_from_config(LocalExecutionBackend(1), config)
    if phase == 'search':
        b0 = {k: raw['static_parameters'][k] for k in raw['parameters']}
        controller.study.enqueue_trial(b0, user_attrs={'role': 'matched_B0'})
    elif phase == 'confirmation':
        for item in selection['sequence']:
            controller.study.enqueue_trial(item['params'], user_attrs={
                'role': item['role'], 'search_trial': item['search_trial']})
    try:
        controller.run_optimization(max_concurrent_trials=1)
        write(STUDY / f'{phase}-finished.json', {'time': time.time(),
            'complete': sum(t.state == optuna.trial.TrialState.COMPLETE for t in controller.study.trials),
            'failed': sum(t.state == optuna.trial.TrialState.FAIL for t in controller.study.trials)})
    except BaseException as exc:
        write(STUDY / 'fatal.json', {'phase': phase, 'error': repr(exc), 'time': time.time()})
        raise


if __name__ == '__main__':
    main()

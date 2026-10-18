"""Run native GuideLLM windows against the server owned by auto-tuning-vllm."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests


def main():
    spec = json.loads(Path(sys.argv[1]).read_text())
    root = Path(spec['output']).parent
    root.mkdir(parents=True, exist_ok=True)
    def progress(stage, **details):
        data = {'phase': spec['phase'], 'trial': root.name, 'stage': stage,
                'updated_unix': time.time(), **details}
        path = Path('/study/measurement-progress.json')
        tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(data, indent=2)); tmp.replace(path)
    report = None
    for index, streams in enumerate(spec['streams']):
        split = spec['split_prefix'] + ('-a' if index % 2 == 0 else '-b')
        point = root / f'c{streams}-window{index}'
        point.mkdir()
        progress('cache_preparation', concurrency=streams, point=index)
        url = spec['url'].removesuffix('/v1')
        reset = requests.post(url + '/reset_prefix_cache', timeout=30)
        reset.raise_for_status()
        rows = json.loads(Path(f'/study/{split}-warmup.json').read_text())
        def warm(row):
            body = {'model': spec['model'], 'messages': [
                {'role': 'system', 'content': row['system_prompt']},
                {'role': 'user', 'content': row['prompt']}], 'max_tokens': 1,
                'temperature': 0, 'ignore_eos': True,
                'chat_template_kwargs': {'enable_thinking': False}}
            r = requests.post(url + '/v1/chat/completions', json=body, timeout=120)
            r.raise_for_status()
            return r.json().get('usage')
        # A wire probe verifies the exact model-template input count and output cap.
        probe = json.loads(Path(f'/study/{split}.jsonl').read_text().splitlines()[0])
        probe_usage = warm(probe)
        if probe_usage['prompt_tokens'] != probe['expected_input_tokens']:
            raise ValueError(f'Input token mismatch: {probe_usage}, expected {probe["expected_input_tokens"]}')
        # Remove the full-prefix cache entry introduced by that wire probe.
        requests.post(url + '/reset_prefix_cache', timeout=30).raise_for_status()
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            usages = []
            for usage in executor.map(warm, rows):
                usages.append(usage)
                progress('cache_preparation', concurrency=streams, point=index,
                         completed_prefixes=len(usages), total_prefixes=len(rows))
        (point / 'warmup.json').write_text(json.dumps({'seconds': time.time()-start, 'usage': usages}))
        native = point / 'guidellm.json'
        backend = {'kind': 'openai_http', 'target': url, 'model': spec['model'],
                   'request_format': '/v1/chat/completions', 'stream': True, 'timeout': 120,
                   'extras': {'body': {'temperature': 0,
                                      'chat_template_kwargs': {'enable_thinking': False}}}}
        cmd = ['guidellm', 'run', '--backend', json.dumps(backend),
               '--tokenizer', json.dumps({'kind': 'huggingface_auto', 'model': spec['model']}),
               '--data', json.dumps({'kind': 'json_file', 'path': f'/study/{split}.jsonl',
                                    'load_kwargs': {'split': 'train'}}),
               '--data-loader', 'kind=pytorch,num_workers=0,shuffle=false',
               '--profile', json.dumps({'kind': 'concurrent', 'streams': streams}),
               '--constraint', f'kind=max_requests,count={spec["requests"][index]}',
               '--metrics', 'kind=generative,sample_size=10000',
               '--output', f'kind=json,path={native}', '--seed', 'kind=static,value=20261018']
        (point / 'command.json').write_text(json.dumps(cmd, indent=2))
        (point / 'metrics-before.prom').write_text(requests.get(url + '/metrics', timeout=10).text)
        start = time.time()
        progress('benchmarking', concurrency=streams, point=index,
                 planned_requests=spec['requests'][index], console=str(point / 'console.log'))
        with (point / 'console.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                           timeout=spec['point_timeout_seconds'], check=True)
        (point / 'metrics-after.prom').write_text(requests.get(url + '/metrics', timeout=10).text)
        data = json.loads(native.read_text())
        counts = data['benchmarks'][0]['scheduler_metrics']['requests_made']
        if counts['errored'] or counts['incomplete'] or counts['successful'] != spec['requests'][index]:
            raise ValueError(f'Incomplete cohort: {counts}')
        expected = [json.loads(line) for line in Path(f'/study/{split}.jsonl').read_text().splitlines()]
        expected = {r['request_id']: r for r in expected[:spec['requests'][index]]}
        seen = set()
        class_counts = {}
        for request in data['benchmarks'][0]['requests']['successful']:
            match = re.search(r'Request ([\w-]+)\.', request['request_args'] or '')
            request_id = match[1] if match else None
            if request_id not in expected or request_id in seen:
                raise ValueError(f'Unexpected or repeated request: {request_id}')
            row = expected[request_id]
            if request['prompt_tokens'] != row['expected_input_tokens'] or request['output_tokens'] != row['output_tokens_count']:
                raise ValueError(f'Token mismatch for {request_id}: measured input/output '
                    f'{request["prompt_tokens"]}/{request["output_tokens"]}, expected '
                    f'{row["expected_input_tokens"]}/{row["output_tokens_count"]}')
            seen.add(request_id)
            c = row['request_class']
            class_counts[c] = class_counts.get(c, 0) + 1
        if seen != set(expected):
            raise ValueError('Request records do not cover the exact frozen cohort')
        (point / 'point.json').write_text(json.dumps({'concurrency': streams,
            'wall_seconds': time.time()-start, 'requests': spec['requests'][index],
            'dataset': split, 'native': str(native),
            'class_counts': class_counts, 'all_token_counts_verified': True,
            'dataset_sha256': hashlib.sha256(Path(f'/study/{split}.jsonl').read_bytes()).hexdigest(),
            'measurement_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'wire_probe_usage': probe_usage}, indent=2))
        if report is None:
            report = data
        else:
            report['benchmarks'].extend(data['benchmarks'])
        # Publish partial native evidence while the remaining windows run.
        Path(spec['output']).write_text(json.dumps(report))
        progress('point_complete', concurrency=streams, point=index, requests=counts,
                 class_counts=class_counts)
    print('GuideLLM windows completed', flush=True)


if __name__ == '__main__':
    main()

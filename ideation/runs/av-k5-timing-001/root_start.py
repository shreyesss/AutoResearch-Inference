"""Orchestrator-only diagnostic startup. Never install or modify packages."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import socket
import subprocess

HERE = Path(__file__).resolve().parent
SERVE = Path('/home/ubuntu/Deepseek_serve-c03')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE / 'startup-processes.json').exists(), 'startup is not retryable implicitly'
    assert subprocess.check_output(['docker', 'ps', '-q'], text=True).strip() == ''
    for port in [8000, 8100, 8101]:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            assert sock.connect_ex(('127.0.0.1', port)) != 0, f'port {port} occupied'
    gpus = subprocess.check_output([
        'nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits'], text=True)
    assert len(gpus.strip().splitlines()) == 8
    assert all(int(line.split(',')[2]) == 0 for line in gpus.strip().splitlines())
    previous = json.loads((HERE.parent / 'c03-execution-001/final-integrity-check.json').read_text())
    checks = []
    for item in previous['original_files']:
        actual = digest(Path(item['path']))
        assert actual == item['sha256'], item['path']
        checks.append({'path': item['path'], 'sha256': actual})
    argv_path = SERVE / 'av-k5/rendered-backends.json'
    rendered = json.loads(argv_path.read_text())
    assert digest(argv_path) == 'e75711be87a18fb707c5f1fa03e1c9c322d36c0a636983051117b8f3fa64df0d'
    attestation = json.loads((HERE / 'installed-source-attestation.json').read_text())
    mismatches = [f['path'] for f in attestation['files'] if not f['matches']]
    assert mismatches == ['vllm/models/deepseek_v41/nvidia/model_state.py']
    preflight = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'node': socket.gethostname(), 'gpu_inventory': gpus,
                 'original_files': checks, 'rendered_argv_sha256': digest(argv_path),
                 'initial_state': 'all GPUs idle; ports closed; no containers',
                 'installed_source_difference': 'Preserve installed model_state.py; reviewed separately; no override'}
    for label, interpreter in [('launcher', '/home/ubuntu/Deepseek_serve/.venv/bin/python'),
                               ('client', '/home/ubuntu/Deepseek_serve/.venv-aiperf/bin/python')]:
        data = subprocess.check_output([interpreter, '-c',
            'import importlib.metadata,json;print(json.dumps(sorted((d.metadata["Name"],d.version) for d in importlib.metadata.distributions())))'])
        (HERE / f'original-{label}-packages.json').write_bytes(data)
        preflight[f'{label}_packages_sha256'] = hashlib.sha256(data).hexdigest()
    (HERE / 'preflight.json').write_text(json.dumps(preflight, indent=2) + '\n')
    processes = []
    for item in rendered['commands']:
        log = HERE / f'startup-replica-{item["replica"]}.log'
        with log.open('xb') as output:
            proc = subprocess.Popen(item['argv'], stdout=output, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        processes.append({'replica': item['replica'], 'pid': proc.pid, 'log': str(log),
                          'argv': item['argv']})
    result = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'processes': processes, 'adaptive_verification': False,
              'purpose': 'diagnostic baseline startup only'}
    (HERE / 'startup-processes.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'started_pids': [p['pid'] for p in processes]}))


if __name__ == '__main__':
    main()

"""Stop only this diagnostic's attested processes and verify original files."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import os
import signal
import socket
import subprocess
import time

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')


def main():
    assert (HERE / 'collection.json').is_file()
    assert json.loads((HERE / 'drain.json').read_text())['status'] == 'pass'
    assert json.loads((HERE / 'final-runtime-identity.json').read_text())['status'] == 'pass'
    identity = json.loads((HERE / 'runtime-identity.json').read_text())
    router = json.loads((HERE / 'router-process.json').read_text())
    argv = Path(f'/proc/{router["pid"]}/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    assert argv == router['argv'], 'router PID identity changed'
    for container in identity['containers']:
        current = json.loads(subprocess.check_output(['docker', 'inspect', container['id']]))[0]
        assert current['Id'] == container['id'] and current['State']['StartedAt'] == container['started_at']
    receipt = {'started_ns': time.time_ns(), 'containers': [], 'router_pid': router['pid']}
    save('cleanup.json', receipt)
    def stop(container):
        result = subprocess.run(['docker', 'stop', '--time', '30', container['id']], capture_output=True, text=True, timeout=45)
        return {'id': container['id'], 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        receipt['containers'] = list(pool.map(stop, identity['containers']))
    os.kill(router['pid'], signal.SIGTERM)
    for attempt in range(20):
        ports = {}
        for port in [8000, 8100, 8101, 9400]:
            with socket.socket() as sock:
                sock.settimeout(.2)
                ports[str(port)] = sock.connect_ex(('127.0.0.1', port)) == 0
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True)
        idle = all(int(line.split(',')[2]) == 0 for line in gpu.strip().splitlines())
        if idle and not any(ports[str(port)] for port in [8000, 8100, 8101]):
            break
        time.sleep(1)
    receipt.update(finished_ns=time.time_ns(), ports_listening=ports, gpu_inventory=gpu,
                   owned_services_stopped=idle and not any(ports[str(p)] for p in [8000, 8100, 8101]),
                   monitoring_preserved=ports['9400'])
    save('cleanup.json', receipt)
    before = json.loads((HERE / 'pre-client-integrity.json').read_text())
    checks = []
    for item in before['checks']:
        actual = digest(Path(item['path']))
        checks.append({'path': item['path'], 'expected': item['expected'], 'sha256': actual,
                       'matches': actual == item['expected']})
    package_checks = []
    for label, interpreter in [('launcher', '/home/ubuntu/Deepseek_serve/.venv/bin/python'),
                               ('client', '/home/ubuntu/Deepseek_serve/.venv-aiperf/bin/python')]:
        data = subprocess.check_output([interpreter, '-c', 'import importlib.metadata,json;print(json.dumps(sorted((d.metadata["Name"],d.version) for d in importlib.metadata.distributions())))'])
        (HERE / f'final-{label}-packages.json').write_bytes(data)
        package_checks.append({'environment': label, 'matches': data == (HERE / f'original-{label}-packages.json').read_bytes(),
                               'sha256': hashlib.sha256(data).hexdigest()})
    result = {'time_ns': time.time_ns(), 'checks': checks, 'package_checks': package_checks,
              'status': 'pass' if all(x['matches'] for x in checks + package_checks) else 'failed'}
    save('final-integrity.json', result)
    print(json.dumps({'cleanup': receipt['owned_services_stopped'], 'monitoring_preserved': receipt['monitoring_preserved'], 'integrity': result['status']}))


if __name__ == '__main__':
    main()

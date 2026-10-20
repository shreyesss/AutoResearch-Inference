"""Orchestrator read-only binding of ready containers, workers, GPUs and sources."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
SERVE = Path('/home/ubuntu/Deepseek_serve-c03')
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
WORKER = re.compile(r'\(Worker_DP(\d+)(?:_[A-Za-z0-9_]+)? pid=(\d+)\)')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, response.read()


def main():
    output = HERE / 'runtime-identity.json'
    assert not output.exists(), 'preserve existing runtime identity'
    manifest_path = SERVE / 'av-k5/observation-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    rendered = json.loads((SERVE / 'av-k5/rendered-backends.json').read_text())
    gpu_rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
                                        '--format=csv,noheader,nounits'], text=True)
    gpu_map = {int(row.split(',')[0]): row.split(',')[1].strip()
               for row in gpu_rows.strip().splitlines()}
    app_rows = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                        '--format=csv,noheader,nounits'], text=True)
    apps = []
    for row in app_rows.strip().splitlines():
        uuid, host_pid = [part.strip() for part in row.split(',')]
        status = Path(f'/proc/{host_pid}/status').read_text()
        namespace_pid = int(re.search(r'^NSpid:\s+(.*)$', status, re.M)[1].split()[-1])
        apps.append({'gpu_uuid': uuid, 'host_pid': int(host_pid), 'worker_pid': namespace_pid,
                     'cgroup': Path(f'/proc/{host_pid}/cgroup').read_text().strip()})
    containers, workers = [], []
    for replica in range(2):
        name = f'dsv41-h200-vllm-latency-2xdep4-sla-{replica}'
        inspect = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
        assert inspect['State']['Running'] and inspect['Config']['Image'] == manifest['image']
        expected = rendered['commands'][replica]['argv']
        assert inspect['Config']['Cmd'] == expected[expected.index(manifest['image']) + 1:]
        assert inspect['Config']['Entrypoint'] == ['vllm']
        for item in manifest['files']:
            dest = '/usr/local/lib/python3.12/dist-packages/' + item['path']
            matches = [m for m in inspect['Mounts'] if m['Destination'] == dest]
            assert len(matches) == 1 and matches[0]['RW'] is False
            assert matches[0]['Source'] == str((SERVE / 'av-k5' / item['source']).resolve())
        code = ('import hashlib,json,pathlib,sys;'
                'print(json.dumps({p:hashlib.sha256(pathlib.Path("/usr/local/lib/python3.12/dist-packages",p).read_bytes()).hexdigest() for p in json.loads(sys.argv[1])}))')
        paths = [f['path'] for f in manifest['files']] + [
            'vllm/v1/worker/gpu/dp_utils.py',
            'vllm/models/deepseek_v41/nvidia/model_state.py']
        hashes = json.loads(subprocess.check_output(['docker', 'exec', name, 'python3', '-c', code, json.dumps(paths)]))
        for item in manifest['files']:
            assert hashes[item['path']] == item['sha256']
        assert hashes['vllm/v1/worker/gpu/dp_utils.py'] == 'b81a663c7e736f93c7be6ff7b6facebeb93ee4a52c280163b2ba9146fe33c341'
        assert hashes['vllm/models/deepseek_v41/nvidia/model_state.py'] == 'b60e0fff9ac60561f569a3beb2bc9ca431b14e3c2833d8537b3f866d5e7340de'
        health, _ = get(f'http://127.0.0.1:{8100 + replica}/health')
        _, body = get(f'http://127.0.0.1:{8100 + replica}/v1/models')
        models = json.loads(body)
        assert health == 200 and models['data'][0]['id'] == 'deepseek-v4.1-flash'
        log = HERE / f'ready-replica-{replica}.log'
        with log.open('xb') as stream:
            subprocess.run(['docker', 'logs', '--timestamps', name], stdout=stream, stderr=subprocess.STDOUT, check=True)
        lines = ANSI.sub('', log.read_text()).splitlines()
        rank_pids = {rank: set() for rank in range(4)}
        completions = {rank: [] for rank in range(4)}
        completion_lines = {rank: [] for rank in range(4)}
        full_capture_lines = {rank: [] for rank in range(4)}
        for line_number, line in enumerate(lines, 1):
            match = WORKER.search(line)
            if match:
                rank, pid = map(int, match.groups())
                rank_pids[rank].add(pid)
                if 'Graph capturing finished' in line:
                    completions[rank].append(line)
                    completion_lines[rank].append(line_number)
                if 'CG Capture: mode=FULL,' in line:
                    full_capture_lines[rank].append(line_number)
        assert all(len(pids) == 1 for pids in rank_pids.values())
        assert all(len(rows) >= 2 for rows in completions.values())
        assert all(full_capture_lines[rank] and
                   completion_lines[rank][-1] > full_capture_lines[rank][-1]
                   for rank in range(4))
        engine_done = [line for line in lines if 'init engine (profile, create kv cache, warmup model) took' in line]
        api_ready = [line for line in lines if 'Application startup complete.' in line]
        assert len(engine_done) == 4 and len(api_ready) == 2
        for rank in range(4):
            pid = next(iter(rank_pids[rank]))
            uuid = gpu_map[replica * 4 + rank]
            matches = [a for a in apps if a['worker_pid'] == pid and a['gpu_uuid'] == uuid
                       and inspect['Id'] in a['cgroup']]
            assert len(matches) == 1, (replica, rank, pid, uuid)
            stat = subprocess.check_output(['docker', 'exec', name, 'cat', f'/proc/{pid}/stat'], text=True)
            start_ticks = stat.rsplit(')', 1)[1].split()[19]
            workers.append({'replica': replica, 'rank': rank, 'worker_pid': pid,
                            'container_id': inspect['Id'], 'gpu_uuid': uuid,
                            'host_pid': matches[0]['host_pid'], 'start_ticks': start_ticks,
                            'capture_completions': completions[rank],
                            'capture_completion_lines': completion_lines[rank],
                            'last_full_capture_line': full_capture_lines[rank][-1]})
        containers.append({'replica': replica, 'name': name, 'id': inspect['Id'],
                           'image': inspect['Image'], 'configured_image': inspect['Config']['Image'],
                           'started_at': inspect['State']['StartedAt'],
                           'engine_args': inspect['Config']['Cmd'], 'source_hashes': hashes,
                           'health': health, 'models': models, 'engine_completions': engine_done,
                           'api_ready': api_ready, 'log': {'path': str(log), 'sha256': digest(log)}})
    receipt = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'containers': containers, 'workers': workers, 'status': 'ready_identity_pass',
               'observation_manifest_sha256': digest(manifest_path),
               'contract_sha256': digest(HERE / 'EVALUATION_CONTRACT.md')}
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'workers': len(workers), 'receipt': str(output)}))


if __name__ == '__main__':
    main()

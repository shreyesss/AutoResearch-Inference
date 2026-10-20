"""Root-only post-client collection and strict drain, without server shutdown."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.request

HERE = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')


def stop(port):
    result = {'port': port, 'sent_ns': time.time_ns()}
    try:
        request = urllib.request.Request(f'http://127.0.0.1:{port}/stop_profile', data=b'', method='POST')
        with urllib.request.urlopen(request, timeout=10) as response:
            result.update(status=response.status, body=response.read().decode())
    except Exception as exc:
        result['error'] = str(exc)
    result['finished_ns'] = time.time_ns()
    return result


def main():
    completion = json.loads((HERE / 'process-completion.json').read_text())
    assert not (HERE / 'collection.json').exists(), 'preserve prior collection'
    # The ordinary runner returns1 for a fully exported but SLO-ineligible run.
    # Service eligibility is not this diagnostic's fidelity gate.
    assert completion['client_exit_code'] in [0, 1]
    run_dir = Path(completion['run_directories'][0])
    status = json.loads((run_dir / 'status.json').read_text())
    assert status['message'] == 'AIPerf workload complete'
    assert (run_dir / 'score.json').is_file()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        save('final-profile-stop.json', list(pool.map(stop, [8100, 8101])))
    samples, streak, deadline = [], 0, time.monotonic() + 60
    while time.monotonic() < deadline and streak < 3:
        sample = {'time_ns': time.time_ns(), 'values': {}, 'errors': []}
        for port in [8000, 8100, 8101]:
            try:
                raw = urllib.request.urlopen(f'http://127.0.0.1:{port}/metrics', timeout=3).read().decode()
                pattern = (r'^dsv41_router_in_flight\{backend="([01])"\}\s+([\d.eE+-]+)$' if port == 8000 else
                           r'^vllm:(num_requests_running|num_requests_waiting)\{([^}]*)\}\s+([\d.eE+-]+)$')
                values = {}
                for line in raw.splitlines():
                    match = re.match(pattern, line)
                    if not match:
                        continue
                    if port == 8000:
                        key, value = match[1], float(match[2])
                    else:
                        engine = re.search(r'(?:^|,)engine="([0-3])"(?:,|$)', match[2])
                        if engine is None:
                            raise ValueError('missing engine label')
                        key, value = match[1] + ':' + engine[1], float(match[3])
                    if key in values:
                        raise ValueError('duplicate gauge')
                    values[key] = value
                expected = {'0', '1'} if port == 8000 else {
                    f'{kind}:{rank}' for kind in ['num_requests_running', 'num_requests_waiting'] for rank in range(4)}
                if set(values) != expected:
                    raise ValueError(f'missing/unexpected gauges: {set(values) ^ expected}')
                sample['values'][str(port)] = values
            except Exception as exc:
                sample['errors'].append({'port': port, 'error': str(exc)})
        sample['all_zero'] = not sample['errors'] and all(v == 0 for group in sample['values'].values() for v in group.values())
        streak = streak + 1 if sample['all_zero'] else 0
        samples.append(sample)
        if streak < 3:
            time.sleep(1)
    save('drain.json', {'status': 'pass' if streak == 3 else 'failed', 'required_consecutive': 3, 'samples': samples})
    identity = json.loads((HERE / 'runtime-identity.json').read_text())
    final = {'time_ns': time.time_ns(), 'workers': [], 'containers': []}
    for worker in identity['workers']:
        proc = Path('/proc') / str(worker['host_pid'])
        # /proc/PID/stat field22, after removing the parenthesized command.
        ticks = proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19]
        final['workers'].append({'replica': worker['replica'], 'rank': worker['rank'],
                                 'host_pid': worker['host_pid'], 'start_ticks': ticks,
                                 'matches_startup': ticks == worker['start_ticks']})
    for container in identity['containers']:
        current = json.loads(subprocess.check_output(['docker', 'inspect', container['id']]))[0]
        paths = ['/usr/local/lib/python3.12/dist-packages/' + p for p in container['source_hashes']]
        raw = subprocess.check_output(['docker', 'exec', container['id'], 'sha256sum', *paths], text=True)
        hashes = {line.split()[1].removeprefix('/usr/local/lib/python3.12/dist-packages/'): line.split()[0] for line in raw.splitlines()}
        final['containers'].append({'replica': container['replica'], 'id': current['Id'],
            'started_at': current['State']['StartedAt'], 'running': current['State']['Running'],
            'source_hashes': hashes, 'matches_startup': current['State']['StartedAt'] == container['started_at']
            and current['Args'] == container['engine_args'] and hashes == container['source_hashes']})
    final['status'] = 'pass' if all(x['matches_startup'] for group in ['workers','containers'] for x in final[group]) else 'failed'
    save('final-runtime-identity.json', final)
    files = []
    for container in identity['containers']:
        path = HERE / f'final-replica-{container["replica"]}.log'
        with path.open('xb') as output:
            subprocess.run(['docker', 'logs', '--timestamps', container['id']], stdout=output, stderr=subprocess.STDOUT, check=True)
        files.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)})
    source = Path('/home/jl_fs/profiler-cache/av-k5-timing-001')
    for src in sorted(source.rglob('*')):
        if not src.is_file():
            continue
        dst = HERE / 'traces' / src.relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        assert not dst.exists()
        shutil.copy2(src, dst)
        checksum = digest(dst)
        assert checksum == digest(src)
        files.append({'source': str(src), 'path': str(dst), 'bytes': dst.stat().st_size, 'sha256': checksum})
    save('collection.json', {'time_ns': time.time_ns(), 'files': files,
         'all_trace_files_retained': True, 'client_completion': completion,
         'containers_still_running_for_final_root_cleanup': True})
    print(json.dumps({'collected_files': len(files), 'drain': streak == 3, 'identity': final['status']}))


if __name__ == '__main__':
    main()

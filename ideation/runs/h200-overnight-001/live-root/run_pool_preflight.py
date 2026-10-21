"""Supervise the reviewed component runner with an independent120-second cap."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def identity(pid):
    return (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    run_id = 'live-event-pool-001'
    files = [ROOT / 'tooling/live/pool-preflight-manifest.json',
             ROOT / 'tooling/live/pool_preflight.py',
             ROOT / 'tooling/live/c25_live_observer.py',
             ROOT / 'live-root/pool_watchdog.py', Path(__file__).resolve()]
    command = ['python3', str(ROOT / 'root_component_v3.py'), '--id', run_id,
               '--timeout-seconds', '60', '--gpu-index', '0', '--contract',
               str(ROOT / 'evaluator/C25_REAL_REQUEST_STAGE_CONTRACT.md'),
               '--review', str(args.review.resolve())]
    for path in files:
        command.extend(['--input', str(path)])
    command += ['--', '/work/tooling/live/pool_preflight.py',
                '--output', '/out/pool-preflight.json']
    prefix = ROOT / 'live-root'
    started = time.monotonic()
    with (prefix / 'pool-allocation-controller.log').open('x') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        ticks = identity(child.pid)
        owned = prefix / 'pool-owned-processes.json'
        owned.write_text(json.dumps({'processes': [{'pid': child.pid,
            'start_ticks': ticks, 'pgid': child.pid, 'role': 'pool-component-runner'}]}, indent=2)+'\n')
        watchdog = subprocess.Popen(['python3', str(prefix / 'pool_watchdog.py'),
            '--parent', str(child.pid), '--ticks', ticks, '--start', str(started),
            '--receipt', str(prefix / 'pool-watchdog.jsonl'), '--owned-processes', str(owned),
            '--name', 'h200-overnight-' + run_id], start_new_session=True)
        try:
            code = child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait(timeout=5)
        processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid',
            '--format=csv,noheader'], text=True, timeout=10).strip()
        containers = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'],
            text=True, timeout=10).strip()
        safe = not processes and not containers
        if safe:
            watchdog.terminate()
            watchdog.wait(timeout=5)
        result = {'runner_exit_code': code, 'supervised_wall_seconds': time.monotonic()-started,
                  'gpu_processes_after': processes, 'running_containers_after': containers,
                  'watchdog_disarmed_after_verified_idle': safe, 'command': command,
                  'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        (prefix / 'pool-supervision.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
        return 0 if code == 0 and safe and result['supervised_wall_seconds'] <= 120 else 1


if __name__ == '__main__':
    raise SystemExit(main())

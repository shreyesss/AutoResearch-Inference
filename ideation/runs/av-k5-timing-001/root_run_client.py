"""Orchestrator: execute the reviewed client and start the reviewed controller."""
from pathlib import Path
import calendar
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
SERVE = Path('/home/ubuntu/Deepseek_serve-c03')
RESULTS = SERVE / 'results/h200/vllm/av-k5-timing'
CLIENT_SHA = '0c9fcff4938f815d32fbc1c279ab185d693799db2770cfb7e271e9349def57b3'
CONTROLLER_SHA = 'd2dd43cd1347de89127806aebda592d51ffa1c69024d46fa1b05b22616219fa7'
NOTICE = re.compile(r'(?P<clock>\d{2}:\d{2}:\d{2}\.\d{3}) NOTICE\s+Phase profiling \(profiling\) started')
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event(kind, **kwargs):
    with (HERE / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps({'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                 'event': kind, **kwargs}) + '\n')


def run(owned):
    assert not (HERE / 'client-process.json').exists(), 'one diagnostic run only'
    assert json.loads((HERE / 'runtime-identity.json').read_text())['status'] == 'ready_identity_pass'
    assert json.loads((HERE / 'startup-capture-inventory.json').read_text())['status'] == 'pass'
    script = HERE / 'run-client.sh'
    control = SERVE / 'av-k5/evaluator/capture_windows.py'
    assert digest(script) == CLIENT_SHA and digest(control) == CONTROLLER_SHA
    assert digest(HERE / 'EVALUATION_CONTRACT.md') == '71c8af4c620e76d168c8efadc0967ea99f4cd381aec9f93d74430f77e1149e15'
    assert not list(RESULTS.glob('**/console.log')), 'unexpected earlier client result'
    with (HERE / 'client.log').open('xb') as output:
        client = subprocess.Popen(['bash', str(script)], stdout=output, stderr=subprocess.STDOUT,
                                  start_new_session=True)
    owned['client'] = client
    (HERE / 'client-process.json').write_text(json.dumps({'pid': client.pid,
        'started_ns': time.time_ns(), 'script_sha256': digest(script)}, indent=2) + '\n')
    event('client_started', pid=client.pid)
    controller = None
    while client.poll() is None and controller is None:
        logs = list(RESULTS.glob('**/console.log'))
        assert len(logs) <= 1, 'ambiguous client log'
        if logs:
            data = logs[0].read_bytes()
            text = ANSI.sub('', data.decode(errors='replace'))
            matches = list(NOTICE.finditer(text))
            assert len(matches) <= 1, 'ambiguous profiling notice'
            if matches:
                match = matches[0]
                now = datetime.datetime.now(datetime.timezone.utc)
                stamp = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + 'T' + match['clock'],
                                                     '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
                if (now - stamp).total_seconds() < -43200:
                    stamp -= datetime.timedelta(days=1)
                elif (now - stamp).total_seconds() > 43200:
                    stamp += datetime.timedelta(days=1)
                anchor = calendar.timegm(stamp.utctimetuple()) * 1_000_000_000 + stamp.microsecond * 1000
                assert 0 <= time.time_ns() - anchor < 10_000_000_000, 'stale phase notice'
                line = next(line for line in text.splitlines() if match.group() in line)
                receipt = {'anchor_ns': anchor, 'anchor_precision': 'UTC millisecond NOTICE, not exact lifecycle ns',
                           'observed_ns': time.time_ns(), 'console_path': str(logs[0]),
                           'console_prefix_bytes': len(data), 'console_prefix_sha256': hashlib.sha256(data).hexdigest(),
                           'notice_line': line, 'exact_lifecycle_reconciliation': 'required after export'}
                (HERE / 'phase-anchor.json').write_text(json.dumps(receipt, indent=2) + '\n')
                command = ['/home/ubuntu/Deepseek_serve/.venv/bin/python', str(control),
                           '--backend-url', 'http://127.0.0.1:8100', '--backend-url', 'http://127.0.0.1:8101',
                           '--profiling-start-ns', str(anchor), '--identity-receipt', str(HERE / 'runtime-identity.json'),
                           '--output', str(HERE / 'profile-control.json')]
                with (HERE / 'profile-controller.log').open('xb') as output:
                    controller = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                owned['controller'] = controller
                (HERE / 'controller-process.json').write_text(json.dumps({'pid': controller.pid, 'argv': command}, indent=2) + '\n')
                event('profiling_notice_and_controller_started', anchor_ns=anchor, controller_pid=controller.pid)
        time.sleep(.2)
    result = client.wait()
    if controller is not None:
        if controller.poll() is None:
            controller.send_signal(signal.SIGINT)
        control_result = controller.wait(timeout=30)
    else:
        control_result = None
    completion = {'finished_ns': time.time_ns(), 'client_exit_code': result,
                  'controller_exit_code': control_result,
                  'run_directories': [str(p.parent) for p in RESULTS.glob('**/console.log')]}
    (HERE / 'process-completion.json').write_text(json.dumps(completion, indent=2) + '\n')
    event('client_and_controller_exited', **completion)
    print(json.dumps(completion))
    return result


def main():
    owned = {}
    try:
        return run(owned)
    except BaseException as exc:
        failure = {'failed_ns': time.time_ns(), 'error': f'{type(exc).__name__}: {exc}',
                   'owned_pids': {role: proc.pid for role, proc in owned.items()},
                   'cleanup': {}, 'secondary_errors': []}
        receipt = HERE / 'orchestration-failure.json'
        def best_effort(name, action):
            try:
                return action()
            except BaseException as secondary:
                failure['secondary_errors'].append({'stage': name,
                    'error': f'{type(secondary).__name__}: {secondary}'})
                return None
        def save():
            receipt.write_text(json.dumps(failure, indent=2) + '\n')
        best_effort('initial_failure_receipt', save)
        # First stop scheduling captures; SIGINT permits the approved controller's
        # existing finally block to stop profiling if an episode is active.
        controller = owned.get('controller')
        if controller is not None and controller.poll() is None:
            best_effort('controller_interrupt', lambda: controller.send_signal(signal.SIGINT))
            best_effort('controller_grace_wait', lambda: controller.wait(timeout=25))
            if controller.poll() is None:
                best_effort('controller_kill', controller.kill)
                best_effort('controller_final_wait', lambda: controller.wait(timeout=5))
        client = owned.get('client')
        if client is not None:
            best_effort('client_group_term', lambda: os.killpg(client.pid, signal.SIGTERM))
            best_effort('client_grace_wait', lambda: client.wait(timeout=20))
            if client.poll() is None:
                best_effort('client_group_kill', lambda: os.killpg(client.pid, signal.SIGKILL))
                best_effort('client_final_wait', lambda: client.wait(timeout=5))
        if controller is not None:
            # A control failure must not leave profiling enabled. Reuse only the
            # builder's bounded stop operation, never issue another start.
            def stop_profiles():
                import importlib.util
                path = SERVE / 'av-k5/evaluator/capture_windows.py'
                spec = importlib.util.spec_from_file_location('avk5_control_cleanup', path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.both(['http://127.0.0.1:8100', 'http://127.0.0.1:8101'], 'stop_profile')
            failure['cleanup']['profile_stop'] = best_effort('final_profile_stop', stop_profiles)
        failure['cleanup']['exit_codes'] = {role: proc.poll() for role, proc in owned.items()}
        failure['cleanup']['finished_ns'] = time.time_ns()
        best_effort('final_failure_receipt', save)
        best_effort('failure_event', lambda: event('orchestration_failed', receipt=str(receipt), error=failure['error']))
        raise


if __name__ == '__main__':
    raise SystemExit(main())

"""Report actual container liveness as well as the controller's saved status."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / '.artifacts/optuna-direct-v1'


def main():
    status = json.loads((ROOT / 'status.json').read_text())
    phase = status['phase']
    age = time.time() - status['updated_unix']
    name = (ROOT / f'{phase}-container-name.txt').read_text().strip()
    result = subprocess.run(['docker', 'inspect', '--format', '{{json .State}}', name],
                            capture_output=True, text=True, timeout=10)
    state = json.loads(result.stdout) if result.returncode == 0 else None
    finished = (ROOT / f'{phase}-finished.json').exists()
    alerts = []
    if phase == 'search' and finished and not (ROOT / 'confirmation-finished.json').exists():
        receipt = json.loads((ROOT / 'search-finished.json').read_text())
        if time.time() - receipt['time'] > 180:
            alerts.append('Search completed but confirmation has not published its heartbeat; campaign handoff stalled')
    if not finished:
        if state is None or not state['Running']:
            alerts.append('Controller container is absent/stopped without a phase completion receipt')
        if age > 180:
            alerts.append('Controller heartbeat is more than 180 seconds old')
    payload = {'checked_unix': time.time(), 'phase': phase, 'container': name,
               'container_state': state, 'heartbeat_age_seconds': round(age, 1),
               'phase_finished': finished, 'alerts': alerts}
    path = ROOT / 'monitor-health.json'
    tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(payload, indent=2)); tmp.replace(path)
    if alerts:
        (ROOT / 'monitor-alert.json').write_text(json.dumps(payload, indent=2))
        print(json.dumps(payload))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Root-executed bounded profile RPCs; does not launch or generate workload."""
import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.request
from pathlib import Path

OFFSETS = (90, 210)
STOP_AFTER_S = 15
HTTP_TIMEOUT_S = 10


def rpc(base, action):
    result = {'backend': base, 'action': action, 'request_start_ns': time.time_ns()}
    try:
        request = urllib.request.Request(base.rstrip('/') + '/' + action, data=b'', method='POST')
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            result.update(status=response.status, response_bytes=len(response.read(65537)))
        result['ok'] = result['status'] == 200
    except Exception as exc:
        result.update(ok=False, error=f'{type(exc).__name__}: {exc}')
    result['request_end_ns'] = time.time_ns()
    return result


def both(backends, action):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(lambda base: rpc(base, action), backends))


def wait_until(deadline_ns):
    while True:
        remaining = (deadline_ns - time.time_ns()) / 1e9
        if remaining <= 0:
            return
        time.sleep(min(remaining, .2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend-url', action='append', required=True)
    parser.add_argument('--profiling-start-ns', type=int, required=True)
    parser.add_argument('--identity-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if len(args.backend_url) != 2 or len(set(args.backend_url)) != 2:
        parser.error('exactly two distinct backend URLs required')
    if args.output.exists():
        parser.error('output exists; receipts are immutable')
    identity = args.identity_receipt.read_bytes()
    result = {'schema_version': 1, 'purpose': 'AV OFF k5 timing only',
              'profiling_start_ns': args.profiling_start_ns,
              'identity_receipt': str(args.identity_receipt.resolve()),
              'identity_sha256': hashlib.sha256(identity).hexdigest(),
              'identity_validation': 'external root and independent reviewer',
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'fixed_offsets_s': list(OFFSETS), 'stop_after_s': STOP_AFTER_S,
              'http_timeout_s': HTTP_TIMEOUT_S, 'episodes': [], 'status': 'running'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    save()
    try:
        for offset in OFFSETS:
            due = args.profiling_start_ns + offset * 1_000_000_000
            if time.time_ns() >= due:
                raise RuntimeError(f'predeclared episode {offset}s already elapsed; no late/replacement capture')
            wait_until(due)
            lateness_ns = time.time_ns() - due
            if lateness_ns > 1_000_000_000:
                raise RuntimeError(f'episode {offset}s missed trigger by {lateness_ns}ns; no catch-up')
            episode = {'offset_s': offset, 'scheduled_start_ns': due}
            episode['dispatch_lateness_ns'] = lateness_ns
            result['episodes'].append(episode)
            try:
                episode['start'] = both(args.backend_url, 'start_profile')
                starts = [item['request_start_ns'] for item in episode['start'] if 'request_start_ns' in item]
                episode['backend_request_start_skew_ns'] = max(starts) - min(starts) if len(starts) == 2 else None
                save()
                if not all(item['ok'] for item in episode['start']):
                    raise RuntimeError('partial/failed profiler start; no retry')
                wait_until(due + STOP_AFTER_S * 1_000_000_000)
            finally:
                episode['stop'] = both(args.backend_url, 'stop_profile')
                save()
            if not all(item['ok'] for item in episode['stop']):
                raise RuntimeError('failed profiler stop; root must inspect actual worker state')
        result['status'] = 'control_completed_trace_adequacy_pending'
    except BaseException as exc:
        result.update(status='failed', error=f'{type(exc).__name__}: {exc}')
    finally:
        result['finished_ns'] = time.time_ns()
        save()
    print(json.dumps({'status': result['status'], 'receipt': str(args.output)}))
    return 0 if result['status'] == 'control_completed_trace_adequacy_pending' else 1

if __name__ == '__main__':
    raise SystemExit(main())

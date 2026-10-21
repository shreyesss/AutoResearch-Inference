"""One resumable GitHub opening-record collector, independent of chat lifetime."""
import argparse
import copy
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def coverage(store, config):
    rows = []
    for repo in config['repositories']:
        state = store.get_checkpoint('discovery:github:' + repo, {})
        counts = dict(store.db.execute("SELECT kind,count(*) FROM documents WHERE id LIKE ? AND kind IN ('pr','issue') GROUP BY kind", ('github:' + repo + ':%',)))
        rows.append({'repo': repo, 'issues': counts.get('issue', 0), 'prs': counts.get('pr', 0),
                     'all_history_complete': bool(state.get('initial_scan_complete') and state.get('initial_scope', {}).get('all_history')),
                     'pages_in_pass': state.get('pages_in_pass', 0), 'records_in_pass': state.get('records_in_pass', 0),
                     'upper_bound': store.get_checkpoint('backfill:bound:' + repo, {}).get('number'),
                     'retry_after': state.get('retry_after'), 'rate_limit': state.get('rate_limit'),
                     'rate_remaining': state.get('rate_remaining')})
    return rows


def estimate(rows, seconds_per_page=None, rate_limit=60, cooldown_seconds=0):
    # Issue and PR numbers share a sequence; gaps make this an upper bound,
    # never a claimed exact source count. Imported rows do not prove coverage.
    missing = [r['repo'] for r in rows if not r['all_history_complete'] and r['upper_bound'] is None]
    pages = sum(max(0, math.ceil(r['upper_bound'] / 100) - r['pages_in_pass']) for r in rows
                if not r['all_history_complete'] and r['upper_bound'] is not None)
    seconds = max(0, cooldown_seconds) + max(pages * (seconds_per_page or 0), pages * 3600 / max(1, rate_limit))
    return {'kind': 'throughput-based planning estimate plus current cooldown; excludes publication, idle pauses and outages',
            'remaining_page_upper_bound_known_repos': pages, 'unknown_repositories': missing,
            'seconds_per_successful_page': seconds_per_page,
            'current_cooldown_seconds': max(0, round(cooldown_seconds)),
            'estimated_hours_known_repos': round(seconds / 3600, 2),
            'complete_estimate': not missing, 'assumed_requests_per_hour': rate_limit}


def status(root):
    from .foundation import _read
    from .discovery import load_config
    from .store import Store
    job = _read(root / 'research/jobs/github-backfill.json', {'status': 'not_started'})
    store = Store(root / 'research/corpus.sqlite')
    try:
        rows = coverage(store, load_config(root / 'research/config.json'))
        job['repositories'] = rows
        job['cooldown'] = store.get_checkpoint('discovery:github_rate', {})
    finally:
        store.db.close()
    # PID existence alone is unsafe after PID reuse. The singleton lock proves
    # whether a collector currently owns this state directory.
    with (root / '.backfill.lock').open('a+b') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            job['worker_running'] = False
        except BlockingIOError:
            job['worker_running'] = True
    return job


def start(root, *, env_file=None, publish_every=300):
    if publish_every < 60:
        raise ValueError('Publication interval must be at least 60 seconds')
    from .foundation import _write
    current = status(root)
    if current['worker_running']:
        return current
    (root / '.backfill-stop').unlink(missing_ok=True)
    log = root / 'research/jobs/github-backfill.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'ideation.backfill', '--state-dir', str(root), '--publish-every', str(publish_every)]
    if env_file:
        command += ['--env-file', str(Path(env_file).expanduser().resolve())]
    with log.open('ab') as stream:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                                 start_new_session=True, close_fds=True)
    receipt = {'status': 'starting', 'pid': child.pid, 'started_at': stamp(), 'log': str(log),
               'publish_every_seconds': publish_every, 'host': os.uname().nodename}
    _write(root / 'research/jobs/github-backfill-launch.json', receipt)
    return receipt


def stop(root):
    (root / '.backfill-stop').touch()
    return {'stop_requested': True, 'meaning': 'Finish current page batch, publish checkpoint, then exit; no signals to reused PIDs.'}


def work(root, env_file=None, publish_every=300):
    from .foundation import _locked, _read, _write, _snapshot
    from .discovery import load_config, refresh
    from .store import Store
    from .github import GitHub, RateLimited
    from .providers import load_provider_env
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.backfill.lock').open('a+b') as singleton:
        try:
            fcntl.flock(singleton, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        if env_file:
            os.environ['IDEATION_ENV_FILE'] = env_file
        job = {'pid': os.getpid(), 'started_at': stamp(), 'status': 'running', 'successful_pages': 0,
               'fetch_seconds': 0., 'failed_repositories': {}, 'publish_every_seconds': publish_every,
               'host': os.uname().nodename, 'scope': 'all opening bodies/metadata; no comments/diffs/reviews'}
        path = root / 'research/jobs/github-backfill.json'
        last_publish = time.monotonic()
        last_auth = None
        active_rate_limit = None
        while True:
            # File can be filled or rotated while waiting. Never write token to state.
            if env_file:
                from dotenv import dotenv_values
                values = dotenv_values(env_file, interpolate=False)
                for key in ('GITHUB_TOKEN', 'GH_TOKEN'):
                    if values.get(key):
                        os.environ[key] = values[key]
            load_provider_env()
            auth = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN') or ''
            wait = 2
            with _locked(root):
                config = load_config(root / 'research/config.json')
                store = Store(root / 'research/corpus.sqlite')
                try:
                    if last_auth is not None and auth != last_auth:
                        active_rate_limit = None
                        store.checkpoint('discovery:github_rate', {})
                        for repo in config['repositories']:
                            key = 'discovery:github:' + repo
                            state = store.get_checkpoint(key, {})
                            state.pop('retry_after', None)
                            store.checkpoint(key, state)
                        job['failed_repositories'] = {}
                    last_auth = auth
                    job['authenticated_env_token'] = bool(auth)
                    rows = coverage(store, config)
                    pending = [r['repo'] for r in rows if not r['all_history_complete'] and r['repo'] not in job['failed_repositories']]
                    if (root / '.backfill-stop').exists():
                        job['status'] = 'stopped'
                    elif not pending:
                        job['status'] = 'blocked' if job['failed_repositories'] else 'complete'
                    else:
                        cooldown = store.get_checkpoint('discovery:github_rate', {})
                        now = dt.datetime.now(dt.timezone.utc)
                        retry = cooldown.get('retry_after')
                        remaining = (dt.datetime.fromisoformat(retry.replace('Z', '+00:00')) - now).total_seconds() if retry else 0
                        if remaining > 0:
                            job['status'], wait = 'waiting_for_rate_limit', min(30, remaining + 1)
                        else:
                            job['status'] = 'running'
                            # One sequence upper bound per repo, at most one extra
                            # call per batch; raw response and provenance retained.
                            for repo in pending:
                                if not store.get_checkpoint('backfill:bound:' + repo):
                                    client = GitHub(store, repo)
                                    try:
                                        latest, _ = client.get('issues', {'state': 'all', 'sort': 'created', 'direction': 'desc', 'per_page': 1})
                                        store.checkpoint('backfill:bound:' + repo, {'number': latest[0]['number'] if latest else 0, 'at': stamp(), 'meaning': 'shared issue/PR sequence upper bound, not exact count'})
                                    except RateLimited as error:
                                        # Let refresh handle structured rate cooldown.
                                        pass
                                    except Exception as error:
                                        if getattr(error, 'code', None) in (401, 404, 410, 422):
                                            job['failed_repositories'][repo] = {'http_status': error.code, 'at': stamp()}
                                    break
                            cfg = copy.deepcopy(config)
                            cfg.update(repositories=[r for r in pending if r not in job['failed_repositories']], github_initial_days=None, github_recent_lane=False)
                            cfg['budgets'].update(github_pages=4, pages_per_repository=1, paper_requests=0, citation_requests=0)
                            started = time.monotonic()
                            receipt = refresh(store, cfg, build_shortlist=False)
                            for observed in receipt['coverage']:
                                if observed.get('last_fetch') == receipt['started_at'] and observed.get('rate_limit'):
                                    active_rate_limit = int(observed['rate_limit'])
                            job['fetch_seconds'] += time.monotonic() - started
                            successes = sum(1 for c in receipt['coverage'] if c.get('status') in ('partial', 'completed_pass') and c.get('last_fetch') == receipt['started_at'])
                            job['successful_pages'] += successes
                            job['last_batch'] = {k: receipt[k] for k in ('started_at', 'completed_at', 'requests', 'errors')}
                            for error in receipt['errors']:
                                if error.get('repo') and error.get('http_status') in (401, 404, 410, 422):
                                    job['failed_repositories'][error['repo']] = error
                    job['repositories'] = coverage(store, config)
                    limit = active_rate_limit or (5000 if auth else 60)
                    cooldown = store.get_checkpoint('discovery:github_rate', {}).get('retry_after')
                    remaining_wait = (dt.datetime.fromisoformat(cooldown.replace('Z', '+00:00')) - dt.datetime.now(dt.timezone.utc)).total_seconds() if cooldown else 0
                    job['eta'] = estimate(job['repositories'], job['fetch_seconds'] / job['successful_pages'] if job['successful_pages'] else None, limit, remaining_wait)
                    job['eta']['rate_limit_observed_this_process'] = active_rate_limit is not None
                    job['updated_at'] = stamp()
                    _write(path, job)
                finally:
                    store.db.close()
                terminal = job['status'] in ('stopped', 'complete', 'blocked')
                if terminal or time.monotonic() - last_publish >= publish_every:
                    try:
                        job['snapshot'] = _snapshot(root, 'research')
                        job.pop('publication_error', None)
                    except Exception as error:
                        job['publication_error'] = {'type': type(error).__name__, 'at': stamp(), 'local_progress_retained': True}
                    last_publish = time.monotonic()
                    _write(path, job)
                print(json.dumps({'at': job['updated_at'], 'status': job['status'], 'pages': job['successful_pages'], 'publication_error': job.get('publication_error')}), flush=True)
                if terminal:
                    return
            # Do not hold the writer lock while idle; new credentials are checked
            # every 30s even during a rate-limit wait.
            time.sleep(wait)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state-dir', type=Path, required=True)
    p.add_argument('--env-file')
    p.add_argument('--publish-every', type=int, default=300)
    a = p.parse_args()
    try:
        work(a.state_dir, a.env_file, a.publish_every)
    except Exception as error:
        # Never log URLs/exception messages which may embed credentials.
        print(json.dumps({'status': 'worker_failed', 'type': type(error).__name__, 'at': stamp()}), flush=True)
        raise SystemExit(1)

"""Real isolated lock contention, safe failures and unchanged default behavior."""
import asyncio
from contextlib import contextmanager
import errno
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from ideation.foundation import _locked, invoke, main, validate_lock_timeout, WriterBusyError


@contextmanager
def holder(root):
    child = subprocess.Popen([sys.executable, '-u', '-c',
        'import fcntl,sys; f=open(sys.argv[1],"a+b"); fcntl.flock(f,fcntl.LOCK_EX); '
        'print("ready",flush=True); sys.stdin.readline()', str(root / '.writer.lock')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'ready'
        yield child
    finally:
        if child.poll() is None:
            child.communicate('\n', timeout=5)
        assert child.returncode == 0


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def initialize(root):
    invoke(['--state-dir', str(root), '--local-only', 'init'])


def cli(root, timeout=None):
    cmd = [sys.executable, '-m', 'ideation.foundation', '--state-dir', str(root),
           '--local-only', '--defer-snapshot']
    if timeout is not None:
        cmd += ['--lock-timeout', str(timeout)]
    return cmd + ['search', 'PRIVATE_QUERY_SENTINEL']


@pytest.mark.parametrize('timeout', [0, 0.05])
def test_actual_cli_busy_preserves_state_and_sanitizes(tmp_path, timeout):
    initialize(tmp_path)
    with holder(tmp_path):
        before = hashes(tmp_path)
        r = subprocess.run(cli(tmp_path, timeout), capture_output=True, text=True, timeout=5)
        assert r.returncode == 1 and not r.stdout
        error = json.loads(r.stderr)
        assert error['error_code'] == 'writer_busy'
        assert 'PRIVATE_QUERY_SENTINEL' not in r.stderr
        assert hashes(tmp_path) == before
        with patch('ideation.foundation._execute') as execute, patch('ideation.journal.start') as start:
            with pytest.raises(WriterBusyError):
                invoke(['--state-dir', str(tmp_path), '--lock-timeout', '0', 'search', 'x'])
            execute.assert_not_called(); start.assert_not_called()


@pytest.mark.parametrize('timeout', [None, 3])
def test_default_blocks_and_explicit_budget_can_succeed_after_release(tmp_path, timeout):
    initialize(tmp_path)
    with holder(tmp_path) as lock:
        child = subprocess.Popen(cli(tmp_path, timeout), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            with pytest.raises(subprocess.TimeoutExpired):
                child.communicate(timeout=0.15)
            lock.communicate('\n', timeout=5)
            out, err = child.communicate(timeout=5)
            assert child.returncode == 0 and not err
            assert json.loads(out) == []
        finally:
            if child.poll() is None:
                child.kill(); child.communicate()


def test_free_zero_budget_and_command_exception_release(tmp_path):
    initialize(tmp_path)
    with _locked(tmp_path, timeout=0):
        pass
    with pytest.raises(RuntimeError):
        with _locked(tmp_path, timeout=0):
            raise RuntimeError('command failure')
    with _locked(tmp_path, timeout=0):
        pass


@pytest.mark.parametrize('bad', ['nan', 'inf', '-1', 'PRIVATE_VALUE_SENTINEL'])
def test_actual_cli_invalid_timeout_has_static_error_no_state(tmp_path, bad):
    # = also prevents argparse mistaking a negative value for another option.
    r = subprocess.run([sys.executable, '-m', 'ideation.foundation', '--state-dir', str(tmp_path / 'absent'),
                        '--lock-timeout=' + bad, 'search', 'x'], capture_output=True, text=True, timeout=5)
    assert r.returncode == 2
    assert 'lock timeout must be finite nonnegative seconds' in r.stderr
    assert 'PRIVATE_VALUE_SENTINEL' not in r.stderr
    assert not (tmp_path / 'absent').exists()


def test_config_validation_and_noncontention_errors(tmp_path):
    for bad in (True, False, float('nan'), float('inf'), -1, {}, []):
        with pytest.raises(ValueError, match='finite nonnegative'):
            validate_lock_timeout(bad)
    for code in (errno.EACCES, errno.EBADF, errno.ENOENT):
        with patch('ideation.foundation.fcntl.flock', side_effect=OSError(code, 'PRIVATE_OS_SENTINEL')):
            with pytest.raises(OSError) as caught:
                with _locked(tmp_path, timeout=0):
                    pass
            assert caught.value.errno == code


def test_provider_error_is_not_misreported_busy(tmp_path, capsys):
    with patch('ideation.foundation.invoke', side_effect=OSError(errno.EACCES, 'PRIVATE_PROVIDER_SENTINEL')):
        assert main(['--state-dir', str(tmp_path), '--lock-timeout', '0', 'paper-search', 'x']) == 1
    out = capsys.readouterr()
    assert 'PRIVATE_PROVIDER_SENTINEL' not in out.err + out.out
    assert 'writer_busy' not in out.err


def test_actual_mcp_busy_free_and_config_validation(tmp_path):
    pytest.importorskip('mcp')
    from mcp import Client
    from ideation.mcp_server import create_server
    initialize(tmp_path)
    for bad in (True, float('nan'), float('inf'), -1):
        with pytest.raises(ValueError, match='finite nonnegative'):
            create_server(tmp_path, lock_timeout=bad)

    async def check():
        with patch('ideation.sources.Sources._request') as provider:
            async with Client(create_server(tmp_path, lock_timeout=0, defer_snapshot=True)) as client:
                with holder(tmp_path):
                    before = hashes(tmp_path)
                    result = await client.call_tool('search_local', {'query': 'PRIVATE_QUERY_SENTINEL'})
                    assert result.is_error
                    assert 'writer_busy' in str(result.content)
                    assert 'PRIVATE_QUERY_SENTINEL' not in str(result.content)
                    assert hashes(tmp_path) == before
                free = await client.call_tool('search_local', {'query': 'x'})
                assert not free.is_error
                provider.assert_not_called()
    asyncio.run(check())


def test_budget_expiry_does_not_attempt_late_acquisition(tmp_path):
    with patch('ideation.foundation.time.monotonic', side_effect=[0.0, 0.0, 0.1]), \
         patch('ideation.foundation.time.sleep') as sleep, \
         patch('ideation.foundation.fcntl.flock', side_effect=[BlockingIOError(errno.EAGAIN, 'busy'), None]) as flock:
        with pytest.raises(WriterBusyError):
            with _locked(tmp_path, timeout=0.05):
                pytest.fail('late acquisition must not execute')
        assert flock.call_count == 1
        sleep.assert_called_once_with(0.05)

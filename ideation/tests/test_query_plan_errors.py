"""Actionable static schema guidance without exposing arbitrary error text."""
import asyncio
import copy
import json
import subprocess
import sys
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from ideation.foundation import invoke, main
from ideation.query_plan import (OBSERVATION_STATUSES, QueryPlanObservationStatusError,
                                QueryPlanRowError, compile_plan)


def plan():
    return {'mechanism': 'Reuse an identical activation',
            'queries': [{'query': 'activation reuse', 'provider': 'arxiv',
                         'purpose': 'Find constraints', 'why': 'Check fan-out'}],
            'observations': []}


def status_plan(status):
    value = plan()
    value['observations'] = [
        {'query': 'prior', 'provider': 'local', 'status': 'empty', 'reason': 'No hits'},
        {'query': 'PRIVATE_QUERY_SENTINEL', 'provider': 'arxiv', 'status': status,
         'reason': 'PRIVATE_REASON_SENTINEL'}]
    return value


@pytest.mark.parametrize('status', ['off_topic', 'PRIVATE_STATUS_SENTINEL', None, [],
                                  {'PRIVATE_STATUS_SENTINEL': True}, 42])
def test_status_error_has_static_enum_and_bounded_location(status):
    with pytest.raises(QueryPlanObservationStatusError) as caught:
        compile_plan('PRIVATE_QUESTION_SENTINEL', status_plan(status))
    error = caught.value
    assert error.field == 'observations' and error.index == 1
    assert error.error_code == 'query_plan_observation_status_invalid'
    assert 'observations[1].status must be one of:' in error.safe_message
    assert error.allowed_values == ('useful', 'irrelevant', 'empty', 'error', 'redundant')
    assert all(value in error.safe_message for value in OBSERVATION_STATUSES)
    assert 'PRIVATE_' not in str(error) and 'off_topic' not in str(error)


@pytest.mark.parametrize('index', [-1, 50, True, 'PRIVATE_LOCATION_SENTINEL'])
def test_status_error_rejects_unbounded_or_noninteger_location(index):
    with pytest.raises(ValueError, match='Invalid query plan error location'):
        QueryPlanObservationStatusError(index)


@pytest.mark.parametrize('status', ['useful', 'irrelevant', 'empty', 'error', 'redundant'])
def test_existing_statuses_remain_unchanged(status):
    result = compile_plan('Question', status_plan(status))
    assert result['observations'][1]['status'] == status
    assert result['limits']['network_calls'] == 0


def test_real_cli_invalid_status_and_explicitly_corrected_plan(tmp_path):
    invoke(['--state-dir', str(tmp_path / 'state'), '--local-only', 'init'])
    base = [sys.executable, '-m', 'ideation.foundation', '--state-dir',
            str(tmp_path / 'state'), '--local-only', '--defer-snapshot',
            'expand', '--question', 'PRIVATE_QUESTION_SENTINEL']
    path = tmp_path / 'plan.json'
    path.write_text(json.dumps(status_plan('PRIVATE_STATUS_SENTINEL')))
    failed = subprocess.run(base + ['--plan', str(path)], capture_output=True, text=True)
    assert failed.returncode == 1 and failed.stdout == ''
    error = json.loads(failed.stderr)
    assert error['error_code'] == 'query_plan_observation_status_invalid'
    assert error['field'] == 'observations' and error['index'] == 1
    assert error['allowed_values'] == list(OBSERVATION_STATUSES)
    assert 'PRIVATE_' not in failed.stderr
    path.write_text(json.dumps(status_plan('irrelevant')))
    fixed = subprocess.run(base + ['--plan', str(path)], capture_output=True, text=True)
    assert fixed.returncode == 0 and not fixed.stderr
    result = json.loads(fixed.stdout)['result']
    assert result['observations'][1]['status'] == 'irrelevant'
    assert result['limits']['network_calls'] == 0


def test_real_mcp_status_guidance_and_explicit_correction(tmp_path):
    pytest.importorskip('mcp')
    from mcp import Client
    from ideation.mcp_server import create_server
    invoke(['--state-dir', str(tmp_path), '--local-only', 'init'])

    async def check():
        with patch('ideation.sources.Sources._request') as provider:
            async with Client(create_server(tmp_path, allow_network=True, defer_snapshot=True)) as client:
                failed = await client.call_tool('expand_queries', {
                    'question': 'PRIVATE_QUESTION_SENTINEL',
                    'plan': status_plan('PRIVATE_STATUS_SENTINEL')})
                assert failed.is_error
                text = str(failed.content)
                assert 'query_plan_observation_status_invalid' in text
                assert 'observations[1].status' in text
                assert all(value in text for value in OBSERVATION_STATUSES)
                assert 'PRIVATE_' not in text
                fixed = await client.call_tool('expand_queries', {
                    'question': 'Question', 'plan': status_plan('irrelevant')})
                assert not fixed.is_error
                assert fixed.structured_content['result']['observations'][1]['status'] == 'irrelevant'
                assert fixed.structured_content['result']['limits']['network_calls'] == 0
                provider.assert_not_called()
    asyncio.run(check())


@pytest.mark.parametrize('field', ['queries', 'observations'])
@pytest.mark.parametrize('bad_row', ['PRIVATE_INPUT_SENTINEL', None, [], 42])
def test_row_errors_have_only_static_location_and_guidance(field, bad_row):
    value = plan()
    valid = (copy.deepcopy(value['queries'][0]) if field == 'queries' else
             {'query': 'prior', 'provider': 'local', 'status': 'empty', 'reason': 'No hits'})
    value[field] = [valid, bad_row]
    with pytest.raises(QueryPlanRowError) as caught:
        compile_plan('Question', value)
    error = caught.value
    assert error.field == field and error.index == 1
    assert f'{field}[1] must be an object' in error.safe_message
    assert 'PRIVATE_INPUT_SENTINEL' not in str(error)
    assert error.error_code == 'query_plan_row_must_be_object'


@pytest.mark.parametrize('field', ['queries', 'observations'])
def test_real_cli_bad_row_and_corrected_plan(tmp_path, field):
    invoke(['--state-dir', str(tmp_path / 'state'), '--local-only', 'init'])
    base = [sys.executable, '-m', 'ideation.foundation', '--state-dir',
            str(tmp_path / 'state'), '--local-only', '--defer-snapshot',
            'expand', '--question', 'CPU research']
    path = tmp_path / 'plan.json'
    value = plan()
    value[field] = ['PRIVATE_INPUT_SENTINEL']
    path.write_text(json.dumps(value))
    failed = subprocess.run(base + ['--plan', str(path)], capture_output=True, text=True)
    assert failed.returncode == 1 and failed.stdout == ''
    error = json.loads(failed.stderr)
    assert error['error_code'] == 'query_plan_row_must_be_object'
    assert error['field'] == field and error['index'] == 0
    assert f'{field}[0]' in error['message']
    assert 'PRIVATE_INPUT_SENTINEL' not in failed.stderr
    path.write_text(json.dumps(plan()))
    fixed = subprocess.run(base + ['--plan', str(path)], capture_output=True, text=True)
    assert fixed.returncode == 0 and not fixed.stderr
    assert json.loads(fixed.stdout)['result']['limits']['network_calls'] == 0


def test_cli_provider_exception_stays_sanitized(tmp_path, capsys):
    failure = HTTPError('https://provider.invalid/?api_key=PRIVATE_PROVIDER_SENTINEL',
                        401, 'PRIVATE_PROVIDER_SENTINEL', {}, None)
    with patch('ideation.foundation.invoke', side_effect=failure):
        assert main(['--state-dir', str(tmp_path), 'paper-search', 'test']) == 1
    output = capsys.readouterr()
    error = json.loads(output.err)
    assert error['error_type'] == 'HTTPError'
    assert 'error_code' not in error
    assert 'PRIVATE_PROVIDER_SENTINEL' not in output.err + output.out


def test_real_mcp_row_guidance_corrected_plan_and_provider_sanitization(tmp_path):
    pytest.importorskip('mcp')
    from mcp import Client
    from ideation.mcp_server import create_server
    invoke(['--state-dir', str(tmp_path), '--local-only', 'init'])

    async def check():
        with patch('ideation.sources.Sources._request') as provider:
            async with Client(create_server(tmp_path, allow_network=True, defer_snapshot=True)) as client:
                for field in ('queries', 'observations'):
                    value = plan(); value[field] = ['PRIVATE_INPUT_SENTINEL']
                    result = await client.call_tool('expand_queries', {'question': 'CPU research', 'plan': value})
                    assert result.is_error
                    text = str(result.content)
                    assert f'{field}[0] must be an object' in text
                    assert 'query_plan_row_must_be_object' in text
                    assert 'PRIVATE_INPUT_SENTINEL' not in text
                fixed = await client.call_tool('expand_queries', {'question': 'CPU research', 'plan': plan()})
                assert not fixed.is_error
                assert fixed.structured_content['result']['limits']['network_calls'] == 0
                provider.assert_not_called()
                failure = HTTPError('https://provider.invalid/?api_key=PRIVATE_PROVIDER_SENTINEL',
                                    401, 'PRIVATE_PROVIDER_SENTINEL', {}, None)
                with patch('ideation.foundation.invoke', side_effect=failure):
                    async with Client(create_server(tmp_path, allow_network=True)) as failing_client:
                        failed = await failing_client.call_tool('search_papers', {'query': 'LLM inference'})
                        assert failed.is_error
                        assert 'HTTPError' in str(failed.content)
                        assert 'PRIVATE_PROVIDER_SENTINEL' not in str(failed.content)
    asyncio.run(check())

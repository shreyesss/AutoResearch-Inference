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
from ideation.query_plan import QueryPlanRowError, compile_plan


def plan():
    return {'mechanism': 'Reuse an identical activation',
            'queries': [{'query': 'activation reuse', 'provider': 'arxiv',
                         'purpose': 'Find constraints', 'why': 'Check fan-out'}],
            'observations': []}


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

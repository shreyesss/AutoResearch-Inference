import asyncio
import json
from pathlib import Path

import pytest
mcp = pytest.importorskip('mcp')
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from ideation.foundation import invoke
from ideation.mcp_server import create_server
from ideation.store import Store


def test_mcp_shared_tools_and_network_boundary(tmp_path):
    invoke(['--state-dir',str(tmp_path),'init'])
    fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/evidence_fixture.json').read_text())
    store=Store(tmp_path/'research/corpus.sqlite');store.put(fixture['source']);store.db.commit();store.db.close()
    async def check():
        async with Client(create_server(tmp_path)) as client:
            listed=await client.list_tools()
            names={t.name for t in listed.tools}
            assert {'record_claim','record_hypothesis','screen','plan_experiment','changes_since'} <= names
            assert not {'execute','run_shell','launch_gpu'} & names
            result=await client.call_tool('search_local',{'query':'verification'})
            assert not result.is_error
            assert fixture['source']['id'] in json.dumps(result.structured_content)
            denied=await client.call_tool('discover',{'dry_run':False})
            assert denied.is_error
            recorded=await client.call_tool('record_claim',{'claim':fixture['claim']})
            assert not recorded.is_error
            assert 'reported' in json.dumps(recorded.structured_content)
    asyncio.run(check())


def test_stdio_real_transport_roundtrip(tmp_path):
    import sys
    invoke(['--state-dir',str(tmp_path),'init'])
    async def check():
        params=StdioServerParameters(command=sys.executable,args=['-m','ideation.mcp_server','--state-dir',str(tmp_path)])
        async with Client(params) as client:
            result=await client.call_tool('doctor',{})
            assert not result.is_error
            assert result.structured_content['network_checked'] is False
    asyncio.run(check())

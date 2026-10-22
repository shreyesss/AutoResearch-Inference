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
            denied=await client.call_tool('search_papers',{'query':'speculation','after':'2026-09-01'})
            assert denied.is_error
            recorded=await client.call_tool('record_claim',{'claim':fixture['claim']})
            assert not recorded.is_error
            assert 'reported' in json.dumps(recorded.structured_content)
    asyncio.run(check())


def test_mcp_online_search_forwards_dates_and_provider(tmp_path):
    from unittest.mock import patch
    calls=[]
    def fake(args):
        calls.append(args)
        return {'status':'completed','hits':[]}
    async def check():
        with patch('ideation.foundation.invoke', fake):
            async with Client(create_server(tmp_path,allow_network=True)) as client:
                result=await client.call_tool('search_papers',{'query':'speculative decoding','providers':['openalex'],
                    'after':'2026-09-01','before':'2026-10-23','limit':12})
                assert not result.is_error
                assert result.structured_content['status']=='completed'
    asyncio.run(check())
    assert calls[0][3:]==['paper-search','speculative decoding','--limit','12','--provider','openalex',
                         '--after','2026-09-01','--before','2026-10-23']


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


def test_mcp_repo_refresh_online_boundary_and_scope(tmp_path):
    from unittest.mock import patch
    calls=[]
    def fake(args):
        calls.append(args)
        return {'scope':'opening_records','status':'partial'}
    async def check():
        with patch('ideation.foundation.invoke',fake):
            async with Client(create_server(tmp_path)) as client:
                denied=await client.call_tool('refresh_repositories',{'repositories':['example/new-repo']})
                assert denied.is_error and calls==[]
            async with Client(create_server(tmp_path,allow_network=True)) as client:
                result=await client.call_tool('refresh_repositories',{'repositories':['example/new-repo'],'force':True})
                assert not result.is_error
    asyncio.run(check())
    assert calls[0][3:]==['refresh','--only','github','--repo','example/new-repo','--force']


def test_mcp_iterative_surface_and_checkpoint_modes(tmp_path):
    from unittest.mock import patch
    calls=[]
    def fake(args):
        calls.append(args)
        if '--plan' in args:
            value=json.loads(Path(args[args.index('--plan')+1]).read_text())
            assert value['mechanism']=='queue interference'
        return {'ok':True}
    async def check():
        with patch('ideation.foundation.invoke',fake):
            async with Client(create_server(tmp_path, defer_snapshot=True)) as client:
                for name, arguments in (
                    ('recall_hypotheses',{'query':'routing'}),
                    ('command_history',{'limit':5}),
                    ('source_show',{'source_id':'paper:test','revision_hash':'abc'}),
                    ('search_local',{'query':'routing','date_field':'created_at'}),
                    ('expand_queries',{'question':'reduce interference','plan':{'mechanism':'queue interference'}}),
                    ('checkpoint',{}),
                ):
                    result=await client.call_tool(name,arguments)
                    assert not result.is_error
    asyncio.run(check())
    assert all('--defer-snapshot' in args for args in calls[:-1])
    assert '--defer-snapshot' not in calls[-1]
    assert '--local-only' in calls[-1]
    assert '--revision-hash' in calls[2]
    assert calls[3][-4:]==['--date-field','created_at','--match','any']


def test_mcp_deep_read_explicit_selection_reaches_cli(tmp_path):
    from unittest.mock import patch
    calls=[]
    pin={'repo':'owner/engine','ref':'a'*40,'path':'kernel.py'}
    def fake(args):
        calls.append(args)
        return {'ok':True}
    async def check():
        with patch('ideation.foundation.invoke',fake):
            async with Client(create_server(tmp_path, allow_network=True)) as client:
                for repositories in (['author/project'], []):
                    result=await client.call_tool('investigate',{'source_ids':['arxiv:2610.12345'],
                        'question':'Does this code implement the selected mechanism?', 'offline':False,
                        'repositories':repositories, 'code_sources':[pin]})
                    assert not result.is_error
    asyncio.run(check())
    assert calls[0][calls[0].index('--repository')+1]=='author/project'
    assert json.loads(calls[0][calls[0].index('--code-source')+1])==pin
    assert '--repository' not in calls[1]
    assert calls[1][calls[1].index('--max-repositories')+1]=='0'
    assert all(args[args.index('--citations-per-paper')+1]=='3' for args in calls)


def test_mcp_investigate_citation_limit_forwarding_and_validation(tmp_path):
    from unittest.mock import patch
    calls=[]
    def fake(args):
        calls.append(args)
        return {'ok':True}
    async def check():
        with patch('ideation.foundation.invoke',fake), patch('ideation.sources.Sources._request') as request:
            async with Client(create_server(tmp_path,allow_network=True)) as client:
                arguments={'source_ids':['arxiv:2610.15366'], 'question':'Read full text', 'offline':False}
                for limit in (0,5):
                    result=await client.call_tool('investigate',{**arguments,'citations_per_paper':limit})
                    assert not result.is_error
                for limit in (-1,6):
                    result=await client.call_tool('investigate',{**arguments,'citations_per_paper':limit})
                    assert result.is_error
                    assert 'citations_per_paper must be 0..5' in str(result.content)
                assert len(calls)==2
            request.assert_not_called()
    asyncio.run(check())
    assert [args[args.index('--citations-per-paper')+1] for args in calls]==['0','5']


def test_mcp_uninitialized_state_recovery_hint(tmp_path):
    async def check():
        async with Client(create_server(tmp_path, allow_network=True)) as client:
            result=await client.call_tool('search_papers',{'query':'exact tokenization'})
            assert result.is_error
            assert 'researchctl --state-dir PATH init' in str(result.content)
    asyncio.run(check())


def test_mcp_missing_source_is_local_absence(tmp_path):
    invoke(['--state-dir', str(tmp_path), 'init'])
    async def check():
        async with Client(create_server(tmp_path, allow_network=True)) as client:
            result = await client.call_tool('source_show', {'source_id': 'paper:missing'})
            assert result.is_error
            assert 'source_not_retained' in str(result.content)
            assert 'Local absence does not prove upstream absence' in str(result.content)
    asyncio.run(check())

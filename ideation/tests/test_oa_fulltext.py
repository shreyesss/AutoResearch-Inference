"""Real parser/cache/CLI/MCP coverage; only the remote transport is replaced."""
import asyncio
import contextlib
import hashlib
import io
import json
from unittest.mock import patch

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from ideation.deep_dive import investigate
from ideation.foundation import main
from ideation.sources import Sources
from ideation.store import Store


def pdf_bytes():
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    stream = DecodedStreamObject()
    text = 'Mechanism evidence and numerical compatibility require independent checks. ' * 8
    stream.set_data(('BT /F1 10 Tf 10 700 Td (' + text + ') Tj ET').encode())
    page[NameObject('/Contents')] = writer._add_object(stream)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def put_paper(store, name, pdf_url='https://papers.example.edu/paper.pdf', **location):
    doc = {'id': 'openalex:' + name, 'source': 'openalex', 'kind': 'paper', 'title': name,
           'url': 'https://doi.org/10.1234/' + name, 'body': 'An abstract, not full text.',
           'created_at': '2026-10-01', 'updated_at': '2026-10-20',
           'metadata': {'read_depth': 'abstract', 'canonical_paper_id': 'doi:10.1234/' + name,
                        'locations': [{'is_oa': True, 'pdf_url': pdf_url,
                                       'landing_page_url': 'https://doi.org/10.1234/' + name, **location}]}}
    store.put(doc)
    store.db.commit()
    return doc['id']


def dive(store, tmp_path, ids, **kw):
    return investigate(store, 'Read selected evidence', ids, str(tmp_path),
                       max_repositories=0, citations_per_paper=0, **kw)


@pytest.mark.parametrize('mime', ['application/pdf', 'application/octet-stream'])
def test_explicit_oa_pdf_partial_coverage_and_dates(tmp_path, mime):
    store = Store(tmp_path / 'corpus.sqlite')
    try:
        good = put_paper(store, 'good')
        missing = put_paper(store, 'doi-only', None)
        html = put_paper(store, 'html', 'https://papers.example.edu/login.pdf')
        budget = put_paper(store, 'budget', 'https://papers.example.edu/next.pdf')
        original = store.get(good)
        raw = pdf_bytes()
        def transport(url, *args):
            return (raw, mime) if url.endswith('paper.pdf') else (b'<html>Abstract only</html>', mime)
        with patch.object(Sources, '_request', side_effect=transport) as http:
            result = dive(store, tmp_path / 'run', [good, missing, html, budget], max_http_calls=2, max_fulltexts=4)
        assert http.call_count == 2
        assert result['fulltext_coverage'] == {'completed': 1, 'skipped': 2, 'failed': 1, 'selected_papers': 4}
        by_id = {r['source_id']: r for r in result['reads']}
        assert by_id[missing]['reason'] == 'no_supported_oa_pdf_locator'
        assert by_id[budget]['reason'] == 'http_budget_exhausted'
        assert by_id[html]['reason'] == 'fetch_or_extraction_failed'
        full = store.get(by_id[good]['fulltext']['id'])
        assert full['kind'] == 'fulltext' and full['parent'] == 'doi:10.1234/good'
        assert full['created_at'] == '2026-10-01' and full['updated_at'] is None
        assert full['metadata']['source_record_content_hash'] == original['content_hash']
        assert full['metadata']['sha256'] == hashlib.sha256(raw).hexdigest()
        assert full['metadata']['content_type'] == mime
        assert full['metadata']['source_record_updated_at'] == '2026-10-20'
        assert full['metadata']['version_pinned'] is False
        assert '[PDF page 1]' in full['body'] and 'Mechanism evidence' in full['body']
        assert store.get(good) == original
        assert store.db.execute("SELECT count(*) FROM documents WHERE kind='fulltext'").fetchone()[0] == 1
        assert 'Dossier readiness can rely on abstracts' in (tmp_path / 'run/REPORT.md').read_text()
    finally:
        store.db.close()


def test_pdf_cache_offline_and_fulltext_count_cap(tmp_path):
    store = Store(tmp_path / 'corpus.sqlite')
    try:
        a = put_paper(store, 'cached')
        b = put_paper(store, 'uncached', 'https://papers.example.edu/other.pdf')
        with patch.object(Sources, '_request', return_value=(pdf_bytes(), 'APPLICATION/PDF')):
            first = dive(store, tmp_path / 'first', [a, b], max_http_calls=1, max_fulltexts=1)
        assert first['reads'][1]['reason'] == 'fulltext_limit'
        with patch.object(Sources, '_request') as http:
            replay = dive(store, tmp_path / 'replay', [a, b], max_http_calls=0, max_fulltexts=2)
        http.assert_not_called()
        assert replay['http_cache_misses'] == 0
        assert replay['reads'][0]['fulltext']['cache']['hit'] is True
        assert replay['reads'][1]['reason'] == 'http_budget_exhausted'
    finally:
        store.db.close()


def test_arxiv_looking_path_on_external_host_keeps_locator_and_identity(tmp_path):
    store = Store(tmp_path / 'corpus.sqlite')
    url = 'https://papers.example.edu/archive/arxiv.org/pdf/2601.01234v1'
    try:
        identity = put_paper(store, 'external', url)
        with patch.object(Sources, '_request', return_value=(pdf_bytes(), 'application/pdf')) as http:
            result = dive(store, tmp_path / 'run', [identity])
        assert http.call_args.args[0] == url
        record = store.get(result['reads'][0]['fulltext']['id'])
        assert record['id'].startswith('web:')
        assert record['metadata']['canonical_paper_id'] == 'doi:10.1234/external'
        assert record['metadata']['version_pinned'] is False
        assert store.get('fulltext:2601.01234v1') is None
        cache = result['reads'][0]['fulltext']['cache']
        from datetime import datetime
        assert (datetime.fromisoformat(cache['expires_at']) - datetime.fromisoformat(cache['fetched_at'])).days < 365
    finally:
        store.db.close()


def test_blank_pdf_page_markers_are_not_extracted_evidence(tmp_path):
    writer = PdfWriter()
    for _ in range(30):
        writer.add_blank_page(width=612, height=792)
    raw = io.BytesIO()
    writer.write(raw)
    store = Store(tmp_path / 'corpus.sqlite')
    try:
        identity = put_paper(store, 'scanned')
        with patch.object(Sources, '_request', return_value=(raw.getvalue(), 'application/pdf')):
            result = dive(store, tmp_path / 'run', [identity])
        assert result['reads'][0]['status'] == 'failed'
        assert result['fulltext_coverage']['completed'] == 0
        assert result['reasoning_source_ids'] == [identity]  # Original abstract only.
        assert store.db.execute("SELECT count(*) FROM documents WHERE kind='fulltext'").fetchone()[0] == 0
        empty = store.get(identity)
        empty['body'] = ''
        store.put(empty)
        store.db.commit()
        with patch.object(Sources, '_request') as http, patch('ideation.deep_dive.ResearchTools') as model:
            no_evidence = dive(store, tmp_path / 'empty', [identity], max_http_calls=0,
                               reason=True, brief={'objective': 'inspect'})
        http.assert_not_called()
        model.assert_not_called()
        assert no_evidence['status'] == 'no_usable_sources'
        assert no_evidence['reasoning_source_ids'] == []
    finally:
        store.db.close()


@pytest.mark.parametrize('url,oa', [(None, True), ('http://papers.example.edu/x.pdf', True),
    ('https://127.0.0.1/x.pdf', True), ('https://localhost/x.pdf', True),
    ('https://user:password@papers.example.edu/x.pdf', True), ('https://[bad/x.pdf', True),
    ('https://papers.example.edu/x.pdf', False)])
def test_unsupported_locations_are_explicit_skips_without_fetch(tmp_path, url, oa):
    store = Store(tmp_path / 'corpus.sqlite')
    try:
        identity = put_paper(store, 'unsupported', url, is_oa=oa)
        with patch.object(Sources, '_request') as http:
            result = dive(store, tmp_path / 'run', [identity])
        http.assert_not_called()
        assert result['reads'][0]['reason'] == 'no_supported_oa_pdf_locator'
        assert result['fulltext_coverage']['completed'] == 0
        assert result['sources'][0]['read_depth'] == 'abstract'
    finally:
        store.db.close()


def cli(state, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(['--state-dir', str(state), *args])
    assert code == 0, err.getvalue()
    return json.loads(out.getvalue())


def test_actual_cli_pdf_and_doi_only_then_offline_replay(tmp_path):
    cli(tmp_path, 'init')
    store = Store(tmp_path / 'research/corpus.sqlite')
    a = put_paper(store, 'pdf')
    b = put_paper(store, 'doi-only', None)
    store.db.close()
    args = ['--local-only', '--defer-snapshot', 'investigate', '--question', 'Read papers',
            '--source-id', a, '--source-id', b, '--deep-count', '2',
            '--max-repositories', '0', '--citations-per-paper', '0']
    with patch.object(Sources, '_request', return_value=(pdf_bytes(), 'application/pdf')) as http:
        result = cli(tmp_path, *args, '--max-http-calls', '1')
    assert http.call_count == 1
    assert result['dossier']['fulltext_coverage']['completed'] == 1
    assert result['dossier']['reads'][1]['reason'] == 'no_supported_oa_pdf_locator'
    with patch.object(Sources, '_request') as http:
        cached = cli(tmp_path, *args, '--offline')
    http.assert_not_called()
    assert cached['dossier']['http_cache_misses'] == 0
    assert cached['dossier']['fulltext_coverage']['completed'] == 1


def test_actual_mcp_pdf_partial_and_offline_budget(tmp_path):
    Client = pytest.importorskip("mcp").Client
    from ideation.mcp_server import create_server
    cli(tmp_path, 'init')
    store = Store(tmp_path / 'research/corpus.sqlite')
    a = put_paper(store, 'pdf')
    b = put_paper(store, 'uncached', 'https://papers.example.edu/uncached.pdf')
    c = put_paper(store, 'doi-only', None)
    store.db.close()
    async def check():
        async with Client(create_server(tmp_path, allow_network=True, defer_snapshot=True)) as client:
            args = {'source_ids': [a, b, c], 'question': 'Inspect evidence', 'repositories': [], 'citations_per_paper': 0}
            with patch.object(Sources, '_request', return_value=(pdf_bytes(), 'application/octet-stream')) as http:
                result = await client.call_tool('investigate', {**args, 'offline': False, 'max_http_calls': 1})
            assert not result.is_error and http.call_count == 1
            d = result.structured_content['dossier']
            assert d['fulltext_coverage'] == {'completed': 1, 'skipped': 2, 'failed': 0, 'selected_papers': 3}
            with patch.object(Sources, '_request') as http:
                replay = await client.call_tool('investigate', args)
            http.assert_not_called()
            assert not replay.is_error
            assert replay.structured_content['dossier']['http_cache_misses'] == 0
            assert replay.structured_content['dossier']['reads'][1]['reason'] == 'http_budget_exhausted'
    asyncio.run(check())

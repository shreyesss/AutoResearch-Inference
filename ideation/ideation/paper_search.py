"""Explicit, bounded online literature search using existing cached providers."""
import datetime as dt
import hashlib
import json

from .evidence import ResearchTools
from .sources import provider_error
from .store import content_fingerprint, now


def search_papers(store, query, providers=None, after=None, before=None, limit=10, client=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        raise ValueError('Supply a nonempty query of at most 2000 characters')
    query = ' '.join(query.split())
    providers = ['arxiv', 'openalex'] if providers is None else providers
    if not isinstance(providers, list) or not providers or any(p not in ('arxiv', 'openalex', 'hf') for p in providers):
        raise ValueError('Choose arxiv, openalex and/or hf')
    providers = list(dict.fromkeys(providers))
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('limit must be 1..20 per provider')
    for value in (after, before):
        if value is not None:
            if not isinstance(value, str) or len(value) != 10:
                raise ValueError('Dates must be YYYY-MM-DD')
            dt.date.fromisoformat(value)
    if after and before and after >= before:
        raise ValueError('after must precede exclusive before')
    identity = {'query': query, 'providers': providers, 'after': after, 'before': before, 'limit_per_provider': limit}
    query_id = 'paper-query:' + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    client = client or ResearchTools(store)
    results, hits = [], []
    for provider in providers:
        try:
            response = client.search(query, provider=provider, after=after, before=before, limit=limit)
            ids = response.get('ids', [])
            # Provider exception messages may contain authenticated URLs. Keep
            # explicit failure status and types, never raw exception strings.
            errors = []
            for error in response.get('errors', []):
                safe = {'provider': provider, 'error_type': error.get('error_type', 'ProviderSearchError')}
                code = error.get('http_status')
                if type(code) is int and 100 <= code <= 599:
                    safe['http_status'] = code
                errors.append(safe)
            results.append({'provider': provider, 'ids': ids, 'errors': errors, 'status': 'partial' if errors else 'completed',
                            'cache': response.get('cache') or getattr(getattr(client, 'sources', None), 'last_cache', None),
                            'attempts': response.get('attempts', [])})
            for rank, identifier in enumerate(ids, 1):
                doc = store.get(identifier)
                if not doc:
                    continue
                # Also enforce dates at our boundary; provider upper bounds can
                # be inclusive, and HF filtering happens after its top-k search.
                date = (doc.get('created_at') or '')[:10]
                if (after and (not date or date < after)) or (before and (not date or date >= before)):
                    continue
                metadata = doc.get('metadata', {})
                canonical = metadata.get('canonical_paper_id') or ('arxiv:' + identifier.split(':', 1)[1].split('v')[0] if identifier.startswith(('arxiv:', 'hf:')) else identifier)
                hits.append({'id': identifier, 'title': doc['title'], 'url': doc['url'], 'published_at': doc.get('created_at'),
                             'provider': provider, 'provider_rank': rank, 'revision_hash': content_fingerprint(doc),
                             'abstract': doc['body'][:6000], 'read_depth': metadata.get('read_depth', 'abstract'),
                             'canonical_paper_id': canonical})
                store.edge(identifier, 'discovered_by', query_id, identifier, {**identity, 'provider': provider, 'retrieved_at': now(),
                           'meaning': 'Returned by explicit provider query; not proof of relevance or independent discovery'})
            store.db.commit()
        except Exception as error:
            results.append({'provider': provider, 'ids': [], 'errors': [{'provider': provider, **provider_error(error)}], 'status': 'failed'})
    groups = {}
    for hit in hits:
        groups.setdefault(hit['canonical_paper_id'], []).append(hit['id'])
    return {**identity, 'query_id': query_id, 'searched_at': now(), 'hits': hits, 'providers': results,
            'paper_groups': groups, 'unique_paper_identities': len(groups),
            'interpretation': 'Mirrors sharing an explicit identity are one paper, not independent supporting evidence; unresolved identities may still duplicate.',
            'status': 'completed' if all(r['status'] == 'completed' for r in results) else 'partial' if hits else 'failed',
            'date_semantics': 'publication/submission date; after inclusive, before exclusive',
            'logical_provider_calls': len(providers), 'model_calls': 0, 'gpu_calls': 0,
            'coverage': 'Bounded relevance-ranked provider results, not exhaustive retrieval. Seed lookup is not independent discovery. Mirrors retain source IDs; no title-based deduplication.'}

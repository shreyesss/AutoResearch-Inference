"""Reproducible H200 research collection; no generation or serving mutations."""
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT))
os.environ['IDEATION_ENV_FILE'] = '/home/ubuntu/.env'
from ideation.store import Store, now
from ideation.github import GitHub
from ideation.fathom import FathomTools
from ideation.evidence import ResearchTools
from ideation.hypotheses import HypothesisTools

RUN = Path(__file__).resolve().parents[1]
OLD = PROJECT / 'runs/pr-evaluation-audit-001'
DB = PROJECT / 'data/corpus.sqlite'
ROWS = list(csv.DictReader((OLD / 'inputs/vllm-dsv41-dspark-items.csv').open()))
REPOS = sorted({r['repo'] for r in ROWS})

def save(name, value):
    p = RUN / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

QUERIES = {
    'hopper': 'H200 H100 H20 Hopper SM90',
    'model': '"DeepSeek-V4.1" "DSv4.1" DSpark',
    'attention': 'planner sparse indexer topk SWA',
    'speculation': 'drafter padding "adaptive verification" "block rejection"',
    'communication': 'DeepEP "allgather_reducescatter" "CPU allreduce" "NVLink"',
    'host': 'Engram NUMA pinned registration',
    'scheduler': 'scheduler "data parallel" "prefix cache" routing',
    'fusion': 'Marlin fusion MXFP4 "launch overhead"',
    'negative': 'regression deadlock corruption "incorrect output"',
}

def bootstrap():
    store = Store(DB)
    count = 0
    for line in (OLD / 'inputs/corpus-opening-records.jsonl').open():
        d = json.loads(line)
        d.setdefault('source', 'github')
        d.setdefault('kind', 'pr' if '/pull/' in d.get('url', '') else 'issue')
        d.setdefault('url', d['id'].replace('github:', 'https://github.com/').replace(':', '/issues/', 1))
        d.setdefault('metadata', {})
        if isinstance(d['metadata'], str):
            d['metadata'] = json.loads(d['metadata'])
        d['metadata']['import_origin'] = str(OLD / 'inputs/corpus-opening-records.jsonl')
        # This is historical import, not a live refresh.
        if not store.get(d['id']):
            store.put(d)
            count += 1
    store.db.commit()
    memory = HypothesisTools(store).import_runs(str(PROJECT / 'runs'))
    save('bootstrap.json', {'at': now(), 'imported': count, 'repos': REPOS, 'rows': len(ROWS), 'memory_import': memory})
    print(json.dumps({'imported': count, 'repos': len(REPOS), 'memory': memory.get('memory')}), flush=True)

def local():
    store = Store(DB)
    results = []
    for repo in REPOS:
        for family, query in QUERIES.items():
            hits = store.search(query, id_prefix='github:' + repo + ':', limit=35)
            results.append({'repo': repo, 'family': family, 'query': query, 'hits': [{'id': x['id'], 'title': x['title'], 'kind': x['kind'], 'updated_at': x.get('updated_at')} for x in hits]})
    save('discovery/local-searches.json', results)
    print(json.dumps({'queries': len(results), 'unique_hits': len({h['id'] for r in results for h in r['hits']})}), flush=True)

def live():
    # Per-repository complete pagination for the overlap interval, with explicit cap.
    # Opening feed includes PRs and issues; discussions are hydrated separately.
    store = Store(DB)
    records = []
    for repo in REPOS:
        gh = GitHub(store, repo)
        start = now()
        error = None
        try:
            gh.sync(feeds=['issues'], max_pages=12 if repo == 'vllm-project/vllm' else 4, recent_days=4)
        except Exception as e:
            error = type(e).__name__ + ': ' + str(e)
        checkpoint = store.get_checkpoint(repo + ':recent:issues', {})
        records.append({'repo': repo, 'started_at': start, 'finished_at': now(), 'checkpoint': checkpoint, 'error': error})
        save('discovery/live-repo-coverage.json', records)
        print(json.dumps(records[-1]), flush=True)

def web():
    for repo in REPOS:
        store = Store(DB)
        f = FathomTools(store)
        query = 'site:github.com/' + repo + ' (H200 OR H100 OR H20 OR SM90 OR Hopper) (performance OR latency OR DeepSeek)'
        record = {'repo': repo, 'query': query, 'at': now()}
        try:
            record['result'] = f.search(query, refresh=True)
            record['source'] = store.get(record['result']['id'])
        except Exception as e:
            record['error'] = type(e).__name__ + ': ' + str(e)
        save('discovery/web-' + repo.replace('/', '--') + '.json', record)
        print(json.dumps({k:v for k,v in record.items() if k != 'source'}), flush=True)
        store.db.close()

def literature():
    store = Store(DB)
    research = ResearchTools(store)
    queries = ['GPU sparse attention indexer inference', 'mixture of experts inference communication overlap', 'speculative decoding dynamic batching padding', 'prefix cache routing language model serving']
    for i, query in enumerate(queries):
        r = {'query': query}
        try:
            r['result'] = research.search(query, provider='openalex', limit=5, refresh=True)
            r['sources'] = [store.get(x) for x in r['result']['ids']]
        except Exception as e:
            # Provider exceptions may include credential-bearing URLs.
            r['error'] = type(e).__name__
        save('discovery/literature-' + str(i) + '.json', r)
        print(json.dumps({'query':query,'ids':r.get('result',{}).get('ids',[]),'error':r.get('error')}), flush=True)

if __name__ == '__main__':
    globals()[sys.argv[1]]()

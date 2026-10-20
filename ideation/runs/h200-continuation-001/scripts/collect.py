"""Resumable bounded acquisition and uncapped local topic scan; no serving work."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from collections import Counter

PROJECT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from ideation.store import Store, now
from ideation.github import GitHub

TOPICS = {
    'speculation': r'dspark|dflash|draft|speculat|mtp|adaptive.verification|confidence.head|acceptance',
    'graph_shapes': r'cuda.graph|graph.capture|graph.replay|padding|padded|bucket|ragged|variable.length',
    'attention_indexer': r'flashmla|attention|indexer|top.?k|deepselect|sparse|candidate.only|page.mapping|\brope\b|bank.conflict',
    'moe_compute': r'marlin|humming|moe|gemm|mxfp4|nvfp4|expert|swiglu',
    'mhc_fusion': r'\bmhc\b|hyper.connection|prenorm|epilogue|fusion|fused|materializ',
    'communication': r'deepep|nvlink|all.?gather|all.?reduce|reduce.?scatter|collective|rank.skew|synchroniz',
    'host_memory': r'engram|numa|host.memory|pinned.memory|registration|zero.copy|host.lookup',
    'scheduler': r'schedul|admission|prefill|queue|head.of.line|token.budget|async|dispatch',
    'kv_routing': r'kv.cache|prefix.cache|cache.hit|cache.affinity|rout|evict|offload|yoco|bounded.replay',
    'load_balance': r'eplb|load.balanc|expert.replic|straggl|hot.expert',
    'correctness': r'correct|deadlock|hang|race.condition|sampling|determin|numerical|nan|temperature|\boob\b|out.of.bounds|illegal.memory|abort|crash|leak|watchdog',
    'quantization': r'quant|fp8|bf16|fp4|mxfp|amax|underflow|overflow|scale.factor',
    'release_compatibility': r'public.release|model.*support.*deepseek|vendor.patch|dependency|abi|compatib',
    'evaluation': r'benchmark|evaluat|profil|metric|percentile|itl|tpot|ttft|throughput|regression',
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def collect(resume=False):
    s = Store(PROJECT / 'data/corpus.sqlite')
    original = list(csv.DictReader((PROJECT / 'runs/pr-evaluation-audit-001/inputs/vllm-dsv41-dspark-items.csv').open()))
    repos = ['deepseek-ai/DeepInfer', 'vllm-project/vllm', 'sgl-project/sglang'] + sorted(
        {r['repo'] for r in original} - {'vllm-project/vllm'}) + ['vllm-project/humming', 'vllm-project/FlashMLA']
    summary = []
    for repo in repos:
        output = RUN / 'discovery' / (repo.replace('/', '--') + '.json')
        # Exact saved receipts are resumed, not silently refreshed or treated as current forever.
        previous = json.loads(output.read_text()) if output.exists() else None
        if previous and (not resume or previous['complete_for_interval'] or not previous.get('next_url')):
            summary.append(previous)
            continue
        g = GitHub(s, repo)
        g.syncing = True
        record = {'repo': repo, 'started_at': now(), 'since': None if repo.endswith('/DeepInfer') else '2026-10-13T00:00:00Z',
                  'pages': [], 'ids': [], 'complete_for_interval': False, 'error': None}
        cap = 5 if repo.endswith('/DeepInfer') else 4 if repo == 'vllm-project/vllm' else 3 if repo == 'sgl-project/sglang' else 2
        next_url = None
        if previous:
            history = RUN / 'discovery/feed-history'
            history.mkdir(exist_ok=True)
            raw = output.read_bytes()
            (history / (output.stem + '-' + hashlib.sha256(raw).hexdigest()[:16] + '.json')).write_bytes(raw)
            record = previous
            record['resumed_at'] = now()
            record['error'] = None
            next_url = record['next_url']
            cap = 2  # Explicit bounded increment; keep the next cursor if still incomplete.
        try:
            for page in range(cap):
                params = {'state': 'all', 'per_page': 100, 'sort': 'updated', 'direction': 'desc'}
                if record['since']:
                    params['since'] = record['since']
                items, headers = g.get(next_url) if next_url else g.get('issues', params)
                for item in items:
                    g.ingest(item)
                    record['ids'].append(f"github:{repo}:{item['number']}")
                s.db.commit()
                link = headers.get('Link') or headers.get('link', '')
                match = re.search(r'<([^>]+)>;\s*rel="next"', link)
                next_url = match.group(1) if match else None
                record['pages'].append({'count': len(items), 'remaining': headers.get('X-RateLimit-Remaining') or headers.get('x-ratelimit-remaining')})
                if not next_url:
                    record['complete_for_interval'] = True
                    break
        except Exception as error:
            record['error'] = type(error).__name__ + ': ' + str(error)[:250]
        record.update(finished_at=now(), next_url=next_url, page_cap=cap)
        write(output, record)
        summary.append(record)
        print(json.dumps({'repo': repo, 'records': len(record['ids']), 'complete': record['complete_for_interval'], 'error': record['error']}), flush=True)
    write(RUN / 'discovery/feed-coverage.json', summary)


def scan():
    s = Store(PROJECT / 'data/corpus.sqlite')
    docs = {d['id']: dict(d) for d in s.db.execute("SELECT id,title,body,url,kind FROM documents WHERE source='github' AND kind IN ('pr','issue')")}
    catalog = [dict(d) for d in s.db.execute('SELECT * FROM source_catalog')]
    entries = {d['id']: {'id': d['id'], 'repo': d['repo'], 'title': d['title'], 'url': d['url'], 'origin': 'catalog'} for d in catalog}
    for identity, doc in docs.items():
        entries.setdefault(identity, {'id': identity, 'repo': identity.split(':')[1], 'title': doc['title'], 'url': doc['url'], 'origin': 'opening_record'})
    counts = Counter()
    rows = []
    for identity, entry in sorted(entries.items()):
        doc = docs.get(identity)
        text = (entry['title'] + '\n' + (doc['body'] if doc else '')).lower()
        topics = [k for k, pattern in TOPICS.items() if re.search(pattern, text)]
        counts.update(topics)
        rows.append({**entry, 'topics': ','.join(topics), 'depth': 'opening_body' if doc else 'title_only',
                     'disposition': 'needs_primary_review' if topics else 'unmatched_not_excluded'})
    with (RUN / 'discovery/topic-ledger.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    unmatched = sorted((r for r in rows if not r['topics']), key=lambda x: hashlib.sha256(x['id'].encode()).hexdigest())
    write(RUN / 'discovery/unmatched-audit-sample.json', unmatched[:40])
    matrix = {repo: {topic: sum(r['repo'] == repo and topic in r['topics'].split(',') for r in rows) for topic in TOPICS} for repo in sorted({r['repo'] for r in rows})}
    write(RUN / 'discovery/topic-coverage.json', {'at': now(), 'topics': TOPICS, 'counts': dict(counts), 'by_repo': matrix,
          'unique_entries': len(rows), 'title_only': sum(r['depth'] == 'title_only' for r in rows),
          'unmatched': len(unmatched), 'sample_size': min(40, len(unmatched)),
          'limitations': ['No local result cap; all stored titles and available opening bodies scanned.', 'Regex retrieval is not semantic review or a completeness guarantee.', 'No automatic exclusions; unmatched sources remain visible.', 'Live feed caps and interval are separate in feed-coverage.json.']})
    print(json.dumps({'entries': len(rows), 'topic_counts': dict(counts), 'unmatched': len(unmatched)}))


if __name__ == '__main__':
    {'collect': collect, 'resume': lambda: collect(resume=True), 'scan': scan}[sys.argv[1]]()

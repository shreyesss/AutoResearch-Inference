"""Retain selected openings, proposed patches and source pins for close review."""
import concurrent.futures
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from ideation.store import Store, now

SELECTED = {
    'deepseek-ai/DeepInfer': [35, 47, 54, 88, 91, 92, 99, 101, 107, 108, 111, 100, 102, 112],
    'vllm-project/vllm': [61903, 59609, 59611, 61509, 61869, 41148],
    'sgl-project/sglang': [45433, 45421, 45407, 45207, 45031],
    'deepseek-ai/DeepEP': [789],
    'deepseek-ai/DeepGEMM': [344, 463, 473],
    'deepseek-ai/DeepSpec': [26],
    'deepseek-ai/FlashMLA': [197],
}


def download(spec):
    repo, number, doc = spec
    target = RUN / 'sources' / (repo.replace('/', '--') + '--' + str(number))
    target.mkdir(exist_ok=True)
    receipt_path = target / 'receipt.json'
    if receipt_path.exists():
        return json.loads(receipt_path.read_text())
    record = {'repo': repo, 'number': number, 'at': now(), 'url': doc['url'], 'state': doc.get('state'), 'files': {}, 'errors': []}
    (target / 'opening.json').write_text(json.dumps(doc, indent=2) + '\n')
    urls = [('page.html', doc['url'])]
    if doc['kind'] == 'pr':
        urls.append(('changes.patch', f'https://patch-diff.githubusercontent.com/raw/{repo}/pull/{number}.patch'))
    for name, url in urls:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'inference-research'}), timeout=40) as response:
                raw = response.read()
            if name.endswith('.patch') and b'diff --git ' not in raw:
                raise ValueError('No diff in response')
            (target / name).write_bytes(raw)
            record['files'][name] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        except Exception as error:
            record['errors'].append({'url': url, 'error': type(error).__name__})
    receipt_path.write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    store = Store(PROJECT / 'data/corpus.sqlite')
    work = []
    for repo, numbers in SELECTED.items():
        for number in numbers:
            doc = store.get(f'github:{repo}:{number}')
            if doc:
                work.append((repo, number, doc))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(download, work))
    for item in records:
        folder = RUN / 'sources' / (item['repo'].replace('/', '--') + '--' + str(item['number']))
        if (folder / 'changes.patch').exists():
            identity = f"github:{item['repo']}:{item['number']}"
            store.put({'id': identity + ':continuation-patch', 'source': 'github', 'kind': 'code',
                       'title': identity + ' proposed patch (unexecuted)', 'body': (folder / 'changes.patch').read_text(),
                       'url': item['url'] + '.patch', 'parent': identity, 'metadata': item['files']['changes.patch']})
    store.db.commit()
    (RUN / 'sources/primary-manifest.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps({'sources': len(records), 'patches': sum('changes.patch' in r['files'] for r in records), 'errors': [r for r in records if r['errors']]}))


if __name__ == '__main__':
    main()

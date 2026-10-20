"""Archive current PR pages and patches; HTML discussion coverage is explicit."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import sys
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
from ideation.store import Store, now

TARGETS = {
 'vllm-project/vllm': [58818,58984,61767,59468,59849,59923,62359,51333,51199,61834,52464,57673,59418,61615,59204,61830,62000,62463,61875,62603,59488,52318,56697,61461,60768,60777,59129,54032,58540,56752,62384,56205,58986,57352],
 'deepseek-ai/DeepGEMM': [303,325,350,399,411,415,440,448,449,452,473],
 'deepseek-ai/FlashMLA': [200,213,216,221],
 'deepseek-ai/DeepEP': [605,693,763],
 'deepseek-ai/DeepSelect': [14,25],
 'deepseek-ai/TileKernels': [18,23,32],
 'deepseek-ai/DeepJIT': [12,14,17],
 'deepseek-ai/Engram': [27],
 'deepseek-ai/deepseek-recipe': [11,15,24,25],
 'flashinfer-ai/flashinfer': [6009,6058,6243,6343,6517,6587],
 'SemiAnalysisAI/InferenceX': [2963,3077,3099,3134,3239],
 'vllm-project/recipes': [1005,1136,989],
}

def fetch(item):
    repo, number = item
    identity = f'github:{repo}:{number}'
    prefix = repo.replace('/', '--') + '--' + str(number)
    out = ROOT / 'primary' / prefix
    out.mkdir(parents=True, exist_ok=True)
    record = {'id': identity, 'repo':repo, 'number':number, 'fetched_at':now(), 'discussion_coverage':'HTML-visible only; not exhaustive formal reviews or paginated replies'}
    try:
        response = requests.get(f'https://github.com/{repo}/issues/{number}', timeout=60)
        response.raise_for_status()
        html = response.content
        (out/'page.html').write_bytes(html)
        soup = BeautifulSoup(html, 'html.parser')
        for x in soup(['script','style','nav','header','footer']): x.decompose()
        main = soup.find('main') or soup
        body = main.get_text('\n', strip=True)
        (out/'page.txt').write_text(body)
        record.update(url=response.url, html_sha256=hashlib.sha256(html).hexdigest(), text_sha256=hashlib.sha256(body.encode()).hexdigest(), characters=len(body), title=soup.title.get_text() if soup.title else identity)
        if '/pull/' in response.url:
            patch = requests.get(response.url + '.patch', timeout=90)
            record['patch_status'] = patch.status_code
            if patch.status_code == 200 and patch.text.startswith('From '):
                (out/'changes.patch').write_bytes(patch.content)
                record.update(patch_sha256=hashlib.sha256(patch.content).hexdigest(), patch_commit_shas=re.findall(r'^From ([a-f0-9]{40}) ', patch.text, re.M), changed_paths=sorted(set(re.findall(r'^diff --git a/(.*?) b/',patch.text,re.M))))
            else:
                record['patch_error'] = 'HTTP ' + str(patch.status_code) + ' or non-patch payload'
        record['body'] = body
    except Exception as e:
        record['error'] = type(e).__name__ + ': ' + str(e)
    return record, out

def main():
    items=[(r,n) for r,ns in TARGETS.items() for n in ns]
    store = Store(ROOT.parents[1]/'data/corpus.sqlite')
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for record,out in executor.map(fetch,items):
            if 'body' in record:
                # Keep canonical API/Markdown opening record intact. HTML text is a separate source snapshot.
                store.put({'id':record['id']+':live-page','source':'github','kind':'resource','title':record['title'],'body':record.pop('body'),'url':record['url'],'parent':record['id'],'metadata':{k:v for k,v in record.items() if k!='body'}})
                store.db.commit()
            (out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
            records.append(record)
            (ROOT/'primary-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
            print(record['id'],record.get('characters'),record.get('patch_status'),record.get('error',''),flush=True)

if __name__=='__main__':main()

"""Bounded, cached primary-source refresh through the existing GitHub tool.

Run from ideation on the controller. No environment-file reads, inference,
serving changes, or GPU work. Existing GitHub cache/rate-limit behavior applies.
"""
import hashlib
import json
from pathlib import Path
from ideation.store import Store, now
from ideation.github import GitHub

ROOT = Path('runs/h200-pr-evaluation-audit-001')
ITEMS = {
    'vllm-project/vllm': [62463,62000,61830,61615,59418,57673,56697,52318,59488,61875,58872,59204,60768,60777,61461,59129,52795,54011,56448,53709,58540,62603,58684,61399,61039,62040,58984,59468,61161,62199,62259,59559,62062,61724,51333,59849,59327,60938,61261,54077,47926,62278,57110,59096,59140,62041,47891,61375,61961,51743,59305,56443,52164,53852,62467],
    'deepseek-ai/DeepSelect': [14],
    'deepseek-ai/DeepGEMM': [303,350,452,455,469,448,449,476,477,473],
    'deepseek-ai/FlashMLA': [200],
    'vllm-project/FlashMLA': [26],
    'SemiAnalysisAI/InferenceX': [3310,3099,3077,2963,3000],
}
ISSUES = {('vllm-project/vllm',n) for n in [61830,54011,51743,59305,56443]}
ISSUES |= {('deepseek-ai/DeepGEMM',n) for n in [449,476]}
DIFFS = {('vllm-project/vllm',n) for n in [62463,62000,61615,59418,57673,56697,52318,59488,61875,58872,59204,60768,60777,61461,59129,52795,56448,53709,62603,61039,52164,53852,62467]}
DIFFS |= {('deepseek-ai/DeepSelect',14),('vllm-project/FlashMLA',26),('deepseek-ai/DeepGEMM',448),('SemiAnalysisAI/InferenceX',3310)}

def main():
    dest=ROOT/'sources';dest.mkdir(parents=True,exist_ok=True)
    store=Store('data/corpus.sqlite');manifest=[]
    for repo,nums in ITEMS.items():
        gh=GitHub(store,repo)
        for number in nums:
            path=dest/(repo.replace('/','__')+'__'+str(number)+'.json')
            if path.exists():
                old=json.loads(path.read_text())
                if old.get('document') and not old.get('error'):
                    manifest.append({'repo':repo,'number':number,'file':path.name,'reused_snapshot':True});continue
            record={'repo':repo,'number':number,'retrieved_at':now()}
            try:
                endpoint='issues' if (repo,number) in ISSUES else 'pulls'
                try:
                    doc,headers=gh.get(endpoint+'/'+str(number))
                except Exception:
                    if endpoint!='pulls':raise
                    doc,headers=gh.get('issues/'+str(number));endpoint='issues'
                record.update(document=doc,endpoint=endpoint,body_sha256=hashlib.sha256((doc.get('body')or'').encode()).hexdigest())
                if endpoint=='pulls' and (repo,number) in DIFFS:
                    files,_=gh.get('pulls/'+str(number)+'/files',{'per_page':100})
                    record['files']=files
                    record['files_complete']=len(files)==doc.get('changed_files')
                print(repo,number,endpoint,doc.get('state'),'files',len(record.get('files',[])),flush=True)
            except Exception as e:
                record['error']=type(e).__name__+': '+str(e)
                print(repo,number,'ERROR',type(e).__name__,flush=True)
            path.write_text(json.dumps(record,indent=2)+'\n')
            manifest.append({'repo':repo,'number':number,'file':path.name,'error':record.get('error')})
            (dest/'retrieval-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (dest/'retrieval-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()

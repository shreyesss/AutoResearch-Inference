import json
from unittest.mock import patch
import pytest
from ideation.store import Store
from ideation.paper_search import search_papers
from ideation.foundation import invoke

class Provider:
    def __init__(self, store): self.store=store; self.calls=[]
    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        p=kwargs['provider']
        if p=='hf':raise RuntimeError('secret authenticated URL must not be logged')
        ids=[]
        for i,date in enumerate(['2026-09-01','2026-09-30','2026-10-01']):
            identifier=p+':'+str(i)
            self.store.put({'id':identifier,'source':p,'kind':'paper','title':'Speculation '+str(i),'body':'fixture',
                            'url':'https://example.org/'+str(i),'created_at':date})
            ids.append(identifier)
        return {'ids':ids,'errors':[],'cache':{'hit':True}}


def test_provider_dates_persistence_provenance_and_partial_failure(tmp_path):
    store=Store(tmp_path/'corpus.sqlite');client=Provider(store)
    try:
        result=search_papers(store,'speculative decoding',['arxiv','openalex','hf'],'2026-09-01','2026-10-01',5,client)
        assert len(result['hits'])==4
        assert all(h['published_at']<'2026-10-01' for h in result['hits'])
        assert result['status']=='partial' and result['logical_provider_calls']==3
        assert 'secret authenticated' not in json.dumps(result)
        assert client.calls[0][1]['after']=='2026-09-01'
        assert store.db.execute("SELECT count(*) FROM edges WHERE relation='discovered_by'").fetchone()[0]==4
    finally:store.db.close()


@pytest.mark.parametrize('kwargs',[{'after':'2026-13-01'},{'after':'2026-09-01','before':'2026-09-01'},{'providers':[]},{'providers':['serper']},{'limit':21},{'limit':True}])
def test_invalid_search_rejected_before_provider_call(tmp_path,kwargs):
    store=Store(tmp_path/'corpus.sqlite');client=Provider(store)
    try:
        with pytest.raises(ValueError):search_papers(store,'speculation',client=client,**kwargs)
        assert client.calls==[]
    finally:store.db.close()


def test_cli_search_keeps_receipt_and_dates(tmp_path):
    invoke(['--state-dir',str(tmp_path),'init'])
    with patch('ideation.paper_search.ResearchTools',Provider):
        result=invoke(['--state-dir',str(tmp_path),'--local-only','paper-search','speculation','--provider','arxiv','--after','2026-09-01','--before','2026-10-01'])
    assert len(result['hits'])==2
    from pathlib import Path
    assert (Path(result['output'])/'search.json').exists()

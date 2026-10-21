#!/usr/bin/env python3
"""Offline fixture trace. Requires a fresh directory; no provider or GPU calls."""
import argparse
import json
from pathlib import Path
from ideation.foundation import invoke, _locked
from ideation.store import Store


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    args=parser.parse_args(); root=args.state_dir.expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit('Choose a fresh empty directory; production state is not a fixture destination')
    fixture=json.loads((Path(__file__).resolve().parents[1]/'ideation/examples/evidence_fixture.json').read_text())
    base=['--state-dir',str(root),'--local-only']
    invoke(base+['init'])
    with _locked(root):
        store=Store(root/'research/corpus.sqlite');store.put(fixture['source']);store.db.commit();store.db.close()
    inputs=root/'demo-inputs';inputs.mkdir()
    def record(command,value):
        path=inputs/(str(len(list(inputs.iterdir())))+'.json');path.write_text(json.dumps(value,indent=2))
        return invoke(base+command+['--record',str(path)])['record']
    claim=record(['claim','record'],fixture['claim'])
    proposal=fixture['proposal'];proposal['claim_links']=[{'claim_id':claim['id'],'relation':'supports','rationale':'Mechanism only; target gain unknown'}]
    hypothesis=record(['hypothesis','propose'],proposal)
    identity=hypothesis['id']
    screen=record(['screen',identity],{})
    plan=record(['eval-plan',identity],{'purpose':'diagnostic','scope':'service'})
    decision=record(['decide',identity],{'status':'deferred','actor':'offline-fixture-agent','rationale':'Missing target trace and reproducible execution pins','reopen_when':'Target timing/acceptance trace and baseline manifest are available'})
    dossier=invoke(base+['hypothesis','show',identity])
    out=root/'demo-transcript.json'
    out.write_text(json.dumps({'fixture':True,'source':fixture['source']['id'],'claim':claim,'hypothesis':identity,'screen':screen,'eval_plan':plan,'decision':decision,'dossier':dossier,'network_calls':0,'gpu_calls':0},indent=2))
    print(json.dumps({'transcript':str(out),'hypothesis_id':identity,'status':dossier['hypothesis']['status'],'target_prediction':None,'experiment_status':dossier['hypothesis']['experiment_status'],'network_calls':0,'gpu_calls':0},indent=2))


if __name__=='__main__':
    main()

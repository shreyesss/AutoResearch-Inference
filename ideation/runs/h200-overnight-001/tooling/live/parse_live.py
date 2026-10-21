"""Frozen descriptive live reader: no native round pairing or event bootstrap."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def worker_external_id(value):
    # Pinned InputProcessor.assign_request_id appends exactly 8 uuid characters.
    match=re.fullmatch(r'((?:chatcmpl-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})|(?:cmpl-[0-9a-f]{16}-0))-([0-9a-f]{8})',value)
    return match.group(1) if match else None

def read_lines(path):
    with Path(path).open() as handle:
        yield from handle

def read_client(artifacts):
    records={};errors=[]
    raw=Path(artifacts)/'profile_export_raw.jsonl'
    for line in read_lines(raw):
        row=json.loads(line);meta=row['metadata'];xid=meta['x_request_id']
        if row['request_headers'].get('X-Request-ID')!=xid:raise AssertionError('header/metadata ID mismatch')
        ids=set();usage=None;done=False;finish=None
        for response in row['responses']:
            for packet in response['packets']:
                if packet['name']!='data':continue
                data=packet['value']
                if data=='[DONE]':done=True;continue
                event=json.loads(data)
                if event.get('id'):ids.add(event['id'])
                if event.get('usage'):usage=event['usage']
                for choice in event.get('choices',[]):
                    if choice.get('finish_reason') is not None:finish=choice['finish_reason']
        external='chatcmpl-'+xid
        if ids!={external}:raise AssertionError('ambiguous or unexpected exact response ID')
        if external in records:raise AssertionError('duplicate client request ID')
        complete=(row['status']==200 and done and finish in ('length','stop') and usage is not None
            and not meta.get('was_cancelled') and not meta.get('context_overflow_skip'))
        record=dict(external_id=external,phase=meta['benchmark_phase'],phase_index=meta['phase_index'],
            complete=complete,committed_tokens=(usage.get('completion_tokens') if usage else None),finish=finish)
        records[external]=record
        if not complete:errors.append(external)
    profile=[v for v in records.values() if v['phase']=='profiling']
    # Actual AIPerf uses 'profiling'; unknown phases remain explicit.
    return records,dict(total=len(records),profiling=len(profile),profiling_complete=sum(v['complete'] for v in profile),
        errors=errors,phases=dict(Counter(v['phase'] for v in records.values())),
        committed_tokens_by_phase={phase:sum(v['committed_tokens'] or 0 for v in records.values() if v['phase']==phase)
                                  for phase in sorted({v['phase'] for v in records.values()})}),sha(raw)

def read_primers(path, clients):
    value=json.loads(Path(path).read_text())
    assert value['primer_status']=='passed' and len(value['requests'])==8
    inventory=set();caps=(17,19,23,29);tokens=(671,2581,3967,10059,678)
    for request in value['requests']:
        replica,rank=request['replica'],request['requested_internal_rank'];key=(replica,rank)
        assert key not in inventory and replica in (0,1) and rank in range(4)
        inventory.add(key);cap=caps[rank];expected=tokens[(replica+rank)%5]
        assert request['independent_token_oracle']=='pass' and request['token_ids']==[expected]*cap
        assert request['finish_reason']=='length' and request['usage']['completion_tokens']==cap
        assert request['headers']['X-data-parallel-rank']==str(rank)
        external=request['response_id']+'-0'
        assert re.fullmatch(r'cmpl-[0-9a-f]{16}-0',external) and external not in clients
        clients[external]=dict(external_id=external,phase='metric_primer',phase_index=-1,complete=True,committed_tokens=cap,finish='length')
    return {'requests':8,'committed_tokens':sum(caps)*2,'sha256':sha(path)}

def stats(values):
    values=sorted(values)
    return dict(count=len(values),mean_us=statistics.mean(values),median_us=statistics.median(values),
        p95_us=values[max(0,math.ceil(.95*len(values))-1)],min_us=values[0],max_us=values[-1]) if values else None

def classify(record,clients):
    matched=[clients.get(worker_external_id(x)) for x in record['req_ids']]
    phases={v['phase'] if v else 'unknown' for v in matched}
    phase=next(iter(phases)) if len(phases)==1 else 'mixed_phase'
    primary=phase=='profiling' and not record['has_prefill'] and record['target']['cg_mode']=='FULL' and record['draft']['cg_mode']=='FULL'
    return phase,primary,sum(x is None for x in matched)

def stratum(replica,rank,record):
    maximum=max(record['context_upper'])
    context='lt8192' if maximum<8192 else '8192to32767' if maximum<32768 else 'ge32768'
    return (replica,rank,record['target']['num_reqs'],record['target']['num_tokens'],record['draft']['num_reqs'],record['draft']['num_tokens'],context)

def validate_activation(receipt,native,arm):
    assert native['native_oracle_passed'] is True and native['capture_attestation_passed'] is True
    assert native['guards'] and all(native['guards'].values())
    assert receipt['activation']['active'] is (arm=='B')
    assert native['activation']['active'] is (arm=='B')
    if arm=='B':assert receipt['activation']==native['activation']
    assert native['captures'] and all(c['branch']==('fused' if arm=='B' else 'installed') and c['sample_steps']==[0,1,2,3,4] for c in native['captures'])

def load_arm(path,arm,expected_run=None,observer_sha=None):
    path=Path(path);traffic=json.loads((path/'live-traffic.json').read_text())
    assert traffic['status']=='passed' and traffic['arm']==arm
    if expected_run is not None:assert traffic['run_id']==expected_run
    clients,client_summary,client_sha=read_client(path/'artifacts')
    assert client_summary['profiling']==480 and client_summary['profiling_complete']==480 and not client_summary['errors']
    assert sha(path/'live-control.json')==traffic['control_receipt']['sha256']
    primer_summary=read_primers(path/'live-control.json',clients)
    client_summary['metric_primers']=primer_summary
    cells=defaultdict(list);blocks=defaultdict(list);exposure=Counter();uuids={};raw=[];first={};contexts=defaultdict(list)
    receipts=[]
    for replica in range(2):
        for rank in range(4):
            p=path/'live-observations'/f'replica{replica}'/f'rank{rank}.json';r=json.loads(p.read_text())
            assert (r['status'],r['arm'],r['run_id'],r['replica'],r['rank'],r['nonce'])==('passed',arm,traffic['run_id'],replica,rank,traffic['nonce'])
            assert r['overflow']==r['unfinished_calls']==r['missing_outputs']==0 and not r['errors']
            if observer_sha is not None:assert r['observer_sha256']==observer_sha
            native=json.loads((path/'observations'/f'replica{replica}'/f'rank{rank}.json').read_text())
            for field in ('pid','pid_start_ticks','gpu_uuid','run_id','arm'):assert r[field]==native[field]
            assert native['status']=='passed' and native['restored'] is True
            validate_activation(r,native,arm)
            assert r['initialization']['capacity']==65536 and r['initialization']['events']==131072
            data=p.with_name(r['records_path']);assert sha(data)==r['records_sha256']
            rows=[json.loads(line) for line in read_lines(data)]
            assert len(rows)==r['real_calls']==r['admitted_calls']
            assert [x['call_index'] for x in rows]==list(range(len(rows)))
            uuids[replica,rank]=r['gpu_uuid'];receipts.append({'path':str(p),'sha256':sha(p)})
            exposure['dummy_calls']+=r['dummy_calls']
            for row in rows:
                assert math.isfinite(row['duration_us']) and row['duration_us']>0
                assert math.isfinite(row['time_unix_s']) and row['actual_rows']>0
                assert len(row['context_upper'])==row['actual_rows'] and all(type(x) is int and x>=0 for x in row['context_upper'])
                assert row['stream']==r['stream']
                assert row['output'] is not None and row['output']['output_worker_pid']==r['pid']
                assert row['output']['req_ids']==row['req_ids']
                assert len(row['req_ids'])==row['actual_rows']==len(row['output']['num_sampled_tokens'])
                assert [len(x) for x in row['output']['sampled_token_ids']]==row['output']['num_sampled_tokens']
                phase,primary,unknown=classify(row,clients)
                exposure['real_calls']+=1;exposure['active_rows']+=row['actual_rows'];exposure['unknown_request_rows']+=unknown
                exposure['phase:'+phase]+=1;exposure['prefill_calls' if row['has_prefill'] else 'pure_decode_calls']+=1
                exposure['draft_capacity:'+str(row['draft']['num_reqs'])]+=1
                exposure['model_returned_tokens']+=sum(row['output']['num_sampled_tokens'])
                raw.append((replica,rank,row['duration_us'],phase))
                if phase=='profiling':first.setdefault((replica,rank),row['time_unix_s'])
                if primary:
                    key=stratum(replica,rank,row);cells[key].append(row);contexts[key].extend(row['context_upper'])
                    start=first[replica,rank]
                    block=int((row['time_unix_s']-start)//10);assert block>=0
                    blocks[replica,rank,block].append(row['duration_us'])
    assert len(set(uuids.values()))==8
    return dict(run_id=traffic['run_id'],uuids=uuids,cells=cells,blocks=blocks,exposure=dict(exposure),
        clients=client_summary,client_sha=client_sha,receipts=receipts,raw=raw,contexts=contexts)

def context_stats(values):
    data=stats(values)
    return {k.replace('_us','_tokens'):v for k,v in data.items()}

def validate_launch(a,b,launch):
    import uuid
    norm=lambda v:str(uuid.UUID(v.removeprefix('GPU-')))
    assert a['run_id']==b['run_id']==launch['run_id']
    inventory={}
    for line in launch['gpu_inventory'].splitlines():
        fields=[x.strip() for x in line.split(',')];inventory[int(fields[0])]=norm(fields[1])
    for item in (a,b):
        for (replica,rank),value in item['uuids'].items():assert norm(value)==inventory[4*replica+rank]

def summarize(a,b):
    assert a['run_id']==b['run_id'] and a['uuids']==b['uuids']
    common=sorted(set(a['cells'])&set(b['cells']));rows=[]
    for key in common:
        av=[x['duration_us'] for x in a['cells'][key]];bv=[x['duration_us'] for x in b['cells'][key]]
        aa,bb=stats(av),stats(bv)
        rows.append(dict(stratum=key,A=aa,B=bb,delta_us=aa['mean_us']-bb['mean_us'],
            gain_percent=100*(aa['mean_us']-bb['mean_us'])/aa['mean_us'],
            A_active_rows=sum(x['actual_rows'] for x in a['cells'][key]),B_active_rows=sum(x['actual_rows'] for x in b['cells'][key]),
            A_context_upper=context_stats(a['contexts'][key]),B_context_upper=context_stats(b['contexts'][key])))
    denominator=sum(len(a['cells'][k]) for k in common)
    wa=sum(len(a['cells'][k])*statistics.mean(x['duration_us'] for x in a['cells'][k]) for k in common)/denominator if denominator else None
    wb=sum(len(a['cells'][k])*statistics.mean(x['duration_us'] for x in b['cells'][k]) for k in common)/denominator if denominator else None
    arms={}
    for label,item in [('A',a),('B',b)]:
        primary=sum(map(len,item['cells'].values()));covered=sum(len(item['cells'][k]) for k in common)
        profile_us=sum(us for _,_,us,phase in item['raw'] if phase=='profiling')
        tokens=item['clients']['committed_tokens_by_phase'].get('profiling',0)
        arms[label]=dict(exposure=item['exposure'],client=item['clients'],primary_calls=primary,common_calls=covered,
            common_coverage=covered/primary if primary else None,
            unmatched=[dict(stratum=k,statistics=stats([x['duration_us'] for x in v]),active_rows=sum(x['actual_rows'] for x in v),context_upper=context_stats(item['contexts'][k])) for k,v in item['cells'].items() if k not in common],
            chronological_10s_blocks=[dict(replica=k[0],rank=k[1],block=k[2],statistics=stats(v)) for k,v in sorted(item['blocks'].items())],
            profiling_gpu_sum_us_per_committed_token=profile_us/tokens if tokens else None,
            profiling_gpu_sum_us_by_rank={f'{r}:{k}':sum(us for rr,kk,us,phase in item['raw'] if (rr,kk)==(r,k) and phase=='profiling') for r in range(2) for k in range(4)},
            ratio_scope='sum across concurrent GPU real-proposal spans; excludes dummy EP support; not ITL',receipts=item['receipts'],client_raw_sha256=item['client_sha'])
    return dict(status='descriptive_complete' if common else 'no_common_primary_strata',run_id=a['run_id'],arms=arms,common_strata=rows,
        standardized=dict(A_weighted_mean_us=wa,B_A_weighted_mean_us=wb,delta_us=wa-wb if wa is not None else None,
            gain_percent=100*(wa-wb)/wa if wa else None,weight='A call counts in complete common stratum inventory'),
        inference='one fresh A/B start; descriptive, no service confidence interval, independent-call assumption or winning-cell gate')

def main():
    p=argparse.ArgumentParser();p.add_argument('--arm-a',type=Path,required=True);p.add_argument('--arm-b',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--launch-manifest',type=Path,required=True);a=p.parse_args()
    try:
        manifest=json.loads(a.manifest.read_text());observer_sha=next(v['sha256'] for v in manifest['files'] if v['destination'].endswith('/c25_live_observer.py'))
        aa=load_arm(a.arm_a,'A',observer_sha=observer_sha);bb=load_arm(a.arm_b,'B',aa['run_id'],observer_sha)
        validate_launch(aa,bb,json.loads(a.launch_manifest.read_text()));result=summarize(aa,bb);code=0
    except Exception as exc:result={'status':'incomplete','error':f'{type(exc).__name__}: {exc}'};code=2
    if a.output.exists():raise AssertionError('output exists')
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');raise SystemExit(code)
if __name__=='__main__':main()

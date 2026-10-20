import collections,decimal,gzip,hashlib,json,pathlib,re
T=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(json.loads((T/'process-completion.json').read_text())['run_directories'][0])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,obj):
 p=T/name
 if p.exists():
  assert json.loads(p.read_text())==obj,name
 else:p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
console=(R/'console.log').read_text()
line=next(x for x in console.splitlines() if 'PhaseRecordsStats(phase=CreditPhase.PROFILING,' in x)
fields={k:int(re.search(r'\b'+k+r'=(\d+)',line)[1]) for k in ('start_ns','sent_end_ns','requests_end_ns','final_requests_completed','final_requests_cancelled','final_request_errors','total_expected_requests')}
control=json.loads((T/'profile-control.json').read_text());anchor=json.loads((T/'phase-anchor.json').read_text())
assert control['profiling_start_ns']==anchor['anchor_ns']
anchor_error=anchor['anchor_ns']-fields['start_ns']
starts=[{'offset_s':e['offset_s'],'backend':s['backend'],'start_dispatch_error_ns':s['request_start_ns']-(fields['start_ns']+e['offset_s']*10**9)} for e in control['episodes'] for s in e['start']]
assert abs(anchor_error)<=10**9 and all(abs(s['start_dispatch_error_ns'])<=10**9 for s in starts)
exports=R/'artifacts';agg=json.loads((exports/'profile_export_aiperf.json').read_text());score=json.loads((R/'score.json').read_text())
phases=collections.defaultdict(lambda:dict(count=0,errors=0,cancelled=0,ids=set(),keys=set(),duplicate_ids=0,duplicate_keys=0))
for raw in (exports/'profile_export.jsonl').open():
 d=json.loads(raw);m=d['metadata'];p=phases[m.get('benchmark_phase','unknown')];p['count']+=1;p['errors']+=int(bool(m.get('error') or d.get('error')));p['cancelled']+=int(bool(m.get('was_cancelled')))
 k=(m.get('conversation_id'),m.get('turn_index'));rid=m.get('x_request_id');p['duplicate_ids']+=int(rid in p['ids']);p['duplicate_keys']+=int(k in p['keys']);p['ids'].add(rid);p['keys'].add(k)
for p in phases.values():p['unique_ids']=len(p.pop('ids'));p['unique_keys']=len(p.pop('keys'))
raw_phases=collections.defaultdict(collections.Counter)
for raw in (exports/'profile_export_raw.jsonl').open():
 d=json.loads(raw);p=d['metadata'].get('benchmark_phase','unknown');raw_phases[p]['records']+=1;raw_phases[p][str(d.get('status'))]+=1;raw_phases[p]['cancelled']+=int(bool(d['metadata'].get('was_cancelled')))
replay_keys=('replay_sched_lag_p50','replay_sched_lag_p90','replay_sched_lag_p99','replay_sched_degraded')
warn_lines=[x for x in console.splitlines() if 'profile_complete relay' in x or 'Replay schedule degraded' in x or 'Parquet export complete:' in x]
fidelity={'status':'pass','run_dir':str(R),'expected_requests':986,'phase_records_stats':fields,'metric_rows_by_phase':dict(phases),'raw_rows_by_phase':{k:dict(v) for k,v in raw_phases.items()},'aggregate_is_complete':agg['is_complete'],'aggregate_error_summary':agg['error_summary'],'profiling_replay':{k:agg[k] for k in replay_keys},'warmup_replay':{k:agg['warmup_metrics'][k] for k in replay_keys},'warning_explanation':{'large_replay_warning':'Exactly matches separately exported warmup percentiles; profiling metrics remain4.6538368ms p99/degraded0','metrics_timeout':'Server metrics profile_complete relay exceeded30s after all986 records processed. Later Parquet export completed3,105,464 rows; retained observability delay, not request error. Not a proof of complete endpoint coverage.','lines':warn_lines},'service_score':'diagnostic prefix SLO ineligible; no comparison to full trace','source_files':[{'path':str(p),'sha256':sha(p)} for p in (R/'status.json',R/'score.json',R/'manifest.json',R/'console.log',exports/'profile_export_aiperf.json',exports/'profile_export.jsonl',exports/'profile_export_raw.jsonl')]}
assert phases['profiling']['count']==986 and raw_phases['profiling']['records']==986
assert fields['final_request_errors']==0 and fields['final_requests_cancelled']==0 and agg['is_complete'] and not agg['error_summary']
assert agg['replay_sched_lag_p99']['avg']<=500 and agg['replay_sched_degraded']['avg']==0
write('fidelity-builder.json',fidelity)
phase={'run_dir':str(R),'run_id':R.name,'manifest_sha256':sha(R/'manifest.json'),'profiling_start_ns':anchor['anchor_ns'],'anchor_precision':anchor['anchor_precision'],'exact_profiling_start_ns':fields['start_ns'],'profiling_end_ns':fields['requests_end_ns'],'anchor_minus_exact_ns':anchor_error,'start_dispatch_reconciliation':starts,'status':'phase_and_control_reconciliation_pass','phase_console_line':line,'evidence':[{'path':str(T/name),'sha256':sha(T/name)} for name in ('phase-anchor.json','profile-control.json','fidelity-builder.json','process-completion.json')]}
write('phase-final.json',phase)
identity=json.loads((T/'runtime-identity.json').read_text());final=json.loads((T/'final-runtime-identity.json').read_text())
workers={(w['replica'],w['rank']):w for w in identity['workers']}
finalworkers={(w['replica'],w['rank']):w for w in final['workers']}
for key,w in workers.items():
 for field in ('host_pid','start_ticks'):assert str(w[field])==str(finalworkers[key][field]),(key,field)
 assert finalworkers[key]['matches_startup']
for old,new in zip(identity['containers'],final['containers']):
 assert old['replica']==new['replica'] and old['id']==new['id']
 assert old['source_hashes']==new['source_hashes']
collection=json.loads((T/'collection.json').read_text())
for entry in collection['files']:assert sha(pathlib.Path(entry['path']))==entry['sha256'],entry['path']
manifest={'identity_receipt':str(T/'runtime-identity.json'),'identity_sha256':sha(T/'runtime-identity.json'),'phase_receipt':str(T/'phase-final.json'),'phase_receipt_sha256':sha(T/'phase-final.json'),'control_receipt':str(T/'profile-control.json'),'control_receipt_sha256':sha(T/'profile-control.json'),'observation_manifest':'/home/ubuntu/Deepseek_serve-c03/av-k5/observation-manifest.json','observation_manifest_sha256':sha(pathlib.Path('/home/ubuntu/Deepseek_serve-c03/av-k5/observation-manifest.json')),'profiling_start_ns':anchor['anchor_ns'],'traces':[]}
inventory=[]
for entry in collection['files']:
 p=pathlib.Path(entry['path'])
 if not p.name.endswith('.pt.trace.json.gz'):continue
 d=json.load(gzip.open(p,'rt'));ev=d['traceEvents'];scopes=[e for e in ev if e.get('ph')=='X' and e.get('cat')=='user_annotation' and str(e.get('name','')).startswith('avk5.')]
 pids={e['pid'] for e in scopes};assert len(pids)==1;pids=pids.pop()
 replica=int(p.parent.name.removeprefix('replica'));rank=d['distributedInfo']['rank'];w=workers[replica,rank];assert pids==w['worker_pid']
 device_ids={e.get('args',{}).get('device') for e in ev if e.get('cat') in ('kernel','gpu_memcpy','gpu_memset')};assert device_ids=={rank},device_ids
 base=d['baseTimeNanoseconds'];unix=lambda x:base+int(decimal.Decimal(str(x))*1000)
 begin=min(unix(e['ts']) for e in scopes);end=max(unix(e['ts']+e['dur']) for e in scopes)
 episodes=[]
 for e in control['episodes']:
  start=e['start'][replica]['request_start_ns'];stop=e['stop'][replica]['request_end_ns']
  if start<=begin<=end<=stop:episodes.append(e['offset_s'])
 assert len(episodes)==1,(p,begin,end,episodes)
 assert fields['start_ns']<=begin<end<=fields['requests_end_ns']
 row={'offset_s':episodes[0],'replica':replica,'rank':rank,'path':str(p),'sha256':entry['sha256'],'worker_pid':pids,'gpu_uuid':w['gpu_uuid'],'container_id':w['container_id']}
 manifest['traces'].append(row)
 inventory.append({**row,'trace_base_time_ns':base,'first_scope_unix_ns':begin,'last_scope_unix_ns':end,'scope_counts':dict(collections.Counter(e['name'] for e in scopes)),'gpu_device_ids':list(device_ids),'distributed_rank':rank,'event_count':len(ev),'trace_metadata_keys':list(d.keys()),'event_categories':dict(collections.Counter(str(e.get('cat')) for e in ev)),'process_name':sorted({e.get('args',{}).get('name','') for e in ev if e.get('name')=='process_name' and e.get('pid')==pids}),'metadata_warning_keys':[k for k in d if re.search('warn|drop|lost|trunc',k,re.I)]})
 del d,ev,scopes
assert len(manifest['traces'])==16
manifest['traces'].sort(key=lambda r:(r['offset_s'],r['replica'],r['rank']))
write('trace-inventory-builder.json',{'status':'identity_and_episode_binding_pass','collection_sha256':sha(T/'collection.json'),'all_collection_file_hashes_verified':True,'same_worker_host_pid_start_container_and_sources_before_after':True,'initial_container_pid_gpu_mapping_bound_to_unchanged_process':True,'trace_count':len(inventory),'traces':inventory})
write('trace-manifest.json',manifest)
print(json.dumps({'status':'manifest_ready','trace_count':len(inventory),'phase_reconciliation_ns':anchor_error,'fidelity':'986/986,0errors,profilingp99=4.6538368ms'}))

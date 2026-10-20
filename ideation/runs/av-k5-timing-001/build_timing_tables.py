import collections,csv,datetime,hashlib,json,math,pathlib,statistics
T=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(json.loads((T/'process-completion.json').read_text())['run_directories'][0])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((T/'trace-summary-v2.json').read_text());rows=[]
for item in d['traces']:
 ident,s=item['identity'],item['summary'];cycles=s['complete_eligible_decode_cycles'];wall=sum(c['cycle_wall_span_us'] for c in cycles)
 row={k:ident[k] for k in ('offset_s','replica','rank','worker_pid','gpu_uuid')};row.update(complete_decode_cycles=len(cycles),native_execute_ranges=s['native_execute_range_count'],all_target_scopes=s['scope_counts'].get('avk5.target_forward',0),cycle_span_sum_us=wall)
 for key in ('target_union_us','draft_total_union_us','draft_execution_union_us','draft_outside_execution_union_us','target_draft_overlap_us','other_correlated_union_us','unattributed_union_us','all_activity_union_us','idle_without_observed_gpu_activity_us'):
  row['sum_'+key]=sum(c[key] for c in cycles)
 row['target_occupied_fraction']=row['sum_target_union_us']/wall if wall else None
 row['draft_occupied_fraction']=row['sum_draft_total_union_us']/wall if wall else None
 row['idle_fraction']=row['sum_idle_without_observed_gpu_activity_us']/wall if wall else None
 row['unattributed_fraction']=row['sum_unattributed_union_us']/wall if wall else None
 row['median_cycle_wall_us']=statistics.median(c['cycle_wall_span_us'] for c in cycles) if cycles else None
 row['adequacy_problems']=s['adequacy_problems'];row['cycle_exclusions']=s['cycle_exclusion_counts'];row['unclassified_reasons']=s['unclassified_reasons'];rows.append(row)
receipt={'status':'descriptive_only_full_required_adequacy_not_met','parser_sha256':d['source_sha256'],'summary_sha256':sha(T/'trace-summary-v2.json'),'definition':'Per rank/window sums of interval unions over finite nonoverlapping complete same-device cycles; no cross-device wall-time sum','required_cells':16,'cells_at_least10cycles':sum(r['complete_decode_cycles']>=10 for r in rows),'cells_without_parser_adequacy_problems':sum(not r['adequacy_problems'] for r in rows),'exposed_service_savings':'unknown','rows':rows}
(T/'timing-table.json').write_text(json.dumps(receipt,indent=2)+'\n')
with (T/'timing-table.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
phase=json.loads((T/'phase-final.json').read_text());start=phase['exact_profiling_start_ns'];control=json.loads((T/'profile-control.json').read_text())
windows=[(60,80),(110,130),(180,200),(230,250)]
context=[{'offsets_s':[a,b],'telemetry_rows':0,'times':[],'values':collections.defaultdict(list),'request_values':collections.defaultdict(list),'request_count':0,'control_or_export_overlap':[]} for a,b in windows]
for ctx,(a,b) in zip(context,windows):
 for episode in control['episodes']:
  for replica in (0,1):
   # Native trace processing/export can continue between start and stop response.
   x=(episode['start'][replica]['request_start_ns']-start)/1e9;y=(episode['stop'][replica]['request_end_ns']-start)/1e9
   if max(a,x)<min(b,y):ctx['control_or_export_overlap'].append({'episode_offset_s':episode['offset_s'],'replica':replica,'conservative_control_to_stop_response_overlap_s':min(b,y)-max(a,x),'scope':'May include export; not proof profiler continuously active'})
p=R/'telemetry/telemetry.jsonl';digest=hashlib.sha256()
with p.open('rb') as f:
 for raw in f:
  digest.update(raw);row=json.loads(raw);time=datetime.datetime.fromisoformat(row['timestamp']);ns=int(time.timestamp()*1e9);offset=(ns-start)/1e9
  for ctx,(a,b) in zip(context,windows):
   if not a<=offset<=b:continue
   ctx['telemetry_rows']+=1;ctx['times'].append(offset)
   for key,value in row.items():
    relevant=(key=='host.cpu_percent' or (key.startswith('gpu.') and key.endswith(('.sm_util_percent','.memory_util_percent','.hbm_used_bytes'))) or (key.startswith(('engine0.','engine1.')) and any(metric in key for metric in (':num_requests_running{',':num_requests_waiting{',':kv_cache_usage_perc{'))))
    if relevant and isinstance(value,(int,float)) and math.isfinite(value):ctx['values'][key].append(value)
for raw in (R/'artifacts/profile_export.jsonl').open():
 row=json.loads(raw);meta=row['metadata']
 if meta.get('benchmark_phase')!='profiling':continue
 offset=(meta['request_start_ns']-start)/1e9
 for ctx,(a,b) in zip(context,windows):
  if not a<=offset<=b:continue
  ctx['request_count']+=1
  for key in ('input_sequence_length','output_sequence_length','time_to_first_token','request_latency','inter_token_latency'):
   value=row.get('metrics',{}).get(key,{}).get('value')
   if isinstance(value,(int,float)) and math.isfinite(value):ctx['request_values'][key].append(value)
for ctx in context:
 times=ctx.pop('times');ctx['first_last_sample_offsets_s']=[min(times),max(times)] if times else None;ctx['max_sample_gap_s']=max((b-a for a,b in zip(times,times[1:])),default=None)
 ctx['sample_weighted_statistics']={k:{'finite_count':len(v),'min':min(v),'max':max(v),'sample_mean':statistics.mean(v)} for k,v in ctx.pop('values').items()}
 ctx['request_start_cohort_statistics']={k:{'count':len(v),'median':statistics.median(v),'mean':statistics.mean(v)} for k,v in ctx.pop('request_values').items()}
(T/'inactive-profile-bracket-context.json').write_text(json.dumps({'scope':'Predeclared intervals kept fixed; different traffic/cache states, not unbiased profiler overhead. Telemetry timestamps are collection-loop starts. Missing finite samples remain visible throughcounts.','telemetry_path':str(p),'telemetry_sha256':digest.hexdigest(),'phase_receipt_sha256':sha(T/'phase-final.json'),'windows':context},indent=2)+'\n')
print(json.dumps({'table_rows':len(rows),'qualified_parser_cells':receipt['cells_without_parser_adequacy_problems'],'windows':[{'offsets':c['offsets_s'],'rows':c['telemetry_rows'],'requests':c['request_count'],'overlap':c['control_or_export_overlap']} for c in context]}))

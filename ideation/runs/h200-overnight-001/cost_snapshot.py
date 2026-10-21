"""Report actual allocation cost; an active allocation is explicitly provisional."""
import datetime
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
now=datetime.datetime.now(datetime.timezone.utc)
rows=[]
for path in sorted(list((ROOT/'executions').glob('*/execution.json'))+list((ROOT/'native-executions').glob('*/execution.json'))+list((ROOT/'live-executions').glob('*/execution.json'))):
    value=json.loads(path.read_text());active=value.get('state')=='running'
    wall=(now-datetime.datetime.fromisoformat(value['started_at_utc'])).total_seconds() if active else value['wall_seconds']
    count=value['allocated_gpus'];rows.append({'id':path.parent.name,'receipt':str(path.relative_to(ROOT)),'state':value['state'],'provisional':active,'wall_seconds':wall,'visible_GPU_hours':wall*count/3600,'eight_GPU_exclusive_node_equivalent_hours':wall*8/3600,'full_service_attempts_consumed':value['service_attempts_consumed']})
result={'time_utc':now.isoformat(),'allocations':rows,'provisional':any(x['provisional'] for x in rows),'total_visible_GPU_hours':sum(x['visible_GPU_hours'] for x in rows),'total_eight_GPU_node_equivalent_hours':sum(x['eight_GPU_exclusive_node_equivalent_hours'] for x in rows),'full_service_attempts_consumed':sum(x['full_service_attempts_consumed'] for x in rows),'dollar_cost':None,'note':'Includes startup, measurement, failed setup and cleanup; native shared allocation also includes bounded review wait. Per-GPU/node price is unknown. Exclusive-node equivalent is shown separately for one-GPU components. Engineering person-hours are not inferred from agent count.'}
(ROOT/'cost-current.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

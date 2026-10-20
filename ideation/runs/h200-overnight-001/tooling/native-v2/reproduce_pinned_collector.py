"""Execute the exact-image collector with explicit timestamp inputs on CPU."""
import hashlib
import importlib.util
import json
from pathlib import Path
from prometheus_client.metrics_core import Metric
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[1]/'native-root/metrics-repair-source/prometheus_client/multiprocess.py'
spec=importlib.util.spec_from_file_location('prometheus_client._c25_pinned_multiprocess',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def samples(timestamps):
    metric=Metric('fixture','CPU fixture','gauge');metric._multiprocess_mode='mostrecent'
    for rank,stamp in enumerate(timestamps):
        metric.add_sample('fixture',(('engine',str(rank)),('pid','1')),0,timestamp=stamp)
    result=list(module.MultiProcessCollector._accumulate_metrics({'fixture':metric},True))[0]
    return [dict(labels=s.labels,value=s.value) for s in result.samples]
before=samples([0,0,0,0]);rank0=samples([100,0,0,0]);allranks=samples([100,100,100,100])
assert before==[] and len(rank0)==1 and len(allranks)==4
print(json.dumps(dict(status='passed',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    before_set=before,after_rank0_set=rank0,after_all_set=allranks,
    scope='exact-image _accumulate_metrics code, CPU-only constructed samples; not service drain proof'),indent=2))

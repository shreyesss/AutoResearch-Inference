"""CPU-only exact mostrecent gauge failure; no server or request mutation."""
import json
import os
from pathlib import Path
import tempfile
# Configure before importing prometheus_client so its multiprocess ValueClass is used.
with tempfile.TemporaryDirectory() as directory:
    os.environ['PROMETHEUS_MULTIPROC_DIR']=directory
    from prometheus_client import Gauge,Counter,CollectorRegistry,generate_latest,multiprocess
    import prometheus_client.metrics,prometheus_client.values
    gauge=Gauge('vllm:num_requests_running','fixture',['model_name','engine'],multiprocess_mode='mostrecent')
    counter=Counter('vllm:request_success','fixture',['model_name','engine','finished_reason'])
    for rank in range(4):
        gauge.labels('deepseek-v4.1-flash',str(rank))
        counter.labels('deepseek-v4.1-flash',str(rank),'length')
    def collect():
        registry=CollectorRegistry();multiprocess.MultiProcessCollector(registry)
        return generate_latest(registry).decode()
    before=collect();gauge.labels('deepseek-v4.1-flash','0').set(0);rank0=collect()
    for rank in range(1,4):gauge.labels('deepseek-v4.1-flash',str(rank)).set(0)
    allranks=collect()
    def lines(value):return [x for x in value.splitlines() if x.startswith('vllm:num_requests_running{')]
    assert len(lines(before))==0 and len(lines(rank0))==1 and len(lines(allranks))==4
    import hashlib
    print(json.dumps(dict(status='passed',scope='CPU-only prometheus mechanics; not a service drain',
        sources={str(Path(m.__file__)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (multiprocess,prometheus_client.metrics,prometheus_client.values)},
        initial_gauges=lines(before),after_only_rank0_set=lines(rank0),after_all_actual_sets=lines(allranks)),indent=2))

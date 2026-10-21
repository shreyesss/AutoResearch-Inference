"""Root-only single idle GPU engineering preflight; no model/service imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import torch
from c25_live_observer import CAPACITY, EventPool, atomic
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists(), "refusing to overwrite preflight"
started=time.monotonic()
assert torch.cuda.device_count()==1
pool=EventPool()
for begin,end in pool.pairs:
    begin.record(pool.stream);end.record(pool.stream)
values,seconds=pool.resolve(range(CAPACITY))
assert len(values)==CAPACITY and all(math.isfinite(v) and v>=0 for v in values)
atomic(a.output,dict(status='passed',capacity=CAPACITY,initialization=pool.initialization,
    flush_seconds=seconds,total_seconds=time.monotonic()-started,
    rss_max_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    cuda_memory_allocated=torch.cuda.memory_allocated(),cuda_memory_reserved=torch.cuda.memory_reserved(),
    gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),minimum_us=min(values),maximum_us=max(values),
    helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    observer_sha256=hashlib.sha256(Path(__file__).with_name('c25_live_observer.py').read_bytes()).hexdigest()))

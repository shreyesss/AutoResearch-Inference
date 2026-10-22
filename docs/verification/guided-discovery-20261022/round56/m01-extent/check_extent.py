"""Integer extent invariant; no kernel execution or latency model."""
import json

def extent_by_tasks(n, block_m):
    return sum(((min(block_m,n-start)+15)//16)*16 for start in range(0,n,block_m))

cases=0
for block_m in range(16,257,16):
    for n in range(0,4097):
        got=extent_by_tasks(n,block_m)
        expected=((n+15)//16)*16
        assert got==expected,(n,block_m,got,expected)
        cases+=1
print(json.dumps({"cases":cases,"m_domain":[0,4096],"block_m_domain":"multiples16 in16..256, mathematical domain not all asserted legal target tactics","identity":"sum_chunk align(valid_m,16) = align(n,16)","native_or_gpu_execution":False,"performance_evidence":False},indent=2))

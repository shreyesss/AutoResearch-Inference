"""Symbolic row identities/counts only; no tensors, GEMM or runtime execution."""
from pathlib import Path
import json

def indices(requests):
 out=[];offset=0
 for start,slots in requests:
  for j,slot in enumerate(slots):
   if slot>=0 and (start+j+1)%2==0:out.append(offset+j)
  offset+=len(slots)
 return out
cases=[('even_prefill',[(0,list(range(8)))]),('odd_prefill',[(1,list(range(7)))]),('ragged_two_boundary_singletons',[(1,[8]),(7,[11])]),('ragged_mixed',[(0,[1,2,3]),(3,[4,5,6])]),('padding',[(1,[-1,8,-1,10])]),('empty_and_single',[(0,[]),(0,[9])]),('verify_six',[(20,list(range(6)))]),('verify_five_odd',[(21,list(range(5)))])]
rows=[]
for name,reqs in cases:
 active=indices(reqs);N=sum(len(slots)for _,slots in reqs);capacity=sum((len(slots)+1)//2 for _,slots in reqs)
 assert len(active)<=capacity<=N
 mapping={packed:original for packed,original in enumerate(active)}
 assert list(mapping.values())==active and len(set(mapping.values()))==len(active)
 rows.append({'name':name,'requests':reqs,'active_original_rows':active,'N':N,'per_request_parity_unknown_capacity':capacity,'baseline_MACs_per_owner':N*512*128,'ideal_active_MACs_per_owner':len(active)*512*128,'scope':'row-count arithmetic; no native arithmetic or latency'})
neg=[{'name':'global_odd_stride','requests':[(1,[8]),(7,[11])],'required':indices([(1,[8]),(7,[11])]),'naive':[1]}, {'name':'start_parity_ignored','requests':[(1,[1,2,3])],'required':indices([(1,[1,2,3])]),'naive':[1]}]
assert all(x['required']!=x['naive']for x in neg)
# A one-token-per-request fixed capacity does not shrink merely because half current positions are boundaries.
assert sum((1+1)//2 for _ in range(64))==64
Path(__file__).with_suffix('.json').write_text(json.dumps({'scope':'symbolic source predicate, not executed source/native kernel','cases':rows,'negative_controls':neg,'single_token_decode_fixed_capacity_rows':64,'single_token_decode_input_rows':64},indent=2))

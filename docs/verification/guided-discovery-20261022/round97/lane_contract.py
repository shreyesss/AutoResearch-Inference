"""Pure symbolic lane/dataflow check, not native FP32 Sinkhorn execution."""
from pathlib import Path
import json,struct,itertools
B=Path(__file__).parent
def add(a,b):return ('+',a,b)
def canonical(t):
 if isinstance(t,str):return t
 a,b=canonical(t[1]),canonical(t[2]);return ('+',*sorted((a,b),key=repr))
def xor_reduce(values,masks):
 for mask in masks:values={i:add(v,values[i^mask]) for i,v in values.items()}
 return values
values={i:f'x{(i-8)//4}{(i-8)%4}' if 8<=i<24 else f'inactive{i}' for i in range(32)}
rows=xor_reduce(values,[2,1]);cols=xor_reduce(values,[4,24]); checks=[]
for r in range(4):
 for c in range(4):
  lane=8+4*r+c
  nr=add(add(f'x{r}0',f'x{r}2'),add(f'x{r}1',f'x{r}3'))
  nc=add(add(f'x0{c}',f'x1{c}'),add(f'x2{c}',f'x3{c}'))
  checks.append({'row':r,'column':c,'old_lane':lane,'new_store_lane':r//2,'new_register':(r%2)*4+c,'row_pairing_equal_mod_commutation':canonical(rows[lane])==canonical(nr),'column_pairing_equal_mod_commutation':canonical(cols[lane])==canonical(nc)})
assert all(c['row_pairing_equal_mod_commutation'] and c['column_pairing_equal_mod_commutation'] for c in checks)
assert len({(c['new_store_lane'],c['new_register']) for c in checks})==16
f=lambda x:struct.unpack('f',struct.pack('f',x))[0]
negative=None
for x in itertools.product([1.,2**-23,2**-24,2**-25],repeat=4):
 target=f(f(x[0]+x[2])+f(x[1]+x[3]));wrong=f(f(x[0]+x[1])+f(x[2]+x[3]))
 if target!=wrong:negative={'values':x,'xor2_then1':target,'adjacent_pairs':wrong};break
assert negative
out={'scope':'Source-derived symbolic grouping and destination bijection only. Commutative canonicalization excludes exceptional NaN/signed-zero semantics and does not model exp, reciprocal, FMA, compiler or device execution.','checks':checks,'positive_binary32_reassociation_negative':negative,'iterations_changed':False,'launches_removed':0}
(B/'lane_contract.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'positions':len(checks),'all_pass':True,'reassociation_negative':negative}))

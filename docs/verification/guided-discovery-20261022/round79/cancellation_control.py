"""Finite rational representation control, not execution of any GPU code."""
from fractions import Fraction as F
from pathlib import Path
import json

def pow2(e):
    return F(2)**e

def representable():
    vals=[]
    for code in range(127):
        exp,mant=divmod(code,8)
        value=F(mant)*pow2(-9) if exp==0 else (1+F(mant,8))*pow2(exp-7)
        vals.append((value,code))
    return vals

values=representable()
def e4m3_rne(x):
    sign=-1 if x<0 else 1
    x=abs(x)
    v,c=min(values,key=lambda vc:(abs(x-vc[0]),vc[1]%2))
    return sign*v

def group_quant(group):
    amax=max(map(abs,group)); sf=F(1)
    if amax==0:return [F(0)]*len(group),F(0)
    needed=amax/F(448)
    while sf<needed:sf*=2
    while sf/2>=needed:sf/=2
    return [e4m3_rne(x/sf)*sf for x in group],sf

# All inputs are exactly representable BF16 values. Not sampled target activations.
first=[F(129,128)]+[F(1)]*127
second=[F(-1)]*128
q1,s1=group_quant(first);q2,s2=group_quant(second)
baseline=first[0]+second[0]
changed=q1[0]+q2[0]
assert s1==s2==F(1,256)
assert baseline==F(1,128) and changed==0
result={
 'scope':'One deliberately selected finite cancellation counterexample using ideal E4M3 RNE and group128 power-of-two scales. Not CUDA execution, target observation, full floating-point emulation, or quality prevalence.',
 'baseline_BF16_partial_values':[str(first[0]),str(second[0])],
 'group_scales':[str(s1),str(s2)],
 'dequantized_partial_values':[str(q1[0]),str(q2[0])],
 'FP32_sum_then_BF16_baseline':str(baseline),
 'FP32_sum_then_BF16_changed':str(changed),
 'conclusion':'Both final sums are exactly BF16 representable and differ; output FP8 transport is not lossless merely because accumulation remains FP32.',
 'logical_payload_per_H5120_partial':{'BF16_bytes':10240,'E4M3_value_bytes':5120,'UE8M0_scale_bytes':40,'total_FP8_bytes':5160,'scope':'Payload only; excludes allocation padding, transactions, signaling, routing fractions and encode/decode cost. Not measured link traffic or latency.'}}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')

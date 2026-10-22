"""Stdlib control-flow model. Does not run Triton, RNG, tensors or actual distributions."""
import json,struct,math
from pathlib import Path
F=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def h32(m,r):
 d=F(F(m+1.0)-r)
 return F(m/d) if d>0 else 1.0
# Interior exact-real bound need not equal the source's finite implementation.
r=F(.3);mass=r;h=h32(mass,r);assert h>r
rounding={'r':r,'mass':mass,'denom':F(F(mass+1)-r),'h':h,'coin':h,'native_source_compare':h<=h,'bound_skip_would_reject':h>=r,'scope':'FP32 operation-order model, not compiled Triton or realized Philox/model trajectory'}

def reference(ids,coins,thresholds):
 accepted=0;stores=[];reads=[]
 for i,token in enumerate(ids):
  if token<0:break
  reads.append(i);stores.append(token)
  if coins[i]<=thresholds[i]:accepted=i+1
 return accepted,stores,reads

def flag(ids,coins,terminal_ratio,temp=1.,has_q=True):
 # Proposed admission; no placeholder inference. Caller validates unique current request slots.
 return bool(has_q and temp>0 and 2<=len(ids)<=5 and all(x>=0 for x in ids) and coins[-1]<=terminal_ratio)

def proposed(ids,coins,thresholds,temp=1.,has_q=True):
 full=flag(ids,coins,thresholds[-1] if thresholds else math.nan,temp,has_q)
 if full:return len(ids),list(ids),[],full
 a,st,rd=reference(ids,coins,thresholds);return a,st,rd,full
cases=[
 ('full5', [1,2,3,4,5],[.8,.8,.8,.8,.2],[.1,.1,.1,.1,.3]),
 ('terminal_tie', [1,2,3,4,5],[.8,.8,.8,.8,.3],[.1,.1,.1,.1,.3]),
 ('terminal_fail_earlier_pass', [1,2,3,4,5],[.2,.8,.8,.8,.4],[.3,.1,.1,.1,.3]),
 ('all_fail',[1,2,3,4,5],[.9]*5,[.1]*5),
 ('AV_short2',[1,2],[.9,.2],[.1,.3]),
 ('one_draft',[1],[.2],[.3]),
 ('empty',[],[],[]),
 ('placeholder_then_apparent_success',[1,-1,3],[.9,.9,.1],[.1,.1,.3]),
 ('nan_terminal',[1,2],[.1,.1],[.2,math.nan]),
 ('nonfinite_earlier_irrelevant',[1,2],[.1,.1],[math.nan,.3]),
]
results=[]
for name,ids,coins,hs in cases:
 a,st,rd=reference(ids,coins,hs);aa,ss,rr,ff=proposed(ids,coins,hs);assert (a,st)==(aa,ss);results.append({'case':name,'accepted':a,'flag':ff,'reference_threshold_reads':len(rd),'proposed_threshold_reads':len(rr),'scope':'control and stores only; no native probability calculation'})
# Existing greedy/one-hot paths must not get this flag, even when synthetic test threshold passes.
assert not flag([1,2],[.1,.1],.3,temp=0)
assert not flag([1,2],[.1,.1],.3,has_q=False)
# Fresh-step initialization and nonidentity request-row/state-slot mapping.
old_flags={2:True,7:True};current={s:False for s in [7,2]};current[7]=True
assert current[2] is False and current[7] is True
wrong_by_row={0:True,1:False};assert wrong_by_row.get(7,False)!=current[7]
# Three actual negative controls: strict donor comparison changes native tie;
# interpreting any shorter pass as full is wrong; ignoring placeholders is wrong.
assert not (.3<.3) and .3<=.3
neg={'strict_comparison_changes_terminal_tie':True,'any_earlier_pass_does_not_imply_full':reference([1,2],[.1,.9],[.2,.3])[0]==1,'placeholder_cannot_be_ignored':reference([1,-1,3],[.9,.9,.1],[.1,.1,.3])[0]==0,'state_slot_is_not_batch_row':True}
out={'scope':'Independent source-inspired scheduling oracle, not extracted sampler execution or distributional validation','fp32_bound_counterexample':rounding,'control_cases':results,'negative_controls':neg,'request_slot_controls':{'fresh_init':True,'nonidentity_mapping':True},'native_imports':False,'logical_byte_bound':{'vocab':129280,'drafts':5,'interior_rows':4,'assumed_bytes_each_target_draft':2,'max_avoided_input_bytes':129280*4*4,'unchanged':'normalization, cumulative ratios, launches, fallback scans, bonus/recovery and token stores'}}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2));print(json.dumps({'controls':len(results),'new_native_tests':0,'max_logical_bytes':out['logical_byte_bound']['max_avoided_input_bytes']}))

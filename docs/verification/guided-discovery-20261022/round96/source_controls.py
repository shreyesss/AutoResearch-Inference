"""Source/stdlib controls only: no runtime import, GEMM or timing."""
from pathlib import Path
from fractions import Fraction
import ast,json,struct
b=Path(__file__).parent
s=(b/'sources/vllm__models__deepseek_v41__common__ops__fused_compress_quant_cache.py').read_text();tree=ast.parse(s)
f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_fused_save_compress_norm_kernel')
hooks=[x.lineno for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_store_latent'];assert len(hooks)==2
store=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_store_latent');assert 'normed.to(tl.bfloat16)' in ast.get_source_segment(s,store)
# Exact dyadic illustration, embedded in two coordinates of a512-wide vector.
# These are not measured normalized target activations.
x0=Fraction(1)+Fraction(1,512);x1=Fraction(1);w=Fraction(256)
# BF16 ULP at1 is1/128; x0 is closer to1 than to1+1/128.
assert x0-1 < Fraction(1,256)
reference=w*Fraction(1)-w*x1
skip_input_round=w*x0-w*x1
assert reference==0 and skip_input_round==Fraction(1,2)
# Idealized no-contention schedule; arbitrary work units are NOT microseconds.
cases=[]
for name,Q,C,K,J,I,Kf in [('move_delays_main_insert',0,1,1,0,10,1),('move_hidden_by_query',10,1,1,1,1,1),('slower_fused_scalar_work',1,1,1,1,1,4)]:
 old=max(Q,C)+max(K+J,I);new=max(Q,C+Kf)+max(J,I)
 cases.append(dict(name=name,Q=Q,C=C,K=K,J=J,I=I,Kf=Kf,current=old,fused=new,delta=new-old))
assert cases[0]['delta']>0 and cases[1]['delta']<0 and cases[2]['delta']>0
out={'scope':__doc__,'producer_store_hook_source_lines':sorted(hooks),'bf16_input_boundary':{'reference':str(reference),'incorrect_unrounded':str(skip_input_round),'scope':'Exact dyadic scalar negative control, not observed activation or native GEMM parity.'},'schedule_cases':cases,'schedule_scope':'Two-stage source dependency model only; no contention/cache/launch time modeled. K includes current GEMM only; J includes remaining K-store and index-Q work. Fused arm retains K-store.','per_valid_row_projection_MACs':512*128,'per_program_logical_weight_operands_bytes':512*128*2,'scope_weight_bytes':'Operand enumeration, not measured HBM. Inter-CTA L2 and batched baseline reuse unknown.'}
(b/'source_controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

"""Exact real two-token source-equation discriminator. No native execution."""
from fractions import Fraction as F
from pathlib import Path
import json,itertools
p=(F(4,5),F(1,5));q=(F(1,2),F(1,2));pc=(F(1,2),F(1,2));qc=(F(9,10),F(1,10))
block=F(0);seq=F(0);rows=[]
for a,b in itertools.product(range(2),repeat=2):
 mass=q[a]*qc[b];r1=min(p[a]/q[a],F(1));r2=min(r1*pc[b]/qc[b],F(1))
 residual=sum(max(r1*pv-qv,F(0)) for pv,qv in zip(pc,qc));denom=residual+1-r1
 h1=residual/denom if denom>0 else F(1)
 block_l2=r2;block_l1=(1-r2)*h1
 block_e=2*block_l2+block_l1
 seq_e=r1*(1+min(pc[b]/qc[b],F(1)))
 block+=mass*block_e;seq+=mass*seq_e
 rows.append({k:str(v) for k,v in {'first_token':a,'second_token':b,'draft_path_mass':mass,'clipped_joint_ratio_1':r1,'clipped_joint_ratio_2':r2,'next_residual_mass':residual,'block_first_threshold':h1,'block_expected_accepted_given_draft':block_e,'sequential_expected_accepted_given_draft':seq_e}.items()})
assert block==F(23,20) and seq==F(28,25) and block-seq==F(3,100)
# At path(1,1), threshold1=1/7 can fail, but threshold2=1 selects length2.
assert rows[3]['block_first_threshold']=='1/7' and rows[3]['clipped_joint_ratio_2']=='1'
out={'p_root':list(map(str,p)),'q_root':list(map(str,q)),'p_child_both_parents':list(map(str,pc)),'q_child_both_parents':list(map(str,qc)),'rows':rows,'block_expected_accepted':str(block),'ordinary_sequential_expected_accepted':str(seq),'difference':str(block-seq),'scope':'Source-equation rational arithmetic for one fixed two-token block, no EOS within that block and independent ideal verifier uniforms. Not EDR full-horizon reproduction, native floating-point/RNG test, DSpark data, AV simulation, or speed forecast. Shows ordinary stop-on-first-rejection and native block rules need different transition models.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'block':str(block),'sequential':str(seq),'different':True}))

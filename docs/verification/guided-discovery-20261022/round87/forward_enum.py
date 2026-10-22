"""Complete rational fixed-B block-sampler law; no native imports.

No EOS. Each round samples B draft tokens, applies the source block rule,
commits accepted prefix plus correction/bonus, then applies a fixed output cap.
Ideal independent verifier uniforms are analytically integrated. Native RNG,
floating arithmetic, AV, and GPU execution are outside this model.
"""
from fractions import Fraction as F
from functools import lru_cache
from collections import defaultdict
from itertools import product
from pathlib import Path
import json,hashlib
V=('a','b')

def model(variant,mode):
 def p(prefix):
  base=F((7,3,6,4,8)[len(prefix)%5],10)
  if 'b' in prefix and mode in ('p','both'):
   base=F(1+(len(prefix)*3+prefix.count('b')+variant*2)%9,10)
  return {'a':base,'b':1-base}
 def q(anchor,prefix):
  base=F(2+(anchor*3+len(prefix)*2)%7,10)
  if 'b' in prefix and mode in ('q','both'):
   base=F(1+(anchor*2+len(prefix)*4+prefix.count('b')*2+variant*3)%9,10)
  return {'a':base,'b':1-base}
 return p,q

def round_law(prefix,B,p,q):
 n=len(prefix);out=defaultdict(F)
 for draft in product(V,repeat=B):
  mass=F(1);rs=[F(1)];hs=[]
  for i,y in enumerate(draft):
   ctx=prefix+draft[:i];py=p(ctx);qy=q(n,ctx)
   if not qy[y]:mass=F(0);break
   mass*=qy[y]
   rs.append(min(rs[-1]*py[y]/qy[y],F(1)))
  if not mass:continue
  for i in range(B):
   if i==B-1:h=rs[i+1]
   else:
    ctx=prefix+draft[:i+1];pn=p(ctx);qn=q(n,ctx)
    residual=sum(max(rs[i+1]*pn[v]-qn[v],F(0)) for v in V)
    den=residual+1-rs[i+1];h=residual/den if den else F(1)
   assert 0<=h<=1;hs.append(h)
  # L is the greatest passing threshold; all later thresholds must fail.
  suffix_fail=F(1);lengths={}
  for tau in range(B,0,-1):
   lengths[tau]=hs[tau-1]*suffix_fail;suffix_fail*=1-hs[tau-1]
  lengths[0]=suffix_fail;assert sum(lengths.values())==1
  for tau,lp in lengths.items():
   if not lp:continue
   ctx=prefix+draft[:tau];pt=p(ctx)
   if tau==B:tokenlaw=pt
   else:
    qt=q(n,ctx);res={v:max(rs[tau]*pt[v]-qt[v],F(0)) for v in V};z=sum(res.values())
    assert z>0,(prefix,draft,tau,rs,hs,lengths)
    tokenlaw={v:r/z for v,r in res.items()}
   for v,tp in tokenlaw.items():
    if tp:out[(ctx+(v,),tau)]+=mass*lp*tp
 assert sum(out.values())==1
 return out

def full_law(N,B,p,q):
 @lru_cache(None)
 def go(prefix):
  if len(prefix)>=N:return {(prefix[:N],0):F(1)}
  out=defaultdict(F)
  for (committed,tau),mass in round_law(prefix,B,p,q).items():
   for (sequence,rounds),future in go(committed[:N]).items():out[(sequence,rounds+1)]+=mass*future
  return dict(out)
 result=go(());assert sum(result.values())==1
 for seq in product(V,repeat=N):
  observed=sum(v for (s,r),v in result.items() if s==seq);target=F(1)
  for i,y in enumerate(seq):target*=p(seq[:i])[y]
  assert observed==target,(N,B,seq,observed,target)
 return result

def retained_inputs(N,B,p,q):
 # Stronger than required: all-a target distributions held fixed beyond cap.
 rows={'p':[],'q':[]}
 for t in range(N+B+1):rows['p'].append({'prefix':'a'*t,'distribution':{k:str(v) for k,v in p(('a',)*t).items()}})
 for n in range(N):
  for t in range(n,n+B):rows['q'].append({'anchor':n,'prefix':'a'*t,'distribution':{k:str(v) for k,v in q(n,('a',)*t).items()}})
 return rows

def trajectory_posterior(sequence,B,p,q):
 """Candidate block-specific reduction; independent of round_law enumeration."""
 N=len(sequence)
 @lru_cache(None)
 def suffix(n):
  if n==N:return {0:F(1)}
  remaining=N-n;out=defaultdict(F);P=F(1);Q=F(1);survival=F(1)
  for k in range(1,min(B+1,remaining)+1):
   if k==remaining or k==B+1:
    boundary=survival
   else:
    token=sequence[n+k-1];prefix=sequence[:n+k-1]
    P*=p(prefix)[token];Q*=q(n,prefix)[token]
    next_survival=min(survival,Q/P);boundary=survival-next_survival;survival=next_survival
   for rounds,prob in suffix(n+k).items():out[rounds+1]+=boundary*prob
  assert sum(out.values())==1
  return dict(out)
 return suffix(0)

def occupancy_mean(sequence,B,p,q):
 """EDR-style forward occupancy with block posterior hazards, cap terminal."""
 N=len(sequence);survivals={}
 for n in range(N):
  P=Q=F(1);row=[F(1)]
  for j in range(1,min(B,N-n)+1):
   prefix=sequence[:n+j-1];v=sequence[n+j-1]
   P*=p(prefix)[v];Q*=q(n,prefix)[v];row.append(min(row[-1],Q/P))
  survivals[n]=row
 occ={0:F(1)};rounds=F(1)
 for t in range(N-1):
  nxt=defaultdict(F)
  for n,w in occ.items():
   j=t-n+1
   if j>B:h=F(0)
   else:
    prev=survivals[n][j-1]
    if not prev:assert not w
    h=survivals[n][j]/prev if prev else F(0)
   nxt[n]+=w*h;nxt[t+1]+=w*(1-h)
  rounds+=nxt[t+1];occ=dict(nxt);assert sum(occ.values())==1
 return rounds

def analyze(N,B,variant,mode):
 p,q=model(variant,mode);inputs=retained_inputs(N,B,p,q);law=full_law(N,B,p,q);x=('a',)*N
 formula_checks=0
 for seq in product(V,repeat=N):
  jm={r:sum(v for (ss,k),v in law.items() if ss==seq and k==r) for r in range(1,N+1)};zm=sum(jm.values())
  formula=trajectory_posterior(seq,B,p,q)
  assert all(jm[r]/zm==formula.get(r,F(0)) for r in jm),(N,B,variant,mode,seq,jm,formula)
  assert occupancy_mean(seq,B,p,q)==sum(F(r)*prob for r,prob in formula.items())
  formula_checks+=1
 joint={str(r):sum(v for (seq,k),v in law.items() if seq==x and k==r) for r in range(1,N+1)};prob=sum(joint.values());posterior={k:v/prob for k,v in joint.items()};expected=sum(F(int(k))*v for k,v in posterior.items())
 return {'N':N,'B':B,'variant':variant,'off_path_change':mode,'retained_input_sha256':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),'retained_inputs':inputs,'selected_output':''.join(x),'selected_output_probability':str(prob),'posterior_round_count':{k:str(v) for k,v in posterior.items()},'expected_rounds_given_output':str(expected),'joint_outcomes':len(law),'trajectory_formula_checks':formula_checks,'all_output_target_law_checked':True,'off_path_example':{'prefix':'b','p':{k:str(v) for k,v in p(('b',)).items()},'q_anchor0':{k:str(v) for k,v in q(0,('b',)).items()}}}

def zero_support_controls():
 cases=[]
 specs=[('disjoint deterministic',lambda pre:{'a':F(1),'b':F(0)},lambda n,pre:{'a':F(0),'b':F(1)}),
        ('zero proposal on target support',lambda pre:{'a':F(1,2),'b':F(1,2)},lambda n,pre:{'a':F(1),'b':F(0)}),
        ('identical deterministic',lambda pre:{'a':F(1),'b':F(0)},lambda n,pre:{'a':F(1),'b':F(0)})]
 for name,p,q in specs:
  for B in (1,2,3):
   law=full_law(3,B,p,q);checked=0;excluded=0
   for seq in product(V,repeat=3):
    joint={r:sum(v for (ss,k),v in law.items() if ss==seq and k==r) for r in (1,2,3)};prob=sum(joint.values())
    if not prob:excluded+=1;continue
    formula=trajectory_posterior(seq,B,p,q)
    assert all(joint[r]/prob==formula.get(r,F(0)) for r in joint)
    assert occupancy_mean(seq,B,p,q)==sum(F(r)*v for r,v in formula.items())
    checked+=1
   cases.append({'case':name,'B':B,'positive_target_outputs_checked':checked,'zero_target_outputs_not_conditioned':excluded})
 # A zero-survival state is unreachable. A finite harmless hazard may be set
 # to zero there; never divide zero by zero or infer an occupied transition.
 survival=[F(1),F(0),F(0)];hazards=[survival[j]/survival[j-1] if survival[j-1] else F(0) for j in (1,2)]
 assert hazards==[0,0]
 return {'cases':cases,'zero_occupancy_hazard_control':list(map(str,hazards)),'scope':'Exact finite support controls only; no native log(0), NaN or RNG validation.'}

def main():
 rows=[];comparisons=[]
 for N,B in [(3,1),(3,2),(4,2),(4,3)]:
  base=analyze(N,B,0,'none');rows.append(base)
  for mode,variant in [('p',1),('q',1),('both',1),('both',2)]:
   r=analyze(N,B,variant,mode);assert r['retained_input_sha256']==base['retained_input_sha256'];rows.append(r)
   comparisons.append({'N':N,'B':B,'mode':mode,'variant':variant,'all_retained_inputs_identical':True,'output_probability_identical':r['selected_output_probability']==base['selected_output_probability'],'posterior_identical':r['posterior_round_count']==base['posterior_round_count'],'mean_identical':r['expected_rounds_given_output']==base['expected_rounds_given_output']})
 out={'scope':__doc__,'model_count':len(rows),'matched_comparisons':len(comparisons),'trajectory_formula_comparisons':sum(r['trajectory_formula_checks'] for r in rows),'posterior_counterexamples':sum(not x['posterior_identical'] for x in comparisons),'comparisons':comparisons,'models':rows,'zero_support_controls':zero_support_controls()}
 Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('model_count','matched_comparisons','posterior_counterexamples','trajectory_formula_comparisons')}))
if __name__=='__main__':main()

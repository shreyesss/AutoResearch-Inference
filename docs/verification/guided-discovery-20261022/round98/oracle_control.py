"""Finite ternary pathwise common-tape control, not native or continuous-law proof."""
from pathlib import Path
from fractions import Fraction as F
import json,random
b=Path(__file__).parent
rng=random.Random(9801)
def normalize(v):
 s=sum(v);return tuple(F(x,s) for x in v)
def target(prefix):
 n=len(prefix);h=sum((i+1)*(x+1) for i,x in enumerate(prefix))
 return normalize((1+(h+n)%5,1+(2*h+n)%7,1+(h+3*n)%4))
def draft(prefix,anchor,step):
 h=sum(prefix);return normalize((1+(h+anchor)%6,1+(h+step)%5,1+(3*h+step)%7))
def sample(p,noise):return min(range(3),key=lambda i:(noise[i]/p[i],i))
def reference(tape,L):
 p=[]
 while len(p)<L:p.append(sample(target(p),tape[len(p)]))
 return p
def speculative(tape,L,policy):
 committed=[];rounds=0;matches=0;budget_trace=[]
 while len(committed)<L:
  anchor=len(committed);candidate=committed.copy();proposals=[];contexts=[candidate.copy()]
  for step in range(min(5,L-anchor)):
   t=sample(draft(candidate,anchor,step),tape[len(candidate)]);proposals.append(t);candidate.append(t);contexts.append(candidate.copy())
  # Deliberately inspect future proposals and future tape. No claim native AV does this.
  n=len(proposals)
  # Batched target evaluation uses proposed contexts, including incorrect descendants.
  target_samples=[sample(target(c),tape[anchor+j]) for j,c in enumerate(contexts) if anchor+j<L]
  if policy=='fixed':admit=n
  elif policy=='future_token':admit=sum(proposals)% (n+1)
  else:admit=int(tape[min(L-1,anchor+n-1)][0])%(n+1)
  budget_trace.append(admit);rounds+=1
  for j in range(admit+1):
   if len(committed)>=L:break
   pos=len(committed);y=target_samples[j];committed.append(y)
   if j==admit:break # bonus or zero-admission target draw
   if y!=proposals[j]:break
   matches+=1
  assert rounds<=L
 return committed,rounds,matches,budget_trace
checks=[]
for case in range(64):
 L=1+case%13;tape=[tuple(F(rng.randrange(1,97),rng.randrange(1,17)) for _ in range(3)) for _ in range(L)]
 oracle=reference(tape,L)
 for policy in ['fixed','future_token','future_noise']:
  actual,rounds,matches,admit=speculative(tape,L,policy);assert actual==oracle
  checks.append({'case':case,'policy':policy,'L':L,'rounds':rounds,'matches':matches,'admitted':admit})
# Known common exponential race diagonal probability; mathematical single-token
# coupling only, not expected progress for the five-token native block verifier.
p=(F(3,5),F(3,10),F(1,10));q=(F(1,5),F(3,10),F(1,2))
diag=[1/sum(max(p[j]/p[i],q[j]/q[i]) for j in range(3)) for i in range(3)]
accept=sum(diag);maximal=sum(min(a,c) for a,c in zip(p,q));assert accept<maximal
out={'scope':__doc__,'comparisons':len(checks),'tapes':64,'policies':['fixed','future_token','future_noise'],'result':'same finite-noise target-only outputs for all checks','cases':checks,'single_token_acceptance_example':{'p':list(map(str,p)),'q':list(map(str,q)),'shared_exponential_race':str(accept),'maximal_coupling':str(maximal),'interpretation':'Useful adverse progress control, not actual block accepted length or continuous sampling test.'},'excluded':['native model/logits/numerics','real random PRF independence','AV implementation','EOS/custom processors/cache commits/rank graphs','latency or GPU cost']}
(b/'oracle_control.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='cases'})

"""Fix the complete draft distribution; vary only discarded target information."""
from fractions import Fraction as F
from pathlib import Path
import json
q=[F(2,5),F(3,10),F(3,10)];alpha=F(4,5)
ps={'A':[F(2,5),F(1,2),F(1,10)],'B':[F(2,5),F(1,10),F(1,2)],'C':[F(2,5),F(9,20),F(3,20)]}
def coarse(v):return (v[0],sum(v[1:]))
assert len({coarse(p) for p in ps.values()})==1
# A preceding sampled token can produce alpha=.8: target=.4, draft=.5.
assert F(2,5)/F(1,2)==alpha
cases=[]
for name,p in ps.items():
 assert sum(p)==sum(q)==1 and all(x>0 for x in p+q)
 residual=[max(alpha*a-b,F(0)) for a,b in zip(p,q)]
 cases.append({'case':name,'target':list(map(str,p)),'full_draft':list(map(str,q)),'alpha':str(alpha),'target_selected_and_other':list(map(str,coarse(p))),'residual':list(map(str,residual)),'residual_mass':str(sum(residual)),'positive_token_ids':[i for i,x in enumerate(residual) if x>0]})
assert [x['residual_mass'] for x in cases]==['1/10','1/10','3/50']
assert cases[0]['positive_token_ids']!=cases[1]['positive_token_ids']
out={'scope':'Exact-rational information-loss counterexample for pinned max(alpha * target - draft, 0). Full draft distribution remains identical in every case. No native arithmetic, probability trace or service result.','alpha_example':'A previous-step target/draft sampled-token ratio of (2/5)/(1/2) yields4/5; this establishes a legal mathematical prefix ratio, not an observed runtime value.','cases':cases,'conclusion':'Identical target selected-token probability and complement mass, even with identical full draft probabilities, cannot determine residual support or mass.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'masses':[x['residual_mass'] for x in cases],'supports':[x['positive_token_ids'] for x in cases]}))

"""Exact scalar counterexample; no native model/backend imports or timing."""
from fractions import Fraction as F
import json
from pathlib import Path

P = [(F(9,10),F(1,10)),(F(17,20),F(3,20)),(F(9,10),F(1,10))]
WEIGHTS = [(8,1),(4,2),(1,8)]
def overlap(p,q):
    return sum(min(x,y) for x,y in zip(p,q))
def proposal(power):
    return [tuple(F(w**power,sum(v**power for v in row)) for w in row) for row in WEIGHTS]
def pack(x):
    return {"fraction":str(x),"decimal":float(x)}
def score(q):
    root=overlap(P[0],q[0])
    child=[overlap(P[i+1],q[i+1]) for i in range(2)]
    teacher_forced=root*(1+sum(P[0][i]*child[i] for i in range(2)))
    actual=root+sum(min(P[0][i],q[0][i])*child[i] for i in range(2))
    # Independent path enumeration: propose i then j; use two independent acceptance coins.
    first=F(0); both=F(0)
    for i in range(2):
        accept_i=min(F(1),P[0][i]/q[0][i])
        first+=q[0][i]*accept_i
        for j in range(2):
            accept_j=min(F(1),P[i+1][j]/q[i+1][j])
            both+=q[0][i]*q[i+1][j]*accept_i*accept_j
    assert actual==first+both
    return {"q":[list(map(str,row)) for row in q],"root_acceptance":pack(root),
            "child_acceptance":list(map(pack,child)),"teacher_forced_surrogate":pack(teacher_forced),
            "exact_accepted_draft_tokens":pack(actual),"enumerated_accepted_draft_tokens":pack(first+both)}
old=score(proposal(2)); new=score(proposal(1))
assert F(new["teacher_forced_surrogate"]["fraction"])>F(old["teacher_forced_surrogate"]["fraction"])
assert F(new["exact_accepted_draft_tokens"]["fraction"])<F(old["exact_accepted_draft_tokens"]["fraction"])
# Null distribution control: when q=p everywhere, both objectives are exactly two.
null=score(P)
assert F(null["teacher_forced_surrogate"]["fraction"])==2
assert F(null["exact_accepted_draft_tokens"]["fraction"])==2
result={"scope":"two-token autoregressive chain, standard sequential rejection, all support positive, no EOS; not native DSpark block verification",
        "construction":"fixed illustrative case selected by seeded search for a sign reversal, not representative sampling",
        "p":[list(map(str,row)) for row in P],"temperature_1":old,"temperature_2":new,"null_q_equals_p":null,
        "interpretation":"teacher-forced window surrogate improvement alone does not certify expected accepted progress; does not refute calibration"}
Path(__file__).with_name("result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"temperature_1":old,"temperature_2":new},indent=2))

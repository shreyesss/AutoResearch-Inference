"""Finite fair-coin selection control, not native AV or Gumbel execution."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import json

def mass_zero(outputs):
    return Fraction(sum(x == 0 for x in outputs), len(outputs))

policies = {
    'admit_neither_coin': (False, False),
    'admit_only_zero': (True, False),
    'admit_only_one': (False, True),
    'admit_both_coins': (True, True),
}
results=[]
for name, policy in policies.items():
    discarded=[];retained=[];reference=[]
    outcomes=[]
    for prior_noise, fresh_noise in product(range(2), repeat=2):
        admitted=policy[prior_noise]
        # Naive common-noise proposal: use the inspected noise if admitted;
        # otherwise draw a fresh target noise at the same output position.
        discard_output=prior_noise if admitted else fresh_noise
        # Stable per-position noise: scheduling changes only when it is used.
        retain_output=prior_noise
        discarded.append(discard_output);retained.append(retain_output)
        reference.append(prior_noise)
        outcomes.append({'prior_noise':prior_noise,'fresh_noise':fresh_noise,
                         'admitted':admitted,'discard_output':discard_output,
                         'retained_output':retain_output})
    assert mass_zero(reference)==mass_zero(retained)==Fraction(1,2)
    expected={'admit_neither_coin':Fraction(1,2),'admit_only_zero':Fraction(3,4),
              'admit_only_one':Fraction(1,4),'admit_both_coins':Fraction(1,2)}[name]
    assert mass_zero(discarded)==expected
    results.append({'policy':name,'admit_for_noise0_or1':list(policy),
                    'reference_p0':str(mass_zero(reference)),
                    'discard_and_resample_p0':str(mass_zero(discarded)),
                    'persistent_position_p0':str(mass_zero(retained)),
                    'outcomes':outcomes})
# Countercontrol: a scheduling coin independent of the target-position noise
# does not create the same selection bias when uncommitted noise is replaced.
independent=[]
for gate, prior_noise, fresh_noise in product(range(2),repeat=3):
    independent.append(prior_noise if gate==0 else fresh_noise)
assert mass_zero(independent)==Fraction(1,2)
out={'scope':__doc__,'policies':results,'independent_gate_p0':str(mass_zero(independent)),
     'enumerated_joint_outcomes':24,'new_hypothesis':False,'network_calls':0,'gpu_calls':0,
     'native_failure_claimed':False,'general_Gumbel_correctness_proved':False}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({r['policy']:r['discard_and_resample_p0'] for r in results}))

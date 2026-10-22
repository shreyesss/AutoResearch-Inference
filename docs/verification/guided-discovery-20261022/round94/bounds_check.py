"""Scalar opportunity bounds; no native execution or workload measurement."""
from itertools import product
from collections import defaultdict
from pathlib import Path
import json

def interval(scheduled, accepted, eligible=True):
    assert 0 <= accepted <= scheduled
    if not eligible:
        return 0, max(accepted - 1, 0)
    return (max(accepted - 1, 0) if accepted == scheduled else 0,
            max(accepted - 1, 0))

# Independent hidden-state enumeration: here eligibility is known true;
# admitted capacity is any integer from accepted through scheduled.
# Actual FV86 omits m-1 interior rows iff the whole admitted block passes.
pairs = [(s, a) for s in range(6) for a in range(s + 1)]
single = {}
for s, a in pairs:
    possibilities = [max(m - 1, 0) if a == m else 0 for m in range(a, s + 1)]
    assert interval(s, a) == (min(possibilities), max(possibilities))
    single[s, a] = possibilities
joint_checks = 0
hidden_checks = 0
for rows in product(pairs, repeat=3):
    totals = [sum(x) for x in product(*(single[row] for row in rows))]
    wanted = (sum(interval(*r)[0] for r in rows), sum(interval(*r)[1] for r in rows))
    assert wanted == (min(totals), max(totals))
    joint_checks += 1
    hidden_checks += len(totals)

# If only N, total accepted A, and fixed scheduled maximum5 are retained,
# enumerate every accepted array and every possible hidden opportunity sum.
# Equality below verifies sharp bounds under these relaxed assumptions.
aggregate_checks = 0
for n in range(1, 5):
    by_total = defaultdict(list)
    for accepted in product(range(6), repeat=n):
        lower = sum(4 if a == 5 else 0 for a in accepted)
        upper = sum(max(a - 1, 0) for a in accepted)
        by_total[sum(accepted)].append((lower, upper))
    for total, intervals in by_total.items():
        predicted = (4 * max(0, total - 4 * n), total - (total + 4) // 5)
        observed = (min(x[0] for x in intervals), max(x[1] for x in intervals))
        assert predicted == observed, (n, total, predicted, observed)
        aggregate_checks += 1

examples = [
    {'scheduled':5,'accepted':2,'rows_bound':list(interval(5,2)), 'meaning':'Partial visible acceptance; full hidden admission is ambiguous'},
    {'scheduled':5,'accepted':5,'rows_bound':list(interval(5,5)), 'meaning':'Maximum acceptance forces full admission under the stated mapping'},
    {'scheduled':5,'accepted':1,'rows_bound':list(interval(5,1)), 'meaning':'No interior row can be omitted'},
    {'scheduled':5,'accepted':5,'eligibility_unverified':True,'rows_bound':list(interval(5,5,False)), 'meaning':'Branch/ID validity unknown: no positive unconditional lower bound'},
]
out={'scope':__doc__,'observed_workload_data':False,'gpu_calls':0,'network_calls':0,
     'maximum_scheduled':5,'single_pair_checks':len(pairs),
     'joint_observation_checks':joint_checks,'hidden_assignment_checks':hidden_checks,
     'aggregate_moment_checks':aggregate_checks,'examples':examples,
     'assumptions':['Accepted count maps to actual verifier accepted drafts before stop truncation',
       '0 <= accepted <= admitted <= scheduled <= 5',
       'Known eligible nongreedy full-q block path with all admitted IDs valid for positive lower bound',
       'No per-step total-budget or confidence constraint used; extra constraints may tighten bounds'],
     'not_estimated':['actual admission frequency','saved physical memory traffic','latency','native correctness','service improvement']}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k.endswith('checks')}))

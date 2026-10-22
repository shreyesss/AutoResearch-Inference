"""Information-loss witness, not AV/native execution or observed traffic."""
import json
from pathlib import Path

# Both scenarios have the same configured/scheduled drafts and sampled output
# length. Only the actual GPU-admitted length differs; the reviewed scheduler
# statistics do not receive that length.
cases = [
    {"scenario": "short admitted block fully accepted", "scheduled": 5,
     "admitted": 2, "accepted": 2, "all_valid": True},
    {"scenario": "full admitted block partly accepted", "scheduled": 5,
     "admitted": 5, "accepted": 2, "all_valid": True},
]
for row in cases:
    a = row['accepted']
    row['retained_observables'] = {
        'per_step_drafted': [row['scheduled']], 'per_step_accepted': [a],
        'acceptance_histogram': [int(j == a) for j in range(6)],
        'mean_acceptance_length': 1 + a, 'draft_acceptance_rate': a/row['scheduled'],
        'accepted_per_pos': [int(j < a) for j in range(5)],
        'drafted_per_pos': [int(j < row['scheduled']) for j in range(5)],
    }
    row['terminal_full_pass'] = a == row['admitted']
    row['residual_rows_eligible_to_skip'] = row['admitted'] - 1 if row['terminal_full_pass'] else 0
assert cases[0]['retained_observables'] == cases[1]['retained_observables']
assert cases[0]['terminal_full_pass'] != cases[1]['terminal_full_pass']
result = {'scope': __doc__, 'cases': cases,
          'same_retained_metrics': True, 'different_terminal_eligibility': True,
          'conclusion': 'Scheduler-length detailed metrics do not determine actual AV terminal-pass eligibility.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'same_retained_metrics': True, 'different_terminal_eligibility': True}))

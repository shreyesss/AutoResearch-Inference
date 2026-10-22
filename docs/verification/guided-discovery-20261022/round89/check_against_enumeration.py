"""Compare reusable binary64 tool against round87 complete rational forward law."""
import importlib.util
import itertools
import json
import math
from pathlib import Path
from fractions import Fraction
from ideation.round_estimate import estimate_rounds

base = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finite', base/'round87-block-offline-contract/forward_enum.py')
finite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finite)
checked = 0
max_error = 0.0
for length, size in [(3, 1), (3, 2), (4, 2), (4, 3)]:
    for mode, variant in [('none', 0), ('p', 1), ('q', 1), ('both', 1), ('both', 2)]:
        p, q = finite.model(variant, mode)
        law = finite.full_law(length, size, p, q)
        for sequence in itertools.product(finite.V, repeat=length):
            joint = {r: sum(v for (s, k), v in law.items() if s == sequence and k == r)
                     for r in range(1, length+1)}
            total = sum(joint.values())
            expected = sum(Fraction(r)*v/total for r, v in joint.items())
            record = {
                'schema_version': 1, 'law': 'block', 'block_size': size,
                'horizon': 'fixed_output_cap_no_eos_full_block', 'adaptive_verification': False,
                'probability_semantics': 'normalized_after_sampling_transforms_all_anchors',
                'provenance': {'kind': 'synthetic', 'target': 'round87 finite p', 'proposal': 'round87 finite q',
                               'trajectory': ''.join(sequence), 'probability_source': 'complete normalized binary distributions'},
                'target_probabilities': [float(p(sequence[:i])[token]) for i, token in enumerate(sequence)],
                'proposal_probabilities_by_anchor': [[float(q(n, sequence[:t])[sequence[t]])
                                                     for t in range(n, min(n+size, length))]
                                                    for n in range(length)],
            }
            result = estimate_rounds(record)
            error = abs(result['expected_rounds_given_trajectory'] - float(expected))
            max_error = max(error, max_error)
            assert math.isclose(result['expected_rounds_given_trajectory'], float(expected), abs_tol=1e-12)
            checked += 1
output = {'conditional_means_compared': checked, 'max_absolute_error': max_error,
          'reference': 'Complete rational forward sampler enumeration from frozen round87; not its posterior recursion',
          'scope': 'Finite synthetic CPU cases; no target model, native sampler, GPU or latency validation'}
Path(__file__).with_suffix('.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps(output))

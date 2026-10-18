"""Freeze finalists using development results before running any held-out input."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / '.artifacts/optuna-direct-v1'


def main():
    destination = STUDY / 'confirmation-selection.json'
    if destination.exists():
        raise RuntimeError('Finalist selection already frozen')
    finished = json.loads((STUDY / 'search-finished.json').read_text())
    trials = json.loads((STUDY / 'search-trials.json').read_text())
    complete = [t for t in trials if t['state'] == 'COMPLETE']
    b0 = next(t for t in complete if t['attrs'].get('role') == 'matched_B0')
    candidates = [t for t in complete if t['number'] != b0['number']]
    if not candidates:
        raise RuntimeError('No successful candidate to confirm')
    def values(t):
        return [-t['values'][0], *t['values'][1:]]
    def dominates(a, b):
        av, bv = values(a), values(b)
        return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))
    front = [t for t in candidates if not any(dominates(other, t) for other in complete)]
    # If B0 dominates every candidate, test the best observed tradeoffs anyway;
    # this can confirm a negative outcome without pretending a win exists.
    pool = front or candidates
    selected = []
    for objective in range(3):
        candidate = min(pool, key=lambda t: (values(t)[objective], t['number']))
        if candidate not in selected:
            selected.append(candidate)
    def item(t, role):
        return {'search_trial': t['number'], 'role': role, 'params': t['params']}
    payload = {'frozen_unix': time.time(), 'search_finished': finished,
        'rule': 'distinct throughput/TTFT/TPOT extrema of development Pareto frontier; at most three candidates',
        'test_feedback_to_search': False, 'all_candidates_dominated_by_b0': not bool(front),
        'sequence': [item(b0, 'heldout_B0_before'),
                     *[item(t, 'heldout_candidate') for t in selected],
                     item(b0, 'heldout_B0_after')]}
    destination.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()

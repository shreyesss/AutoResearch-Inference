"""Exact finite ordinary-rejection control; no model/native imports.

Independent enumeration sums accepted and residual event mass. The other
calculation implements paper2610.10411 Eq3/5/16 conditioned on target output.
Neither calculation implements native DSpark block rejection or serving cost.
"""
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
import json


def target(prefix, length):
    if len(prefix) == length:
        return {"E": F(1)}
    a = F(2 if not prefix or prefix[-1] == "a" else 4, 7)
    return {"a": a, "b": 1-a}


def draft(prefix, anchor, length, variant):
    if len(prefix) == length:
        return {"E": F(1)}
    # Positive anchor/parent-conditioned laws. No fitted model data.
    a = F(1 + (anchor*3 + len(prefix)*2 + variant +
               (2 if prefix and prefix[-1] == "a" else 0)) % 8, 10)
    return {"a": a, "b": 1-a}


def enumerate_events(length, block, variant):
    mass, weighted_rounds = defaultdict(F), defaultdict(F)

    def visit(prefix, anchor, rounds, prob):
        if prefix and prefix[-1] == "E":
            mass[prefix] += prob
            weighted_rounds[prefix] += prob*rounds
            return
        p = target(prefix, length)
        if len(prefix)-anchor == block:  # target bonus
            for token, pt in p.items():
                new = prefix+(token,)
                visit(new, len(new), rounds+(token != "E"), prob*pt)
            return
        q = draft(prefix, anchor, length, variant)
        for token in p:
            accepted = min(p[token], q[token])
            residual = max(p[token]-q[token], F(0))
            if accepted:
                visit(prefix+(token,), anchor, rounds, prob*accepted)
            if residual:
                new = prefix+(token,)
                visit(new, len(new), rounds+(token != "E"), prob*residual)

    visit((), 0, 1, F(1))
    assert sum(mass.values()) == 1
    return mass, weighted_rounds


def conditional_rounds(sequence, block, variant, reverse_ratio=False):
    occupancy = {0: F(1)}
    rounds = F(1)
    length = len(sequence)-1
    for pos, token in enumerate(sequence[:-1]):
        nxt = defaultdict(F)
        prefix = sequence[:pos]
        for anchor, weight in occupancy.items():
            if pos-anchor == block:
                acceptance = F(0)  # forced bonus transition
            else:
                p = target(prefix, length)[token]
                q = draft(prefix, anchor, length, variant)[token]
                acceptance = min(F(1), p/q if reverse_ratio else q/p)
            nxt[anchor] += weight*acceptance
            nxt[pos+1] += weight*(1-acceptance)
        rounds += nxt[pos+1]
        occupancy = dict(nxt)
        assert sum(occupancy.values()) == 1
    return rounds


def run():
    cases = []
    mismatches = 0
    sequence_checks = 0
    for length, block, variant in product([1, 2, 3, 4], [1, 2, 3], [0, 1, 4]):
        mass, weighted = enumerate_events(length, block, variant)
        estimate = F(0)
        reversed_estimate = F(0)
        for seq, prob in mass.items():
            expected_mass = F(1)
            for pos, token in enumerate(seq):
                expected_mass *= target(seq[:pos], length)[token]
            assert prob == expected_mass
            rounds = conditional_rounds(seq, block, variant)
            assert rounds == weighted[seq]/prob
            estimate += prob*rounds
            reversed_estimate += prob*conditional_rounds(seq, block, variant, True)
            sequence_checks += 1
        assert estimate == sum(weighted.values())
        mismatches += reversed_estimate != estimate
        cases.append({"ordinary_tokens": length, "block": block,
                      "variant": variant, "expected_rounds": str(estimate),
                      "wrong_ratio_rounds": str(reversed_estimate),
                      "target_sequences": len(mass)})
    assert mismatches > 0
    # This control isolates different stopping semantics, not model-derived h.
    passes = [False, True]
    first_failure = 0
    latest_passing = max([i+1 for i, passed in enumerate(passes) if passed], default=0)
    assert first_failure != latest_passing
    return {"status": "passed", "cases": cases, "case_count": len(cases),
            "conditional_sequence_checks": sequence_checks,
            "wrong_ratio_mismatching_cases": mismatches,
            "stopping_semantics_control": {"illustrative_tests": passes,
                "first_failure_accepted": first_failure,
                "latest_passing_accepted": latest_passing,
                "meaning": "Not a realized native probability/RNG fixture"},
            "limits": ["Finite synthetic ordinary sequential rejection only",
                       "No native DSpark block rejection, AV or floating arithmetic",
                       "No measured model acceptance, GPU work or latency gain"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

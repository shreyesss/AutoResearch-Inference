"""Source/stdlib diagnostics only. Never import or execute donor tensor code."""
from pathlib import Path
from fractions import Fraction as F
import ast
import hashlib
import json

B = Path(__file__).parent
def node(path, name):
    raw = (B / 'donor' / path).read_text()
    module = ast.parse(raw)
    for cls in module.body:
        if isinstance(cls, ast.ClassDef) and cls.name == name:
            return raw, cls
    raise AssertionError(name)

gen_raw, gen = node('generator.py', 'InvariantGenerator')
single_raw, single = node('strategy.py', 'InvariantSingleDraftStrategy')
multi_raw, multi = node('strategy.py', 'InvariantMultiDraftStrategy')
def method(cls, name):
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
def gumbel_calls(m):
    return [ast.unparse(n) for n in ast.walk(m) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == 'gumbel_sample']

single_calls = gumbel_calls(method(single, 'verify_draft'))
multi_calls = gumbel_calls(method(multi, 'verify_draft'))
assert single_calls == ['gumbel_sample(logits, rn)']
assert 'gumbel_sample(logits[alive_group_id, depth])' in multi_calls
assert 'position = input_ids.size(-1) - input_len' in gen_raw
assert 'randomness.uniform_()' in gen_raw
assert 'randomness[position:(position + self.max_draft_len + 1), 0, :]' in single_raw

# Shared exponential coupling on binary full-support distributions is monotone
# in E0/E1. Its diagonal probabilities equal min(p_i,q_i). This is a
# one-position control of the fresh terminal draw, not the configured K>=2 run.
p = [F(4, 5), F(1, 5)]
q = [F(1, 5), F(4, 5)]
diag = [min(a, b) for a, b in zip(p, q)]
reject = 1 - sum(diag)
wrong = [diag[i] + reject * p[i] for i in range(2)]
tv = sum(abs(wrong[i] - p[i]) for i in range(2)) / 2
assert wrong == [F(17, 25), F(8, 25)] and tv == F(3, 25)

# K=2 boundary control: both drafts deterministically choose token1, while
# the shared target winner is categorical p (min of two Exp clocks has common
# rate2). If Y=0 all candidates reject; replacing it by independent p yields
# output0=p0^2, not p0. This uses a zero proposal mass and is not benchmark data.
wrong_k2 = [p[0] * p[0], p[1] + p[0] * p[1]]
assert wrong_k2 == [F(16, 25), F(9, 25)]

# Full-support K=2, depth0: every draft's target logits have the same actual
# prefix. Paper min-exponential / donor max-uniform yields one common Y.
# Put a=q0/q1=1/4 and b=p0/p1=4. Condition on min(E11,E12)=t.
# P(all X=1,Y=1) = 2 integral exp(-(1+b)t) * J(t) dt, where
# J(t)=exp(-(b+1)t)-a/(1+a)*exp(-(b+b/a)t).
# This evaluates exactly by integrating exponentials; no quadrature or model.
a, bb = q[0] / q[1], p[0] / p[1]
all_one_y_one = 2 * (1 / (2 * (bb + 1)) -
                        a / (1 + a) / (1 + 2 * bb + bb / a))
assert all_one_y_one == F(23, 125)
reject_k2 = q[1] ** 2 - all_one_y_one
# Y=1 cannot have both draft tokens0: at the smallest E1, X=0 implies
# minE0 <= E0 < a*minE1 < b*minE1, contradicting Y=1.
diag_k2 = [p[0] - reject_k2, p[1]]
wrong_k2_full = [diag_k2[i] + reject_k2 * p[i] for i in range(2)]
assert wrong_k2_full == [F(443, 625), F(182, 625)]

# Logical resident storage if donor default float32 tape is copied unchanged;
# no measured memory traffic or allocation latency. Native uses regeneration.
allocations = []
for name, length, depth, count, vocab in [
    ('donor standard K1', 128, 4, 1, 151936),
    ('donor standard K8', 128, 4, 8, 151936),
    ('target illustrative output1024 K1', 1024, 5, 1, 129280),
    ('target illustrative output1024 K8', 1024, 5, 8, 129280),
]:
    size = (length + depth + 1) * count * vocab * 4
    allocations.append(dict(label=name, output_length=length, draft_depth=depth,
        draft_count=count, vocab=vocab, assumed_itemsize=4, bytes=size,
        MiB=size / 2**20))

result = {
 'scope': 'AST source observations and two exact ideal-law countercontrols; no torch/native/GPU execution or deployment inputs',
 'donor_commit': 'a9d042912b42e5b2b0ea48d650f1b2e8f05af68a',
 'source_sha256': {p:hashlib.sha256((B/'donor'/p).read_bytes()).hexdigest()
                   for p in ['generator.py','strategy.py','utils.py','test.py','qwen2_std.json']},
 'single_verify_gumbel_calls': single_calls,
 'multi_verify_gumbel_calls': multi_calls,
 'single_position_tape_observed': True,
 'K1_full_support_countercontrol': {'target':list(map(str,p)), 'proposal':list(map(str,q)),
    'match_diagonal':list(map(str,diag)), 'fresh_after_rejection':list(map(str,wrong)),
    'TV':str(tv), 'limitation':'class supports K1; retained benchmark configurations use multi K>=2'},
 'K2_zero_proposal_countercontrol': {'target':list(map(str,p)), 'proposal':['0','1'],
    'fresh_after_rejection':list(map(str,wrong_k2)),
    'limitation':'boundary law control, not observed logits or same-topk50 benchmark fixture'},
 'K2_full_support_countercontrol': {'target':list(map(str,p)), 'proposal':list(map(str,q)),
    'all_drafts_one_and_target_one':str(all_one_y_one),
    'no_matching_draft':str(reject_k2), 'match_diagonal':list(map(str,diag_k2)),
    'fresh_after_rejection':list(map(str,wrong_k2_full)), 'TV':str(p[0]-wrong_k2_full[0]),
    'branch':'first position, identical target prefix on both rows, all rejections leave alive_group_id=0; fresh target redraw uses that same p',
    'limitation':'ideal continuous-noise integration, not finite torch PRNG/benchmark execution'},
 'logical_tape_allocations': allocations,
 'verdict':'single path supplies source precedent; do not transplant the multi-path fresh rejection redraw; no speed or complete donor-correctness claim'
}
(B/'source_controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

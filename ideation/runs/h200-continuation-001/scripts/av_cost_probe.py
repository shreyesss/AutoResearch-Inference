"""CPU counterexample to a budget-independent draft cost, not a speed estimate.

Execute only the extracted installed get_num_tokens method with synthetic arrays.
An independent exhaustive prefix-allocation oracle checks its choice. All costs
are invented fixtures; neither runtime behavior nor H200 latency is measured.
"""
import ast
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np

RUN = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=RUN / 'sources/installed-adaptive-verification.py')
parser.add_argument('--output', type=Path, required=True, help='New receipt path; existing artifacts are not overwritten')
args = parser.parse_args()
if args.output.exists():
    raise ValueError('Choose a new output file; retain prior receipts')
SOURCE = args.source
tree = ast.parse(SOURCE.read_text())
method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'get_num_tokens')
method.decorator_list = []
module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
namespace = {'np': np}
exec(compile(module, str(SOURCE), 'exec'), namespace)
n, k = 5, 5
confidence = np.tile([0.9,0.8,0.5,0.3,0.1], (n,1))
req_ids = [f'r{i}' for i in range(n)]
verify = np.array([0.4 if t <= 8 else 0.6 if t <= 16 else 1.0 if t <= 24 else 1.3 for t in range(31)])
draft_constant = np.full(65, 0.7)
state = NS(req_id_to_index={r:i for i,r in enumerate(req_ids)}, num_computed_tokens_np=np.full(n,100), prefill_len=NS(np=np.full(n,100)))
manager = NS(cost_tables=(draft_constant,verify), req_states=state, num_speculative_steps=k,
             _stale_confidences=[NS(np=confidence)], _stale_idx=0, _max_total_logits=256, num_bonus_tokens=1)
selected_tokens = namespace['get_num_tokens'](manager,{r:6 for r in req_ids},{r:[1]*k for r in req_ids})
selected_budget = selected_tokens-n

# Independent enumeration: 6^5 prefix allocations; no flattened top-k implementation.
survival = np.cumprod(confidence,axis=1)
best_progress = np.zeros(n*k+1)
for lengths in itertools.product(range(k+1),repeat=n):
    progress = n + sum(sum(survival[i,:length]) for i,length in enumerate(lengths))
    budget = sum(lengths)
    best_progress[budget] = max(best_progress[budget],progress)
constant_objective = [best_progress[b]/(0.7+verify[n+b]) for b in range(n*k+1)]
oracle_constant = max(range(n*k+1),key=lambda b:constant_objective[b])
assert selected_budget == oracle_constant

# Source-derived possible target buckets; synthetic draft latency assigned to each.
bucket = lambda rows: next(x for x in [8,16,24,32] if x >= rows)
synthetic_draft_cost = {8:0.8,16:1.6,24:2.4,32:3.2}
coupled_objective = [best_progress[b]/(verify[n+b]+synthetic_draft_cost[bucket(n+b)]) for b in range(n*k+1)]
oracle_coupled = max(range(n*k+1),key=lambda b:coupled_objective[b])
assert oracle_coupled != selected_budget
assert coupled_objective[oracle_coupled] > coupled_objective[selected_budget]

result={'scope':'Synthetic CPU source-method counterexample only; no measured milliseconds, dispatch or service gain.',
        'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'method_lines':[method.lineno,method.end_lineno],
        'fixture':{'requests':n,'k':k,'confidence_per_request':confidence[0].tolist(),
                   'constant_draft_cost':0.7,'synthetic_coupled_draft_cost_by_target_bucket':synthetic_draft_cost},
        'installed_method_budget':selected_budget,'independent_constant_cost_budget':oracle_constant,
        'independent_coupled_cost_budget':oracle_coupled,
        'checks':{'constant_cost_agrees':True,'coupled_cost_changes_decision':True,'selected_code_imports_no_torch_or_cuda':True},
        'implication':'A constant draft-cost assumption can choose the wrong budget if actual draft cost changes with the target graph. Establish real dispatch and measured costs before changing a controller.',
        'not_established':['Frequency of this interaction','Actual component latency','Correctness of a candidate controller','End-to-end benefit','Permission to repeat C03 or enable AV']}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

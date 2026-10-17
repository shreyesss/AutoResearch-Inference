# Frozen OPS replay in the evaluator

`infra/freeze-ops-synthetic-cell.py` writes one native AIPerf `single-turn` JSONL,
one workload card, and one scenario manifest per measured synthetic source cell.
The JSONL fixes request bodies, output caps, IDs, and arrival timestamps. Its
manifest pins the asset hashes and model/tokenizer identity.

The evaluator only accepts an OPS scenario after its manifest is explicitly
listed in `configs/workloads/registry.json` and its card and manifest both have
`readiness: validated`. The freeze step writes `prepared`; an independent
fixed-schedule B0 replay must establish request completeness and correct
payload/output realization before promotion. Prepared scenarios can be inspected
with `ScenarioRegistry.load(id, require_validated=False)` but cannot enter a
normal evaluation.

For a registered cell, the registry verifies the hashes and derives the true
schedule length from the final frozen timestamp. The evaluator sets the AIPerf
benchmark window to at least that length plus 10 seconds, allows 60 to 180
seconds for drain, and sets the process deadline beyond both windows. The
ordinary 60-second fixtures keep their previous 70-second benchmark,
60-second grace, and 180-second process deadline. AIPerf rejects an externally
constructed policy that would cut off a frozen schedule or its grace window.
Each cell records its limits in `evaluation-policy.json`.

The adapter uses `--custom-dataset-type single-turn --fixed-schedule` with the
frozen JSONL. It does not regenerate arrivals or re-sample prompts. A replay
with missing requests, wrong outputs, client lag, or a truncated export is
ineligible and retains its raw logs for inspection.

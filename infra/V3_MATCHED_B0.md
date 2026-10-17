# Matched evaluator B0 on qualified development inputs

This is the next gate **after** `development_inputs_qualified` in
`.artifacts/v3-independent-capture/development-overnight-checkpoint.json`.
The new campaign `configs/campaign-sla-b0-v3.json` reuses the pinned Qwen,
vLLM image, GPU, and resolved stock serving configuration from v2, but has a
separate immutable campaign ID and ledger. Its registry contains only the two
development windows. The engine uses `screen` with
`fresh-server-cell-v1`: one fresh server and disjoint warmup per 240-request
window. This takes roughly two full 40-minute dispatches plus startup/drain.

Read-only checks:

```bash
PYTHONPATH=src .venv/bin/python infra/run_v3_matched_b0.py check-config
PYTHONPATH=src .venv/bin/python infra/run_v3_matched_b0.py check
```

The second command returns success only after both input manifests have been
replay-validated, promoted, and split-audited; it also checks the overnight
checkpoint, versioned hashes, class counts, and that the shared B0 source
container was stopped. The first command checks static campaign, policy,
split and registry pins without requiring captured input artifacts.

After the overnight input checkpoint passes, run the actual evaluator B0:

```bash
PYTHONPATH=src .venv/bin/python infra/run_v3_matched_b0.py run \
  > .artifacts/v3-independent-capture/matched-evaluator-b0-launch.log 2>&1
```

The runner checks that the GPU is idle, refuses an existing campaign output,
and invokes `iar baseline --backend real --stage screen` for exactly the two
qualified development scenarios. It saves the exact command, console log,
preflight pins, native CellResults, raw AIPerf records, and a
`matched-evaluator-b0-receipt.json` containing each result path and hash. It
fails if either CellResult is not valid/normal, lacks complete 240/240
accounting, does not match its frozen schedule hash, or lacks raw records.

The SLA study's `adaptive_development.baseline_cell_paths` must contain the
actual first window CellResult path from the receipt. The second path is a
development replication/confirmation B0. Both are evaluator measurements;
the earlier fixed-schedule replay validation report is **not** a CellResult.
The 0.1 requests/s B0 cells anchor behavior at that rate only. Neither this
script nor its receipt claims SLA capacity; class-aware adaptive load probing
and independent confirmation are separate next gates.

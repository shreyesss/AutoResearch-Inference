# B200 PR evaluation audit: reconstruction guide

This directory is an **audit and test plan**, not a benchmark result. It inventories 5,532 PR/issue catalog entries, identifies 64 source-reviewed candidate/dependency records, and groups proposed tests into 18 performance experiments (E01–E18) and five correctness/reliability gates (G01–G05). No patch, image build, deployment, GPU test or quality test was run here. The configured baseline is **not** an attested live server.

## Read in this order

1. [REPORT.md](REPORT.md) — decisions, review depth, exclusions and priority order.
2. [PROTOCOL.md](PROTOCOL.md) — exact target/profile, E1/E2 historical benchmarks, SLO and cost math, A/B decision rules.
3. [EXPERIMENT_INDEX.md](EXPERIMENT_INDEX.md) — link to each experiment's isolated arms and evidence gates.
4. [MECHANISM_CARDS.md](evaluation/MECHANISM_CARDS.md) — upstream-reported inefficiency/fix, **separate** agent hypothesis, and activation signal for every E/G ID.
5. [EVALUATION_PLAN.md](evaluation/EVALUATION_PLAN.md) — task-specific counters, correctness gates, tool integration and fixed enhanced evalset. [Evaluator critique](evaluation/EVALUATOR_RECONCILIATION.md) explains the choices.
6. [EVALUATION_CAPABILITIES.md](evaluation/EVALUATION_CAPABILITIES.md) — what the inspected serving checkout and evaluation drivers actually supported. The [plain-language guide](walkthrough/NOVICE_GUIDE.md) and [E01–E03 deep dives](walkthrough/README.md) are optional explanations.

**Start a new test by choosing one E/G card, checking actual runtime eligibility, then following its gate and the protocol.** Do not treat an upstream PR description, a catalog label or a source snapshot as proof of a live bottleneck. Do not stack alternative PRs and attribute a combined gain to one change.

## What is in the checkout

| Location | Role | Rebuild status |
|---|---|
| `inputs/` | Frozen original catalog Markdown/CSV plus 31 MB cached PR opening records; [input hashes](input-manifest.json) | Keep: required to rebuild the 5,532-row ledger offline. |
| `spec-candidates/`, `kernel-candidates/`, `root-candidates/` | Specialist source reviews, selected PR objects and candidate decisions | Keep: `scripts/build_audit.py` reads their `candidates.json`; other JSON retains exact evidence and source identity. |
| `scripts/build_audit.py` | Standard-library offline builder | Regenerates `PR_DISPOSITIONS.csv`, `RANKED_PRS.csv`, `experiments.json`, `coverage.json`, `input-manifest.json` and `experiments/*.md` from frozen inputs/reviews. It does **not** regenerate the hand-authored protocol, report, mechanism cards or evaluation plan. |
| `scripts/register_plans.py` | Optional historical memory registration | Writes to `ideation/data/hypotheses.sqlite`; **do not run during ordinary reconstruction**. It uses the ideation package/jsonschema and saves a pre-registration backup in `archive/memory/`. Existing [receipts](memory-registration.json) and [cards](hypothesis-cards.json) preserve the already planned IDs. |
| `PR_DISPOSITIONS.csv`, `RANKED_PRS.csv`, `experiments.json`, `experiments/*.md` | Generated decision ledger and experiment cards | Read directly or verify with the offline builder in a temporary copy. Family assignment for a backlog row is a review destination, not an approved cherry-pick. |
| `evaluation/` | Current evaluator analysis and source inventory | Documentation/manifest, with raw source and CLI captures moved to `archive/`. |
| `archive/` | Original raw evaluator snapshot, CLI captures, pre-registration database and an **outdated** deliverable hash list | Preserve for provenance; it is not a live source tree or the current digest manifest. See [archive map](archive/README.md). |

The large `inputs/corpus-opening-records.jsonl` remains alongside the two frozen catalog files because the builder and quote validator need it. The archive is for material that does not belong in the working decision surface; nothing was deleted.

## Baseline and source pins to preserve

- Serving checkout inspected read-only: `Deepseek_serve` commit `2e6fa287d90adf7318ad314de27aa2f595aac821`. Its selected files and SHA-256 values are in [the source-snapshot manifest](evaluation/snapshot-manifest.json), with files under [`archive/evaluator-source-snapshot/`](archive/evaluator-source-snapshot/). This snapshot is **partial**, not a runnable checkout.
- Configured vLLM source mapping: `ac9126e58aa7bbab1856ba6593ba4d5003fea516`; default image digest: `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`. Verify the real runtime digest/source and equivalent behavior before selecting a patch.
- Target profile: one eight-B200 node, two four-GPU replicas, TP1/DP4/EP4 per replica, API2, DSpark k5, adaptive verification OFF, prefix caching ON, Engram host offload ON, HICache OFF. The historical R7b-style E1 comparison needs `lat-seqs-128`, not the profile's seq64 default. Preserve bounded external router settings.
- Historical E1: native `agent-f75`, 8,192 input / 1,024 exact output tokens, 6,144-token shared prefix, Zipf pool 64; c256/384/512, 120 s warmup / 150 s measure. Historical E2: AIPerf 0.13.0 Mooncake fixed-schedule median/burst/cache-heavy 600 s windows with source revision/SHA in [`campaign.yaml`](archive/evaluator-source-snapshot/ops_aiperf/campaign.yaml). The proposed enhanced evalset adds **separately named** diagnostics and held-out windows; it never replaces these anchors.

## Reconstruct or verify offline after pulling

From the repository root, use Python 3.10+; the builder itself uses only the standard library. Work in a temporary copy to avoid overwriting the checked-in decision cards:

```bash
RUN=ideation/runs/pr-evaluation-audit-001
tmp_dir=$(mktemp -d)
cp -a "$RUN" "$tmp_dir/audit"
python3 "$tmp_dir/audit/scripts/build_audit.py"
diff -u "$RUN/coverage.json" "$tmp_dir/audit/coverage.json"
diff -u "$RUN/RANKED_PRS.csv" "$tmp_dir/audit/RANKED_PRS.csv"
diff -u "$RUN/PR_DISPOSITIONS.csv" "$tmp_dir/audit/PR_DISPOSITIONS.csv"
```

Check the three `inputs/` SHA-256 values in [`input-manifest.json`](input-manifest.json), then inspect [`coverage.json`](coverage.json): 5,532 unique identities, 64 source-reviewed candidate/dependency rows, 23 plans, no GPU experiments. The original [`verification.json`](verification.json) records the audit-time checks; it is a historical receipt, not proof that a newly pulled runtime is configured. The archived [`deliverable-sha256.json`](archive/original-deliverable/deliverable-sha256.json) predates later documentation and is **not** a current whole-directory integrity check.

The builder is deterministic over the frozen files, but it does not repeat live GitHub review, resolve moving PR heads or attest a serving image. `root-candidates/build_review.py` and specialist readers are provenance scripts whose output may depend on stored/current PR objects; their saved JSON is the frozen source for this audit. For exact PR bodies and head SHAs, inspect candidate JSON and the cached opening records; for original classifications inspect `inputs/`. No external `Deepseek_serve` checkout is required to *read* this run, but a full serving checkout and live host inspection are required to execute any proposed experiment.

## Execution handoff for an agent

1. Read the selected experiment, its linked mechanism card and source record; distinguish upstream claim from our hypothesis and any conditional adaptation.
2. Attest the real image/source, model/draft/tokenizer, dependency and resolved profile. Check whether the fix is already present or the affected branch is inactive. Record exact source/PR head SHA.
3. Run the experiment's smallest activation probe and relevant G01–G05/reference tests. If telemetry is missing, report **mechanism unverified**.
4. Use unprofiled E1/E2 comparison and the existing scorers. Use Nsight Systems/Compute only for short diagnosis; track all replicas/ranks and all eight GPUs.
5. Freeze the [enhanced evalset](evaluation/EVALUATION_PLAN.md#5-fixed-enhanced-evalset-and-pareto-decision), then compare qualifying cost–TTFT–TPOT points with run-level uncertainty. Preserve failed points and raw artifacts.

Nothing in this checkout establishes a B200 speedup. The actionable output is a reproducible shortlist and the measurements needed to accept or reject it.

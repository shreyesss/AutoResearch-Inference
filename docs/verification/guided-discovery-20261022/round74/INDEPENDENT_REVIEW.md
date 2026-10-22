# Independent review — round74 AV activation

Verdict: the bounded activation audit is supported. AV68 remains a source-supported, execution-deferred same-step elision. This review neither establishes AV activation nor rejects a separately justified AV activation/tuning experiment.

## Decision-changing source check

At c455, `vllm/config/speculative.py:555` defaults AV false. `vllm/v1/worker/gpu/spec_decode/speculator.py:174–178` copies the configured flag and initializes estimator selection from it. Its `load_model` calls the DSpark override at line229 before checking `use_acceptance_estimator` at251. DSpark's override at106–114 sets `use_confidence_head` from the enabled flag and loaded head, and only clears **use_acceptance_estimator** when a head is available. It does not clear **enable_adaptive_verification** when the head is absent. The actual estimator construction at259–263 and local-argmax rejection at252–258 therefore support the report. The contrary runner comment at692–693 is stale for this inspected DSpark path; comment text is not configuration evidence.

Manager construction at `adaptive_verification.py:450–510` returns None when disabled and raises for unsupported mismatch/varlen capabilities when requested. `model_runner.py:1119–1126` profiles initial costs for an existing manager; missing curves raise at `adaptive_verification.py:240–245`. These are source paths and startup requirements, not evidence that initialization occurred in the planned deployment.

The per-step guard at `model_runner.py:1390,1423` is truthiness of the scheduled-draft dictionary, not sum of draft counts. A nonempty dictionary whose entries contain zero drafts still selects the manager. Empty dictionaries, including the separate multi-bonus general case, do not. The prior round68 overwrite proof need not be re-simulated for this audit.

## Evidence and scope

Independently verified all seven author artifact hashes, all 154 inventoried file hashes, and all excerpts/full-file hashes for 14 pinned source files. Recomputed inventory totals: 154 files, 143 distinct content hashes, 20 AV matches, no exact c455/model-revision string match, no skipped selected files. Read the inventory selector: it is filename/suffix/size bounded and does not cover all local artifacts, other machines, cloud archives, or loaded runtime objects. The counts are not independent deployment observations. The source-backed capability map does not establish the selected attention backend or native compiled availability; Mega attention and MegaMoE must remain distinct.

Read the selected B200 base/profile/image/menu and historical effective-config evidence. Conflicting declaration levels and old ac9126/image3d176 provenance prevent transfer to the exact planned target. The stored d464 baseline node explicitly declares planned-only identity and has no AV setting. Its readonly receipt was inspected; this review does not rerun a canonical baseline query or infer runtime identity from absence of a string match.

## How to apply the outcome

“Do not enable AV just to make the optimization eligible” means do not silently change the evaluated baseline or attribute AV policy gains to copy elision. A separately justified AV activation/tuning investigation remains valid existing-family work. It should declare its changed policy, establish correct compatible startup/cost initialization, and compare the elision on/off with the same effective AV policy. Policy activation and same-step transfer elimination have different denominators and their estimated gains cannot be added without controls.

Next evidence is an existing exact-run receipt tying model revision, loaded image/source, effective V2/AV settings, attention/graph configuration and successful manager/cost initialization to each independently configured engine group. An eligible step proves existence only, not frequency or exposed cost. If AV is disabled on that fixed baseline, AV68 is inactive there. If it is unknown, neither inactivity nor a benefit is established. Stop additional generic searches or scalar fixtures for this specific readiness question until such evidence is available.

## Review operations

Read-only filesystem/source inspection and hash checks; no target imports, native/GPU execution, online queries, canonical mutations, or status/card changes. An initial shell read used the pinned-tree cwd for two campaign-relative files and failed; corrected absolute campaign cwd reads succeeded. A separate optional OPERATIONS.md lookup for a prepared canonical wrapper was absent and has no scientific bearing. All author originals remain unchanged.

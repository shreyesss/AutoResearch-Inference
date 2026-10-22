# Round74 — adaptive-verification activation evidence for AV68

**Result: activation remains unknown on the exact planned target. AV68 stays deferred; no new hypothesis, implementation qualification or service claim.**

The cheapest remaining check was retained deployment evidence, not another metadata simulation. The audit found no exact launch/runtime attestation for callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883` with `deepseek-ai/DeepSeek-V4.1-Flash-1017` revision `1bae0e1088993b9b82de08f59de5be5a34e42170`. This is a bounded local finding, not proof that adaptive verification is disabled or that no evidence exists elsewhere.

## What was inspected

`audit_retained.py` read 154 small UTF-8 metadata/configuration files, representing 143 distinct content hashes:

| Local scope | Files | Selection |
|---|---:|---|
| Current AutoResearch `configs/` | 59 | JSON/YAML/shell/text configuration |
| Retained B200 campaign configurations | 23 | JSON/YAML/shell/text configuration |
| Retained B200 AIPerf scores | 23 | `manifest.json` only |
| AutoResearch historical run directories | 47 | Runtime identity, launch, execution, checkpoint metadata, environment, deployment or effective-config filenames |
| skunk-work historical run directories | 2 | Same filename selection |

No selected file exceeded the 2 MiB bound; no raw datasets or profiler traces were reprocessed. Zero exact vLLM-pin matches and zero exact model-revision matches were found in this inventory; 20 files mentioned adaptive verification. The complete paths, hashes and search terms are retained in `retained-audit.json`. These are files, not 154 independent deployments.

The canonical baseline was separately read through SQLite `mode=ro`, without migration constructors. Its original node explicitly says **planned source profile only**, with image, loaded dependencies, graph distribution and timing unknown. It contains the expected model/source/topology, but no adaptive-verification setting. `baseline-readback.json` preserves that node unchanged. The campaign brief likewise distinguishes its plan from a verified running deployment. The local execution `.artifacts/` directory is absent in this checkout.

## Evidence disposition

| Retained evidence | Observed setting | Why it does not settle AV68 activation |
|---|---|---|
| B200 `configs/vllm/base.yaml` | `adaptive_verification: true` | A configuration declaration. The selected two-DEP4 profile separately declares `dspark_adaptive_verification: false`; effective precedence/launch is not established by this file alone. |
| B200 `latency-2xdep4-sla.yaml` | DSpark5 and AV false | Useful historical profile, not a c455/Flash1017 runtime attestation. Its image map identifies `ac9126e…` and image `3d17635…`. |
| B200 `experiments.yaml` | Both AV-true and AV-false speculative-config variants | An available experiment menu does not prove which variant ran. |
| Historical H200 `runtime-identity.json` and derived `effective-config-evidence.json` | Both replica argv contain `enable_adaptive_verification:false`; image `3d17635…` | Stronger evidence for that historical run, with a different image/model context. It cannot be transferred to the current planned target. Repeated handoff/launch copies are not new activation observations. |
| Baseline d464 and campaign brief | Exact desired source/model/topology; no effective AV setting | Planning evidence only. |

Older Mooncake/agent-75 service metrics remain useful for workload design. They do not establish AV activation, scheduled-draft frequency or exposed copy cost on this target. No old run was relabelled as current evidence.

## Exact source map: what would make the branch active?

The pinned source is sufficient to define the check, but cannot provide its runtime answer. Exact source excerpts, line numbers, fork URLs and full-file hashes are in `pinned-source-evidence.json`.

1. **Runner selection:** `VllmConfig.use_v2_model_runner` honors explicit environment selection, otherwise tests availability and unsupported features. `gpu_worker._make_model_runner` chooses V2 from that effective value. AV68 concerns the V2 `prepare_inputs` path, not merely a DSpark setting in an arbitrary runner.
2. **Requested AV:** `SpeculativeConfig.enable_adaptive_verification` defaults to **false**. The speculator copies this flag into `self.enable_adaptive_verification`; DSpark5 alone does not enable it.
3. **Confidence path:** DSpark selects the checkpoint confidence head when present and AV is enabled, otherwise the base speculator can instantiate the online acceptance estimator. The absence of a loaded confidence head is **not by itself proof AV is off**. The runner comment about clearing the flag without a head is not supported by the inspected DSpark assignment path; the actual code governs this audit. The estimator path additionally rejects local-argmax reduction when it cannot obtain draft logits.
4. **Manager construction:** `maybe_create_adaptive_verification_manager` returns `None` when the effective flag is false. If true, it checks target attention groups for CPU/device query-length mismatch support and variable-length graph support, including model-specific additional support. Unsupported combinations raise rather than establishing a usable active manager.
5. **Target backend capability:** the correct `deepseek_v41` selector makes Mega attention the conditional SM100 default when its implementation/topology is available, with FlashMLA fallback and explicit overrides. Mega inherits the V4.1 FlashMLA metadata builder with `ALWAYS` graph support; its SWA FlashMLA builder also declares `ALWAYS`. The generic non-SSM backend capability permits CPU/device query-length mismatch. This makes a compatible source path plausible; it does not attest the actual backend, compiled availability, graph mode or loaded image. MegaMoE EP4 and Mega attention are separate selections.
6. **Successful initialization:** the runner profiles initial AV costs when a manager exists; missing draft/verification cost curves cause an error. A successful AV-enabled startup record is stronger than a requested CLI flag alone.
7. **Per-step eligibility:** even with a manager, `prepare_inputs` uses it only when the scheduled-draft dictionary is nonempty. A nonempty dictionary with a chosen draft budget of zero is still the AV68 branch. Zero scheduled drafts or manager absence keeps the general copies.

The overwrite/data-consumer proof from round68 is not rerun here. The present check changes no integer selector, model semantics, graph or GPU operation.

## Minimal missing evidence and decision

Obtain an **existing launch/startup receipt for the exact evaluated run**, binding:

- loaded model revision and image-to-c455 source identity;
- effective V2 runner selection and effective speculative configuration;
- selected target backend/graph configuration and successful AV manager/cost-table initialization for each independently configured engine group.

An already-retained step record showing a nonempty scheduled-draft dictionary would then establish at least one AV68-eligible step. It would not establish its frequency or exposed latency. There is no request here to collect that record now, start a service, query a GPU or introduce production synchronization.

If the exact receipt shows AV disabled, AV68 is inactive for that baseline; do not enable AV just to make the optimization eligible. If it shows AV enabled and initialization succeeds, retain the source-backed proposal for the previously specified native differential and unchanged standard agent-75/Mooncake evaluation, when authorized. A measured benefit still requires the eligible-step frequency and exposed transfer/host cost. Unknown activation does not refute the source-level copy-elision premise.

**Outcome:** one existing AV68 readiness question remains unresolved due to a specific absent attestation. Zero new papers, provider calls, native/model/GPU operations, hypotheses, canonical writes, repository edits or service gains. The audit is complete; another generic search or repeated scalar fixture would not close this evidence gap.

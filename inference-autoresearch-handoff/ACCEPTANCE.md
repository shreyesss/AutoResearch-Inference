# Definition of ready

This checklist is for the implementation agents. The handoff itself does not satisfy these runtime checks.

## CPU/mock build complete

- [ ] Installable Python package and all eight CLI commands exist, with documented arguments and examples.
- [ ] Shared schemas/DTOs validate and serialize; unknown serving/workload overrides fail visibly.
- [ ] Agent 1 builds deterministic mock packs with stable hashes and deliberate shared/unique content; fake tokenizer is labeled, never used for real token claims.
- [ ] Agent 2 runtime/evaluator mocks prove lifecycle, lock, cleanup and failure accounting.
- [ ] Agent 3 runs a deterministic multi-proposal campaign and produces the expected empirical frontier from known fixtures.
- [ ] TTFT/TPOT formulas, units, reasoning/chunk alignment, valid tool-only outputs, missing metrics and eligible counts have meaningful tests.
- [ ] Every planned/dispatched request is accounted for; timed-out/unfinished slow work cannot disappear.
- [ ] Cache-off under a reuse-heavy workload is accepted as legitimate behavior; cache contamination is rejected separately.
- [ ] Overload, client dispatch lag, unsupported flags, startup OOM, correctness failure and valid regressions retain distinct reasons.
- [ ] Equivalent omitted/default flag configurations deduplicate; deliberate repeats remain possible.
- [ ] Exact/conditional/confirmed archive filtering handles directions, ties, unknown values and incomparable groups/stages.
- [ ] Resume neither duplicates a completed expensive trial nor imports stale runtime/model/traffic identities.
- [ ] Budget/timeout/cleanup checks do not leave a running mock or real server orphan.
- [ ] Report and raw data are reproducible and prominently identify mock runs.

## Real experimental setup ready

- [ ] Hardware identity is known; approximate 86 GB does not remain the sole hardware specification.
- [ ] Docker GPU and actual installed vLLM/AIPerf interfaces verified; image/model/tokenizer/template revisions locked.
- [ ] Chosen serving image supports Qwen3.8-27B, intended parsers and native MTP if proposed. No Flash-Next/MoE flags leak into the dense model config.
- [ ] Base fixed task settings boot with actual memory/graph/recurrent-state headroom. Precision is not silently changed to fit.
- [ ] Required output controls and total server-tokenized inputs verified with actual requests, including the document case.
- [ ] Cache reset/restart, execution warmup and intended prefix-only prewarm are tested on the hybrid model. Unsupported warm protocol is blocked explicitly.
- [ ] AIPerf real run yields raw records, measured timings, usage, schedule lag and complete accounting; adapter exports pass schema and independent spot checks.
- [ ] Baseline capacity calibration records achieved load, completion and stationarity evidence, or stops without guessing.
- [ ] Common absolute traffic schedules frozen; baseline and candidate share hashes and preparation protocol.
- [ ] One real candidate completes launch → smoke → measurement → drain → record → stop, with actual command/logs and cleanup evidence.
- [ ] Authenticated Codex proposal driver emits schema-valid JSON; failure is reported rather than replaced with random proposals. Proposer runs separately from the GPU server.
- [ ] A bounded real search evaluates at least several distinct feasible configurations and creates a report, even if no baseline improvement is found.
- [ ] At least baseline plus one promising/tradeoff candidate receive matched repeated confirmation if budget permits. Otherwise frontier is clearly provisional.
- [ ] Real results remain separate from mock fixtures, with no fake performance or global-optimum claim.

## Completion note required from coordinating agent

Provide changed files, commands actually executed, check results, locked versions, hardware manifest path, actual output paths, approximate evaluation cost, failed/unsupported cases and external blockers. Distinguish 'code implemented', 'mock tested', 'server smoke tested', 'real campaign run' and 'performance improvement confirmed'. These are different completion claims.

If no GPU/authentication is present, complete CPU/mock and all unaffected code. Supply a precise real-mode runbook and list which checks remain unexecuted. Do not label the real experimental setup ready on CPU success alone.


## v0.2 scientific readiness — required before real adaptive search

- [ ] Accessible source slices have schema/license/version/hash/coverage audit and reproducible characterization; unavailable data is blocked, not invented.
- [ ] Workload cards distinguish representative, diagnostic and stress roles; suite was not selected for candidate gains.
- [ ] Source-to-pack fidelity includes joint lengths, multi-scale arrivals, context evolution, tool gaps and reuse/cardinality, with transformations and missingness disclosed.
- [ ] Search/evaluation splits preserve complete sessions and guard shared identities/namespaces; holdout outcomes stay out of context.
- [ ] Mixed contention and session/reuse packs are defined from source evidence; semantic MTP content has provenance.
- [ ] Installed AIPerf text input/load inventory covers controls, aliases, defaults, units, conflicts, mapping and unsupported/deferred items.
- [ ] Forced/natural outputs and recorded/live/dependent protocols have separate contracts and group identities.
- [ ] Actual target requests/tokens, dispatch/lag, prefix construction and dependency timing match the frozen policy; live realized streams are recorded, not called identical.
- [ ] Baseline repeats establish noise/drift; pilot contrasts, controls and a few interactions have fixed plans and recorded costs.
- [ ] Axis×regime classification uses resolved changes, metric uncertainty and diagnostic availability. Flatness/inconclusiveness is preserved.
- [ ] Matching QualificationReport authorizes search only with validated traffic, B0 and at least one plausible reproducible effect. Mock/stale evidence cannot unlock real search.
- [ ] Diagnostic retrieval is read-only/scoped; active profiles are optional, locked, budgeted and separate from timed cells.
- [ ] Hypothesis/exploration, predictions, falsification, structured feedback and supported/contradicted/unresolved interpretation persist across resume.
- [ ] Raw ledger, stable procedural skill and evidence-backed scoped lessons are distinct; external priors/cross-run memory are explicit settings.
- [ ] Reports include per-class mixed-workload tails, actual offered/realized load, negative results, qualification status, costs and provenance.

A closed scientific gate does not invalidate independently completed code. A setup may be mock-complete or real-measurement-ready while sensitivity qualification remains blocked/flat/inconclusive. These statuses must be reported separately. The older real-campaign checklist applies only after this gate permits search.

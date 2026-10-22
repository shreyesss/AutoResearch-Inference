# Anonymous skill-output review

Judgments frozen before version-label disclosure. The evaluator read the previously frozen case packets/rubric and anonymous per-case A/B outputs only; it did not read the arm map, original output folders or after skills. Roles share a filesystem, so blinding is procedural rather than access-enforced.

## Result

| Case | A / 12 | B / 12 | Judgment |
| --- | ---: | ---: | --- |
| D00 | 10 | 12 | B clearer |
| H01 | 12 | 12 | Tie |
| H02 | 12 | 12 | Tie |
| H03 | 12 | 12 | Tie |

**No critical failure was found in any output.** Three held-out synthetic cases are ties on the frozen rubric. D00, the known development anchor, favors B for clearer experimental contrasts and less ambiguous policy wording. This is not evidence of general quality improvement.

## Criterion-level evidence

Each dimension is scored 0–2 under the frozen rubric; totals summarize observations, not success probabilities. All quoted excerpts below were checked against the retained output bytes.

### D00

B more clearly separates shared policy interface and matched-budget versus tuned-deployment contrasts. Neither output has a critical failure; A contains ambiguous predetermined-tree wording, not proven implementation error.

#### A: 10/12; critical failures: none

- **task_fidelity: 2/2.** “Implement and compare both fixed-tree and calibrated best-first policies even if fixed-tree loses.” — Preserves required policies, checkpoint override, sole benchmark and no separate ROI campaign.
- **mechanism_and_baseline_delta: 1/2.** “Required policy A builds a frozen, predetermined tree using these available positions.” — Useful five-position adaptation, but wording blurs freezing an inference policy with a predetermined tree; candidate construction dependencies remain insufficiently specified. This ambiguity is not treated as demonstrated implementation error.
- **evidence_transfer: 2/2.** “do not copy the Qwen seven-position configuration or infer its performance transfers.” — Separates inference-only reuse, optional source training and nontransferable external results.
- **cross_evidence_synthesis: 2/2.** “Physical preceding positions cannot represent branch ancestry merely by adding a tree attention mask.” — Uses source model-state limitation to alter verifier/ancestry design.
- **discriminating_evaluation: 1/2.** “Include matched native target-only and native chain controls alongside both complete policies in each comparison” — Includes controls, correctness, timing and fitting split, but does not separate matched-budget policy attribution from equally tuned final deployment comparison; that matters for interpreting the two methods.
- **memory_and_uncertainty: 2/2.** “Neither repeatability nor exactness is currently established.” — Unknown identity/runtime/correctness remains explicit; historical unsuffixed scope superseded without claiming runs.

#### B: 12/12; critical failures: none

- **task_fidelity: 2/2.** “No separate baseline or ROI campaign precedes implementation; native controls belong inside comparisons.” — Follows user overrides and both required policies without a speedup prerequisite.
- **mechanism_and_baseline_delta: 2/2.** “Implement a fixed-tree policy and a separate best-first policy over the same supported candidate representation.” — Separates shared integration and policy changes; freezes neural weights while permitting local scalars.
- **evidence_transfer: 2/2.** “The reported trained package's results do not establish this adaptation's benefit.” — Rejects transferring combined-training gains or seven-position settings.
- **cross_evidence_synthesis: 2/2.** “Native Engram hashes use physical preceding positions, so a tree mask alone cannot make the layout safe” — Integrates tree proposal design and native ancestry restriction into a concrete correctness dependency.
- **discriminating_evaluation: 2/2.** “Compare independently tuned configurations for deployment benefit; equal candidate/node budgets can separately test selection quality.” — Defines distinct scientific contrasts, construction-inclusive timing, matched controls and calibration separation.
- **memory_and_uncertainty: 2/2.** “failure of native repeatability requires diagnosis, not a tree speedup claim.” — Preserves unresolved baseline validity and forbids claimed execution/benefit.

### H01

Both actionable and cautious. A uniquely checks admission-time availability; B uniquely warns logged queue state is endogenous under changed routing. Neither consistently dominates.

#### A: 12/12; critical failures: none

- **task_fidelity: 2/2.** “frozen weights, CPU design only; no fixed ROI floor.” — Honors scope and optional novelty/ROI.
- **mechanism_and_baseline_delta: 2/2.** “The intervention replaces the router's fixed overload-spill decision, not the coupled DP/EP execution within each engine.” — Identifies changed decision and correct independent-engine boundary.
- **evidence_transfer: 2/2.** “Omit training; do not present the proxy as an equivalent predictor or import the reported +22%” — Reuses policy interface without treating missing learned predictor as either mandatory or magically reproduced.
- **cross_evidence_synthesis: 2/2.** “Prefix-hit information is usable at admission only if actually available then” — Combines recorded-hit evidence with actionable signal-availability constraint; accounts for alternate-cache uncertainty.
- **discriminating_evaluation: 2/2.** “Decisions changing across unsupported service assumptions make the result inconclusive.” — Provides bounded replay, counterfactual limits, decision branches and existing matched service evaluator.
- **memory_and_uncertainty: 2/2.** “an additional “new cache placement” card would duplicate that lead and overstate readiness” — Revises prior hypothesis on new data without duplicating it or resolving absent eviction evidence.

#### B: 12/12; critical failures: none

- **task_fidelity: 2/2.** “No minimum ROI or performance forecast is imposed.” — Stays CPU-only and useful-method rather than novelty-gated.
- **mechanism_and_baseline_delta: 2/2.** “Treat each four-GPU engine as a destination; its four coupled DP/EP ranks are not four independent servers” — Correct routing unit and existing affinity/spill comparator.
- **evidence_transfer: 2/2.** “Prompt length minus observed hit-prefix length supplies an uncached-prompt-work proxy, not measured service time.” — Separates policy from training and acknowledges proxy limits.
- **cross_evidence_synthesis: 2/2.** “Do not recursively treat recorded queue occupancy as the state that a changed routing policy would have produced.” — Connects changed routing to endogenous queue observations; avoids invalid replay interpretation.
- **discriminating_evaluation: 2/2.** “If choices reverse under unmeasured decode/cache assumptions, return inconclusive” — Specifies actionable falsification and eventual existing evaluator without simulated performance claims.
- **memory_and_uncertainty: 2/2.** “justify a separate duplicate cache-placement candidate” — Explicitly denies duplicate proposal and preserves missing data and limited evidence coverage.

### H02

Both isolate byte-preserving compaction, preserve quantization rejection, check graph/read lifetimes and refuse to infer joint savings. Different emphases are complementary.

#### A: 12/12; critical failures: none

- **task_fidelity: 2/2.** “Do not reopen the prior four-bit quantization proposal.” — Preserves exact-equivalence and frozen-weight task while permitting a distinct component adaptation.
- **mechanism_and_baseline_delta: 2/2.** “Isolate CACHE-Q's independent page manager: move live cache data without changing bytes and update logical-to-physical indirection” — Identifies byte-preserving component and incremental opportunity beyond paging.
- **evidence_transfer: 2/2.** “the reported 35% combines quantization and compaction and cannot be assigned to page management” — Does not transfer combined-method gain or aggregate accuracy into losslessness.
- **cross_evidence_synthesis: 2/2.** “If graph references cannot safely be refreshed, restrict the eligible pages or defer compaction.” — Combines relocation quiescence precondition with current graph/concurrency behavior.
- **discriminating_evaluation: 2/2.** “Stop if existing allocation already achieves the same releasable-page count, or no pages can move safely” — Supplies existing replay, ownership/state checks, falsifier and missing-data inconclusive branch.
- **memory_and_uncertainty: 2/2.** “trace replay tests those properties on the supplied events.” — Limits CPU evidence, retains original rejection, and explicitly rejects finite-token-test proof.

#### B: 12/12; critical failures: none

- **task_fidelity: 2/2.** “There is no new evidence warranting reopening that same quantization proposal.” — Honors original exact-correctness constraint and limits hypothesis count.
- **mechanism_and_baseline_delta: 2/2.** “Reuse packing plus indirection; omit four-bit encoding, learned clipping thresholds and residual-window handling.” — Clear separable component selection and unchanged logical-value contract.
- **evidence_transfer: 2/2.** “Do not infer attention runtime, tensor values or a compaction share of the joint 35% claim” — Avoids partial-method gain attribution and unsupported tensor evidence.
- **cross_evidence_synthesis: 2/2.** “A graph captured with a stale pointer cannot be made safe merely by updating a separate table.” — Combines source precondition with actual runtime hazard, rather than superficial method borrowing.
- **discriminating_evaluation: 2/2.** “moving whole pages without reducing live physical allocations is not a KV-memory improvement.” — Chooses relevant measured quantity, checks baseline incrementality and gives clear advance/stop/defer outcomes.
- **memory_and_uncertainty: 2/2.** “Finite agreement cannot prove exact equivalence for all inputs” — Maintains uncertainty and limits simulated/finite evidence correctly.

### H03

Both correctly identify installed-but-disabled callback activation, weak indirect TTFT pathway, unsupported SM100 port and startup-error semantics. No meaningful rank difference.

#### A: 12/12; critical failures: none

- **task_fidelity: 2/2.** “Do not install packages, change the service or launch traffic now.” — Stays inside CPU/source-only scope and current p99 TTFT objective.
- **mechanism_and_baseline_delta: 2/2.** “The callback occurs after completion, so its own request's first token cannot directly benefit” — Identifies installed-but-disabled activation and only plausible indirect TTFT mechanism.
- **evidence_transfer: 2/2.** “If the timing instead covers an entire batch, attribution differs; its denominator must be clarified.” — Handles component saving units and denominator ambiguity without service forecast; rejects SM100 direct transfer.
- **cross_evidence_synthesis: 2/2.** “Staging package availability changes feasibility, but does not prove serving-image compatibility” — Combines new environment evidence with prior startup error and current deployability.
- **discriminating_evaluation: 2/2.** “Stop pursuing FAST-C for this objective if inspection establishes isolation from TTFT-relevant resources” — Gives dependency/source falsifier and later matched off/on comparison with missing first-token observables.
- **memory_and_uncertainty: 2/2.** “not a negative serving result: there was no traffic or performance measurement.” — Keeps startup error distinct from scientific invalidation and unknown local timing.

#### B: 12/12; critical failures: none

- **task_fidelity: 2/2.** “No GPU execution or service changes occurred.” — States no execution and remains within CPU/source-only planning scope throughout.
- **mechanism_and_baseline_delta: 2/2.** “a configuration/integration intervention, not a missing-code optimization” — Correct active-baseline delta and indirect future-request TTFT pathway.
- **evidence_transfer: 2/2.** “Do not infer equivalent invocation frequency, batch occupancy or exposed savings in this deployment.” — No source percentage transfer; explicit SM100 incompatibility and conditional arithmetic.
- **cross_evidence_synthesis: 2/2.** “Compare the staging package version/ABI requirements with the serving image manifest using existing records; change neither environment.” — Turns prior error plus staging availability into a narrow feasible source/identity check.
- **discriminating_evaluation: 2/2.** “Shared-resource code paths support requesting targeted CPU scheduling/callback traces; they do not establish material contention.” — Names missing discriminator and existing-record coverage gap with stop/inconclusive criteria.
- **memory_and_uncertainty: 2/2.** “It is an execution error and supplies no negative performance result” — Preserves historical outcome and service-evidence limits.

## Practical usefulness and limits

Both versions propose useful next checks: branch-local Engram ancestry and exactness before interpreting tree timings; queue-policy reuse with missing duration/eviction uncertainty retained; allocator compaction isolated from disallowed quantization; and callback source/dependency checks before claiming TTFT relevance. These are planned actions. No retrieved paper, executable replay, verified command, implementation, model forward pass or GPU benchmark was produced by this evaluation.

No exact shell commands are validated by these packets. The practical result is a set of reasonable source-inspection questions, comparison designs and stop/inconclusive branches, not an execution-ready artifact. Missing baseline/source identities remain legitimate limits. Both arms respect the supplied scope override without demanding numerical ROI before planning.

D00 A’s “frozen, predetermined tree” is treated as an ambiguity in describing method reuse, not proof that an incorrect tree algorithm was implemented. Its score difference is also supported by the missing distinction between matched-budget policy comparison and tuned deployment comparison. D00 B states that distinction. Neither D00 arm actually implemented either policy.

For H01, A checks whether observed cache-hit information exists at admission; B checks that recorded queue states cannot be recursively reused as counterfactual states after changed routing. These are complementary strengths and do not justify claiming a winner. H02 and H03 likewise have different emphases but no meaningful difference under the frozen rubric.

Ceiling effects are visible: both versions satisfy all six criteria on the three held-out fixtures. A harder follow-up should use incomplete/conflicting full source artifacts and actual bounded retrieval, then test whether plans survive code inspection. The current fixtures cannot certify that ability. If these cases inform another skill revision they become development cases; they cannot remain a fresh held-out test.

Only one generation per arm was collected. Each generator handled four cases in a shared context, so cases and outputs are not independent samples. D00 is explicitly the development example; H01–H03 are synthetic engineering fixtures. No p-values, reliability claim or general improvement percentage is warranted. The richer skill package, if any, cannot be causally isolated from normal generation variation by this sample alone.

`scores.json` preserves criterion-level scores, exact output quotations, artifact hashes and these limits. Version labels must be revealed only after this report and score file are retained.

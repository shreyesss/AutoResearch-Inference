# Root review: SN98 is a distinct deferred verifier experiment

The proposal survives source and mathematical review as a deferred research
direction. It is not an implementation-qualified change or evidence of lower
ITL. Removing mandatory ratio-test inputs while retaining that test would be
wrong; replacing the whole verifier with a separately justified coupling is a
different, coherent experiment. The inspected pinned source does not implement
this proposed mode.

## Supported mechanism and limits

The inspected paper gives the shared-clock single-sample component and a batched
target verification scheme. Its multi-draft topology, top-k target truncation,
watermark machinery and donor timings are unnecessary and are correctly
excluded. Full target logits remain. The author distinguishes one sample per
context from native draft depth five, and its position-tape adaptation from
the paper's independent-context theorem.

`POSITION_TAPE_ARGUMENT.md` states a sufficient pathwise construction and its
assumptions. The author's finite ternary controls exercise proposed contexts,
including incorrect descendants, and three admission policies. They do not
prove continuous sampling or native state management. The separate round99
coin control establishes that selectively discarding previously inspected noise
can be biased; it does not diagnose a current DSpark failure.

Native source confirms two concrete integration hazards: cache presence changes
speculative-step seed mixing, and `draft_logits is None` selects greedy
proposal generation. Shared-noise mode needs an explicit sampling/verifier
contract; deleting a buffer or removing a salt globally is insufficient.
The unchanged confidence head and AV policy may predict the wrong new acceptance
behavior even if the new decoder's target law is correct.

## Additional runner seam and consumer boundary

The hash-verified c455 `model_runner.py` provides an existing interface seam:
`model_state.custom_sampler(self.sampler)` can supply a sampler/rejection-sampler
pair. This is a source hook, not a deployed plugin or a promise that no runner
patch is required. An explicit guarded verifier mode must preserve the normal
no-draft branch and the same `SamplerOutput` contract.

The runner applies grammar masks and derives invalid-draft metadata before the
verifier call, passes persistent `draft_logits`, and consumes `num_sampled` and
`num_rejected` in postprocessing and `observe_verification`. A new implementation
must preserve row/count semantics, request-state updates and invalid-draft
handling, or explicitly use the old path for unsupported modes. Keep early
output-copy sequencing intact. A search of worker references and bounded runner
reads is not a completed audit of every cache consumer or every model hook.

Independent adversarial review sharpens that fallback condition: eligibility
established from the committed prefix before inspecting future tape can select
a separate mode. A late decision based on sampled invalid drafts, AV or other
noise-dependent conditions cannot simply discard the tape and invoke native
independent sampling. Use target-only same-tape correction at the current prefix
or establish a different valid conditional law. Otherwise the round99 selection
bias can reappear inside an apparently conservative fallback.

## Adversarial progress and evaluation

Shared-exponential coupling is not universally maximal. The explicit one-token
example yields agreement18/35 versus3/5, with expected progress53/35 versus8/5.
The required complete-round cost ratio is below53/56 in that toy setting. This
cannot be substituted for native five-token block progress. More per-row target
noise generation can consume the removed statistics/residual savings, and lower
progress can increase expensive target rounds.

Keep this behind narrower same-law optimizations such as FV86 until its stable
position/seed adapter, processor lifecycle and progress/cost evidence are
concrete. That ordering reflects integration uncertainty, not a measured speedup
ranking. Compare the strongest compatible baseline, with C025/FV86 separately
identified; do not add their claimed savings to an alternative verifier that
removes or changes the same work.

The existing Mooncake and agent-p75 workloads remain the serving comparisons.
They cannot by themselves certify the new coupling/cache lifecycle, so an
additional scoped target-only-oracle differential is justified. Its outcome
would establish a correctness contract, not a throughput win. No GPU work,
native build, model import or implementation is authorized by this review.

## Verification receipt

All50 frozen author files verified;13 exact quotations occur in the identified
source revisions;7 copied target files match the verified source archive. The
additional runner copy also matches the archive. Source reads were bounded to
the named mechanisms; no whole-codebase audit is claimed. The initial local
verification script assumed revision documents were dictionaries and failed
with a TypeError; it was corrected to parse serialized JSON and then passed.
No research data or original author packet was changed. The author CPU oracle
was read, not rerun to inflate a test count.

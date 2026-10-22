# Evidence-backed lessons from rounds 29–30

Read-only recommendation; no repository changes, provider calls, canonical mutations or new experiments. Existing discovery, research, critic skills, synthesis reference, methodology and ROI guidance were read. They already cover semantic query authorship, provider failure versus empty results, partial reuse, provenance, current-path exposure and CPU scope. Do not add another generic checklist or orchestration layer.

## 1. Worth a small skill refinement: identify the earlier consumer

**Evidence:** round30 first found a superficially matching producer sequence: target stores P, rescales O, then signals SO readiness; donor #5602 publishes P before rescaling O. Reading target consumers reversed the apparent positive: QK already independently polls its readiness, while the sole SV consumer still needs both P and rescaled O. Splitting the notification alone changes no useful readiness condition. Round29 similarly exposed a subtle negative: adding quantization to the n<=8 input epilogue delays release of the side coefficient stream; n9–16 has different enqueue order. The useful distinction was exact producer/consumer event ordering, not another GPU-optimization keyword.

**Gap in current instructions:** synthesis.md asks for ordering/ownership and the ROI skill asks for exposed time, but neither explicitly requires naming the consumer newly unblocked by a synchronization/publication change. The missing question caused an initially promising interpretation that later source inspection reversed. Existing source/oracle guidance is broad enough to permit the right audit, so this is a narrow emphasis improvement, not missing framework functionality.

**Suggested addition (two sentences in synthesis.md under Connection, or critic—not both):**

> For an overlap, readiness or staging change, identify the producer event, every affected consumer, and the first useful operation that can start earlier; compare with the target's existing independent issue/polling path. Preserve accumulator and buffer-reuse dependencies, and account separately for branches where the proposed event is absent or the producer already overlaps work.

This helps distinguish a true dependency removal from renaming/splitting the same conjunction. It does not demand a simulated timing model. Source evidence can reject the proposed shortcut or leave a broader redesign open.

**Verification scope:** existing round29/30 cases are field examples supporting usefulness, not controlled proof that edited wording improves future hypothesis yield. A small regression replay can ask the agent to identify earlier consumers from frozen snippets under unchanged criteria; retain both outputs if evaluating the wording. Do not invent a benchmark score from this review.

## 2. Worth a small CLI usability repair: safe local validation error

**Observed failure:** `researchctl --local-only --defer-snapshot init` failed before state initialization with generic ValueError text. Two subsequent commands failed as state_not_initialized. The actual reason was a known local flag restriction, but main() intentionally masks all exception text to protect credential-bearing provider URLs. Resolving it required reading foundation.py841–842 rather than following a useful error message. Exact round30 operational-errors.json and journal distinguish the failed initialization from real provider requests.

**Minimal suggestion:** a specific, safe validation exception/error code for unsupported defer combinations, with a fixed constant message saying the command cannot defer checkpoints and to remove `--defer-snapshot`. Preserve redaction of arbitrary ValueError/provider messages; do not print raw exception text or user input. The shared invoke path should remain the source of truth so CLI and tool callers receive compatible classification. No need to change what is allowed or to make init silently defer snapshots.

**Meaningful checks:** unsupported init/refresh usage returns the safe code before creating/changing state; supported paper-search still retains defer behavior; a deliberately secret-bearing unrelated ValueError remains redacted. This fix saves diagnosis friction; it is not a scientific-yield claim.

## 3. No changes justified by these rounds

- arXiv429 was correctly retained as failure. Explicit provider switch succeeded; do not add unbounded retry or automatic semantic broadening.
- The author-repository investigate failure was retained and a pinned source-only fetch recovered useful code. Need more diagnosis before proposing repository fallback logic; one RuntimeError alone does not justify automatically selecting different repositories.
- All-page compact recall worked:138 cards/five pages/stable hash. No further recall surface change needed here.
- PR operation-vocabulary triangulation worked and revealed both a donor and contrary evidence. Existing skill already requires this step; do not add another search agent/harness.
- No new numerical ROI requirement: unknown target rescale frequency and reference cost correctly keep reduction-only work deferred. A stricter universal gate would discard useful selective reuse rather than improve it.

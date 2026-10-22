# Bounded external review

Review type: delegated, separate review of the supplied synthetic cases. Evidence: `inputs/cases.json` is the stipulated inspected source; `inputs/control-skill.md` supplies the review method. General workflow, methodology, ROI and evaluation-gating documents were read only as process guidance. No actual deployment or timing evidence was inspected.

For an eligible observation, omitted rows are `m-1` if `a=m>=2`, otherwise zero, with `0<=a<=m<=s<=5`. The quantities below are counterfactual opportunities if the proposed shortcut is applied. They are not measured savings. Added flag work has unknown duration.

| Case | Tight total omitted-row range | What existing records establish | Numerical latency or promotion claim? |
|---|---:|---|---|
| paired | 8–9 over four observations | Two full-length acceptances force eight rows; one shorter acceptance may add one | No |
| summary | 12–34 over ten observations | Aggregate acceptance plus the cap forces a positive lower bound | No |
| mixed_modes | 0–9 over four observations | Eligibility is unknown; all observations may be ineligible | No |
| latency | Exactly 4 for one observation | 2,068,480 logical bytes of omitted row work | No |

## Paired

Eligibility is stipulated. Each `a=s=5` forces `m=5` and removes four rows. The `a=2` observation removes one row only if `m=2`; larger admitted counts remove zero. The `a=1` observation always removes zero. Thus the per-observation bounds are `[4,4], [4,4], [0,1], [0,0]`, summing to **8–9**. Feasible admitted counts `[5,5,3,1]` and `[5,5,2,1]` attain the two endpoints.

The strongest support is the forced eight-row opportunity. The unresolved admitted count changes the total by only one row, while missing time evidence prevents a value claim. Cheapest next action: enumerate the feasible counts on CPU, as completed here. An already retained admitted-count record for the third observation would resolve the residual ambiguity; none is supplied and no new collection is authorized. Advance the arithmetic finding; defer performance promotion.

## Summary

Ten observations could accept at most 50 drafts. The total 43 leaves only seven missing acceptances. Every observation with `a<5` consumes at least one of these seven, so at least three observations must have `a=5`; they also have `m=5`. They force **12** omitted rows. The lower endpoint is attained by accepted counts `[4,4,4,4,4,4,4,5,5,5]` with all admitted counts five.

For the upper endpoint, each positive-acceptance observation contributes at most `a-1`. At least nine observations must have positive acceptance to sum to 43 under the cap five. Hence the total cannot exceed `43-9=34`. Accepted and admitted counts both `[0,3,5,5,5,5,5,5,5,5]` attain **34**. No missing denominator was inferred from the metric: the count of observations and cap are provided explicitly.

The strongest support is that an aggregate can still force opportunity. The strongest limitation is that the same total permits both endpoint constructions; the 86% aggregate acceptance ratio is neither shortcut frequency nor speedup. Cheapest next action: finite CPU feasibility arithmetic, completed here. Retain **12–34** rather than demand an unavailable histogram before drawing any conclusion. Already retained paired counts, if later available, could narrow it. Advance this diagnostic finding; defer promotion.

## Mixed modes

Even though `a=s=5` still forces `m=5`, it does not establish the eligible nongreedy full-probability branch. Every observation could be ineligible, yielding **zero** omitted rows. If every observation is eligible and admitted counts are `[5,5,2,1]`, the total is **nine**. Thus the unconditional tight bound is **0–9**; **8–9** applies only under the additional all-eligible assumption.

The strongest competing explanation is that synthetic acceptance or another ineligible mode produced the counts. Cheapest next action: enumerate eligibility alongside the count constraints, completed here. Already retained mode provenance is the observation that could change this conclusion; the fixture supplies none. Stop at the unconditional bound and defer an activation claim. Counts alone cannot recover the mode.

## Latency

The complete eligible observation forces **four** omitted rows. At 517,120 logical bytes per row, this is **2,068,480 logical bytes**, or **1.97265625 MiB**. This is logical accounting. It does not establish physical memory traffic, measured kernel duration, bandwidth savings or client-visible time.

No measured kernel time, exposed critical-path contribution, added flag duration, representative opportunity frequency, or service latency is supplied. Unchanged or worse latency remains compatible with these facts. A numerical ITL improvement, a latency percentage, a cost saving and promotion are unsupported. Preserve the useful mechanism hypothesis without calling unknown ROI a disproof.

The cheapest authorized next action is the row/byte calculation and a precise missing-input diagnosis, completed here. Existing matched timing artifacts could later resolve net component saving after flag overhead and overlap; service qualification would additionally need matched workload, useful output progress, correctness and the intended service metric. None is provided. Defer measurement and promotion; this task authorizes no GPU work or new data collection.

## Verification and limits

A Python standard-library enumeration checked every feasible admitted-count combination for the paired case, every eligibility assignment for mixed modes, and every sorted ten-value accepted histogram summing to 43 for the summary. Sorting is sufficient because the observations share the same cap and eligibility and total omitted rows is permutation invariant. Each histogram's extrema were computed over all feasible admitted counts. Assertions checked all four numerical results. This validates the finite arithmetic under the stipulated contract; it does not execute the native shortcut or establish correctness or performance on a serving system.

No new data was collected, no network, GPU, model import or compilation was used, and no canonical research state was written. The fixture artifacts retain this review; they do not update a hypothesis ledger. Further retrieval is unnecessary within this closed evidence scope. Reopen bounds only for supplied admitted/mode data, and reopen latency/promotion only for suitable timing and service evidence under separate execution authority.

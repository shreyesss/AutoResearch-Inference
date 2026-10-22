# Block-verifier shortcut review

Review type: delegated, separate review. This is a bounded synthetic decision exercise. The copied `inputs/treatment-skill.md` supplies review guidance; `inputs/cases.json` is the sole source of case evidence. General workflow, methodology, ROI and evaluation-gating documents were read as guidance. No independent source or deployment validation is claimed.

For an eligible observation define omitted rows as `r=(m-1)` when `a=m>=2`, and zero otherwise. For ineligible observations `r=0`. All bounds below are tight over the supplied integer constraints and apply only to the indicated fixture population.

| Case | Potential omitted rows | Latency or promotion supported? |
| --- | ---: | --- |
| paired | 8–9 over four observations | No |
| summary | 12–34 over ten observations | No |
| mixed_modes | 0–9 over four observations | No |
| latency | Exactly 4 in one observation | No |

## paired

Accepted=scheduled=5 forces admitted=5 in the first two observations, so each omits four rows. Accepted=2 permits admitted=2 (one row) or 3..5 (zero). Accepted=1 can never omit a row. Endpoints are attained with admitted [5,5,3,1] and [5,5,2,1].

Strongest support: At least eight omitted rows are forced without an admitted-count counter.

Strongest objection: Row opportunity does not reveal exposed cost or flag overhead; net service benefit could be absent or negative.

Cheapest next action: Retain the tight bound from existing inputs; the CPU enumeration has verified it. Do not request an admitted counter merely to reconfirm the two forced full-admission events. Stop within the supplied evidence scope and defer performance promotion.

What changes the decision: Existing admitted detail could settle only the remaining one-row uncertainty, if that mattered to a future decision. A future authorized exposed-cost and overhead comparison is needed for service value.

Verdict: advance opportunity reasoning; defer performance promotion.

## summary

If k observations accept five, total accepted is at most 5k+4(10-k)=40+k; therefore k>=3, forcing at least 12 omitted rows. This minimum is attained by accepted [5,5,5,4,4,4,4,4,4,4], with admitted=5 throughout. For the upper bound, each positive accepted count contributes at most accepted-1; 43 accepted drafts require at least ceil(43/5)=9 positive observations, hence at most 43-9=34 rows. This is attained by eight accepted counts of five, one of three, and one of zero, with admitted=accepted.

Strongest support: The aggregate alone forces at least three fully accepted five-draft observations and a positive lower opportunity bound.

Strongest objection: The acceptance total does not identify the histogram or admitted counts; it cannot justify treating 43/50 as full-block frequency or latency gain.

Cheapest next action: Use the tight [12,34] range, already checked by finite CPU dynamic programming. No new histogram or counter is needed to establish positive opportunity. Stop after recording uncertainty; defer service promotion.

What changes the decision: Retained per-observation data could narrow the range if a future exposed-cost decision depends on it; unavailable data is not authorization to collect more.

Verdict: advance bounded opportunity reasoning; defer performance promotion.

## mixed_modes

The first two observations force admitted=5, but all observations could be ineligible, giving zero. If all are eligible and admitted=[5,5,2,1], nine rows are possible. Thus [0,9] is tight. The endpoints do not imply every intermediate integer is attainable.

Strongest support: There is a nine-row conditional ceiling and two forced full-admission events.

Strongest objection: Full admission does not establish eligible-mode execution; synthetic acceptance or other modes may explain all records.

Cheapest next action: Record [0,9] and defer activation/value claims. Mode provenance would be the cheapest discriminator if already retained, but the fixture provides none and disallows new collection. Do not request an admitted counter first or treat an engine label as per-observation path evidence.

What changes the decision: Verified eligible-path attribution of either five-accepted observation would establish at least four omitted rows. Proven ineligibility of all observations gives zero. Unresolved mode keeps the lower bound at zero.

Verdict: defer pending eligibility evidence; not disproven.

## latency

The shortcut omits 5-1=4 rows, corresponding to 4*517120=2068480 logical bytes. No kernel duration, physical memory-traffic measurement, usable bandwidth, exposure, service baseline, or overhead duration is provided.

Strongest support: Mechanism activation and logical work reduction are exact for this one synthetic observation.

Strongest objection: Logical bytes are not elapsed time or necessarily avoided device traffic; overlap, implementation effects, and added flag work can erase or reverse a time benefit.

Cheapest next action: Retain the exact four-row and logical-byte result; explicitly leave numerical ITL change unknown and defer promotion. No new timing collection is authorized. A future authorized component comparison would need matched correctness and net exposed savings; service promotion additionally needs matched service evidence under a frozen objective.

What changes the decision: Positive exposed savings after all overhead would support further evaluation, not certify ITL. Nonpositive net savings would reject a speedup claim for that condition. Missing timing remains inconclusive.

Verdict: defer performance promotion; reject the current numerical ITL inference.

## Assumptions and limits

The scheduled, admitted and accepted counters refer to the same verification observation and count draft tokens consistently. Eligibility is stipulated only where explicitly given. No assumption connects scheduled count to admitted count beyond the supplied inequalities. These are potential omission counts under the proposal, not measured savings or evidence that a candidate implementation preserves correctness.

The paired and summary cases establish positive opportunity without requiring new counters. Their populations differ, so their totals are not a ranking of deployment value. Mixed modes has unresolved applicability; the complete latency case has known opportunity and unresolved time value. The strongest competing explanation for no speedup is that removed work is cheap or hidden while added flag work consumes the potential gain.

A time model would require net exposed critical-path savings per eligible event, event frequency in a defined workload, added overhead on all affected calls, useful output progress and a comparable baseline. These values are unknown. No nontrivial numerical time bound follows from rows or logical bytes, and even the sign of net service benefit is unknown. Acceptance fractions cannot supply the missing timing or useful-output denominator. No ITL tail, throughput, capacity or cost conclusion is supported.

The existing stipulated contract plus a stdlib finite enumeration/dynamic program is the sufficient evaluator for this bounded arithmetic question. It exhaustively checks allowed admitted counts for the paired records and reachable (accepted-total, omitted-total) states for the summary. It does not model GPU execution, correctness, or service behavior. Missing eligibility and timing cannot be recovered by arithmetic. No specific installed serving evaluator was inspected or claimed to cover them.

Execution stopped after the permitted arithmetic and artifact writing. There was no GPU work, model import, native compilation, network access, new data collection, live-state inspection or canonical ledger write. The outputs are a local review record; they do not update a hypothesis ledger or authorize an experiment. Reopen only with relevant eligibility or cost evidence and appropriate execution authorization.

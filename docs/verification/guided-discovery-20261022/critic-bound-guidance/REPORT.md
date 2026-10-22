# Critic guidance comparison — existing counters

## Outcome

**No demonstrated improvement; leave the production skill unchanged.** Both
independent fresh-agent passes solved all four fixed synthetic cases and declined
unsupported latency/promotion claims. Adding another paragraph would duplicate
behavior already demonstrated here. This result is about these cases only, not
proof that the existing skill always reasons correctly.

## Design and controls

Before either response, the parent froze four raw cases, arithmetic expectations,
and two copied versions of the same inference-critic skill. The treatment adds
one paragraph encouraging useful bounds from non-identifying counters, explicit
mapping/population/eligibility assumptions, and avoiding redundant measurements.
The control is byte-identical to the production skill. No implementation or
production skill was edited.

Two separate fresh-context subagents received identical task/evidence and their
assigned skill copy. They used the inherited model settings with no overrides,
ran sequentially, and could read the same general repository guidance. Neither
was given expected answers, the other skill/output, or the preceding round94
reports. The parent froze criteria before responses, then judged the visible
outputs; the parent judge was not blinded. There was one response per arm, no
retry/tuning to the cases, and no statistical effect-size claim.

The fixture stipulates the source/count contract and branch facts. It tests
conditional decision reasoning, not the ability to discover a missing mapping
in a real codebase, retrieve papers, judge model quality or demonstrate serving
benefit. Both agents used stdlib arithmetic; neither performed GPU/native/model
execution, network requests, new data collection or canonical writes. Their
command logs retain the executed reads and summarized inline calculations; they
are not an independent replay of native behavior.

## Observed decisions

| Case | Frozen expected omitted-row bound | Current skill | Proposed paragraph |
|---|---|---|---|
| Four eligible paired observations |8–9|Correct|Correct|
| Ten eligible observations,43 accepted drafts |12–34|Correct|Correct|
| Same paired counts, modes unobserved |0–9|Correct|Correct|
| One known complete five-draft observation |4|Correct|Correct|

Both also computed2,068,480 logical bytes for the final case, without turning it
into physical traffic or ITL. Both treated N as verification observations, kept
unverified mode eligibility separate from count constraints, and preferred the
already available bounds over unnecessary new counters. Existing data could
narrow ambiguity later, but no collection was authorized or launched.

The treatment states some distinctions more explicitly; that wording difference
is not a measured decision-quality gain. The parent observed no changed verdict,
corrected bound or avoided wrong experiment relative to the control. Retain this
null result and the outputs rather than claiming skill improvement from added
instructions. The actual useful contribution remains round94's source-grounded
counter-bound derivation and its independent review.

## Durability

Input hashes and criteria are in input-manifest.json/criteria.json. Full assigned
skill copies, raw cases, both answer formats and actual-command logs are frozen
by this packet's manifest. judgments.json records parent checks. Git delivery,
canonical research retention, later S3 publication and VM restoration remain
separate operations. No global test pass or cloud synchronization is implied.

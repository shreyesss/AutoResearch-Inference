# Checkpoint 27 — exact arithmetic, activation evidence and measured research yield

The discovery loop remains active. This checkpoint adds one independently reviewed Engram direction, closes a bounded activation audit, and repairs an observed research-tool failure. **No GPU execution, implementation qualification or measured serving improvement.**

## New direction: exact Engram remainder constants

The pinned hash kernel computes rolling XORs of token-ID products, then reduces each by a fixed prime to select learned embedding rows. This target has 48 prime divisors across its two Engram layers. The divisors are loaded at runtime, even though their values are fixed for the model layout. The hypothesis is that preparing divisor constants once could reduce repeated arithmetic in this invocation.

The relevant domain is nonnegative 63-bit values. A convenient existing 32-bit helper and a direct widening of the selected paper's formula are both invalid transfers. Independent adversarial arithmetic found counterexamples. The adapted proposal instead uses:

```
mu = floor(2^64 / p)             # prepared once, p > 1
q  = high64(x * mu)
r  = x - q*p
result = r-p if r >= p else r
```

For unsigned64 `x`, the estimated quotient is exact or one below the true quotient; one correction therefore gives the exact remainder. The source establishes a narrower valid 63-bit range, including mapped padding and replaced dead-history values. This is a mathematical argument, not a test of native integer lowering. The author checked 3,312 scalar cases; the independent reviewer checked four separate controls, including failure of the direct paper transplant.

**ER73 stays deferred for a three-arm experiment:** A = original loaded-prime `%`; B = actual constant-divisor specialization; C = prepared reciprocal plus correction. The original compiler may already lower A efficiently. C may lose to B or add loads/register pressure. Compare exact bucket identity, native generated instructions and resource use before timing. No timing or numerical ROI is available. One hash invocation covers both layers: do not multiply its savings by 40 decoder layers or five speculative tokens.

Prepare constants with the actual **`NgramHashState`** owner. The frozen author report and first review called it `EngramHash`; the explicit correction accompanies them. Preserve masks, original XOR order, output offsets and graph/lifetime contracts; generic masked divisor 1 requires special handling. This is independent of the request-mapping idea still under review.

[Mechanism and experiment](round73/REPORT.md), [independent review](round73/INDEPENDENT_REVIEW.md), [owner correction](round73/OWNER_CORRECTION.md), [independent formula control](round73/independent-formula-control.json).

## AV68: distinguish source support from an active workload

The audit inspected 154 bounded local metadata/configuration files, 143 distinct contents. None attested the exact c455 source and Flash1017 model revision. Older runs and conflicting configuration declarations cannot establish current AV activation. The stored baseline is explicitly a planned source profile.

Actual code also corrected an assumption: absence of a DSpark confidence head does not necessarily disable AV; an online estimator path exists. A requested flag is still insufficient—backend compatibility, manager construction and cost initialization must succeed. The eligible per-step branch requires a nonempty scheduled-draft dictionary, including a selected budget of zero.

AV68 remains deferred, with a precise missing input: an existing exact-run launch/startup receipt and an eligible step record. More generic searches or scalar metadata simulations cannot supply it. Separately investigating AV activation/tuning is valid, but its policy change must be controlled separately from copy elision; their gains cannot simply be added. [Audit](round74/REPORT.md), [independent review](round74/INDEPENDENT_REVIEW.md).

## Yield through rounds 64–74

| Observed output | Count and meaning |
| --- | --- |
| Successful paper-search receipts | 11: ten dated searches plus one explicit older-paper seed lookup |
| Returned records | 64; 64 distinct declared IDs, without independent cross-provider entity resolution |
| Selected fulltexts read | 5, in rounds 64/66/69/70/73 |
| New mechanism directions retained for future experiments | 3: CR64, HM65, ER73 |
| Previously parked direction formalized | 1: AV68, continuing the round 65 component |
| Qualified implementations / measured service gains | 0 / 0 |

These adaptive, overlapping investigations do not support a paper-to-win conversion rate. Round69's failed empty receipt is preserved but excluded from successful searches. Source-only rounds, repeated reviews and the older seed are not counted as independent new-paper discoveries. [Exact query receipts and counts](yield-6474/counts.json).

The strongest near-term shortlist remains PJ01 and CF59, followed by the narrower AV68/HM65/CR64 interventions subject to their prerequisites. ER73 adds a precise arithmetic experiment; it does not outrank them on an invented latency forecast. Broader recent-paper exploration continues alongside these source-specific checks.

## Tool repair tested on the actual failed command

Round73's query expansion supplied `off_topic`, which is outside the existing observation-status enum. The old command returned only a generic `ValueError`. The repair returns the bounded field/index and five allowed values through CLI and MCP, without echoing submitted text or provider secrets. The original invalid plan still fails; an explicitly corrected copy succeeds with zero provider requests. No automatic scientific judgment or new search policy was introduced.

Verification: 29 focused tests passed, including actual CLI and MCP calls; the required research gate passed 382 tests and 29 subtests. Bootstrap dry-run and diff check passed. The independent reviewer reran the 29 focused tests; root verified the reviewed code hashes. This establishes command repair, not improved hypothesis quality. [Report](observation-status/REPORT.md), [review](observation-status/INDEPENDENT_REVIEW.md), [receipts](observation-status/validation.json).

## Durable state

Root independently reread canonical round 63, yield 58–63 and round 64 retention: 209 artifact references and 139 source revisions across the three packets, plus exact saved LP63/CR64 hypothesis states, both deferred. Counts are packet sums, not deduplicated corpus totals. Later imports are queued through the existing single writer; this checkpoint does not call those complete. [Readback](retention-27/canonical-readback.json).

At 06:58:45 UTC, local job receipts showed 951 successful GitHub pages, last batch completed 06:54:12 UTC without errors. Published research lineage was `b57a565…752` at 06:49:06 UTC; a newer local snapshot `1dd2460…966f` existed. This is local publication evidence, not a fresh remote check or a claim that all later packets reached S3 or a VM. [Observation](retention-27/publication-observation.json), [delivery hashes](source-copy-manifest-27.json).

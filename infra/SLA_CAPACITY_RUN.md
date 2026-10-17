# SLA-capacity campaign reset

**Status: preparation, not a launched SLA run.** The exploratory Optuna
overnight search was stopped on 17 October 2026 before another proposal could
start. Its completed cells and interrupted trial remain in the v2 ledger. The
scheduled B0 adaptive pilot had not run. No result from that campaign is an SLA
or capacity result.

## Proposed research service contract

The values below are a proposal for this pinned Qwen3.8-27B, BF16, TP1,
single-RTX-PRO-6000 study. They are not product-owner commitments. They were
chosen slightly above the only available mixed B0 p90 observations so B0 can
anchor a feasible-load search; a second B0 window could change that assessment.
The machine-readable proposal is `configs/sla-policy-proposed.json`.

| Request shape | Mixed B0 TTFT p90 (n) | Proposed TTFT p90 limit | Mixed B0 TPOT p90 | Proposed TPOT p90 limit |
| --- | ---: | ---: | ---: | ---: |
| Chat | 1,078 ms (17) | 1,500 ms | 52.55 ms/token | 70 ms/token |
| Agent | 1,847 ms (8) | 2,500 ms | 58.25 ms/token | 70 ms/token |
| Code | 442 ms (6) | 750 ms | 55.14 ms/token | 70 ms/token |
| Document | 8,931 ms (5) | 12,000 ms | 57.24 ms/token | 70 ms/token |

Require zero observed failed, timed-out, canceled, censored or missing
requests. Report offered and realized requests/s, output tokens/s, p50/p90/p95/
p99 and per-class denominators at every point. The capacity objective is the
highest **independently confirmed offered request rate** satisfying all four
class limits and complete dispatch/accounting. The starting 0.1 requests/s is
an anchor, not a capacity target. The rate bracket must expand if its high end
is clean and contract-feasible.

The proposed policy asks for at least 30 eligible requests per class and a
one-sided 95% binomial upper bound on deadline-breach probability no greater
than 10%. This bound assumes independent requests; common contention makes
multiple independent windows necessary. The 36-request screen has only 5
document requests and is therefore never SLA-eligible. A zero-error sample
is an operational check, not proof of a true zero error rate.

## Measured versus missing gates

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Frozen service contract | Approved class deadlines, percentile, error rule, rate objective, hashes | Proposed file exists; application owner has not confirmed it. |
| Independent inputs | Two development and two sealed-test windows with new content and arrival seeds, replay validated; no test payloads in proposer workspace | Split plan and audit code exist; real manifests have not been captured. |
| Matched B0 | One complete B0 per qualified window with input, dispatch, server and request records | Only the old 36-request mixed B0 exists. |
| Class-aware load search | Rate proposals, all native AIPerf trials, per-class SLA scoring, no client throttle, no sustained backlog | Existing `iar adaptive` is a throughput-only 36-request pilot. It is not the SLA search. |
| Serving search | Typed server settings, matched fixed-load screen, repeats for finalists, costs and full evidence | Existing v2 loop has a 36-request validity screen and three active axes; no automatic repeats. |
| Confirmation | Freeze finalists and rules, paired B0/candidate on independent development windows, then sealed test | Not run. |

Native AIPerf 0.13 `--search-sla` can filter **aggregate** TTFT/TPOT and
errors. Its current rate planner does not enforce our four class-specific
deadlines by itself. Use AIPerf for load generation, sampling and raw exports;
the harness must check each class from exact request records and retain all
sampled points. A chosen in-sample rate is provisional until fresh-schedule
confirmation. Sample count is a protocol choice, never an adaptive search axis.

The pinned vLLM image exposes more scheduler, KV and execution flags. The
current low-rate OPS36 cell does not show the sequence or KV pressure needed
to interpret most of them. Inspect load-curve queue, preemption, KV and GPU
evidence first, then admit a binding axis in a new domain version with a
boot-verified B0/candidate contrast. See `infra/PINNED_SEARCH_AXIS_AUDIT.md`.

## Next inspectable checkpoint

1. Review the proposed service contract and exact independent split plan.
2. Capture and replay-validate one development window and its matched B0;
   inspect class counts, load, errors, queue and wall time before generating
   the remaining windows.
3. Run class-aware adaptive probing on B0; inspect **every** proposed rate and
   why it passed/failed. A 36-request pilot can bracket possible pressure but
   cannot pass the proposed class sample minimum. Probe a larger qualified
   development corpus near the suspected boundary, then confirm the selected
   rate on new fixed arrivals. Feed the full B0 curve to Codex **before** its
   first SLA-directed proposal, not after an optimizer finishes.
4. Only then launch a fresh versioned SLA serving-search campaign. Do not
   relabel the stopped exploratory v2 search as this campaign.

The four planned 240-request windows each take roughly 40 minutes of dispatch
at 0.1 requests/s before server startup or drain. Each window must contain at
least 30 verified requests in every class; a random seed that misses this
minimum is rejected before replay. The long windows belong to
candidate confirmation, not every exploratory proposal. Actual wall time and
class counts must be measured before scheduling a full campaign.

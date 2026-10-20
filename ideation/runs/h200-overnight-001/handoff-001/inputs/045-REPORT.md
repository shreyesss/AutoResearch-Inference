# H200 research continuation: findings and next decisions

Updated 21 October 2026, Asia/Calcutta. Research and CPU/software checks only;
**zero new serving/GPU runs and neither remaining full service attempt used.**

The deeper search produced three plausible, falsifiable mechanisms, but no
demonstrated optimization gain. The useful outcome is a narrower allocation:
continue C24's cost/measurement investigation offline, inspect the isolated
DSpark sampler's exact eligibility, and hold the FP32 router port pending evidence
that it applies. Publication novelty is not a selection requirement.

## Current intervention decisions

| Family | Proposed intervention and evidence | Current decision |
| --- | --- | --- |
| C24 | Price the target **and subsequent draft graph** after DP synchronization. Installed AV already includes a request-indexed draft-cost term; source analysis shows the draft graph can change with the target budget. An independent synthetic CPU oracle changes the optimal budget from 11 to 3 when invented coupled costs are included. | Continue offline dispatch/measurement design, cap 8 engineer-hours. Preserve the completed instrumentation-inconclusive timing verdict and GPU hold. No real policy error or latency benefit is measured. |
| C25 | Port only the unsharded DSpark sampler fusion from vLLM PR61869. It retains the bias GEMM and could remove repeated sampling/glue work. The whole PR depends on specialized SM100 execution; the narrow H200 adapter is a separate proposal. | Conditional source/configuration audit, cap 4 engineer-hours. Resolve draft watermark ownership, accessor/dispatch gates and real-weight parity before implementation. Complete kernel/launcher source is now retained; SM90 correctness and materiality remain unknown. |
| C26 | Port PR61903's SM90 BF16x3 router kernel **if** an eligible FP32-weight branch is active and unoptimized. | Hold implementation/GPU work. Three sampled checkpoint gates are BF16; nominal GateLinear's FP32 output does not establish FP32 weights. Loaded dtype/actual dispatch remain unverified, so this is a cheap adverse applicability finding, not a measured performance rejection. |

[Detailed intervention plans](INTERVENTIONS.md) specify controls, correctness,
opportunity coverage, expected-effect uncertainty, engineering costs, GPU budgets
and support/stop/inconclusive rules. [Cheap check receipts](ELIGIBILITY_CHECKS.md)
separate actual observations from synthetic examples and nominal source.

C03's valid unfavorable screen remains unchanged: primary ITL +1.8467%, TTFT
p99 +7.8332%, E2E p99 −5.33%; no promotion. C01's external grouped-Humming
poor-result notice still lacks local raw artifacts; its indexed arm remains
distinct and untested. C24's timing coverage/association failures are preserved.
A new rubric does not reset any of these outcomes.

## What the deeper scan did—and did not cover

The earlier process used title/catalog rules, ranked searches capped at 35 hits
per query/repository, bounded recent feeds and selected mechanism packets. It
was useful discovery, **not comprehensive semantic review or a complete bulk
archive**. SGLang had supplemental coverage; DeepInfer was absent from the
original 13-repository catalog.

This pass scanned **8,908 distinct local PR/issue identities** across fourteen
overlapping topic groups without a local query-result cap. **1,122 remain
title-only.** It fetched/refreshed **2,202 unique opening records across 17
repositories**; these are not all new additions. DeepInfer's all-state endpoint
was exhausted at **95 PRs**, while vLLM, SGLang, InferenceX and FlashInfer retain
unfinished feed cursors. Other recent feeds cover updates since 13 October UTC.

A 40-entry unmatched sample found missing RoPE, quantization, correctness and
release vocabulary; eight leads were explicitly reopened. Expanded patterns
retain **525 unmatched entries**, with no automatic exclusion. Because that
sample guided query repair, it is not an independent recall estimate.

Closer acquisition retained **28 selected pages/openings and 26 patches**,
including 14 DeepInfer PRs. The generation packet combines 23 primary/code/paper
sources and 31 quote-validated claims; the follow-up adds actual cheap-check
evidence and complete sampler source. Acquisition depth, semantic review and
pilot readiness are separate quantities. Full historical discussions, all
reviews and every patch remain outside this pass.

See [filtering audit](FILTERING_AUDIT.md), [topic ledger](discovery/topic-ledger.csv),
[per-feed receipts](discovery/feed-coverage.json), and the
[compressed opening snapshot](sources/feed-openings.jsonl.gz) with its
[count/hash manifest](sources/feed-openings-manifest.json).

## DeepInfer's contribution

The pinned release supplies confidence-scheduled verification, runtime cost
correction, asynchronous scheduling, shared indexer/attention metadata, fused
paths, load balancing and bounded replay. Its full serving stack is not released,
and its released NVIDIA path remains SM100.

The new PR review materially changes the Hopper picture: #92 contains a broad
SM90 port with author-reported H20 results, beyond the earlier RFC/helper work.
Its discussion says it will be maintained outside mainline. It is an expensive
port/integration lane, not established H200 service support or a drop-in gain.
The reported GSM8K demonstration/scoring overlap also prevents treating that
claim as our clean held-out quality qualification.

Other useful leads include #54 timing-event/host overhead, #111 queue/output
work, #99 single-node Engram compatibility, #107 logical-expert history across
remaps, and resource/configuration/evaluation correctness fixes. Their relevance
depends on matching local paths: large-queue fixtures, extra collectives,
different weight formats and disabled EPLB cannot simply transfer into the
current seq64 Marlin/EP4 service. See the sourced
[DeepInfer review](DEEPINFER.md) and [95-PR disposition ledger](DEEPINFER_DISPOSITIONS.csv).

## How continuation and review now work

The new `hypothesis.continue` tool freezes the complete family register, linked
cards, explicit holds, prior results and supplied artifacts with hashes. The
generator and critic receive every indexed family state alongside bounded
database recall. A new handoff records added/modified/removed inputs and links
its predecessor. Changed results block publication of an obsolete assessment;
old proposals and reviews remain intact. Explicit reopening requires new
evidence and a scope/mechanism delta.

The rubric is present in both generation and workflow. This run's frozen weights
are expected baseline value 30, pilot decision value 25, engineering time/fit 20,
evaluation cost 15 and evidence/history 10; threshold 70. They are prioritization
judgments, not a probability or speedup estimator. Unknown local benefit is
allowed at ideation and must be resolved before an expensive attempt.

Two proposal/critique rounds preserve six proposal instances for three
mechanisms. The sampler's first draft was structurally rejected for citing an
unregistered report path; its revision repairs the evidence ID. The raw first
run also exposed duplicate parent/revision selection when parents used global
memory IDs. The runner now resolves those IDs correctly, and a fresh eligibility
review reconsiders one latest revision per mechanism with the new evidence.
Historical raw outputs remain unchanged. A fourth idea was not manufactured to
fill the requested maximum.

The final review records C24 **accepted for offline test design, 83/100**;
sampler fusion **deferred, 71/100**; router port **deferred, 63/100**. The router
was previously 70/100 before the BF16 evidence. For the sampler, the copied
proposal's missing-source statement is obsolete: the operator's current card
and dispositions explicitly correct availability while retaining the raw model
deferral and the unresolved watermark/adapter/correctness gates.

Use [the final eligibility review](eligibility-followup/decision.md),
[current dispositions](dispositions.json), and
[the latest continuation handoff](handoff-003/continuation.json) for next work.
The [workflow documentation](../../docs/CONTINUATION.md) contains CLI examples;
[system upgrade plan](SYSTEM_UPGRADE_PLAN.md) records completed fixes and the next
validation work.

## What this establishes about AI research

The process produced source-grounded conditional interventions, incorporated
unfavorable/inconclusive history, caught a citation error, revised proposals,
and used a cheap check to reduce willingness to allocate to one lead. **58
software tests pass**, including stale-result blocking and revision-lineage
selection. CPU probe outcomes are linked to immutable proposal IDs with explicit
scope; synthetic sensitivity is not recorded as a service validation.

This is evidence that the mechanics can support a disciplined research process.
It does not establish a performance win, comprehensive retrieval recall, or
superiority to human/keyword/random selection. The next decisive validation is
whether the bounded offline work and qualified pilots yield a useful matched
service improvement per total time and evaluation cost. A justified stop is
also useful if it prevents an expensive inapplicable attempt. The
[research-validation plan](RESEARCH_VALIDATION.md) specifies the prospective
equal-budget comparison and preserves those limits.

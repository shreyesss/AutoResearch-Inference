# Checkpoint 21 — rescue useful components and surface contradictory evidence

The guided discovery loop remains active. All work in this checkpoint is source analysis, ordinary Python diagnostics, research-tool tests and retention verification. **No GPU experiment, serving change or measured inference improvement.**

## New candidate: CF59, context projection overlap

Recent-paper discovery led from per-step host overhead to whole-step graph coverage, then to the actual diff of vLLM PR61869. Earlier opening-record screens grouped that PR with C025 sampling fusion. That whole-PR classification was too broad: the diff also contains a separate context-projection scheduling mechanism. This is an additive correction to checkpoints and screens that described the PR as a duplicate.

The target hidden features are ready before rejection sampling finishes. Native DSpark then performs three different context projections and norms before inserting their outputs into KV. The projection math can potentially run while sampling proceeds; slot and position publication must wait for sampling-dependent state. CF59 proposes that narrow split with unchanged weights and arithmetic.

This differs from C025 sampler work reduction and PJ01 removal of unused projection columns. Their gains are **not additive**: either optimization may shrink the overlap window. An optimistic bound is `min(context duration, sampling interval) - added overhead`; all three terms remain unmeasured for the pinned deployment.

The independent audit found material conditions:

- Preserve the native early token-output copy. The complete donor graph delays it.
- Bind both target and draft graph modes; a donor non-FULL draft branch can recompute projections already prepared earlier.
- Preserve prefix/eager-tail partitions, padded shapes, per-layer weights, slot mapping and collective order.
- Establish stream-safe scratch and projected-buffer ownership before attempting a port.

**Outcome: one new deferred typed hypothesis in isolated state, zero accepted implementations.** Symbolic CPU probes detect specific duplicate-row and premature-buffer-reuse errors; they do not establish native numerical or CUDA correctness. Existing Mooncake and agent-p75 remain the service workloads. Additional internal observations are needed to establish overlap and KV safety, rather than inventing a new service benchmark. [Full experiment design](round59/REPORT.md), [independent review](round59/INDEPENDENT_REVIEW.md).

## Recent low-bit literature: four component dispositions

| Component | Source audit outcome |
|---|---|
| Quantize before activation duplication | Already performed by the native producer; no new card |
| Fold microscale factors into a lookup kernel | The paper's separable-factor assumption is not guaranteed by native arbitrary group scales; direct transfer rejected, repaired exact representations remain possible |
| Vector lookup hardware | Direct accelerator-specific transfer rejected; the broader lookup idea was investigated separately |
| Reuse tensor-memory scale storage | Deferred option; lifetime, allocation granularity and resource exposure are unresolved |

Two dated OpenAlex searches returned 16 distinct paper identities; four selected fulltexts were read at mechanism/limitation depth. Forty-four PR records were retained from bounded searches and three bodies read deeply. These are coverage counts, not 44 audited implementations. A rational-arithmetic counterexample falsifies a format-only scale-factorization guarantee; it does not claim the actual checkpoint has those values. [Report](round60/REPORT.md), [independent review](round60/INDEPENDENT_REVIEW.md).

## Yield, without a quota

| Lane | Discovery coverage | Formal outcome |
|---|---|---|
| Round 58 | 8 paper hits, one selected fulltext | One parked component; no new formal card |
| Round 59 | 44 hit references / 43 distinct papers, one selected fulltext; actual PR diff audit | One deferred card, CF59; graph and event-pool leads parked |
| Round 60 | 16 distinct papers, four selected fulltexts | Four component dispositions; no new formal card |

This slice produces **one deferred candidate and zero implementation-qualified or measured wins**. Cross-lane paper identities and component families have not been deduplicated into a global denominator. A source-backed next step is useful, but it is not a promised performance improvement.

## Tool repair: old acceptance no longer hides later objections

Compact recall now shows unique linked refuting-claim count, up to three IDs, and an omitted count. New objections alter the inventory hash. The original selection and baseline remain intact; a scoped objection is not automatic rejection. Multiple claims from one source do not constitute independent evidence. The skill directs the agent to the complete dossier before reuse.

The actual canonical M01 record now displays its historical accepted diagnostic selection **and three later refuting claims**. This prevents its obsolete arithmetic premise from silently returning as an accepted implementation idea. A read-only transaction inspected all 143 canonical cards and made zero database changes. Compact recall does not check newer source revisions or certify correctness when its objection count is zero. [Tool verification](refutation-recall/REPORT.md), [actual readback](refutation-recall/canonical-readback.json).

Verification: **365 research tests and 29 subtests passed**, bootstrap dry run passed, skill validation passed using the existing isolated validator dependencies. [Independent review](refutation-recall/INDEPENDENT_REVIEW.md) passed, including a read-only multi-claim fixture. The inventory hash covers the compact projection; an additional rationale on an already-linked claim does not change it. These tests verify tool behavior, not research quality or inference speed.

## Durable memory and exposure search

The earlier approved retention packages are complete. Root independently rechecked **383 retained artifact hashes and 224 exact source revisions** in canonical state. M01's three scoped objections are attached; its original card, baseline and selection remain unchanged. The new CF59 card is still isolated and awaits reviewed import/restore verification. [Verification receipt](source-verification-21.json), [M01 completion](retention-21/M01-complete.json).

A bounded S3 evidence search listed 9,481 object keys and read eight selected small manifests, without finding a compatible exact-pin projection/sampling trace. No raw GPU experiment was launched. This is not proof no such trace exists under other names, within archives, or elsewhere. Old benchmark throughput and external telemetry cannot establish the missing component durations. [Coverage report](remote-trace-discovery/REPORT.md), [independent review](remote-trace-discovery/INDEPENDENT_REVIEW.md).

No new cloud publication is asserted for these later canonical imports. The ordinary publisher owns snapshot/lineage progress; a local retention receipt is not an S3 receipt. Raw sources and state remain outside Git; small delivery copies are recorded in [the copy manifest](source-copy-manifest-21.json).

Next lanes investigate ongoing-request migration under shared expert parallelism and source-supported adaptive dispatch. Existing priors and contrary evidence remain mandatory checks. The discovery loop continues without an acceptance quota.

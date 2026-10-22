# Checkpoint37 — transfer only the parts that survive source review

## Outcome

The two newest directions remain deferred: SL97 changes Sinkhorn register ownership; SN98 changes the single-chain sampling/verifier coupling. This batch narrows their implementation contracts and excludes misleading donor behavior. **No implementation qualification or measured inference win. No GPU work.**

| Branch | Useful new evidence | Disposition |
|---|---|---|
| SN98 cross-paper/code synthesis | A persistent single-chain noise tape exists in donor code; its multi-draft rejection branch instead redraws the correction, which fails an exact probability counterexample | Retain single-chain ingredient; exclude that multi-draft branch |
| SN98 native adapter | Existing target Gumbel, shifted candidate comparison and original count/cache consumers provide a bounded interface | Seeded parity prototype source-feasible; unseeded serving blocked on effective-seed lifetime |
| SL97 output ownership | An explicit sender selection plus one source-level exit shuffle restores all16 native Comb owners | Mapping resolved; numerical/codegen/register/cost gates remain |
| Expert-weight reuse | Logical repeats exist, but native sizing already minimizes M blocks; a naive loop reorder violates the scheduling readiness implication | No new hypothesis; larger reuse design parked |

## 1. Shared noise: papers do not make every donor branch correct

[Round101](round101/REPORT.md) combines two full texts with pinned implementation inspection. ERSD (`2504.15475v1`) warns of lower acceptance than greedy rejection; target-evaluation savings are not wall-clock savings. GLS (`2506.05632v3`, version dated11 January2026) obtains additional coverage from multiple draft samples, which add work. These are relevant older foundations for the newer SN98 lead, not newly published October papers.

The inspected donor test defaults to top_k50 and masks other logits. A full-width tensor does not establish full-support sampling. Its persistent full-horizon tape would occupy about508MiB/request at the stated1024-output, depth5, K1, vocabulary129280, float32 shape; keyed regeneration is the proposed native adaptation, with its own cost.

More consequentially, its multi-draft all-rejection branch draws fresh target noise, while the paper algorithm and single-draft branch retain the selected target token. An independent continuous-law calculation for K2 with full-support p=(.8,.2), q=(.2,.8) gives token0 probability443/625=.7088 after this redraw instead of.8. This is a counterexample to that inspected branch, not a refutation of the paper or a native vLLM bug. See the [independent review](round101/INDEPENDENT_REVIEW.md).

## 2. Native adapter: the seed must outlive preemption

[Round103](round103/REPORT.md) maps actual source rows and consumers. Target row s+j predicts the candidate at s+j+1. Emit the matching prefix plus the already drawn target correction/bonus; preserve sampled/rejected counts, cache truncation, asynchronous output copy and device AV offsets. Do not reinterpret draft_logits=None as this mode: it selects greedy behavior in the current drafter.

The worker removes preempted request state. Re-addition with SamplingParams.seed=None generates a new effective seed. SN98 needs the same future-position noise when a logical request resumes after lookahead, so its seed needs a longer-lived owner. An explicitly seeded initial parity arm can be bounded; it cannot qualify standard unseeded serving. Saved workload defaults omit the request seed, and AIPerf's workload random seed is a different setting. Executed request payloads were not recovered in this audit.

The design also requires request-lifetime mode admission and same-tape late fallback. An unsupported request arriving later must not silently switch existing shared-noise requests to independent native sampling. Target head work remains; all admitted target rows now need Gumbel draws and a packing stage. Acceptance loss can outweigh removed probability/residual work. ROI remains null.

[Independent source review](round103/INDEPENDENT_REVIEW.md) found no blocking contradiction in the narrow seeded design. It adds one implementation distinction: durable effective-seed ownership should not silently change the public explicit-seed flag, which affects backend eligibility in broader sampling modes.

## 3. Sinkhorn: output transport is an actual operation

[Round104](round104/REPORT.md) resolves the earlier missing transport. In the donor parity layout, each lane selects register `(lane>>1)&7`; each original Comb destination idx receives from lane `2*(idx&7)+(idx>>3)`. All32 lanes participate. Integer tags confirm16/16 correct destinations. A receiver-local selection followed by a lane0/1 broadcast fails14/16 because the shuffle reads the sender's selected value.

This is one source-level exit shuffle plus an eight-way selection and index arithmetic. It is not free, and compiled instruction/register behavior is unknown. Both layouts still use four source-level shuffles per normalization stage. The proposal preserves native Pre/Post stores, original mix_value return, arithmetic primitives, epsilon, iterations and final synchronization. No floating-point or native correctness has been demonstrated.

[Independent review](round104/INDEPENDENT_REVIEW.md) verified the inverse mapping and actual warp-uniform call sites. Its next decision-changing gate is compiled resource/codegen inspection when separately authorized, not further tag sweeps. No compiler or GPU was run.

## 4. Weight reuse: expose the scheduler contract before changing order

[Round102](round102/REPORT.md) finds logical weight reloads across M blocks, but current sizing already minimizes these blocks. Existing weight-packet/locality hypotheses cover much of the opportunity. TMA demand loads do not prove repeated HBM traffic.

The native readiness counter assumes an M-major issue prefix. A four-M/nine-N example shows naive N-major order reaching the first nine-claim threshold while six of the first M's tasks remain unissued. This falsifies that metadata implication, not a measured deadlock. Actual K-outer reuse needs additional accumulators and stage ownership; merely reordering loops does not remove the existing loads. No new card was produced.

## Yield, tool usefulness and state

- Round101: one citation query, two full texts, five donor files; one useful implementation precedent and one unsafe branch isolated; zero new identity.
- Round102: targeted source investigation, no paper query; no new identity. Prior overlap and scheduler costs stopped a generic reuse claim.
- Round103:20 target source files plus retained benchmark construction/defaults; concrete adapter and seed-lifetime gate; zero new identity.
- Round104: one small stdlib tag control; resolves output ownership only; zero new identity.
- No new model/GPU performance results, and no throughput or latency estimate inferred from operation/byte counts.

The normal command journal was verified against the authoritative state journal. An earlier manually exported snapshot mirror contained only init. The additive [journal clarification](round101/JOURNAL_CLARIFICATION.md) preserves this correction: recorded arguments are normalized and redacted, not raw argv. This was an export-reading mistake; no production journal code change was justified.

The independent97/98/99 retention audit restored267 artifacts and87 source revisions, preserved both original deferred IDs and null ROI, and verified SL97's blocked-then-ready evaluation history. Root approved sequential local canonical retention after the existing queue; completion and cloud publication still require separate receipts. See [retention review](retention-37/REVIEW.md). This checkpoint does not claim those queued records are already on S3.

Production code/skills were unchanged in this batch. Document/source integrity and the stated CPU controls were checked; no new full-suite result is claimed. Discovery continues on recent scheduling/prefill literature while these bounded source designs receive independent review.

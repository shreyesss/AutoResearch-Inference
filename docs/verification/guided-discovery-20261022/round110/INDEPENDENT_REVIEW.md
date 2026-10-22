# Independent review: FV86 flag adapter

## Verdict

No source blocker found to the bounded adapter described in frozen round110. It resolves a real ownership question for the existing deferred FV86 proposal; it does not implement the adapter or qualify correctness, exposure or speed. Retain the original card, baseline and status. No new hypothesis is needed.

I read the actual pinned producer, residual reader/writer, rejection common tail, resampling and insertion, plus mapping/AV/chunk/grammar and RNG helpers. Executed checks independently verify all 25 frozen files, ten archive-equal source copies, ten source fingerprints and thirteen exact quotes. AST inspection confirms the sole direct mass-reader call and absence of the mass buffer from resampling. No target module, torch, Triton, compiler or GPU was invoked. These are source checks, not adapter tests.

## Ownership and freshness

In `rejection_sampler_utils.py:444–498`, local position zero returns before any residual write. The sole mass-reader call at 624 reads `logit_idx+1`; it cannot read the current request start in a valid one-bonus packed interval. Consequently `(start,0)` is disjoint from the live residual cells. Distinct nonempty intervals own distinct starts. This argument depends on that actual interval invariant; pointer identity or allocation reuse alone would not prove freshness.

The proposed producer must reset every actual current-request cell before its existing greedy return (`:355–360`). This includes zero/one-draft and invalid-draft requests. All flag consumers must remain under block/full-q/feature guards; the ordinary and one-hot branches have no such buffer. Moving the existing allocation before the producer provides storage without adding a launch, but extends the allocation lifetime and may affect capture/allocator behavior. Source ordering supports the design; no compiled visibility or graph replay proof was executed.

`input_batch.py:692–708` writes local position `block` at `start+block`, so the residual consumer can recover its current start by subtraction. `model_runner.py:1448–1456` performs AV reallocation before that expansion; the flag must use final device boundaries, not scheduler draft counts or stale CPU sums. `rejection_sampler.py:340–366` rebases request chunks and logits together; its AV single-chunk guard avoids the stale CPU boundary case. Model-only hidden-row padding does not create extra sampler intervals (`model_runner.py:1621–1627`). Unsupported custom/PCP/multi-bonus/zero-length intervals remain excluded. No broad multi-rank admission was proven.

## Sampling semantics and consumers

With all admitted draft IDs valid, the native block loop continues after a failed interior test and records the latest passing index (`rejection_sampler_utils.py:565–645`). Thus a terminal pass at step `m-1` establishes accepted length `m`. This is the specific premise; it is not a generic first-rejection shortcut. The true branch must write every accepted draft ID and retain the common stores at 685–710. The original full-pass branch leaves both rejected LSE values at zero and still stores them. Resampling then selects the bonus row and insertion performs the count increment; it must not be pre-incremented. The original ratio stores remain live inputs and must not be repurposed.

Eligibility must inspect the verification-token argument, including grammar-invalid copies (`rejection_sampler.py:426–432`). Any placeholder forces false and the original path. This also ensures the terminal result cannot jump across an invalid draft. Keep the original real-ID contexts for watermark/sampling processing. Keeping that code path is not independent watermark qualification.

The proposed terminal predicate must use the **stored FP32** cumulative value at `end-2`, the original step `m-1`, the current persistent-state seed and position at `end-2`, and the exact `<=` comparator. `gumbel.py:66–76` is indexed/stateless in source; omitting earlier evaluations therefore does not advance a mutable stream. That observation does not establish compiled equivalence of a new in-kernel reload/SSA path, exponential approximation, casts or RNG lowering. NaN terminal comparisons must remain false and take the original fallback. This finite-precision gate is part of the claimed same-path optimization, not a universal demand that every possible future sampling proposal be bit-identical.

## Cost and next stopping point

True rows omit interior mass computation and the old acceptance loop, while stats, all cumulative ratio stores, grid launches, bonus recovery and insertion remain. False rows gain flag work and duplicate the terminal scalar test. Each residual CTA may gain a metadata load; the modified producer can gain register pressure or changed code generation. Reusing a cell does not make these costs free. A dedicated flag tensor remains a legitimate alternative if it produces a simpler or better compiled contract.

The source gap is sufficiently narrowed. Further scalar sweeps or another address-only fixture would not resolve the remaining uncertainty. A future authorized implementation should inspect stored-ratio/exp/RNG lowering, poison omitted mass cells, force true and fallback paths, and verify valid output IDs/counts/LSE stores under reordered slots, AV and replay. No such work is authorized or performed here. Compatible terminal-pass exposure and exposed residual time remain unknown; no ROI or changed priority follows from this review alone.

## Evidence identity

All source paths above refer to `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`. The main utils file SHA256 is `44de886702efc8189efa3c90d4d1646bd1b6b002b39e74a89e1120bbad3ca141`; the exact remaining file hashes are in the independently verified author's `source-manifest.json`. The archive hash and exact source ranges are retained in `checks.json`. Author manifest: `afde68786dfacb02abb3db21e39f5c5b295cd5d620bfc1e14d2f0955c60fe0a4`.

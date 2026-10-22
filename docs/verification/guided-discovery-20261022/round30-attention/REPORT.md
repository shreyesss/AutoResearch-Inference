# Round 30: declared-reference attention and a rejected barrier shortcut

## Decision

**No implementation-qualified improvement.** Retain one reduction-only discovery lead pending numerical admission and exposure. Reject two direct transfers as scoped: the entire FoldAttention decode/cache path, and copying a donor `p_full/o_ready` barrier split alone into the pinned Mega reader. These are recorded screened interventions, not three accepted/new canonical hypotheses. No canonical record, baseline or status changed.

Research uses planned DeepSeek-V4.1-Flash-1017, vLLM `c4557869393db4d75c483d92edd02a5125500883` and configured FlashMLA `5dceadbd9eabc9acfc547ef18ec8f7b14b980682`. This is source evidence, not live binary/deployment attestation. No GPU, model import, compiled kernel, timing or serving change occurred.

## Discovery and retained coverage

1. Read all **138 compact cards, five pages**, in one read-only SQLite transaction with stable inventory hash. This avoids mistaking prior TopK, gather reuse, physical-index publication or cross-query reuse for a new direction. Compact truncation remains visible; no claim of reading every historic full dossier.
2. Agent-authored query plan sought GPU attention normalization/reduction execution. `expand` recorded it; it did not invent queries autonomously.
3. First arXiv query (June 1 inclusive–October 23 exclusive) failed HTTP429. That is failed coverage, not zero papers. No blind retry.
4. Explicit OpenAlex alternative with the same dates succeeded: **20 hits / 20 provider-declared paper identities**. All abstract-level dispositions are in `paper-dispositions.json`. One selected paper was read in full: [FoldAttention](https://arxiv.org/abs/2609.33410), September 27. The retrieval used unversioned HTML, whose exact body hash is retained; web inspection additionally confirmed v1. No unrecorded version pin is implied.
5. `investigate` retained the full text; its repository stage failed. Separate source-only tar retrieval pinned the actual author repository at `207b7553ebcef63fe8d9aabab28d18f88f8a7af5`; no package import/build. Thirty-one source/README files retained, only relevant decode/reference/cache paths inspected in depth.
6. The new operation vocabulary triggered **three real local PR searches**, not another model-name search: softmax+rescale, softmax+reference, FoldAttention. Read-only whole-corpus FTS selected a bounded subset, copied to isolated state for actual `pr-search` receipts. Results are limited20/query with `updated_at` dates, not exhaustive. Selected donor/counterexample PRs were read; full diff/head code for #5602 was retrieved. Others remain opening-record leads.

Initialization initially used an unsupported `--defer-snapshot` flag; it failed before initialization/provider calls and was retried with supported `init --local-only`. Operational errors, provider failures and journal are retained. State mutations were isolated; deferred evidence is not a new S3 snapshot/publication.

## A. Selective FoldAttention component

### What transfers mathematically

For one query, choose a finite reference Z, evaluate weights `2**(score-Z)`, accumulate numerator A and denominator L, and output A/L. A common shift cancels in real arithmetic; disjoint contributions can add without pairwise max/rescaling. This component does not require optional training, value approximation, changed selected support or the donor's cache format.

A narrow target proposal would retain the original typed compressed/SWA occurrences, original query/position and quantized cache values, and learned sink. Replace only repeated softmax maximum/rebase work with an admitted reference plus complete fallback. Original model semantics are the aim; real-arithmetic identity does **not** establish finite BF16/FP8 output equivalence.

### Why whole-donor transfer is rejected

Author implementation is Hopper SM90, D64/D128 and a two-plane INT8 key cache, optionally two-plane E4M3 values. Finite-depth gating changes numerator contributions; even its dense path changes represented keys. Target Mega reader consumes fixed-record FP8 or compressed NVFP4 caches, H512, selected compressed positions plus layer-local SWA, and a learned zero-value attention sink. Replacing it with donor code would change multiple contracts. Neither donor headline speedups nor its dense-mode number predict this deployment.

### Concrete current baseline

- `sources/target-mega-wrapper.py:326–364` calls `fused_norm_rope_attn_rope_cast_decode` with original cache/index/lens, sink, scale, positions and `enable_q_norm=False`.
- `sources/target-attention.py:369–389,790–818`: latent `qr` is RMS-normalized before learned `wq_b`; this does not imply a unit-normalized final per-head query. Learned KV normalization also prevents treating keys as unit vectors without weight bounds.
- `sources/target-core.cuh:902–1006`: each tile finds its maximum, but **already defers O rescaling** until max-reference exceeds **six binades**; first tile initializes without an O rescale. Do not model every tile as an expensive accumulator rewrite.
- Decode selected work is based on reserved SWA width plus actual compressed selected count (`target-core.cuh:452–463`), commonly bounded512+128 in this source configuration. It does not scan raw8K/128K context merely because a request is long. Actual selected counts and branch distribution are unknown.
- Target computes `li + exp2(sink-mi)` at output and returns zero when `li==0` (`target-core.cuh:663–676`). Donor's sampled key at position0 is not this learned sink logit.

### Remaining material gate

The paper estimates a reference using192 sampled slots and reports4–8us front-kernel overhead in its H100 environment. On a saturated640-position target domain,192 is30% of selected positions before any extra work; this is an arithmetic exposure warning, not a timing forecast. A sampled estimate is not a universal range bound. Author code has a real optional check/rerun (`donor/src/fold_attention/kv_cache.py:710–740,955–964`), disabled by default; `bool(bad.any())` crosses to the host. A captured target arm cannot silently omit the guard because timed donor runs do.

A stronger target-specific static bound, already-available valid reference, or bounded device-side replay might make this useful. None was established. Computing a full-row maximum first may cost the work intended to remove. Preserve BF16 probability conversion, final LSE/reporting, sink, empty rows, exceptional-value policy, and accumulator range; no claim that arbitrary changed reduction ordering preserves token output.

**Disposition: deferred discovery lead, low implementation priority until a cheap admissible reference and actual exposed maximum/rescale work are demonstrated.** This is distinct from AT01 indexer head screening and AT02 cross-token KV sharing; those optimize different operations.

## B. Paper→PR synthesis: #5602 barrier split

Retained [FlashInfer #5602](https://github.com/flashinfer-ai/flashinfer/pull/5602), head `cb273439cf2de29a2546d53eb3053eb7083192a9`, contains a concrete component: publish P before deferred O rescale; a new `o_ready` barrier protects subsequent PV. The fixed donor file is `sources/donor5602-kernel.cu`; exact repo path and SHA are in `donor5602-pin.json`. This is Kimi dense MLA, not proof of sparse target benefit. Wider reference threshold is a separate numerical change and excluded.

### Why an apparently matching source line is insufficient

Target softmax does wait `bar_SO_empty`, write S/P, conditionally rescale O, then signal `bar_SO_full` (`target-core.cuh:981–997`). Superficially, moving the signal looks promising. The complete consumer chain defeats that shortcut:

- `issue_sv` consumes S/P **and** the accumulated O; its completed MMA releases both KV slot and `bar_SO_empty` (`1069–1083`). The wait therefore protects actual data dependence and reuse, not just notification overhead.
- In one-CTA decode with two P buffers, the MMA warp already independently polls QK readiness and SO readiness (`1087–1136`). A pending rescale/SV input does not prevent a ready QK issue. QK does not consume a hypothetical early P-ready signal.
- SV must wait for both P and rescaled O whether represented as one barrier or two. Releasing it after P alone changes arithmetic: it can add the new contribution and then incorrectly rescale it along with old O.
- Two-CTA decode / prefill use fixed interleaving and the P-empty contract (`1138–1184`). Splitting only SO into two predicates still leaves the same SV dependency. Any deeper lookahead, additional buffer or issue-distance rewrite is a different intervention requiring its own alias/phase proof; it is not demonstrated by donor barrier syntax.
- No-rescale cases must be counted separately; new barriers add overhead there. Actual rescale frequency was not observed.

**Disposition: reject the narrow claim that copying `p_full/o_ready` alone removes an exposed dependency in this source.** This is not a proof that every future target pipeline redesign is useless. No new canonical hypothesis was made for this shortcut.

Other PR evidence: #6093 records a real small-factor/FTZ rescale failure in another MSA implementation; #6908 addresses unchanged-max correctness elsewhere. They strengthen numerical test design, not a claim that c455 has those bugs. #4991 skip-softmax intentionally changes work/support at nonzero threshold and targets prefill. #5644 lazy rescale overlaps an already-present target mechanism; its different stage/ring tuning is not transplanted without a separate source need.

## C. Executed CPU falsifiers and their limits

`python3 contracts.py`, exit0; standard library only:

-100 finite random scalar cases show common-shift additive identity to max absolute7.77e-16 in Python double. **Not BF16/GPU equality.**
-640-position synthetic score vector, sampled positions benign, one unsampled score150: even synthetic Z=log2(640) overflows a FP32 exponential. Sampling positions use the donor's documented first/recent/stratum structure; **actual estimator code was not executed**, no target activation measured.
-Learned sink omission changes a one-key output0.5→1; empty selected support needs explicit zero handling.
-27 abstract readiness cases show splitting one conjunction into two signals leaves earliest required SV/QK readiness unchanged under the inspected dependency model. **Not a device simulator or performance experiment.**
-Unsafe early PV example: `(2*.25)+3=3.5`, versus rescaling after adding new contribution `(2+3)*.25=1.25`.
-Slack6 scalar examples distinguish zero later rescaling from four later rescales; these are illustrative sequences, not measured frequencies.

## Future evaluation only if reopened

First consume already-retained compatible traces if any contain per-tile logits/reference moves and precise selected-reader timing. None was found or generated in this round. Fast CPU work can test proposed range bounds, exact mask/sink handling and dependency invariants; it cannot estimate GPU issue timing.

A later authorized kernel comparison must preserve complete selected supports, cache bytes, original reductions/rounding contract or explicitly validate the changed numerical path, sink/empty rows, decoder graph shapes, all actual CTA variants and exceptional values. Compare against existing slack6 Mega implementation, not an always-rescaling straw baseline. Include reference estimation/guard/replay, barrier overhead and output quantization in elapsed cost.

Existing Mooncake and agent-75 can measure long-output ITL, TTFT, request E2E, goodput and tail guards for an eligible arm. They cannot reveal per-tile rescale counts or a silent numerical support change by aggregate throughput alone; a bounded component/correctness diagnostic would supply that missing observable. No new workload is justified solely by the paper's long dense context. No GPU work is authorized here.

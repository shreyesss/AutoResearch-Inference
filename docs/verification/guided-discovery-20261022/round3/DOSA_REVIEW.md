# Independent DoSA transfer audit

## Decision

**Advance a bounded CPU numerical-contract diagnostic; defer a target kernel port and service qualification.** The useful new mechanism is certified head pruning during prefill, scoped first to a non-producing indexer. It is not a turnkey flag. Unknown ROI is not itself a rejection, but the current short-context and long-output-ITL objective supplies weak exposure evidence.

## Source grounding

Paper: https://arxiv.org/html/2610.13990v1 . It handles signed ReLU weights using positive residual bounds and a lower bound on omitted negative subtraction. Strict upper-bound rejection retains equality; seed scores must come from enough distinct visible keys. Prefill screens heads; decoding retains full-head scoring and uses temporal witnesses for selection. The FP8 numerical certificate requires separate dominance over computed reference scores, not just real arithmetic, plus complete recovery on invalid/overflow cases. Those are relevant reusable mechanisms; headline results on other models and long contexts do not predict our result.

Code: llm-sys/dosa-sglang `582a8a151d5b14bd3b9d79e932a6390638d11e5a`, reached from report repository `d744698bb452433b16a7c7cb4a8d7094e06cdecb`. Independently inspected worker-pinned files in `round3-attention/sources/`:

- `dosa.py:18,52–71`: fixed TOPK2048, FP8 Q, FP32 weights, fixed FP8 cache layouts. This cannot directly consume target packed MXFP4 Q/K and BF16 consumer weights.
- `planner.cu:59–90,298–357`: actual directed FP64 arithmetic, outward float conversion, invalid-input checks and reference/screening allowances. The certificate is implemented, not merely a proposed theorem. This inspection is not a complete kernel correctness audit.
- `dosa.py:130–152,493–496`: recovery reaches original-score recomputation and full-domain selection, rather than merely selecting again from incomplete survivors. For our sparse consumer, full domain means all original visible candidate tokens; expanding to all KV changes target semantics.
- `select.cu:184` guards boundary/temporary capacity. Porting requires preserving error propagation, score ordering, ID mapping and complete recovery.

## Exact target branch matters

Pinned vLLM `c4557869393db4d75c483d92edd02a5125500883`:

- `models/deepseek_v41/attention.py:1325–1328`: producer publishes candidate blocks as well as its token selection. Consumer indexers select within those blocks.
- `attention.py:1418–1463`: sparse scoring is **opt-in** through `attention_config.indexer_sparse_logits`, only for candidate consumers. Producer and earlier indexers remain dense. Consumer weights become BF16; dense-path weights remain FP32. Do not assert every indexer currently uses the sparse path without effective config evidence.
- `model_executor/layers/sparse_mqa_indexer.py:78–85`: MXFP4 candidate-consuming path is SM100-specific and uses BF16 weights.
- `model_executor/kernels/attention/dsa/sparse_mqa_logits.py:273–280`: DeepSelect operates on BF16 sparse scores. Casting them back to FP32 does not recreate higher precision scoring.

MXFP4 group scales do not invalidate the mathematical signed-ReLU bound: reconstructed effective vectors still admit it. They invalidate direct reuse of a scalar-FP8 encoding/error model. Build a bound over the actual payloads, group scales, accumulation, weighted reduction and final rounding. Changing to FP8 to fit the public implementation changes a separate accuracy/precision variable and cannot establish exact equivalence.

## Two executed CPU falsifiers

`contract_falsifiers.py` and JSON are pure arithmetic illustrations, not target activations or GPU tests.

1. **Computed-score dominance:** real score and valid real upper bound1.004 round to BF16 reference1.0078125. Comparing the real upper to a seed threshold in reference arithmetic falsely prunes a boundary-tied candidate. Under an explicit lower-ID tie rule it changes the winner. This does not assert the target uses that tie rule; it shows why the rule and reference rounding must be pinned. An outward reference-score allowance repairs the premise.
2. **Producer dual output:** an illustrative tokenK1 threshold discards a score needed by blockK2. Therefore a token-only certificate cannot preserve producer candidate publication. First exclude producer layers; later use a separate block-winner certificate if worthwhile. Preserve newest-block pinning and all-minus-infinity handling as part of that output contract.

## Selective reuse and genuine difference

Existing proposals include candidate-only scoring, DeepSelect/selector choice, score/writeback fusion and index-to-KV mapping fusion. Those avoid irrelevant keys or selection traffic after full head scoring. Certified omitted-head evaluation is a distinct additional change **within the same retained candidate domain**. Its decoding witness-selection branch overlaps existing temporal/selection directions and should not be counted as another novel accepted idea without a specific missing implementation delta.

A practical first scope is prefill in consumer-only layers, preserving the producer unchanged. A dense non-producing indexer is another possible scope, but needs its own reference dtype and visibility contract. Do not combine these into one untested blanket acceleration.

## Minimal gates and outcome measurement

1. Resolve effective sparse mode and exact scorer, query/key formats, tie rule and exceptional values. Source pin does not prove live container equivalence.
2. Use a CPU reference over the *actual formats* and small adversarial fixtures: signed/zero weights, zero anchors, cancellation, scale extremes, near-boundary ties, padding, disjoint candidates and invalid/overflow recovery. Establish a conservative bound; synthetic pruning rates are not deployment yield.
3. Reuse existing saved target activations if available; do not run GPUs to collect them. Measure survival ratio, planned heads, seed/plan overhead proxy and visible compressed-domain sizes. If such data is absent, empirical usefulness remains unknown.
4. At K512, seed scoring requires at least512 distinct visible tokens for a conventional threshold. When the domain is no larger thanK, there is no topK head-pruning benefit. Consumer capacity2048 blocks times8 positions limits the scanned domain to16384 compressed positions before bounds; raw prompt length is not the relevant denominator.
5. Future authorized test must compare the original exact sparse scorer/DeepSelect path against screening+refinement+selection+recovery, retaining complete component timing and memory. Use existing Mooncake/agent-p75 if their actual prefill schedule exposes the regime. Add numerical/candidate-domain differential tests for correctness, not a new long-context serving benchmark to manufacture a target-suite win.
6. Promotion needs measured target-suite TTFT/goodput with ITL tail guards and unchanged correctness. No accepted-token or theoretical FLOP proxy substitutes. No numeric service-gain forecast is justified now.

## Audit scope

No GPU use, compilation, model execution, serving changes or canonical memory writes. This reviewer independently read the relevant author and pinned target branches and executed two CPU contract falsifiers. It did not prove the entire author implementation correct or measure target activation geometry. Signed weights and precision differences are engineering obligations, not grounds to reject the reusable mathematical idea outright.

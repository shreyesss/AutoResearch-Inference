# Round95 — exact-output operator fusion screen

## Decision

**Zero new formal hypotheses and no new runtime component qualified.** One newly read October paper supplies a useful comparison method, but its concrete operation does not match the inspected target. Two tempting manual-fusion transfers are already implemented on the relevant target source paths or belong to a different model/backend. The negative screens remain explicit; this is not a claim that the target has no remaining fusion opportunities.

Target: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, frozen Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, planned B200 TP1/DP4/EP4, baseline d464. These are source/configuration pins, not live deployment attestation. No GPU, native/model imports, compilation, serving changes, canonical/cloud writes or paid model calls occurred.

## Prior coverage and adaptive retrieval

Complete compact recall contains 153 cards over two pages with stable inventory hash `8cc1793bcb8a602cfee8b83c71abb69678d31c1eed23ca6b6a08a87b8913a8b8`. Bounded canonical read-only report searches complement it for operator fusion, persistent compiler, mKernel, normalization and activation handoff. MF19/round29, OP36, NQ33, PJ01, CF59, Meld/round77 and mKernel/round69 already cover obvious producer handoffs, reductions, discarded projections and persistent scheduling. This is literal/manual coverage, not a semantic novelty certificate. The separate round96 index-K producer task was excluded.

1. OpenAlex `GPU inference operator fusion small batch`, October 1 inclusive through October 23 exclusive, returned 10 identities. Several results used “fusion” for feature or sensor fusion and “small batch” for industrial sorting. Potentially relevant papers mostly concerned WebGPU/Intel, compressed tensors, or methods rather than a missing NVIDIA operation.
2. The explicit arXiv query required GPU, kernel/operator fusion or megakernel, and inference/compiler. Its window was widened to September 1–October 23 and the small-batch phrase was deliberately relaxed. It returned 5 identities. Weave is already N03; Argus is measurement methodology. The newest TrainBridge paper warranted one targeted full-text read.

All 15 identities and abstract dispositions are preserved. No additional provider query was needed after the concrete source comparison failed to expose a new operation. The second expand attempt initially declared an undeclared relaxation and failed; the plan was repaired after the query had run. This ordering is retained, not presented as a successful pre-query expansion.

## Selected primary paper: TrainBridge

**TrainBridge: Agentic NPU Training Optimization Guided by GPU Compilation Evidence**, arxiv2610.29171v1, 21 October 2026, was retrieved with one actual fulltext cache miss through `investigate`. The exact-source lookup found no retained title/ID before fetching. I read its mechanism, KeyShift example, evidence-transfer procedure, measurement setup and validation criteria. The linked repositories were enumerated by the dossier but not selected or fetched; no donor implementation is claimed inspected.

The paper compares eager and compiled execution of the **same GPU training program**, identifies an eliminated operation, then checks whether an equivalent inefficiency remains in an NPU implementation. Operators, dtypes, layouts, intermediates and launch boundaries are the matching evidence. This is a transferable research method without requiring neural training in our system. It does not establish that arbitrary source code with multiple operations is inefficient or that enabling a compiler will preserve the target numerical contract.

Its concrete example is KeyShift: half the key features shift by one sequence token through overlapping-slice updates. The NPU rewrite removes ViewCopy overhead. The reported local result uses BF16 `[1,24576,6,128]`; broader results concern H100/Ascend 910C training, with validation-loss/accuracy criteria and tuning time excluded. None of those gains or correctness thresholds transfers to target decode ITL or exact output.

## Target and PR triangulation

### Screen95-A — KeyShift functionalization: rejected direct transfer

The inspected target attention preparation projects the current query and uses explicit normalization/RoPE/cache operators. The selected target files contain no KeyShift/key_shift or ViewCopy expression, and the actual dataflow read confirms no equivalent half-feature previous-token shift in that preparation path. The target compressor’s grouped latent construction and paged insertion are different semantics. This is bounded source absence in the relevant inspected path, not a whole-repository proof that every overlapping view update is absent.

Removing a model-specific shift would be wrong if the target had one; replacing an implementation of the same shift could be valid. Here no matching operation was identified, so there is no runtime proposal or reason to build a toy speedup case. Reopen only with an exact target operation plus consumer that matches a concrete donor transformation.

### Screen95-B — move generic MLA compiler fusion to this model: source-present or mismatched

Canonical read-only PR scouts were capped at 15 per query. The two selected opening records were imported into isolated state and replayed through actual `pr-search`; that replay covers only those two records. No live PR diff or donor test was executed.

- vLLM#45573 ports a compiler RoPE/cache fusion to manual fusion and reports DeepSeek-V2-Lite/RTX PRO 6000 testing. Its posted on/off latency numbers are close, not target performance evidence.
- vLLM#43772 describes manual Triton MLA attention+FP8 quantization for the DeepSeekV2/TritonMLA path. It does not establish missing fusion in V4.1 MegaAttention.

Pinned target `attention.py` already calls fused Q/KV RMSNorm, with an eligible branch sharing normalized quantized Q. `_prepare_and_attn` overlaps Q/SWA preparation with compression, then main-cache insertion with indexer preparation. `_fused_qnorm_rope_kv_insert` explicitly invokes the packed-cache fused normalization/RoPE/quantization/cache operation. These are actual source calls, not compiler-optimization assumptions. Backend eligibility and active runtime selection remain conditional.

For the MegaAttention source path, output allocation supplies FP8 values and packed scales, and `_o_proj` states and consumes the attention kernel’s inverse-RoPE/FP8 output directly. There is no extra generic attention-output quantization stage to remove there. The subsequent BF16 WO-A result feeding WO-B remains the separate **OP36** hypothesis and is not recounted. Generic fallback backends can differ; this screen does not claim universal fusion coverage.

### Screen95-C — semantic eager/compiled comparison: retain as method, not hypothesis

The paper supports inspecting a matched source transformation and verifying the destination inefficiency, rather than importing an entire training package. This is consistent with the campaign’s current source/consumer critique. There is no retained matched target eager/compiled artifact pair here, and compilation is prohibited in this task. Thus no active compiler gap, eliminated kernel, or skill-quality improvement is demonstrated. No new tool or skill patch is justified merely by reading this method.

## Next decision and evaluator relevance

The cheapest useful reopening evidence is **one concrete target subgraph with a materialized intermediate or redundant operation plus a compatible transformed counterpart**. It must include the first useful consumer, mutation/alias ownership, shapes, stream/graph boundary and numerical policy. Existing MF19/OP36/PJ01/CF59 dossiers already supply stronger specific opportunities than this screen. Do not run another generic fusion query to rename them.

No new numerical or performance experiment is proposed from these results. If a matching operation emerges later, existing Mooncake/agent-p75 serving measurements remain the benefit evaluator, with operation-specific output/cache correctness checks. Current evidence cannot establish critical-path exposure, throughput or client ITL, and no arithmetic ROI is invented.

## Yield and limitations

Two provider queries, 15 returned identities, one new versioned fulltext read, two retained PR opening-record replays, two exact pinned target code files, eight exact source quotations. Three explicit screens: one direct-operation rejection, one source-present/mismatched fusion rejection, one retained research method. **Zero formal hypotheses, zero implementation promotions, zero GPU tests.** No source-level proof of general optimality or global literature coverage.

Navigation failures are preserved in the tool ledger: wrong expand CLI option, wrong isolated ledger location producing empty recall, and undeclared query relaxation. Corrected recall found 153 records before detailed full-text selection; initial empty receipts remain. One broad output was truncated, followed by bounded title/abstract and function reads. These are agent mistakes, not provider failures or evidence of improved hypothesis quality. Local isolated records are retained with deferred snapshots; no S3 or fresh-machine recovery is claimed.

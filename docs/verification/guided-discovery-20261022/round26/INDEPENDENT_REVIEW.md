# Independent source review — round26 Engram WKV DAG

**Verdict: retain the source refinement; keep A01 deferred.** No blocking factual correction found in the frozen report. This review confirms a dependency opportunity and a queue-order constraint. It does not establish an executable scheduling change, numerical equality, actual workspace alias or service gain.

Reviewed frozen `round26-engram-wkv-dag/REPORT.md`, source/manifest, prior identity, decision delta and arithmetic probe. All frozen artifact hashes and listed source hashes checked successfully. Only Python standard-library source parsing and arithmetic were executed; no vLLM, Torch, CUDA, FlashInfer, MPS or model imports occurred. Originals were not modified.

## 1. Actual order and events

In retained `vllm__models__deepseek_v41__nvidia__model.py`:

- Lines 778–817 create one shared prefetch stream for CPU-offloaded Engram and pass it into the local decoder layers.
- Lines 977–1041 compute current-forward hashes and iterate local layers in order, calling `prepare_embeddings` before decoder execution. The batch path is an explicit alternative.
- Lines 559–575 finalize the preceding residual/mHC state and call Engram at the injection boundary. This supports keeping the gate at its original dependency point.

In retained `common__engram.py`:

- Lines 1541–1543 explicitly serialize offloaded lookups on that shared stream.
- Lines 1620–1641 select background versus inline execution. The background path waits for current-stream producers, records hash storage on its stream and records the layer's own event **after its lookup**.
- Lines 1644–1655 wait on the layer's event, not completion of all later stream work. Thus the existing layer1 consumer need not wait for lookup14 merely because they share a stream.
- Appending WKV1 to that stream after both lookups have been queued would introduce lookup14→WKV1 FIFO order. Waiting only on lookup1's event does not remove this queue dependency. Inserting WKV before lookup14 instead delays lookup14; a separate stream removes FIFO but not hardware contention.

The inline branch uses the DP-wide maximum count and must keep the all-rank policy. The ordinary event diagram is conditional on the shared-host/background route. `EngramBatch.create` lines1443–1455 rejects effective table dp_size1; its private-sharded route stages/exchanges/unpacks all layers before exposing each `QuantizedActivation` (1458–1516). That collective path cannot be moved using the simple shared-host diagram. Shared host capacity fallback remains an activation question, not a settled live fact.

## 2. Projection shape and multiplicity

Exact config `text_config.engram_layer_ids=[1,14]`, max_ngram4, heads8, head_dim256, hidden5120 and hc_mult4. Constructor lines1554–1567 give **logical input 6144 and logical output25600**. There are two Engram WKV calls in an enabled full target forward owning both layers; no 40-layer or nominal five-draft-step multiplier is justified.

This is a logical shape, not evidence of a local shard's installed physical tensor shape on every layout. The source uses ColumnParallelLinear with output gathering; actual TP, sequence parallelism, PP ownership and rows affect execution. Planned TP1 would remove that TP-column distinction, but the historical immutable A01 baseline is not silently replaced by that planned baseline. Hash/profile skips and dynamic actual row counts remain conditions.

## 3. Input availability and remaining hidden-state dependency

AST inspection of `Engram.forward` found exactly the two alternative WKV input expressions:

```python
self._batch.wkv_input(self, hash_ids.shape[0])
self.embed(hash_ids).flatten(-2)
```

Neither depends on `hidden_states`. The later `_fused_engram_post_wkv_kernel` receives both hidden states and projected KV (1693–1730), confirming the projection/gate distinction. The weights are fixed within inference. Early launch still requires lookup completion, any relevant TP/DP exchange, identical token ordering/count and preservation of staged rows/scales until consumption. Host-side availability of a Python object is not proof that its device producer has completed.

## 4. Quantization, workspace and lifetime scope

The quantization branch is conditionally supported by source: block32×32 + E8M0 nonignored LinearBase dispatches static MXFP8 weights/dynamic activations (`quant_config.py`221–243). Named CuTeDSL wrapper processing stores column-major `[K,N]` weights and swizzled scales; apply either takes matching QuantizedActivation or quantizes raw input. It calls vLLM `mm_mxfp8`, which forwards `out=None` to external FlashInfer (`utils__flashinfer.py`1054–1074).

`WorkspaceManager` selects by ubatch/lane and documents stream-aware keys when persistent-resource users overlap (124–145). This does **not** show that the named external GEMM uses that manager or that two real operations alias. The report correctly retains unknown external scratch ownership as an inspection gate. No actual conflict, safe overlap or graph capture lifetime was demonstrated.

Staging, result and any quantization-scale lifetimes must be checked independently. The layer1 and layer14 work could safely share storage if their actual lifetime intervals do not overlap; merely using different streams proves neither safety nor unsafety.

## 5. Arithmetic probe audit

Extracted and executed only the pure `scenario` function from the frozen probe. Replayed1,024 invented parameter combinations and verified the stated upper bound, readiness and lookup14-delay identities. Reproduced baseline15, late-append21, separate-stream11 and contention17 from dimensionless input values. This is a check of the author's arithmetic, not independent evidence about GPU timings or CUDA scheduling.

The model assumes its supplied service times, serialized queues and a conservative pre-MegaMoE fence. It omits real overlap-dependent service times, launch/quantization/event overhead, rank skew, capture behavior and whole-forward effects. The delayed layer14 readiness is a necessary cost to inspect, not a complete estimate of its eventual service penalty. The report labels these limits adequately. Four interval examples are illustrative supplied ranges; they do not identify an actual allocation or ownership violation.

## 6. Decision and next observation

Preserve existing A01 identity `hypothesis:36794075a7034c3f1ff100e73c1d8436a4606397c8e07766ed5388ef64b16646`, its immutable historical baseline and deferred disposition. The strongest positive is independently available projection input; the strongest counterweight is queue/resource interference plus unresolved graph/scratch lifetime.

The cheapest decision-changing next evidence is a saved compatible dispatch/stream trace or exact external implementation audit showing the relevant backend, ownership and legal window. An endpoint result alone cannot prove those lifetimes. No new runtime or GPU command is authorized by this review. No additional literature search was required to review this source question.

Artifacts: `source_check.py`, `checks.json`, `review.json` and `manifest.json`. The check's shape counts and arithmetic are source/symbolic observations only; implementation/service qualification remains inconclusive.

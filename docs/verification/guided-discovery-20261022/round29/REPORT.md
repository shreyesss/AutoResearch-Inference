# Round29 — MF19 output fusion for the small-row overlap path

## Decision

**Keep MF19-01 deferred; retain a distinct implementation arm within the same hypothesis.** Existing ID `hypothesis:ad1fb886045bbfd8c17b1fbc2746dbf3a79089b61e4977a50825c8e75482000e`, baseline `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`. No new hypothesis identity, changed baseline, implementation or service qualification.

The original donor arm cannot help captured small-row cases that take mHC overlap: its overlap branch returns no packed output. **The existing overlap input kernel nevertheless already owns the final normalized values.** An optional output epilogue could write the same BF16 result plus MXFP8 values and both required packed scale layouts, without replacing the overlap schedule or recomputing normalization in another kernel. This is a supported integration proposal, not an existing capability or a compiled implementation.

The proposed adaptation selectively reuses donor #57977's output descriptor/consumer staging contract. It adds a new producer epilogue to the pinned TileLang input path. It does not transfer the donor compound10% GPU-busy claim, disable overlap, change routing or claim a target speedup.

## Exact sources and scope

- Target source `c4557869393db4d75c483d92edd02a5125500883`, planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, TP1/DP4/EP4 within each four-B200 group. Source is not live deployment attestation.
- Donor vLLM PR57977, retained head `18aac3985191e3850baeb16311ac7431521349d9`. Original API/diff/full files are in frozen round19; selected exact sources and their hashes are copied here. No fresh PR status claim.
- Exact producer: `ops/mhc.py::mhc_pre_delayed_overlap` → `warmup.MHC_PRE_NORM_KERNEL` → `tilelang_kernels.py::mhc_pre_big_fuse_with_norm_tilelang`, `split_mode="input"`.
- Consumer: pinned `prepare_megamoe.py::_quantize_fp8_groups` and shared-scale address expression; donor `MegaMoEInputs`, `MegaMhcFp8Out.for_mega_moe`, `hidden_states_staged` and `prepare_megamoe_inputs(None, ...)`.

Only retained sources were needed. **Zero new online queries**: the outstanding question was an exact producer/consumer contract, and another paper search would not resolve compiler layouts, ownership or exposure. No Torch, TileLang, Triton, CUDA, MPS or model imports; no compiler/build or GPU call.

## 1. What currently runs for small captured rows

`c455-model.py`506–513 permits mHC overlap only under FULL graph capture, positive local rows≤16, and the support predicate. Captured graphs preserve that selected path on replay; eager warmup is not its runtime trace. `supports_mhc_overlap` allows the relevant B200/hidden5120/hc4 shape and excludes ubatching; it does not require TP4. Actual scheduling frequency is unknown.

At the FFN boundary the caller joins the earlier coefficient stream, performs shifted post/pre, then calls FFN/router; after FFN it joins the newly produced coefficients (`c455-model.py`625–650). In `mhc_pre_delayed_overlap`:

1. A BF16 normalized `layer_input` is allocated if the caller did not supply one.
2. The input epilogue runs on the caller stream; coefficient GEMM and stats epilogue run on `mhc_stream`.
3. For **rows1–8**, input epilogue finishes before `stream.wait_stream(main)` releases coefficient work. Extra quantization here delays both input availability and coefficient release.
4. For **rows9–16**, coefficient work is queued first and input epilogue runs concurrently on main. Added reductions/stores can slow input/router readiness or compete with the coefficient work.

At TP1/EP4, the specialized TP4 all-reduce path is not selected (`supports_mhc_all_reduce` requires TP4 and no EP). Thus the initial arm targets `compute_input=True`, ordinary shifted input production. A supplied `layer_input` bypass skips this epilogue entirely: **it must not return a staged descriptor unless a producer actually wrote the packed outputs**. Zero rows, disabled overlap, unsupported formats and other shapes preserve existing behavior; never mark buffers ready merely because they were allocated.

The donor overlap wrapper still returns its final packed descriptor as `None`; only its MegaMHC branch writes it. Therefore this is genuinely a missing producer capability, not an already-enabled flag.

## 2. Where the extra output can be produced

The exact TileLang kernel (`c455-tilelang-kernels.py`300–503) uses one96-thread CTA per token. On NVIDIA, mix threads are0–31; collapse/input threads are32–95. In input mode only the collapse branch does relevant work. Hidden5120 yields `hidden_block=gcd(1024,5120)=1024`, five logical tiles.

Pass1 collapses four residual streams with the carried pre-mix, rounds to BF16 shared storage and accumulates squared values from those rounded values. The RMS factor is computed over the full5120 values. Pass2 loads each1024-value tile, multiplies by RMS factor and BF16 normalization weights, and writes BF16 `layer_input`.

**Proposed insertion: pass2, after explicitly materializing the same final BF16-rounded values that the existing store produces.** Keep that BF16 store for the router and any ordinary consumers. From those rounded values, compute contiguous logical groups of32, emit E4M3 bytes, pack four scale exponent bytes per int32 and write routed/shared scale layouts directly into donor-compatible MegaMoE input buffers.

This can logically occur in the existing second pass: a full additional HBM read/normalization pass is not required. It still adds group-max reductions, reciprocal/format conversions, packing and stores. The compiler may require additional register/shared-memory movement or barriers; no compiled layout/resource result exists.

**Logical contiguity is not lane contiguity.** Thirty-two groups fit a1024-value tile, but the current TileLang fragment assignment across64 collapse threads is not inspected lowered CUDA. A warp shuffle treating32 lanes as one quantization group is unjustified. A compatible implementation must declare/use a correct logical `[32 groups,32 values]` reduction or otherwise prove the emitted lane mapping. This is an implementation gate, not a reason to replace the mHC algorithm.

## 3. Exact numerical contract

Preserve both existing BF16 boundaries:

1. FP32 weighted residual collapse → **BF16** → FP32 squared-sum/RMS calculation.
2. Normalized weighted FP32 output → **BF16** → FP32 input to quantization.

The second boundary is currently implicit in `T.copy(ol, layer_input)` with BF16 destination. A fused epilogue must make the rounding explicit and use those exact values for both the BF16 store and quantization. Quantizing higher-precision `ol` is a different computation.

Pinned staging contract, per group32:

```text
amax = max(max(abs(BF16_output_as_FP32)), 1e-4)
scale = FP32(amax / 448)
exp = clamp(exponent_bits(scale) + (mantissa_bits(scale) != 0), 1, 254)
quant_scale = bitcast_FP32(exp << 23)
scaled = BF16_output_as_FP32 * FP32(1 / quant_scale)
fp8 = conversion to E4M3 (baseline uses tl.float8e4nv)
```

The conversion's rounding/saturation, ties, signed zero, subnormals and NaN/Inf behavior must match the baseline's actual lowering. The CPU fixture uses ideal finite nearest-even E4M3 and explicit saturation solely to illustrate the contract; it does not certify TileLang versus Triton conversion lowering. Do not silently assume all target activations are finite. A future differential must characterize the baseline's exceptional semantics as well.

### Executed CPU falsifiers

`contract_probe.py/json` uses standard Python only:

- **Skipping the first boundary:** BF16 residuals and FP32 pre-mix give illustrative collapsed values1.49900007 and0.50099999. Rounded inputs become1.5 and0.5. Across a5120-wide repeated fixture, the scalar normalized BF16 output differs at2560 positions if this boundary is omitted (one output0.447265625 versus0.44921875). This is a rounding-necessity example, not the compiled reduction/rsqrt tree and not a claim of final FP8 mismatch for that case.
- **Skipping the final boundary:** arbitrary final FP32 value224.300003 rounds to BF16224. Its group scale is0.5/exponent126. Quantizing before rounding gives scale1.0/exponent127 and different packed FP8 bytes. These are adversarial epilogue inputs, not observed values from target weights.
- **Scale placement:** extracted the exact integer `_shared_sf_row` expression without tensor imports;70 combinations of counts0/1/8/9/16/17/32/64/128/129 and candidate block sizes verified uniqueness and padded-capacity bounds. This does not assert which BLOCK_M the target scheduler selects.
- Verified logical group coverage5120=160×32, little-endian four-byte packing, and a finite signed-zero oracle control. None of these proves GPU lane mapping, normalization numerical identity or implementation speed.

## 4. Packed layouts and ownership

For hidden5120, each row has160 group exponents, packed into40 int32 words. Donor-compatible outputs:

- FP8 activation `x`: logical `[rows,5120]`, use the supplied strides.
- Routed `x_sf`: logical `[rows,40]` packed words, actual K-major supplied strides.
- Shared scale view:40 packed words per physical row, written through the full buffer view. Its row is:

```text
block_id = row // shared_block_m
within = row % shared_block_m
shared_row = block_id * ceil(shared_block_m/128)*128
           + (within//128)*128 + (within%32)*4 + (within%128)//32
```

Do not hardcode BLOCK_M128 or use a plain row-major copy. Use the same scheduler-derived `get_block_m(rows)` used by the consumer, retain actual strides, and require capacity `ceil(rows/BLOCK_M)*ceil(BLOCK_M/128)*128` rows. A logical small-row slice can write beyond its first logical rows into the padded backing view. Write only valid row/word locations and preserve original unused-padding semantics.

Donor `get_symm_buffer` caches by EP group/device/shape/format, **not layer or ubatch**. Early output therefore writes shared step storage; shape compatibility alone is no ownership proof. Initial scope remains no ubatching, one sequential caller-stream chain, unchanged collective order and proper warmup/capture allocation. The coefficient stream must never write these packed outputs. Preserve existing first-launch synchronization and dependency/PDL ordering; do not infer safety for concurrent forwards or arbitrary stream overlap.

The intended readiness boundary is simple: only after the input epilogue genuinely emits BF16 plus all required FP8/scale outputs may the FFN call receive `hidden_states_staged=True`. Later routing/EPLB still runs, retains physical remapping and padding handling, and stages its own IDs/weights. No changes to quantized weight format or EP communication are proposed. NVFP4 activation API is excluded; the intended target's MXFP4 expert weights use MXFP8 activations, which is the relevant donor input contract.

## 5. Smallest patch boundaries, not an implementation claim

| Component | Bounded change |
|---|---|
|FFN model boundary|Request donor-compatible MegaMoE input slices for eligible MXFP8 steps; keep BF16 router input and existing coefficient waits.|
|`mhc_shifted_post_pre` / `mhc_pre_delayed_overlap`|Thread optional packed output descriptor into the actual input producer; return populated descriptor only for a producing branch. Existing bypasses returnNone.|
|`MHCPreNormKernel.CompileKey` / warmup|Add a bounded input-output variant/layout key and matching warmup enumeration. Keep stats mode signature/behavior compatible and avoid lazy new allocations/compiles during graph replay.|
|TileLang input epilogue|Keep collapse/RMS and BF16 output unchanged; add per-group max/conversion/packed routed+shared stores from final BF16 values. Prove fragment layout.|
|MegaMoE consumer|Reuse donor staged-activation path and validation; skip activation staging only, preserve top-k/EPLB/routing work.|

This is more than toggling donor `fp8_out`: it requires a producer kernel extension and wrapper/warmup/consumer plumbing. It is smaller than replacing mHC or importing the donor's attention and routing optimizations together.

## 6. What could improve, and what remains

Baseline small-row activation staging uses BLOCK_M1/BLOCK_K128: forty CTAs per row in the combined staging launch. The proposed arm avoids reading5120 BF16 values again (**10,240 logical bytes per row**) and removes activation work from that staging launch. FP8/scale writes still happen, and quantization arithmetic moves into the earlier producer rather than disappearing. The BF16 store remains. This is source-level work accounting, not measured HBM traffic or latency.

With routing staging retained, the donor skips activation work but **still launches** staging on one K tile to pack top-k. Therefore do not claim an entire kernel launch disappears. The earlier producer gains160 group reductions and FP8/scale stores per row, potentially raising registers/shared memory, delaying router readiness and—for rows1–8—coefficient launch. Savings may be zero or negative. No target component exposure or scalar ROI estimate exists.

The original arm remains for eligible MegaMHC shapes. This refinement addresses a different producer branch under the same “consume already-produced quantized FFN input” mechanism. Count one MF19 identity, not a second accepted idea or additional qualified yield.

## 7. Rejected shortcuts and future evaluation

Rejected as scoped: return a nonnull descriptor without writes; quantize unrounded normalized FP32; disable overlap to force MegaMHC; infer a32-lane reduction from32-value groups; borrow the TP4-only all-reduce producer in TP1/EP4; skip routing/EPLB merely because activations are staged. A standalone post-producer quantization pass is not this fusion and does not establish reduced launch count versus stock combined preparation.

Next implementation gate, only if separately authorized: compile/lower the exact epilogue variant and inspect group mapping/resource usage; then compare BF16 outputs, FP8 bytes, both scale layouts, routing IDs/weights and expert results at rows1/8/9/16/17, ragged/padded/zero rows and repeated shape changes. Preserve the supplied-layer_input bypass negative test and capture/eager selection. Runtime tests must compare stock overlap, original donor arm and refined overlap-output arm independently, including coefficient delay and total iteration time.

Existing agent-p75 and Mooncake can test ITL/TTFT/tails/throughput at matched workloads. Extra event/kernel instrumentation is needed to attribute earlier input readiness versus coefficient interference and the remaining routing launch. No new benchmark is required solely to obtain an endpoint score; no source arithmetic certifies that score. No GPU experiment was run or authorized here.

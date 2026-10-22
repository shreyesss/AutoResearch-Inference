# Independent router producer/selection screen review

**Agree with zero new cards and a parked small-row component.** MoRE's running selection is selectively reusable without its learned low-rank replacement, but the target already fuses projection/selection on the larger-row native Mega path. Its small-row split is a real conditional source boundary; a donor win against a different fused baseline does not establish a win there.

I read the relevant MoRE fulltext passages, pinned target dispatch/GateLinear/top-k code, FI6129 opening/numerical/benchmark claims, host schedule diff and selected generated reduction changes. All 33 changed-file patches are retained and inventoried; I did not audit every generated instruction or execute the donor. All 38 author artifact hashes and six target-copy hashes match.

## Target comparator and numerical contract

The native Mega forward picks threshold1 for128experts and16 otherwise. The main384-expert target therefore uses GateLinear plus fused_topk_bias at padded M<=16, and bf16_mega_gate above that. This threshold applies only after native-Mega eligibility, not universally to every router/backend. GateLinear has several dtype/quantization/batch-invariance paths; eligible BF16 input/weight reaches the specialized low-latency kernel. FP32 output is not evidence of FP32 weight storage. Actual backend and row occupancy remain unknown.

The selected small-row top-k kernel already handles sqrtsoftplus, bias-assisted selection, unbiased selected weights, sum normalization/scaling, padding and stable smaller-ID tie choice. It also sanitizes NaN ranking values while selected weights follow the original expression. A replacement must preserve the complete stated contract, including exceptional inputs, rather than assume mathematically monotone score transforms imply identical finite-precision results.

FI6129's exact target-size shapes make it relevant. The host diff really introduces sixteen-way splitting and the SM100 cluster-token route. Nevertheless its reported native comparator is DeepGEMM39d8 fused gate, not the selected <=16 target sequence. The body acknowledges changed normalized weights from a different compensated reduction; improved FP64 error is not bitwise reference equivalence, and sampled top-k agreement is not an all-input near-tie proof. Repeated identical donor outputs establish determinism of that donor, not agreement with the pinned target. The changed numerical policy is a declared gate, not evidence the component can never be useful.

The donor's cold-L2/direct-kernel GPU-span measurements and source/export retention ratios must not become our long-output ITL prediction. The source/export tables chiefly test fidelity of delivered schedules to their source implementation. A missing matched target comparator and missing target critical-path exposure are enough to withhold qualification even if every donor number is reproduced.

## Selective follow-up

Keep the running-selection/fused small-row schedule as a component lead. If retained target traces identify substantial exposed router time, compare the actual GateLinear+dsv4_topk path, native fused gate and donor under identical loaded dtype, shape, bias/routing options and graph mode. Preserve expert IDs and normalized weights under the agreed numerical contract before measuring service impact. No additional synthetic timing or invented percentage is useful now.

The reported3072*Mbytes are logical score store/read traffic; they can be cached and are small relative to gate weight reads. Eliminating that traffic or a Python-visible launch is not a sufficient materiality argument. Existing PDL, native fused routes and changed reduction pressure further prevent additive savings estimates. Standard Mooncake/agent75 remain the eventual service tests; no new serving harness is required by the current evidence.

No GPU/network/canonical mutation or new hypothesis selection was performed in this review.

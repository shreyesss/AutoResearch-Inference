# Round73 — exact Engram remainder arithmetic

**One scoped deferred experiment proposal, ER73-01; no implementation/service qualification or performance forecast.** The target's n-gram hash kernel uses runtime-loaded prime divisors. These divisors are fixed by the model layout. There is a concrete exact-arithmetic arm: precompute divisor-dependent constants and retain the same rolling hash, output buckets and launch. The CPU range proof survives; native lowering, constant ownership and exposed cost remain gates. Unknown timing alone does not invalidate this bounded experiment.

No GPU/native/model imports, builds, serving changes, canonical/cloud writes or Git mutation. The probe executes extracted Python prime-generation functions and integer arithmetic only.

## 1. Evidence-driven search

Read all145 compact prior cards across two pages with the same inventory hash, plus bounded standalone report matches. EG01 changes staging representation; EG02 reuses looked-up rows; A01 overlaps WKV; round51 reuses projected features; round55 prefetches future hashes; HS30 removes prompt-tail registration helpers. None is this integer remainder substitution. Compact recall does not certify exhaustive semantic novelty.

Two dated arXiv searches covered September1–October22:

1. GPU/CUDA + hashing/embedding + integer/modulo/lookup:8 abstract hits. They concern Paillier, BPE, lattice quantization, solver generation, TT embedding reuse, distributed prefix discovery, two-bit conditional memory and encrypted MoE. All are retained with dispositions. None supplied a matching exact63-bit remainder implementation; no wholesale rejection of useful inference components merely because training appears in a paper.
2. GPU/CUDA + modular reduction/integer division/Barrett:0 hits without provider error. This is bounded retrieval, not proof no recent work exists.

An explicit older, seeded lookup then retrieved [Lemire, Kaser and Kurz, 1902.01961v3](https://arxiv.org/html/1902.01961v3). Selected theorem/background/implementation sections establish exact precomputed-reciprocal methods and the compiler comparator. The illustrative direct-remainder C recipe uses32-bit numerators; it is not a drop-in for the target's63-bit values. Its CPU results are not GPU timing evidence. One selected fulltext was actually read; the dated8 remain abstract-depth screens.

Six bounded read-only local searches found the exact target source and SGLang#39138. Actual PR metadata, all4 patches and the pinned hash file were read. The merged head `a551b5744beb5ad9f50c1df8d214774404554f72` fuses decode history commit, but still uses loaded primes and `%`. Our V2 source already supplies lookback tokens and has no matching post-hash five-operation history tail. This donor therefore provides a precise exclusion, not a second optimization bundled into ER73.

The expansion tool rejected my unsupported observation status `off_topic`; its failed plan/output and corrected `irrelevant` retry remain. Early guessed source paths failed and were resolved with file search. An export helper initially assumed query IDs were corpus documents; they are not in this tool version. The corrected export retains all three complete query receipts separately and explicitly lists those absent document IDs. No query records or discovery results were invented.

## 2. Exact source gap and valid arithmetic domain

Target: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, exact Flash-1017 checkpoint revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, planned TP1/DP4/EP4. Planned baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`; no live configuration attestation.

[`common/engram.py`](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/common/engram.py)186–205 bounds odd multipliers using the compressed vocabulary size. Lines288–421 load current/history mapped IDs, replace dead/blocked values with the mapped pad ID, accumulate `rolling ^= value * multiplier`, then compute `rolling % prime + offset`. The prime is loaded from a generated buffer, not presented as a per-lane compile-time constant in this source.

Configured values:

- Two Engram layers,1 and14; maximum n-gram4;8 heads:48 total prime divisors.
- Extracting the actual source prime-generator functions gives16000057 through16000889. Per-layer bucket totals exactly match384006168 and384016682.
- Compressed IDs and mapped pad are in`[0,99092)`. Dead sentinel`-1` is replaced before multiplication. V1 valid cache values are mapped IDs, dead IDs or initialized0; V2 missing history uses mapped pad. Invalid token/history addressing is outside the existing kernel contract, not repaired here.
- With `b=floor(floor((2^63-1)/99092)/2)`, generated multipliers are at most`2(b-1)+1`. Every valid product is below`2^63`. XOR of such nonnegative63-bit products remains below`2^63`. Signed-positive remainder therefore agrees with unsigned remainder.
- Offset plus corrected remainder stays within the original per-layer table size and the current int32 output range.

This is a source/domain proof, not actual tokenization/history execution. The finite scalar cases do not establish observed hash distributions. Reducing each product before XOR is invalid; the XOR must remain unchanged.

## 3. Conservative exact arm and simpler comparator

Let`Q=2^64`, positive prime`p`, and`mu=floor(Q/p)` prepared once with the owning prime table. For`0<=x<Q`:

```
q = high64(x * mu)
r = x - q*p
result = r-p if r >= p else r
```

The reciprocal is rounded down. The approximate quotient differs from the exact quotient by at most one, so`0<=r<2p`; one conditional subtraction is exact. Because`q*p<=x`, the reconstructed product/subtraction fit unsigned64. This is a conservative integer derivation, not a claim that the paper's illustrative direct32-bit code implements this exact target arm.

`arithmetic_probe.py` checks the source-generated48 primes, product bounds and3312 scalar boundary/random cases. It catches correction-required values and explicitly falsifies truncating the numerator to32 bits, moving modulo before XOR, and omitting the correction. The arbitrary-precision reference computes the high product mathematically; it does **not** execute Triton, test GPU multiply-high lowering or certify all runtime masks/graphs. The proof covers the whole admitted integer domain; sample count is not its justification.

Same pinned source already uses a host-precomputed `FastDiv` in [`csrc/fused_muse_spark_qknorm_rope_kv_insert_kernel.cu`](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/csrc/fused_muse_spark_qknorm_rope_kv_insert_kernel.cu). That helper limits dividends below`2^31`; copying it into Engram would be wrong. It supports the component-level idea, not a target performance claim.

Required causal comparison:

| Arm | Change and decisive question |
|---|---|
| A: original loaded-prime `%` | What does the actual pinned compiler emit? It may already lower division via reciprocal arithmetic. No hardware-IDIV claim. |
| B: exact prime specialization | Can the compiler see each lane's divisor as a constant and emit a cheaper sequence? A tuple indexed by dynamic layer/head is not automatically constant; inspect real code generation and layout. |
| C: precomputed64 reciprocal | Explicitly hoist divisor-dependent preparation while retaining vector layout, one launch and exact correction. Does it beat both A and B after added loads/register pressure? |

The useful new work is hoisting any repeated divisor-dependent preparation or selecting a cheaper exact sequence, **not claiming the `%` syntax proves slow division**. No arm was implemented in the runtime.

## 4. Constants, lifetime and masks

Current configuration needs384 logical bytes for48 uint64 constants, before allocation alignment. Bind them to the full divisor tuple, layer/head ordering and existing `EngramHash` owner before captured reads. A changed model/layout requires regeneration and compatible captured pointers. Ordinary learned-weight reload does not inherently change these generated nonpersistent primes; do not invent an unnecessary per-step refresh. Sleep/wake/rebinding and actual graph lifetime still need checking.

Current8 heads exactly fill`BLOCK_H=8`. A generic masked head loads divisor1, whose reciprocal`2^64` does not fit uint64; preserve an explicit divisor1 result or fall back for unsupported layouts. Never truncate that reciprocal. No new cross-step output cache, row identity, activation representation, RNG progression or hash distribution is introduced.

Compared with HM65, this avoids a dirty-publication/copy-pool policy. Compared with AV68, it adds a real arithmetic/compiler contract and constants, so it is not automatically lower risk. These are implementation-readiness distinctions, not measured ROI rankings.

## 5. Stream placement and honest cost bound

`nvidia/model.py:975–1040` calls the hash on the **current forward stream** before embedding preparation and `_run_layers`. The hash call itself changes no stream. For the host-prefetch route, `_start_prefetch` calls `prefetch_stream.wait_stream(current)`, records hash lifetime, launches lookup on the auxiliary stream and records the per-layer completion event. The current stream continues into early layers; the corresponding Engram consumer later waits for that event. Inline/DP-sharded routes retain their separate existing behavior.

Thus the inspected source has:

```
current forward stream: input embedding -> hash -> early decoder layers -> Engram consumer
                                         |
auxiliary lookup stream:                 wait -> lookup -> completion event -> consumer wait
```

Hash is ordered before both early-layer work and lookup launch. This does not measure occupied or exposed duration, CPU launch gaps, earlier concurrent work, cross-rank skew or the service critical path. Preserving the launch means no standalone launch-count saving is claimed; CUDA graphs may further reduce host overhead already.

For this intervention alone, best-case round improvement is bounded by the **exposed removable portion of the one hash invocation**, less any added arithmetic/constant-load/contention costs. `48*N` is the logical number of hash outputs for current rows, not native instruction count. Do not multiply by40 decoder layers,3 draft layers or5 DSpark steps. Verification rows are already part of`N`; conversion to client ITL requires actual committed progress and streaming measurements.

## 6. Null branches, support branches and next step

Retain ER73-01 as a scoped deferred experiment because it has an exact supported domain, a small source delta and a cheap falsifier—not because a speedup is known.

**Stop or prefer another arm if:** A already emits an equivalent sequence; B is simpler/faster; C increases register pressure or constant-load work; native hash identities/masks/lifetimes fail; or occupied hash savings do not improve exposed round/service time.

**Support requires later authorized work:** inspect code generation for A/B/C under the actual compiler; exact hash/output differential on valid/dead/pad/history boundaries, partial blocks, changed batches, graph replay and model reinitialization; then compare whole hash kernels and full forward/serving behavior. Keep the native launch/workload and standard Mooncake/agent-p75 measurements. Add hash/lookup attribution, not an invented benchmark distribution. No native/compiler/GPU execution was run in this task.

Artifacts include all9 paper identities and3 query receipts, selected exact source/revisions, four PR patches, source/domain checks, the deferred author card and complete local command journals. One author proposal; zero typed identities or implementation/service promotions. Independent review is recorded separately when available.

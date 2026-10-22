# Round50 — paged sparse MQA launch dependency and cache hint

## Decision

Two concrete components are absent from the inspected pinned sparse path: **early metadata→logits programmatic launch** and an **evict-first hint on paged indexer-key gathers**. Both remain **deferred**, with zero implementation/service qualification. The PDL component is more actionable than a whole donor-kernel port; the cache hint is a separate, lower-confidence policy experiment. Neither should be ranked as a current default-deployment improvement without exposure evidence.

The decisive constraint is that `attention_config.indexer_sparse_logits` defaults **False** in c455. The source itself describes that path as paying off at long contexts (roughly32K+) and being slower below; this is a source statement, not our measurement. Enabling it merely to obtain the donor's small chain-level PDL gain is unjustified for the8Kagent workload. Compare PDL against an already-enabled, otherwise unchanged sparse baseline. No GPU/device/model/native imports, serving changes, Git edits or canonical state writes occurred.

## Evidence and pins

- Target vLLM: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`.
- Target DeepGEMM: `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`.
- Its exact `.gitmodules` and recursive tree resolve DeepJIT to `deepseek-ai/DeepJIT@3732a3b9a0a2e5126396908a362ba5abdf043b2f`.
- [FlashInfer#6429](https://github.com/flashinfer-ai/flashinfer/pull/6429): fetched PR API says merged2026-10-18; head `a266eeb1a390e4f78448fe903b47ac1d1ed7d47c` in `yyihuang/flashinfer`, base `eb9f0d28d08ac2b7275a1be4ad423044bc8e7569`, merge `6e453df8594472b23627ce23617aae9c8c4b468f`. All27 API file entries retained, selected Python/native patches and exact files inspected. The body's older named base/native comparison is not the target pin.
- Official [CUDA PDL guide](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/programmatic-dependent-launch.html), retrieved text retained. It describes separate release and data-visibility synchronization, opportunistic overlap and graph capture support. It does not guarantee speed or concurrent execution.

`source-export.json`:26documents,27revisions,67edges. Includes the earlier opening record and the current API-observed revision. The report does not treat the PR's claimed percentages or sanitizer results as reproduced. Primary code resolves the question; no extra recent-paper search was justified merely to decorate this source audit. The lane follows round47's paper-led PR triangulation.

## Actual target call chain

With sparse scoring enabled, `deepseek_v41/attention.py:1417+` chooses `SparseMQAIndexer` only for candidate consumers, with MXFP4 cache. Producers/pre-candidate indexers remain dense. `sparse_mqa_indexer.py:190+` calls `sparse_mqa_logits_paged_decode` with per-row contexts, physical page tables, row mapping and shared candidate buffers.

On the first consumer for a metadata instance, `sparse_mqa_logits.py:462+` expands candidate blocks and builds DeepGEMM sparse scheduling metadata. It then calls the paged sparse logits kernel. Later consumers reuse the expansion, end lengths and schedule (`sparse_indexer.py:44–46`). Thus metadata-related savings cannot be multiplied by every indexer layer. Candidate keys and queries still differ as prescribed by the model; shared scheduling is not proof of shared key-cache contents.

The native sparse metadata kernel does work distribution, physical mapping, split records and final per-SM scheduling. Its last CTA publishes the final header and resets workspace state. The logits kernel performs local barrier/TMEM/scale-padding setup, then calls `cudaGridDependencySynchronize()` **before reading the global metadata header**.

## Component P50-01: allow consumer setup during the final metadata tail

### What is missing

Pinned DeepJIT `cuda/options.hpp:207` defaults `enable_pdl=false`. Its runtime constructs these defaults and merges call-specific overrides; `cuda/kernel.hpp:148+` installs the launch attribute only when enabled. DeepGEMM's inspected initialization changes compiler options, not these launch defaults. Both sparse launch initializers omit a PDL override. The sparse metadata kernel has no explicit early release before the last-CTA schedule/header work.

The donor has three coordinated parts:

1. Every metadata CTA emits `griddepcontrol.launch_dependents` after its claim loop, before final completion accounting/schedule stores.
2. The logits host binding sets `cudaLaunchAttributeProgrammaticStreamSerialization` when requested.
3. The logits kernel retains `griddepcontrol.wait` after its local prologue and before global metadata access.

Release does **not** mean the metadata is ready. The wait remains essential. This can overlap launch/local initialization with the producer tail; it neither removes metadata work nor allows logits to consume a partial schedule. The official guide also makes clear that overlap is opportunistic and must not be required for forward progress.

### Minimal target adaptation

Start within existing a7a kernels: add an elected per-CTA early release on the **paged metadata** branch after the claim loop; enable PDL on the paged sparse logits launch; preserve the current dependency wait, final-writer acquire/release protocol, all global stores and output arithmetic. Every launched metadata CTA, including one with no useful row work, must reach release; an early-return path must not omit it. Actual captured graph launch attributes/dependency edges require verification; the existing wait instruction alone does not establish those edges. Do not port the donor's generated fixed-geometry kernel, layouts, test conclusions or broader single-writer changes wholesale.

The donor includes both runtime and exact148/152SM metadata variants. Its paged MXFP4 logits binding uses896threads and232448bytes of dynamic shared memory. Those facts constrain its measured co-scheduling; they are not proof of native target availability or speed. Preserve target's actual geometry/ABI. The target may not co-reside the two full kernels on one SM; setup on other freed SMs is still possible, but unmeasured.

### Priority and falsifier

Deferred, exposure-first. No active flag, captured pair, metadata-tail duration or prologue duration is attested here. If the flag is off, current-path exposure is zero. If the schedule is reused, there is no new metadata producer to hide. If producer tail or consumer setup is negligible, launch overlap may not matter. The source checks establish a missing mechanism, not useful service time.

## Component P50-02: independent paged KV-data eviction priority

Native paged sparse copy loops use `ptx::cp_async_cg<256>` for key data and separate64B scale copies. The donor keeps those addresses/transfer sizes but optionally uses an L2 evict-first cache policy on **key data**. Scale loads remain separate. Eviction hints can reduce interference with more valuable cache contents, but may also discard keys reused by later queries or indexer consumers. This changes a hardware cache hint, not logical prefix-cache eviction.

Donor policy thresholds are MXFP4mean-context<=32768 and MXFP8<=8192. `SparseMetadataPlan.kv_context_tokens()` sums bound context lengths, divides by vector length with floor, and performs one `.item()` host read. `SparseMqaPlan.__init__` resolves the hint once. `run()` does not recompute it after in-place context edits. A context mean is not selected-key traffic, cache reuse distance or per-request fairness; native DSpark flattened rows can also weight that mean by verification rows.

**Do not import that `.item()` as a per-step hot-path policy.** A future first diagnostic should use two fixed hint arms in the existing native kernel, holding PDL off and preserving addresses, predicates, scale copies and graph shape. Only measured results could motivate a CPU-available or device-side policy. The donor threshold is not a universal B200 tuning law. The source gate applies to a different native baseline and does not demonstrate our real warm-cache behavior.

Status:deferred/low priority, independent from P50-01. Same hint vocabulary as WP38's routed-weight locality experiments does not make this the same intervention: the first consumer and data reuse are different. No claim that its benefit compounds with PDL.

## Negative branches and contrary evidence

1. **Whole generated kernel transplant:** not qualified. Donor fixed page/block/capacity layouts, generated bindings, numerical tests and baseline differ. Selective changes to native launch/hint code are smaller and avoid assuming ABI equivalence.
2. **Single-writer metadata repair:** no fresh target bug established. Native a7a already confines final header/reset stores to `thread_idx==0`; donor codegen repair is not evidence this native path needs the same fix.
3. **Multiply PDL savings across all consumer layers:** refuted by existing schedule reuse.
4. **Enable sparse scoring just to gain PDL on8K:** not supported; source default isoff and documents a short-context disadvantage. Enabling sparse mode is a separate comparison, not a free baseline change.
5. **Apply sparse pair result directly to default dense metadata→logits:** stopped after exact source follow-up. Native dense paged metadata already calls `cutlass::arch::launch_dependent_grids()` near entry. In c455, dense scheduling is built/refreshed by metadata construction and copied into its destination (`indexer.py:1744–1751`,1826–1833); model execution intervenes before logits. It is not the donor's inline metadata→logits pair. Missing launch override alone does not show useful overlap with this nonadjacent producer. A possible different Q-producer→logits pair would require a separate exact dependency audit, not relabeling this result.
6. **Context gate mutation is a correctness failure:** false. It is a stale performance policy. The hint's arithmetic is unchanged; actual native parity still needs later verification.

## Executed CPU diagnostic

`host_policy_probe.py` extracts the actual donor `SparseMetadataPlan.kv_context_tokens` method and executes it with inert scalar/vector stubs and an import hook that returns a stub for `torch`. **The torch module and donor module were never imported.** Seven input cases exercise paged mean, boundary32768/32769, floor division, skewed contexts and contiguous ends-minus-starts. Nine stub item calls include a mutation control.

The mutation control binds hint1 at contexts8192, then changes the same vectors to65536: recomputing would choose0, while the stored constructor scalar remains1. AST inspection confirms policy evaluation in the constructor and absence in `run`. Static native checks confirm the inspected release/wait ordering and default flag. These are CPU host-policy/source checks, not CUDA execution, graph certification, timing, race tests or complete numerical validation.

Initial probe guessed a class name incorrectly and failed with `StopIteration`; corrected to the actual `SparseMetadataPlan` before the successful run. No fabricated successful first run.

## Future evaluation design, conditional on later authorization

First use existing launch/config artifacts to establish sparse mode, paged route, dtype, page/candidate geometry, actual query-row/context distributions and which call constructs versus reuses metadata. No new GPU collection is authorized now.

If exposure is established, the minimal controlled sequence is:

| Arm | Metadata release / logits PDL | KV-data hint | Purpose |
|---|---|---|---|
|A|Original|Original|Pinned native baseline|
|B|Added / enabled|Original|Isolate PDL component|
|C|Original|Fixed evict-first|Isolate cache hint|
|D|Added / enabled|Fixed evict-first|Interaction only afterB/C pass|

All other model, quantization, scheduling, output semantics and workload settings stay paired. Test valid-region logits and selected token identities exactly, metadata contents, empty/padded rows, multiple metadata CTAs, dynamic contexts and graph replay; preserve sanitizer results and failures. Measure the whole pair and subsequent consumers, not just one isolated kernel with cold L2. Report first-consumer versus reused-schedule calls separately.

Existing Mooncake and agent75 are service tests for long-output ITL, TTFT and tail guards, throughput/goodput and failures. They cannot identify PDL overlap or cache policy effects by themselves, so a narrowly justified component timeline/cache-counter diagnostic would be additional future instrumentation. No Amdahl fraction or numeric ROI is available; the donor's single-digit chain improvements cannot be projected to service latency.

## Tool use, overlap and stopping rule

Actual compact recall:142-card snapshot; combined literal query had0matches, then separatePDL query5 and eviction query12 with no remaining pages. The all-card round47 inventory had already been inspected. NQ33/MF19 mention PDL but remove different work; WP38 mentions eviction for routed weights. Exact source lookup was also performed. No claim that literal recall is complete semantic deduplication.

Used selected retained PR import; original PR API/file list; four bounded `investigate` calls for6+5+2+2 exact source files, plus focused submodule/runtime/official-guide fetches. No general paper query. Cache receipts, commands, selected diffs, source revisions and negative screens are retained. Failed init with unsupported defer flag, wrong HTTP option spelling, wrong selected-tree paths and wrong relative Python path are documented rather than hidden. The init retry completed locally without S3 publication. Code-only investigation worked and exposed decisive default-path counterevidence. The next needed evidence is runtime exposure, not another broad literature search.

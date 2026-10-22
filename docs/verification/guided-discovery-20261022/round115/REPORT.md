# Round 115 — FP8 candidate-only indexer adapter

**Disposition:** one useful, source-supported adapter refinement of the existing direct-paged candidate-scoring family; implementation and effectiveness remain deferred. **Zero new typed hypotheses and zero GPU experiments.** Four concrete intervention screens are retained below, including the rejected direct transfer and excluded policy change.

## 1. Decision and scope

The new paper did not reveal a missing proposal/refinement algorithm: Flash1017 already has a candidate-source indexer and later candidate consumers. It did direct the search toward whether those consumers actually avoid full-context scoring. The pinned implementation has a sparse scoring path, but restricts that path to an MXFP4 indexer cache. Its **source default indexer format is FP8**, and sparse logits are source-default disabled. Effective deployment settings have not been attested.

Upstream vLLM PR **62011**, pinned at `LopezCastroRoberto/vllm@40b510fd35be53efd662f5a7b687cee44cf146bb`, supplies a narrow missing adapter: use the existing FP8 payload and MX scale encoding with the already-supported FP8 branch of DeepGEMM sparse MQA. This could avoid dense scoring of positions outside the existing candidate blocks without changing cache precision or the candidate policy. It is worth preserving as a future manual-opt-in experiment, conditional on eligibility and numerical/token equality. It is not a demonstrated serving improvement.

This shares its central mechanism with prior `hypothesis:ebbeb3770815c1a4f41305f14c23ad88eb1d0b7ee21f60ff4115237924d0865f` (`h200-attn-20261020-02`). That prior used a different model/runtime/hardware baseline and alternative direct-paged implementation. We retain an SM100/c455 ABI refinement without rewriting the old card, importing its H200 performance scenarios, or declaring a new algorithm identity. Prior AT01, AT02, MP17, CR64 and round57 address screening, sharing, mapping or memory access, not this FP8 host-interface gap.

Planned baseline: Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, callgideon/vLLM `c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, B200 TP1 DP4 EP4, baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`. These are source-plan pins, not a loaded-server receipt. Main attention KV and the indexer K cache are separate representations.

## 2. Adaptive discovery and all outcomes

Complete compact recall covered 154 records, not 154 distinct mechanisms. Bounded report search additionally checked related sharing, cache precision and indexer work. The full direct-paged prior dossier is retained.

1. OpenAlex query `exact sparse attention computation reuse inference`, August 1 through October 22, 2026: 12 hits. Metadata screens retained every hit. Approximate diffusion reuse, new memory hardware and previously investigated methods did not justify another fulltext fetch.
2. Host-authored expansion selected the recent proposal/refinement lead. ArXiv query `ti:"Prism Attention"` in the same date window returned one identity already in the OpenAlex results. **Two online paper queries, 13 hit rows, 12 distinct explicit paper identities, one fulltext read.** No failed provider search or hidden query relaxation occurred.
3. `Prism Attention: Proposal-Refined Index Sharing Mechanism for Efficient LLMs Inference`, arXiv **2610.22985v1**, October 16, 2026, was read at method §§4.1–4.2, setup §5.1, relevant ablations and conclusion. The versioned fulltext and exact source revision are retained. No author implementation was identified; dependency links are not an implementation claim.
4. Read-only local PR search found vLLM62011 and SGLang38944. Both bodies were imported into the isolated state, then inspected through `pr-search`. The exact vLLM head, full diff response and six selected files were fetched. SGLang was body-only corroboration of the existing candidate-consuming mechanism, not a code port.

| Intervention screen | Outcome | Reason / retained component |
|---|---|---|
| Prism expanded proposal pool plus per-layer refinement | Already present in the target mechanism family | Target producer20 publishes candidate blocks; index-source consumers24/28/32/36 refine within them. Paper token pools are not identical to target block pools. |
| Prism INT2 proposal construction and GQA head maximum | Reject direct exact-output transfer as scoped | Asymmetric INT2 is approximate; GQA maximum is not the trained indexer's weighted ReLU head sum. Offline layer assignment also changes the target selection schedule. No blanket rejection of approximate research or frozen-weight calibration. |
| PR62011 FP8 sparse-MQA host adapter | Retain conditional adapter refinement | Concrete absent wrapper support over existing native FP8 capability; preserve cache format, score policy and manual opt-in. |
| PR62011 automatic enablement policy | Exclude from initial arm | Separate policy change; eligibility, short-context regressions and actual exposure must be established before changing defaults. |

`paper-dispositions.json` retains the other 11 paper screens at their actual metadata-only read depth. DoSA, RouteRelay and cross-query reuse are prior work, not new yield. The paper's Qwen3/H800 headline versus dense attention does not estimate improvement over native CSA2.

## 3. Exact target gap and first consumer

The source chain is visible in retained `target/` and `dependency/` copies:

- `vllm/v1/attention/backends/mla/indexer.py:55–62`: `auto` resolves FP8; MXFP4 is opt-in. The round114 68-byte indexer scenario must not be treated as the default. No launch evidence establishes which format is active.
- `vllm/config/attention.py`: `indexer_sparse_logits=False` by default. When enabled, `attention.py:1417–1461` chooses sparse scoring only for candidate-consuming indexers. Producer/pre-candidate indexers stay dense.
- Two current guards require MXFP4: the model constructor and sparse metadata builder. The current sparse wrapper unpacks `q_quant` as an FP4 tuple, views Q/K as `int8`, and hardcodes FP4 gather/cache layout. Removing the guards alone is insufficient.
- The current writer, `indexer_k_store.py:248–267`, already stores FP8 payload plus packed UE8M0 scales when `MX_SCALE` is true. The wrapper sets that branch from `mqa_logits_use_mx_scales()`, which selects SM100. The nearby generic float32-scale comment does not describe this branch.
- `deep_gemm.py:597–635` already provides unit packed Q scales and casts weights to BF16 for SM100 dense logits. FP8 Q's positive per-head scale has been folded into its weights. Retaining this helper preserves the existing ABI convention; it is not a new arithmetic shortcut.
- a7a `sm100_sparse_mqa_logits.hpp` accepts `Float8_e4m3fn`, uses FP8-specific TMA/swizzle/storage shapes and instantiates the corresponding sparse kernels. Sparse capability is already in the dependency; the missing piece is the c455 FP8 host path.
- The donor keeps FP8 Q typed as FP8, calls the existing Q-scale/weight helper, passes the real cache format to `kv_cache_as_quant_view`, and sizes the prefill gather workspace for that format. It retains FP32 producer weights until the existing helper casts them; the FP4 arm can still write BF16 weights directly.

The first useful consumer is the native sparse MQA scorer, followed by DeepSelect and physical index remapping. This is a **consumer-only candidate scoring change**: no new candidate selection, no producer removal, no sparse attention output memoization, no weight updates, no model replacement. M03 (`hypothesis:78e5ab2fbe61364536be6b0a2646f7b55cbaad49f2ec1bebeaca81b3519e02cf`) already covers an all-blocks-fit producer-ranking bypass; that is a separate prior and is not proposed again here.

The source config gives 32 indexer heads, dimension128, top512, candidate2048 blocks of8. Indexer owners are2/8/14/20/24/28/32/36, with candidate source20. Main-cache source sharing and per-layer attention consumers must not be counted as repeated indexer executions. The four later index sources are potential consumers, not four measured exposed costs per request.

## 4. What the CPU/source evidence establishes

`host_abi_probe.py` extracts the actual `SparseMQAIndexer.forward` function from each pinned Python file and runs its control flow against metadata-only stand-ins. It imports no torch, vLLM or native code and performs no tensor arithmetic.

Three cases passed:

1. Deliberately bypassing current constructor guards and passing a three-row FP8 tensor stand-in fails at tuple unpacking, before any scorer call. This is a falsifier of a guard-only patch, not a reported bug in the correctly guarded current runtime.
2. The donor FP8 path invokes the Q-scale/weight helper and passes FP8 Q, packed-scale metadata and FP8 cache interpretation to the decode-call stub.
3. The donor FP4 control retains its int8 packed-FP4 tag and FP4 cache interpretation without the FP8 helper.

The helper and kernel are stubs. Prefill, profiling reservation, AV metadata construction, zero rows, native quantization, capture, output values, timing and device correctness are **not tested** by this probe. Source inspection separately covers the prefill format change. No additional arithmetic sweep would close the native implementation gates.

Donor tests have CUDA/eager, prefill/decode, FP8/FP4 and page-padding cases, plus a numerical tolerance check against a torch reference. They were read, not executed here. Their `_assert_same_selection` compares the multiset of selected logit values and permits different token indices at equal scores. Equal-score ties can select different KV positions and change attention outputs. Therefore these tests and the donor's task score do **not** certify exact target token equality. Native comparison must address score values, token identities/tie contracts, invalid lanes, padding and downstream outputs.

## 5. Minimal adaptation and adjudication

The initial implementation design should transplant only the FP8 argument/cache/workspace adaptations and guard changes, with the original manual flag and original default preserved. Keep existing FP4 behavior as a regression control. No implementation patch was made.

Eligibility gates include SM100, installed compatible DeepGEMM and DeepSelect, correct varlen decode metadata, supported top-k backend, no DCP/PCP, valid page/block alignment and matching candidate-buffer ownership. Planned TP1/DP4/EP4 does not itself attest these. Captured padded rows, native DSpark query counts, adaptive compaction, replay, sequence starts/ends and request-local compressed coordinates must remain correct. Existing unit-scale buffer growth preserves older graph allocations; the port must still reserve/warm required sizes before capture and verify buffer lifetimes.

Future paired arms, only if separately authorized:

- **A:** current FP8 indexer with dense scoring then the same candidate mask and target-compatible top-k behavior.
- **B:** same FP8 cache, candidate pools, parameters, weights and workload, manual sparse scoring through the narrow adapter.
- **Control:** original FP4 sparse path only where already configured; it is not the same-quality substitute for A/B.

First inspect effective format/flag/backend and actual eligible compressed-domain counts from compatible artifacts, with the workload threshold in §6 as the first ROI falsifier. Then native differential tests need compare candidate scores, selected identities and per-request target outputs across short/long contexts, empty/padded rows, replay, AV and capture. A tie difference is an unresolved correctness issue, not automatically harmless. Do not silently waive the frozen target contract. If maintaining identical selection requires an adapter/fallback, its cost belongs in B.

Use the existing Mooncake and agent-p75 workloads for serving ITL, tail latency, TTFT and goodput. They cover useful load/context variation but do not establish component activation or exact equality by themselves. A narrowly added diagnostic is justified only to record consumer path hits, compressed visible length, candidate-covered length, builder/scorer/top-k time and capture/replay behavior. It is not a replacement benchmark or new quality workload.

**Null/falsification:** inactive/ineligible FP8 route; insufficient candidate pruning; inconsistent scores/indices/output; sparse metadata, packing or top-k costs erase savings; memory or stability regression. If all candidates cover the visible context, score-work removal may be absent. Shorter contexts can therefore favor A. Measured serving benefit must exceed added work under matched correctness and existing SLA constraints; no promotion from node count or operation count alone.

## 6. ROI and exposure limits

There is no defensible target latency or percentage estimate. Candidate capacity is at most 16384 compressed positions, not a universal actual size and not raw prompt length. Consumer layers24/28/32/36 use compression ratio1. At finite valid scores, if all valid blocks fit the2048-block budget, selecting candidates excludes no live logical positions. `candidate_blocks.py:157–225` bounds DeepSelect by valid blocks and pads the fallback; `sparse_mqa_logits.py:85–134` sorts/filters candidates, repeats padding and supplies the valid sparse-column `end`. Invalid/all-negative-infinity edge cases still require the exact original masking contract.

The agent-p75 planned8192-input/1024-output shape stays around9216 positions, below this capacity. Thus its normal length range does not support the claimed **logical context-pruning** mechanism. This does not prove equal physical work: dense logits may be max-model-length-wide under graphs, and metadata, padding stores, masking, top-k and native kernel tactics differ. Such an implementation benefit would need its own measured explanation, not be credited to removing16384−512 scores;512 is the final selected attention support, not the candidate-scored domain.

`workload_gate.py` rechecked the three already-retained Mooncake requested-length files against their prior SHA256 values. It retains only the relevant length pairs for reproducibility:

| Saved workload | Requests | Requested input >16384 | Input + requested output >16384 |
|---|---:|---:|---:|
| median | 4004 |417 (10.41%)|439|
| burst |4220|437 (10.36%)|448|
| cache-heavy |4053|364 (8.98%)|380|

These are metadata counts, not actual executed queries, pruning frequency, completed outputs or time-weighted exposure. Longer requests may dominate or may not; prefix caching, replay, padding, server limits and scheduling are not inferred from the table. It establishes some standard-workload opportunity to inspect without inventing a new long-context benchmark, while most requested inputs lie below the pruning threshold. Source20 consumers may score fewer positions on eligible long contexts only if the FP8 sparse route is active and candidate exclusion occurs. Prefill may already be shortened by bounded replay; no full-prompt saving is assumed. Native schedule reuse also prevents multiplying metadata overhead by every consumer.

PR62011's unsuffixed Flash TP4/4-B300 results and Prism's Qwen/H800 results are donor evidence, not measurements of this TP1/DP4/EP4 target. Logical score-work removal does not directly measure HBM traffic or critical-path latency. The strongest cheap remaining discriminator is effective FP8 route and compressed-domain exposure; if unavailable, retain the conditional design without inventing a bottleneck.

## 7. Tool usefulness and failures

The OpenAlex query found a recent fulltext not previously retained; the exact-title arXiv follow-up resolved its version. Fulltext reading closed the broad proposal/refinement novelty claim. PR search then found a concrete missing ABI rather than a generic paper transplant. Selected-file retrieval exposed both the useful adapter and the auto-enable policy that should be separated.

All failed/partial actions are retained:

- Initial direct lookups for old PR62463/62000 were absent from this corpus; this does not establish upstream absence.
- The first isolated PR search occurred before the selected PR imports and returned no hits. The corrected post-import replay is retained separately.
- A replay used unsupported `--query` syntax, failed argument parsing, then succeeded with the documented positional query. This was operator error, not a provider failure.
- An overly broad local `rg` glob admitted large `.jsonl` workload bodies and produced truncated output plus a nonexistent-directory error. No conclusion relies on that output; subsequent discovery used filename-only listing and bounded metadata files. This is a search-scope mistake, not evidence of new corpus coverage.
- The six-file investigate request omitted the documented `--deep-count 0` for code-only use. It therefore also auto-selected two PR records and a SPADE metadata record. All six intended pinned files were fetched within the six-miss budget; extra hydration/fulltext attempts were budget-exhausted, and SPADE was not read in full. Preserve this receipt rather than refetching to make it look clean. The narrow recommendation is to use the existing code-only recipe (`--deep-count 0 --max-repositories 0` with explicit code files); no new tool change is warranted by this misuse.

`history.json` retains normalized redacted commands, while `tool-use.json` distinguishes online queries, selected reads, local replay and source/CPU diagnostics. Source export was explicitly committed and reopened read-only, with every claim quote checked against its immutable revision. No canonical mutation, snapshot/S3 publication, GPU run or performance win is claimed.

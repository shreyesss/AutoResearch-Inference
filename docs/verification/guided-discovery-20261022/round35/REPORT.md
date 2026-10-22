# Round 35 — bounded S3 inventory for PJ01 exposure

## Result

**No exact Flash-1017/c455786 projection exposure or selected linear-backend record was recovered in this pass. PJ01 remains deferred.** This is a bounded inventory result, not a claim that no such artifact exists anywhere.

The useful distinction is between the published research database and independently produced benchmark artifacts. The remote research HEAD and its complete manifest match the local published snapshot byte-for-byte. They do not add unseen runtime evidence. The external benchmark bucket contains real runs and compiler/autotune caches, but the inspected records either describe older campaigns, lack exact runtime binding, or identify an NVFP4 tokenizer outside the required model revision. Compiler-cache presence alone does not identify the actual selected linear class or its exposed duration.

## Identity required

Target model: `deepseek-ai/DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`.

Source: vLLM `c4557869393db4d75c483d92edd02a5125500883`. Planned deployment is eight B200 GPUs in two TP1/DP4/EP4 groups; no runtime attestation was obtained here.

PJ01 needs a baseline-linked record of actual selected linear backend, processed weight/scale shapes and strides, the three **context** projections distinguished from query work, current rows and FULL/eager partition, per-rank critical-path timings, and committed progress under the same workload. None of those required runtime fields was recovered with the exact binding.

## What was inspected

Configuration was read before cloud access: approved private research bucket/namespace and `sofia-ssm` credential profile; existing benchmark findings point to `b200-bench-results`. Credentials were obtained by the existing local credential helper without printing or copying them. No bucket discovery, STS request, node SSH, runtime command, GPU query or remote write was performed.

| Store / scope | Observed result | Decision |
|---|---|---|
| `autoresearch-641134885443-us-east-1/autoresearch/research/HEAD` and referenced manifest | HEAD `743ef260ed43b945f9b0680d6e36dbd09f41cdbc2f3634910c78c5088d9f2628`; downloaded 590,944-byte manifest hashes to that ID, contains 1,512 files, and is identical to local manifest | Existing published research state. No corpus chunks or traces downloaded. Experiment namespaces and historical versions were not traversed. |
| `b200-bench-results/results/b200/vllm/` | Complete recursive page: 106 objects, October 10 campaign paths, October 11 modification timestamps | Older campaign branch; no run payloads or traces fetched. |
| `deepseek-v4.1-flash/_shared/` | Complete recursive page: 848 objects; includes FlashInfer 0.7.0.post1 `100a` autotune JSON and DeepGEMM metadata, including October 20 `sm90` cache entries | Keys/sizes only. No evidence binding these caches to the target checkpoint/image or distinguishing context projections. Cache bodies were not fetched. |
| First non-shared DeepSeek page | 1,000 objects, all under `i-01040ad89b81a570e`; October 10–12 campaign names; page truncated | Partial older index. Did not continue or fetch old traces. |
| `deepseek-v4.1-flash/i-041ecef219910b16f/` | Complete 263-object page, October 18 campaign; fetched one 2,829-byte Mooncake-median manifest | It identifies model alias `deepseek-v4.1-flash-nvfp4` and NVIDIA NVFP4 tokenizer revision `c48dca0146b56d64c8116dbb6fcace8b7cc835f8`, not required Flash-1017. Loaded-model equivalence is not established. |
| `deepseek-v4.1-flash/i-097469ebb78e9333e/` | One delimiter page plus first recursive page: 1,000 objects, October 14–15 receipt/repository/campaign entries; recursive page truncated | Partial older index. Large reports/telemetry/request traces were not fetched. |

The fetched external manifest's `git_revision=2e6fa287d90adf7318ad314de27aa2f595aac821` and `git_dirty=true` concern the benchmark harness. **They are not proof of the vLLM serving commit.** Its environment object is empty. It does not supply processed projection tensors, selected backend, component timing, or per-round committed progress. The tokenizer mismatch prevents treating it as an exact-target evidence record; it does not by itself prove every aspect of what the server loaded.

LastModified values are object-upload metadata, not guaranteed run times. Campaign dates and manifest creation time supply separate context; dates alone never substitute for source/checkpoint matching.

## Target-instance follow-up

The user previously identified `i-060afaf8202cf0734` (`bitlane-b1`) as the B200 source VM. The untruncated DeepSeek root index enumerates six EC2 instance prefixes and one `jl-vm` prefix; none matches that instance. No explicit occurrence of that ID appears in any downloaded index or object. Therefore the separately authorized targeted extension was **not used**: zero additional LISTs or GETs. The data could have been stored under another key or another approved store; this check cannot exclude that.

Three other EC2 prefixes and `jl-vm-541077` were only enumerated, not inspected. `results/preflight` and `results/server-logs` were not traversed. The two truncated pages were not completed. The request ceiling was reached, so no broadening was attempted.

## Request budget, byte accounting and logging limitation

- **10 LIST SDK calls**, **2 HEAD SDK calls**, **3 GET SDK calls**; all completed successfully. LIST limit 10; GET limit 20. No pagination or retry was intentionally launched beyond those calls.
- 3,217 unique object keys listed across returned pages. This is not the bucket's total object count.
- GET payloads: **593,838 bytes** total. LIST/HEAD response bodies: **1,349,217 bytes**. Total observed response bodies: **1,943,055 bytes**, excluding HTTP headers/TLS. No object above 1 MiB was fetched; no large trace was downloaded.
- Fourteen operation events retain observed one-attempt transport counters. The final GET's event was overwritten when a still-running LIST wrote the shared log last. Its exact executed command, successful tool output and payload file survive. That event was reconstructed with exact payload length/hash; timestamps and transport-attempt count remain explicitly unknown. Thus the exact logical SDK count is known, but the exact total number of HTTP attempts is **not** claimed. Minimum is 15. See `LOGGING_CORRECTION.md`.
- The local inventory script now uses a file lock to serialize request logging. No request was rerun to conceal or repair the missing timing counter.

## Consequence for investigation

There is still no defensible exposed-time ceiling for PJ01. The 71.43% reduction in nominal projection-output MACs cannot become an ITL forecast from these artifacts. Do not use an unrelated autotune cache or older aggregate throughput point as a substitute.

Reopen retrieval on an exact artifact key, run manifest or provenance index identifying the Flash-1017/c455786 campaign. A loader log may first settle actual backend/layout cheaply; only a matched context-operation trace plus committed progress can estimate the optimistic round-amortized headroom. This pass adds no hypothesis, acceptance, GPU test or service claim.

## Reproducibility

`requests.json` records every logical operation and measured response bytes, including the explicit reconstructed event. Numbered list/head/object files retain actual responses. `inventory-summary.json` contains machine-readable field gaps and scope. `target-instance-followup.json` retains the exact-ID check. `local-inputs.json` pins the safe configuration/reference files consulted; no credential files are copied or hashed. `manifest.json` pins this frozen inventory.

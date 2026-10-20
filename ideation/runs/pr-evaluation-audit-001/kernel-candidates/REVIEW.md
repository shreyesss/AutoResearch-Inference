# B200 kernel and dependency candidate audit

## Scope and evidence

Reviewed supplied CSV classifications and detailed Markdown, 28 stored vLLM full bodies and 17 current upstream PR objects using the existing cached GitHub client. Primary snapshots are `local-records.json` and `upstream-records.json`; exact PR-head SHAs are retained. This is one specialist subset of the full5532-item audit. No GPU work, cherry-picks, new evaluation harness or memory plans were executed.

The supplied research assumes a B300 block and v0.32.0. Our target is eight B200 SM100 GPUs. Snapshot image config pins ac9126e58aa7..., not an assumed release. All inclusion decisions remain pending exact image/source/dependency audit. A merged PR is not necessarily present; an open PR is not automatically novel or applicable.

## Ranked candidates and prerequisites

Rank is engineering triage priority, not predicted speedup. Correctness gates must precede performance comparisons; startup work is not steady-state throughput work.

|Rank|Item|Class / action|Mechanism and eligibility|
|---|---|---|---|
|1|[vllm-project/vllm#61039](https://github.com/vllm-project/vllm/pull/61039)|performance: shortlist|Stop scoring static max_model_len blocks beyond each row context; DeepSelect row ends plus BF16 logits. Exact sparse indexer/candidate consumer present; DeepSelect supported; DCPoff forBF16 leg. #61149 changes logits API, so rebase rather than paste old wrapper. Separate length-awareness from BF16 ablation.|
|2|[vllm-project/vllm#60468](https://github.com/vllm-project/vllm/pull/60468)|startup: shortlist|Warm MegaMoE, MegaGate and staging specializations before readiness. Actual deep_gemm_mega_moe backend and unrepresented shapes; persist DG_JIT_CACHE_DIR; no steady-state speedup claim.|
|3|[deepseek-ai/DeepGEMM#478](https://github.com/deepseek-ai/DeepGEMM/pull/478)|correctness_gate: inspect_before_perf|Replace reusedgridid splitbarrier tags with perexecutionepoch for mega_mhc. Exact installed JITheaders and mega_mhc captured path; B200repro exists. Vendorpatchonlyifabsent; preservedependencyversion.|
|4|[deepseek-ai/DeepGEMM#451](https://github.com/deepseek-ai/DeepGEMM/pull/451)|correctness_gate: inspect_before_perf|Reset stale MegaMoE peerreadiness before existing pullbarrier. DeepGEMMFP8xFP4/BF16MegaMoE graphs; exactpin audit. vLLM60936 is NOTthispinupdate.|
|5|[vllm-project/vllm#60613](https://github.com/vllm-project/vllm/pull/60613)|correctness_gate: inspect_before_perf|Initializecallerprovided sparseindexworkspace tail to-1 before MegaAttn prefill. DeepSeekV4.1 MegaAttn exactcopiedcombinefunction, includingfreshshortrows andboundedreplaystart; provefixabsent.|
|6|[vllm-project/vllm#57977](https://github.com/vllm-project/vllm/pull/57977)|performance: shortlist_conditional|PreserveMXFP8 activation/scales between mHC,projection andMoE toremove dequant/requantlaunches. Sourcevalidated4B200TP4+SP; desiredTP1DEP differs and may exposeadditionalleg. Consumerlayout andpostloadkernelmustmatch; includeJIT warmup.|
|7|[vllm-project/vllm#60802](https://github.com/vllm-project/vllm/pull/60802)|performance: shortlist_conditional|PreferDeepSelect foreligiblelargeverificationrows instead ofpersistentTopK. Checkcurrentauto mayalreadydeep_select; sourceperformance GLMnotDeepSeek; bootvariance12-25% underminessmalleffects.|
|8|[deepseek-ai/FlashMLA#227](https://github.com/deepseek-ai/FlashMLA/pull/227)|performance: shortlist_conditional|B200148SMH64QNormoff fusedattention:KVprefetch/conversion overlap,TMEMrelease,maskload,pipelinechanges. ExactH64D512TopK640; prefillBF16eligible; reporteddecode allFP8KV, notmixedFP4. Rebaseagainst#229interleavedlayout/vendorpin.|
|9|[vllm-project/vllm#62359](https://github.com/vllm-project/vllm/pull/62359)|performance: shortlist_conditional|HostNUMAcuMem2Mpage sharedEngram backing toreduceGPUtranslationcost vsregistered64Kmapping. Actualdp_shared_memory and hosttables; probeFABRIChandleexportonB200x86. Fallback/noengagementisnooptimization. NUMAbind samearms.|
|10|[vllm-project/vllm#59849](https://github.com/vllm-project/vllm/pull/59849)|performance: shortlist_conditional|Exactsize registeredhostEngramstorage avoids pinnedpoweroftworounding; possiblelookupbenefit. Differentpath fromsharedcuMem; GB10onlysource, B200PCIe/NUMAtransferunknown; validateactualallocatorandfallback.|
|11|[vllm-project/vllm#60938](https://github.com/vllm-project/vllm/pull/60938)|research_prototype: prototype_after_simple_wins|FuseEngramgate/residual withfollowingdelayedmHCcollapse+RMSNorm toavoidrepeatreads. TP1,noSP,noactiveoverlapstream alignsDEP candidate; GPUcorrectness/perfpending; keepflagoffuntilexactupstreamtests pass.|
|12|[vllm-project/vllm#61971](https://github.com/vllm-project/vllm/pull/61971)|performance: low_cost_low_expected_value|Shareint32RoPEpositions withinfullgraphcontext instead40casts. MegaAttnFULLgraphs, exactsameinputtensorcontext; source0.39%targetGPU notserving.|
|13|[vllm-project/vllm#57843](https://github.com/vllm-project/vllm/pull/57843)|startup: bundle_after_inclusion_check|WarmmHCprojection specializations missingfromgenericwarmup. ActualDeepGEMM mHCprojection andnewshapeJITlogs; compareto60468coverage; avoiddoublewarmup.|
|14|[vllm-project/vllm#58559](https://github.com/vllm-project/vllm/pull/58559)|startup: bundle_after_inclusion_check|Warm sparseTopK/DSparkinputprep Tritonspecializations missedbycapture. Exactcalledkernels andnoexistingcoverage; sourceDSparkrelevantbutDFlashsubpaths notautomaticmatch.|
|15|[vllm-project/vllm#62011](https://github.com/vllm-project/vllm/pull/62011)|quality_performance_tradeoff: alternative_precision_lane|Enable sparseMQAlogits withFP8indexer insteadrequiringMXFP4. Requires61149packedUE8M0layout; changesprecision/cachecapacityvsMXFP4 baseline. Treatownqualitylane notfreewin.|
|16|[flashinfer-ai/flashinfer#5523](https://github.com/flashinfer-ai/flashinfer/pull/5523)|research_integration: prototype_after_route_audit|AlternativegeneratedSM100a148SM routes forMQA,mHC,MegaGate,MoE,includingH5120FP4. Experimental APIsnotautomaticallyusedbyvLLM; exactroute/shape/ABI/EPcollectiveadmission needed. Startoneoperator withfallback;notreplaceentirestack.|
|17|[deepseek-ai/DeepGEMM#394](https://github.com/deepseek-ai/DeepGEMM/pull/394)|research_integration: defer_shape_port|CTApairedweight/scalepackets optionalmodel-loadtransform; smalltokenlegalsocombineswarpgroup+evictionchanges. MeasuredH7168I3072 no sharedexperts, unlikeFlashH5120I2304+shared; validatepacketshape+repackingmemory. Needseparateablations.|
|18|[deepseek-ai/DeepGEMM#404](https://github.com/deepseek-ai/DeepGEMM/pull/404)|research_integration: defer_until_engagement|EVICT_FIRST routedweightTMAhint for<=512tokens toreducecachepollution. MeasuredV4FlashH4096notV4.1H5120; inspectgeneratedSASS/engagement notassumeflagworks; verify withrealrouting.|
|19|[deepseek-ai/DeepGEMM#436](https://github.com/deepseek-ai/DeepGEMM/pull/436)|version_conditional: defer_api_preflight|PlaceMXlogitscleanupafterCTAcompute; compilerplacement mayreducewaiting. Oldclean_logits API removedby61149DeepGEMM6ce1; likelynoapplicablecall onnewpin. Requireexactoldpathandclean_logits=True; otherwiseexclude.|
|20|[vllm-project/vllm#61371](https://github.com/vllm-project/vllm/pull/61371)|dependency_tradeoff: audit_not_blind_upgrade|FlashMLA229vendorupgrade changesKVrecordinterleaving andblockpacking. Treatpairedwriter/reader/layoutasatomicdependency; measured9.5%KVtokencapacityloss withMegaAttn;61149alignmentdependency.|
|21|[vllm-project/vllm#61149](https://github.com/vllm-project/vllm/pull/61149)|dependency: audit_dependency|DeepGEMM2.8.1pin/MQAAPIandpackedMXFP8FP8cache adaptation. Requiredfor62011/61371; removedclean_logits/logits_dtype changes61039/436port; checkinstalledactualpin.|
|22|[deepseek-ai/DeepGEMM#471](https://github.com/deepseek-ai/DeepGEMM/pull/471)|dependency: watch_dependency|2.8.2fusedFP8cast/clamp/epilogueandpagedstride support. BreakingFP8Quantizationclassrename; noautoclaimsbaselineimprovement. IncludeonlyifselectedcandidateusesnewAPI.|
|23|[vllm-project/recipes#1002](https://github.com/vllm-project/recipes/pull/1002)|configuration: existing_comparator|B200TP2withhostEngram enablinglowerGPUreplicacount. RecipehasactualB200source; baselinealreadyhostoffload sooffloadaloneisnotnew. Compare4xTP2vs2xDEP4ona8GPUbudget onlyifnotalreadytested.|
|24|[SemiAnalysisAI/InferenceX#3095](https://github.com/SemiAnalysisAI/InferenceX/pull/3095)|configuration: diagnostic_not_direct_patch|Minimumgraphcapture64 curesB300lowconcurrencyc1tailunderrecipe. Currentprofilecap512alreadyexceeds64; inspectactualcapturelistandDSparksequencecoverage. R7bseq128*kplus1=768 cap512issueisothercoverageproblem.|
|25|[vllm-project/vllm#62467](https://github.com/vllm-project/vllm/pull/62467)|conditional_correctness: deprioritize_default_path|Boundscheck histogram_topk float4tail when -infthreshold andlengthnotmultiple4. PRsaysnoshippeddefaultmodelreachesbug. V4.1candidate2048*8covers<=8192; inspectpersistentbackend/adversarialchangedcandidateconfig beforepromote.|
|26|[vllm-project/vllm#62269](https://github.com/vllm-project/vllm/pull/62269)|conditional_correctness: conditional_dependency|KeepEngramalltoallreceivebufferinsameallocatoras send. Onlycumemallocator+hostDPshard path; currentflagsdonotestablishenablecumem. RequiredifnewEngramexperimentenablesit, notunconditionalperf.|

## Corrections to the supplied broad recommendations

- **62467 is conditional hardening**, not an established shipped DeepSeek corruption route. Current PR explicitly states default/near-default model configurations cannot reach the bad masked short-row case. Keep its upstream regression, inspect reachability before prioritizing it over60613 or graph epochs.
- **DeepGEMM478 has direct B200 validation** of stale mega_mhc graph barriers;451 is the separate MoE readiness issue. vLLM60936 is prefill index-combination optimization, not a pin update for451.
- **58818 is excluded for current SM100 MegaAttention**: the source explicitly says it does not use those planner holders.
- **FlashMLA227 becomes more interesting on B200 than on the source B300 block**, but only the148SM H64 QNorm-off specialization; reported decode usesallFP8KV, while mixedFP4fallsback. Rebase around229 layout changes first.
- **DeepGEMM381 is not a Flash model optimization despite B200 in the title**: explicit hidden7168/top8/256expert gate differs from Flash.
- **61371 is not a free library upgrade**: its own measurements show9.5%lessMegaAttnKVcapacity, or24.6%withoutpairedalignmentrelaxation. Treatlayoutreaders/writers and61149 asonecompatiblechange.
- **436 is stale-API conditional**: clean_logits changed/removedby61149; a2x isolatedoldAPI result isirrelevantifthatpathisgone.
- **62359 is a prefill candidate, not a decode claim**; source reportszero decode gain and usesGB200host-memorycapabilities. B200FABRIC/NUMAeligibilitymustbemeasured.

## Reuse existing evaluation machinery

Use `testing/b200/vllm/run.sh`, existing native concurrency sweeps, text-grid/document/ragged/cache workloads and production-Mooncake median/burst/cache-heavy replay. Preserve exact workload, checkpoint, precision, DSpark real acceptance, cache preparation, image, routing and eight-GPU cost denominator. Compare R7b twoDEP4 at256/384/512 and R10DEP8 at1024 within comparableworkloads; lowloadcontrols forhostboundchanges. Main evaluation audit supplies exactcommands.

Primary objective: strictSLOgoodput/capacity and cost per successfulSLOrequest; custom campaign goodput separately. Fixed1x replay chiefly tests tails ifallrequests alreadyserved. For capacity useexisting rate sweeps; neverprojectkernelgeomean ontoservingthroughput. Profile only toverifytheactualchangedpath; existing kernel_summary/nsys/ncu wrappers suffice. Coldstart tests reuseexistingrunner+JITlogs, reportingreadinesscost separately. No newautoresearchharness isneeded.

Detailedper-candidateevaluationfit, dependencies, actualsources andexactquotes are in `candidates.json`. Numericvendorresults are authorreports; nonewasreproducedhere.

## Exclusions / lower-priority holds

- deepseek-ai/DeepGEMM#381: Explicitgate hidden7168,intermediate2048,256experts,top8,EP8 andnarrow128TPE; FlashV4.1H5120I2304top6failsgate. B200 in title doesnotmakeitapplicable.
- deepseek-ai/DeepGEMM#386: VendorbenchmarkDeepSeekV4Proonly; broadtiling/UE8M0/directcombine proposal insufficientFlashshapeevidence; below394/404forboundedport.
- deepseek-ai/FlashMLA#196: Onlygeneric sparse_fwd withouttopk_length; currentMegaAttn supplieslengths/differentfusedpath. No work savedwherelengthalreadyprovided.
- deepseek-ai/FlashMLA#187: SparseprefillHCA oddtailoptimization thinoneparagraphbody; unverifiedspecificMegaAttncallsite;lowerprioritythan227.
- vllm-project/vllm#58818: Fullbody explicitlySM100MegaAttentiondoesnotuseplanholders;H20plannerwinirrelevantcurrentpath.
- flashinfer-ai/flashinfer#6059: V3.2FP8cacheABI132bytesandH64denseSM100noadmittedroutes; pagedSM100batch<=16admission only. NotdropinV4.1MXFP4indexer.
- SemiAnalysisAI/InferenceX#3181: ClosedunmergedB300EngramHBMexperiment withnoresults. CurrentB200hostoffloadintentional; GPUmemorytradeoffneedsseparatelane.
- vllm-project/vllm#61868: LargeGB300TP4specializeddecode; desiredTP1DEPnotmatching. CouldreconsiderforTP4comparatoronly.
- vllm-project/vllm#62091: GPUresidentEngrampeerHBM path; currentcpu_offloadtrue bypassesit.
- vllm-project/vllm#61530: RequiresMXFP4packedEngramcheckpoint; currentrevisionFP8Engram assumedfromsourceandmustconfirm; notparameteronlyoptimization.
- vllm-project/vllm#57575: GenericFlashMLAsparseprefill bufferreservation, sourceGLMvalidation; confirmMegaAttnnotusingit. Do notpromoteonlyforMLAtitle.
- vllm-project/vllm#60936: Realprefillindexcombinecandidate butfullmodel+0.60%ishistoricalunpairedvs2.3%CV; lowerthanothercandidates. Correctness60613 prerequisite; notDeepGEMM451integration.

## Additional current-path dependency checks

- **59327** sorts host Engram lookups and runs large lookups inline. Audit its presence before testing host backing or NUMA changes; source thresholds came from GB200.
- **59923** is a particularly relevant TP1 DP optimization: packed FP8 rows, one batched prefill exchange and small-batch peer exchange. It requires DP-sharded rather than DP-shared tables. Therefore its path and62359 shared-table backing are not simply additive. Verify resolved `dp_shared_memory`, not just `cpu_offload`.
- **59922** adds producer-assisted BF16 top512 with verification lengths1–6. It has real B200 kernel tests, but a reported short-context n6 case is slower than the existing default. Keep it as a conditional alternative with shape-level negative controls, not a global replacement.

Final specialist output: **29 candidate/dependency records and15 explicit exclusions or holds**. The full source snapshots and classifications cover all inspected records.

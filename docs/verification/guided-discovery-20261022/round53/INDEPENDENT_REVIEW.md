# Independent round53 review — rollback premise and actual V2 path

## Verdict

Agree with the source screen: no new formal intervention or performance qualification. Separating SubTernary's persistent execution resources and validity-pointer idea from its ternary kernels is useful. Its CPU baseline's allocation/copy/context-switch cost does not establish that pinned V4.1 performs a full-history KV copy after rejection. The source evidence contradicts that direct-transfer premise; it does not prove zero rollback overhead or universal O(1) state maintenance.

## Actual caller correction and additional source closure

The author's `gpu_model_runner.py` example is the older runner. It is valid as a generic pinned implementation example, but must not be presented alone as proof of the V2 DSpark path. I inspected the actual V2 `gpu/model_runner.py:postprocess_sampled` call to `input_batch.post_update` and its `_post_update_kernel`.

That kernel updates accepted output IDs/counts and computes `computed_delta = query_len - num_rejected`, then adjusts the computed-token counter. It has no historical-KV tensor argument. Its work includes accepted-token writes and optional penalty-bin updates; those are real operations, not a measured free rollback. They are different from copying every old KV vector.

The runner subsequently calls `model_state.postprocess_state`, so stopping at `post_update` would leave an unresolved hook. Native NVIDIA V4.1's model hook selects `DeepseekV41ModelState`, which inherits `DefaultModelState`, which inherits `ModelState`. Neither of the first two overrides `postprocess_state`; the interface implementation returns None. This closes that specific V2 post-sampling hook in the inspected source. It is not a complete proof of CED/SWA/Engram cache semantics across the whole model, a live runtime attestation, or a reason to remove other state updates.

The retained scheduler branch guards stale/preempted outputs and subtracts rejected counts. The lookahead/freeing path uses processed-token bounds to avoid freeing state still in flight or needed after rollback. The block pool supplies already managed logical objects and callbacks. Those operations do not by their names imply operating-system virtual-memory allocation or TLB shootdowns. Callback, prefix-cache copy-on-write, connector and allocator behavior elsewhere still require their own evidence; the narrow source screen is sufficient to reject the simplistic missing-copy premise without claiming an exhaustive no-copy theorem.

The native DSpark class calls its parallel backbone then sequential Markov sampling, with FULL graph coverage described in that class. The paper's separate CPU autoregressive drafter/thread-pool baseline is a materially different execution shape. This does not prove every vLLM execution is captured or launch overhead is negligible.

## Paper and PR interpretation

I read the selected fulltext's transactional-scratchpad section and its stated CPU comparisons. The model of accepting a prefix by advancing validity and overwriting stale speculative slots is a reusable correctness discipline. It is not an observed absence in this GPU runtime. The paper's broad comparison to PagedAttention allocation/TLB overhead is not independent evidence for this exact code; no reported milliseconds or speedup can be transferred.

A static scratchpad port also has to respect this model's compressed/sliding-window/indexer/Engram state and distributed serving, so a paper's simple causal mask is insufficient to certify that port. The author's decision to stop rather than manufacture a subtraction microtest is appropriate. No new arithmetic simulator would measure the hypothesized old-history copy.

The FI6448/6360 PR bodies are leads for separate dispatch/tuning compatibility checks. Their body-only read depth is correctly stated. Neither their hardware claims nor the36 returned local records are36 validated interventions. The alternative tuning-methodology direction can be examined separately without reopening the rejected rollback premise.

## Checks and limits

Verified all19 author-file hashes and compared its five selected source copies against the existing c455 tree. Retained eight additional exact V2/model-state source files and their corrected callgideon/vllm pinned URLs with this review; AST inspection confirms the inspected inheritance/override structure. No modules were imported from these sources, no GPU/torch/native engine ran, and no new provider query or synthetic performance test was executed.

One source lookup included a nonexistent older model-file path and reported it; the actual model hook was found under `vllm/models/deepseek_v41/nvidia`. A combined paper/source read was truncated, so the specific transactional section and relevant code ranges were subsequently read directly. No exhaustive fulltext/source-runtime claim follows.

No author packet or canonical scientific state was changed. Separate authorized source-ingestion work is not an experiment validating this mechanism.

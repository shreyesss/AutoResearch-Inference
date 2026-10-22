# CF59 additive eligibility review: prompt logprobs

The root observation is confirmed in pinned c455 source. `gpu/model_runner.py` computes sampled-row logits in `sample()` before calling its sampler; `sample_tokens()` subsequently calls both prompt-logprob methods before constructing `AsyncOutput`. Both methods receive `self.model.compute_logits` as a callback.

`sample/prompt_logprob.py:69–118` can invoke that callback on prompt slices for requested token-ID scores. `:120–173` sends prompt hidden states to the chunked helper; `:283–319` calls the same callback for each chunk. These are additional possible head GEMMs after the proposed fork. The token-ID path skips decode-only/completed-prompt requests; the ordinary path returns if no requests need prompt logprobs, or no included prompt remains. Thus mere configured logprobs is not proof of concurrent work on every decode step. Mixed prompt/decode steps remain a concrete case to gate.

For the first CF59 selective arm, require both prompt-logprob paths to be inactive for the current eligible batch, or independently establish stream-safe, nonaliased workspace and output-buffer lifetimes across those head calls and context projection. Do not silently borrow the whole donor graph manager's no-logprobs admission policy: the selective fork is a separate adapter. Preserve original AsyncOutput release and rejection-dependent context publication.

This refines the existing unresolved scratch/eligibility requirement; it does not reject CF59 or change its deferred selection, baseline, five source claims, or original card. No measured exposure, backend execution, GPU calls, service gain or new hypothesis is established. Original round59 and retention-585960/v1 manifests remain unchanged. This additive review is not included in that already frozen retention package.

Read scope: exact pinned Python caller/callback branches only. A shell glob lookup initially failed before reading files; corrected bounded rg --files resolved the actual path. No tests, queries, network calls or runtime imports were required.

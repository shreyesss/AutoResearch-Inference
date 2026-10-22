# Independent bounded check of CF59 optional prompt-logprob refinement

No blocking correction. I read the exact pinned model runner and prompt-logprob worker, plus the retained Bitlane sweep/payload builder and both standard workload YAMLs. No calls, imports of runtime/native modules, network or source changes were made.

The ordinary `sample()` branch invokes `self.model.compute_logits` before rejection sampling. Thus the selective fork must occur inside that boundary or an equivalent split; forking before `sample()` also overlaps the head and is outside the narrow arm.

After `sample()` returns, `sample_tokens()` calls both prompt-logprob worker methods with `self.model.compute_logits`, before constructing AsyncOutput. They can issue additional head GEMMs. The worker shows a sharper conditional scope:

- Standard prompt logprobs are enabled per request when `sampling_params.prompt_logprobs is not None`; no enabled requests returns immediately. Even enabled requests must include unscored prompt rows; ordinary completed-prompt decode rows return.
- Fixed-ID prompt scoring is populated only when `prompt_logprob_token_ids is not None`, returns immediately if its dictionary is empty, skips completed prompt/resumed requests, and invokes `logits_fn` inside its chunk loop.

Therefore “fork after the first head” alone does not exclude every later head call on mixed/prefill batches. An explicit no-prompt-logprob admission rule or scratch/lifetime proof is necessary for those cases. This is a possible path, not an observed race. Pure decode of completed prompts is narrower than all sample_tokens invocations.

Saved agent-p75 and Mooncake YAML request maps contain sampling/reasoning flags but no prompt-logprob fields. The retained sweep `REQUEST_KEYS` allowlist does not include prompt_logprobs or prompt_logprob_token_ids; `payload()` constructs only those whitelisted keys plus reasoning/chat-template settings. Both workload AIPerf argument lists omit such flags. The retained keyed wrapper only supplies authentication. These files support **the saved builder does not explicitly request prompt logprobs**; they do not certify an executed wire payload, every AIPerf/server default, gateway mutation, unrelated concurrent request or live invocation. Do not drop a per-batch guard based solely on these defaults.

CF59 remains the same deferred identity. No timing or service estimate changes. The original early AsyncOutput boundary still must be preserved, and callback/connector/sharding variants must be admitted explicitly rather than inheriting unrelated donor graph guards implicitly.

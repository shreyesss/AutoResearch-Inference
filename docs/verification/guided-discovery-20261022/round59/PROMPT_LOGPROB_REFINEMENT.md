# CF59 refinement: define the fork and audit optional post-sampling work

Root reread the retained exact-pin model runner after the independent review. No donor/native execution, new network call or typed status change occurred.

`sample()` computes the target LM head at line1627 in the ordinary branch, then invokes sampling/rejection. Therefore a fork after the LM head and before rejection belongs inside that method (or an equivalent split with preserved state), not merely before the entire `sample()` call. The latter would also overlap the LM head, contrary to the proposed narrow arm.

After `sample()` returns, `sample_tokens()` invokes two optional prompt-logprob workers with `self.model.compute_logits` at lines2168–2183, before creating AsyncOutput at2202. This is a source-level possible additional logits call, not proof a given request activates it. Waiting until the first LM head ends does not alone guarantee that no later GEMM overlaps the side stream.

The initial arm must explicitly exclude unsupported prompt-logprob cases, or inspect their actual activation and prove scratch ownership for the additional calls. It must also retain the original early output-copy ordering. Do not silently inherit the full donor graph manager's guards while implementing only its context fork. Conditions on optional sampling/connector/sharding paths must be explicit in the selective adapter.

The existing CF59 report already leaves external scratch ownership unresolved. This observation sharpens that gate; it neither proves a race nor rejects the candidate. Agent-p75/Mooncake request flags must be read from their frozen workload configuration before claiming the guarded arm covers them. The hypothesis remains deferred and no timing/ROI estimate changes.

Evidence is the retained exact source hash plus bounded line excerpts. An initial guessed speculator filename did not exist; bounded file discovery corrected the path. No absent-file result supported a scientific conclusion.

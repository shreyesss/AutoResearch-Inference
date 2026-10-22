# Corrected target-summary falsifier for round66

The original counterexample fixes the target distribution and varies draft probabilities while keeping the draft selected-plus-other summary unchanged. It proves that **discarding individual draft probabilities** can lose necessary residual information. It does not, by itself, prove insufficiency of the proposed target-only compression when the full cached draft distribution remains available. The original report's broad interpretation must be read with this limitation.

The appended check matches the actual proposed information loss. It fixes the entire draft distribution at `[2/5,3/10,3/10]` and `alpha=4/5`, then varies target probabilities:

| Target probabilities | Target selected / other mass | Residual mass | Positive residual token |
|---|---|---|---|
| `[2/5,1/2,1/10]` | `2/5 / 3/5` | `1/10` | 1 |
| `[2/5,1/10,1/2]` | `2/5 / 3/5` | `1/10` | 2 |
| `[2/5,9/20,3/20]` | `2/5 / 3/5` | `3/50` | 1 |

Every available compressed target summary, full draft distribution and cumulative factor is identical across cases. Yet the pinned positive-part expression yields different support and, in the third case, a different total residual mass. This establishes the target-summary insufficiency that the original varying-draft fixture did not isolate.

The factor 4/5 is mathematically admissible as a preceding sampled-token target/draft ratio `(2/5)/(1/2)`. The current selected token has equal target/draft probability 2/5. This is an illustrative legal probability construction, not an observed target trace, finite-precision native execution or proof of the complete acceptance algorithm.

Source anchor remains `rejection_sampler_utils.py:490–494`, where `p` is the cumulative factor and `m_b/m_s` are target/draft probabilities. Recovery at 871–893 also consumes individual target/draft values. The fixture executes exact `Fraction` arithmetic only.

The final scoped disposition remains: selected target logits plus one aggregate other bucket are insufficient to replace the native verifier inputs without additional per-token information or recomputation. Pruned CTC's theorem is unaffected. Richer streamed designs remain possible; no new hypothesis is created. Original frozen artifacts remain unchanged.

# Round111 additive correction — PJ01 operation scope

This correction supersedes the PJ01 operation descriptions below while preserving the original report, readback, and manifest byte for byte. It does not change the audit's null exposure bound or introduce new evidence.

## Correct operation

PJ01 removes unused **Q output columns from the context-only draft projection**. It is not a target-model projection optimization, a general deletion of query rows, or removal of the retained KV normalization/cache path. The context path still needs its KV outputs, KV normalization, and cache work.

## Corrections to frozen wording

- `REPORT.md` table: “PJ01 target projection exposure” should read “PJ01 unused Q output-column work in the context-only draft projection.”
- `REPORT.md`, Remaining evidence: “dead-row query projection/norm work” should read “the attributable cost of producing unused Q output columns in the context-only draft projection, under the actual backend, input shape, and capture conditions.” Retained KV normalization/cache work is not claimed removable.
- `readback.json`, `PJ01.reason`: “skipped projection rows” should read “unused Q output columns in the context-only draft projection.” The target-forward span is the wrong operation; the whole draft-proposal span is also too broad and historically incompatible to isolate PJ01's removable component.
- The prose describing the component as omitting target forward is not a useful PJ01 applicability discriminator. The relevant distinction is that C025 measures draft Markov sampling, whereas PJ01 concerns an earlier context-only draft projection.

## Unchanged decision

The historical component sampler timing and padded native whole-proposal timing do not provide an attributable current PJ01 exposure bound. The model/hardware/runtime mismatch remains. FV86 conclusions are unaffected. No additional search, experiment, source execution, or canonical mutation was performed for this correction.

Review provenance: parent independent review identified the operation-scope mismatch before retention. This is an append-only terminology and interpretation correction, not a new hypothesis or changed proposal status.

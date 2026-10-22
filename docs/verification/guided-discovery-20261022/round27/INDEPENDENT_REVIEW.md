# Independent review: round27 tokenizer version bridge

Verdict: no blocking correction for the finite CPU compatibility claim. Retain as a refinement of S01; no implementation or service promotion.

## Independently checked

Read preparation, worker and comparison code and report. Verified all 19 frozen artifact hashes and all 12 referenced source/input hashes. Recomputed complete-ID equality for all 74 named fixtures (70 distinct strings) for both artifact serializations from the retained outputs, using my own receipt checks. Each artifact has 12 genuine native full calls and 62 guarded Rust-HF fallback calls; segmented execution has 118 ordinary-span calls, all routed through the native core. Raw/effective and old/new reference IDs agree on these cases. Verified native binary hash against the installed frozen round20 build. Worker commands use separate Python environments and explicitly assert 0.22.2 versus 0.23.2/Transformers 5.16.1. The loaded effective serialization matches the saved round23 representation.

The 14 split_special_tokens=True mismatches are real negative examples. They demonstrate an exclusion a future adapter must enforce; the diagnostic does not implement or certify such an admission layer. The full 74 native-wrapper matches are not 74 native-core successes: 62 use the old Rust HF engine. The segmented comparisons provide separate native-core coverage for ordinary substrings, with HF added-token matching orchestration.

## What this establishes and leaves open

This resolves a finite cross-version/serialization uncertainty for the selected exact checkpoint strings. It is stronger than merely comparing two wrappers using the same HF version. It does not establish universal tokenizer equivalence, offsets, truncation, paired inputs, postprocessing, a certified repair session, full facade admission, or deployed endpoint semantics. Both artifact runs repeat the same cases; 148 comparisons are not 148 independent strings. Examples are deliberately selected and short (maximum 1,549 characters), not a realistic request-frequency estimate. Actual loader versions on a serving node remain unattested. Existing timing results were not rerun against the new reference.

The experimental native constructor bypasses normal family admission for this CPU diagnostic; registry certification remains unchanged. Import/socket guards and receipts are useful evidence but are not an OS sandbox. I did not rerun the tokenizer corpus or timing, load a model, inspect a device, call the network, or modify canonical state. Review conclusions are bounded to source and recorded-artifact consistency.

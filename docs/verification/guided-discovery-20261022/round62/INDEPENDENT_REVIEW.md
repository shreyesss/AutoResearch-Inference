# Independent root review: round62

Agree with zero new cards. Read the report, exact FlashInfer2836 three-file diff, pinned MegaMoE dispatch and FlashMLA call sites, and selected numerical-admission/static-feature paper sections. Verified all49 frozen artifacts and the target source manifest. Native MegaMoE already supplies topology, capacity, token count, routing count and MMA type to tile dispatch. FlashMLA Mega invokes its own fused operator; the TRTLLM-gen sparse MLA selector is not that path. In the actual donor diff, the batch-dependent head branches are <=32 and128;64 selects its static KeepsMmaAb route. This does not imply every downstream donor launch parameter is globally batch-invariant.

The recent papers support two reusable design ideas: candidate-induced hardware features and pruning against specified reference arithmetic. Their reported trained dense-Hopper ranking and symbolic checker do not establish B200 persistent-MegaMoE performance or FP8/FP4 equivalence. Opaque unsupported instructions must not become proof. No checker, compiler or target kernel was run in this review.

Independently recomputed the binary32 grouping example with Python struct:0 versus1. This only disproves a universal algebraic/dtype equivalence assumption; it does not demonstrate a real tactic mismatch. The report's preservation of the first failed scalar fixture is appropriate.

A concrete source-fidelity issue was independently confirmed: both final text files exactly match exported fulltext bodies, while unnecessary reparsing as HTML changed them. For the numerical paper,96822characters became76525, removing inequalities and C++ references/templates; the second lost template arguments. Character loss is diagnostic of this transformation, not a semantic-error percentage. The corrected bodies preserve original evidence. No new fetch was needed.

Root added a short deep-research skill instruction to inspect the returned representation, preserve exact retained text, and treat cleanup as derived. Skill validation passed. This is a response to observed source corruption; no measured increase in reasoning quality or future compliance is claimed. A first character-level full-file diff was slow and explicitly terminated; bounded line comparison sufficed. This operational stop is not a scientific negative.

All conclusions are source-only. Existing tuning investigations remain unchanged; no GPU, canonical state mutation or performance acceptance occurred.

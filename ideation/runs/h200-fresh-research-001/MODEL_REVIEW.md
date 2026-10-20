# Model review and recovery record

All 17 distinct initial mechanisms are retained. There were 13 unchanged-mechanism recovery descendants and one root quote-only repair, for 31 new immutable records. The latest selection is **16 deferred, 1 rejected, 0 accepted** under the frozen rubric. Eight conditional diagnostic plans were registered without changing those selections. No GPU experiment ran.

| Lane | Initial proposals / requested | Initial outcome | Recovery / latest outcome |
|---|---:|---|---|
| attention | 3 / 4 | completed_no_selection | Original separate critic completed |
| systems | 5 / 5 | failed | New immutable revisit; original proposals preserved |
| compute | 5 / 5 | failed | New immutable revisit; original proposals preserved |
| cross-engine | 3 / 3 | failed | New immutable revisit; original proposals preserved |
| prefill-mqa | 1 / 1 | completed_no_selection | Original separate critic completed; quote-only root descendant changes structural rejection to deferred, critic criteria unchanged |

## Failure and repair details

- Systems, compute and cross-engine critic prompts exceeded the CLI limit of 1,048,576 input characters. They failed before producing reviews. The raw errors, oversized prompts and registered proposals remain in the original directories.
- The source-packing fix retains every packet/cited source, caps extra retrieval at 64 total documents and limits duplicated API metadata. Omitted IDs and excerpt flags are explicit. Recovered critic prompts were roughly 0.5–0.56 MB, and all three completed. Full records remain archived.
- Revisit cards link to originals; the mechanism is unchanged. The systems revisit adds late read-only evidence that Engram uses shared DP memory, leading to the private-branch rejection.
- Prefill evidence repair and the proposer both used the exact nine-character excerpt “avg +3.7%”, below the validator’s 12-character minimum. The original failures remain. The root expands the excerpt to its adjacent exact source context, registers a repair descendant and reapplies unchanged critic judgments. This is an editorial repair, not another model critique or a correctness pass.
- The generated policy rationale accidentally described a 0–1 scale; the frozen copy documents the prose correction to actual 0–5 weighted scoring. Weights, gates and threshold were not relaxed after outcomes.

## Latest mechanisms

| Card | Frozen selection | Score | Root disposition |
|---|---|---:|---|
| [H01](experiments/H01.md) | deferred | 76.0 | planned conditional diagnostic; prerequisites unresolved |
| [H02](experiments/H02.md) | deferred | 76.0 | planned conditional diagnostic; prerequisites unresolved |
| [H03](experiments/H03.md) | deferred | 82.0 | planned conditional diagnostic; prerequisites unresolved |
| [H04](experiments/H04.md) | deferred | 76.0 | planned conditional diagnostic; prerequisites unresolved |
| [H05](experiments/H05.md) | deferred | 76.0 | planned conditional diagnostic; prerequisites unresolved |
| [H06](experiments/H06.md) | deferred | 72.0 | planned conditional diagnostic; prerequisites unresolved |
| [H07](experiments/H07.md) | deferred | 74.0 | planned conditional diagnostic; prerequisites unresolved |
| [H08](experiments/H08.md) | deferred | 78.0 | planned conditional diagnostic; prerequisites unresolved |
| [H09](experiments/H09.md) | deferred | 76.0 | defer implementation; retain conditional design |
| [H10](experiments/H10.md) | deferred | 72.0 | defer implementation; retain conditional design |
| [H11](experiments/H11.md) | deferred | 76.0 | defer implementation; retain conditional design |
| [H12](experiments/H12.md) | deferred | 63.0 | defer implementation; retain conditional design |
| [H13](experiments/H13.md) | deferred | 76.0 | defer implementation; retain conditional design |
| [H14](experiments/H14.md) | deferred | 74.0 | defer implementation; retain conditional design |
| [H15](experiments/H15.md) | deferred | 67.0 | defer implementation; retain conditional design |
| [H16](experiments/H16.md) | deferred | 68.0 | defer implementation; retain conditional design |
| [H17](experiments/H17.md) | rejected | 37.0 | inactive on current baseline |

Scores are prioritization judgments. Required unknowns override a high score; the 82/100 mHC card remains deferred. An experiment plan is an instruction for resolving unknowns, not an executed outcome or a waiver.

Model calls used the existing authenticated CLI configuration, with no explicit model override. Proposer and critic are separate calls to the configured model, not independent experts. [Root synthesis](root-review.json), [decision ledger](decision-ledger.csv), [planned tests](planned-tests.json) and [memory export](memory-export.json) retain the distinction.

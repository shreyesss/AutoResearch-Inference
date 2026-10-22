# Independent review: offline conditional round estimator

**Verdict:** no blocking issue in the reviewed patch. This supports delivery as a conditional CPU diagnostic, not native DSpark/AV validation or a serving improvement.

## Reviewed boundary

Read the complete estimator, documentation and focused tests, plus the foundation parser/command/deferred-snapshot changes, MCP wrapper and shared record/call path. Read the new discovery-skill routing bullet. The source hashes in `source-manifest.json` identify the reviewed revision. No repository files were edited by this reviewer.

The estimator uses the round87 ideal fixed-block posterior: running prefix minimum of Q/P for block verification, product of per-edge minima for ordinary rejection. Forward round-start occupancy sums to the conditional expected round count. Cap-crossing events terminate the current round. Proposal zero support is legal and cannot be revived by a later positive ratio; target zero probability cannot condition an output and is rejected. All-anchor input is required even if a particular anchor has zero occupancy. The tool neither collects nor certifies the supplied probabilities or trajectory origin.

## Independent checks executed

- Focused production tests: `python -m pytest ideation/tests/test_round_estimate.py ideation/tests/test_mcp_research.py::test_mcp_round_estimate_retains_inputs_without_network -q`: **23 passed**. This includes an actual MCP invocation through the normal shared command path.
- Reviewer `independent_controls.py`: **160 exact-rational backward Bellman comparisons** against the production forward/log implementation. These cover both laws, B=1/2/5/16, L=1/2/3/7/13, equal proposals, zero support, zero followed by positive support, and deterministic random rational inputs. This is a distinct calculation of the same assumed posterior, not a separate proof of that posterior or native verifier behavior.
- Hand-derived ternary example: block 1.5 rounds versus ordinary 1.75. B=1 agrees between laws. Minimum-subnormal and 1e-300 controls passed without prefix-product division underflow.
- Strict version/type, huge integer probability, zero target and incompatible AV controls reject with static ValueError messages after the author's narrow guards.
- Actual CLI subprocess in a temporary isolated state retained matching input/result and the canonical-JSON input hash. An invalid law carrying a sentinel string failed without echoing it or adding a new result directory. The temporary state was deleted after the check.

The first reviewer CLI setup incorrectly supplied `--defer-snapshot` to `init`. It was rejected before mutation with the existing actionable error; corrected invocation succeeded. This failure is retained separately and is not an estimator defect.

## Corrections resolved during review

The initial code accepted boolean/float schema version 1 and exposed TypeError/OverflowError for unhashable selectors or enormous integer probabilities. These did not produce false results, but weakened schema errors. The author added strict version and string guards plus range checking before `isfinite`; this review and its source pins cover that corrected code.

## Scope and limits

Input provenance is explicitly caller-declared (`provenance_verified=false`). Normalized scalar realized-token probabilities cannot establish whole-vocabulary normalization, true target sampling, counterfactual anchor coverage or absence of hidden policy state. The docs correctly require these assumptions, exclude AV/EOS and describe fixed full-block generation followed by an output cap. Averages over arbitrary benchmark text are not claimed to be population estimates. Block versus ordinary arithmetic is a control, not a new optimization; the native baseline already uses block rejection.

Binary64 log arithmetic is not exact-rational/native parity and tiny probabilities may underflow. Retained input hashing is canonical JSON, not a claim to preserve original file bytes. The integration validates before writing output records and uses the existing writer/journal/snapshot path; this review does not certify multi-file crash atomicity or cloud restoration. No provider, model, native kernel or GPU calls were used. No full research suite/bootstrap or skill-validator pass is claimed by this reviewer; parent owns required full gates, and the reported skill validator dependency was unavailable.

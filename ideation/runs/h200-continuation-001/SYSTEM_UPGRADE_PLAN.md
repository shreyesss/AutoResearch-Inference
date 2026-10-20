# Research-system upgrades and remaining validation

## Implemented in this pass

- Carry every indexed hypothesis family and explicit experimental holds into
  proposal and critique. Freeze the register, cards, prior results and supplied
  evidence; check for changed inputs before generation and after critique.
  Resume through a new handoff with an explicit added/modified/removed delta.
- Apply expected benefit, engineering time, evaluation GPU-hours and pilot
  decision value at both generation and review. Preserve unknown effects;
  accepting a research design does not release a serving attempt.
- Scan all local titles/opening bodies without a per-query result cap. Retain
  unmatched entries and feed continuation URLs. Audit missed vocabulary and
  separate opening coverage from patch/discussion review depth.
- Add DeepInfer openings, selected implementation/PR reviews and maintenance
  discussion. Keep released code, unmerged proposals, author benchmarks and
  local results separate.
- Preserve proposal failures and lineage. This run exposed a citation to an
  unregistered history path; the structural gate rejected it. The next prompt
  explicitly distinguishes evidence IDs from paths in history. The critic now
  treats candidate count as an upper bound, avoiding quota pressure.
- Supply within-run assessment history to later critics as well as proposers.
  The second critic otherwise questioned a procedural rejection that was real
  but omitted from its context. The final follow-up's refreshed memory includes
  that rejection; future multi-round calls also pass exact within-run history.
- Repair selection deduplication for revisions whose parent uses a global
  memory ID: the child replaces its parent in the current selection while both
  stay in history. Regression tests cover that behavior and a result changing
  during critique, which must block assessment while retaining the proposal.

The original two-round call began before the last prompt/deduplication repairs;
its saved prompts and raw outcomes remain authoritative for that call. The
subsequent eligibility review uses the updated runner. Do not rewrite an old
model decision to look as though it had newer evidence or software.

## Next upgrades, in order of decision value

| Work item | Concrete deliverable | Acceptance criterion |
| --- | --- | --- |
| Applicability packet depth | For a selected port, include the complete critical dispatch predicates, loader path, launcher/reduction and installed-vs-upstream file hashes. | A reviewer can identify activation, semantic exclusions and missing code without treating a truncated packet as a complete implementation. |
| Retrieval coverage measurement | A prospectively frozen, separately labeled topic set spanning hardware, model, correctness, releases, host and kernel work; retain difficult unmatched items. | Report per-topic recall/precision and unresolved labels. Do not measure on the same 40 items used to repair queries. |
| Pilot calibration ledger | Original predicted effect scenarios and effort/GPU budget alongside actual cost, observed component effect and final scoped decision. | Identify which assumption failed and whether the pilot changed allocation. Distinguish a justified stop from an inconclusive measurement. |
| Equal-budget selector comparison | Give the history-aware system, keyword selection and optional seeded topic-matched random selection the same sources and pilot budget; blind candidate scoring. | Compare factual correctness, baseline applicability, test discrimination, prior-outcome preservation and avoidable expensive work. Random is a selector baseline, not a novelty test. |
| Service-value validation | Only for a qualified candidate, matched unprofiled service evidence under the frozen objective, correctness and tail gates. | A demonstrated improvement per total research/evaluation cost, preserving failed attempts and uncertainty. This run supplies no such result. |

Do not implement a new ranking formula to hide absent measurements. Weights are
an explicit prioritization policy; they are not a calibrated model of expected
speedup or success probability. The immediate useful output is a source-grounded,
falsifiable intervention with a cheap decision gate—or a justified hold.

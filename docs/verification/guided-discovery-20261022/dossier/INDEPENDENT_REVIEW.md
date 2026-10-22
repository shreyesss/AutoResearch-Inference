# Independent review — linked research dossier fix

**Verdict: no blocker found for this additive fix.** The previously demonstrated cold-start omission is repaired for the real retained schemas, without changing selection or immutable history.

Reviewed actual diff in `research_flow.py`, CLI dispatch/parser, MCP `hypothesis_show`, and new tests. Source SHA during real-state replay: `bea53aea536c900aa4254a925bc6868095f5257e3eb9f83296a48c6ae3410ceb`.

## Field replay

Reused only the diagnostic database copies created by the earlier read-only audit. Neither canonical state nor the original isolated validation states were opened for mutation. Dossier constructors operated on copies; the measured dossier calls made **zero changes** to the hypothesis database.

| Cohort | Linked records now exposed | Default linked payload | Full linked payload |
|---|---:|---:|---:|
|192022|2 investigations +1 bundle|4,626 characters|70,144 characters|
|21232425|2 investigations +1 bundle|5,096 characters|50,419 characters|

Both original investigation conclusions, false service/implementation qualification flags and historical selection scope are now present. The previously unreferenced21232425 bundle is discoverable through the graph edge rather than requiring an event. Default previews preserve existing order and explicitly count omitted references:

-192022: `review_artifacts`2/2, `evidence`4/80, bundle `artifacts`4/173.
-21232425: `review_artifacts`2/2, investigation `artifacts`4/30, bundle `artifacts`4/150.

With `include_artifacts=True`, merging projected metadata and complete reference arrays **exactly reconstructs every original linked node** in both copies. No fields or references were lost. All preexisting dossier fields compare equal to the earlier readback; S01 status stays accepted for bounded CPU investigation, with immutable node data unchanged.

## API and regression checks

- CLI `hypothesis show --include-artifacts` dispatches the optional flag; the propose branch does not evaluate the show-only attribute.
- MCP adds an optional false-default argument and forwards the flag only when requested; old calls remain valid.
- No compact recall changes in this diff.
- All original non-artifact metadata remains intact. Lists recognized as hash/path reference arrays are projected, including the older `review_artifacts` form.
- Complete mode returns reference data, not file bodies; no linked artifact execution or automatic body retrieval occurs.

Executed:

```sh
.venv/bin/python -m pytest ideation/tests/test_research_flow.py ideation/tests/test_mcp_research.py -q
.venv/bin/python review/dossier-surface-fix/probe.py
```

**42 tests passed in1.52s.** The real-state probe passed with zero hypothesis-DB changes and exact source hash stability during replay. No GPU/network/model calls. No reviewer repository edits.

## Explicit remaining limits

The preview is the first four references, not a ranked report picker. That is honest in help text and complete retrieval is available. It does not add labels that older records lack, nor claim referenced files are available or hash-verified merely because pointers are returned. Artifact arrays must match the current hash/path dictionary shape to be shortened; other metadata is retained as recorded. There is no global response-size cap or snapshot-isolation claim. These limits do not block the demonstrated omission repair.

This fixes tool discoverability, not the scientific quality or current validity of historical investigation conclusions. Later investigations remain separate chronological records; users must interpret their scope and qualification flags.

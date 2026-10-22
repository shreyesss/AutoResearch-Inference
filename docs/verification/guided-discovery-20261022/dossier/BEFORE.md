# Dossier linked-evidence omission — independent replay

## Finding

**Verified usability gap, no evidence deletion.** `ResearchFlow.dossier` at source SHA `29c4e78b3756bade5aa898af5197b18c3913f387635d46add1ac92e54f3e5164` returns hypothesis, typed claims, typed screening/plan/decision records and experiment registry rows. It does not traverse existing `has_investigation` or `has_evidence_bundle` edges. MCP `hypothesis_show` delegates directly to this path.

The retained graph has real S01 refinements and artifact references that this advertised cold-start surface omits. Events sometimes expose IDs, but do not dereference their conclusions. This is not a claim that every piece of CPU evidence is invisible: existing tests, scopes and linked claims expose some of it.

## Actual isolated replay

Used SQLite backup from `mode=ro` / `query_only=ON` connections into fresh diagnostic copies. `ResearchFlow` and dossier constructors ran **only on those copies**, where they may initialize their normal schemas. Original isolated states and canonical state were not mutated. Copies contain database state, not all original artifact files, so their filesystem availability resolutions are not a portability audit.

| Isolated cohort | S01 dossier characters | Investigation nodes omitted | Bundle references omitted | Investigation conclusions present verbatim |
|---|---:|---:|---:|---:|
|192022|96,449|2: round18 and round20/22|173|0/2|
|21232425|72,629|2: round18 and round23|150|0/2|

Both show S01 accepted, preserving its original meaning of bounded CPU investigation. In192022 both investigation IDs and bundle ID appear in events, but their node data does not. In21232425 both investigation IDs appear, while the bundle ID itself is absent. The isolated cohort copies are separate seeds; this replay does not claim they jointly represent the latest canonical state.

Specific missing conclusions:

- Round20/22: “Round20 actual native CPU repair and conditional timing/exposure; round22 simpler stateless full-input segmentation. Same S01 identity, no admission or serving claim.”
- Round23: “Default sidecar concern closed only at5.16.1/0.23.2; native0.22.2 parity/live adapter admission still open.”

The latter is its historical investigation conclusion. Later round27 narrows that finite version gap; a surface must preserve chronology rather than silently rewriting the old node or presenting old limits as an eternal current verdict.

The actual stored reference shapes vary:

- Round18 investigation uses `review_artifacts`, `source_round`, `scope`, `finite_proxy_result` and explicit qualification flags.
- Round20/22 uses `evidence` (80 pointers), `refinement`, `selection_scope`, `implementation_status` and explicit flags.
- Round23 uses `artifacts` (30 pointers), `scope`, `selection_unchanged`, claim IDs and qualification flags.
-192022 bundle has173 pointers and an explicit `artifact_map_path`;21232425 has150 pointers, limits and no explicit map-path field. Do not manufacture one as a recorded fact.

References are pointers and hashes, not embedded file bodies. Dumping all of them is still avoidable response bulk.

## Smallest recommended additive change

1. Add a dossier-only `investigations` and `evidence_bundles` projection from the two existing edge relations. Include ID, kind, original run/round, chronological order, original conclusion/scope/refinement, selection/implementation/service qualifiers, and reference count. Leave all existing dossier fields and compact recall unchanged.
2. Preserve non-artifact metadata rather than invent a new scientific verdict. A graph investigation is supporting history, not a replacement for latest attributed selection or an experimentally validated result. Preserve false flags and historical scope.
3. Include a small deterministic preview of retained report/review/manifest pointers, their state-relative path/base/hash/bytes and source-relative label when recorded. Expose total/omitted counts. Resolve labels from bundles only with matching path **and SHA**, never rewrite immutable nodes. Include explicit artifact-map pointers when provided.
4. Provide an explicit opt-in to retrieve complete linked node data/reference lists, e.g. an additive `hypothesis show` / MCP argument. This avoids a new parallel retrieval engine and ensures an omitted pointer is still accessible without SQL. Returning IDs alone repeats the current problem. If no complete-details option is added immediately, clearly expose the limitation and a concrete existing retrieval route; do not advertise full cold-start access.
5. Do not automatically load173 artifact bodies or copy historical artifacts during a read. Reuse existing read-time artifact resolution when needed; references do not themselves attest local availability or integrity.

Illustrative proposed summary files under this review use four pointers per node and retain metadata. They add only4,905 /5,115 serialized characters for these real states. These are diagnostic projections, **not implemented API output**. Their helper prioritizes recorded report-like labels and demonstrates size only; production handling should use the path-plus-hash match and explicit missing-details route above.

## Minimal regression gates

- No linked records: additive empty arrays, existing shape unchanged.
- Each observed schema (`review_artifacts`, `evidence`, `artifacts`) exposes its original scope and false qualification flags.
- A bundle with no event still appears via the graph edge.
- A later investigation appends history; immutable baseline/card/latest selection do not change.
- Default preview includes counts/omission and known report pointers; opt-in details returns all references without reading bodies.
- Same path/different SHA cannot borrow another record's source label or resolution.
- Compact recall stays bounded and unchanged.

## Artifacts and limitations

`probe.py`, `checks.json`, both `*-dossier-before.json`, `*-linked-nodes.json` and `*-proposed-summary.json` retain the readback. Actual command:

```sh
/Users/shreyas/workspace/AutoResearch-Inference/.venv/bin/python review/dossier-surface/probe.py
```

Exit0. Source hash was unchanged during the probe. Original connections reported zero changes; no canonical writes, GPU/model calls or network calls were made. A preliminary exploratory query used the wrong assumed edge-column name (`source` rather than actual `src`) and failed read-only; the executable probe uses the inspected schema. No repository edits were made by this reviewer.

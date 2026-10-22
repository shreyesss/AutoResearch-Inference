# Recall inspection miss — append-only clarification

The original saved recall contains67records and101,072characters. M02 is record59at character95,014. The actual inspection printed only `json.dumps(a,indent=2)[:20000]` with tool output budget6000tokens. M02 was outside that printed prefix; the complete artifact existed but was not read before the early promising-direction message. This was an inspection mistake, not a search miss or evidence of novelty.

The initial erroneous top-level-card query returned no matches; the query was immediately repaired to read `data.card`. The repaired complete output is `prior-recall.json`. The later adversarial pointer led to a direct extraction, `prior-M02.json`, and zero new identities.

Small tool improvement: return a compact complete list of known mechanism/source-family hits with stableID, short title and latest disposition, explicitly expose truncation/omitted counts, and prioritize exact source/paper matches for detailed read before candidate drafting. Source-family overlap does not automatically reject a useful new component; it makes its prior decision visible.

No tool code changes made here. Original science manifest is preserved; this note adds process evidence.

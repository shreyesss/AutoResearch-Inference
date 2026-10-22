# Independent canonical readback: rounds 15–18

## Scope and method

This is a read-only verification of completed canonical imports. `readback.py` opens both databases with SQLite `mode=ro`, sets `query_only`, and takes read transactions. It does not construct `ResearchFlow` or a `Store`, invoke migrations, restart importers, or write canonical state. New audit files are outside canonical state. No network, GPU, model, or serving calls occur.

The script checks the canonical retained receipt against the external importer receipt, every archived artifact's SHA-256 and byte count, prepared source records against immutable `document_revisions`, current documents against their FTS entries and bounded MATCH probes, exact claim quotes and locators against the specific revision body, hypothesis-to-claim graph relations, baseline content addressing and brief binding, latest selection status, scoped CPU test events, and complete discovery receipts and `discovered_by` revision edges. It also inspects append-only trigger definitions without attempting a canonical write.

## Round 15: verified

| Item | Independently checked |
|---|---:|
| Archived artifacts | 73 |
| Source revision records and current FTS consistency | 83 |
| Exact source-revision claims | 6 |
| Online query receipts / discovered-by edges | 3 / 24 |
| Hypotheses / CPU result events | 2 / 4 |

- **AT02** remains the existing identity, **deferred**. The QUILT/cross-token sharing work is appended refinement evidence. The immutable node bytes match the preserved isolated validation snapshot.
- **CMR01** is the new **deferred** identity. Its CPU artifact and event preserve **2 worse greedy proxy cases out of 200**, along with request-boundary, rank-shape, and adaptive-budget counterexamples. A balanced proxy does not establish shorter distributed execution.
- Both retain the content-addressed planned Flash-1017 baseline: checkpoint `1bae0e1088993b9b82de08f59de5be5a34e42170`, vLLM `c4557869393db4d75c483d92edd02a5125500883`, 8 B200, two planned TP1/DP4/EP4 groups. This is source-plan identity, **not a live deployment assertion**.
- All four new CPU test outcomes remain **inconclusive** for target implementation/service claims. The 1,000 set-identity tests and independent float64 algebra tests are not FP8/BF16 kernel or runtime validation. The synthetic counterexamples remain retained; nothing is promoted to a measured serving win.

## Round 16: verified after root's completed import

33 archived artifacts, 26 source revision records/current FTS entries, three exact claims, five original query receipts, 22 discovery edges, one rejected identity and one scoped inconclusive CPU result were independently checked.

**RT16-01** retains the target-scoped rejection: replacing repeated TP barriers does not transfer directly to the planned TP1 path. The symbolic two-read counterexample is not execution of SiFAR or a GPU memory-model/performance result. The baseline is unchanged.

One failed query has a later successful retry under the same query ID. Its current document therefore says completed/eight hits; the exact original failed receipt remains in immutable revisions. Both are recorded separately. This audit initially stopped on a too-strict current-body equality check, then verified the historical receipt directly. It did not reinterpret the failed round16 attempt as a successful one or duplicate root's independent HTTP-diagnostic audit.

## Rounds 17–18: verified after root's completed import

64 archived artifacts, 77 source revision records/current FTS entries, nine exact claims, five original query receipts, 33 discovery edges, two hypothesis identities and three scoped inconclusive CPU results were independently checked.

- **MP17-01** remains **deferred**, bound to the planned Flash1017 baseline. Its `derived_from`, `compared_with` and `same_mechanism_as` edges point to the prior H200 R1 identity. That parent's different H200 baseline remains intact. The source-closure shared-object and replay-override claims are present and quote the exact retained revision bodies. The CPU event explicitly calls its 500 same-function/equal-input cases consistency checks, not independent kernel validation.
- **S01** remains the same **accepted bounded CPU-investigation** identity. Immutable card bytes match the preserved isolated validation snapshot. The native/HF-proxy distinction, finite common-prefix coverage, renderer rewrites and trusted-prior limitation remain in the new CPU result scopes. Neither the HF suffix proxy nor seven reviewer callback tests are promoted to native session or serving validation.

`readback.json` now records all three cohorts as verified with scientific scope limits. During audit development, the FTS MATCH probe was corrected to use whole alphanumeric terms (`Flash1017`, `Round17`) instead of alphabetic substrings; current FTS bodies were already consistent. Both diagnostic assertion failures were audit assumptions, not canonical mutations or suppressed evidence failures.

## Limits

This verifies retained evidence and its stated scope; it does not rerun the CPU experiments. Existing-node comparisons use preserved isolated validation snapshots, baseline hashes and append-only constraints; no independent canonical pre-import filesystem image was captured for this audit. Source quote integrity does not automatically establish the interpretation of a paper or a performance claim. Current FTS records may legitimately have a later revision than the one cited; those two checks are deliberately separate.

The canonical imports used deferred checkpointing. This audit makes **no S3 completeness or recoverable snapshot claim**.

## Reproduce

From `/Users/shreyas/workspace/AutoResearch-Inference`:

```sh
PYTHONPATH=ideation .venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/review/canonical15-18/readback.py
```

This only replaces external `readback.json`; canonical state is read-only.

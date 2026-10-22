# Independent review — code-only investigate

**Verdict: no blocking issue found in the reviewed change.** This repairs the advertised explicit-code tool path without inventing a prerequisite paper or paper-to-code relationship.

## Source checks

- `validate_selection` validates exact40-hex refs, safe relative paths, explicit repositories and brief-contained selections before `_run_research` creates its Store/refreshes sources.
- A code-only/repository-only selection now invokes the existing bounded investigator even with zero selected source IDs.
- Explicit code fetches continue to share the existing cache-miss budget; cached text can be read with zero remaining network budget.
- Empty/failed code reads are retained as attempted-read receipts but cannot enable reasoning: `reasoning_source_ids` filters empty bodies, `model_calls_enabled` is false, and the model branch is skipped.
- `_run_research` calls typed reasoning retention only for an actually `reasoned` dossier. The former `if args.reason` path could try accessing nonexistent evidence on a failed/empty read.
- No selection returns honest `no_selected_sources` through CLI/MCP; direct internal `investigate` rejects no input. These are consistent interface-level outcomes.
- Explicit files without an associated source do not fabricate implementation edges. Existing selected sources and code can still be read together; evidence bodies do not establish compatibility or authorship.
- `run` refresh remains a separate command behavior. Its refresh traffic is not governed by the deep-read HTTP allowance; use `investigate` for bounded selected reads without refresh. This predates and is not changed by this patch.
- `_import_corpus` is unchanged; this review does not alter source-merge behavior.

## Independently executed checks

`cli_probe.py` invokes real `foundation.main`, Store and HTTP cache in a disposable state. Only HTTP transport is mocked; model/typed-reasoning retention are denied where no usable evidence exists.

Eight successful/error-accounted CLI invocations cover:

1. Initial isolated state creation.
2. Two requested pinned files with HTTP budget1: exactly one fetch/read and one budget error.
3. Offline reuse of that cached pinned file with zero HTTP misses.
4. Brief-only pinned selection through offline `run`, no source IDs.
5. Empty selection returns `no_selected_sources`.
6. Failed explicit read with `--reason`: no model or typed reasoning retention.
7–8. Invalid branch pin and traversal path reject before refresh or HTTP.

Final state: one document, one revision, zero graph edges, zero paper records. No live network/GPU/canonical writes occurred.

Additionally I ran the three changed test modules: **52 tests +15 subtests passed**. They include the actual MCP handler and real cache/CLI dispatch, with mock transport. This is interface/storage behavior evidence, not scientific hypothesis quality validation.

My first probe incorrectly supplied `--defer-snapshot` to `init`, then `run`; the existing explicit policy rejected those calls before mutation. The corrected probe limits deferred snapshots to `investigate`. This was reviewer setup error, not a defect in this patch.

## Bounds

No real provider or model response was requested. Repository-read parsing and arbitrary remote failure modes are not exhaustively tested. Empty-body rejection does not assess whether nonempty evidence is scientifically useful; the host's later critique and exact claim validation remain necessary.

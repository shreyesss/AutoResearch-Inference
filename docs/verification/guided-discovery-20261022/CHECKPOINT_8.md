# Guided discovery — checkpoint 8

22 October 2026. CPU-only research remains active. No GPU queries, experiments,
profiling, model loads or serving changes.

## What changed the decisions

| Direction | Evidence obtained | Current decision |
|---|---|---|
| MF19: mHC produces MegaMoE FP8 inputs | Concrete absent caller integration and upstream donor; small FULL-graph overlap bypasses it; source scale formulas agree in CPU transcription | Deferred until eligible workload exposure and buffer ownership are established |
| S01: incremental tokenization | Real native suffix execution; plain full native encoding beats Python repair, but long added-token appends benefit | Conditional CPU follow-up, requiring valid prior state and actual append exposure |
| S01 alternative: full-input added-token segmentation | Existing donor splitter/assembly reused; 5,429 finite ID comparisons pass; stronger full-operation baseline narrows timing gains | Bounded CPU integration investigation; no session-cache requirement, no service qualification |
| Output-side host work | New paper/PR/source investigation ongoing | Excluded from this checkpoint's card denominator |

### MF19: actual tool pipeline, without manufactured ROI

Three online searches returned 18 rows / 17 explicit paper identities; two full
texts were read. MonoMoE and MegaFlux supplied useful component questions and
counterevidence, not transferable service speedups. The selected donor is
vLLM #57977 at `18aac3985191e3850baeb16311ac7431521349d9`.

The first arm preserves BF16 routing input and the routing-only prepare launch.
It targets the later activation read/quantization pass only where MegaMHC
already executes. The original overlap implementation remains unchanged.
Full details and future unchanged Mooncake/agent-75 evaluation are in the
[mechanism report](round19-moe-fusion/REPORT.md).

The real isolated typed flow retained six exact claims, proposal, two screening
revisions, a CPU diagnostic plan and deferred decision. Initial omission of the
screen's explicit cheapest-falsifier input caused deferral; supplying the bounded
source check advanced diagnosis with **null gain**. The plan is review-ready,
not execution-authorized or service-qualified. [Tool receipt](round19-moe-fusion/typed-flow/TOOL_REPORT.md).

### S01: select the simpler component after measuring alternatives

Incremental repair is not a universal win. At roughly 131k characters, plain
native full encoding took about 0.67 ms versus 1.55 ms for the Python repair path.
Long added-token appends benefited from narrowing an otherwise whole-input HF
fallback, while renderer rewrites correctly fell back. These warm synthetic
CPU timings include output/adapter work but exclude cache population and session
management. [Timing and limitations](round20-native-tokenizer/timing/ADDENDUM.md).

The follow-up reused the donor's **existing** added-token splitter and assembly
helper to encode complete rendered inputs, with no previous session state.
The HF-backed splitter handles literals; ordinary spans call the unchanged
guarded native encoder. The default guard/registry was not disabled.

- 5,429 complete finite target ID comparisons matched HF; all 8,833 ordinary-span
  calls used Gigatoken, with no observed segment fallback.
- Correctness cases covered up to 1,549 characters / 552 tokens. Timing inputs extended
  to 33,751 characters / 16,813 tokens and also checked ID equality.
- Across 24 warm synthetic rendered shapes, segmentation beat external HF in 23,
  but the stronger unchanged guarded-native full operation in only 20.
- Against that stronger baseline, the median per-case ratio was 0.865; individual
  savings ranged from −45 µs to +1.67 ms. Some short, marker-heavy cases regressed 17–44%.

This removes the session-continuity requirement for this alternative. It does
not remove tokenizer configuration/sidecar/API compatibility, short-input
regressions, platform portability or actual workload-exposure questions. No
production crossover threshold was learned. Input tokenization directly concerns
admission/TTFT/CPU capacity; its effect on the primary long-output ITL objective
requires a demonstrated contention pathway and remains unknown.
[Full mechanism and scoped experiment](round22-tokenizer-segments/REPORT.md).

## Measured yield and tool changes

Through reviewed round19: **33 intervention cards: 2 accepted bounded CPU
investigations, 23 deferred, 7 rejected, 1 duplicate; zero implementation-qualified
or service-qualified improvements.** Rounds18/20/22 are refinements of S01,
not extra successes. MP17 is a child in an existing mechanism family. The
diagnostic selection fraction 2/33 is not a predicted success probability.

Updated the critic skill to require actual native/reference/fallback denominators
and a simpler full-operation comparator. Its use in round22 changed the ranking;
this is a field observation, not a controlled proof that the skill improves
research quality. Skill structural validation passed. The validator dependency
was installed only under a temporary directory, not into the research environment.

Updated the MCP screen description and user documentation to expose its actual
record envelope and `inputs.next_cheapest_falsifier`. Missing timing can remain
unknown; the tool does not copy a falsifier from another card automatically.
No screening behavior or scientific gate was weakened. Research suite:
**283 tests + 25 subtests passed**; bootstrap dry run and whitespace check passed.

Reports saying zero model calls mean no extra model API calls made by the research
tools. Host-agent reasoning is not included in that counter; total model cost is
not measured by this study.

## Persistence and continuing work

Independent read-only round15 verification passed: 73 artifacts, 83 immutable source
revisions, 6 exact claims, 24 discovery edges, 2 deferred statuses and 4 scoped CPU
outcomes. [Readback](review/canonical15-18/REPORT.md).

Round16, HTTP diagnostic import and round17–18 canonical writes remain queued
behind the publisher as of this checkpoint. The latest verified publication is
still `b3e4baa…`; the newer local snapshot is not claimed as published. Historical
117-reference retention completed locally, but repaired restore verification is
pending. Round19/20/22 retention preparation is underway; selected reports and
source hashes are in Git, not evidence of canonical/S3 completion.

Continue with the source-supported output-host investigation and new paper-led
questions, while retaining these conditional results. No acceptance quota,
invented timing, or silent GPU escalation is used to improve the apparent yield.

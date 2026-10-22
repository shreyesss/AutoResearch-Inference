# Checkpoint 11 — test the mechanism before transferring the headline

The guided inventory remains **34 retained reviewed hypothesis cards: 2 accepted bounded CPU investigations, 24 deferred, 7 rejected, 1 duplicate; zero implementation/service qualifications**. A separately reviewed host candidate, HS30-01, is deferred but not yet imported. Including that pending candidate gives 35 reviewed proposals/25 deferred; do not mix that denominator with canonical retained cards. Attention and replica screenings below create no additional hypothesis-card yield.

## New source and CPU findings

| Direction | What survived review | Decision |
|---|---|---|
| MF19 small-row fusion | A normalized-input kernel could emit FP8/scales while preserving BF16 routing input. Two BF16 rounding boundaries matter; scalar counterexamples show that removing either can change values or group scale. For <=8 rows, additional work delays the side-stream release as well as the input. | Same deferred MF19 identity. 10,240 logical BF16 read bytes/row are potentially removed, not a service-time forecast. |
| Fixed-reference softmax | A common finite score shift cancels mathematically, including the learned sink. A reduction-only component can be considered without adopting the paper's complete INT8-cache architecture. | Deferred: safe reference/fallback and exposed removable work missing; target already uses slack-six lazy rescaling. |
| Split attention readiness | Donor exposes P-ready and O-rescaled separately, but its PV consumer waits for both. Pinned one-CTA target already polls independent QK work. | Reject signal splitting alone. A different buffering/lookahead redesign would need a separate dependency proof. |
| CRAFT replica budgets | Per-layer redundant-expert allocation is conceptually separable from the whole system. | No forecast: target ABI uses uniform physical count; released replay drops integer remainders, corrupting small-batch load estimates. |
| CAP expert placement | Select placement without lossy expert pruning. | No transfer of reported gain: paper's per-destination communication premise differs from pinned MegaMoE per-expert staging/top-k output slots. Physical network traffic is still unmeasured. |
| HS30 prompt-tail registration | Conditional repeated Python registration calls exist for certain cache geometries/EAGLE flags. | Deferred, low priority. Existing pool already skips duplicate inserts and uses precomputed hashes; remaining bookkeeping may be tiny. |

Read [MF19 refinement](round29/REPORT.md), [attention report](round30-attention/REPORT.md), [replica/placement report](round32/REPORT.md), and [host report](round30-host/REPORT.md), each with independent review alongside it.

## Adversarial checks that materially changed interpretation

- **CRAFT:** exact FloorDiv expression extracted from pinned released Python; 123 of 260 constructed count/replica cases lose invocation mass. One token split over two replicas becomes all zeros, giving an artificial balancedness of 1. This invalidates that replay as a small-batch predictor; it does not refute the entire method or independently reproduce its published experiments.
- **Attention:** 27 abstract DAG cases assign the same equations to both branches. They illustrate a premise; the actual consumer source audit supplies the evidence. The 100 float64 identity cases do not certify target reduced-precision numerics. A constructed missing sample overflows f32; it is not a measured activation.
- **Host:** 1,024 repeated helper calls are not 1,024 expensive insertions. `_insert_block_hash` already checks primary/alias membership. The old donor helper also lacks the target's current non-EAGLE prompt-minus-one boundary logic; copying it wholesale would change behavior. Review proposes examining a smaller early-return alternative before introducing a persistent memo.
- **MF19:** conditional legality and integer layout checks establish neither physical register layout nor output kernel equivalence. Extra quantization can move work onto a critical branch; a traffic reduction alone is insufficient.

## Tool changes actually implemented

Commit `4c89c98` contains:

1. Synthesis instructions now require the first useful consumer newly unblocked by an overlap/readiness change, existing polling behavior, and accumulator/buffer reuse dependencies. Abstract identical-equation tests cannot substitute for source validation.
2. CLI emits the safe typed `unsupported_defer_snapshot` error before credentials, provider requests or state locking. Other arbitrary exception text remains redacted. This addresses an observed failed init/retry sequence.
3. Publication verifies every local chunk occurrence/file but performs immutable transfer work once per unique chunk hash. It records phase timings and context-local numeric SDK counters. Original failure exceptions retain partial diagnostics. Lock scope and lineage CAS are unchanged.

Verification: **301 tests +25 subtests passed**, bootstrap dry-run, diff check and skill validation passed. Independent publication probes also verified conflicting repeated-chunk sizes still fail before manifest/HEAD writes, and a streamed GET body failure preserves its exception/cleanup. No live cloud speedup was measured. Confirmed new-write counters may omit a remote write whose success response was lost; they are not billing/network-byte totals.

## Persistence status at this checkpoint

- Canonical19/20/22 and additional historical text mappings were independently read/hash-verified earlier. Canonical21/23/24/25 resume and26/27 import remain queued behind the active backfill/publication writer lock; no completion receipt yet.
- New29/attention30/32 retention passed isolated import/retry, default snapshot, relocated restore of140 references, and three CPU script replays. Root independently rechecked all source hashes and restored references; canonical apply is now queued. The illustrative float64 residual differed by~1e-16 across interpreters; both were below1e-12, all other fields matched, and the original strict-check failure is preserved. Host30 is separate and pending retention. Local frozen evidence is not a claim of S3 publication.
- Latest read local research manifest: `743ef260ed43b945f9b0680d6e36dbd09f41cdbc2f3634910c78c5088d9f2628`. Published lineage remains `532cb45daeada1624c98219d0307f7ef1bc189a5cf3dece66af4b9d08bf02dde` at 02:57:34 UTC. No new remote download/restore was performed.
- Existing backfill process loaded old code; it has not been restarted. New publication instrumentation is available to subsequent processes, not retroactively to that running publisher.

The loop continues with recent-paper discovery aimed at direct decode work. GPU experiments, device probes, model launches, serving changes and training remain zero. Tool-requested model calls in these probes are zero; host-agent reasoning cost is unmetered.

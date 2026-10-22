# Checkpoint 41 — stricter workload and comparator tests

22 October 2026. CPU/source research only. Zero new formal hypotheses, zero new qualifications and zero measured service wins in this checkpoint. This is useful filtering and refinement of existing directions, not evidence of improved inference.

## What survived and what changed

| Investigation | Mechanism and target-specific result | Disposition / next discriminating evidence |
|---|---|---|
| [115: sparse indexer FP8 adapter](round115/REPORT.md) | Pinned default FP8 blocks the current sparse-logits wrapper. Donor changes cover Q formatting, scale ABI and workspace; deleting guards is insufficient. Host-only AST checks establish call routing, not a native kernel result. | Parked refinement. Candidate capacity is16,384 positions: agent-p75's approximately9,216 maximum context cannot gain from logical candidate pruning. Longer Mooncake requests remain relevant. Need compiled ABI, numerical/membership contract, graph/workspace lifetime and measured exposed cost later. |
| [116: MemoryAttention and host lookup](round116/REPORT.md) | Recent donor row-local normalization folding does not carry through native multirow WKV projection and cross terms. Native prefetch and host-policy mechanisms already exist. Selected packed lookup component remains potentially relevant. | Refines existing row-colocation work. Whole-method adoption rejected; matched native packed comparator is required. Donor timings remain author-reported. |
| [117: comparator acquisition](round117/REPORT.md) | Released whole-Engine and small synchronous lookup benchmarks do not implement the claimed48M-row264-byte native packed microbenchmark. Three linked CI runs return zero downloadable artifacts. | Do not invent a substitute benchmark or call donor timing reproduced. Next useful evidence is the actual matched kernel/harness and paired receipts; access checks do not prove absence from every source. |
| [119: SP109 source-default allocation](round119/README.md) | FP8-default index width132 changes the declared B128 baseline to8 groups/136,224 common bytes/block. Mixed-width construction still fails; three valid manually preserved partitions still save zero stride bytes. | SP109 stays deferred. A viable physical layout is needed for capacity claims; logical traffic and quality remain separate. Mandatory correction: SM100 scale slot contains four repeated UE8M0 bytes, not FP32. |

Independent reviews are linked beside each report.115's donor test permits different selected IDs on ties; it checks selected value multisets, not exact target outputs. The Mooncake fraction above16,384 requested input tokens is roughly9–10.4% across the retained cohorts; this is not a time-weighted benefit estimate or observed live context distribution. Full top-k512 is also distinct from the16,384-position candidate-scoring domain.

## Measured discovery yield

115: two dated queries,13 returned rows/12 paper identities, one selected full text, selected PR and pinned-code triangulation. Four component screens produced one parked refinement and no new card.116: two dated queries,25 metadata/abstract results, one full text, selected donor source.117: seven online acquisition calls for exact PR file sets, missing pinned files and linked CI artifacts; no additional broad paper scan.119: no online requests; one bounded source-default extension with four scalar metadata scenarios and three manual controls.

These counts overlap earlier papers and existing hypotheses. They are not independent discoveries, formal acceptance rates or evidence of service gains. The loop adapted from recent-paper search to code compatibility, workload exposure and comparator acquisition. Repeated generic search was stopped where the missing artifact was already precise.

## Verification and delivery

Root independently verified116/117 source/revision packets and replayed119 in a separate directory.119 verified16 archive source files,7 original quotes plus3 correction source files/4 quotes. The round115 independent reviewer checked exact donor/native sources and workload receipts. These are source and stdlib controls; none exercised native GPU code.

[Retention review](retention-41/REVIEW.md) freshly restored277 artifacts,165 exact source revisions,49 quotes and100 provenance rows representing50 unique query/paper pairs across113–117. No hypothesis state changed in that package.119 is not included there and requires later additive retention. Canonical serialization and S3 publication remain separate from this local restore and Git delivery; no blanket cloud-completion claim is made.

No production Python or skill changed since checkpoint40's408-test/29-subtest verification. Documentation delivery passed whitespace/hash checks; no redundant full suite was run. [Copy manifest](source-copy-manifest-41.json) binds exact selected files and mandatory corrections. Ongoing research: the recent residual-sampling paper and cross-token sparse-indexer candidate reuse; neither unreviewed result is promoted here.

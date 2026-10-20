# Meta-critic: retain A002 and repair unused-rank metric readiness

Reviewed A002's retained controlled-traffic receipt, raw observation 0001,
drain implementation and installed metric logger source before any native B
result. All eight native A receipts and runtime identity passed. The ten initial
requests returned HTTP200, exact independent token/count/usage expectations,
length completion and active k5 speculation. The first drain snapshot then
raised `ValueError` for missing engine activity series and aborted the run.

This is not evidence of a nonzero queue or corrupt output. Both outer replicas'
observed rank0 running/waiting gauges are zero. Ranks1–3 have no running/waiting
series; all forty terminal counters are present, with exactly five rank0 length
completions per replica and zero others. The first snapshot follows the last
completion by roughly 26 ms. The drain helper's nominal sixty-second loop
propagates that first missing-series exception instead of recording unknown
readiness and waiting. Installed metric code updates the activity gauges when
it receives scheduler statistics, whereas this fixture routed every request to
rank0. Plain polling is therefore not guaranteed to initialize unused ranks.

**Recommend a prospectively fixed A002-native/B003-native comparison and a narrow
lifecycle readiness repair.** A third baseline cold load would mainly repeat
already qualified native work to compensate for the client fixture's metrics
assumption. With about forty-one work minutes left under the original deadline,
that is poor allocation. Unlike A001, A002 has complete runtime identity and
successful initial real requests; it is a defensible fixed native comparator.

Freeze A002's exact native files and hashes before B exists. Use a new B run ID,
explicit cross-run comparison manifest and reader identity bindings. Do not
pretend the two arms share a run ID, revise 002 into a complete pair, mix A001
timings, or choose a baseline after seeing B. Keep the native source, workload,
analysis and candidate unchanged. The changed lifecycle requests occur after
native timing, so they do not alter that measurement's treatment definition.
Report the incomplete A002 lifecycle lane and asymmetric subsequent fixture
coverage honestly; independent evaluator acceptance determines what integration
claims the combined evidence supports.

Root/builder's smaller repair is preferable to adding six extra primer requests:
redistribute the existing first five requests per outer replica across all four
ranks, keeping all twenty request bodies and the total request budget. I
recommended **ranks `(0,0,1,2,3)`** for the first five rows: counts remain
`(2,1,1,1)`, while original row0 and row1 remain rank0 references for the later
cancellation/recovery and EOS/wake checks. Freeze the chosen mapping before B.
Then require actual gauges and three consecutive all-eight zero observations.
No absent gauge is converted to zero.

The CPU repair must account for the new known routing/counter offsets. After
this initialization every rank has been used: the earlier never-used-rank
counter exception must not survive as `unused_rank = rank != 0`. Later missing
counters remain unknown, not zero. For transient metric publication, a narrowly
typed valid-but-incomplete observation may reset the consecutive-zero count
and poll within the existing sixty-second deadline. Preserve each raw scrape
and the reason. Unexpected identity, duplicate/nonfinite values, contradictory
counts or malformed observations still fail immediately; do not catch every
`ValueError` indiscriminately.

Require independent review and focused CPU positive/negative controls before
the B-only continuation. Preserve 001 and 002 failures, executed source and all
cost. Keep the original absolute 00:19 work / 00:24 cleanup UTC deadlines; no
new ninety-minute allowance. The B admission decision uses remaining time and
observed startup cost, never A's performance. This repair advances the intended
native comparison without turning incomplete telemetry into a false drain pass
or spending a third cold load on unchanged A.

## Final prospective revision: preserve concurrency, add six primers

After reviewing `evaluator/C25_NATIVE_CONTINUATION_003_CONTRACT.md`, support
root's selected **26-request** revision. This supersedes the earlier preference
for redistributing twenty requests. The stronger reason is to preserve the
original five concurrent, different-ID rank0 rows in each replica, which test
actual multirow committed-token ownership. Adding six short deterministic
requests costs seconds and retains that coverage; another baseline cold load
costs about eighteen minutes.

Keep the original ten requests unchanged. In the same explicitly bounded fresh
initialization phase, append one primer on ranks1,2,3 in each replica, with the
declared existing bodies and exact token/count/usage/k5 checks. Then require the
first strict drain and absolute initial length counts `(5,1,1,1)` per replica,
all other terminal reasons zero, and router counts eight per replica. All eight
engines have now been used, so actual later counter series are mandatory.
Missing gauges remain unknown, with only the typed bounded readiness behavior
described above; the strict all-eight zero gate is unchanged.

The fixed A002/B003 comparison remains appropriate: the exact A002 baseline
freeze was written before any candidate output, native timing precedes the
changed lifecycle traffic, and the independent contract retains original
native input, oracle, identity and statistic checks. A002's incomplete
lifecycle and B003's additional primer coverage must remain explicit. This is
not a retrospectively successful002 run or a paired complete lifecycle test.
The original absolute budget and outcome-independent B admission guard remain
binding. Focused CPU controls and independent executable review are still
required; this meta-review does not release a GPU allocation.

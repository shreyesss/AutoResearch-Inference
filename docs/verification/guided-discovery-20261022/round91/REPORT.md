# Round91 — use existing metrics, but verify what they count

## Outcome

FV86 remains deferred. A bounded local-evidence check did not recover compatible
actual admitted-length/full-valid-pass frequency or exposed residual cost. A
source audit found a useful refinement: the pinned stack already offers detailed
per-request speculative statistics, but those arrays **do not provide the actual
AV-admitted length**. A future FV86 diagnostic must use the effective GPU slice
or equivalent eligibility flag, not silently equate its scheduler count with
admission. No new optimization, model/profiler/GPU run or network request occurred.

## Existing evidence was checked before proposing collection

Prior trace-applicability and remote-evidence reports already distinguish older
H200/unsuffixed-Flash artifacts from exact Flash1017/c455. The retained local
B200 folders contain aggregate scores/manifests/configuration, not the required
joint per-step exposure. Historical AV-k5 timing has different source/model
identity and instrumentation qualifications. We read those prior audits and
selected summary fields; we did not re-download archives, reprocess giant traces
or infer that compatible evidence cannot exist elsewhere.

The initial filename searches printed bounded prefixes only. They locate known
artifact families and are not an exhaustive new corpus audit. No existing exact
target full-pass measurement was found from these leads. The prior audits remain
the scope record; this round does not increase their remote coverage.

## Source trace: detailed is not the same as effective

All six code files match the locally retained committed-object source archive
for `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; the archive hash
was verified. This is a source pin, not live-image attestation. Only source text
was read; no module was imported.

1. `config/observability.py` exposes `per_request_spec_decode_metrics` with
   none/summary/detailed levels. Default is none. Detailed adds ordered accepted
   and drafted arrays; the documented response surface is single-sequence only.
2. `metrics/stats.py::RequestSpecDecodeMetrics.observe` stores the numbers passed
   to it. Its summary includes accepted-count histogram and total drafted tokens;
   mean acceptance length includes a bonus. Neither its name nor level certifies
   that "drafted" means actual AV admission.
3. `core/sched/scheduler.py` obtains `num_draft_tokens` from the length of
   `scheduler_output.scheduled_spec_decode_tokens[request]`. It subtracts grammar
   invalidations before per-request observation. Accepted count comes from the
   returned sampled-token length minus the configured newly sampled count, before
   subsequent stop handling. The aggregate metrics use the same scheduled count.
4. `worker/gpu/model_runner.py` explicitly says the AV reallocation happens on
   the GPU side. It replaces the sampler's `cu_num_logits` with the result of
   `reallocate_drafts`, while the earlier per-request CPU draft counts retain
   their separate role.
5. `adaptive_verification.py::reallocate_drafts` starts capacities from valid
   scheduled counts, chooses an uneven admitted count under its budget, and
   computes `cu_num_logits` from **capacities + bonus count**. Its return values
   are the effective GPU cumulative lengths, query starts and total budget;
   it does not send per-request admitted counts into the scheduler metric call.

Consequently, existing detailed response metrics can describe scheduler-level
acceptance, but are insufficient by themselves to decide `accepted == admitted`
under AV. Config, output validity, probabilistic/full-q branch and other FV86
eligibility restrictions must also be established. No claim is made that the
existing counters are inherently useless or incorrect for their scheduled-count
definition.

## Matched-observation witness

The source-level witness holds every listed retained metric fixed: scheduled5,
accepted2, three sampled outputs including bonus, accepted histogram, both
per-position cumulative arrays, detailed accepted/drafted arrays, mean3 and
draft acceptance2/5. One possible hidden admission is2 (complete valid pass);
another is5 (partial acceptance). FV86 can omit one interior residual row in
the former and none in the latter. Thus those retained fields cannot determine
the required terminal-pass condition. This is a finite information-loss witness,
not an executed AV allocation or observed model trajectory. It does not refute
an output that also retains actual admitted lengths or a native terminal flag.

## Minimal future observation and evaluator reuse

If an existing compatible artifact contains effective per-request admission and
accepted length, use it. Otherwise, when native diagnostics are separately
authorized, capture the joint `(actual admitted valid drafts, accepted drafts)`
before request/stop aggregation, plus the exact eligibility branches. Prefer a
count of the same terminal flag being proposed, with an independently checked
denominator. Do not add a GPU-to-host synchronization on every request merely to
collect it; the collection path and overhead need their own bounded design.

Record graph/ragged/mapping conditions and failures. A residual-stage timeline
must separately determine exposed cost and added flag overhead; a high full-pass
frequency alone is insufficient. Use the existing Mooncake and agent-p75 inputs,
same AV and sampling configuration, and paired native parity/serving controls.
This is small mechanism instrumentation around existing evaluators, not another
load harness or permission to run a GPU experiment now.

## Tool usefulness

The next decision gap was exposure, so existing evidence and exact source were
more useful than another paper query. Six retained code files were registered
through the normal isolated JSONL corpus import, with seven exact quote anchors.
No provider spend or canonical write occurred. A first `git rev-parse` attempt
correctly failed because this retained pin is an archive, not a checkout; the
archive manifest/hash and byte comparisons establish the actual provenance.

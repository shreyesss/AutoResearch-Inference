# Round103 — source adapter design for shared-noise verification

## Decision

**A bounded, explicitly seeded parity patch is source-feasible; normal unseeded serving is not yet admitted.** Existing target-only Gumbel sampling can serve as the functional oracle. A separate DSpark proposal branch can share its unsalted, unstepped stream, and a small first-match packer can return the existing sampler/count interface. This requires no target tree verifier or new drafter weights.

The most important newly resolved blocker is request seed lifetime. The worker removes state on preemption, then re-adds the request. When its sampling seed is None, admission generates a new effective seed. That behavior cannot silently support the proposed persistent tape after lookahead. Explicitly seeded parity is a useful first arm, but does not qualify the standard unseeded workload. A durable effective-seed owner across preemption is a necessary part of the broader patch.

No native code was edited, compiled, imported or executed. No GPU, server, model, new paper query, canonical mutation or performance measurement occurred. This is the same deferred SN98 direction, not a new hypothesis. Exact source pin: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; planned Flash1017@1bae0e1088993b9b82de08f59de5be5a34e42170, TP1/DP4/EP4, native DSpark5, target temperature1/top_p1, baseline d464. Live backend selection remains unattested.

## 1. Smallest proposed patch boundary

1. Add an explicit experimental verification/proposal mode, rather than infer mode from whether a logits cache exists. Preserve current native modes by default.
2. In `DSparkSpeculator._sample_logits`, retain acceptance/confidence observation and normal Markov logits. In the new mode, call the existing `gumbel_sample` with the target stream (`is_drafting=False`), no cache argument and the same effective seed, precision policy and predecessor position. A None **argument to this primitive** avoids step mixing; setting the object's `draft_logits=None` currently selects greedy argmax and is not equivalent.
3. In the eligible target verifier branch, keep gathering and any admitted target processing, then call the same `gumbel_sample` on all actual verification logits. Pack the first matching prefix and its target mismatch/bonus sample. Do not draw a fresh correction.
4. Return the same `SamplerOutput` shape and count semantics. Retain the existing count adjustment, async copy, request update, draft context preparation and AV confidence publication ordering.
5. Bind request mode for its lifetime before exposing future noise. A whole-batch fallback because a later request has unsupported features is not safe for existing shared-noise requests. The smallest research engine can reject unsupported requests before admission; mixed native/shared requests require explicit routing and are a larger arm. No user feature is silently disabled.

For the first parity implementation, the existing cache allocation may remain while writes/reads are bypassed in the new branch. This intentionally does not claim memory-capacity savings. Removing allocation is a later change after loader/scatter, graph and all consumer checks; it must not regress reduced-vocabulary initialization or restore native rejection over stale cache contents.

## 2. Exact row and position map

Let r be a request's current **batch row**, R=`idx_mapping[r]` its request-state slot, s=`cu_num_logits[r]`, e=`cu_num_logits[r+1]`, n=e−s and d=n−1. These are device boundaries; AV can leave the CPU boundaries stale. Let `T[j]` be the target Gumbel sample from logits row s+j.

| Item | Pinned source meaning | Adapter requirement |
|---|---|---|
| Request owner | `idx_mapping` maps batch row to persistent state slot; expanded map repeats R for each logits row | Never key randomness by batch row or slot. Use effective seed belonging to logical request; slot is only the lookup address |
| Target row | `logits_indices` selects the trailing n positions of this request's current query span | Use exact existing gather; do not assume uniform six-row requests or host AV sizes |
| Target position | `pos[s+j]` is the absolute position of the input token whose logits predict the next token | Noise coordinate is predecessor position, not row index j |
| Draft candidate | `draft_sampled[s+j+1]` is the candidate predicted by target row s+j | Comparison is shifted by one. `draft_sampled[s]` is the anchor input, not candidate0 |
| Bonus | Last target row e−1 has no corresponding candidate inside this slice | Emit `T[d]` only if all d candidates match |
| Native DSpark proposal | `sample_pos=query_pos+1`; `_sample_logits` passes `sample_pos−1` | This equals the target predecessor position for the same predicted token; preserve unclamped sampling position versus clamped attention position distinction |
| Zero AV drafts | n=1, d=0 | Emit one target draw; ordinary target-only route and new verifier must agree |
| Chunked prefill | `seq_len < prefill_len` forces zero emitted tokens and zero rejected count | Keep existing helper; an ignored draw is not committed, and its coordinate must not be re-seeded later |
| Graph-padded draft row | `sample_idx_mapping=-1`, input index points to a valid dummy row | Preserve masked writes and no logical request progress; never use dummy coordinates as real seed state |

For fixed prompt length H and generated token index t starting at0, predicted absolute position is H+t and its noise coordinate is H+t−1. There is no need to subtract H inside a new PRF: existing absolute predecessor positions already identify the same future token across regrouping. Request incarnation controls ownership, but adding an arbitrary incarnation salt would change explicit-seed oracle semantics. Identical explicit seeds should retain their declared behavior.

Proposed packer, descriptive only:

```
for each real request r:
    s,e = device_cu[r:r+2]
    d = e-s-1
    m = first j in [0,d) where candidate[s+j+1] is invalid
        or candidate[s+j+1] != T[s+j]; otherwise m=d
    sampled[r,0:m+1] = T[s:s+m+1]
    num_sampled[r] = m+1
```

The output tensor retains `[num_requests, num_speculative_steps+1]`; initialize unused slots or retain a proven existing unused-tail convention, while counts alone determine emitted tokens. No vocabulary work is required in this packer. It must stop before an invalid candidate, yet emit the same target draw at that still-correct prefix. It may not commit descendants evaluated under the mismatching prefix.

## 3. Counts, target cache, draft cache and output release

`get_num_sampled_and_rejected` computes `num_rejected = n - num_sampled`, except unfinished prefill where both are zero. For m accepted drafts, sampled count=m+1 includes correction/bonus, and rejected count=d−m. Keep that exact convention; returning only accepted-draft count would corrupt state.

`post_update` appends all sampled IDs, updates last sampled token and total length, then advances computed count by `query_len−num_rejected`. The correction is output but not yet target-KV-computed; valid input rows through its predecessor remain computed. DFlash preparation uses `valid_ctx_end=ctx_end−num_rejected`; rejected suffix context gets zero positions/PAD slots, while the last sampled correction/bonus becomes the next draft anchor. These consumers can accept the new count contract without changing their meaning. This is source compatibility, not proof that sparse cache/indexer/CED state works after native execution.

Preserve `AsyncOutput` construction before postprocess and next proposal. It copies sampled IDs and counts while keeping tensors alive, and trims CPU lists using `num_sampled`. Moving a new packing/join after that copy would expose incomplete outputs; delaying copy until drafting completes would change streaming latency. The proposed target draws and pack complete at the existing sampling boundary.

EOS, stop-token IDs and maximum length stay in the scheduler's per-token output handling. `_update_request_with_output` appends each token, calls `check_stop`, trims later output and adjusts computed count for resumable requests. String stops remain in output detokenization. A new packer must not bypass these stages or count post-EOS speculative outputs as delivered progress. Initial tests must exercise them even though retained benchmark defaults use ignore_eos=true. Existing user stop behavior is not disabled to simplify the arm.

## 4. Effective seed: actual source blocker and bounded repair

`SamplingStates.add_request` stores the explicit request seed, or draws an int64 using NumPy when seed=None. The drafter copies that seed into its persistent sampling buffers. That storage is sufficient across ordinary steps, but not every request lifetime:

- `finish_requests` unions preempted and finished IDs before removing worker state.
- `add_requests` also removes old state before re-adding a streaming-input update.
- Re-addition calls `sampler.add_request` again, so a None seed is regenerated.
- `RequestState` distinguishes original `prompt_len` from resumed `prefill_len`, confirming that re-prefill may include prior outputs. Position reuse is real, not a new unrelated request.

For SN, any exposed but uncommitted noise coordinate must survive this regrouping. A fresh seed after noise-dependent preemption/admission cannot be assumed equivalent. This is not an allegation against the native ratio verifier; it is a new mode's stronger lifetime contract.

**Arm A, parity only:** require an explicit effective seed in every admitted request and preserve it on re-add. This enables a bounded source patch without a new seed registry, but does not qualify unseeded serving, streaming prompt revision, migration or restart. No automatic retry/recovery is promised beyond the engine's existing failure behavior.

**Arm B, necessary before default workload qualification:** allocate effective seed once per logical request incarnation; retain it across preemption and re-prefill, and remove it only on actual finish/cancel. A scheduler-carried effective seed or worker map keyed by logical request identity could provide this. The implementation must distinguish the existing finished/preempted sets before union, define streaming-input identity, synchronize ownership if a request migrates, and prevent stale state when an ID/slot is reused. Process restart that currently aborts requests need not acquire a new recovery feature; any supported resume must transport the seed. This is a required ownership patch, not an assumption that the present GPU seed array already solves it.

Retained agent-p75 and Mooncake workload YAML omit request `seed`; `sweep.py` forwards it only if supplied. The load generator's `--random-seed` controls prompts and scheduling, not `SamplingParams.seed`. Experiment request overrides can add a seed, and executed request bodies were not recovered here. Thus saved defaults support the relevance of Arm B, while actual launch behavior remains unknown.

## 5. Admission and fallback table

| Condition | Initial decision | Why |
|---|---|---|
| Native DSpark, text path, target temp1/top_p1, top_k normalized to vocab, min_p0 | Admit after inspecting actual config | Existing target-only sampler takes its Gumbel route; no new categorical backend |
| Native full target vocabulary, no reduced draft mapping or base-topk special mode | Initial narrow arm | A later reduced draft support can still preserve target law, but target-token noise keys/scatter and its altered proposal need separate validation; do not silently change existing q support |
| `needs_logits_processing=False` for every admitted request; no custom processors configured | Admit | Sampler returns logits unchanged. Still retain the stage/call boundary rather than duplicate a guessed processor list |
| Thinking enabled in prompt/template, no runtime budget | Potentially admit | `reasoning_effort` changes template; separate `thinking_token_budget` defaults None. “High75” does not prove forced-budget processing |
| Actual thinking budget, penalties, bad words, logit bias, min-token masks, grammar or custom callbacks | Unsupported in initial arm, reject/reroute before future draws | Do not turn features off. Grammar masks live outside `needs_logits_processing`; that flag alone is insufficient |
| Logprobs/token-ID logprobs/sampling masks, watermarking, trace replay, synthetic acceptance | Exclude initially before admission | Additional consumers/forced outputs need explicit oracle and cost contracts; logprob reductions cannot be claimed removed |
| EOS, stop IDs, ignore_eos and output cap | Preserve existing semantics | These are output lifecycle requirements; initial no-processor gate may exclude min_tokens masks but not all stopping |
| AV disabled/enabled as configured | Preserve | Keep confidence generation, stale budget history and device prefix selection. Do not silently force fixed five drafts |
| Static unsupported request before any future draw | Existing native path in a separate admitted mode, or clear admission failure | No selected-future-noise bias |
| Invalid draft marker, AV truncation or another late condition after shared lookahead | Keep same-tape target draw at actual prefix; discard incorrect descendants | Never switch to fresh independent native correction after conditioning on the tape |
| Invalid/missing target logits at required actual prefix | Abort/explicit unsupported path until correct target-only same-tape logits can be computed | A permissive grammar row or all-invalid scores is not a certified fallback distribution |
| OOM/cancellation/native exception | Preserve existing failure behavior | No invented recovery path. Any retry that resumes the logical request must retain its tape identity |

The first research engine should fix mode at construction and validate requests before sampling. A production mixed-mode implementation must carry request mode through packing/graphs and preserve it across new admissions, rather than changing all existing requests when one unsupported request arrives. Target TP1 avoids batch-sharded sampling; retain current DP4/EP4 collective order. PP/PCP/TP-sharded extension, request migration and multi-modal position semantics require additional source gates, not an unannounced new distributed protocol.

## 6. Actual AV and physical work

AV records confidence after proposal and can rank candidate prefixes on device; CPU budget history may lag. Native DSpark confidence includes embeddings of previously sampled parents. Sharing noise changes those parents and the acceptance law, so unchanged confidence weights/budget policy can be less effective. This affects progress and cost, not the pathwise oracle when its tape is retained. Preserve actual AV as a comparator and report admitted draft lengths jointly with committed progress. CPU arrays are upper bounds after nonzero-budget compaction; use device cumulative row offsets in target draws, packer, logprobs and counts.

For full vocabulary129280, existing `gumbel_sample` uses1024-column blocks:127 partial maxima/indices per logits row, then a block argmax and gather. FP32 local maxima plus int64 indices occupy1,524 logical bytes per row; FP64 policy uses2,032. The shared mode adds this full target draw for each admitted target row, plus one O(requests×depth) packing operation. It replaces eligible probability-statistics/cumulative-ratio/interior-residual/recovery stages, but does not eliminate target head logits, draft backbone, five Markov dependencies, confidence, AV, KV writes or all output bookkeeping. No kernel launch is assumed free or fused.

The first prototype may retain cache allocation even when no raw-q values are written. Do not advertise memory removal until allocation and graph/loader consumers are separated. No full-horizon tape allocation is needed if existing target noise is regenerated from stable coordinates; this retains PRF work on every target row. Cost must be compared against tuned C025/native block and FV86 where available, not an unoptimized generic rejection implementation. Existing round98/101 progress-cost objection remains; no timing estimate is derived from bytes or launch counts.

## 7. Next falsifier and stopping point

The source audit has resolved enough to specify a bounded seeded parity patch, and found why it is not yet a default-serving patch. The next meaningful gate is separately authorized native target-only oracle comparison with actual ragged AV rows, mismatches at every depth, zero admitted drafts, chunked/re-prefill, preemption seed persistence, cancellation/slot reuse, EOS/stops, graph replay and exact cache contents. Test seeded and unseeded owner paths separately; assert late fallback uses the same tape. These are future requirements, not tests run now.

Before implementation, root can accept or reject the proposed mode/ownership boundary. There is no need for another paper search or another finite toy proof: frozen98/99/101 already contain those controls. A new shared-noise hypothesis is not counted. The result remains deferred, with a feasible narrow interface and explicit seed-lifetime, feature-admission and native-correctness gates.

## Audit scope

Twenty exact target files were copied and hashed; selected methods were read, not every file audited exhaustively. Three previously retained benchmark source/default files establish request construction limits, not executed payloads. Claims retain exact file/line excerpts. AST inspection parses source only; no target module is imported. Bounded searches initially used a few nonexistent glob/path guesses, then located the actual AV/benchmark paths with `rg --files`; no empty result was treated as absence. Broad draft-logit references were truncated, so cache allocation elimination remains a gated later arm. No source performance or deployment completeness claim follows.

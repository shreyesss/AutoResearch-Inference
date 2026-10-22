# Independent round98 review — persistent-tape chain verification

## Verdict

**SN98 warrants a deferred hypothesis and a bounded adapter-design investigation.** The source delta is a complete alternative verification law, not a shortcut inside native ratio rejection. The claimed ideal pathwise construction is valid under its stated target-prefix, noise and state assumptions. No native implementation, continuous-PRF proof or performance qualification follows. Keep the original report unchanged and apply the fallback refinement below.

I checked all50 frozen author hashes,13 exact revision quotations and seven copied source bodies against c455. I read the selected fulltext AppendixA.4/A.6, report, oracle control, native sampling excerpts and root POSITION_TAPE_ARGUMENT. The check script records their identities. No new search, oracle rerun, GPU/backend import or canonical mutation was needed.

## Why the adapted argument works

The paper's TheoremA.6 explicitly assumes independent context-keyed clocks. A tape keyed by request and absolute output position shares clocks across alternative contexts, so it is a different construction. Root correctly proves that construction separately.

Fix the entire tape and define the target reference recursively at each actual committed prefix. At each proposed row, the first mismatch or all preceding matches certify that the row's predecessors are precisely that reference prefix. Its target sample is consequently the reference token; no child below a mismatch is emitted. A fully matched admitted prefix has the same property for its bonus. Admission may inspect future noise: it changes the partition into rounds, but not which tape entry supplies each committed output. With progress and a finite output bound, induction proves the complete sequence. The reference history uses only earlier position noise, so independent position vectors supply its target categorical law. This does not assert the conditional law given an observed future-dependent admission length, wall-clock cancellation or completed-request selection.

The192 finite comparisons exercise this construction with target rows computed at proposed contexts, including wrong descendants. They are useful implementation-of-the-model checks, not192 independent target trials or a proof of continuous randomness/native correctness. Real PRF finite-state correlations, floating reduction, ties and distribution conventions remain outside this argument. Exact equality to the declared same-tape target reference is an appropriate diagnostic for this particular coupling; it is not a universal same-seed requirement for all lossless speculative decoders.

## Required fallback refinement

The report permits unsupported modes to retain the old path. Distinguish two cases:

- Select an unsupported-feature/native mode before inspecting uncommitted future tape, using a fixed request contract or a decision measurable from the committed prefix. This can be a valid separately admitted mode.
- Discover invalidity after observing future shared noise, sampled draft tokens or an admission decision correlated with them. **Do not silently switch to an independent native rejection draw.** The sufficient fallback is target-only sampling at the committed prefix with the same persistent tape; any alternative needs its own conditional-law proof.

A late switch can reintroduce round99's selective-discard problem even though both unconditional samplers are individually correct. This is a fallback-boundary gate, not evidence of an existing native error and not a rejection of SN98. Stateful processors and grammar invalidity must either stay within a proved pure-prefix/tape path or be excluded before lookahead. Merely labeling a branch “fallback” is insufficient.

## Actual native interface and ownership

At c455 model_runner.py477–523, `model_state.custom_sampler(self.sampler)` can return the sampler/rejection-sampler pair. At1610–1689, the runner constructs full target logits, applies grammar masks, passes `invalid_drafts`, preserves an ordinary no-draft branch, and returns num_sampled/num_rejected. This is an existing seam, not proof that the V4.1 state already implements the new mode or needs no patch.

The following remain concrete adapter requirements:

1. dspark/speculator.py115–153: `draft_logits is None` currently means argmax. Removing persistent q storage must not silently turn probabilistic drafting into greedy. Preserve target-vocabulary mapping and conditional Markov parents; base draft logits and confidence inputs remain.
2. sample/gumbel.py14–20,74–76,241–267: native draft salt and cache-column seed mixing are intentional under ratio rejection. Define an explicit tape mode, not a global salt removal. Cache presence must not choose the seed. The preceding-token position convention (`sample_pos - 1`) must match the target row for ordinary, bonus, compacted and zero-admission rows.
3. rejection_sampler.py410–470: grammar invalidity pins acceptance through a separate verification copy; actual draft IDs still feed processing. Preserve masks, placeholders and output-count semantics. A batch can contain requests with differing admitted counts even when its aggregate speculative branch is selected.
4. spec_decode/speculator.py491–503: observe_verification grades stored features before the next proposal overwrites them. New first-mismatch progress must feed actual counts, not native ratio-law predictions. Unchanged AV code can remain the primary control, but its behavior and learned confidence calibration may change.
5. Preserve the same tape across retries, AV truncation, cancelled work and reused storage; request slot alone is not identity. No-draft/bonus/ordinary sampling must use a compatible reference policy. Rank and graph buffer ownership, cache rollback, EOS/stop and output logprobs remain implementation gates.

Pure prefix-based target processing can be included in F. Mutating state by processing rejected descendants, shape-dependent target numerics or cache contamination can violate the prefix-evaluation premise. The existing speculative target path is a useful starting point but source presence is not a native equality test. The report appropriately excludes unproved custom/watermark/synthetic modes and does not claim a sparse target head.

## Cost and comparative value

The changed law can remove q-normalization and block-residual work, and potentially persistent q-cache traffic. It adds full-target-row noise and reductions, while target backbone/head and the draft backbone/Markov dependence remain. Logprob requests may retain normalization work. Lower match progress can erase any component saving.

The p=(.6,.3,.1), q=(.2,.3,.5) shared-exponential diagonal formula yields18/35; maximal coupling gives3/5. The one-proposal progress ratio53/56 is therefore correct. Its >3/56 complete-round saving requirement is a conditional B1 discriminator, not a DSpark5 estimate or benchmark. Native block verification may recover longer prefixes than first mismatch. Do not feed marginal matching probabilities into the existing ordinary/block round-estimate tool as if it implemented this correlated tape policy.

Compare complete time per committed token and the frozen service objective against the strongest compatible native DSpark baseline, including applicable C025/FV86 changes. Record actual output counts, EOS/stop outcomes, AV admission and paired uncertainty. No target timing, attainable cost saving or on-policy progress distribution is present here.

## Cheapest decisive next work

Produce a narrow interface/seed/row-map design using the existing sampler seam, with a table of static admission versus late same-tape fallback, mixed request counts, zero-admission/bonus, processor/grammar state and rollback. This can reveal a concrete contract conflict without GPUs. Do not add more finite toys to substitute for that source design. Only after those boundaries are explicit should a later authorized native differential test compare the declared target-only tape oracle and speculative execution. Keep status deferred and ROI unknown meanwhile.

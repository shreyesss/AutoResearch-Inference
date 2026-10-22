# S01: executing the actual CPU repair algorithm on Flash-1017 tokenizer inputs

**Disposition: useful CPU compatibility evidence; still deferred for native-engine integration and service benefit.** No new hypothesis identity. No model, GPU, serving modification, MPS/availability probe, provider request or canonical mutation. The pinned donor and target repositories/files remain unchanged.

## What changed from the earlier source audit

The earlier S01 audit established that the tokenizer differs from the certified V4 anchor and that independent append-token concatenation fails. This round executes the donor's **actual boundary certificate, overlap matching, offset reconstruction and splice code** on the exact target tokenization, rather than repeating those two findings.

TokTier commit `0591fe18235f3e64f0576fa7f77a0804af1ba5c2` supplies an importable Python `GigatokenRepair` implementation. Its full facade/reference backend and fast engine require the native Rust extension; `cargo` is absent locally. No native build was attempted. The diagnostic substitutes `tokenizers==0.22.2` **only for the suffix window encoder**, so this is not a native Gigatoken performance/correctness qualification. No registry entry is added and no certified policy is changed.

## Exact control and experimental adaptation

The target file is the retained `deepseek-ai/DeepSeek-V4.1-Flash-1017` tokenizer revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, tokenizer JSON SHA256 `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b`.

1. **Original gate:** invoked the unmodified `Tokenizer._repair_callback` on a minimal constructed object with the target digest and an otherwise permissive fast-CPU route. It returns no repair callback with `artifact_not_in_certified_repair_roster`. This executes the real admission branch; it is not a full facade construction or public session API test.
2. **Explicit experimental arm:** instantiated unmodified `GigatokenRepair`, with the anchor's margin 36, effective max 128, window 512, max 5 retries, min 2 matching tokens and original digest-checked Unicode property table. Its spec is labeled `EXPERIMENTAL_flash1017_reference_window`. The target's maximum added literal length is 36 and the previously audited non-added tokenizer sections are identical to the anchor. Those facts justify this falsification attempt, **not transplanting certification**.
3. **Target encoder and offsets:** every reference/full/suffix encode uses the exact target `tokenizers0.22.2` artifact with `add_special_tokens=False`. The adapter exposes the target added-token IDs and vocabulary. Donor `_verified_byte_lengths` cross-checks lengths, `_spans_from_ids` reconstructs character offsets, `_build_records` and `_find_match` compare IDs/global spans/same-span ordinals, and `_accepted` enforces overlap length plus its synchronizing transition before splice. Original fallback behavior remains active.
4. **Renderer:** executed the pinned c455 standard-library `encode_messages`. The diagnostic wrapper only sends strict rendered appends to repair; a rendered suffix rewrite uses full reference encoding. It does not claim an edit-repair implementation or alter production rendering.

The JSON retains raw donor stats, whose hardcoded `engine=gigatoken`/`backend=fast_cpu` strings are explicitly labeled **not runtime engine attestation**; actual window engine is the HF reference proxy.

## Results actually obtained

| Test group | Cases | Scope |
|---|---:|---|
| Every interior split of all 18 changed old/new added literals |300| Partial special literals across append boundary |
| Unicode/whitespace/digits/contractions/long repeated character boundaries |1124| Includes combining marks, emoji, CJK, newline and a 1024-character repetitive tail |
| All 1283 target added literals, midpoint split |1283| Target ID/added-token handling, not every split of every token |
| Short input, empty delta and invalid prior span count |3| Explicit fallback/noop guards |
| Stateful 100-step append chain |100| Feeds prior repaired IDs and offsets into next actual repair |
| Pinned renderer transitions |8| Chat/thinking, drop-thinking on/off |
| **Total** |**2818**| **2818 complete ID sequences and 2818 offset lists exactly equal full reference** |

Of these, **2813** use the actual donor splice path; the remaining paths are one short-input full fallback, one invalid-state full fallback, one noop, and two explicit renderer-rewrite full fallbacks. The six renderer append transitions preserve 451–492 old tokens in these constructed examples. The two default thinking/drop-thinking transitions rewrite the old trailing six characters and correctly fall back to full encoding.

Most cases reuse the same approximately 2320-character synthetic base. The 100-step chain is one trajectory, and the renderer tests reuse a constructed conversation. These are deliberately concentrated boundary cases, **not 2818 independent workloads or production coverage**.

This is not a tautological full-output comparison: the experimental path only encodes a suffix, reconstructs spans and joins retained prefix IDs to suffix IDs; the comparator independently encodes the full new string. The suffix encoder is shared with the oracle by design, so it cannot detect native fast-engine mistakes. The donor made 3423 window calls over 2813 splice outcomes because some repetitive cases widened the window. No time/throughput result is inferred from those character counts.

## What this supports—and what remains untested

The result supports **structural portability of the donor's Python append-certificate logic on this finite exact-target fixture**. Added-token differences are not by themselves a reason to reject all CPU repair reuse. The proper next CPU integration test is a real native Gigatoken build/loader differential against the same pinned target, in an isolated compatible CPU environment, preserving failed admission until qualification.

Still untested: native corrected-Gigatoken engine, Rust session/store path, deployed Transformers loader/materialized tokenizer face, postprocessing/truncation modes beyond the specified core stream, arbitrary edit repair, worker/session ownership, eviction/cancellation, concurrency, natural workload coverage, and frontend service exposure. A finite passing fixture is not a proof for all Unicode/text sequences. No claim is made that target added-token hash can be allowlisted safely from this result alone.

The current standard agent-p75 and Mooncake inputs do not establish growing same-session text requests. Reuse the installed multiturn workload later only after verifying the session identity reaches the server; preserve agent-p75/Mooncake controls. These CPU probes need no GPU. Any eventual service test must separately measure actual renderer/tokenizer time, full output materialization, cache costs and TTFT before forecasting inference ROI. S01 still has no measured service win.

## Commands and failures

From `scheduling/`: `cpu-venv/bin/python ../round18-tokenizer-repair/repair_probe.py`.

Two initial diagnostic-control setup attempts failed before repair execution because the facade `family` property is read-only and delegates to `_backend.family`; the fixture was corrected to supply a minimal backend namespace. An initial broad filename glob also failed at the shell and was replaced by direct paths. These are diagnostic setup errors, not tokenizer mismatches. The final run writes `repair_probe.json` with every case, source hashes and exact scope. No accelerator/native modules were loaded; an import blocker enforces that boundary. No target source code was modified.

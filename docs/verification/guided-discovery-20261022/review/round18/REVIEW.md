# Independent S01 round18 repair review

**No blocker to retaining this as useful, finite CPU compatibility evidence for existing S01.** It does not qualify native engine correctness, default facade admission, production sessions, service speed or target deployment. Preserve S01's accepted bounded-investigation scope; native integration/service remain unqualified. No new hypothesis identity.

## What I inspected and executed independently

Read the complete worker proxy, final report and append-only REVIEW_CLARIFICATIONS; read unmodified donor GigatokenRepair including byte-length verification, character-span reconstruction, matching, synchronizing witness and splice/fallback paths. Confirmed the donor checkout is clean at0591fe18235f3e64f0576fa7f77a0804af1ba5c2. Independently compared the raw target and anchor tokenizer artifacts.

Executed `window_callback_audit.py` with existing CPU tokenizers0.22.2. Seven valid append cases used a different long numbered prefix and exercised Unicode, whitespace, contractions, digit boundaries and changed added literals. The callback for whole-input reference encoding raised immediately if called inside these cases. All seven took the actual donor splice path, retained660–661prior tokens, used a single522–536character suffix window rather than the3671–3698character complete prompt, and exactly matched full-reference IDs and offsets. This falsifies the concern that these particular fast-path outcomes were just full-input reference fallback in disguise.

Two additional controls exercised original fallback behavior: inconsistent prior ID/span counts directly called full reference without a suffix encode; injected window-encoder failure called full reference and returned matching output. All accelerator/native-engine imports were blocked; no model, native package build or GPU calls occurred. The donor's Python repair class itself was executed; unrelated source files were not executed.

## Trusted prior-state negative control

I deliberately corrupted a cached first token ID outside the suffix overlap while retaining the same list lengths. Repair still spliced and preserved that wrong prefix token. This **violates the donor's trusted prior-state precondition**, so it is not a discovered failure on valid inputs. It demonstrates why valid initial seeding, artifact/loader/session ownership, mutation handling and lifecycle checks remain necessary. The proxy's finite sequence test does not certify the complete public session store. Invalid-count fallback is not universal validation of cached contents.

## Offsets and artifact identity

Exact target tokenizer JSON SHA256:c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b. Donor repair source SHA256:0ff172ef830e60023fbb04bd5bedaec11643a2434aee828c8eda323001dc11c2.

The byte-length path reconstructs character spans, including repeated/overlapping character spans for byte-level pieces, then compares IDs, global spans and same-span ordinals. Multibyte control outputs matched HF offset lists; this does not establish equivalence to an uninspected deployed Transformers materialized tokenizer face.

Raw artifact comparison confirms nine changed added-token rows, matching ID sets and equal non-added sections. At ID128799 the literal changes to<｜System｜>, **normalized changes false→true and special true→false**; this is not exclusively a spelling change. Other changed rows are content changes. All target lstrip/rstrip/single_word flags are false, normalizer is an empty sequence. Maximum added literal is36characters/48UTF8bytes; donor window/margin are character-based, so those different units alone are not a found bound error. Native integration must preserve flags as well as token IDs/spellings.

Both proxy vocabulary bytes and HF-derived lengths originate in the same target artifact. The suffix encoder and full reference share HF0.22.2. Thus this is a real test of partition/splice/offset logic with a trusted reference suffix engine, not independent validation of native Gigatoken encoding or raw vocabulary.

## Admission and coverage

Read the real _repair_callback branch: exact family/digest roster lookup precedes backend.repair_components. The worker's minimal __new__ control validly demonstrates rejection of the supplied target digest under that configured family/route. It does not execute full facade construction, reference fallback wiring, router/device discovery or session persistence. The experimental spec deliberately bypasses admission inside the diagnostic; shipped registry remains unchanged. Guided_adversary independently checked this source branch and noted public session fingerprints include artifact/oracle/engine/config; that path is absent from the probe.

Worker2818matches include2813splices and five fallback/noop cases. Most use one repeated synthetic base;100stateful steps are one trajectory, and eight rendered transitions use one constructed conversation. Full-reference renderer rewrites correctly remain fallback cases. Counts cannot be treated as independent real workloads, broad Unicode proof, native-engine certification or speed evidence. The inherited backend=fast_cpu/engine=gigatoken stats are correctly relabeled as donor strings, not the executed engine.

The conclusion remains finite compatibility progress. Next qualification requires native/reference differential and full loader/session/template lifecycle coverage under the actual frontend, then measured workload exposure and host-time contribution. No estimate of TTFT/ITL or GPU benefit follows from reduced encoded character count; Python scans, matching, allocations and output materialization remain costs.

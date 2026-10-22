# Independent round104 review

**Verdict: no blocking correction.** The proposed output transport is a valid source-level inverse for the stated four-route layout. Keep SL97 deferred with null ROI and no new hypothesis. The refinement resolves ownership; it does not establish native arithmetic parity or efficiency.

## Source grounding and independent check

Verified all seven author manifest entries and both parent manifest/addendum pins. Target epilogue and donor two-lane source bytes exactly match frozen round97. Also read round97 target implementation call sites (hash retained in checks.json).

The target maps Pre to lanes0–3, Post to4–7 and row-major Comb to8–23. Its scalar store chooses normalized_comb only for Comb; Pre/Post use the original mix_value. Normal deliberately does not store Pre but returns the original mix_value, which run_normal_worker broadcasts through pre_coeffs. Shifted stores Pre as well. The final warp sync remains a separate contract. Thus preserving only the16 Comb stores would be insufficient; the report correctly preserves Pre/Post/return too.

The donor gathers original lanes8+i into every even lane and16+i into every odd lane, for i0–7. Normalization changes values but not the local index ownership. Hence each even lane owns matrix indices0–7 and each odd lane owns8–15. This is the four-route component only, not a generic route-count implementation.

For original output index `i=8p+k`, p∈{0,1}, k∈{0,…,7}, choose sender `s=2k+p`. Its parity is p and `(s>>1)&7=k`. The sender's chosen register therefore contains i. The source indices0–15 are a permutation, and destination8+i obtains its original cell. Non-Comb receivers may use source0 and ignore the result.

I independently checked this inverse with stdlib integer arithmetic without importing or running the author's control. All16 cells map correctly. In the specified naïve alternative, sources0/1 are non-Comb lanes and each sends register0, so only cells0/8 match and14 cells fail. This is a finite address permutation and a counterexample to that particular selection placement, not numerical evidence.

## Warp participation and preservation

The indexed shuffle must execute outside the Comb-store predicate in all32 lanes. In particular, sources0–7 are Pre/Post owners; excluding them would make many reads invalid. Upper lanes also participate under the full mask. The inspected Normal call uses warp_idx_in_wg==0 with warp-uniform token bounds, and the Shifted Mix token loop is warp-uniform. These source call sites support placement of an unconditional warp operation, but no compiled convergence/participation test was run.

The proposed comb registers and send value must not overwrite mix_value: Normal still consumes its Pre return, and Shifted/Normal preserve their respective stores. The mapping itself adds no required floating arithmetic, but it requires real selection and exchange instructions. An explicit select over eight scalar registers can avoid assuming that dynamic array indexing stays in registers; compiler lowering remains unverified.

The report correctly retains one source-level exit shuffle, index arithmetic and an eight-way selection cost. Donor entry gathers, duplicated per-lane coefficient work and longer register lifetimes remain. Native and donor each have four source-level shuffles per normalization stage; this transport does not create a total-shuffle saving. Actual40-register Shifted/80-register Normal constraints, spills, instruction scheduling, and the small-row TileLang overlap dispatch prevent a source-only performance inference.

Target epsilon,20iterations, fmaxf/__expf/fast reciprocal and reduction grouping must still be preserved. Integer identity says nothing about NaN, signed zero, finite reassociation or compiler contraction. Pre/Post outputs and return values require separate later numerical checks, not just Comb coverage.

## Next decision-relevant question

Further tag sweeps would not improve this conclusion. The most useful unresolved question is whether the exact target-arithmetic implementation with explicit scalar select8 and preserved mix_value lowers without spills or harmful register/code-size growth in **both** existing Normal and Shifted tactics. That requires separately authorized compiler inspection; no build or native execution is authorized here. It should compare the original kernel and a single layout-plus-transport arm, preserving dispatch and overlap. If that resource gate fails, more symbolic mapping work cannot rescue a latency claim. Actual route exposure and exposed timing would remain later gates even if compilation succeeds.

## Execution and limits

Ran `python3 review/round104-agent/check.py`: hashes, source quote assertions and independent integer inverse only. An initial lookup used an absent filename target-kernel.cuh; bounded directory inspection identified the actual retained target-impl.cuh. No source fetch, model/native import, compile, GPU work, canonical mutation or author artifact edit. No additional hypothesis, measured speedup or implementation qualification.

# Independent round24 review

Disposition supported: append to existing M02; zero new hypotheses. The exact K512 donor branch still selects `kSampled=false`, matching the earlier M02 rejection. A new donor commit is provenance refresh, not a new mechanism.

I inspected pinned c455 `csrc/sampled_topk.cuh` and `csrc/topk.cu`: the baseline already implements sampling, survivor compaction, exact selection and full-row fallback. The caller gates on rows >64, maximum length >=98,304 for K512 and sufficient shared memory. The kernel independently falls back for shorter individual rows. Thus maximum batch length is not evidence that every row samples. No hardware property or actual dispatch was observed.

The two equal-indexer-score/different-attention-value example correctly refutes the implication that equal top-k score multisets guarantee downstream equality. It does not prove native ties occur, disqualify all exact selectors, or demonstrate a donor bug. Preserve reference tie/ordering/numeric semantics in any future comparator.

A K512 non-sampled donor or K2048 producer use case can only reopen with separate absent-component and shape evidence; the paper sampled speedup cannot justify either. Report correctly distinguishes fulltext read from other shallow screens and records the duplicate-recall miss. No GPU, source edits, kernel execution or new qualification.

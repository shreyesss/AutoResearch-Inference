# Round33 review clarification — append-only

The original manifest and report remain unchanged.

`attention._can_fuse_query_quant` begins with the main `self.wq_b` and appends `indexer.wq_b` only when `self.indexer` exists. Indexers are constructed on index-source layers. Thus the report's two-consumer language applies to those layers; other layers require the main compatible consumer alone. Eligibility must be assessed per layer. Neither a fixed indexer multiplier nor an active number of exposed launches has been established.

Matching the existing producer's PDL calls is a necessary patch constraint, not a proof of downstream visibility. The pinned vLLM `mm_mxfp8` wrapper delegates to external FlashInfer; no complete consumer PDL/wait contract was audited. Any future device check must exercise the actual chosen consumer and graph path. The all-byte address partition remains only a finite CPU integer-layout diagnostic.

Disposition is unchanged: NQ33-01 deferred, no implementation-qualified or measured service gain.

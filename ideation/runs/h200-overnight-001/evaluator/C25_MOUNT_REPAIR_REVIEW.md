# C25 component mount failure: scoped infrastructure repair

Independently reviewed `executions/sampler-component-001/execution.json` and
`component/result.json`. The retained first allocation failed with
`FileNotFoundError` while opening the checkpoint shard, before loading either
Markov tensor or invoking any fixture/candidate. It produced no correctness or
timing result. The actual pinned installed source hashes, GPU UUID and baseline
dispatch were recorded; all frozen input hashes remained unchanged. Root
released the container and returned all GPUs to idle after 9.49 seconds,
0.002637 visible-GPU hours. Preserve this failure and its cost.

The root cause is a checkpoint snapshot symlink whose nested target lies outside
the read-only snapshot mount. The actual host shard resolves to the regular
blob under `/home/jl_fs/huggingface/hub/blobs/66/` ending in
`66874185d7e2f8727f885a331e70e910cf8fb42d410a87c0a4bb23894e4f7152`.
This is a mount-boundary error, not evidence against the sampler or permission
to change numerical criteria.

Accept a separately named allocation `sampler-component-002` with a versioned
root runner binding **only that resolved regular blob read-only** at
`/model/model-00046-of-00048.safetensors`. The parent can be empty; do not rely on
the escaping snapshot symlink. Before GPU execution, require a CPU-only
preflight of that exact mount confirming readable header, original header hash,
and both expected BF16 `[129280,256]` keys. Retain source symlink/resolution,
regular-file metadata and mount command. No model bytes or environment changes.

Evaluator harness remains
`7de227dafd67e555155166aa14d8c069e8f010d77750bcd6d5eceea8a7f46019`;
candidate remains
`7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`.
Use the same reviewed command, fixture matrix, shape gates, timing schedule and
failure behavior. The renewed allocation retains the 45-minute/one-GPU ceiling;
the initial 9.49-second infrastructure cost is reported in addition, not hidden.
This is one identified infrastructure repair, not an automatic candidate rerun.
Any later failure requires a new specific review. No service attempt is consumed
or released.

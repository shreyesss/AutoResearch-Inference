# Read-only deployment metadata check

At2026-10-22T01:39:08Z, SSH to `bitlane-b1` succeeded. `docker ps` returned only the running `node-exporter` container. No running vLLM container/image revision was available through this check.

This does not establish that GPUs are idle, that no bare-metal process exists, or that other nodes lack serving workloads. No GPU API/query, process-wide inspection, model loading, benchmark, profiling or container change was performed. It therefore leaves PJ01/EG01/RD01 live-backend applicability unresolved rather than declaring them incompatible.

`receipt.json` records the exact read command, observation and script hash. `remote_read.py` contains the bounded metadata-only script. The initial target remains a pinned source/plan reference, not an attested active image.

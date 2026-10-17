# Container deployment

The controller is trusted: it has Docker socket and GPU access and owns runtime
lifecycle, a one-GPU file lease, frozen workload assets, logs and metrics. The
Codex proposer runs through `deploy/codex-isolated` in a second image. It has
network access for the Codex API, read-only staged source and non-held-out run
files, a writable notes workspace, and a read-only auth mount copied into
ephemeral container storage. It cannot read the host repository, held-out
results, Docker socket or GPU. Do not
run the proposer directly in the controller container.

Build and start after creating `.artifacts` and providing existing Codex auth:

```sh
export IAR_REPO_ROOT="$(pwd -P)"
export IAR_CODEX_HOME="/absolute/path/to/your/.codex"
mkdir -p .artifacts
docker compose -f deploy/compose.yaml --profile build-only build
docker compose -f deploy/compose.yaml up -d controller
docker compose -f deploy/compose.yaml exec controller iar doctor --campaign configs/campaign.json
```

The trusted controller launches the pinned vLLM image by digest as a sibling
container, mounts the exact local model read-only, and binds its endpoint to
`127.0.0.1:8000`. The model can be obtained at the frozen revision with
`scripts/prepare-model.py` before starting. Controller results live under
`.artifacts`; Docker logs, startup checks, GPU samples and `/metrics` snapshots
are retained per cell. The controller image installs AIPerf 0.13.0; the proposer
image installs the observed Codex CLI version 0.162.0-alpha.17.2.

The controller image passed Dockerized `iar doctor --backend real` and a mock baseline. A Dockerized real MTP1 pilot also completed both frozen short-chat cells with full request accounting. The isolated Codex proposer returned a schema-validated proposal in its own container without launching an evaluator. Real autonomous search stays closed until the qualification report passes. Never mix mock and real artifacts in one confirmed frontier.

To inspect a run, execute `iar inspect --campaign configs/campaign.json --backend real --output-dir .artifacts/autoresearch-codebase` in the controller or host environment. It regenerates `inspection/INDEX.md` and `inspection/index.json` under the campaign's real artifact directory. These list the ledger timeline, proposals and feedback, each evaluation and cell's metrics, and paths to server logs, telemetry, AIPerf exports, request records, exact configs and failure records. Large files remain in their original locations. The SQLite ledger is the durable source; the index can be regenerated at any time and does not claim to contain learned lessons.

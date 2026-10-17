# Trusted controller and untrusted proposal process are separate images.
# Build both targets; the proposer never receives the Docker socket or GPU.
FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS proposer
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ripgrep jq python3 && \
    rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/local/bin/python
RUN npm install -g @openai/codex@0.162.0-alpha.17.2
COPY deploy/proposer-entrypoint /usr/local/bin/iar-proposer-entrypoint
RUN chmod 0755 /usr/local/bin/iar-proposer-entrypoint
USER node
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/iar-proposer-entrypoint"]

FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04@sha256:ebef3c171eeef0298e4eb2e4be843105edf3b8b0ac45e0b43acee358e8046867 AS controller
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates docker.io python3 python3-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/iar-venv
ENV PATH=/opt/iar-venv/bin:$PATH
WORKDIR /opt/iar-source
COPY pyproject.toml ./
RUN pip install --no-cache-dir aiperf==0.13.0 'jsonschema>=4.20' 'matplotlib>=3.7'
COPY src ./src
RUN pip install --no-cache-dir -e . --no-deps
COPY deploy/codex-isolated /usr/local/bin/codex
RUN chmod 0755 /usr/local/bin/codex
CMD ["sleep", "infinity"]

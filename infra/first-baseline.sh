#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${ROOT}/.artifacts/models/Qwen3.8-27B"
RUN_DIR="${ROOT}/.artifacts/first-baseline"
IMAGE='vllm/vllm-openai:v0.28.0'
CONTAINER='iar-b0'
MODEL_NAME='Qwen/Qwen3.8-27B'
URL='http://127.0.0.1:8000'

mkdir -p "${RUN_DIR}"

case "${1:-}" in
  up)
    test "$(find "${MODEL_DIR}" -maxdepth 1 -name '*.safetensors' | wc -l)" -eq 18 || {
      echo 'Model download is incomplete: expected 18 safetensors files.' >&2
      exit 1
    }
    if docker container inspect "${CONTAINER}" >/dev/null 2>&1; then
      echo "Container ${CONTAINER} already exists; inspect it before starting another." >&2
      exit 1
    fi
    docker image inspect "${IMAGE}" --format '{{.Id}} {{index .RepoDigests 0}}' > "${RUN_DIR}/image.txt"
    nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader > "${RUN_DIR}/gpu.txt"
    docker run --pull never -d --name "${CONTAINER}" \
      --gpus all --ipc=host -p 127.0.0.1:8000:8000 \
      -v "${MODEL_DIR}:/models/Qwen3.8-27B:ro" \
      "${IMAGE}" \
      /models/Qwen3.8-27B \
      --served-model-name "${MODEL_NAME}" \
      --tensor-parallel-size 1 \
      --dtype bfloat16 \
      --max-model-len 40960 \
      --max-num-seqs 512 \
      --reasoning-parser qwen3 \
      --host 0.0.0.0 --port 8000 > "${RUN_DIR}/container-id.txt"
    echo "Started ${CONTAINER}; inspect with: docker logs -f ${CONTAINER}"
    ;;
  smoke)
    "${ROOT}/.venv/bin/python" - "${URL}" "${MODEL_NAME}" "${RUN_DIR}" <<'PY'
import json, pathlib, sys, urllib.request
url, model, run_dir = sys.argv[1:]
body = {
    "model": model,
    "messages": [{"role": "user", "content": "Give three prime numbers above 100."}],
    "chat_template_kwargs": {"enable_thinking": False},
    "temperature": 0,
    "max_tokens": 64,
    "stream": False,
}
request = urllib.request.Request(
    url + "/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=300) as response:
    result = json.load(response)
path = pathlib.Path(run_dir) / "smoke.json"
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"finish_reason": result["choices"][0]["finish_reason"], "usage": result.get("usage"), "saved": str(path)}))
PY
    ;;
  benchmark)
    curl --fail --silent "${URL}/health" >/dev/null
    warmup_args=()
    if [[ "${WARMUP_REQUEST_COUNT:-0}" != 0 ]]; then
      warmup_args=(--warmup-request-count "${WARMUP_REQUEST_COUNT}")
    fi
    "${ROOT}/.venv/bin/aiperf" profile \
      --model "${MODEL_NAME}" \
      --endpoint-type chat --endpoint /v1/chat/completions \
      --streaming --url 127.0.0.1:8000 \
      --tokenizer "${MODEL_DIR}" --apply-chat-template \
      --use-server-token-count --per-chunk-usage \
      --prompt-input-tokens-mean "${INPUT_TOKENS:-512}" --prompt-input-tokens-stddev 0 \
      --prompt-output-tokens-mean "${OUTPUT_TOKENS:-256}" --prompt-output-tokens-stddev 0 \
      --extra-inputs "{\"chat_template_kwargs\":{\"enable_thinking\":false},\"temperature\":0,\"ignore_eos\":true,\"min_tokens\":${OUTPUT_TOKENS:-256}}" \
      --request-rate "${RPS:-1}" --request-rate-mode constant \
      --concurrency "${CONCURRENCY:-8}" --request-count "${REQUEST_COUNT:-24}" \
      "${warmup_args[@]}" \
      --random-seed "${SEED:-42}" --export-level raw --export-http-trace \
      --output-artifact-dir "${RUN_DIR}/${ARTIFACT_SUBDIR:-aiperf}"
    ;;
  down)
    docker stop "${CONTAINER}"
    docker logs "${CONTAINER}" > "${RUN_DIR}/server.log" 2>&1
    docker inspect "${CONTAINER}" --format '{{json .Config.Cmd}}' > "${RUN_DIR}/server-argv.json"
    docker inspect "${CONTAINER}" --format '{{json .State}}' > "${RUN_DIR}/server-state.json"
    docker rm "${CONTAINER}"
    ;;
  status)
    docker ps --filter "name=^/${CONTAINER}$" --format '{{.ID}} {{.Image}} {{.Status}} {{.Ports}}'
    du -sh "${MODEL_DIR}" 2>/dev/null || true
    ;;
  *)
    echo "Usage: $0 {up|smoke|benchmark|down|status}" >&2
    exit 2
    ;;
esac

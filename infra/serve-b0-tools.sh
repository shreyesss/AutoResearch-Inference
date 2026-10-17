#!/usr/bin/env bash
# Qwen B0 serving profile with vLLM auto tool choice for Exgentic replay.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="$ROOT/.artifacts/models/Qwen3.8-27B"
OUT="$ROOT/.artifacts/ops-b0-tools/server"
IMAGE='vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14'
CONTAINER='iar-b0-tools'
mkdir -p "$OUT"

case "${1:-}" in
  up)
    test "$(find "$MODEL_DIR" -maxdepth 1 -name '*.safetensors' | wc -l)" -eq 18
    if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
      echo "$CONTAINER already exists" >&2
      exit 1
    fi
    docker image inspect "$IMAGE" --format '{{.Id}} {{index .RepoDigests 0}}' > "$OUT/image.txt"
    nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader > "$OUT/gpu.txt"
    docker run --pull never -d --name "$CONTAINER" \
      --gpus all --ipc=host -p 127.0.0.1:8000:8000 \
      -v "$MODEL_DIR:/models/Qwen3.8-27B:ro" \
      "$IMAGE" /models/Qwen3.8-27B \
      --served-model-name Qwen/Qwen3.8-27B \
      --tensor-parallel-size 1 --dtype bfloat16 \
      --max-model-len 40960 --max-num-seqs 512 \
      --reasoning-parser qwen3 \
      --enable-auto-tool-choice --tool-call-parser qwen3_xml \
      --host 0.0.0.0 --port 8000 > "$OUT/container-id.txt"
    ;;
  smoke)
    "$ROOT/.venv/bin/python" - <<'PY'
import json, urllib.request
body={"model":"Qwen/Qwen3.8-27B",
      "messages":[{"role":"user","content":"Say hello."}],
      "tools":[{"type":"function","function":{"name":"echo","description":"Echo text", "parameters":{"type":"object","properties":{"text":{"type":"string"}}}}}],
      "tool_choice":"auto","chat_template_kwargs":{"enable_thinking":False},
      "max_tokens":16,"temperature":0}
request=urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions",
                               data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
with urllib.request.urlopen(request,timeout=300) as response:
    result=json.load(response)
print(json.dumps({"status":200,"usage":result.get("usage"),"finish_reason":result["choices"][0]["finish_reason"]}))
PY
    ;;
  down)
    docker stop "$CONTAINER"
    docker logs "$CONTAINER" > "$OUT/server.log" 2>&1
    docker inspect "$CONTAINER" --format '{{json .Config.Cmd}}' > "$OUT/server-argv.json"
    docker inspect "$CONTAINER" --format '{{json .State}}' > "$OUT/server-state.json"
    docker rm "$CONTAINER"
    ;;
  status)
    docker ps --filter "name=^/$CONTAINER$" --format '{{.ID}} {{.Image}} {{.Status}} {{.Ports}}'
    ;;
  *)
    echo 'Usage: serve-b0-tools.sh {up|smoke|down|status}' >&2
    exit 2
    ;;
esac

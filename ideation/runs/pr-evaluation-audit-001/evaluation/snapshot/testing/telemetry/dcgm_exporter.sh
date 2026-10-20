#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-start}"
CONTAINER_NAME="${DCGM_CONTAINER_NAME:-dsv41-dcgm-exporter}"
DCGM_EXPORTER_IMAGE="${DCGM_EXPORTER_IMAGE:-nvcr.io/nvidia/k8s/dcgm-exporter:4.4.1-4.5.2-ubuntu22.04}"
PORT="${DCGM_EXPORTER_PORT:-9400}"

case "$ACTION" in
  start)
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker run -d --rm \
      --name "$CONTAINER_NAME" \
      --gpus all \
      --cap-add SYS_ADMIN \
      --network host \
      -e DCGM_EXPORTER_LISTEN=":$PORT" \
      "$DCGM_EXPORTER_IMAGE"
    echo "DCGM metrics: http://127.0.0.1:$PORT/metrics"
    ;;
  stop)
    docker rm -f "$CONTAINER_NAME"
    ;;
  status)
    docker inspect --format '{{.State.Status}}' "$CONTAINER_NAME"
    ;;
  *)
    echo "Usage: $0 start|stop|status" >&2
    exit 2
    ;;
esac

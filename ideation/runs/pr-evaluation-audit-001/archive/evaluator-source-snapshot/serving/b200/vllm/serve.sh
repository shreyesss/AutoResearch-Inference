#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"
ensure_storage_dirs

exec "$ROOT/.venv/bin/python" "$ROOT/lib/serve_recipe.py" \
  --hardware b200 --engine vllm "$@"

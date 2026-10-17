#!/usr/bin/env bash
# Full ten-minute filtered Mooncake windows at their existing fixed timestamps.
set -u -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null || exit 1

for name in mooncake-median mooncake-burst mooncake-cache-heavy; do
  "$ROOT/.venv/bin/python" "$ROOT/infra/run-ops-production-b0.py" \
    --workload "$name" --cell "full-$name" --timeout 1800 || \
    echo "$name full fixed-schedule B0 failed; inspect its cell" >&2
done

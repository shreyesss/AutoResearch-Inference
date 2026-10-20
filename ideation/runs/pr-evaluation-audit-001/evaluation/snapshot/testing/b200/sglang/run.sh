#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
export HARDWARE="b200"
export ENGINE="sglang"

exec bash "$ROOT/testing/common/run.sh" "$@"

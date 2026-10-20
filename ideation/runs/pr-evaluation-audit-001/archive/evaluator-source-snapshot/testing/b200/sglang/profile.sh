#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
export HARDWARE="b200"
export ENGINE="sglang"

exec "${PROJECT_ROOT}/testing/common/profile.sh" "$@"

#!/usr/bin/env bash
# Compatibility entrypoint for the redesigned active campaign.
set -Eeuo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/run_active.sh" "$@"

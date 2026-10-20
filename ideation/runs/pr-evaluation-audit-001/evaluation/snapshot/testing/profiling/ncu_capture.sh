#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"
# shellcheck disable=SC1091
source "$ROOT/testing/profiling/require_clean.sh"

PROFILING_CONTAINER="${PROFILING_CONTAINER:?set an isolated profiling container}"
KERNEL_REGEX="${KERNEL_REGEX:?set KERNEL_REGEX after inspecting Nsight Systems}"
LAUNCH_SKIP="${LAUNCH_SKIP:-0}"
LAUNCH_COUNT="${LAUNCH_COUNT:-3}"
CAPTURE_NAME="${CAPTURE_NAME:-ncu-$(date +%Y%m%d-%H%M%S)}"
HOST_OUTPUT="$PROFILER_CACHE_ROOT/ncu/$CAPTURE_NAME"
CONTAINER_OUTPUT="/profiles/ncu/$CAPTURE_NAME"

if (($# == 0)); then
  echo "Pass an isolated one-batch/microbenchmark command after --." >&2
  exit 2
fi
if [[ "${1:-}" == -- ]]; then
  shift
fi

mkdir -p "$HOST_OUTPUT"
cp "$MANIFEST" "$HOST_OUTPUT/baseline-manifest.json"
printf '%q ' "$@" >"$HOST_OUTPUT/microbenchmark-command.txt"
printf '\n' >>"$HOST_OUTPUT/microbenchmark-command.txt"

echo "Nsight Compute replays kernels; these timings are never serving capacity."
echo "Pause DCGM profiling counter watches before continuing."

docker exec "$PROFILING_CONTAINER" \
  ncu \
  --target-processes all \
  --kernel-name "regex:$KERNEL_REGEX" \
  --launch-skip "$LAUNCH_SKIP" \
  --launch-count "$LAUNCH_COUNT" \
  --section SpeedOfLight \
  --section MemoryWorkloadAnalysis \
  --section LaunchStats \
  --section Occupancy \
  --export "$CONTAINER_OUTPUT/profile" \
  --force-overwrite \
  "$@"

cat >"$HOST_OUTPUT/profiling.json" <<EOF
{
  "instrumentation": "nsight-compute",
  "capacity_publishable": false,
  "kernel_regex": $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$KERNEL_REGEX"),
  "launch_skip": $LAUNCH_SKIP,
  "launch_count": $LAUNCH_COUNT,
  "report": "profile.ncu-rep"
}
EOF

echo "Nsight Compute artifacts: $HOST_OUTPUT"

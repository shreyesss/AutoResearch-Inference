#!/usr/bin/env bash
# Ordered active campaign. Execution of all configs requires --execute-all.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN=0
EXECUTE_ALL=0
ONLY=""
FORWARD=()
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --execute-all) EXECUTE_ALL=1; shift ;;
    --only) ONLY="${2:?missing comma-separated IDs}"; shift 2 ;;
    --no-sync) FORWARD+=(--no-sync); shift ;;
    --requests) FORWARD+=("$1" "${2:?missing requests}"); shift 2 ;;
    -h|--help)
      cat <<EOF
Usage:
  $(basename "$0") --plan
  $(basename "$0") --only ID[,ID...] [--no-sync]
  $(basename "$0") --execute-all [--no-sync]

Independent configuration scripts are preferred so results can be inspected
between model loads.
EOF
      exit 0
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

IDS=(
  LAT-00
  LAT-PD-SMOKE
  LAT-TP4-BALANCED
  LAT-TP4-LOW
  LAT-TP4-HYBRID
  LAT-PD-BASELINE
  LAT-PD-PREFILL16K
  LAT-PD-DECODE64
)
scripts=(
  run_import_evidence.sh
  run_pd_smoke.sh
  run_tp4_balanced.sh
  run_tp4_low_latency.sh
  run_tp4_hybrid.sh
  run_pd_baseline.sh
  run_pd_prefill16k.sh
  run_pd_decode64.sh
)

if ((PLAN == 0 && EXECUTE_ALL == 0)) && [[ -z "$ONLY" ]]; then
  echo "Refusing implicit full execution; use --plan, --only, or --execute-all." >&2
  exit 2
fi

selected=0
pd_available=1
for index in "${!IDS[@]}"; do
  id="${IDS[$index]}"
  if [[ -n "$ONLY" ]]; then
    case ",$ONLY," in
      *",$id,"*) ;;
      *) continue ;;
    esac
  fi
  selected=$((selected + 1))
  command=("$SCRIPT_DIR/${scripts[$index]}")
  ((PLAN)) && command+=(--plan)
  if ((EXECUTE_ALL && PLAN == 0)) &&
     [[ "$id" == LAT-TP4-* || "$id" == LAT-PD-BASELINE ||
        "$id" == LAT-PD-PREFILL16K || "$id" == LAT-PD-DECODE64 ]]; then
    command+=(--resume)
  fi
  command+=("${FORWARD[@]}")
  if ((PLAN == 0)) && [[ "$id" == LAT-PD-* && "$id" != LAT-PD-SMOKE ]] &&
     ((pd_available == 0)); then
    echo "Skipping $id because PD smoke did not pass." >&2
    continue
  fi
  if ! "${command[@]}"; then
    if ((EXECUTE_ALL)) && [[ "$id" == LAT-PD-SMOKE ]]; then
      pd_available=0
      echo "PD smoke failed; continuing TP4 and skipping PD configs." >&2
      continue
    fi
    exit 1
  fi
done
((selected > 0)) || {
  echo "no active experiments matched --only" >&2
  exit 2
}
if ((PLAN)); then
  "$SCRIPT_DIR/estimate_runtime.py" \
    --campaign "$SCRIPT_DIR/campaign.yaml"
fi

#!/bin/bash
set -euo pipefail

source_dir="/Users/shreyas/workspace/skunk-work"
remote="sofia-gpu-mumbai:/home/ubuntu/skunk-work/"

if [[ ! -f "$source_dir/IMPLEMENTATION.md" || ! -d "$source_dir/inference-autoresearch-handoff" ]]; then
  echo "skunk-work source directory is missing or incomplete: $source_dir" >&2
  exit 1
fi

rsync -az --delete --timeout=45 \
  --exclude='.git/' \
  --exclude='.DS_Store' \
  -e 'ssh -o BatchMode=yes -o ConnectTimeout=15' \
  "$source_dir/" "$remote"

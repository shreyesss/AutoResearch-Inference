#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="$ROOT/.artifacts/models/Qwen3.8-27B"
CACHE="$ROOT/.artifacts/aiperf-hf-cache"
REVISION=1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
SNAPSHOT="$CACHE/models--Qwen--Qwen3.8-27B/snapshots/$REVISION"

test -f "$MODEL/tokenizer.json"
ACTUAL="$(sha256sum "$MODEL/tokenizer.json" | cut -d' ' -f1)"
EXPECTED=0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "Pinned Qwen tokenizer hash mismatch: $ACTUAL" >&2
  exit 1
fi

mkdir -p "$(dirname "$SNAPSHOT")"
if [[ -L "$SNAPSHOT" ]]; then
  test "$(readlink -f "$SNAPSHOT")" = "$MODEL" || {
    echo "Tokenizer cache snapshot points to a different model: $SNAPSHOT" >&2
    exit 1
  }
elif [[ -e "$SNAPSHOT" ]]; then
  echo "Tokenizer cache snapshot exists and is not our symlink: $SNAPSHOT" >&2
  exit 1
else
  ln -s "$MODEL" "$SNAPSHOT"
fi
printf '%s\n' "$CACHE"

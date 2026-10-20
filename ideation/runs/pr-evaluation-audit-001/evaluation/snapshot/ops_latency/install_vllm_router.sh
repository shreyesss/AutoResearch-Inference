#!/usr/bin/env bash
# Build the native vLLM router at the campaign-pinned revision.

set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../lib/env.sh
source "$ROOT/lib/env.sh"

ROUTER_REPO="${VLLM_ROUTER_REPO:-https://github.com/vllm-project/router.git}"
ROUTER_COMMIT="${VLLM_ROUTER_COMMIT:-37b37a43c577cd7d83bad7b10b8b4650325b4fc7}"
INSTALL_ROOT="${VLLM_ROUTER_INSTALL_ROOT:-$MODEL_STORAGE_ROOT/tools/vllm-router}"
SOURCE_ROOT="$INSTALL_ROOT/source"
BIN="$INSTALL_ROOT/bin/vllm-router"
MIN_CARGO_VERSION="${VLLM_ROUTER_MIN_CARGO_VERSION:-1.83.0}"

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

# Prefer rustup's user-local toolchain even in non-interactive shells, where
# ~/.cargo/bin may not have been added to PATH yet.
if [[ -x "$HOME/.cargo/bin/cargo" ]]; then
  export PATH="$HOME/.cargo/bin:$PATH"
fi

cargo_is_recent_enough() {
  local installed
  command -v cargo >/dev/null 2>&1 || return 1
  installed="$(cargo --version | awk '{print $2}')"
  [[ "$(printf '%s\n%s\n' "$MIN_CARGO_VERSION" "$installed" | sort -V | head -n1)" == \
     "$MIN_CARGO_VERSION" ]]
}

if ! cargo_is_recent_enough; then
  command -v curl >/dev/null || {
    echo "curl is required to install a current Rust toolchain" >&2
    exit 1
  }
  if ! command -v rustup >/dev/null 2>&1; then
    echo "Installing rustup because Cargo $MIN_CARGO_VERSION or newer is required."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs |
      sh -s -- -y --profile minimal
    export PATH="$HOME/.cargo/bin:$PATH"
  fi
  rustup toolchain install stable --profile minimal
  rustup default stable
fi

cargo_is_recent_enough || {
  echo "Cargo $MIN_CARGO_VERSION or newer is required (found $(cargo --version 2>/dev/null || echo none))." >&2
  exit 1
}

if [[ -x "$BIN" && -f "$INSTALL_ROOT/COMMIT" &&
      "$(<"$INSTALL_ROOT/COMMIT")" == "$ROUTER_COMMIT" ]]; then
  echo "vllm-router already installed: $BIN"
  exit 0
fi
mkdir -p "$INSTALL_ROOT"
if [[ ! -d "$SOURCE_ROOT/.git" ]]; then
  git clone "$ROUTER_REPO" "$SOURCE_ROOT"
fi
if ! git -C "$SOURCE_ROOT" fetch --depth 1 origin "$ROUTER_COMMIT"; then
  git -C "$SOURCE_ROOT" fetch origin main --tags
fi
git -C "$SOURCE_ROOT" cat-file -e "$ROUTER_COMMIT^{commit}"
git -C "$SOURCE_ROOT" checkout --detach "$ROUTER_COMMIT"
cargo build --release --manifest-path "$SOURCE_ROOT/Cargo.toml"
mkdir -p "$INSTALL_ROOT/bin"
install -m 0755 "$SOURCE_ROOT/target/release/vllm-router" "$BIN"
printf '%s\n' "$ROUTER_COMMIT" >"$INSTALL_ROOT/COMMIT"
"$BIN" --version

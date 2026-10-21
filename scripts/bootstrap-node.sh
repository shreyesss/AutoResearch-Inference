#!/usr/bin/env bash
# Install CPU-side research tools. Does not launch models, benchmarks, or agents.
set -euo pipefail

source_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
state_root="${AUTORESEARCH_STATE_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/inference-autoresearch}"
venv_root="${XDG_DATA_HOME:-$HOME/.local/share}/autoresearch/venv"
bitlane_repo=""
bitlane_dir="$(dirname "$source_root")/bitlane"
bitlane_ref=""
python_bin=""
research_extras=0
agents=0
storage=0
mcp=0
dry_run=0

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap-node.sh [options]
  --state-root DIR       Durable local state, outside both code checkouts
  --venv-root DIR        CPU research virtualenv, outside both code checkouts
  --python PATH          Python 3.11+ (3.12+ for --research-extras)
  --research-extras      Install optional web-research dependencies
  --agents              Install pinned DiscoveryRSI agent dependency
  --storage             Install optional S3 client dependency
  --mcp                 Install optional stdio research MCP server
  --bitlane-repo URL     Explicit canonical Bitlane Git URL; never guessed
  --bitlane-dir DIR      Separate Bitlane checkout (default: sibling bitlane)
  --bitlane-ref REF      Optional branch/tag/commit for a NEW checkout
  --dry-run             Validate paths and print actions without changing files
  --help

Start with a clone of AutoResearch-Inference and run this script there.
An existing Bitlane checkout is preserved; this script never pulls or resets it.
Use your existing SSH agent/credential helper; never put tokens in Git URLs.
EOF
}

while (($#)); do
  case "$1" in
    --state-root|--venv-root|--python|--bitlane-repo|--bitlane-dir|--bitlane-ref)
      (($# >= 2)) && [[ -n "$2" ]] || { echo "Missing value for $1" >&2; exit 2; }
      case "$1" in
        --state-root) state_root="$2";;
        --venv-root) venv_root="$2";;
        --python) python_bin="$2";;
        --bitlane-repo) bitlane_repo="$2";;
        --bitlane-dir) bitlane_dir="$2";;
        --bitlane-ref) bitlane_ref="$2";;
      esac
      shift 2;;
    --research-extras) research_extras=1; shift;;
    --agents) agents=1; shift;;
    --storage) storage=1; shift;;
    --mcp) mcp=1; shift;;
    --dry-run) dry_run=1; shift;;
    --help|-h) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2;;
  esac
done

if [[ -z "$python_bin" ]]; then
  for candidate in python3.13 python3.12 python3.11 "$HOME/.local/bin/python3.12" python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3,11))'; then
      python_bin="$candidate"
      break
    fi
  done
fi
[[ -n "$python_bin" ]] || { echo "Install Python 3.11+ or pass --python PATH." >&2; exit 2; }
"$python_bin" - "$research_extras" <<'PY'
import sys
minimum = (3, 12) if sys.argv[1] == "1" else (3, 11)
if sys.version_info < minimum:
    raise SystemExit("Python %s.%s+ required for selected dependencies" % minimum)
PY

# Resolve symlinks as well as '..'; code, research state and environments are separate.
"$python_bin" - "$source_root" "$state_root" "$venv_root" "$bitlane_dir" "$bitlane_repo" <<'PY'
import sys
from pathlib import Path
from urllib.parse import urlsplit
source, state, venv, bitlane = [Path(s).expanduser().resolve() for s in sys.argv[1:5]]
for left, right, message in (
    (state, source, "State must be outside the research checkout"),
    (venv, source, "Virtualenv must be outside the research checkout"),
    (bitlane, source, "Bitlane must have a separate code checkout"),
    (state, bitlane, "State must be outside the Bitlane checkout"),
    (venv, bitlane, "Virtualenv must be outside the Bitlane checkout"),
    (state, venv, "State and virtualenv must use separate directories"),
):
    if left == right or left in right.parents or right in left.parents:
        raise SystemExit(message)
url = sys.argv[5]
if url.startswith("-") or "\n" in url or "\r" in url:
    raise SystemExit("Invalid Git URL")
parsed = urlsplit(url)
if parsed.scheme in ("http", "https") and (parsed.username or parsed.password or parsed.query):
    raise SystemExit("Use SSH or a credential helper; credentials must not appear in Git URL")
PY

if [[ "$bitlane_ref" == -* || "$bitlane_ref" == *$'\n'* ]]; then
  echo "Invalid Bitlane ref" >&2; exit 2
fi

for path_name in state_root venv_root bitlane_dir; do
  normalized_path="$("$python_bin" -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "${!path_name}")"
  printf -v "$path_name" '%s' "$normalized_path"
done

if [[ -n "$bitlane_repo" && -e "$bitlane_dir" ]]; then
  [[ -d "$bitlane_dir/.git" ]] || { echo "Existing Bitlane directory is not a Git checkout" >&2; exit 2; }
  existing_remote="$(git -C "$bitlane_dir" remote get-url origin)"
  [[ "$existing_remote" == "$bitlane_repo" ]] || { echo "Existing Bitlane origin differs; choose the matching URL or a new directory" >&2; exit 2; }
  if [[ -n "$bitlane_ref" ]]; then
    requested_commit="$(git -C "$bitlane_dir" rev-parse --verify "${bitlane_ref}^{commit}")"
    actual_commit="$(git -C "$bitlane_dir" rev-parse HEAD)"
    [[ "$requested_commit" == "$actual_commit" ]] || { echo "Existing Bitlane checkout has a different revision; update it explicitly" >&2; exit 2; }
  fi
fi

if ((dry_run)); then
  printf 'Research code: %s\nState root: %s\nVirtualenv: %s\nPython: %s\n' "$source_root" "$state_root" "$venv_root" "$python_bin"
  if [[ -n "$bitlane_repo" ]]; then printf 'Bitlane checkout: %s (explicit repository supplied)\n' "$bitlane_dir"; fi
  printf 'Optional research dependencies: %s\nNo changes made.\n' "$research_extras"
  exit 0
fi

mkdir -p "$state_root" "$(dirname "$venv_root")"
if [[ ! -x "$venv_root/bin/python" ]]; then
  "$python_bin" -m venv "$venv_root"
fi
"$venv_root/bin/python" - "$research_extras" <<'PY'
import sys
minimum = (3,12) if sys.argv[1] == "1" else (3,11)
if sys.version_info < minimum:
    raise SystemExit("Existing virtualenv Python is too old; choose a new --venv-root")
PY
package="$source_root/ideation"
extras=""
if ((research_extras)); then extras="web-research"; fi
if ((agents)); then extras="${extras:+$extras,}agents"; fi
if ((storage)); then extras="${extras:+$extras,}storage"; fi
if ((mcp)); then extras="${extras:+$extras,}mcp"; fi
if [[ -n "$extras" ]]; then package="${package}[$extras]"; fi
"$venv_root/bin/python" -m pip install --disable-pip-version-check -e "$package"

if [[ -n "$bitlane_repo" && ! -e "$bitlane_dir" ]]; then
  mkdir -p "$(dirname "$bitlane_dir")"
  git clone -- "$bitlane_repo" "$bitlane_dir"
  if [[ -n "$bitlane_ref" ]]; then
    git -C "$bitlane_dir" checkout --detach "$bitlane_ref"
  fi
fi

printf '\nResearch environment ready.\n'
printf 'Activate: source %q/bin/activate\n' "$venv_root"
printf 'State: export AUTORESEARCH_STATE_ROOT=%q\n' "$state_root"
printf 'Research checkout: %s\n' "$source_root"
printf 'Command: researchctl --help\n'
if [[ -n "$bitlane_repo" ]]; then printf 'Bitlane checkout: %s (serving installation remains separate)\n' "$bitlane_dir"; fi
printf 'No cloud resources, GPU services, or scheduled jobs were started.\n'

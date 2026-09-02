#!/usr/bin/env bash
# Point the Cursor and Claude Code skill directories at this checkout.
#
#   <checkout>/{governance-system,plan-waves-slices,spec-chain}
#     -> ~/.cursor/skills/<skill>     symlink
#     -> ~/.claude/skills/<skill>     symlink
#
# The three packages must stay siblings: governancectl locates the spec-chain and plan
# validators relative to its own resolved path. With --runtime the host directories
# symlink through a stable intermediate path instead, so moving the checkout later needs
# only one symlink repointed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS=(governance-system plan-waves-slices spec-chain)
HOSTS=("$HOME/.cursor/skills" "$HOME/.claude/skills")
RUNTIME=""
DRY=0

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--runtime PATH] [--dry-run] [--help]

  --runtime PATH  Create PATH as a symlink to this checkout and point the host
                  directories through it (e.g. --runtime ~/.local/share/agent-skills).
  --dry-run       Print what would change without writing.
  --help          Show this message.

With no flags the host skill directories symlink directly at this checkout.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runtime) [[ $# -ge 2 ]] || { echo "--runtime needs a path" >&2; exit 2; }; RUNTIME="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

run() { if [[ $DRY -eq 1 ]]; then echo "[dry-run] $*"; else "$@"; fi; }

for skill in "${SKILLS[@]}"; do
  [[ -f "$REPO_ROOT/$skill/SKILL.md" ]] || { echo "incomplete checkout: $skill/SKILL.md missing" >&2; exit 2; }
done

source="$REPO_ROOT"
if [[ -n "$RUNTIME" ]]; then
  RUNTIME="${RUNTIME/#\~/$HOME}"
  if [[ -e "$RUNTIME" && ! -L "$RUNTIME" ]]; then
    echo "runtime path exists and is not a symlink: $RUNTIME" >&2
    echo "Move it aside first, then re-run." >&2
    exit 4
  fi
  run mkdir -p "$(dirname "$RUNTIME")"
  run ln -sfn "$REPO_ROOT" "$RUNTIME"
  source="$RUNTIME"
fi

for host in "${HOSTS[@]}"; do
  run mkdir -p "$host"
  for skill in "${SKILLS[@]}"; do
    run ln -sfn "$source/$skill" "$host/$skill"
  done
done

if [[ ! -d "$REPO_ROOT/spec-chain/node_modules" ]]; then
  echo "note: spec-chain/node_modules absent; run (cd $REPO_ROOT/spec-chain && npm ci) for the DOCX renderer"
fi

echo "installed: ${HOSTS[*]} -> $source"
if [[ $DRY -eq 0 ]]; then
  echo "verifying:"
  python3 "$REPO_ROOT/governance-system/scripts/validate_suite.py" --root "$REPO_ROOT" --check-symlinks
fi

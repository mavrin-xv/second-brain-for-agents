#!/usr/bin/env bash
# second-brain-for-agents installer: copies the seven skills into Claude Code.
#
#   ./install.sh                     into ~/.claude/skills (all projects)
#   ./install.sh --project           into ./.claude/skills (this project only)
#   ./install.sh --vault ~/notes/v   also create a vault there (safe on an existing one)
#
# Existing skills with the same name are backed up to <name>.bak.<timestamp> first.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude"; VAULT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project) DEST="$(pwd)/.claude" ;;
    --vault) shift; VAULT="${1:-}"; [ -n "$VAULT" ] || { echo "--vault needs a folder" >&2; exit 1; } ;;
    -h|--help) sed -n 2,8p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

say()  { printf '\033[1m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31mxx\033[0m %s\n' "$*" >&2; exit 1; }

PY=""
for c in python3 python py; do   # first one that really runs (Windows ships a python3 stub)
  if command -v "$c" >/dev/null && "$c" -c "import sys; sys.exit(sys.version_info < (3, 8))" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || warn "No Python 3.8+ found. The skills still work by hand; the helper scripts need Python."

mkdir -p "$DEST/skills"
for s in "$HERE"/skills/*/; do
  name="$(basename "$s")"
  if [ -d "$DEST/skills/$name" ]; then
    mv "$DEST/skills/$name" "$DEST/skills/$name.bak.$(date +%s)"
    warn "backed up existing $name"
  fi
  cp -R "$s" "$DEST/skills/$name"
  find "$DEST/skills/$name" -name __pycache__ -type d -prune -exec rm -r {} + 2>/dev/null || true
  say "installed skill $name"
done
cp "$HERE/templates/nightly.sh" "$DEST/skills/dreaming/nightly.sh"

if [ -n "$VAULT" ]; then
  [ -n "$PY" ] || die "Creating a vault needs Python 3.8+."
  "$PY" "$DEST/skills/vault-setup/scripts/init_vault.py" --vault "$VAULT"
fi

command -v qmd >/dev/null || say "optional: npm install -g @tobilu/qmd   (better search; the built-in ranker works without it)"
say "done. Try: \"set up a vault in ~/notes/vault\", then \"save this: <a link>\"."

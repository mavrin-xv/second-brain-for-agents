#!/usr/bin/env bash
# Nightly vault job: graph, health, ingest queue, dreaming scan. Writes only GRAPH.md,
# backlink footers, files in proposals/ and log lines. Never edits what a note says.
#
#   VAULT_DIR=~/notes/vault ./nightly.sh
#   PACK=./skills VAULT_DIR=./vault ./nightly.sh     # run from a clone of this repo
set -u
PACK="${PACK:-$HOME/.claude/skills}"
VAULT_DIR="${VAULT_DIR:?set VAULT_DIR to your vault folder}"
export VAULT_DIR
PY=""
for c in python3 python py; do   # first one that really runs (Windows ships a python3 stub)
  if command -v "$c" >/dev/null && "$c" -c "import sys; sys.exit(sys.version_info < (3, 8))" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "nightly: no Python 3.8+ found" >&2; exit 1; }
DAY="$(date +%F)"
REPORT="$VAULT_DIR/proposals/health-$DAY.txt"
mkdir -p "$VAULT_DIR/proposals"
fail=0

if command -v qmd >/dev/null; then
  { qmd update && qmd embed; } >/dev/null 2>&1 || { echo "qmd index update failed" >> "$REPORT"; fail=1; }
fi
"$PY" "$PACK/knowledge-graph/scripts/build_graph.py" --footers || { echo "graph step failed" >> "$REPORT"; fail=1; }
"$PY" "$PACK/vault-health/scripts/vault_health.py" >> "$REPORT" || { echo "health step failed" >> "$REPORT"; fail=1; }
"$PY" "$PACK/wiki-ingest/scripts/ingest_queue.py" --stale-days 3 >> "$REPORT" || true
"$PY" "$PACK/dreaming/scripts/dream_digest.py" scan --days 1 || { echo "dream scan failed" >> "$REPORT"; fail=1; }

[ "$fail" = 0 ] || echo "nightly: one or more steps failed, see $REPORT" >&2
exit "$fail"

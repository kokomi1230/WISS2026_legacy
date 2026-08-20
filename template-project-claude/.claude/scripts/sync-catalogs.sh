#!/usr/bin/env bash
# Regenerate docs/CATALOG.html from docs/CATALOG.md (unified catalog for plugins,
# skills, subagents, etc).
# Idempotent; safe to run after manual edits or when hooks may have missed updates.

set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_bootstrap.sh"
# build_catalog.py はテンプレート自身の資産なので REPO_ROOT 側に在る。対象データの
# 場所は build_catalog.py が CLAUDE_PROJECT_DIR を見て自分で決める。
cd "$REPO_ROOT"

if [ -z "$PYTHON_CMD" ]; then
  echo "sync-catalogs: no working Python 3.7+ interpreter found (python3/python/py -3)" >&2
  exit 127
fi

QUIET=""
CHECK=""
for arg in "$@"; do
  case "$arg" in
    --quiet) QUIET="--quiet" ;;
    --check) CHECK="--check" ;;
  esac
done

rc=0
# $PYTHON_CMD is deliberately unquoted: it may be a two-word command ("py -3").
$PYTHON_CMD .claude/scripts/build_catalog.py $QUIET $CHECK || rc=$?

# Clean up any stale lock file
rm -f .claude/.catalog-sync-lock

exit $rc

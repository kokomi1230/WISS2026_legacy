#!/usr/bin/env bash
# PostToolUse hook: regenerate docs/CATALOG.html when the source MD or
# enabled-plugin state changes. CATALOG.md is the unified catalog for
# plugins, skills, subagents, etc.
# Self-recursion is prevented by .claude/.catalog-sync-lock (the build script touches it).

set -uo pipefail

# A hook must never block the user's tool call, so a missing or broken
# bootstrap exits quietly instead of erroring.
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)/_bootstrap.sh" 2>/dev/null || exit 0
# hook は「編集中のプロジェクト」に対して動くので PROJECT_ROOT を使う。
# build_catalog.py 自身は REPO_ROOT 側から起動する（通常この 2 つは一致する）。
ROOT="$PROJECT_ROOT"
[ -z "$PYTHON_CMD" ] && exit 0

# Read tool_input.file_path from stdin (suppress errors if JSON is malformed)
FILE=$($PYTHON_CMD -c "import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass" 2>/dev/null || true)

# Early exit if no file path
[ -z "$FILE" ] && exit 0

# Skip during build scripts' own writes (self-recursion guard)
[ -e "$ROOT/.claude/.catalog-sync-lock" ] && exit 0

case "$FILE" in
  */CATALOG.md|*/.claude/settings.json)
    # cd してから相対パスで起動する: native Windows Python は Git Bash の
    # /c/... 形式を解決できないが、相対パスなら CWD 経由で解決される。
    (cd "$REPO_ROOT" && $PYTHON_CMD .claude/scripts/build_catalog.py --quiet) \
      2>>"$ROOT/.claude/.catalog-sync.log"
    ;;
esac

# Always exit 0 - never block the user's tool call on hook failures
exit 0

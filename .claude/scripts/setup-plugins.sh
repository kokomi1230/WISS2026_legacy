#!/usr/bin/env bash
# Install all Claude Code plugins at USER scope on a fresh machine, idempotently.
#
# Model (see docs/PLUGIN_INSTALL_SCOPE.md):
#   - install layer (user scope): every plugin (incl. OAuth ones like slack) is
#     installed once per machine.
#       * core  -> installed AND enabled at user scope (default-on everywhere)
#       * extra -> installed at user scope but disabled (each project enables as needed)
#   - per-project ON/OFF is done via project enabledPlugins (true/false); a project
#     `false` disables a user-enabled plugin AND its bundled MCP server for that project.
#   - OAuth plugins are fine at user scope: auth is machine-global and the enable flag
#     holds no secret. Only secrets (API keys/tokens) stay in .env / settings.local.json.
#   - raw MCP servers (unity/figma) are NOT handled here; they cannot be disabled
#     per-project at user scope, so they live in .mcp.json + enabledMcpjsonServers.
#
# Source of truth: .claude/plugins-user-scope.json (marketplaces / core / extra / auth).
#
# Usage:
#   bash .claude/scripts/setup-plugins.sh          # apply (install + enable/disable)
#   bash .claude/scripts/setup-plugins.sh --check   # dry-run: print the commands only
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_bootstrap.sh"
# マニフェストはテンプレート自身の資産。CLAUDE_PROJECT_DIR ではなく REPO_ROOT を
# 使う。cd してから相対パスで扱うのは、native Windows Python が Git Bash の
# /c/... 形式を解決できないため。
cd "$REPO_ROOT"
MANIFEST=".claude/plugins-user-scope.json"
DRY_RUN=0
[[ "${1:-}" == "--check" || "${1:-}" == "--dry-run" ]] && DRY_RUN=1
export DRY_RUN  # _bootstrap.sh の run() が参照する

if ! command -v claude >/dev/null 2>&1; then
  echo "error: 'claude' CLI not found on PATH" >&2
  exit 1
fi
if [[ ! -f "$MANIFEST" ]]; then
  echo "error: manifest not found: $MANIFEST" >&2
  exit 1
fi
if [[ -z "$PYTHON_CMD" ]]; then
  echo "error: no working Python 3.7+ interpreter found (python3/python/py -3)" >&2
  exit 1
fi

# Read JSON arrays/objects via Python (no jq dependency).
# The path and key go through argv, never through the Python source text: a path
# containing a backslash (C:\Users\... on Windows) or a single quote would otherwise
# be parsed as a string escape and raise SyntaxError.
# encoding='utf-8' is required: on Windows, Python's open() defaults to the
# system codepage (e.g. cp932), which cannot decode the manifest's Japanese comments.
# tr -d '\r' is required: native Windows Python's print() emits CRLF, and a
# trailing \r surviving into `read -r` silently corrupts the plugin/marketplace
# name (e.g. "foo\r"), making every subsequent `claude plugin ...` call fail
# with a confusing "not found in marketplace" error.
# $PYTHON_CMD is deliberately unquoted below: it may be a two-word command ("py -3").
read_list() {
  $PYTHON_CMD -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]]))' \
    "$MANIFEST" "$1" | tr -d '\r'
}
read_markets() {
  $PYTHON_CMD -c 'import json,sys; [print(k, v) for k, v in json.load(open(sys.argv[1], encoding="utf-8"))["marketplaces"].items()]' \
    "$MANIFEST" | tr -d '\r'
}

echo "== 1. marketplaces (user scope) =="
while read -r name repo; do
  [[ -z "$name" ]] && continue
  run claude plugin marketplace add "$repo" --scope user
  # 'add' on an already-registered marketplace is a no-op, so force a refresh
  # here too; otherwise a stale local cache makes every install below fail
  # with "not found in marketplace".
  run claude plugin marketplace update "$name"
done < <(read_markets)

echo "== 2. install core + extra (user scope) =="
while read -r p; do [[ -z "$p" ]] && continue; run claude plugin install "$p" --scope user; done < <(read_list core)
while read -r p; do [[ -z "$p" ]] && continue; run claude plugin install "$p" --scope user; done < <(read_list extra)

echo "== 3. enable core, disable extra (user scope) =="
while read -r p; do [[ -z "$p" ]] && continue; run claude plugin enable  "$p" --scope user; done < <(read_list core)
while read -r p; do [[ -z "$p" ]] && continue; run claude plugin disable "$p" --scope user; done < <(read_list extra)

echo
echo "Done. All plugins (incl. OAuth ones like slack) are installed at user scope."
echo "OAuth auth happens on first use (once per machine). Enable extras per project"
echo "via /init-project. Raw MCP servers (unity/figma) are handled via .mcp.json."

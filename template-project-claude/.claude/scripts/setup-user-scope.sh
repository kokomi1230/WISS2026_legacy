#!/usr/bin/env bash
# Deploy this repository's user-scope/ assets into the Claude Code config dir.
#
# Model (see docs/PLUGIN_INSTALL_SCOPE.md):
#   - user-scope/ in THIS repository is the single source of truth for assets that
#     every project uses (proofreading agents, writing-style skills, /swap-punctuation,
#     /cost-report, /notion-sync, statusline.sh).
#   - The config dir (~/.claude, or %USERPROFILE%\.claude on Windows) is a derived
#     artifact. Sync is one-way; nothing is ever read back from it.
#   - Plugins are a separate layer handled by setup-plugins.sh. This script never
#     touches enabledPlugins / extraKnownMarketplaces.
#   - Secrets stay in <config-dir>/.env and settings.local.json, which this script
#     neither reads nor writes.
#
# Usage:
#   bash .claude/scripts/setup-user-scope.sh           # deploy (copy, idempotent)
#   bash .claude/scripts/setup-user-scope.sh --check    # dry-run: print planned actions
#   bash .claude/scripts/setup-user-scope.sh --diff     # drift only; exit 2 when drift
#   bash .claude/scripts/setup-user-scope.sh --link     # symlink instead of copy (non-Windows)
#
# --link is for the maintainer's canonical checkout only: edits in the config dir then
# land straight in the repository. It is wrong for the per-project copies made with
# `cp -r`, because deleting that copy would break the user scope machine-wide.
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_bootstrap.sh"
# 資産はテンプレート自身の中にある。CLAUDE_PROJECT_DIR（編集中のプロジェクト）で
# はなく REPO_ROOT を使う。cd してから相対パスで渡すのは、native Windows Python が
# Git Bash の /c/... 形式を解決できないため（相対パスなら CWD 経由で解決される）。
cd "$REPO_ROOT"
SOURCE_DIR="user-scope"
ENGINE=".claude/scripts/user_scope_sync.py"

MODE="apply"
LINK_FLAG=""
for arg in "$@"; do
  case "$arg" in
    --check|--dry-run) MODE="check" ;;
    --diff)            MODE="diff" ;;
    --link)            LINK_FLAG="--link" ;;
    # 冒頭のコメントブロックだけを出す。行番号を直書きするとコメントを足すたびに
    # ずれるため、「# で始まらない行が来たら終わり」で判定する。
    -h|--help)         awk 'NR>1 { if (!/^#/) exit; print }' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "error: unknown option: $arg" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "error: source not found: $SOURCE_DIR" >&2
  exit 1
fi
if [[ ! -f "$ENGINE" ]]; then
  echo "error: engine not found: $ENGINE" >&2
  exit 1
fi

if [[ -z "$PYTHON_CMD" ]]; then
  echo "error: no working Python 3.7+ interpreter found (python3/python/py -3)" >&2
  exit 1
fi

# $PYTHON_CMD is deliberately unquoted: it may be a two-word command ("py -3").
exec $PYTHON_CMD "$ENGINE" "$MODE" --source "$SOURCE_DIR" $LINK_FLAG

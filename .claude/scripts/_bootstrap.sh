#!/usr/bin/env bash
# Shared bootstrap for every shell entry point in this template.
# Source it; do not execute it:
#
#   . "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_bootstrap.sh"
#
# After sourcing you have:
#   PYTHON_CMD    a working Python 3.7+ command (may be two words: "py -3")
#   REPO_ROOT     this template's own root, always derived from this file's location
#   PROJECT_ROOT  the project being acted on: $CLAUDE_PROJECT_DIR, else REPO_ROOT
#   run()         echo-and-execute wrapper honouring DRY_RUN=1
#
# REPO_ROOT vs PROJECT_ROOT is not a stylistic choice. A hook runs against whatever
# project the user is editing ($CLAUDE_PROJECT_DIR), but the template's own assets
# (scripts, manifest, user-scope/) always live next to this file. Resolving assets
# through CLAUDE_PROJECT_DIR makes every setup script fail the moment it is invoked
# from a different project. Use REPO_ROOT for assets, PROJECT_ROOT for target data.
#
# Callers that must never fail (PostToolUse hooks) should guard the source:
#   . "$ROOT/.claude/scripts/_bootstrap.sh" 2>/dev/null || exit 0

# --- パス解決 ---------------------------------------------------------------
# POSIX 形式（Git Bash なら /c/Users/...）で統一する。native Windows パスを
# 使わないのは、`cd` がバックスラッシュ路径を確実に扱えないため。native な
# Windows プロセス（python）へパスを渡すときは、絶対パスではなく
# 「cd 済みディレクトリからの相対パス」を渡すこと。相対パスなら CWD 経由で
# 解決されるため、POSIX/native の変換自体が不要になる。
_abspath() { (cd "$1" && pwd); }

# 本ファイルは常に <repo>/.claude/scripts/ に在る。
REPO_ROOT="$(_abspath "$(dirname "${BASH_SOURCE[0]}")/../..")"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"

# --- Python の探索 ----------------------------------------------------------
# バージョン下限が要る理由: 本テンプレートの Python はすべて
# `from __future__ import annotations` を使うため 3.7+ が要る。単に「起動するか」
# だけを見ると、PATH の先に居る古い 3.6 が合格してしまい、あとで SyntaxError で
# 落ちる。また Windows では python3 が Microsoft Store の
# app-execution-alias スタブ（"Python" と表示して非ゼロ終了する）へ解決される
# ことがあり、実体は python / py -3 側にある。
find_python() {
  local candidate
  for candidate in "python3" "python" "py -3"; do
    if $candidate -c "import sys; assert sys.version_info >= (3, 7)" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_CMD="$(find_python || true)"

# 非対話 Python は Windows でシステムコードページ（cp932 等）を既定にするため、
# 本テンプレートが出す日本語メッセージが化ける。UTF-8 を明示する。
export PYTHONIOENCODING=utf-8

# --- 実行ヘルパー -----------------------------------------------------------
# DRY_RUN=1 のとき実行せず表示だけする。失敗しても止めないのは、導入スクリプトが
# 「適用済みで冪等に失敗する」ケースを正常系として扱うため。
run() {
  if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "  [dry-run] $*"
  else
    echo "  + $*"
    "$@" || echo "    (skip: command failed or already applied)"
  fi
}

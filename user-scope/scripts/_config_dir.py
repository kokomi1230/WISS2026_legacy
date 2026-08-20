r"""Claude Code の設定ディレクトリを解決する。user-scope 配下のスクリプト共通。

`.claude/scripts/user_scope_sync.py` と同じ規則を持つが、実装を共有していない。
user-scope 資産は配置先（`~/.claude/scripts/`）で単独動作する必要があり、そこから
テンプレートリポジトリの `.claude/scripts/` を import できないためである。規則を
変えるときは両方を直すこと。

解決順:
  1. CLAUDE_CONFIG_DIR（ハーネスの規約。隔離環境での検証にも使う）
  2. Windows なら %USERPROFILE%\.claude
  3. $HOME/.claude
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_windows() -> bool:
    """Git Bash から native Python が呼ばれる場合も Windows とみなす。"""
    return os.name == "nt" or sys.platform in ("win32", "msys", "cygwin")


def config_dir() -> Path:
    """設定ディレクトリ。

    Windows で Path.home() を使わないのは、Git Bash 上の MSYS Python では HOME が
    %USERPROFILE% と一致しないことがあるため。
    """
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    if is_windows():
        profile = os.environ.get("USERPROFILE")
        if profile:
            return Path(profile) / ".claude"
    return Path.home() / ".claude"


def mirror_dir() -> Path:
    """Notion ミラーの位置。notion_sync.py が使う NOTION_MIRROR_DIR と同じ規則。"""
    override = os.environ.get("NOTION_MIRROR_DIR")
    return Path(override).expanduser() if override else Path.home() / ".notion-mirror"


def repository_dir() -> Path:
    """git リポジトリの置き場。マシンごとに違うので環境変数で上書きできる。"""
    override = os.environ.get("REPOSITORY_DIR")
    return Path(override).expanduser() if override else Path.home() / "Documents" / "Repository"


def source_root() -> Path:
    """解説資料の原文置き場。

    先頭の `_` は「Notion 由来ではなく、こちらが予約した領域」の印である。ミラー直下の
    名前は Notion 側のページ名が決めるため、印を付けないと同名ページができた瞬間に混ざる。
    """
    override = os.environ.get("DOC_SOURCE_DIR")
    return Path(override).expanduser() if override else mirror_dir() / "_md"


def resolve_source(relative: str) -> Path:
    """`<project>/docs/<name>.md` 形式の相対パスを原文の実体へ解決する。

    `_md/` が原本だが、移行前のプロジェクト `docs/` も見る。移行を一度に済ませなくても
    パイプラインが動き続けるようにするためで、移行が終われば後者は空振りする。
    """
    candidate = source_root() / relative
    return candidate if candidate.is_file() else repository_dir() / relative

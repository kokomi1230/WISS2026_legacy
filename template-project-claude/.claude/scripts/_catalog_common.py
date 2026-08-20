r"""`.claude/scripts/` の共通ユーティリティ。

CATALOG.md はプラグイン・スキル・subagent の統合 source-of-truth。
外部依存なし（標準ライブラリのみ）。以下を提供する:
- frontmatter パース（YAML のミニマルなサブセット）
- HTML エスケープ
- カタログテンプレートの描画（{{KEY}} 置換）
- hook からの呼び出し用の自己再帰ロック
- 設定ディレクトリの解決と、設定ファイルへの実トークン直書き検査

設定ディレクトリの解決をここに置くのは、テンプレートから派生したどのプロジェクトでも
本モジュールだけは必ず存在するためである。`user_scope_sync.py`（原本の配置エンジン）は
テンプレートリポジトリにしか無いので、そちらに置くと派生プロジェクトで import できない。
"""

from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
TEMPLATE_PATH = PROJECT_ROOT / ".claude" / "templates" / "catalog.html.tmpl"
LOCK_PATH = PROJECT_ROOT / ".claude" / ".catalog-sync-lock"

# ntn_xxxxxxxx のような雛形を実トークンと誤認しないため、1 文字の繰り返しは除外する。
_SECRET_RE = re.compile(r"(?:ntn_|sk-|secret_)([A-Za-z0-9]{16,})")


# ---------- 設定ディレクトリ ----------


def is_windows() -> bool:
    """Git Bash から native Python が呼ばれる場合も Windows とみなす。"""
    return os.name == "nt" or sys.platform in ("win32", "msys", "cygwin")


def config_dir_path() -> str:
    """Claude Code の設定ディレクトリを文字列で決める。

    CLAUDE_CONFIG_DIR を最優先するのは、ハーネスの規約であると同時に、隔離環境で
    検証できるようにするため。Windows で Path.home() を使わないのは、Git Bash 上の
    MSYS Python では HOME が %USERPROFILE% と一致しないことがあるから。

    Path ではなく str を返すのは、Windows 分岐を macOS 上のテストからも呼べるように
    するため（pathlib は他 OS の Path を生成できない）。
    """
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return os.path.expanduser(override)
    if is_windows():
        profile = os.environ.get("USERPROFILE")
        if profile:
            return os.path.join(profile, ".claude")
    return os.path.join(os.path.expanduser("~"), ".claude")


def resolve_config_dir() -> Path:
    return Path(config_dir_path())


def resolve_legacy_json(config_dir: Path) -> Path:
    """MCP 登録先の .claude.json。通常は設定ディレクトリと兄弟関係にある。"""
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        return config_dir / ".claude.json"
    return config_dir.parent / ".claude.json"


def audit_secrets(config_dir: Path) -> list[str]:
    """設定ファイルに実トークンが直書きされていないか点検する。

    .env と settings.local.json は秘匿情報の置き場所として正しいので対象外。
    """
    findings = []
    for path in (config_dir / "settings.json", resolve_legacy_json(config_dir)):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(len(set(m)) > 1 for m in _SECRET_RE.findall(text)):
            findings.append(str(path))
    return findings


# ---------- frontmatter パース ----------

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    r"""YAML 風の frontmatter をパースする。(メタ情報 dict, 本文) を返す。

    対応形式: `key: scalar`、`key: [a, b, c]`、複数行の `key:\n  - x\n  - y`。
    完全な YAML パーサーではない。SKILL.md 形式向けに意図的に最小実装としている。
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    meta: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            current_key = None
            continue
        if line.startswith("  - ") and current_key:
            meta.setdefault(current_key, []).append(line[4:].strip().strip("\"'"))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if not val:
                current_key = key
                meta[key] = []
                continue
            current_key = None
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",")]
                meta[key] = [x for x in items if x]
            else:
                meta[key] = val.strip("\"'")
    return meta, body


# ---------- HTML ヘルパー ----------


def esc(s: Any) -> str:
    """HTML 属性・テキスト内容用にエスケープする。"""
    return html.escape(str(s), quote=True)


def render_template(placeholders: dict[str, str]) -> str:
    """テンプレートを読み込み、{{KEY}} プレースホルダーを置換する。"""
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, val in placeholders.items():
        text = text.replace("{{" + key + "}}", val)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if leftover:
        raise SystemExit(f"未解決のプレースホルダーがあります: {sorted(set(leftover))}")
    return text


# ---------- 自己再帰ロック ----------


def lock_held() -> bool:
    return LOCK_PATH.exists()


def acquire_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")


def release_lock() -> None:
    try:
        LOCK_PATH.unlink()
    except FileNotFoundError:
        pass


# ---------- ロギング ----------


def log(quiet: bool, *args: object) -> None:
    if quiet:
        return
    print(*args, file=sys.stderr)

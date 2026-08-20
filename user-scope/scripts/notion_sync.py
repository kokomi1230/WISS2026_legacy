#!/usr/bin/env python3
"""Notion のページをローカルの Markdown ミラーへ一方向で pull する。

Notion を「人間が書く・探す・読む」側、ローカルミラーを「エージェントが Grep / Read で
走査する」側と役割分担するための同期スクリプト。同期が書いた領域はいつでも取り直せる
派生物であり、手で編集しない。書き戻しは Notion 側へ行い、次の pull でミラーへ降りてくる。

MCP 経由ではなく REST API を直接叩くのは、ページ本文をモデルのコンテキストに通さない
ためである（コンテキストを通すと、ミラー化によるコスト削減が打ち消される）。

ミラーは全プロジェクト共通の 1 箇所に置く。既定は ~/.notion-mirror/、
環境変数 NOTION_MIRROR_DIR で上書きできる。

`_` で始まる直下のディレクトリ（_md/ 原文・_html/ 清書版）は Notion 由来ではなく、
同期の管理外である。消してはならないため走査からも外している。

Usage:
  python3 notion_sync.py                 # 増分同期
  python3 notion_sync.py --check         # 差分件数のみ表示（書き込みなし、差分ありで exit 2）
  python3 notion_sync.py --dry-run       # 取得予定ページの一覧を表示（書き込みなし）
  python3 notion_sync.py --full          # manifest を無視して全ページを再取得

終了コード: 0=正常 / 1=エラー / 2=差分あり（--check 時）/ 3=未設定（NOTION_TOKEN 不在）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config_dir import config_dir  # noqa: E402

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
# 配置先と参照先を一致させる。CLAUDE_CONFIG_DIR で配置したのに ~/.claude を読むと
# 「配置したはずの .env が見つからない」という食い違いが起きる。
USER_CONFIG_DIR = config_dir()

# .env の探索順。作業中のプロジェクト固有の設定を、全プロジェクト共通の設定より優先する。
# 本スクリプトはユーザースコープ（~/.claude/scripts/）に置かれるため、
# __file__ からの相対でプロジェクトを推定してはいけない。
ENV_SEARCH_PATHS = (PROJECT_ROOT / ".env", USER_CONFIG_DIR / ".env")

DEFAULT_MIRROR_DIR = Path.home() / ".notion-mirror"
MANIFEST_NAME = "_manifest.json"
# 書き出しのみに使う。将来 manifest の形式を変えたとき、移行要否の判定に用いる
MANIFEST_VERSION = 1

API_BASE = "https://api.notion.com/v1"
# 2022-06-28 に固定する。2025-09-03 以降は databases が data sources へ再編されており、
# 本スクリプトが使う databases エンドポイントの形が変わるため。
API_VERSION = "2022-06-28"
# 複数データソースを持つ DB は 2022-06-28 の /databases/{id} が 400 を返す。
# タイトル取得のフォールバックにのみ使う。
MULTI_SOURCE_API_VERSION = "2025-09-03"

# Notion API のレート上限は平均 3 req/s。安全側に倒して間隔を空ける
MIN_REQUEST_INTERVAL_SEC = 0.34
MAX_RETRIES = 4
RETRY_MARGIN_SEC = 0.5
REQUEST_TIMEOUT_SEC = 60
API_PAGE_SIZE = 100
ERROR_DETAIL_MAX_CHARS = 300

# ファイル名に埋める短縮 ID の長さ。タイトルが変わってもパスを安定させるために使う
SHORT_ID_LENGTH = 8
TITLE_SLUG_MAX_LENGTH = 40

SETUP_HINT = """NOTION_TOKEN が未設定のため同期を行いませんでした。

セットアップ手順:
  1. https://www.notion.so/my-integrations で内部インテグレーションを作成する
     （Notion MCP と資格情報を共有するため、権限は読み取りに加えて挿入・更新も有効にする）
  2. ミラーしたい Notion のページ / データベースを開き、そのインテグレーションに共有する
  3. 次のいずれかに設定する（後ろほど優先度が低い）

       環境変数 NOTION_TOKEN
       <プロジェクト>/.env
       ~/.claude/.env        ← 全プロジェクト共通

     いずれも書式は NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxx

詳細は ~/.claude/skills/notion-knowledge-base/reference.md を参照。"""


# ---------- 設定の読み込み ----------


def load_env_file(path: Path) -> dict[str, str]:
    """.env から KEY=VALUE 形式の行を読む。存在しなければ空を返す。"""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip("\"'")
    return values


def resolve_setting(name: str) -> str | None:
    """設定値を 環境変数 → プロジェクトの .env → ~/.claude/.env の順に探す。"""
    if os.environ.get(name):
        return os.environ[name]
    for path in ENV_SEARCH_PATHS:
        value = load_env_file(path).get(name)
        if value:
            return value
    return None


def resolve_token() -> str | None:
    """NOTION_TOKEN を探す。"""
    return resolve_setting("NOTION_TOKEN")


def resolve_mirror_dir() -> Path:
    """ミラーの出力先を決める。全プロジェクト共通の固定位置を既定とする。"""
    override = resolve_setting("NOTION_MIRROR_DIR")
    return Path(override).expanduser() if override else DEFAULT_MIRROR_DIR


# ---------- API クライアント ----------


class NotionPageUnavailableError(Exception):
    """共有が外れた等でページを取得できないことを示す。呼び出し側はそのページをスキップする。"""


class NotionRequestError(Exception):
    """上記以外の API エラー。補助的な問い合わせでは握りつぶし、本筋の取得では中断する。"""


class NotionClient:
    """Notion REST API の最小クライアント。標準ライブラリのみで実装する。"""

    def __init__(self, token: str, quiet: bool = False) -> None:
        """トークンを保持し、レート制限用の時刻と DB タイトルのキャッシュを初期化する。

        `_database_titles` は同一データベースへのタイトル問い合わせを 1 回に抑えるためのキャッシュ。
        """
        self.token = token
        self.quiet = quiet
        self._last_request_at = 0.0
        self._database_titles: dict[str, str] = {}

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < MIN_REQUEST_INTERVAL_SEC:
            time.sleep(MIN_REQUEST_INTERVAL_SEC - elapsed)
        self._last_request_at = time.monotonic()

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        api_version: str = API_VERSION,
    ) -> dict[str, Any]:
        """API を呼ぶ。429 は Retry-After に従って再試行する。"""
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": api_version,
            "Content-Type": "application/json",
        }
        for attempt in range(MAX_RETRIES):
            self._throttle()
            req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as res:
                    return json.loads(res.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                if err.code == 429 and attempt < MAX_RETRIES - 1:
                    wait_sec = float(err.headers.get("Retry-After") or 1) + RETRY_MARGIN_SEC
                    log(self.quiet, f"  レート制限のため {wait_sec:.1f}s 待機します")
                    time.sleep(wait_sec)
                    continue
                if err.code == 401:
                    raise SystemExit("NOTION_TOKEN が無効です。インテグレーションのトークンを確認してください。")
                if err.code in (403, 404):
                    # 取得の途中で共有が外れたページ。空の本文で既存ファイルを潰さないよう、
                    # 呼び出し側にスキップさせる
                    raise NotionPageUnavailableError(path)
                detail = err.read().decode("utf-8", errors="replace")[:ERROR_DETAIL_MAX_CHARS]
                raise NotionRequestError(f"Notion API エラー ({err.code}) {path}: {detail}")
            except urllib.error.URLError as err:
                raise SystemExit(f"Notion API へ接続できません: {err.reason}")
        return {}

    def search_pages(self) -> list[dict[str, Any]]:
        """インテグレーションに共有されている全ページのメタ情報を列挙する。

        本文は取得しない。列挙は安価なので毎回全件行い、本文取得だけを増分に絞る。
        """
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {"filter": {"value": "page", "property": "object"}, "page_size": API_PAGE_SIZE}
            if cursor:
                body["start_cursor"] = cursor
            payload = self.request("POST", "/search", body)
            pages.extend(payload.get("results", []))
            if not payload.get("has_more"):
                break
            cursor = payload.get("next_cursor")
        return [page for page in pages if not page.get("archived") and not page.get("in_trash")]

    def fetch_children(self, block_id: str) -> list[dict[str, Any]]:
        """ブロックの子を全件取得する（ページネーション込み）。"""
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            query = f"?page_size={API_PAGE_SIZE}" + (f"&start_cursor={cursor}" if cursor else "")
            payload = self.request("GET", f"/blocks/{block_id}/children{query}")
            blocks.extend(payload.get("results", []))
            if not payload.get("has_more"):
                break
            cursor = payload.get("next_cursor")
        return blocks

    def database_title(self, database_id: str) -> str:
        """データベースのタイトルを取得する（同一 ID は 1 回だけ問い合わせる）。

        タイトルは保存先ディレクトリ名にしか使わない補助情報なので、取得に失敗しても
        同期は続行する。複数データソースを持つ DB は 2022-06-28 では 400 になるため、
        新しい API バージョンで取り直す。
        """
        if database_id not in self._database_titles:
            title = ""
            for version in (API_VERSION, MULTI_SOURCE_API_VERSION):
                try:
                    payload = self.request("GET", f"/databases/{database_id}", api_version=version)
                except (NotionPageUnavailableError, NotionRequestError):
                    continue
                title = plain_text(payload.get("title", []))
                if title:
                    break
            self._database_titles[database_id] = title or "database"
        return self._database_titles[database_id]


# ---------- リッチテキスト / ブロックの変換 ----------


def plain_text(rich_text: list[dict[str, Any]]) -> str:
    """装飾を落とした素のテキストを返す。"""
    return "".join(span.get("plain_text", "") for span in rich_text)


def rich_text_to_markdown(rich_text: list[dict[str, Any]]) -> str:
    """リッチテキストを Markdown の装飾付き文字列へ変換する。"""
    parts: list[str] = []
    for span in rich_text:
        text = span.get("plain_text", "")
        if not text:
            continue
        annotations = span.get("annotations", {})
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        href = span.get("href")
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def media_url(block_payload: dict[str, Any]) -> str:
    """image / file / video 等のブロックから URL を取り出す。"""
    if block_payload.get("type") == "external":
        return block_payload.get("external", {}).get("url", "")
    return block_payload.get("file", {}).get("url", "")


# 子をそのまま展開するだけの入れ物ブロック。プレースホルダにすると中身が丸ごと消えるため個別に扱う
TRANSPARENT_BLOCKS = {"column_list", "column", "synced_block"}

HEADING_RE = re.compile(r"^heading_(\d+)$")
MAX_HEADING_LEVEL = 6


def blocks_to_markdown_lines(client: NotionClient, blocks: list[dict[str, Any]], depth: int = 0) -> list[str]:
    """ブロック列を Markdown の行リストへ変換する。子ブロックは再帰的に取得する。

    未対応の種類は HTML コメントのプレースホルダとして残し、内容を黙って落とさない。
    """
    lines: list[str] = []
    indent = "  " * depth
    ordered_index = 0

    for block in blocks:
        block_type = block.get("type", "")
        payload = block.get(block_type) or {}
        text = rich_text_to_markdown(payload.get("rich_text", []))

        if block_type != "numbered_list_item":
            ordered_index = 0

        if block_type in TRANSPARENT_BLOCKS:
            if block.get("has_children"):
                lines.extend(blocks_to_markdown_lines(client, client.fetch_children(block["id"]), depth))
            continue

        if block_type == "paragraph":
            lines.append(indent + text if text else "")
        elif HEADING_RE.match(block_type):
            # API は heading_1..3 を返す仕様だが、実データには heading_4 も現れる。
            # Markdown の上限 6 に丸めて拾う
            level = min(int(block_type.split("_")[1]), MAX_HEADING_LEVEL)
            lines.append("")
            lines.append(f"{'#' * level} {text}")
            lines.append("")
        elif block_type == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif block_type == "numbered_list_item":
            ordered_index += 1
            lines.append(f"{indent}{ordered_index}. {text}")
        elif block_type == "to_do":
            mark = "x" if payload.get("checked") else " "
            lines.append(f"{indent}- [{mark}] {text}")
        elif block_type == "toggle":
            lines.append(f"{indent}- **{text}**")
        elif block_type == "quote":
            lines.append(f"{indent}> {text}")
        elif block_type == "callout":
            icon = (payload.get("icon") or {}).get("emoji", "")
            lines.append(f"{indent}> {icon} {text}".rstrip())
        elif block_type == "code":
            language = payload.get("language", "")
            lines.append(f"{indent}```{language}")
            lines.extend(f"{indent}{line}" for line in plain_text(payload.get("rich_text", [])).splitlines())
            lines.append(f"{indent}```")
        elif block_type == "divider":
            lines.append("")
            lines.append("---")
            lines.append("")
        elif block_type == "equation":
            lines.append(f"{indent}$${payload.get('expression', '')}$$")
        elif block_type == "table":
            lines.extend(table_to_markdown_lines(client, block, indent))
            continue
        elif block_type in ("image", "video", "file", "pdf"):
            url = media_url(payload)
            caption = rich_text_to_markdown(payload.get("caption", [])) or block_type
            prefix = "!" if block_type == "image" else ""
            lines.append(f"{indent}{prefix}[{caption}]({url})")
        elif block_type in ("bookmark", "embed", "link_preview"):
            url = payload.get("url", "")
            caption = rich_text_to_markdown(payload.get("caption", [])) or url
            lines.append(f"{indent}[{caption}]({url})")
        elif block_type in ("child_page", "child_database"):
            title = payload.get("title", "")
            lines.append(f"{indent}- [{title}](https://www.notion.so/{block['id'].replace('-', '')})")
        else:
            lines.append(f"{indent}<!-- 未対応ブロック: {block_type} -->")

        if block.get("has_children") and block_type != "table":
            lines.extend(blocks_to_markdown_lines(client, client.fetch_children(block["id"]), depth + 1))

    return lines


def table_to_markdown_lines(client: NotionClient, block: dict[str, Any], indent: str) -> list[str]:
    """table ブロックを Markdown の表へ変換する。"""
    rows = client.fetch_children(block["id"]) if block.get("has_children") else []
    cell_rows: list[list[str]] = []
    for row in rows:
        cells = (row.get("table_row") or {}).get("cells", [])
        cell_rows.append([rich_text_to_markdown(cell).replace("|", "\\|") or " " for cell in cells])
    if not cell_rows:
        return []

    has_header = (block.get("table") or {}).get("has_column_header", False)
    width = max(len(row) for row in cell_rows)
    padded_rows = [row + [" "] * (width - len(row)) for row in cell_rows]
    separator = f"{indent}|" + "---|" * width

    # Markdown の表はヘッダ行が必須。Notion 側にヘッダが無い場合は空のヘッダを補う
    if not has_header:
        padded_rows.insert(0, [" "] * width)

    lines = [""]
    for index, row in enumerate(padded_rows):
        lines.append(f"{indent}| " + " | ".join(row) + " |")
        if index == 0:
            lines.append(separator)
    lines.append("")
    return lines


# ---------- プロパティ / frontmatter ----------


def property_to_value(prop: dict[str, Any]) -> Any:
    """Notion のプロパティ値を、frontmatter に書ける素の値へ変換する。"""
    prop_type = prop.get("type", "")
    data = prop.get(prop_type)

    if prop_type in ("title", "rich_text"):
        return plain_text(data or [])
    if prop_type in ("select", "status"):
        return (data or {}).get("name", "")
    if prop_type == "multi_select":
        return [option.get("name", "") for option in data or []]
    if prop_type == "date":
        if not data:
            return ""
        start, end = data.get("start", ""), data.get("end")
        return f"{start}/{end}" if end else start
    if prop_type == "people":
        return [person.get("name", "") for person in data or []]
    if prop_type == "relation":
        return [item.get("id", "") for item in data or []]
    if prop_type == "files":
        return [item.get("name", "") for item in data or []]
    if prop_type in ("formula", "rollup"):
        # formula / rollup は {"type": "number", "number": 3} のように結果の型を自己申告する
        result = data or {}
        return result.get(result.get("type", ""), "")
    if prop_type in ("checkbox", "number", "url", "email", "phone_number", "created_time", "last_edited_time"):
        return data if data is not None else ""
    if prop_type in ("created_by", "last_edited_by"):
        return (data or {}).get("name", "")
    return ""


_YAML_UNSAFE_RE = re.compile(r"^[\s>|&*!%@`\[\]{}#-]|[:#]\s|[\n\"']|\s$")


def yaml_scalar(value: Any) -> str:
    """frontmatter 用にスカラーを整形する。安全なら素のまま、そうでなければ引用符で囲む。

    Grep しやすさを優先し、不要な引用符を付けない（例: `状態: 未整理`）。
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or _YAML_UNSAFE_RE.search(text):
        return json.dumps(text, ensure_ascii=False)
    return text


def build_frontmatter(page: dict[str, Any], title: str, source_database: str) -> list[str]:
    """ページのメタ情報とプロパティを frontmatter の行リストにする。"""
    lines = [
        "---",
        f"title: {yaml_scalar(title)}",
        f"notion_id: {page['id']}",
        f"notion_url: {yaml_scalar(page.get('url', ''))}",
        f"last_edited_time: {yaml_scalar(page.get('last_edited_time', ''))}",
        f"notion_database: {yaml_scalar(source_database)}",
    ]
    for name, prop in (page.get("properties") or {}).items():
        if prop.get("type") == "title":
            continue
        value = property_to_value(prop)
        if value == "" or value == []:
            continue
        if isinstance(value, list):
            lines.append(f"{name}: [{', '.join(yaml_scalar(item) for item in value)}]")
        else:
            lines.append(f"{name}: {yaml_scalar(value)}")
    lines.append("---")
    lines.append("")
    return lines


# ---------- パスの決定 ----------

_UNSAFE_PATH_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_WHITESPACE_RE = re.compile(r"\s+")

# 種別を表すプロパティ名の候補。ミラー内でディレクトリを分けるために使う
KIND_PROPERTY_NAMES = ("種別", "Type", "type", "カテゴリ", "Category")


def slugify(text: str, max_length: int = TITLE_SLUG_MAX_LENGTH) -> str:
    """ファイル名 / ディレクトリ名に使える文字列へ変換する。日本語はそのまま残す。"""
    text = _UNSAFE_PATH_RE.sub("", text)
    text = _WHITESPACE_RE.sub("-", text.strip())
    text = text.strip("-.")
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text or "untitled"


def page_title(page: dict[str, Any]) -> str:
    """ページのタイトルプロパティを取り出す。"""
    for prop in (page.get("properties") or {}).values():
        if prop.get("type") == "title":
            return plain_text(prop.get("title") or [])
    return ""


def page_date(page: dict[str, Any]) -> str:
    """ファイル名の先頭に付ける日付。日付プロパティを優先し、なければ作成日を使う。"""
    for prop in (page.get("properties") or {}).values():
        if prop.get("type") == "date" and prop.get("date"):
            start = prop["date"].get("start", "")
            if start:
                return start[:10]
    return (page.get("created_time") or "")[:10]


def page_kind(page: dict[str, Any]) -> str:
    """種別プロパティの値。ミラー内のサブディレクトリ名になる。"""
    properties = page.get("properties") or {}
    for name in KIND_PROPERTY_NAMES:
        prop = properties.get(name)
        if prop and prop.get("type") in ("select", "status"):
            return (prop.get(prop["type"]) or {}).get("name", "")
    return ""


def resolve_page_path(client: NotionClient, page: dict[str, Any]) -> tuple[str, str]:
    """ミラー内の相対パスと、親データベース名を決める。

    データベース配下のページは「DB 名 / 種別」のディレクトリへ、
    それ以外のページは pages/ へ置く。
    """
    parent = page.get("parent") or {}
    if parent.get("type") == "database_id":
        source_database = client.database_title(parent["database_id"])
        directory = Path(slugify(source_database))
        kind = page_kind(page)
        if kind:
            directory = directory / slugify(kind)
    else:
        source_database = "pages"
        directory = Path("pages")

    short_id = page["id"].replace("-", "")[:SHORT_ID_LENGTH]
    date = page_date(page)
    stem = f"{date}-{slugify(page_title(page))}-{short_id}" if date else f"{slugify(page_title(page))}-{short_id}"
    return str(directory / f"{stem}.md"), source_database


# ---------- manifest ----------


def load_manifest(mirror_dir: Path) -> dict[str, dict[str, str]]:
    """manifest を読む。無ければ空を返す。"""
    path = mirror_dir / MANIFEST_NAME
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload.get("pages", {})


def save_manifest(mirror_dir: Path, pages: dict[str, dict[str, str]]) -> None:
    """manifest を書き出す。"""
    payload = {
        "version": MANIFEST_VERSION,
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "pages": pages,
    }
    (mirror_dir / MANIFEST_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prune_empty_dirs(mirror_dir: Path) -> None:
    """ファイル削除で空になったディレクトリを取り除く。"""
    # 深い階層から処理し、子を消した結果空になった親も同じ走査で回収する
    for path in sorted(mirror_dir.rglob("*"), key=lambda entry: len(entry.parts), reverse=True):
        # `_` 始まりは同期の管理外（_md/ の原文・_html/ の清書版）。中身を作るのも消すのも同期ではない
        if any(part.startswith("_") for part in path.relative_to(mirror_dir).parts):
            continue
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


# ---------- 同期本体 ----------


def log(quiet: bool, *args: object) -> None:
    if quiet:
        return
    print(*args, file=sys.stderr)


def sync(args: argparse.Namespace) -> int:
    """Notion をミラーへ同期する。

    ページの列挙は毎回全件行い（メタ情報のみなので安価、削除の検出にも必要）、
    本文の取得だけを last_edited_time の差分に絞る。--check / --dry-run は
    書き込みの前に return するため、ミラーを一切変更しない。
    """
    token = resolve_token()
    if not token:
        print(SETUP_HINT, file=sys.stderr)
        return 3

    mirror_dir = resolve_mirror_dir()
    client = NotionClient(token, quiet=args.quiet)

    log(args.quiet, f"ミラー: {mirror_dir}")
    log(args.quiet, "共有ページを列挙しています...")
    remote_pages = {page["id"]: page for page in client.search_pages()}
    manifest = load_manifest(mirror_dir)

    pages_to_fetch = [
        page
        for page_id, page in remote_pages.items()
        if args.full
        or page_id not in manifest
        or manifest[page_id].get("last_edited_time") != page.get("last_edited_time")
    ]
    page_ids_to_delete = [page_id for page_id in manifest if page_id not in remote_pages]

    log(
        args.quiet,
        f"共有ページ {len(remote_pages)} 件 / 取得対象 {len(pages_to_fetch)} 件"
        f" / 削除対象 {len(page_ids_to_delete)} 件",
    )

    if args.check:
        return 2 if (pages_to_fetch or page_ids_to_delete) else 0

    if args.dry_run:
        for page in pages_to_fetch:
            path, _ = resolve_page_path(client, page)
            print(f"  取得: {path}")
        for page_id in page_ids_to_delete:
            print(f"  削除: {manifest[page_id]['path']}")
        return 0

    if not pages_to_fetch and not page_ids_to_delete:
        log(args.quiet, "変更はありません。")
        return 0

    mirror_dir.mkdir(parents=True, exist_ok=True)
    skipped = 0

    for index, page in enumerate(pages_to_fetch, start=1):
        page_id = page["id"]
        title = page_title(page) or "(無題)"
        try:
            relative_path, source_database = resolve_page_path(client, page)
            log(args.quiet, f"  [{index}/{len(pages_to_fetch)}] {relative_path}")
            body = blocks_to_markdown_lines(client, client.fetch_children(page_id))
        except NotionPageUnavailableError:
            # 取得中に共有が外れた。既存ファイルと manifest は触らず次回に持ち越す
            log(args.quiet, f"  [{index}/{len(pages_to_fetch)}] スキップ（取得不可）: {title}")
            skipped += 1
            continue

        frontmatter = build_frontmatter(page, title, source_database)
        content = "\n".join(frontmatter + [f"# {title}", ""] + body).rstrip() + "\n"

        target = mirror_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        # ページの移動やリネームで出力先が変わった場合、旧ファイルを残さない
        previous_path = manifest.get(page_id, {}).get("path")
        if previous_path and previous_path != relative_path:
            (mirror_dir / previous_path).unlink(missing_ok=True)

        manifest[page_id] = {"path": relative_path, "last_edited_time": page.get("last_edited_time", "")}

    for page_id in page_ids_to_delete:
        (mirror_dir / manifest[page_id]["path"]).unlink(missing_ok=True)
        log(args.quiet, f"  削除: {manifest[page_id]['path']}")
        del manifest[page_id]

    save_manifest(mirror_dir, manifest)
    prune_empty_dirs(mirror_dir)
    log(args.quiet, "完了" + (f"（{skipped} 件スキップ）" if skipped else ""))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Notion をローカルの Markdown ミラーへ一方向で同期する")
    parser.add_argument("--check", action="store_true", help="差分件数のみ表示（書き込みなし、差分ありで exit 2）")
    parser.add_argument("--dry-run", action="store_true", help="取得 / 削除の対象一覧を表示（書き込みなし）")
    parser.add_argument("--full", action="store_true", help="manifest を無視して全ページを再取得")
    parser.add_argument("--quiet", action="store_true", help="進捗ログを抑制")
    try:
        return sync(parser.parse_args())
    except NotionRequestError as err:
        # 本筋の取得での API エラー。traceback ではなく 1 行で報告して終了する
        raise SystemExit(str(err))


if __name__ == "__main__":
    sys.exit(main())

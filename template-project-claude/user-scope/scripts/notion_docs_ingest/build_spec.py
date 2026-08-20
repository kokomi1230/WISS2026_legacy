"""ミラーの 42 ノートから投入スペックを組み立てる。

lead は既存の `概要` プロパティを流用し、mermaid / edits / html は overrides.json から取る。
定型文書の集約ノートは docs 取り込みの対象外なので除外する。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _config_dir import mirror_dir, resolve_source  # noqa: E402

MIRROR = mirror_dir() / "研究ノート_DB"
HERE = Path(__file__).parent
OVERRIDES = json.loads((HERE / "overrides.json").read_text(encoding="utf-8"))
OUT = HERE / "spec.json"

SOURCE_RE = re.compile(r"`([A-Za-z_][\w.-]*/[^`]*\.md)`")
# 定型文書 118 本を集約したメタノート。原文 1 本の取り込みではないため除外する
EXCLUDE_TITLES = {"全リポジトリに複製された定型文書"}
# 取り込み前は `## 出典`、取り込み後は `## 取り込み元`。二度目の実行でも同じ集合を得るため両方見る
SOURCE_HEADINGS = ("## 取り込み元", "## 出典")


def find_source_section(text: str) -> str | None:
    for heading in SOURCE_HEADINGS:
        if heading in text:
            return text.split(heading, 1)[1].split("\n## ", 1)[0]
    return None


def parse_note(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if find_source_section(text) is None:
        return None
    fields: dict[str, str] = {}
    for line in text.splitlines():
        for key in ("notion_id", "title", "概要"):
            prefix = f"{key}: "
            if line.startswith(prefix) and key not in fields:
                fields[key] = line[len(prefix) :].strip()
    if fields.get("title") in EXCLUDE_TITLES:
        return None
    tail = find_source_section(text) or ""
    sources = [s for s in SOURCE_RE.findall(tail) if resolve_source(s).is_file()]
    if not sources:
        return None
    primary = max(sources, key=lambda s: resolve_source(s).stat().st_size)
    head = resolve_source(primary).read_text(encoding="utf-8").splitlines()
    override = OVERRIDES.get(primary, {})
    return {
        "page_id": fields["notion_id"],
        "note_title": fields["title"],
        "kind": path.parent.name,
        "sources": sources,
        "primary": primary,
        "source_title": next((line[2:].strip() for line in head if line.startswith("# ")), fields["title"]),
        "lead": fields.get("概要", ""),
        "html": override.get("html"),
        "mermaid": override.get("mermaid", []),
        "edits": override.get("edits", []),
    }


def main() -> None:
    entries = [e for e in (parse_note(p) for p in sorted(MIRROR.rglob("*.md"))) if e]
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    n_fig = sum(len(e["mermaid"]) for e in entries)
    n_html = sum(1 for e in entries if e["html"])
    n_edit = sum(len(e["edits"]) for e in entries)
    print(f"{len(entries)} 件 / mermaid {n_fig} 個 / HTML {n_html} 本 / 重複整理 {n_edit} 箇所")
    missing = [e["primary"] for e in entries if not e["lead"]]
    if missing:
        print("lead が空:", missing)
    unused = set(OVERRIDES) - {e["primary"] for e in entries}
    if unused:
        print("未使用の override:", sorted(unused))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CLAUDE.md / .claude/rules/ / README.md を検査する。読取専用。

判定を人の目視ではなくスクリプトに寄せるのは、行数・paths: の有無・リンク切れが
機械的に数えられる事実であり、目視に任せると同じファイルで判定がぶれるためである。

コードブロックの中は見出しにもリンクにも数えない。`# セットアップ` のようなシェル
コメントを見出しと誤認すると、構造の判定が丸ごと狂う（実際に起きた）。

  python3 validate_docs.py [PATH]        人間向けレポート
  python3 validate_docs.py --json        機械可読

終了コード: 0 = clean / 1 = 警告のみ / 2 = 要対応
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAJOR, MINOR, INFO = "major", "minor", "info"
BLOCKING = (MAJOR,)

# 公式ドキュメントの目標値。200 行を超えると指示の遵守率が落ち、250 行は事実上の上限。
CLAUDE_MD_TARGET_LINES = 200
CLAUDE_MD_HARD_LIMIT = 250
# standard-readme の Short Description の上限。
README_DESCRIPTION_MAX = 120

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
LINK_RE = re.compile(r"\[([^\]]*)\]\((?!https?://|#|mailto:)([^)\s]+)\)")
# CLAUDE.md 冒頭で他ファイルを読み込む記法。起動時に全ロードされる。
IMPORT_RE = re.compile(r"(?:^|\s)@([\w./~-]+\.(?:md|json|txt))\b")

# この系統のテンプレートに由来する定型節。プロジェクト固有の内容を持たないので、
# 残っていれば削れる。前方一致で見る（`主要 skill` と `主要 skill / command` など揺れる）。
TEMPLATE_SECTION_PREFIXES = (
    "推奨プラグイン",
    "一括インストール",
    "主要 subagent",
    "主要 skill",
    "推奨ディレクトリ構造",
    "クイックスタート",
    "このテンプレートの構造",
    "カタログ同期メカニズム",
    "プラグイン導入・有効化の方針",
    "別マシン",
    "自動同期の限界",
)

# README に欲しい節。表記の揺れを許すため、いずれか 1 つ当たれば充足とみなす。
# ライセンスは入れない。公開しない個人 / 社内のプロジェクトでは無いのが正常であり、
# required にすると 21 件中 18 件で発火した。ほぼ全件で鳴る検査は読み飛ばされる。
# セットアップも執筆プロジェクトでは意味を持たないため、指摘は INFO に留める。
README_SECTIONS = (
    ("セットアップ", ("セットアップ", "インストール", "導入", "install", "setup", "getting started")),
    ("使い方", ("使い方", "使用方法", "実行", "usage", "使用", "how to", "クイックスタート", "quick start")),
)


class Finding:
    """1 件の指摘。level が判定の重みを持つ。"""

    def __init__(self, target: str, level: str, detail: str, hint: str = ""):
        """hint は直し方。示せないときは空にする。"""
        self.target = target
        self.level = level
        self.detail = detail
        self.hint = hint

    def as_dict(self) -> dict:
        """--json 出力用のプレーンな dict へ変換する。"""
        return {"target": self.target, "level": self.level, "detail": self.detail, "hint": self.hint}


def strip_fences(lines: list[str]) -> list[tuple[int, str]]:
    """コードブロックの外側の行だけを (行番号, 本文) で返す。

    閉じ記号は開始と同じ種類で同じ長さ以上でなければならない。単純に反転させると、
    ````markdown の中に ```bash を入れ子にした見本で開閉がずれる。
    """
    out: list[tuple[int, str]] = []
    opener = ""
    for i, line in enumerate(lines, 1):
        match = FENCE_RE.match(line)
        if match:
            token = match.group(1)
            if not opener:
                opener = token
                continue
            if token[0] == opener[0] and len(token) >= len(opener):
                opener = ""
                continue
        if not opener:
            out.append((i, line))
    return out


def has_emoji(text: str) -> list[str]:
    """絵文字を拾う。矢印や罫線は対象外にする。

    U+1F000 以降を絵文字とみなす。`→` `↓` のような記号を含めると、正しい日本語文書が
    軒並み誤検出される（実際に自分の検査で誤検出した）。
    """
    return sorted({ch for ch in text if ord(ch) >= 0x1F000})


def dead_links(path: Path, root: Path) -> list[str]:
    """リンク先が実在しないものを返す。コードブロック内は見ない。"""
    dead = []
    for _, line in strip_fences(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        for match in LINK_RE.finditer(line):
            target = match.group(2).split("#", 1)[0]
            if not target:
                continue
            if (path.parent / target).exists() or (root / target).exists():
                continue
            dead.append(target)
    return dead


def check_claude_md(root: Path) -> list[Finding]:
    path = root / "CLAUDE.md"
    if not path.exists():
        return [Finding("CLAUDE.md", MAJOR, "存在しない", "プロジェクトの規約を書く。project-docs skill の手順に従う")]
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    found: list[Finding] = []

    count = len(lines)
    if count > CLAUDE_MD_HARD_LIMIT:
        found.append(
            Finding(
                "CLAUDE.md",
                MAJOR,
                f"{count} 行（上限 {CLAUDE_MD_HARD_LIMIT}）",
                "条件付きの規約を .claude/rules/ へ、長い解説を docs/ へ移す",
            )
        )
    elif count > CLAUDE_MD_TARGET_LINES:
        found.append(Finding("CLAUDE.md", MINOR, f"{count} 行（目標 {CLAUDE_MD_TARGET_LINES} 未満）", "同上"))

    stale = []
    for _, line in strip_fences(lines):
        match = HEADING_RE.match(line)
        if match and any(match.group(2).startswith(p) for p in TEMPLATE_SECTION_PREFIXES):
            stale.append(match.group(2))
    if stale:
        found.append(
            Finding("CLAUDE.md", MINOR, f"テンプレート定型節 {len(stale)} 件: {', '.join(stale[:3])}", "節ごと削る")
        )

    imports = IMPORT_RE.findall(text)
    if imports:
        found.append(
            Finding(
                "CLAUDE.md",
                MINOR,
                f"@import {len(imports)} 件: {', '.join(imports[:3])}",
                "import 先は起動時に全ロードされコンテキストを削減しない。.claude/rules/ の paths: を使う",
            )
        )

    emoji = has_emoji(text)
    if emoji:
        found.append(
            Finding("CLAUDE.md", MAJOR, f"絵文字 {len(emoji)} 種: {' '.join(emoji[:5])}", "角括弧テキストに置き換える")
        )

    dead = dead_links(path, root)
    if dead:
        found.append(
            Finding(
                "CLAUDE.md", MAJOR, f"リンク切れ {len(dead)} 件: {', '.join(dead[:3])}", "リンクを外すか対象を復元する"
            )
        )

    return found


def check_rules(root: Path) -> list[Finding]:
    rules_dir = root / ".claude" / "rules"
    if not rules_dir.is_dir():
        return []
    found: list[Finding] = []
    for path in sorted(rules_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root)
        head = text.splitlines()[:12]
        if not any(line.startswith("paths:") for line in head):
            found.append(
                Finding(
                    str(rel),
                    MINOR,
                    "paths: が無い",
                    "paths: が無い rule は起動時に無条件ロードされ、CLAUDE.md に書くのと変わらない",
                )
            )
        emoji = has_emoji(text)
        if emoji:
            found.append(Finding(str(rel), MAJOR, f"絵文字 {len(emoji)} 種", "角括弧テキストに置き換える"))
        dead = dead_links(path, root)
        if dead:
            found.append(Finding(str(rel), MAJOR, f"リンク切れ {len(dead)} 件: {', '.join(dead[:3])}"))
    return found


def check_readme(root: Path) -> list[Finding]:
    path = root / "README.md"
    if not path.exists():
        return [Finding("README.md", MINOR, "存在しない", "人間の読者向けの説明を置く")]
    text = path.read_text(encoding="utf-8")
    visible = strip_fences(text.splitlines())
    found: list[Finding] = []

    headings = [(n, HEADING_RE.match(line)) for n, line in visible if HEADING_RE.match(line)]
    h1 = [m.group(2) for _, m in headings if len(m.group(1)) == 1]
    if not h1:
        found.append(Finding("README.md", MAJOR, "H1 のタイトルが無い", "先頭に `# <プロジェクト名>` を置く"))

    # タイトル直後の最初の本文行を Short Description とみなす。
    desc = ""
    seen_h1 = False
    for _, line in visible:
        if HEADING_RE.match(line):
            if len(HEADING_RE.match(line).group(1)) == 1:
                seen_h1 = True
                continue
            if seen_h1:
                break
        elif seen_h1 and line.strip():
            desc = line.strip()
            break
    if desc and len(desc) > README_DESCRIPTION_MAX:
        found.append(
            Finding(
                "README.md",
                MINOR,
                f"説明が {len(desc)} 字（上限 {README_DESCRIPTION_MAX}）",
                "1 文に絞り、詳細は下の節へ",
            )
        )

    titles = " ".join(m.group(2).lower() for _, m in headings)
    missing = [label for label, keys in README_SECTIONS if not any(k.lower() in titles for k in keys)]
    if missing:
        found.append(Finding("README.md", INFO, f"節が足りない: {', '.join(missing)}", "該当する作業があるなら足す"))

    emoji = has_emoji(text)
    if emoji:
        found.append(
            Finding("README.md", MAJOR, f"絵文字 {len(emoji)} 種: {' '.join(emoji[:5])}", "角括弧テキストに置き換える")
        )

    dead = dead_links(path, root)
    if dead:
        found.append(Finding("README.md", MAJOR, f"リンク切れ {len(dead)} 件: {', '.join(dead[:3])}"))

    return found


def run(root: Path) -> list[Finding]:
    return check_claude_md(root) + check_rules(root) + check_readme(root)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".", help="プロジェクトのルート（既定はカレント）")
    ap.add_argument("--json", action="store_true", help="機械可読な JSON で出力する")
    args = ap.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"error: ディレクトリが見つかりません: {root}", file=sys.stderr)
        return 2

    findings = run(root)
    blocking = [f for f in findings if f.level in BLOCKING]

    if args.json:
        print(
            json.dumps(
                {"root": str(root), "findings": [f.as_dict() for f in findings], "count": len(findings)},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"# ドキュメント検査 ({root.name})\n")
        if not findings:
            print("指摘なし。")
        for level in (MAJOR, MINOR, INFO):
            group = [f for f in findings if f.level == level]
            if not group:
                continue
            print(f"## {level} ({len(group)})")
            for f in group:
                print(f"- {f.target}: {f.detail}")
                if f.hint:
                    print(f"      → {f.hint}")
            print()

    if blocking:
        return 2
    # INFO は報告するが終了コードに影響させない。判断材料であって不備ではない。
    return 1 if any(f.level == MINOR for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

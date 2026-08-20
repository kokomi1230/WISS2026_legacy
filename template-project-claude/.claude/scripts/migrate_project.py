#!/usr/bin/env python3
"""既に派生済みのプロジェクトを、現行のテンプレート規約へ追随させる。

対象は CLAUDE.md の圧縮と .claude/rules/ の配置だけである。テンプレート運用資産の
削除は detemplate.py が既に持っているので、そちらを CLAUDE_PROJECT_DIR 付きで呼ぶ:

    CLAUDE_PROJECT_DIR=<target> python3 .claude/scripts/detemplate.py --apply

CLAUDE.md の圧縮は「消すもの」を見出しで列挙する方式にしてある。残す側を列挙すると、
列挙し漏れたプロジェクト固有の節が消える。消す側の列挙なら、漏れても古い節が残るだけで
情報は失われない。失敗の向きを安全側へ倒すための設計である。

モード:
  --plan   変更内容を JSON で出力する（書込なし）
  --apply  CLAUDE.md を書き換え、rules を配置する
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_RULES = TEMPLATE_ROOT / ".claude" / "rules"

# H2 節ごと削除する。配下の H3 も一緒に落ちる。
# 前方一致で判定するのは、同じ節が `主要 skill` と `主要 skill / command` のように
# プロジェクトごとに揺れて記録されているためである。
DROP_H2_PREFIXES = (
    "推奨プラグイン",
    "一括インストール",
    "主要 subagent",
    "主要 skill",
    "推奨ディレクトリ構造",
    "クイックスタート",
    "このテンプレートの構造",
    "カタログ同期メカニズム",
    "プラグイン導入・有効化の方針",
    "外部参照",
)

# H3 のみ削除し、親の H2 は残す。skill が同じ内容を持ち自動発火するもの、および
# テンプレート運用の説明が対象。
DROP_H3_PREFIXES = (
    "コーディング規約ワークフロー",
    "日本語執筆ワークフロー",
    "英文執筆ワークフロー",
    "Unity 開発ワークフロー",
    "Figma デザインワークフロー",
    "Notion 知識ベースワークフロー",
    "役割分担",
    "原本は本リポジトリの",
    "ユーザースコープの資産",
    "別マシン",
    "補助コマンド",
    "自動同期の限界",
    "必須（軸",
    "特化追加",
    "MCP（",
)

# 親が削除対象でも道連れにしない見出し。削除区間はここで打ち切る。
# 秘匿情報の方針は 3 層モデルの H2 配下に置かれているが、プラグイン導入の話が
# 不要になっても方針自体は残す必要がある。巻き添えで消すと規約が失われる。
KEEP_ALWAYS_PREFIXES = ("認証・秘匿情報スコープ方針",)

# この深さ以降の見出しも道連れにしない。テンプレート定型は H3 までで構成されており、
# H4 以深はプロジェクトが独自に足した詳細しか存在しない（全 21 件の実測で確認）。
KEEP_FROM_LEVEL = 4

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
# コードブロックの開始 / 終了。``` と ~~~ の両方を受ける。
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# 箇条書き 1 項目まるごとがリンクの行。本文中のインラインリンクは対象にしない。
LINK_ITEM_RE = re.compile(r"^\s*[-*]\s*\[[^\]]*\]\((?!https?://|#|mailto:)([^)\s]+)\)")
# 表の 1 行目セルがリンクの行（`| [docs/X.md](docs/X.md) | 用途 |`）。
LINK_ROW_RE = re.compile(r"^\s*\|\s*\[[^\]]*\]\((?!https?://|#|mailto:)([^)\s]+)\)")
# 本文中に埋まったリンク。行ごと消すと文が壊れるので、markup だけ外す。
INLINE_LINK_RE = re.compile(r"\[([^\]]*)\]\((?!https?://|#|mailto:)([^)\s]+)\)")


def _matches(title: str, prefixes: tuple[str, ...]) -> str | None:
    for prefix in prefixes:
        if title.startswith(prefix):
            return prefix
    return None


def compress_claude_md(text: str) -> tuple[str, list[str]]:
    """テンプレート定型の節を落とす。削除リストに無い見出しは中身を見ずに残す。

    戻り値は (新本文, 削除した見出しのリスト)。
    """
    lines = text.splitlines()
    kept: list[str] = []
    dropped: list[str] = []
    # 現在どのレベルの節を捨てている最中かを保持する。0 は捨てていない状態。
    dropping_level = 0
    # 親を失った見出しを繰り上げる量と、繰り上げ対象の深さの下限。
    promote_delta = 0
    promote_from = 0
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
        # コードブロック内の `# コマンドの説明` を見出しと誤認しない。誤認すると
        # 削除区間がそこで打ち切られ、テンプレート定型の後半が残ってしまう。
        match = None if in_fence else HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2)
            if promote_delta and level < promote_from:
                # 繰り上げた部分木を抜けた。
                promote_delta = 0
                promote_from = 0
            if dropping_level and (
                level <= dropping_level or level >= KEEP_FROM_LEVEL or _matches(title, KEEP_ALWAYS_PREFIXES)
            ):
                if level > dropping_level:
                    # 親ごと消える節から救い出した見出しは、親が居た深さへ繰り上げる。
                    # 元の深さのまま残すと、無関係な直前の節にぶら下がって読める。
                    promote_delta = level - dropping_level
                    promote_from = level
                dropping_level = 0
            if not dropping_level:
                drop = (level == 2 and _matches(title, DROP_H2_PREFIXES)) or (
                    level == 3 and _matches(title, DROP_H3_PREFIXES)
                )
                if drop:
                    dropping_level = level
                    dropped.append(title)
                elif promote_delta and level >= promote_from:
                    line = "#" * (level - promote_delta) + " " + title
        if not dropping_level:
            kept.append(line)
    return "\n".join(kept).rstrip() + "\n", dropped


def sweep_dead_links(text: str, project_root: Path) -> tuple[str, list[str]]:
    """リンク先が実在しない箇条書き / 表の行を落とす。

    節の削除だけでは `## 参考` に消えたドキュメントへのリンクが残る。行全体がリンク
    項目のときだけ消すのは、本文中のインラインリンクを巻き添えにしないためである。
    """
    kept: list[str] = []
    removed: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
        if in_fence:
            # コード例の中のリンク記法は文書のリンクではないので触らない。
            kept.append(line)
            continue
        match = LINK_ITEM_RE.match(line) or LINK_ROW_RE.match(line)
        if match:
            target = match.group(1).split("#", 1)[0]
            if target and not (project_root / target).exists():
                removed.append(target)
                continue
        kept.append(_defuse_inline_links(line, project_root, removed))
    return "\n".join(kept).rstrip() + "\n", removed


def _defuse_inline_links(line: str, project_root: Path, removed: list[str]) -> str:
    """文中の死んだリンクを code span へ落とす。

    行ごと消すと文が壊れる（「出典: [X](X) Part 3 Step 3」のような使われ方をする）。
    リンクを外して参照だけ残せば、文意を保ったままリンク切れが消える。
    """

    def replace(match: re.Match) -> str:
        target = match.group(2).split("#", 1)[0]
        if not target or (project_root / target).exists():
            return match.group(0)
        removed.append(target)
        return f"`{match.group(1)}`"

    return INLINE_LINK_RE.sub(replace, line)


def collapse_blank_runs(text: str) -> str:
    """節を抜いた跡に残る 3 行以上の空行を 1 行へ詰める。"""
    return re.sub(r"\n{3,}", "\n\n", text)


def plan_rules(project_root: Path) -> tuple[list[str], list[str]]:
    """配置する rules を決める。対象が存在しないプロジェクトへは配らない。

    user-scope.md は配らない。detemplate.py が user-scope/ を消すため、
    paths が永久にマッチしない rule になる。
    """
    install: list[str] = []
    skipped: list[str] = []
    dest_dir = project_root / ".claude" / "rules"
    wanted = {
        "catalog.md": (project_root / "docs" / "CATALOG.md").exists(),
        "python.md": any(p for p in project_root.rglob("*.py") if ".git" not in p.parts and "_archived" not in p.parts),
    }
    for name, applicable in wanted.items():
        if not applicable:
            skipped.append(f"{name} (対象ファイルなし)")
        elif (dest_dir / name).exists():
            skipped.append(f"{name} (既存を保持)")
        elif not (TEMPLATE_RULES / name).exists():
            skipped.append(f"{name} (配布元なし)")
        else:
            install.append(name)
    return install, skipped


def is_git_repo(project_root: Path) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def sweep_readme(project_root: Path, apply: bool) -> list[str]:
    """README.md のリンク切れも掃除する。

    README は圧縮しない（プロジェクトの説明でありテンプレート定型ではない）。ただし
    テンプレート解説 docs へのリンクは削除で切れるため、そこだけは直す必要がある。
    """
    readme = project_root / "README.md"
    if not readme.exists():
        return []
    before = readme.read_text(encoding="utf-8")
    swept, dead = sweep_dead_links(before, project_root)
    if not dead:
        # 直すべきリンクが無いなら触らない。空行の詰めだけを理由に他人の README へ
        # 差分を作ると、移行が何を変えたのか読み手に分からなくなる。
        return []
    if apply:
        readme.write_text(collapse_blank_runs(swept), encoding="utf-8")
    return dead


def run(project_root: Path, apply: bool) -> dict:
    claude_md = project_root / "CLAUDE.md"
    before = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    compressed, dropped = compress_claude_md(before)
    swept, dead_links = sweep_dead_links(compressed, project_root)
    after = collapse_blank_runs(swept)
    rules_install, rules_skipped = plan_rules(project_root)
    readme_dead = sweep_readme(project_root, apply)

    if apply:
        if before and after != before:
            claude_md.write_text(after, encoding="utf-8")
        if rules_install:
            dest_dir = project_root / ".claude" / "rules"
            dest_dir.mkdir(parents=True, exist_ok=True)
            for name in rules_install:
                shutil.copy2(TEMPLATE_RULES / name, dest_dir / name)

    return {
        "target": str(project_root),
        "claude_md": {
            "lines_before": len(before.splitlines()),
            "lines_after": len(after.splitlines()),
            "dropped_sections": dropped,
            "dead_links_removed": dead_links,
        },
        "readme_dead_links_removed": readme_dead,
        "rules_install": rules_install,
        "rules_skipped": rules_skipped,
        "applied": apply,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True, help="対象プロジェクトのパス")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="変更内容を JSON で出力する（書込なし）")
    mode.add_argument("--apply", action="store_true", help="CLAUDE.md を書き換え rules を配置する")
    ap.add_argument(
        "--allow-nogit",
        action="store_true",
        help="git 管理外でも実行する。復元手段が無くなるため既定では拒否する",
    )
    args = ap.parse_args()

    project_root = Path(args.target).expanduser().resolve()
    if not project_root.is_dir():
        print(f"error: 対象が見つかりません: {project_root}", file=sys.stderr)
        return 2
    if project_root == TEMPLATE_ROOT:
        print("error: テンプレート本体は対象外です（前段で対応済み）", file=sys.stderr)
        return 2
    if not is_git_repo(project_root) and not args.allow_nogit:
        print(
            f"error: git 管理下ではありません: {project_root}\n"
            "       書き換えを戻せないため中断します。--allow-nogit で強行できます。",
            file=sys.stderr,
        )
        return 2

    print(json.dumps(run(project_root, apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

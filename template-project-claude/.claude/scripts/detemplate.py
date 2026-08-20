#!/usr/bin/env python3
"""テンプレート運用専用の資産を派生プロジェクトから取り除く（脱テンプレート化）。

削除対象は下の DELETE_TARGETS に固定してある。呼び出し側から任意のパスを渡せる作りに
しないのは、消してよいものを判断する責任をスクリプト側に閉じ込めるためである。

削除を Bash ではなく Python で行うのは、/init-project の allowed-tools に
`Bash(rm:*)` という広い権限を足さずに済ませるため。

git 管理下のパスは `git rm -r --cached` でインデックスから外してから実体を消す。
これにより `git checkout HEAD -- <path>` で元に戻せる。原本は常にテンプレート
リポジトリ側に残るので、削除は二重の安全網の内側にある。

モード:
  --plan        削除対象を理由付き JSON で出力する（書込なし）
  --apply       削除を実行する
  --force-here  .template-origin ガードを無視する（テンプレート本体で強行する場合）
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _catalog_common import PROJECT_ROOT  # noqa: E402

# テンプレート本体を示すマーカー。`name: <ディレクトリ名>` を 1 行持つ。
TEMPLATE_ORIGIN_MARKER = PROJECT_ROOT / ".template-origin"
TEMPLATE_ORIGIN_NAME_RE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)

# 削除対象。(相対パス, 理由) の組。存在しないパスは黙って飛ばす（冪等性のため）。
# 並び順が削除順であり、自分自身とガードは最後に消す。
DELETE_TARGETS: tuple[tuple[str, str], ...] = (
    ("user-scope/", "全プロジェクト共通資産の原本。複製を派生に残すと古い版を掴む事故が起きる"),
    (".claude/scripts/setup-user-scope.sh", "user-scope 配置スクリプト。原本と一緒に不要になる"),
    (".claude/scripts/user_scope_sync.py", "同上"),
    (".claude/scripts/setup-plugins.sh", "プラグイン導入。マシン単位の作業でありプロジェクトの作業ではない"),
    (".claude/plugins-user-scope.json", "user scope 導入マニフェスト"),
    (".claude/scripts/apply_profile.py", "プロファイル適用。初期化が済めば使わない"),
    (".claude/profiles/", "用途プロファイル。apply_profile.py と対で不要になる"),
    (".claude/commands/init-project.md", "一度きりの初期化コマンド"),
    (".claude/commands/profile-switch.md", "apply_profile.py に依存するため道連れ"),
    (".claude/rules/user-scope.md", "削除済みディレクトリを対象とする rule"),
    (".claude/skills/_archived/", "プロファイル選定で外れた skill の退避先"),
    (".claude/agents/_archived/", "同上（subagent）"),
    (".claude/commands/_archived/", "同上（command）"),
    ("docs/CLAUDE_CODE_BEST_PRACTICES.md", "テンプレート解説。原本はテンプレートリポジトリにある"),
    ("docs/CODING_STYLE_GUIDE.md", "同上"),
    ("docs/JAPANESE_WRITING_GUIDE.md", "同上"),
    ("docs/NOTION_FEATURE_OVERVIEW.md", "同上"),
    # 解説資料 HTML はミラーへ集約したので普段は不在。移行前のコピーに残っていても消せるよう
    # 列挙は保つ（存在しないパスは読み飛ばされる）
    ("docs/NOTION_FEATURE_OVERVIEW.html", "同上"),
    ("docs/PROJECT_OVERVIEW.html", "同上"),
    ("docs/PLUGIN_INSTALL_GUIDE.md", "同上"),
    ("docs/PLUGIN_INSTALL_SCOPE.md", "同上"),
    ("docs/PROJECT_PROFILES.md", "同上"),
    ("docs/_archived/", "役目を終えたテンプレート文書の退避先"),
    (".claude/scripts/detemplate.py", "このスクリプト自身。最後に消す"),
    (".template-origin", "テンプレート本体を示すマーカー。派生プロジェクトには不要"),
)


def is_template_origin() -> bool:
    """今いるのがテンプレート本体か。マーカーの有無だけでは判定できない。

    マーカーは git 追跡下にあるので、`cp -r` でも `git clone` でもコピー先に付いてくる。
    存在だけを見るとすべてのコピーで初期化が止まってしまう。そこでマーカーに記録した
    ディレクトリ名と実際のディレクトリ名を突き合わせる。テンプレートは別名へコピーして
    使う前提であり、名前が変わっていればそれは派生プロジェクトである。

    絶対パスではなくディレクトリ名で照合するのは、マシン固有のパスをリポジトリに
    残さないためである。
    """
    if not TEMPLATE_ORIGIN_MARKER.exists():
        return False
    match = TEMPLATE_ORIGIN_NAME_RE.search(TEMPLATE_ORIGIN_MARKER.read_text(encoding="utf-8"))
    if match is None:
        # 名前を読めないマーカーは安全側に倒して本体扱いにする。
        return True
    return match.group(1) == PROJECT_ROOT.name


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _is_git_repo() -> bool:
    return _git("rev-parse", "--is-inside-work-tree").returncode == 0


def compute_plan() -> dict:
    """削除対象のうち実在するものを列挙する。読取専用。"""
    targets = []
    for rel, reason in DELETE_TARGETS:
        path = PROJECT_ROOT / rel.rstrip("/")
        if not path.exists():
            continue
        targets.append(
            {
                "path": rel,
                "kind": "dir" if path.is_dir() else "file",
                "reason": reason,
            }
        )
    return {
        "template_origin": is_template_origin(),
        "git_repo": _is_git_repo(),
        "targets": targets,
        "count": len(targets),
    }


def apply_plan(plan: dict) -> dict:
    """削除を実行する。git 管理下ならインデックスから外してから実体を消す。"""
    use_git = plan["git_repo"]
    removed: list[str] = []
    failed: list[dict] = []
    for target in plan["targets"]:
        rel = target["path"]
        path = PROJECT_ROOT / rel.rstrip("/")
        if not path.exists():
            # --apply を 2 回走らせても落ちないようにする。
            continue
        if use_git:
            # 追跡外のパスでは失敗するが、その場合も実体の削除は続ける。
            _git("rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "--", rel.rstrip("/"))
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            failed.append({"path": rel, "error": str(exc)})
            continue
        removed.append(rel)
    return {"removed": removed, "failed": failed, "count": len(removed)}


def rebuild_catalog() -> dict:
    """削除で無効になった docs/CATALOG.html を作り直す。

    削除対象にはカタログが追跡するコマンドと `_archived/` が含まれるので、消しただけでは
    HTML が実体とずれる。hooks は Claude Code の Write / Edit でしか発火せず、Python からの
    削除では動かないため、ここで明示的に呼ぶ。呼び出し側の手順に委ねると忘れられる。
    """
    script = Path(__file__).resolve().parent / "build_catalog.py"
    if not script.exists():
        return {"ok": False, "detail": "build_catalog.py が無い"}
    proc = subprocess.run(
        [sys.executable, str(script), "--quiet"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "detail": (proc.stderr or proc.stdout).strip()[:200]}
    return {"ok": True, "detail": "docs/CATALOG.html を再生成"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="削除対象を JSON で列挙する（書込なし）")
    mode.add_argument("--apply", action="store_true", help="削除を実行する")
    ap.add_argument(
        "--force-here",
        action="store_true",
        help=".template-origin があっても実行する。テンプレート本体を壊すので通常は使わない",
    )
    args = ap.parse_args()

    plan = compute_plan()

    if is_template_origin() and not args.force_here:
        print(
            "error: .template-origin を検出しました。ここはテンプレート本体のリポジトリです。\n"
            "       脱テンプレート化はコピーしてから実行してください:\n"
            "         cp -r . ../my-project && cd ../my-project\n"
            "       どうしてもここで実行する場合は --force-here を付けてください。",
            file=sys.stderr,
        )
        return 2

    if args.plan:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    result = apply_plan(plan)
    catalog = rebuild_catalog()
    print(
        json.dumps(
            {**result, "git_repo": plan["git_repo"], "catalog": catalog},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

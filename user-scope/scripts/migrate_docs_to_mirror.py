"""各プロジェクトの docs/ にある解説資料をミラーへ集約する。

同じ資料が複数のリポジトリに複製され、どれが最新か分からなくなっていた
（BrainProducts.html が 5 箇所、ANALYSIS.html と PROTOCOL.html が 3 箇所ずつ）。
原文を ~/.notion-mirror/_md/、清書版を ~/.notion-mirror/_html/ の 1 箇所へ寄せる。

  <project>/docs/<name>.md    -> _md/<project>/docs/<name>.md
  <project>/docs/<name>.html  -> _html/ の対応する清書版へ集約（同一なら元を消すだけ）

docs/ に残すのはテンプレート基盤だけである。CATALOG.md / CATALOG.html は
/catalog-sync・/doctor・/init-project・apply_profile.py が参照し、テンプレート解説の
Markdown は detemplate.py が初期化時の削除対象として管理しているため、動かすと壊れる。

Usage:
  python3 migrate_docs_to_mirror.py                      # 計画を表示（既定・書き込みなし）
  python3 migrate_docs_to_mirror.py --apply              # 実行
  python3 migrate_docs_to_mirror.py --include-dir ~/Documents/Tips
                                                         # Repository 以外も対象に加える

git 管理下のファイルは `git rm` で削除をステージするに留める。コミットはしない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config_dir import config_dir, mirror_dir, repository_dir, source_root  # noqa: E402

# docs/ に残すもの。テンプレート基盤であり、移すとツールの参照が壊れる
KEEP = {
    "CATALOG.md",
    "CATALOG.html",
    "CLAUDE_CODE_BEST_PRACTICES.md",
    "CODING_STYLE_GUIDE.md",
    "JAPANESE_WRITING_GUIDE.md",
    "NOTION_FEATURE_OVERVIEW.md",
    "PLUGIN_INSTALL_GUIDE.md",
    "PLUGIN_INSTALL_SCOPE.md",
    "PROJECT_PROFILES.md",
}
UNSORTED = "_unsorted"
# 走査しないサブツリー。退避先と、Superpowers がリポジトリ内で管理する作業成果物
SKIP_DIRS = {"_archived", "superpowers"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def html_map() -> dict[str, str]:
    """overrides.json の `<project>/docs/<name>.md` -> `_html/...` 対応を読む。"""
    path = config_dir() / "scripts" / "notion_docs_ingest" / "overrides.json"
    if not path.is_file():
        return {}
    overrides = json.loads(path.read_text(encoding="utf-8"))
    return {key: value["html"] for key, value in overrides.items() if value.get("html")}


def find_mirror_html(name: str, mapping: dict[str, str]) -> Path | None:
    """清書版の既存パスを探す。overrides.json の指定を優先し、無ければ同名を探す。"""
    mirror = mirror_dir()
    for source, target in mapping.items():
        if Path(source).stem == Path(name).stem:
            candidate = mirror / target
            if candidate.is_file():
                return candidate
    matches = sorted((mirror / "_html").rglob(name))
    return matches[0] if matches else None


def wanted(path: Path) -> bool:
    return path.is_file() and path.suffix in (".md", ".html") and path.name not in KEEP


def scan(repository: Path, extra: list[Path]) -> list[tuple[Path, str]]:
    """走査して (実体, `<project>/docs/<name>` 形式のキー) を返す。

    Repository 配下は各プロジェクトの docs/ を再帰的に、それ以外のディレクトリは
    直下だけを見る。後者を再帰させると無関係なリポジトリの README まで巻き込む。
    """
    found: list[tuple[Path, str]] = []
    for docs in sorted(repository.glob("*/docs")):
        for path in sorted(docs.rglob("*")):
            if not wanted(path) or SKIP_DIRS & set(path.parts):
                continue
            found.append((path, path.relative_to(repository).as_posix()))
    for root in extra:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*")):
            if not wanted(path):
                continue
            found.append((path, f"{root.name}/{path.name}"))
    return found


def plan_for(path: Path, key: str, mapping: dict[str, str]) -> dict:
    """1 ファイルの移送計画。action は move / delete / conflict のいずれか。"""
    if path.suffix == ".md":
        return {"src": path, "key": key, "action": "move", "dst": source_root() / key}

    existing = find_mirror_html(path.name, mapping)
    if existing is None:
        project = key.split("/", 1)[0]
        target = mirror_dir() / "_html" / UNSORTED / project / path.name
        return {"src": path, "key": key, "action": "move", "dst": target}
    if digest(existing) == digest(path):
        return {"src": path, "key": key, "action": "delete", "dst": existing}
    return {"src": path, "key": key, "action": "conflict", "dst": existing}


GITIGNORE = """\
# 同期が書く領域は notion_sync.py --full でいつでも取り直せるので追跡しない。
# 追跡するのは再生成できない _md/（原文）と、その清書版 _html/ だけ。
/*
!/.gitignore
!/_md/
!/_html/
"""


def ensure_mirror_repo() -> None:
    """ミラーを git 管理下に置く。_md/ に原本が入る以上、消えたら取り戻せないため。"""
    mirror = mirror_dir()
    mirror.mkdir(parents=True, exist_ok=True)
    ignore = mirror / ".gitignore"
    if not ignore.is_file():
        ignore.write_text(GITIGNORE, encoding="utf-8")
        print(f"{ignore} を作成")
    if (mirror / ".git").is_dir():
        return
    subprocess.run(["git", "-C", str(mirror), "init", "--quiet"], check=True)
    print(f"{mirror} を git リポジトリにした（_md/ と _html/ だけを追跡）")


def remove(path: Path) -> str:
    """git 管理下なら削除をステージし、そうでなければ単に消す。コミットはしない。"""
    result = subprocess.run(
        ["git", "-C", str(path.parent), "rm", "-f", "--quiet", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "git rm"
    path.unlink()
    return "unlink"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="実際に移動する（既定は計画表示のみ）")
    parser.add_argument("--include-dir", action="append", default=[], help="Repository 以外に走査するディレクトリ")
    args = parser.parse_args()

    mapping = html_map()
    found = scan(repository_dir(), [Path(d).expanduser() for d in args.include_dir])
    plans = [plan_for(path, key, mapping) for path, key in found]
    if not plans:
        print("対象なし")
        return

    width = max(len(p["key"]) for p in plans)
    captions = (
        ("move", "移す"),
        ("delete", "ミラーに同一のものがあるので元を消す"),
        ("conflict", "内容が違う。手で確認する"),
    )
    for kind, caption in captions:
        group = [p for p in plans if p["action"] == kind]
        if not group:
            continue
        print(f"\n[{caption}] {len(group)} 件")
        for item in group:
            destination = item["dst"]
            try:
                shown = destination.relative_to(mirror_dir()).as_posix()
            except ValueError:
                shown = str(destination)
            print(f"  {item['key']:<{width}}  ->  {shown}")

    if not args.apply:
        print("\n計画のみ。実行するには --apply を付ける")
        return

    ensure_mirror_repo()
    moved = deleted = 0
    for item in plans:
        if item["action"] == "conflict":
            continue
        if item["action"] == "move":
            item["dst"].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item["src"], item["dst"])
            moved += 1
        else:
            deleted += 1
        remove(item["src"])
    conflicts = sum(1 for p in plans if p["action"] == "conflict")
    print(f"\n移動 {moved} 件 / 削除 {deleted} 件 / 保留 {conflicts} 件")
    print("各リポジトリで git status を確認してからコミットすること（本スクリプトはコミットしない）")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""user-scope/ の資産を Claude Code の設定ディレクトリへ配置する。

原本は本リポジトリの user-scope/ にあり、設定ディレクトリ（macOS/Linux は
~/.claude、Windows は %USERPROFILE%\.claude）は配置先＝派生物である。逆方向の
同期は行わない。書き手を 1 方向に保ち、どちらが正かの曖昧さを構造的に排除する。

setup-user-scope.sh から呼ばれる。ファイル操作と JSON マージをすべて Python 側に
寄せているのは、bash の挙動差（GNU/BSD/Git Bash）を跨がないようにするため。

  python3 user_scope_sync.py apply [--link]
  python3 user_scope_sync.py check          # dry-run。実行予定を出すだけ
  python3 user_scope_sync.py diff           # drift 検出のみ。drift ありで exit 2
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置対象。ディレクトリはツリーごと、ファイルは単体で配置する。
ASSET_DIRS = ("skills", "agents", "commands", "scripts")
ASSET_FILES = ("statusline.sh",)

# 配置時に持ち込まない派生物。user-scope/.gitignore と同じ意図。
EXCLUDE_NAMES = frozenset({"__pycache__", ".DS_Store", ".env", "ingest_state.json"})
EXCLUDE_SUFFIXES = (".pyc",)

# 配置スクリプトが決して触らない領域。運用データと秘匿情報。
PROTECTED = ("plugins", "projects", "sessions", "history.jsonl", ".env", "settings.local.json")

DRIFT_EXIT_CODE = 2

# 上書き前の退避を何世代残すか。冪等な導入スクリプトなので上限が要る。
BACKUP_GENERATIONS = 5

# 設定ディレクトリの解決と秘匿情報の検査は _catalog_common が持つ。派生プロジェクトには
# 本モジュールが無く _catalog_common だけがあるため、共有できる側へ置いている。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _catalog_common import (  # noqa: E402
    audit_secrets,
    is_windows,
    resolve_config_dir,
    resolve_legacy_json,
)

# --- 環境の解決 -------------------------------------------------------------


def to_native_path(path: Path) -> str:
    """絶対パスを OS ネイティブ表記の文字列へ変換する（Windows は cygpath -w を使う）。

    MSYS Python は /c/Users/... 形式を返すため、Windows 環境の絶対パス表記を得る
    中間ステップとして使う。シェルへ渡せる形にするのは to_shell_arg() の役目。
    """
    absolute = str(path.resolve())
    if sys.platform in ("msys", "cygwin") and shutil.which("cygpath"):
        try:
            return subprocess.run(
                ["cygpath", "-w", absolute], capture_output=True, text=True, check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            pass
    return absolute


def to_shell_arg(path: Path) -> str:
    r"""statusLine.command に埋め込む、シェル引数として安全な絶対パス文字列を返す。

    command を解釈するのは Claude Code 本体ではなく bash 自身（"bash <path>"）。
    Windows のバックスラッシュ区切りは bash のエスケープとして食われて経路が壊れる
    （例: C:\\Users\\keita\\... → C:Userskeita...、無音で statusLine が消える）ため、
    区切りを / に正規化する。ユーザー名に空白を含む環境（C:\\Users\\John Smith\\...）
    では正規化だけでは引数が分割されて壊れるので、二重引用符で囲む。
    """
    normalized = to_native_path(path).replace("\\", "/")
    return '"{}"'.format(normalized)


# --- ファイル配置 -----------------------------------------------------------


def is_excluded(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES or path.name.endswith(EXCLUDE_SUFFIXES):
        return True
    return any(part in EXCLUDE_NAMES for part in path.parts)


def iter_source_files(root: Path):
    """配置対象の実ファイルを (絶対パス, root からの相対パス) で列挙する。"""
    for name in ASSET_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and not is_excluded(path.relative_to(root)):
                yield path, path.relative_to(root)
    for name in ASSET_FILES:
        path = root / name
        if path.is_file():
            yield path, Path(name)


def compute_drift(src_root: Path, dest_root: Path) -> tuple[list[str], list[str], list[str]]:
    """(不足, 内容差分, 余剰) を返す。余剰は配置対象ツリー内の孤児のみ数える。"""
    missing, changed = [], []
    expected: set[Path] = set()
    for src, rel in iter_source_files(src_root):
        expected.add(rel)
        dest = dest_root / rel
        if not dest.exists():
            missing.append(str(rel))
        elif not filecmp.cmp(src, dest, shallow=False):
            changed.append(str(rel))

    orphaned = []
    for name in ASSET_DIRS:
        base = dest_root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(dest_root)
            if is_excluded(rel):
                continue
            if rel not in expected:
                orphaned.append(str(rel))
    return missing, changed, orphaned


def copy_tree(src: Path, dest: Path) -> None:
    ignore = shutil.ignore_patterns(*EXCLUDE_NAMES, "*.pyc")
    shutil.copytree(src, dest, ignore=ignore, dirs_exist_ok=True)


def prune_backups(backups_root: Path, keep: int = BACKUP_GENERATIONS) -> list[str]:
    """古い退避世代を削除して keep 世代に収める。

    本スクリプトは冪等で何度でも実行される前提なので、上限を設けないと実行のたびに
    数百 KB ずつディスクを食い続ける。世代名はタイムスタンプなので名前順＝新しい順。
    """
    if not backups_root.is_dir():
        return []
    generations = sorted((p for p in backups_root.iterdir() if p.is_dir()), reverse=True)
    removed = []
    for stale in generations[keep:]:
        shutil.rmtree(stale, ignore_errors=True)
        removed.append(stale.name)
    return removed


def backup_existing(dest_root: Path, names: list[str], stamp: str) -> Path | None:
    """上書き前の退避。復旧の起点になるので、退避してから消す順序を崩さない。"""
    targets = [n for n in names if (dest_root / n).exists()]
    if not targets:
        return None
    backup_dir = dest_root / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in targets:
        source = dest_root / name
        if source.is_dir():
            copy_tree(source, backup_dir / name)
        else:
            shutil.copy2(source, backup_dir / name)
    pruned = prune_backups(backup_dir.parent)
    if pruned:
        print(f"  退避の古い世代を削除: {len(pruned)} 件")
    return backup_dir


def place_assets(src_root: Path, dest_root: Path, use_link: bool, dry_run: bool) -> None:
    names = list(ASSET_DIRS) + list(ASSET_FILES)
    if dry_run:
        for name in names:
            verb = "symlink" if use_link else "copy"
            print(f"  [dry-run] {verb} user-scope/{name} -> {dest_root / name}")
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_existing(dest_root, names, stamp)
    if backup_dir:
        print(f"  退避: {backup_dir}")

    for name in names:
        src = src_root / name
        if not src.exists():
            continue
        dest = dest_root / name
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)

        if use_link:
            dest.symlink_to(src.resolve(), target_is_directory=src.is_dir())
            print(f"  + symlink {name} -> {src}")
        elif src.is_dir():
            copy_tree(src, dest)
            print(f"  + copy {name}/")
        else:
            shutil.copy2(src, dest)
            dest.chmod(0o755)
            print(f"  + copy {name}")

    # copy2 は実行ビットを保つが、symlink 経由や Windows 由来だと落ちることがある。
    if not use_link and not is_windows():
        for path in (dest_root / "scripts").rglob("*.sh"):
            path.chmod(0o755)


# --- JSON マージ ------------------------------------------------------------


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as error:
        raise SystemExit(f"error: {path} が JSON として壊れている: {error}")


def write_json(path: Path, data: dict, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"  + write {path}")


def strip_comments(data: dict) -> dict:
    """`_comment` など下線始まりのキーは原本の注釈であり、配置先へは持ち込まない。"""
    return {k: v for k, v in data.items() if not k.startswith("_")}


def merge_settings(src_root: Path, config_dir: Path, dry_run: bool) -> None:
    """settings.user.json のキーだけを既存 settings.json へ差し込む。

    enabledPlugins と extraKnownMarketplaces は setup-plugins.sh
    （claude plugin enable/disable）の管理領域なので、読まず・書かず・消さない。
    """
    template = strip_comments(load_json(src_root / "settings.user.json"))
    if not template:
        return
    dest_path = config_dir / "settings.json"
    merged = load_json(dest_path)

    for key, value in template.items():
        if key == "permissions":
            current = merged.setdefault("permissions", {})
            for rule_kind in ("allow", "ask", "deny"):
                if rule_kind not in value:
                    continue
                # マシン固有に足された許可を消さないよう和集合を取る。
                existing = current.get(rule_kind, [])
                current[rule_kind] = existing + [r for r in value[rule_kind] if r not in existing]
            if "defaultMode" in value:
                current["defaultMode"] = value["defaultMode"]
        elif key == "statusLine":
            resolved = dict(value)
            command = resolved.get("command", "")
            resolved["command"] = command.replace("__STATUSLINE_SH__", to_shell_arg(config_dir / "statusline.sh"))
            merged["statusLine"] = resolved
        else:
            merged[key] = value

    write_json(dest_path, merged, dry_run)


def merge_mcp_servers(src_root: Path, config_dir: Path, dry_run: bool) -> None:
    """user scope の MCP 定義を .claude.json へ差し込む。他のキーには触れない。"""
    template = strip_comments(load_json(src_root / "mcp-servers.user.json"))
    servers = template.get("mcpServers", {})
    if not servers:
        return
    dest_path = resolve_legacy_json(config_dir)
    merged = load_json(dest_path)
    existing = merged.setdefault("mcpServers", {})
    for name, definition in servers.items():
        existing[name] = definition
    write_json(dest_path, merged, dry_run)


# --- エントリポイント -------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("apply", "check", "diff"))
    parser.add_argument("--link", action="store_true", help="copy ではなく symlink で配置する")
    parser.add_argument("--source", required=True, help="user-scope/ の絶対パス")
    args = parser.parse_args()

    src_root = Path(args.source)
    if not src_root.is_dir():
        raise SystemExit(f"error: source not found: {src_root}")
    config_dir = resolve_config_dir()

    if args.mode == "diff":
        missing, changed, orphaned = compute_drift(src_root, config_dir)
        if not (missing or changed or orphaned):
            print(f"drift なし: {config_dir}")
            return 0
        print(f"drift あり: {config_dir}")
        for label, items in (("未配置", missing), ("内容差分", changed), ("孤児", orphaned)):
            for item in items:
                print(f"  [{label}] {item}")
        return DRIFT_EXIT_CODE

    dry_run = args.mode == "check"
    use_link = args.link and not is_windows()
    if args.link and is_windows():
        print("警告: Windows では symlink に開発者モード/管理者権限が要るため copy で配置する")

    print(f"== 配置先: {config_dir} ==")
    if not dry_run:
        config_dir.mkdir(parents=True, exist_ok=True)

    print("== 1. 資産の配置 ==")
    place_assets(src_root, config_dir, use_link, dry_run)

    print("== 2. settings.json のマージ（enabledPlugins は保全） ==")
    merge_settings(src_root, config_dir, dry_run)

    print("== 3. user scope MCP の登録 ==")
    merge_mcp_servers(src_root, config_dir, dry_run)

    print(f"== 4. 保全した領域（未変更）: {', '.join(PROTECTED)} ==")

    if not dry_run:
        leaked = audit_secrets(config_dir)
        if leaked:
            print("警告: 設定ファイルに実トークンらしき文字列がある。")
            for path in leaked:
                print(f"  {path}")
            print("  値は .env / settings.local.json へ移し、設定には ${VAR} 参照を書くこと。")

    env_file = config_dir / ".env"
    if not env_file.exists():
        print(f"次の手順: cp user-scope/.env.example {env_file} して実値を埋める")
    if is_windows():
        print("注意: 日次/週次の自動記録（launchd）は macOS 限定。/notion-digest の手動実行は両対応。")
    else:
        print(f"任意: bash {config_dir}/scripts/install_notion_digest_launchd.sh で自動記録を登録できる")
    return 0


if __name__ == "__main__":
    sys.exit(main())

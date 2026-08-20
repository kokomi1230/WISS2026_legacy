#!/usr/bin/env python3
"""テンプレ環境の健全性診断。/doctor と /init-project のプリフライトが共有する。

チェックを Markdown の heredoc ではなくコードとして持つのは、テストできること・
複数のコマンドから同じ判定を再利用できることの 2 点が理由である。

  python3 doctor.py               # 人間向けレポート（全チェック）
  python3 doctor.py --preflight   # 導入判定のみ（/init-project のステップ 0）
  python3 doctor.py --json        # 機械可読

終了コード: 0 = clean / 1 = warning のみ / 2 = blocking あり
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _catalog_common import (  # noqa: E402
    LOCK_PATH,
    PROJECT_ROOT,
    audit_secrets,
    parse_frontmatter,
    resolve_config_dir,
    resolve_legacy_json,
)

# user_scope_sync は原本を配置するエンジンで、テンプレートリポジトリにしか無い。
# テンプレートから派生したプロジェクトでも doctor は動く必要があるので、
# 依存する検査（user-scope の配置 drift）だけを条件付きにする。
try:
    from user_scope_sync import compute_drift  # noqa: E402
except ImportError:
    compute_drift = None

CRITICAL, MAJOR, MINOR, INFO = "critical", "major", "minor", "info"
# critical / major は作業を止めるべき水準。minor / info は報告のみ。
BLOCKING_LEVELS = (CRITICAL, MAJOR)

SETTINGS = PROJECT_ROOT / ".claude" / "settings.json"
SETTINGS_LOCAL = PROJECT_ROOT / ".claude" / "settings.local.json"
MCP_JSON = PROJECT_ROOT / ".mcp.json"
PROFILES_DIR = PROJECT_ROOT / ".claude" / "profiles"
USER_SCOPE_SRC = PROJECT_ROOT / "user-scope"
PLUGINS_MANIFEST = PROJECT_ROOT / ".claude" / "plugins-user-scope.json"
KIND_DIRS = ("skills", "agents", "commands")

# Markdown の相対リンク。http(s)・アンカー・mailto は対象外。
MD_LINK_RE = re.compile(r"\[[^\]]*\]\((?!https?://|#|mailto:)([^)\s]+)\)")
# コードブロックの開始 / 終了。記号の種類と長さを捕まえる。
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def outside_fences(text: str):
    """コードブロックの外側の行だけを返す。

    コード例に書いた `[X](X)` を実在しないリンクとして数えると、書き方の見本を
    載せているだけのドキュメントが軒並み誤検出される。
    閉じ記号は開始と同じ種類で同じ長さ以上でなければならない。そうしないと
    ````markdown の中に ```bash を入れ子にした見本で開閉がずれる。
    """
    opener = ""
    for line in text.splitlines():
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
            yield line


class Result:
    """1 チェックの結果。level は問題があるときのみ意味を持つ。"""

    def __init__(self, name: str, ok: bool, level: str, detail: str, hint: str = ""):
        """hint は修復コマンド。ok=True のときは空にする。"""
        self.name = name
        self.ok = ok
        self.level = level
        self.detail = detail
        self.hint = hint

    def as_dict(self) -> dict:
        """--json 出力用のプレーンな dict へ変換する。"""
        return {
            "name": self.name,
            "ok": self.ok,
            "level": self.level,
            "detail": self.detail,
            "hint": self.hint,
        }


def ok(name: str, detail: str) -> Result:
    return Result(name, True, INFO, detail)


def ng(name: str, level: str, detail: str, hint: str = "") -> Result:
    return Result(name, False, level, detail, hint)


def is_template_repo() -> bool:
    """テンプレート運用の資産が残っているか。

    /init-project の脱テンプレート化を通した派生プロジェクトでは .claude/profiles/ ごと
    消える。プロファイル・原本・導入マニフェストを前提にする検査は、そこでは「未対応」
    ではなく「対象外」なので、FAIL ではなく情報として扱う。
    """
    return PROFILES_DIR.is_dir()


def load_json(path: Path):
    """(データ, エラー文字列) を返す。存在しなければ (None, None)。"""
    if not path.exists():
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as error:
        return None, str(error)


# --- 導入判定（プリフライトと全体診断で共有） -------------------------------


def check_settings_syntax() -> Result:
    data, error = load_json(SETTINGS)
    if error:
        return ng("settings.json 構文", CRITICAL, error, "JSON を修正する")
    if data is None:
        return ng("settings.json 構文", MAJOR, "ファイルが無い", "/init-project で生成する")
    return ok("settings.json 構文", f"enabledPlugins {len(data.get('enabledPlugins', {}))} 件")


def check_claude_cli() -> Result:
    if shutil.which("claude"):
        return ok("claude CLI", "PATH に在る")
    return ng(
        "claude CLI",
        MAJOR,
        "PATH に見つからない",
        "Claude Code をインストールする（setup-plugins.sh が動かない）",
    )


def check_node() -> Result:
    missing = [c for c in ("node", "npx") if not shutil.which(c)]
    if not missing:
        return ok("node / npx", "両方在る")
    return ng(
        "node / npx",
        MINOR,
        f"未検出: {', '.join(missing)}",
        "Node.js 18+ を入れる（生 MCP: unity / figma / notion が起動できない）",
    )


def check_user_scope_deployed() -> Result:
    """原本 user-scope/ と配置先の drift を見る。

    原本を持つのはテンプレートリポジトリだけなので、派生プロジェクトでは検査対象外に
    なる（配置の責任はテンプレート側にある）。
    """
    config_dir = resolve_config_dir()
    if not USER_SCOPE_SRC.is_dir() or compute_drift is None:
        return ok("user-scope 配置", "対象外（原本はテンプレートリポジトリが持つ）")
    missing, changed, orphaned = compute_drift(USER_SCOPE_SRC, config_dir)
    if not (missing or changed or orphaned):
        return ok("user-scope 配置", f"drift なし（{config_dir}）")
    parts = []
    if missing:
        parts.append(f"未配置 {len(missing)}")
    if changed:
        parts.append(f"内容差分 {len(changed)}")
    if orphaned:
        parts.append(f"孤児 {len(orphaned)}")
    return ng(
        "user-scope 配置",
        MAJOR,
        " / ".join(parts),
        "bash .claude/scripts/setup-user-scope.sh",
    )


def check_plugins_installed() -> Result:
    """マニフェストの core+extra が user scope に install 済みかを見る。"""
    manifest, error = load_json(PLUGINS_MANIFEST)
    if manifest is None and not error and not is_template_repo():
        return ok("plugin 導入", "対象外（マニフェストはテンプレートリポジトリが持つ）")
    if error or manifest is None:
        return ng("plugin 導入", MINOR, "マニフェストを読めない", str(error or "ファイルが無い"))
    expected = set(manifest.get("core") or []) | set(manifest.get("extra") or [])
    if not expected:
        return ok("plugin 導入", "マニフェストが空")

    installed_path = resolve_config_dir() / "plugins" / "installed_plugins.json"
    data, error = load_json(installed_path)
    if error or data is None:
        return ng(
            "plugin 導入",
            MAJOR,
            f"{len(expected)} 件すべて未 install",
            "bash .claude/scripts/setup-plugins.sh",
        )
    # 1 プラグインは複数スコープに install され得るので、user scope の記録だけを拾う。
    user_scoped = {
        key
        for key, records in (data.get("plugins") or {}).items()
        if any(r.get("scope") == "user" for r in records or [])
    }
    missing = sorted(expected - user_scoped)
    if not missing:
        return ok("plugin 導入", f"user scope に {len(expected)} 件")
    return ng(
        "plugin 導入",
        MAJOR,
        f"未 install {len(missing)} / {len(expected)} 件（例: {', '.join(missing[:3])}）",
        "bash .claude/scripts/setup-plugins.sh",
    )


def check_env_file() -> Result:
    env_file = resolve_config_dir() / ".env"
    if env_file.exists():
        return ok(".env", str(env_file))
    origin = "user-scope/.env.example" if is_template_repo() else "テンプレートリポジトリの user-scope/.env.example"
    hint = f"cp {origin} <上記パス> して実値を埋める（Notion 系のみ影響）"
    return ng(".env", MINOR, f"{env_file} が無い", hint)


PREFLIGHT_CHECKS = (
    check_settings_syntax,
    check_claude_cli,
    check_user_scope_deployed,
    check_plugins_installed,
    check_node,
    check_env_file,
)


# --- 全体診断のみのチェック -------------------------------------------------


def check_catalog_lock() -> Result:
    """残置した .catalog-sync-lock を検出する。

    build_catalog.py はロック保持中に呼ばれると何もせず 0 を返す（自己再帰ガード）。
    そのためロックが残っていると PostToolUse hook が黙って動かなくなり、drift 判定も
    「最新」と誤報告する。ロックの有無は独立したチェックにする必要がある。
    """
    if LOCK_PATH.exists():
        return ng(
            "catalog ロック",
            MAJOR,
            f"残置ロックあり: {LOCK_PATH}",
            "/catalog-sync（hook が停止し drift 判定も無効になっている）",
        )
    return ok("catalog ロック", "なし")


def check_catalog_drift() -> Result:
    """build_catalog.py の --check を import 経由で走らせる（サブプロセス不要）。"""
    if LOCK_PATH.exists():
        # ロック保持中は build_catalog が即 return 0 するため、判定そのものが無効。
        return ng("catalog drift", MAJOR, "残置ロックのため判定不能", "/catalog-sync")
    try:
        import build_catalog
    except Exception as error:  # noqa: BLE001 - 起動不能そのものを報告したい
        return ng("catalog drift", MAJOR, f"build_catalog を import できない: {error}")
    argv = sys.argv
    sys.argv = ["build_catalog.py", "--check", "--quiet"]
    try:
        rc = build_catalog.main()
    except SystemExit as error:
        rc = error.code if isinstance(error.code, int) else 1
    finally:
        sys.argv = argv
    if rc == 0:
        return ok("catalog drift", "HTML は最新")
    return ng("catalog drift", MAJOR, f"drift あり（exit={rc}）", "/catalog-sync")


def check_settings_local() -> Result:
    _, error = load_json(SETTINGS_LOCAL)
    if error:
        return ng("settings.local.json 構文", MAJOR, error, "JSON を修正する")
    return ok("settings.local.json 構文", "OK" if SETTINGS_LOCAL.exists() else "未使用")


def check_plugin_key_format() -> Result:
    data, _ = load_json(SETTINGS)
    keys = list((data or {}).get("enabledPlugins", {}))
    bad = [k for k in keys if not re.match(r"^[A-Za-z0-9_-]+@[A-Za-z0-9_./()-]+$", k)]
    if bad:
        return ng("enabledPlugins キー形式", MAJOR, ", ".join(bad), "name@marketplace 形式へ直す")
    return ok("enabledPlugins キー形式", f"{len(keys)} 件すべて妥当")


def check_archived_overlap() -> Result:
    overlaps = []
    for kind in KIND_DIRS:
        root = PROJECT_ROOT / ".claude" / kind
        archived = root / "_archived"
        if not archived.is_dir():
            continue
        for path in archived.rglob("*.md"):
            if (root / path.relative_to(archived)).exists():
                overlaps.append(f"{kind}/{path.relative_to(archived)}")
    if overlaps:
        return ng("archived 重複", MAJOR, ", ".join(overlaps[:5]), "片方を削除する")
    return ok("archived 重複", "なし")


def check_mcp_env() -> Result:
    data, error = load_json(MCP_JSON)
    if error:
        return ng(".mcp.json 構文", MAJOR, error)
    if data is None:
        return ok(".mcp.json", "未使用")
    referenced: set[str] = set()
    for server in (data.get("mcpServers") or {}).values():
        for value in (server.get("env") or {}).values():
            referenced |= set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)\}", str(value)))
        for arg in server.get("args") or []:
            referenced |= set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)\}", str(arg)))
    present = set(os.environ)
    for env_file in (PROJECT_ROOT / ".env", resolve_config_dir() / ".env"):
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line and not line.startswith("#"):
                    present.add(line.split("=", 1)[0].strip())
    missing = sorted(referenced - present)
    if missing:
        return ng(".mcp.json 参照 env", MINOR, ", ".join(missing), ".env に追記する")
    return ok(".mcp.json 参照 env", f"参照 {len(referenced)} 件すべて解決")


def check_profile_frontmatter() -> Result:
    if not is_template_repo():
        return ok("profile frontmatter", "対象外（プロファイルはテンプレートリポジトリが持つ）")
    bad = []
    for path in sorted(PROFILES_DIR.glob("*.md")):
        if path.stem.startswith("_"):
            continue
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not isinstance(meta.get("enabled_plugins"), list):
            bad.append(path.name)
    if bad:
        return ng("profile frontmatter", MAJOR, ", ".join(bad), "enabled_plugins を YAML list にする")
    return ok("profile frontmatter", f"{len(list(PROFILES_DIR.glob('*.md')))} 件すべて妥当")


def check_hook_scripts() -> Result:
    data, _ = load_json(SETTINGS)
    missing = []
    for event in ("PreToolUse", "PostToolUse"):
        for matcher in (data or {}).get("hooks", {}).get(event, []):
            for hook in matcher.get("hooks", []):
                command = hook.get("command", "")
                match = re.search(r"\$\{CLAUDE_PROJECT_DIR\}/(\S+)", command)
                if match and not (PROJECT_ROOT / match.group(1)).exists():
                    missing.append(match.group(1))
    if missing:
        return ng("hooks スクリプト", MINOR, ", ".join(missing), "パスを直すか設定から外す")
    return ok("hooks スクリプト", "すべて実在")


def check_secrets_inline() -> Result:
    config_dir = resolve_config_dir()
    leaked = audit_secrets(config_dir)
    if leaked:
        return ng(
            "秘匿情報の直書き",
            CRITICAL,
            ", ".join(leaked),
            "値を settings.local.json の env へ移し ${VAR} 参照にする。露出したトークンは失効・再発行",
        )
    return ok("秘匿情報の直書き", f"{config_dir / 'settings.json'} / {resolve_legacy_json(config_dir).name} とも clean")


def check_statusline() -> Result:
    data, _ = load_json(resolve_config_dir() / "settings.json")
    command = (data or {}).get("statusLine", {}).get("command", "")
    if not command:
        return ok("statusLine", "未設定")
    target = command.split(" ", 1)[1].strip('"') if " " in command else ""
    if target and Path(target).is_file():
        return ok("statusLine", target)
    return ng("statusLine", MINOR, f"参照先が無い: {command}", "bash .claude/scripts/setup-user-scope.sh")


def check_scope_collision() -> Result:
    config_dir = resolve_config_dir()
    collisions = []
    for kind in KIND_DIRS:
        project = {p.name for p in (PROJECT_ROOT / ".claude" / kind).glob("*") if p.name != "_archived"}
        user_dir = config_dir / kind
        user = {p.name for p in user_dir.glob("*")} if user_dir.is_dir() else set()
        collisions += [f"{kind}/{n}" for n in sorted(project & user)]
    if collisions:
        return ng(
            "スコープ間の同名衝突",
            MAJOR,
            ", ".join(collisions),
            "CLAUDE.md「アセットのスコープ方針」で置き場所を決めて片方を消す",
        )
    return ok("スコープ間の同名衝突", "なし")


def check_doc_links() -> Result:
    """追跡対象の Markdown 内の相対リンクが実在するかを見る。

    退避や改名でリンクが切れても気づけないため常設する。vendored skill は
    原典のまま保つ方針なので対象外。
    """
    roots = [
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / ".claude" / "commands",
        PROJECT_ROOT / ".claude" / "agents",
        PROJECT_ROOT / ".claude" / "rules",
        PROJECT_ROOT / "user-scope",
    ]
    files = [PROJECT_ROOT / "README.md", PROJECT_ROOT / "CLAUDE.md"]
    for root in roots:
        files += [p for p in root.rglob("*.md") if "_archived" not in p.parts]
    broken = []
    for path in files:
        if not path.exists():
            continue
        for line in outside_fences(path.read_text(encoding="utf-8", errors="replace")):
            for target in MD_LINK_RE.findall(line):
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                if not resolved.exists():
                    broken.append(f"{path.relative_to(PROJECT_ROOT)} -> {target}")
    if broken:
        return ng("ドキュメントのリンク", MAJOR, f"{len(broken)} 件切れ: " + "; ".join(broken[:5]))
    return ok("ドキュメントのリンク", f"{len(files)} ファイル走査、切れなし")


def check_project_docs() -> Result:
    """CLAUDE.md の行数と .claude/rules/ の paths: を見る。

    より詳しい検査は project-docs skill の validate_docs.py が持つが、ここからは
    呼ばない。user scope のスクリプトに実行時依存すると、未配置の環境で /doctor 自体が
    壊れる。数えるだけで済む 2 点に絞って doctor 側で完結させる。
    """
    problems = []
    level = MINOR
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if claude_md.exists():
        lines = len(claude_md.read_text(encoding="utf-8", errors="replace").splitlines())
        if lines > 250:
            problems.append(f"CLAUDE.md {lines} 行（上限 250）")
            level = MAJOR
        elif lines > 200:
            problems.append(f"CLAUDE.md {lines} 行（目標 200 未満）")

    rules_dir = PROJECT_ROOT / ".claude" / "rules"
    missing = []
    if rules_dir.is_dir():
        for path in sorted(rules_dir.rglob("*.md")):
            head = path.read_text(encoding="utf-8", errors="replace").splitlines()[:12]
            if not any(line.startswith("paths:") for line in head):
                missing.append(path.name)
    if missing:
        # paths: が無い rule は起動時に無条件ロードされ、CLAUDE.md に書くのと変わらない。
        problems.append(f"paths: 無しの rule: {', '.join(missing)}")

    if not problems:
        return ok("ドキュメント構成", "CLAUDE.md の分量と rules の paths: は妥当")
    return ng(
        "ドキュメント構成",
        level,
        " / ".join(problems),
        "/project-docs で詳細を確認する（条件付きの規約は .claude/rules/ へ移す）",
    )


# 適用済み CLAUDE.md の H1。apply_profile.patch_claude_md が書く形式と対になっている。
APPLIED_PROFILE_RE = re.compile(r"^#\s+\S.*\(([A-Za-z0-9_-]+)\)\s*$", re.MULTILINE)


def check_baseline_noop() -> Result:
    """現プロファイルの baseline が noop かどうか（情報提供のみ）。"""
    if not is_template_repo():
        return ok("baseline plan", "対象外（プロファイル適用はテンプレートリポジトリで行う）")
    try:
        import apply_profile
    except Exception as error:  # noqa: BLE001
        return ng("baseline plan", MINOR, f"apply_profile を import できない: {error}")
    text = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
    available = apply_profile.available_profiles()
    # H1 から読む。frontmatter を CLAUDE.md へ注入しなくなったため、本文中の
    # `name: <profile>` に頼ることはできない。
    match = APPLIED_PROFILE_RE.search(text)
    current = match.group(1) if match and match.group(1) in available else None
    if not current:
        return ok("baseline plan", "プロファイル未適用（初期化前）")
    plan = apply_profile.compute_plan(current)
    return ok("baseline plan", f"{current}: noop={plan.get('noop')}")


FULL_CHECKS = PREFLIGHT_CHECKS + (
    check_catalog_lock,
    check_catalog_drift,
    check_settings_local,
    check_plugin_key_format,
    check_archived_overlap,
    check_mcp_env,
    check_profile_frontmatter,
    check_hook_scripts,
    check_secrets_inline,
    check_statusline,
    check_scope_collision,
    check_doc_links,
    check_project_docs,
    check_baseline_noop,
)


# --- 実行 -------------------------------------------------------------------


def run(checks) -> list[Result]:
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as error:  # noqa: BLE001 - 1 チェックの失敗で全体を止めない
            results.append(ng(check.__name__, MAJOR, f"チェック自体が例外: {error}"))
    return results


def exit_code(results: list[Result]) -> int:
    failures = [r for r in results if not r.ok]
    if any(r.level in BLOCKING_LEVELS for r in failures):
        return 2
    return 1 if failures else 0


def report(results: list[Result], preflight: bool) -> None:
    title = "環境プリフライト" if preflight else "環境診断レポート"
    # テンプレートはコピーして使うため、名前を固定で書くとコピー先で必ず誤る
    print(f"# {title} ({PROJECT_ROOT.name})")
    print(f"設定ディレクトリ: {resolve_config_dir()}\n")

    blocking = [r for r in results if not r.ok and r.level in BLOCKING_LEVELS]
    warnings = [r for r in results if not r.ok and r.level not in BLOCKING_LEVELS]
    passed = [r for r in results if r.ok]

    if blocking:
        print(f"## 要対応 ({len(blocking)})")
        for r in blocking:
            print(f"- [{r.level}] {r.name}: {r.detail}")
            if r.hint:
                print(f"      → {r.hint}")
    if warnings:
        print(f"\n## 警告 ({len(warnings)})")
        for r in warnings:
            print(f"- [{r.level}] {r.name}: {r.detail}")
            if r.hint:
                print(f"      → {r.hint}")
    print(f"\n## OK ({len(passed)}/{len(results)})")
    for r in passed:
        print(f"- {r.name}: {r.detail}")

    if not blocking and not warnings:
        print("\nすべて clean。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # --preflight と --all は対象が違うので併用できない。黙って片方を無視すると
    # 「--all を付けたのに 6 項目しか見ていない」ことに気づけない。
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--preflight",
        action="store_true",
        help="導入判定のみ（/init-project のステップ 0 が使う）",
    )
    scope.add_argument("--all", action="store_true", help="全チェック（既定と同じ。意図の明示用）")
    parser.add_argument("--json", action="store_true", help="機械可読な JSON で出力する")
    args = parser.parse_args()

    results = run(PREFLIGHT_CHECKS if args.preflight else FULL_CHECKS)
    code = exit_code(results)

    if args.json:
        print(
            json.dumps(
                {
                    "mode": "preflight" if args.preflight else "full",
                    "config_dir": str(resolve_config_dir()),
                    "exit_code": code,
                    "results": [r.as_dict() for r in results],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        report(results, args.preflight)
    return code


if __name__ == "__main__":
    sys.exit(main())

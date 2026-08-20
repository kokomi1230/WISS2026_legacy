#!/usr/bin/env python3
"""プロジェクトプロファイルを適用する: enabledPlugins 切替・アセット退避・CLAUDE.md 書換。

CATALOG.md (docs/CATALOG.md) が profile -> asset マッピングの source of truth。
各エントリの `- profiles: <csv>` フィールドがそのエントリを使うプロファイルを宣言する。

`meta` タグ付きエントリは共通基盤とみなし、選択プロファイルに関わらず常に維持する。

モード:
  --plan              JSON プランを標準出力へ（変更なし）
  --apply             .claude/settings.json（enabledPlugins）を書き換える。
                      退避用の mv コマンドは呼び出し元（Claude Code）が Bash 経由で
                      実行できるよう JSON で返す（ユーザーの mv 許可プロンプトを維持するため）
  --write-claude-md   CLAUDE.md を書換: 境界見出しより前を選択プロファイルの MD 内容に
                      置き換える（境界は CLAUDE_MD_BOUNDARY_RE を参照）
  --scaffold          プロファイル frontmatter の scaffold: に沿ってディレクトリを作る
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _catalog_common import (  # noqa: E402
    PROJECT_ROOT,
    acquire_lock,
    parse_frontmatter,
    release_lock,
)
from build_catalog import parse_md  # noqa: E402

CATALOG_MD = PROJECT_ROOT / "docs" / "CATALOG.md"
SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"
PROFILES_DIR = PROJECT_ROOT / ".claude" / "profiles"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
# user scope のインストールマニフェスト: core/extra/auth のプラグイン集合を定義する。
# プラグインは user scope に一度だけインストールされる（core は有効化、extra は
# インストール済みだが無効、auth はローカル限定）。project settings.json には
# 有効化された core との差分のみを保存する。
PLUGINS_MANIFEST = PROJECT_ROOT / ".claude" / "plugins-user-scope.json"

KIND_ROOT = {
    "skill": PROJECT_ROOT / ".claude" / "skills",
    "subagent": PROJECT_ROOT / ".claude" / "agents",
    "command": PROJECT_ROOT / ".claude" / "commands",
}

# このタグが付いたエントリは、選択プロファイルに関わらず常に維持する。
UNIVERSAL_TAG = "meta"

# CLAUDE.md のうちプロファイル本文で置き換える範囲の終端。'## プロジェクト規約' が現行の
# 境界だが、この見出しへ移行する前に初期化した派生プロジェクトは '## クイックスタート' を
# 持つ。旧見出しも受けないとそれらで --write-claude-md が中断するため両方を候補にする。
CLAUDE_MD_BOUNDARY_RE = re.compile(r"^## (?:プロジェクト規約|クイックスタート)\b", re.MULTILINE)


def available_profiles() -> list[str]:
    if not PROFILES_DIR.is_dir():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob("*.md") if not p.stem.startswith("_"))


def _matches(entry: dict, profile: str) -> bool:
    profs = entry.get("profiles") or []
    return profile in profs or UNIVERSAL_TAG in profs


def _entry_fs_path(entry: dict) -> Path | None:
    kind = entry["kind"]
    if kind == "skill":
        rel = entry.get("path") or f".claude/skills/{entry['category']}/{entry['name']}"
        return PROJECT_ROOT / rel
    if kind == "subagent":
        return PROJECT_ROOT / ".claude" / "agents" / f"{entry['name']}.md"
    if kind == "command":
        return PROJECT_ROOT / ".claude" / "commands" / f"{entry['name']}.md"
    return None


def _shell_quote(s: str) -> str:
    if s and all(c.isalnum() or c in "/._-" for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def _archive_destination(rel: str) -> str:
    """.claude/<kind-dir>/<rest> を .claude/<kind-dir>/_archived/<rest> に変換する。"""
    parts = rel.split("/")
    if len(parts) < 3:
        # 想定外の形式。フラットな退避先にフォールバックする
        return f"{'/'.join(parts[:-1])}/_archived/{parts[-1]}"
    head = parts[:2]  # ['.claude', 'skills']
    tail = parts[2:]  # ['writing', 'foo']
    return "/".join(head + ["_archived"] + tail)


def _load_user_scope_sets() -> tuple[set[str], set[str], set[str]]:
    """plugins-user-scope.json から (core, extra, auth) のプラグインキー集合を読む。

    これらは user-scope インストール層を定義する。project settings.json には
    有効化された `core` との差分のみを保存する: extra を有効化（true）、
    core を除外（false）。マニフェストが無ければ空集合を返す（レガシーリセットにフォールバック）。
    """
    try:
        m = json.loads(PLUGINS_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set(), set(), set()
    return (
        set(m.get("core") or []),
        set(m.get("extra") or []),
        set(m.get("auth_local_only") or []),
    )


def load_profile_meta(profile: str) -> dict:
    """プロファイル MD の frontmatter を読む。呼び出しごとに 1 回だけ読み込む。"""
    profile_file = PROFILES_DIR / f"{profile}.md"
    if not profile_file.exists():
        raise SystemExit(f"プロファイル MD が見つかりません: {profile_file}")
    meta, _ = parse_frontmatter(profile_file.read_text(encoding="utf-8"))
    return meta


def _profile_list_field(meta: dict, profile: str, key: str, *, require_at: bool) -> list[str]:
    """frontmatter の list フィールドを検証して返す。

    enabled_plugins / enabled_mcp はどちらも「YAML list を読み、文字列だけを拾う」
    という同じ形をしている。違いは plugin キーが `name@marketplace` 形式を要求する
    ことだけなので、require_at で切り替える。

    - enabled_plugins: そのプロファイルが有効化するマーケットプレイスプラグイン。
      CATALOG.md の `profiles:` は skill/subagent/command の退避判定にのみ使い、
      プラグインの有効/無効はこちらが source of truth。
    - enabled_mcp: .mcp.json のサーバのうち enabledMcpjsonServers 許可リストへ
      載せるもの。省略時はそのプロファイルは MCP サーバを 1 つも有効化しない。
    """
    raw = meta.get(key) or []
    if not isinstance(raw, list):
        raise SystemExit(f"profile {profile}: {key} は YAML list である必要があります（実際: {type(raw).__name__}）")
    return [s for s in raw if isinstance(s, str) and s and (not require_at or "@" in s)]


def compute_plan(profile: str) -> dict:
    if not CATALOG_MD.exists():
        raise SystemExit(f"CATALOG.md が見つかりません: {CATALOG_MD}")
    _meta, entries = parse_md(CATALOG_MD.read_text(encoding="utf-8"))

    current_enabled: dict[str, bool] = {}
    current_mcp: list[str] = []
    if SETTINGS_JSON.exists():
        try:
            _data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
            current_enabled = _data.get("enabledPlugins") or {}
            current_mcp = list(_data.get("enabledMcpjsonServers") or [])
        except json.JSONDecodeError:
            current_enabled = {}
            current_mcp = []

    # プロファイル MD の frontmatter が有効化集合を決める。CATALOG と現在有効な集合の
    # 和集合が無効化候補プール（厳格リセットのセマンティクス）。
    profile_meta = load_profile_meta(profile)
    enable_set: set[str] = set(_profile_list_field(profile_meta, profile, "enabled_plugins", require_at=True))
    # プロファイルが宣言する MCP 許可リスト（有効化する .mcp.json サーバ名）。
    mcp_allow = sorted(set(_profile_list_field(profile_meta, profile, "enabled_mcp", require_at=False)))

    plugins_skipped: list[dict] = []
    catalog_plugin_keys: set[str] = set()

    archive: dict[str, list[str]] = {"skill": [], "subagent": [], "command": []}
    already_archived: list[str] = []

    for e in entries:
        kind = e["kind"]
        if kind == "plugin":
            mp = (e.get("marketplace") or "").strip()
            # マーケットプレイス非経由のプラグイン（standalone MCP 等）は
            # enabledPlugins では管理しない。`claude mcp add` で追加され
            # ~/.claude.json の mcpServers に存在する。
            if not mp or " " in mp or "external" in mp.lower():
                plugins_skipped.append(
                    {
                        "name": e["name"],
                        "marketplace": mp,
                        "reason": "マーケットプレイス非経由のプラグイン。claude mcp add で設定してください",
                    }
                )
                continue
            catalog_plugin_keys.add(f"{e['name']}@{mp}")
        elif kind in ("skill", "subagent", "command"):
            fs_path = _entry_fs_path(e)
            if fs_path is None or not fs_path.exists():
                continue
            try:
                rel = str(fs_path.relative_to(PROJECT_ROOT))
            except ValueError:
                continue
            if "_archived" in fs_path.parts:
                already_archived.append(rel)
                continue
            if _matches(e, profile):
                continue
            archive[kind].append(rel)

    core, extra, auth = _load_user_scope_sets()
    if core or extra:
        # 差分モデル: project settings.json には有効化された user-scope `core` との
        # 差分のみを保存する。プロファイルが望む extra（および非 core/非 auth の
        # プラグイン）は true、プロファイルが外す core は false を書く。auth
        # プラグインはここには書かない（アカウント分離方針に従い settings.local.json
        # に置く）。プロファイルにもう合致しない管理下キーは削除し、
        # ファイルを最小限の差分に保つ。
        plugins_enable = sorted(enable_set - core - auth)
        plugins_disable = sorted(core - enable_set)
        managed = core | extra | auth
        keep = set(plugins_enable) | set(plugins_disable)
        plugins_remove = sorted(k for k in current_enabled if k in managed and k not in keep)
    else:
        # レガシーフォールバック（マニフェストなし）: 厳格リセット。現在有効か
        # CATALOG に存在し、かつ enable_set に無いものは全て無効化する。
        currently_enabled_keys = {k for k, v in current_enabled.items() if v}
        disable_set = (currently_enabled_keys | catalog_plugin_keys) - enable_set
        plugins_enable = sorted(enable_set)
        plugins_disable = sorted(disable_set)
        plugins_remove = []

    # 現在の状態から実際に何か変わるかを判定する。
    changes_plugins = (
        any(current_enabled.get(k) is not True for k in plugins_enable)
        or any(current_enabled.get(k) is not False for k in plugins_disable)
        or bool(plugins_remove)
    )
    changes_mcp = sorted(current_mcp) != mcp_allow
    has_archive = any(archive[k] for k in archive)
    noop = not changes_plugins and not changes_mcp and not has_archive

    archive_out = {
        "skills": sorted(archive["skill"]),
        "agents": sorted(archive["subagent"]),
        "commands": sorted(archive["command"]),
    }
    return {
        "profile": profile,
        "plugins": {
            "enable": plugins_enable,
            "disable": plugins_disable,
            "remove": plugins_remove,
            "skipped_no_marketplace": sorted(plugins_skipped, key=lambda d: d["name"]),
        },
        "mcp": {"enable": mcp_allow},
        "archive": archive_out,
        "already_archived": sorted(already_archived),
        "bash_commands": _build_bash_commands(archive_out),
        "noop": noop,
    }


def _build_bash_commands(archive: dict[str, list[str]]) -> list[dict]:
    """kind 別に、退避エントリの mkdir+mv コマンド対を組み立てる。"""
    bash_commands: list[dict] = []
    kind_map = [
        ("skill", archive.get("skills") or []),
        ("subagent", archive.get("agents") or []),
        ("command", archive.get("commands") or []),
    ]
    for kind, items in kind_map:
        items = [i for i in items if i]
        if not items:
            continue
        parents = sorted({_archive_destination(p).rsplit("/", 1)[0] for p in items})
        mkdir_cmd = "mkdir -p " + " ".join(_shell_quote(p) for p in parents)
        mv_cmd = "; ".join(f"mv {_shell_quote(src)} {_shell_quote(_archive_destination(src))}" for src in items)
        bash_commands.append({"kind": kind, "mkdir": mkdir_cmd, "mv": mv_cmd})
    return bash_commands


def validate_plan_file(raw: dict) -> tuple[dict, list[str]]:
    """外部から与えられたプラン dict（Claude が編集したもの等）を正規化する。

    (正規化後プラン, 警告一覧) を返す。致命的エラーは SystemExit を送出する。
    プランは plugins.{enable,disable}（文字列リスト）と
    archive.{skills,agents,commands}（リポジトリ相対パスのリスト）を持つ必要がある。
    存在しないファイルを指す退避パスは削除する（警告）。'name@marketplace' 形式
    でないプラグインキーも削除する（警告）。bash_commands は archive リストから
    再構築する。
    """
    warnings: list[str] = []
    if not isinstance(raw, dict):
        raise SystemExit("plan-file: トップレベルはオブジェクトである必要があります")
    plugins = raw.get("plugins") or {}
    archive = raw.get("archive") or {}
    mcp = raw.get("mcp") or {}
    enable = list(plugins.get("enable") or [])
    disable = list(plugins.get("disable") or [])
    remove = list(plugins.get("remove") or [])
    mcp_enable = [s for s in (mcp.get("enable") or []) if isinstance(s, str) and s]
    skills = list(archive.get("skills") or [])
    agents = list(archive.get("agents") or [])
    commands = list(archive.get("commands") or [])

    def clean_plugin_keys(keys: list[str], label: str) -> list[str]:
        out: list[str] = []
        for k in keys:
            if not isinstance(k, str) or "@" not in k:
                warnings.append(f"{label}: 不正なキーを削除しました {k!r}（'name@marketplace' 形式が必要）")
                continue
            out.append(k)
        return out

    enable = clean_plugin_keys(enable, "plugins.enable")
    disable = clean_plugin_keys(disable, "plugins.disable")
    overlap = set(enable) & set(disable)
    if overlap:
        warnings.append(f"enable と disable の両方にあるキー（enable を優先）: {sorted(overlap)}")
        disable = [k for k in disable if k not in overlap]

    def clean_paths(paths: list[str], expected_prefix: str, label: str) -> list[str]:
        out: list[str] = []
        for p in paths:
            if not isinstance(p, str):
                warnings.append(f"{label}: 文字列でないエントリを削除しました {p!r}")
                continue
            if not p.startswith(expected_prefix):
                warnings.append(f"{label}: {p!r} を削除しました（{expected_prefix} で始まる必要があります）")
                continue
            if "_archived" in p.split("/"):
                warnings.append(f"{label}: 退避済みの {p!r} を削除しました")
                continue
            full = PROJECT_ROOT / p
            if not full.exists():
                warnings.append(f"{label}: {p!r} を削除しました（ディスク上に見つかりません）")
                continue
            out.append(p)
        return out

    skills = clean_paths(skills, ".claude/skills/", "archive.skills")
    agents = clean_paths(agents, ".claude/agents/", "archive.agents")
    commands = clean_paths(commands, ".claude/commands/", "archive.commands")

    normalized = {
        "profile": raw.get("profile") or "<from-plan-file>",
        "plugins": {
            "enable": sorted(set(enable)),
            "disable": sorted(set(disable)),
            "remove": sorted(set(remove)),
            "skipped_no_marketplace": list(plugins.get("skipped_no_marketplace") or []),
        },
        "mcp": {"enable": sorted(set(mcp_enable))},
        "archive": {
            "skills": sorted(set(skills)),
            "agents": sorted(set(agents)),
            "commands": sorted(set(commands)),
        },
        "already_archived": list(raw.get("already_archived") or []),
        "bash_commands": [],
        "noop": False,
    }
    normalized["bash_commands"] = _build_bash_commands(normalized["archive"])
    return normalized, warnings


def patch_settings(plan: dict, dry_run: bool = False) -> dict:
    """enabledPlugins と enabledMcpjsonServers（.mcp.json 許可リスト）を settings.json に書く。

    enable -> true、disable -> false、remove -> キー削除（user scope を継承）。
    管理対象外のプラグインには触れない。マーケットプレイスは現在 user scope に
    あるため、extraKnownMarketplaces はもう書かない。
    """
    if not SETTINGS_JSON.exists():
        return {"changed": 0, "missing_settings": True}
    data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    enabled = dict(data.get("enabledPlugins") or {})
    before_enabled = dict(enabled)
    for key in plan["plugins"]["enable"]:
        enabled[key] = True
    for key in plan["plugins"]["disable"]:
        enabled[key] = False
    for key in plan["plugins"].get("remove", []):
        enabled.pop(key, None)
    changed_enabled = [k for k in set(before_enabled) | set(enabled) if before_enabled.get(k) != enabled.get(k)]

    # MCP 許可リスト: このプロジェクトで有効化する .mcp.json サーバをプロファイルが
    # 完全に指定する（空リスト = なし）。plan に存在する場合のみ書き込む。
    mcp_allow = sorted((plan.get("mcp") or {}).get("enable") or [])
    before_mcp = sorted(data.get("enabledMcpjsonServers") or [])
    has_mcp_plan = "mcp" in plan
    changed_mcp = has_mcp_plan and before_mcp != mcp_allow

    if (changed_enabled or changed_mcp) and not dry_run:
        data["enabledPlugins"] = enabled
        if has_mcp_plan:
            if mcp_allow:
                data["enabledMcpjsonServers"] = mcp_allow
            else:
                data.pop("enabledMcpjsonServers", None)
        acquire_lock()
        try:
            SETTINGS_JSON.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        finally:
            release_lock()
    return {
        "changed": len(changed_enabled),
        "changed_keys": sorted(changed_enabled),
        "mcp_changed": changed_mcp,
        "mcp_enabled": mcp_allow,
        "dry_run": dry_run,
    }


def scaffold_dirs(profile: str, dry_run: bool = False) -> dict:
    """プロファイル frontmatter の scaffold: に沿って作業ディレクトリを作る。

    既存ディレクトリには触らない。初期化を途中から再開しても中身を壊さないためであり、
    このモードが冪等である根拠でもある。新規作成したものだけ .gitkeep を置く。既存の
    ディレクトリに .gitkeep を足すと、実ファイルがあるのに空ディレクトリの目印が残る。
    """
    meta = load_profile_meta(profile)
    entries = meta.get("scaffold") or []
    created: list[str] = []
    skipped: list[str] = []
    for rel in entries:
        rel = str(rel).strip().strip("/")
        # 親ディレクトリからの脱出を弾く。scaffold: はリポジトリ内だけを対象とする。
        if not rel or rel.startswith(".") or ".." in Path(rel).parts:
            skipped.append(rel or "(空)")
            continue
        target = PROJECT_ROOT / rel
        if target.exists():
            skipped.append(rel)
            continue
        created.append(rel)
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
            (target / ".gitkeep").touch()
    return {"created": created, "skipped": skipped, "dry_run": dry_run}


def patch_claude_md(profile: str, dry_run: bool = False) -> dict:
    """CLAUDE.md の冒頭（境界見出しより前）をプロファイル本文で置き換える。

    frontmatter は落とす。enabled_plugins などは apply_profile / doctor が読む機械用
    メタデータであり、人間向けの指示書に載せる意味がないため。
    見出しのプロジェクト名はディレクトリ名から取る。テンプレートはコピーして使う
    前提なので、テンプレート名を固定で書くとコピー先で必ず誤る。

    既存 CLAUDE.md に境界が無い場合は中断する。黙って空 tail に倒すと、境界より後ろに
    書かれたプロジェクト固有の規約を丸ごと消してしまうため。
    """
    profile_file = PROFILES_DIR / f"{profile}.md"
    if not profile_file.exists():
        raise SystemExit(f"プロファイル MD が見つかりません: {profile_file}")
    _meta, body = parse_frontmatter(profile_file.read_text(encoding="utf-8"))
    profile_body = body.strip() + "\n"
    current = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    m = CLAUDE_MD_BOUNDARY_RE.search(current)
    if current.strip() and m is None:
        raise SystemExit(
            f"既存の {CLAUDE_MD.name} に境界見出し『## プロジェクト規約』がありません。"
            "このまま書き換えると境界より後ろの内容を失うため中断します。"
            "テンプレ運用を離れたプロジェクトではプロファイルの再適用は不要です。"
        )
    fixed_tail = current[m.start() :] if m else ""
    new_header = f"# {PROJECT_ROOT.name} ({profile})\n\n{profile_body}\n"
    new_full = new_header + fixed_tail
    changed = new_full != current
    if changed and not dry_run:
        CLAUDE_MD.write_text(new_full, encoding="utf-8")
    return {"changed": changed, "bytes": len(new_full), "dry_run": dry_run}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", help="プロファイル名（.claude/profiles/ 内のファイルと一致させる）")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--write-claude-md", action="store_true")
    mode.add_argument(
        "--scaffold",
        action="store_true",
        help="プロファイルの scaffold: に沿って作業ディレクトリを作る（既存には触らない）",
    )
    mode.add_argument(
        "--list-profiles",
        action="store_true",
        help="利用可能なプロファイルを JSON で列挙する（--profile 不要）。"
        "/init-project が選択肢を実体から組むために使う",
    )
    ap.add_argument(
        "--plan-file",
        help="JSON プラン（--plan の出力を編集したもの）。--apply とあわせるとプロファイル由来のプランを上書きする",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="--apply / --write-claude-md で、書き込まず変更内容のみ表示する"
    )
    ap.add_argument("--yes", action="store_true", help="予約済み引数。確認は呼び出し元の /init-project コマンドが行う")
    args = ap.parse_args()

    avail = available_profiles()

    if args.list_profiles:
        # description も返すのは、/init-project が選択肢のラベルを実体から作れるようにするため。
        profiles = [{"name": name, "description": load_profile_meta(name).get("description", "")} for name in avail]
        print(json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2))
        return 0

    if not args.profile:
        print("error: --profile は --list-profiles 以外のモードで必須です", file=sys.stderr)
        return 2
    if args.profile not in avail:
        print(
            f"error: プロファイル '{args.profile}' が見つかりません。利用可能: {', '.join(avail)}",
            file=sys.stderr,
        )
        return 2

    if args.plan:
        if args.plan_file:
            print("error: --plan-file は --apply と併用時のみ有効です", file=sys.stderr)
            return 2
        plan = compute_plan(args.profile)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    if args.apply:
        warnings: list[str] = []
        if args.plan_file:
            plan_path = Path(args.plan_file)
            if not plan_path.exists():
                print(f"error: plan-file が見つかりません: {plan_path}", file=sys.stderr)
                return 2
            try:
                raw = json.loads(plan_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"error: plan-file が正しい JSON ではありません: {exc}", file=sys.stderr)
                return 2
            plan, warnings = validate_plan_file(raw)
        else:
            plan = compute_plan(args.profile)
        settings_result = patch_settings(plan, dry_run=args.dry_run)
        print(
            json.dumps(
                {
                    "profile": args.profile,
                    "plan_source": "plan-file" if args.plan_file else "profile-derived",
                    "settings": settings_result,
                    "archive": plan["archive"],
                    "bash_commands": plan["bash_commands"],
                    "noop": plan.get("noop"),
                    "warnings": warnings,
                    "dry_run": args.dry_run,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.write_claude_md:
        if args.plan_file:
            print("error: --plan-file は --apply と併用時のみ有効です", file=sys.stderr)
            return 2
        result = patch_claude_md(args.profile, dry_run=args.dry_run)
        print(json.dumps({"profile": args.profile, **result}, ensure_ascii=False))
        return 0

    if args.scaffold:
        if args.plan_file:
            print("error: --plan-file は --apply と併用時のみ有効です", file=sys.stderr)
            return 2
        result = scaffold_dirs(args.profile, dry_run=args.dry_run)
        print(json.dumps({"profile": args.profile, **result}, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

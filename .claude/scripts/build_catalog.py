#!/usr/bin/env python3
"""CATALOG.md から docs/CATALOG.html を描画する。

CATALOG.md はプラグイン・スキル・subagent 等の統合 source-of-truth。
各エントリは `- kind: plugin|skill|subagent` を宣言できる（既定: plugin）。

パイプライン:
  CATALOG.md（手編集）
  + .claude/settings.json（enabledPlugins -> plugin エントリを自動で [enabled] 化）
  + ~/.claude.json（projects[<root>].mcpServers -> エントリの `install:` 行が
                    `claude mcp add <name> ...` で <name> が登録済みなら自動で [enabled] 化）
    -> docs/CATALOG.html
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _catalog_common import (
    PROJECT_ROOT,
    acquire_lock,
    esc,
    lock_held,
    log,
    parse_frontmatter,
    release_lock,
    render_template,
)

SOURCE_MD = PROJECT_ROOT / "docs" / "CATALOG.md"
OUTPUT_HTML = PROJECT_ROOT / "docs" / "CATALOG.html"
SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"
CLAUDE_JSON = Path.home() / ".claude.json"

# install コマンド先頭の `claude mcp add [scope flags] <name>` にマッチ。
# `add` と name の間の `-s <scope>` / `--scope <scope>` は任意で許容する。
_MCP_ADD_RE = re.compile(r"\bclaude\s+mcp\s+add\b" r"(?:\s+(?:-s|--scope)\s+\S+)?" r"\s+([A-Za-z0-9_.\-:]+)")

KIND_ORDER = ["plugin", "skill", "subagent", "command"]
KIND_LABELS = {
    "plugin": "プラグイン",
    "skill": "スキル",
    "subagent": "subagent",
    "command": "コマンド",
}
KIND_BADGE = {
    # (前景色, 背景色) — 既存の CSS パレットから選ぶ
    "plugin": ("var(--official)", "rgba(96,165,250,0.15)"),
    "skill": ("var(--accent)", "rgba(94,234,212,0.15)"),
    "subagent": ("var(--community)", "rgba(167,139,250,0.15)"),
    "command": ("var(--restricted)", "rgba(244,114,182,0.15)"),
}

CATEGORY_ORDER_BY_KIND = {
    "plugin": [
        "official",
        "code-quality",
        "autonomous",
        "search-data",
        "devops",
        "integration",
        "business-knowledge",
    ],
    "skill": [
        "dev",
        "write",
        "research",
        "project",
        "meta",
    ],
    "subagent": ["subagent"],
    "command": ["command"],
}

CATEGORY_LABELS = {
    "official": "official",
    "code-quality": "code-quality",
    "autonomous": "autonomous",
    "search-data": "search-data",
    "devops": "devops",
    "integration": "integration",
    "business-knowledge": "business",
}

STATUS_SIGIL = {
    # status -> (表示ラベル, CSS のシジル色キー)
    "enabled": ("enabled", "official"),
    "available": ("available", "self"),
    "partner": ("partner", "community"),
    "self": ("self", "self"),
    "anthropic": ("anthropic", "official"),
    "community": ("community", "community"),
    "active": ("active", "official"),  # subagent/command のファイルが存在する
    "planned": ("planned", "restricted"),  # CATALOG には記載があるがファイルが無い
}


def parse_md(text: str) -> tuple[dict, list[dict]]:
    """CATALOG.md をパースし (frontmatter, entry_records) を返す。"""
    meta, body = parse_frontmatter(text)
    entries: list[dict] = []
    current_cat: str | None = None
    current: dict | None = None
    in_schema_section = False  # 「エントリの追加」節配下のエントリは無視する

    def flush() -> None:
        nonlocal current
        if current:
            entries.append(current)
        current = None

    for line in body.splitlines():
        # H2 — セクション区切り。カテゴリをリセットし、スキーマ説明節内のエントリはスキップ
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            flush()
            current_cat = None
            in_schema_section = "エントリの追加" in m.group(1) or "schema" in m.group(1).lower()
            continue
        if in_schema_section:
            continue
        m = re.match(r"^### (\S+)\s*$", line)
        if m:
            flush()
            current_cat = m.group(1).strip()
            continue
        m = re.match(r"^####\s+(\S+)(?:\s+\[(\w+)\])?\s*$", line)
        if m:
            flush()
            name = m.group(1).strip()
            status = (m.group(2) or "available").strip()
            current = {
                "name": name,
                "category": current_cat or "uncategorized",
                "status": status,
                "kind": "plugin",  # 既定値。エントリごとの `- kind:` で上書き可
                "description": "",
                "tags": [],
                "profiles": [],
                "marketplace": "",
                "url": "",
                "installs": "",
                "install": "",
                "path": "",
                "copy": "",
            }
            continue
        if not current:
            continue
        m = re.match(r"^>\s+(.+)$", line)
        if m:
            current["description"] = m.group(1).strip()
            continue
        m = re.match(r"^-\s+(\w+):\s*(.+)$", line)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            if key in ("tags", "profiles"):
                current[key] = [v.strip() for v in val.split(",") if v.strip()]
            else:
                current[key] = val
            continue
    flush()
    return meta, entries


def _load_project_mcp_servers(claude_json_path: Path, project_root: Path) -> set[str]:
    """このプロジェクト向けに ~/.claude.json にインストール済みの MCP サーバ名集合を返す。

    `claude mcp add <name> ...` で追加された standalone MCP は settings.json の
    enabledPlugins ではなく ~/.claude.json に、スコープに応じて次のいずれかの
    位置に保存される:
      - user scope:    トップレベルの `mcpServers`
      - project scope: `projects[<absolute-project-path>].mcpServers`（既定）
    どちらのスコープでもエントリを [enabled] とマークできるよう、両方を統合する。
    """
    if not claude_json_path.exists():
        return set()
    try:
        data = json.loads(claude_json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    names: set[str] = set()
    user_scope = data.get("mcpServers") or {}
    if isinstance(user_scope, dict):
        names.update(k for k in user_scope.keys() if isinstance(k, str))
    projects = data.get("projects", {}) or {}
    proj = projects.get(str(project_root), {}) or {}
    project_scope = proj.get("mcpServers") or {}
    if isinstance(project_scope, dict):
        names.update(k for k in project_scope.keys() if isinstance(k, str))
    return names


def _extract_mcp_name(install_cmd: str) -> str | None:
    if not install_cmd:
        return None
    m = _MCP_ADD_RE.search(install_cmd)
    return m.group(1) if m else None


def _read_enabled_plugins(path: Path) -> dict:
    """settings ファイルから enabledPlugins マップを返す（ファイルが無い/壊れていれば空）。"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("enabledPlugins") or {}
    except json.JSONDecodeError:
        return {}


def apply_enabled_state(entries: list[dict], settings_path: Path) -> None:
    # 実効的な有効化状態は3つのスコープを統合する（優先度: 低 -> 高）:
    #   user (~/.claude/settings.json) = インストール層・既定 ON の core
    #   project (.claude/settings.json) = コミット済みの差分（extra を ON、core を除外）
    #   local (.claude/settings.local.json) = 個人・認証情報（notion 等）
    # user scope で有効だが project の差分に無いプラグインもここでは [enabled] のまま。
    # project の `false` は user の `true` を正しく上書きする。
    user_enabled = _read_enabled_plugins(Path.home() / ".claude" / "settings.json")
    project_enabled = _read_enabled_plugins(settings_path)
    local_enabled = _read_enabled_plugins(settings_path.parent / "settings.local.json")
    effective = {**user_enabled, **project_enabled, **local_enabled}
    enabled_names = {key.split("@")[0] for key, val in effective.items() if val and "@" in key}

    mcp_servers = _load_project_mcp_servers(CLAUDE_JSON, PROJECT_ROOT)

    for e in entries:
        if e["kind"] != "plugin":
            continue
        if e["status"] == "enabled":
            continue
        if e["name"] in enabled_names:
            e["status"] = "enabled"
            continue
        mcp_name = _extract_mcp_name(e.get("install", ""))
        if mcp_name and mcp_name in mcp_servers:
            e["status"] = "enabled"


def apply_filesystem_state(entries: list[dict], project_root: Path) -> None:
    """対応するファイルが存在すれば status を 'active' に、無ければ 'planned'/'available' にする。

    CATALOG.md の願望的な記述ではなく、ファイルシステムの実態を反映する。
    """
    agents_dir = project_root / ".claude" / "agents"
    commands_dir = project_root / ".claude" / "commands"
    for e in entries:
        if e["kind"] == "subagent":
            f = agents_dir / f"{e['name']}.md"
            e["status"] = "active" if f.exists() else "planned"
        elif e["kind"] == "command":
            f = commands_dir / f"{e['name']}.md"
            e["status"] = "active" if f.exists() else "planned"
        elif e["kind"] == "skill":
            # スキルは .claude/skills/<category>/<name>/SKILL.md に置かれる
            path = e.get("path") or f".claude/skills/{e['category']}/{e['name']}"
            skill_md = project_root / path / "SKILL.md"
            if not skill_md.exists():
                # path が既に /SKILL.md を含む、またはファイル自体を指す場合がある
                p2 = project_root / path
                skill_md = p2 if p2.suffix == ".md" else (p2 / "SKILL.md")
            if skill_md.exists():
                e["status"] = "active"
            # 見つからなければ既存の status（通常は "available"）のまま


# ---------- ファイルシステム探索（CATALOG.md への新規エントリ追加） ----------


def _read_fm(path: Path) -> dict:
    try:
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        return meta or {}
    except OSError:
        return {}


def discover_subagents(root: Path) -> list[dict]:
    """`.claude/agents/*.md` をスキャン。frontmatter から名前・説明・tools 等を抽出。"""
    agents = root / ".claude" / "agents"
    if not agents.is_dir():
        return []
    out = []
    for f in sorted(agents.glob("*.md")):
        if f.name.startswith("_") or f.name == "README.md":
            continue
        if "_archived" in f.parts:
            continue
        meta = _read_fm(f)
        out.append(
            {
                "name": meta.get("name") or f.stem,
                "kind": "subagent",
                "category": "subagent",
                "description": meta.get("description") or "",
                "tools": meta.get("tools") or "",
                "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
                "profiles": meta.get("profile_relevance") if isinstance(meta.get("profile_relevance"), list) else [],
            }
        )
    return out


def discover_commands(root: Path) -> list[dict]:
    """`.claude/commands/*.md` をスキャン。frontmatter から description/argument-hint 等を抽出。"""
    cmds = root / ".claude" / "commands"
    if not cmds.is_dir():
        return []
    out = []
    for f in sorted(cmds.glob("*.md")):
        if f.name.startswith("_") or f.name == "README.md":
            continue
        if "_archived" in f.parts:
            continue
        meta = _read_fm(f)
        out.append(
            {
                "name": f.stem,
                "kind": "command",
                "category": "command",
                "description": meta.get("description") or "",
                "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
                "profiles": meta.get("profile_relevance") if isinstance(meta.get("profile_relevance"), list) else [],
            }
        )
    return out


def discover_skills(root: Path, warn=None) -> list[dict]:
    """`.claude/skills/<category>/<name>/SKILL.md` を再帰スキャン。

    frontmatter が name/description どちらか欠落の場合は skip + 警告ログ。
    """
    skills = root / ".claude" / "skills"
    if not skills.is_dir():
        return []
    out = []
    for sk in sorted(skills.rglob("SKILL.md")):
        if "_archived" in sk.parts:
            continue
        rel = sk.relative_to(skills).parent
        parts = rel.parts
        if len(parts) < 2:
            # 期待構造は <category>/<name>/SKILL.md
            if warn:
                warn(f"skill skip (unexpected path depth): {sk}")
            continue
        meta = _read_fm(sk)
        name = meta.get("name") or parts[-1]
        desc = meta.get("description") or ""
        if not desc or not name:
            if warn:
                warn(f"skill skip (missing name or description): {sk}")
            continue
        out.append(
            {
                "name": name,
                "kind": "skill",
                "category": meta.get("type") or parts[0],
                "description": desc,
                "source": meta.get("source") or "",
                "license": meta.get("license") or "",
                "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
                "profiles": meta.get("profile_relevance") if isinstance(meta.get("profile_relevance"), list) else [],
                "path": f".claude/skills/{rel}",
            }
        )
    return out


def _format_discovered_entry(entry: dict) -> str:
    """発見済みエントリを CATALOG.md の Markdown ブロックとして描画する。"""
    lines = [f"<!-- AUTO-DISCOVERED {date.today().isoformat()}: {entry['name']} -->"]
    status = "active"
    lines.append(f"#### {entry['name']} [{status}]")
    lines.append(f"> {entry['description']}")
    lines.append("")
    lines.append(f"- kind: {entry['kind']}")
    if entry.get("tools"):
        lines.append(f"- tools: {entry['tools']}")
    if entry.get("source"):
        lines.append(f"- source: {entry['source']}")
    if entry.get("license"):
        lines.append(f"- license: {entry['license']}")
    if entry.get("path"):
        lines.append(f"- path: {entry['path']}")
    if entry.get("tags"):
        lines.append(f"- tags: {', '.join(entry['tags'])}")
    if entry.get("profiles"):
        lines.append(f"- profiles: {', '.join(entry['profiles'])}")
    lines.append("")
    return "\n".join(lines)


# エントリの挿入・削除に使うサブセクション見出し
_H4_RE = re.compile(r"^####\s+(\S+)(?:\s+\[(\w+)\])?\s*$", re.MULTILINE)
_AUTO_COMMENT_RE = re.compile(r"^<!-- AUTO-DISCOVERED [^-]+? -->\n", re.MULTILINE)


def _find_entry_span(text: str, name: str, kind: str) -> tuple[int, int] | None:
    """`#### name [..]` ブロックの (start, end) 範囲を返す（先頭のコメント行含む）。

    end は次の #### / ### / ## / --- または EOF の開始位置。

    kind の一致を必須にしているのは、名前だけで全文検索すると kind を跨いだ同名
    エントリ（例: subagent と plugin が同名）を取り違え、消すつもりのない plugin
    エントリを CATALOG.md から削除してしまうため。CATALOG.md は手編集の
    source of truth なので、この取り違えは復旧しにくい。
    """
    pat = re.compile(r"^####\s+" + re.escape(name) + r"(?:\s+\[\w+\])?\s*$", re.MULTILINE)
    end_pat = re.compile(r"^(####\s|###\s|##\s|---\s*$)", re.MULTILINE)
    for m in pat.finditer(text):
        start = m.start()
        # 先頭の <!-- AUTO-DISCOVERED ... --> 行を取り込めるよう start を前方へ拡張
        lines_before = text[:start].splitlines(keepends=True)
        if lines_before and lines_before[-1].lstrip().startswith("<!-- AUTO-DISCOVERED"):
            start -= len(lines_before[-1])
        em = end_pat.search(text, m.end())
        end = em.start() if em else len(text)
        block_kind = "plugin"  # CATALOG.md の既定 kind
        for line in text[m.end() : end].splitlines():
            stripped = line.strip()
            if stripped.startswith("- kind:"):
                block_kind = stripped.split(":", 1)[1].strip()
                break
        if block_kind == kind:
            return start, end
    return None


def _insert_under_subsection(text: str, h2_title: str, h3_category: str, block: str) -> str:
    """## h2_title セクション内の ### h3_category サブセクション末尾に `block` を追記する。

    サブセクションが無ければ、H2 セクション末尾に見出しごと新規追加する。
    """
    h2_re = re.compile(r"^## " + re.escape(h2_title) + r"\s*$", re.MULTILINE)
    h2m = h2_re.search(text)
    if not h2m:
        # H2 セクションが無い場合、末尾に新規追加する（末尾の --- または EOF の前）
        new_section = f"\n## {h2_title}\n\n### {h3_category}\n\n{block}\n---\n"
        return text + new_section
    # H2 の範囲の終端を特定
    next_h2 = re.compile(r"^## ", re.MULTILINE).search(text, h2m.end())
    h2_end = next_h2.start() if next_h2 else len(text)
    section = text[h2m.start() : h2_end]
    # 対象の H3 サブセクションを探す
    h3_pat = re.compile(r"^### " + re.escape(h3_category) + r"\s*$", re.MULTILINE)
    h3m = h3_pat.search(section)
    if h3m:
        # この H3 の終端を探す（次の ### またはセクション末尾）
        next_h3 = re.compile(r"^### ", re.MULTILINE).search(section, h3m.end())
        h3_end_rel = next_h3.start() if next_h3 else len(section)
        # 挿入位置の前の末尾空行・--- を除去
        trimmed = section[h3m.start() : h3_end_rel].rstrip()
        # 区切りの改行を確保
        new_section = section[: h3m.start()] + trimmed + "\n\n" + block + "\n" + section[h3_end_rel:]
        return text[: h2m.start()] + new_section + text[h2_end:]
    else:
        # H3 が見つからない場合、H2 セクション末尾に新規 H3 + block を追加（末尾の --- があればその前）
        sec_trim = section.rstrip()
        # 末尾の "---" を除去
        if sec_trim.endswith("---"):
            sec_trim = sec_trim[:-3].rstrip()
        new_section = sec_trim + f"\n\n### {h3_category}\n\n" + block + "\n\n---\n\n"
        return text[: h2m.start()] + new_section + text[h2_end:]


# kind -> (CATALOG.md 内の H2 見出し、既定 H3 カテゴリ) のマッピング
_KIND_TO_H2 = {
    "subagent": "subagent 一覧",
    "command": "コマンド一覧",
    "skill": "スキル一覧",
}


def sync_catalog_md(
    text: str, discovered_by_kind: dict[str, list[dict]], log_fn=None
) -> tuple[str, dict[str, list[str]], dict[str, list[str]]]:
    """未登録の発見済みエントリを追加し、ディスクから消えたエントリを削除する。

    (new_text, added_by_kind, removed_by_kind) を返す。
    対象 kind は {subagent, skill, command} のみ。plugin/mcp はそのまま維持する。
    """
    log_fn = log_fn or (lambda *a: None)

    # 1. 既存 CATALOG エントリを kind 別にパースする
    existing_meta, _ = parse_frontmatter(text)  # noqa: F841 (frontmatter は不要)
    _, existing_entries = parse_md(text)
    by_kind: dict[str, dict[str, dict]] = {"subagent": {}, "skill": {}, "command": {}}
    for e in existing_entries:
        if e["kind"] in by_kind:
            by_kind[e["kind"]][e["name"]] = e

    # 2. 発見済みの名前集合を構築する
    discovered_names: dict[str, set[str]] = {k: {d["name"] for d in v} for k, v in discovered_by_kind.items()}

    # 3. 追加分・削除分を判定する
    added: dict[str, list[str]] = {"subagent": [], "skill": [], "command": []}
    removed: dict[str, list[str]] = {"subagent": [], "skill": [], "command": []}

    new_text = text
    # 3a. 追加: 発見済み ∖ 既存
    for kind, discovered_entries in discovered_by_kind.items():
        if kind not in by_kind:
            continue
        for d in discovered_entries:
            if d["name"] in by_kind[kind]:
                continue  # 既に CATALOG にある
            block = _format_discovered_entry(d)
            new_text = _insert_under_subsection(new_text, _KIND_TO_H2[kind], d["category"], block)
            added[kind].append(d["name"])

    # 3b. 削除: 既存 ∖ 発見済み（管理対象の kind のみ）
    for kind, name_set in discovered_names.items():
        if kind not in by_kind:
            continue
        for name in list(by_kind[kind]):
            if name in name_set:
                continue
            # エントリブロックを削除する
            span = _find_entry_span(new_text, name, kind)
            if span is None:
                continue
            new_text = new_text[: span[0]] + new_text[span[1] :]
            removed[kind].append(name)

    # 3c. 削除によって生じた余分な空行を正規化する
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)

    return new_text, added, removed


def copy_target(entry: dict) -> str:
    """行の Copy ボタンがクリップボードに書き込む内容を返す。"""
    if entry.get("copy"):
        return entry["copy"]
    if entry["kind"] == "plugin":
        if entry.get("install"):
            return entry["install"]
        mp = entry.get("marketplace") or "claude-plugins-official"
        return f"/plugin install {entry['name']}@{mp}"
    if entry["kind"] == "skill":
        if entry.get("install"):
            return entry["install"]
        return entry.get("path") or f".claude/skills/{entry['category']}/{entry['name']}"
    if entry["kind"] == "subagent":
        return entry["name"]
    if entry["kind"] == "command":
        return f"/{entry['name']}"
    return entry["name"]


def kind_badge(kind: str) -> str:
    fg, bg = KIND_BADGE.get(kind, ("var(--fg-soft)", "transparent"))
    return (
        f'<span class="r-kind" data-kind="{esc(kind)}" '
        f'style="font-family:var(--mono);font-size:0.66rem;font-weight:600;'
        f"letter-spacing:0.04em;color:{fg};background:{bg};"
        f'padding:1px 6px;border-radius:3px;text-transform:uppercase;">{esc(kind)}</span>'
    )


def render_row(entry: dict) -> str:
    name = entry["name"]
    cat = entry["category"]
    kind = entry["kind"]
    status = entry["status"]
    sigil_label, sigil_color = STATUS_SIGIL.get(status, (status, "self"))
    desc = entry.get("description") or "（説明なし）"
    tags = entry.get("tags") or []
    profiles = entry.get("profiles") or []
    url = entry.get("url") or ""

    tag_html_parts = [f'<button class="tag-chip" data-tag="{esc(t)}" type="button">{esc(t)}</button>' for t in tags[:6]]
    if len(tags) > 6:
        tag_html_parts.append(f'<span class="tag-more">+{len(tags)-6}</span>')
    tag_html = "".join(tag_html_parts)

    prof_html = "".join(f'<span class="prof-pill">{esc(p)}</span>' for p in profiles)

    # 行下部の source-line。kind ごとに内容が異なる
    if kind == "plugin":
        source_parts = [entry.get("marketplace")] if entry.get("marketplace") else []
        if entry.get("installs"):
            source_parts.append(entry["installs"])
    elif kind == "skill":
        source_parts = []
        if entry.get("path"):
            source_parts.append(entry["path"])
        if entry.get("license"):
            source_parts.append(entry["license"])
    else:  # subagent
        source_parts = []
        if entry.get("tools"):
            source_parts.append(f"tools: {entry['tools']}")
    source_line = " · ".join(p for p in source_parts if p)

    url_html = (
        f' <a href="{esc(url)}" target="_blank" rel="noopener" '
        f'style="font-family:var(--mono);font-size:0.74rem;color:var(--accent);">[link]</a>'
        if url
        else ""
    )

    copy_str = copy_target(entry)
    copy_title = {
        "plugin": "インストールコマンドをコピー",
        "skill": "パスをコピー",
        "subagent": "subagent 名をコピー",
    }.get(kind, "コピー")

    data_tags = esc(" ".join(tags))
    data_profiles = esc(" ".join(profiles))
    return f"""    <article class="row" data-kind="{esc(kind)}" data-source="{esc(sigil_color)}" data-name="{esc(name)}" data-tags="{data_tags}" data-profiles="{data_profiles}" data-cat="{esc(cat)}">
      <div class="r-meta">
        <span class="r-sigil" data-k="{esc(sigil_color)}">{esc(sigil_label)}</span>
      </div>
      <div class="r-body">
        <header class="r-head" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          {kind_badge(kind)}
          <h3 class="r-name" style="margin:0;">{esc(name)}</h3>
          <span class="r-path">{esc(cat)}/{esc(name)}</span>{url_html}
        </header>
        <p class="r-desc">{esc(desc)}</p>
        <div class="r-foot">
          <div class="r-tags">{tag_html}</div>
          <div class="r-profiles">{prof_html}</div>
        </div>
        <div class="r-source">{esc(source_line)}</div>
      </div>
      <div class="r-actions">
        <button class="copy-btn" data-copy="{esc(copy_str)}" type="button" title="{esc(copy_title)}">⌘C</button>
      </div>
    </article>
"""


def render_category_section(idx: int, cat: str, entries: list[dict], kind: str) -> str:
    rows = "\n".join(render_row(e) for e in entries)
    cat_id = f"cat-{kind}-{cat}"
    return f"""  <section class="category" data-cat="{esc(cat)}" data-kind="{esc(kind)}" id="{esc(cat_id)}">
    <header class="cat-head">
      <span class="cat-idx">{idx:02d}</span>
      <h2 class="cat-title">{esc(cat)}</h2>
      <span class="cat-count" data-cat-count="{esc(cat)}">{len(entries)}</span>
      <span class="cat-kbd">g {idx}</span>
    </header>
    <div class="rows">
{rows}    </div>
  </section>
"""


def count_by(entries: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in entries:
        out[e[key]] = out.get(e[key], 0) + 1
    return out


def build_hero(meta: dict, entries: list[dict]) -> str:
    total = len(entries)
    by_kind = count_by(entries, "kind")
    version = meta.get("version") or str(date.today())

    # 分かりやすさのため、0件でも全 kind を常に表示する
    def pill_for(k: str) -> str:
        n = by_kind.get(k, 0)
        if k in ("subagent", "command"):
            active = sum(1 for e in entries if e["kind"] == k and e["status"] == "active")
            planned = n - active
            if planned > 0:
                return f'<span class="pill">{active} {esc(KIND_LABELS[k])}<span style="color:var(--muted);font-weight:400;"> (+{planned} planned)</span></span>'
        return f'<span class="pill">{n} {esc(KIND_LABELS[k])}</span>'

    kind_pills = "".join(pill_for(k) for k in KIND_ORDER)
    kbd = '<span class="kbd" style="font-family:var(--mono);color:var(--fg-soft);background:var(--bg-elev);border:1px solid var(--rule);padding:1px 6px;border-radius:3px;font-size:0.78rem;">'
    return f"""  <div class="hero-top">
    <span class="pill accent">v {esc(version)}</span>
    <span class="pill">{total} エントリ</span>
    {kind_pills}
  </div>
  <h1>catalog/<span class="blink">_</span></h1>
  <p class="deck">
    プラグイン・スキル・subagent・コマンドを 1 ファイルで管理。{kbd}/</span> で検索、 <code style="font-family:var(--mono);color:var(--accent);background:transparent;">#tag</code> で絞り込み、 {kbd}?</span> でヘルプ。
  </p>"""


def build_stats(entries: list[dict]) -> str:
    total = len(entries)
    by_kind = count_by(entries, "kind")
    plugins_only = [e for e in entries if e["kind"] == "plugin"]
    enabled = sum(1 for p in plugins_only if p["status"] == "enabled")
    sub_active = sum(1 for e in entries if e["kind"] == "subagent" and e["status"] == "active")
    sub_planned = by_kind.get("subagent", 0) - sub_active
    cmd_active = sum(1 for e in entries if e["kind"] == "command" and e["status"] == "active")
    cmd_planned = by_kind.get("command", 0) - cmd_active

    def planned_suffix(n: int) -> str:
        return f" (+{n} planned)" if n > 0 else ""

    stats = [
        f'  <div class="stat"><span class="lbl">合計</span><span class="num">{total}</span><span class="delta">エントリ</span></div>',
        f'  <div class="stat"><span class="lbl">plugin</span><span class="num official">{by_kind.get("plugin", 0)}</span><span class="delta">{enabled} enabled</span></div>',
        f'  <div class="stat"><span class="lbl">skill</span><span class="num">{by_kind.get("skill", 0)}</span><span class="delta">.claude/skills/</span></div>',
        f'  <div class="stat"><span class="lbl">subagent</span><span class="num community">{sub_active}</span><span class="delta">.claude/agents/{esc(planned_suffix(sub_planned))}</span></div>',
        f'  <div class="stat"><span class="lbl">command</span><span class="num restricted">{cmd_active}</span><span class="delta">.claude/commands/{esc(planned_suffix(cmd_planned))}</span></div>',
    ]
    return "\n".join(stats)


def build_filter_bar(entries: list[dict]) -> str:
    total = len(entries)
    by_kind = count_by(entries, "kind")

    # kind 別クイックボタン。クリックで検索欄にトリガーワードをセットし、既存の検索フィルタに乗せる
    kind_row_parts = [
        '<div class="kind-quick" style="display:flex;gap:6px;align-items:center;font-family:var(--mono);font-size:0.74rem;color:var(--fg-soft);margin-top:6px;">',
        '<span style="color:var(--muted);">kind:</span>',
    ]
    for k in KIND_ORDER:
        n = by_kind.get(k, 0)
        # 全 kind を常に表示し、0件ならグレーアウトして存在自体は分かるようにする
        disabled_style = "opacity:0.5;cursor:default;" if n == 0 else "cursor:pointer;"
        kind_row_parts.append(
            f'<button type="button" class="kind-quick-btn" data-kind-filter="{esc(k)}" '
            f'style="font-family:inherit;font-size:inherit;color:var(--fg);background:var(--bg-elev);'
            f'border:1px solid var(--rule);padding:2px 8px;border-radius:4px;{disabled_style}">'
            f'{esc(k)} <span style="color:var(--muted);">({n})</span></button>'
        )
    kind_row_parts.append(
        '<button type="button" class="kind-quick-btn" data-kind-filter="" '
        'style="font-family:inherit;font-size:inherit;color:var(--muted);background:transparent;'
        'border:1px solid var(--rule-soft);padding:2px 8px;border-radius:4px;cursor:pointer;">クリア</button>'
    )
    kind_row_parts.append("</div>")
    kind_row_html = "\n      ".join(kind_row_parts)

    # source トグル（status: enabled/available）— plugin にのみ意味がある
    src_buttons = """    <div class="src-toggle" role="group" aria-label="プラグイン状態で絞り込み">
      <button class="src-btn active" data-src="all">全て</button>
      <button class="src-btn" data-src="official">[enabled]</button>
      <button class="src-btn" data-src="self">[available]</button>
    </div>"""

    by_cat: dict[str, int] = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    # kind と同義になるカテゴリ（kind 名と一致する単一 kind のカテゴリ）は
    # カテゴリフィルタから除外する。kind クイックフィルタで代替できるため。
    skip_cat_buttons = {"subagent", "command"}
    cat_btns = [f'<button class="cat-btn active" data-cat="all">全て<span class="ct">{total}</span></button>']
    seen = set()
    ordered_cats: list[str] = []
    for k in KIND_ORDER:
        for cat in CATEGORY_ORDER_BY_KIND.get(k, []):
            if cat in by_cat and cat not in seen and cat not in skip_cat_buttons:
                ordered_cats.append(cat)
                seen.add(cat)
    for cat in sorted(set(by_cat) - seen):
        if cat in skip_cat_buttons:
            continue
        ordered_cats.append(cat)
    for cat in ordered_cats:
        label = CATEGORY_LABELS.get(cat, cat)
        cat_btns.append(
            f'<button class="cat-btn" data-cat="{esc(cat)}">{esc(label)}<span class="ct">{by_cat[cat]}</span></button>'
        )
    cat_html = (
        '    <div class="cat-toggle" role="group" aria-label="カテゴリで絞り込み">\n      '
        + "".join(cat_btns)
        + "\n    </div>"
    )

    # JS: 検索入力欄に相乗りする形で、既存フィルタが data-kind も見るよう拡張する。
    # kind-quick-btn クリック時、既存の innerText マッチ（kind バッジのテキストは
    # DOM 内にある）を活かすため、kind を検索欄に入力する。
    kind_filter_js = """  <script>
  (function(){
    var btns = document.querySelectorAll('.kind-quick-btn');
    var search = document.getElementById('search');
    btns.forEach(function(b){
      b.addEventListener('click', function(){
        var k = b.getAttribute('data-kind-filter') || '';
        // data-kind で直接フィルタする（検索テキストマッチより正確）
        document.querySelectorAll('.row').forEach(function(r){
          var matches = !k || r.getAttribute('data-kind') === k;
          r.dataset.kindFiltered = matches ? '' : 'hide';
        });
        // 空になったカテゴリも非表示にする
        document.querySelectorAll('.category').forEach(function(sec){
          var any = false;
          sec.querySelectorAll('.row').forEach(function(r){
            if (r.dataset.kindFiltered !== 'hide' && !r.classList.contains('is-hidden')) any = true;
          });
          sec.classList.toggle('is-kind-hidden', !any);
        });
        // style タグ経由で CSS ルールを切り替える
        var st = document.getElementById('kind-filter-style');
        if (!st){
          st = document.createElement('style');
          st.id = 'kind-filter-style';
          st.textContent = '.row[data-kind-filtered="hide"]{display:none !important;} .category.is-kind-hidden{display:none !important;}';
          document.head.appendChild(st);
        }
        // アクティブ状態の見た目を更新
        btns.forEach(function(x){
          x.style.background = (x.getAttribute('data-kind-filter') === k) ? 'var(--accent-soft)' : (x.getAttribute('data-kind-filter') ? 'var(--bg-elev)' : 'transparent');
          x.style.borderColor = (x.getAttribute('data-kind-filter') === k) ? 'var(--accent)' : (x.getAttribute('data-kind-filter') ? 'var(--rule)' : 'var(--rule-soft)');
        });
      });
    });
  })();
  </script>"""

    return f"""  <h3><span class="prompt">$</span> filter</h3>
  <div class="filter-row">
{src_buttons}
{cat_html}
    <button class="clear-btn" id="clear-btn" type="button">クリア ⨯</button>
  </div>
  {kind_row_html}
  <div class="active-filters" id="active-filters"></div>
{kind_filter_js}"""


def build_main(entries: list[dict]) -> str:
    parts: list[str] = []
    idx = 1
    for kind in KIND_ORDER:
        kind_entries = [e for e in entries if e["kind"] == kind]
        if not kind_entries:
            continue
        parts.append('  <div class="section-head">')
        parts.append(f"    <h2>{KIND_LABELS[kind]}</h2>")
        desc = {
            "plugin": "`/plugin install` または `claude mcp add`",
            "skill": ".claude/skills/<cat>/<name>/SKILL.md",
            "subagent": ".claude/agents/<name>.md",
            "command": ".claude/commands/<name>.md",
        }.get(kind, "")
        parts.append(f"    <p>{desc}</p>")
        parts.append("  </div>")
        parts.append("")
        grouped: dict[str, list[dict]] = {}
        for e in kind_entries:
            grouped.setdefault(e["category"], []).append(e)
        for cat in CATEGORY_ORDER_BY_KIND.get(kind, []) + sorted(
            set(grouped) - set(CATEGORY_ORDER_BY_KIND.get(kind, []))
        ):
            if cat in grouped:
                parts.append(render_category_section(idx, cat, grouped[cat], kind))
                idx += 1
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check", action="store_true", help="HTML が古い場合、非ゼロで終了する")
    ap.add_argument(
        "--no-discover",
        action="store_true",
        help="ファイルシステム探索をスキップする（CATALOG.md を手動管理として扱う）",
    )
    args = ap.parse_args()

    if lock_held():
        log(args.quiet, "build_catalog: ロック取得中のためスキップ（自己再帰ガード）")
        return 0

    if not SOURCE_MD.exists():
        log(args.quiet, f"build_catalog: ソースが見つかりません: {SOURCE_MD}")
        return 1

    text = SOURCE_MD.read_text(encoding="utf-8")

    # ステップ A: ファイルシステム探索 + CATALOG.md への追加/削除同期
    if not args.no_discover:

        def warn(msg):
            log(args.quiet, f"build_catalog: 警告 {msg}")

        discovered = {
            "subagent": discover_subagents(PROJECT_ROOT),
            "command": discover_commands(PROJECT_ROOT),
            "skill": discover_skills(PROJECT_ROOT, warn=warn),
        }
        new_text, added, removed = sync_catalog_md(text, discovered)
        if new_text != text:
            for kind in ("subagent", "skill", "command"):
                if added.get(kind):
                    log(args.quiet, f"build_catalog: {kind} を {len(added[kind])} 件追加: {', '.join(added[kind])}")
                if removed.get(kind):
                    log(args.quiet, f"build_catalog: {kind} を {len(removed[kind])} 件削除: {', '.join(removed[kind])}")
            if not args.check:
                # CATALOG.md を書き込む前にロックを取得し、Write の PostToolUse hook が
                # 自分自身を再帰的に呼ばないようにする。
                acquire_lock()
                try:
                    SOURCE_MD.write_text(new_text, encoding="utf-8")
                finally:
                    release_lock()
            text = new_text

    meta, entries = parse_md(text)
    if not entries:
        log(args.quiet, "build_catalog: エントリを1件もパースできませんでした。中断します")
        return 1

    apply_enabled_state(entries, SETTINGS_JSON)
    apply_filesystem_state(entries, PROJECT_ROOT)

    by_kind = count_by(entries, "kind")
    kind_summary = ", ".join(f"{by_kind[k]} {k}" for k in KIND_ORDER if by_kind.get(k))

    placeholders = {
        "TITLE": "catalog/ — Claude Code 統合カタログ",
        "BRAND_PATH": "CATALOG.md",
        "SEARCH_PLACEHOLDER": "検索 — 例: firecrawl, github, lsp",
        "TOTAL_COUNT": str(len(entries)),
        "HERO": build_hero(meta, entries),
        "STATS": build_stats(entries),
        "FILTER_BAR": build_filter_bar(entries),
        "MAIN": build_main(entries),
        "VERSION_LABEL": f"v {meta.get('version', date.today())} catalog",
    }
    output = render_template(placeholders)

    if args.check:
        existing = OUTPUT_HTML.read_text(encoding="utf-8") if OUTPUT_HTML.exists() else ""
        if existing != output:
            print(f"DRIFT: {OUTPUT_HTML} は古くなっています", file=sys.stderr)
            return 2
        log(args.quiet, "build_catalog: HTML は最新です")
        return 0

    acquire_lock()
    try:
        OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_HTML.write_text(output, encoding="utf-8")
    finally:
        release_lock()
    log(args.quiet, f"build_catalog: {OUTPUT_HTML} を書き込みました（{len(entries)} entries: {kind_summary}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

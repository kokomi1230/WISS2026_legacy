"""docs の Markdown を全文のまま Notion の研究ノートへ投入する。

- 原文の見出し・段落・表・コードブロックをそのまま移す（要約しない）
- 冒頭に要点 callout、末尾に取り込み元セクションを足す
- 言語指定の無いフェンスに言語を補う（Notion の誤検出を防ぐ）
- spec で指定された ASCII 図の直前へ mermaid を差し込む
- spec で指定された重複箇所を置換する
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _config_dir import config_dir, resolve_source  # noqa: E402

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
SPEC = Path(__file__).with_name("spec.json")
# 投入済み本文のハッシュ。--check で原文の更新を検出するために使う
STATE = Path(__file__).with_name("ingest_state.json")

BOX = set("├└│┌┐┘┤┬┴┼─→←↓↑▼▲")
FENCE_OPEN = re.compile(r"^```(\S*)\s*$")
# Notion は地の文の `foo.md` をドメインとみなし http://foo.md へリンク化する。
# ファイル名はコードなので、バッククォートで囲んで誤リンクを止める。
# Notion は `base_mode.py` の一部（`mode.py`）や `settings/README.md` の末尾だけも拾うため、
# パスの区切りとアンダースコアを含めたトークン全体を囲む必要がある。
FILE_EXT = "md|py|html|yaml|yml|json|toml|cfg|txt|sh|ts|tsx|js|css|psyexp|bib|csv|lock|ini"
# 境界は ASCII で判定する。`\w` は和文にもマッチするため、
# 「過剰なCLAUDE.md」「CLAUDE.mdの肥大化」のように和文と隣接した名前を取りこぼす。
BARE_FILE = re.compile(
    rf"(?<![A-Za-z0-9_/`.\-])((?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_][A-Za-z0-9_.\-]*\.(?:{FILE_EXT}))(?![A-Za-z0-9_`/])"
)
BASH_HEAD = (
    "$",
    "uv ",
    "python",
    "pip ",
    "cd ",
    ".venv/",
    "CI=",
    "git ",
    "npx ",
    "claude ",
    "pytest",
    "black ",
    "mypy ",
    "rm ",
    "ls ",
    "find ",
    "grep ",
    "curl ",
    "open ",
    "dotnet ",
    "QT_QPA",
)


def token() -> str:
    """.env から NOTION_TOKEN を読む。

    .env が無い場合も SystemExit にする。traceback を出しても利用者にできることは
    「.env を作る」しかなく、原因が読み取りにくくなるだけである。
    """
    env = config_dir() / ".env"
    if not env.is_file():
        raise SystemExit(f"{env} がありません。user-scope/.env.example をコピーして NOTION_TOKEN を記入してください")
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("NOTION_TOKEN="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit(f"{env} に NOTION_TOKEN がありません")


def guess_language(body: str) -> str:
    """言語指定の無いフェンスに与える言語を決める。"""
    stripped = [line for line in body.splitlines() if line.strip()]
    if not stripped:
        return "text"
    first = stripped[0].lstrip()
    if any(ch in BOX for ch in body):
        return "text"
    if first.startswith(("{", "[")):
        return "json"
    if any(first.startswith(h) for h in BASH_HEAD):
        return "bash"
    return "text"


def tag_fences(text: str) -> str:
    """言語指定の無いフェンスへ言語を補う。"""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        lang = m.group(1)
        body: list[str] = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith("```"):
            body.append(lines[j])
            j += 1
        if not lang:
            lang = guess_language("\n".join(body))
        out.append(f"```{lang}")
        out.extend(body)
        out.append("```" if j < len(lines) else "```")
        i = j + 1
    return "\n".join(out)


def insert_mermaid(text: str, figures: list[dict]) -> tuple[str, int]:
    """mermaid ブロックを差し込む。

    anchor がフェンス内にあればそのフェンスの直前へ、地の文にあればその行の直後へ置く。
    前者は ASCII 図の言い換え、後者は文章で書かれた流れの図示にあたる。
    """
    inserted = 0
    for fig in figures:
        anchor = fig["anchor"]
        lines = text.splitlines()
        block = ["", "```mermaid", fig["code"].rstrip(), "```", ""]

        target = None
        for idx, line in enumerate(lines):
            if not FENCE_OPEN.match(line):
                continue
            j = idx + 1
            while j < len(lines) and not lines[j].startswith("```"):
                if anchor in lines[j]:
                    target = idx
                    break
                j += 1
            if target is not None:
                break

        if target is None:
            for idx, line in enumerate(lines):
                if anchor in line:
                    target = idx + 1
                    break
        if target is None:
            print(f"    [警告] anchor が見つからない: {anchor[:40]!r}")
            continue

        lines[target:target] = block
        text = "\n".join(lines)
        inserted += 1
    return text, inserted


def strip_h1(text: str) -> str:
    """先頭の H1 だけを落とす。

    「最初に現れた `# ` の行」を消すとコードブロック内のコメントを誤って消しうるため、
    本文の最初の非空行が H1 のときに限って落とす。
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if line.startswith("# "):
            del lines[i]
            while i < len(lines) and not lines[i].strip():
                del lines[i]
        break
    return "\n".join(lines)


def quote_bare_filenames(text: str) -> str:
    """地の文の裸のファイル名をバッククォートで囲む。

    コードスパン・フェンス・リンク記法の中は触らない。Notion の自動リンク化対策。
    """
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # コードスパンとリンクを退避してから置換し、あとで戻す
        holds: list[str] = []

        def hold(m: re.Match[str]) -> str:
            holds.append(m.group(0))
            return f"\x00{len(holds) - 1}\x00"

        masked = re.sub(r"`[^`]*`|\[[^\]]*\]\([^)]*\)", hold, line)
        masked = BARE_FILE.sub(lambda m: f"`{m.group(1)}`", masked)
        out.append(re.sub(r"\x00(\d+)\x00", lambda m: holds[int(m.group(1))], masked))
    return "\n".join(out)


def build_body(entry: dict) -> str:
    primary = resolve_source(entry["primary"])
    text = primary.read_text(encoding="utf-8")

    for edit in entry.get("edits", []):
        if edit["old"] not in text:
            print(f"    [警告] edits の old が見つからない: {edit['old'][:40]!r}")
            continue
        text = text.replace(edit["old"], edit["new"], 1)

    text = strip_h1(text)
    text = quote_bare_filenames(text)
    text = tag_fences(text)
    text, n_fig = insert_mermaid(text, entry.get("mermaid", []))

    size_kb = primary.stat().st_size / 1024
    n_lines = len(primary.read_text(encoding="utf-8").splitlines())
    head = [
        '<callout icon="/icons/document_gray.svg" color="gray_bg">',
        f"\t**{entry['source_title']}**",
        f"\t{entry['lead']}",
        f"\t出典: `{entry['primary']}`（{n_lines} 行 / {size_kb:.1f} KB）",
    ]
    if entry.get("html"):
        head.append(f"\t清書版 HTML: `~/.notion-mirror/{entry['html']}`")
    # `---` の前後に空行を置く。空行が無いと直前の行が setext 見出しとして解釈される
    head += ["</callout>", "", "---", "", ""]

    tail = ["", "", "---", "", "## 取り込み元", ""]
    for src in entry["sources"]:
        note = "" if src == entry["primary"] else "（上と同一内容）"
        tail.append(f"- `{src}`{note}")

    return "\n".join(head) + text.strip() + "\n".join(tail) + "\n", n_fig


def patch(page_id: str, body: str, auth: str) -> dict:
    req = urllib.request.Request(
        f"{API}/pages/{page_id}/markdown",
        data=json.dumps({"type": "replace_content", "replace_content": {"new_str": body}}).encode("utf-8"),
        headers={"Authorization": f"Bearer {auth}", "Notion-Version": VERSION, "Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=300) as res:
        return json.loads(res.read().decode("utf-8"))


def load_state() -> dict[str, str]:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    check = "--check" in args
    only = next((a for a in args if not a.startswith("--")), None)
    entries = json.loads(SPEC.read_text(encoding="utf-8"))
    state = load_state()

    if check:
        stale = []
        for entry in entries:
            body, _ = build_body(entry)
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if state.get(entry["page_id"]) != digest:
                stale.append(entry["primary"])
        if stale:
            print(f"投入し直しが要るノート {len(stale)} 件（原文が変わったか未投入）:")
            for p in stale:
                print(f"  {p}")
        else:
            print(f"{len(entries)} 件すべて Notion と原文が一致している")
        return

    auth = token()
    total_in = 0
    for entry in entries:
        if only and only not in entry["primary"]:
            continue
        body, n_fig = build_body(entry)
        size = len(body.encode("utf-8"))
        total_in += size
        label = f"{entry['primary']:<70s} {size:>7d} B"
        if n_fig:
            label += f"  mermaid×{n_fig}"
        if dry:
            print(f"[dry] {label}")
            continue
        try:
            result = patch(entry["page_id"], body, auth)
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")[:300]
            print(f"[NG ] {label}\n       HTTP {err.code}: {detail}")
            continue
        flag = "truncated!" if result.get("truncated") else "ok"
        if not result.get("truncated"):
            state[entry["page_id"]] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        print(f"[{flag:>4s}] {label}")
    if not dry:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n投入合計: {total_in} B")


if __name__ == "__main__":
    main()

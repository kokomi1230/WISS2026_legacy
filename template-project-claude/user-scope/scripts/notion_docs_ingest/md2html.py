"""docs の Markdown を解説資料テンプレートの HTML へ起こす。

テンプレートの CSS とスクリプトは explainer-doc-html skill の assets から取り込むため、
そこを直せば全 HTML に反映される。
内容 → 部品の割り当ては explainer-doc-html skill の対応表に従う。
`.note` / `.caution` / `.info` への昇格だけは機械判定できないため hints.json で指定する。
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _config_dir import config_dir, mirror_dir, resolve_source  # noqa: E402

# テンプレートの原本は explainer-doc-html skill の assets。skill 本体と同じ場所に
# 置くことで、どのマシン・どのプロジェクトからでも同じものが確実に見つかる。
# 別のテンプレートで起こしたい場合だけ EXPLAINER_TEMPLATE で上書きする。
TEMPLATE = Path(
    os.environ.get("EXPLAINER_TEMPLATE") or config_dir() / "skills" / "explainer-doc-html" / "assets" / "template.html"
)
OUT_ROOT = mirror_dir()
HERE = Path(__file__).parent

# 対話部品を入れる閾値。短い表に付けても操作する動機が無く、記号が並ぶだけ騒がしくなる
LONG_TABLE_ROWS = 8

# テンプレートに pre の定義が無いので補う。配色トークンは原本のものを使う
EXTRA_CSS = """
  pre{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--rule);
    border-radius:4px;padding:14px 16px;margin:16px 0;overflow-x:auto;font-size:.82rem;line-height:1.6;}
  pre code{background:none;padding:0;font-size:1em;white-space:pre;}
  .srcline{font-size:.8rem;color:var(--sub);margin-top:6px;}
"""

WARN_WORDS = (
    "注意",
    "禁止",
    "不可",
    "避ける",
    "してはならない",
    "非対応",
    "失敗",
    "危険",
    "壊",
    "消え",
    "破綻",
    "厳禁",
)

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
QA = re.compile(r"^\*\*Q[.．]\s*(.+?)\*\*$")
# 部制の見出し。h1 で書けば以降の複数節がその部に属し、h2 で書けばその節ひとつで部になる
PART = re.compile(r"^第([0-9０-９一二三四五六七八九十]+)部[：:　\s]*(.*)$")


def inline(text: str) -> str:
    """インライン記法を HTML へ。エスケープ後にタグを戻す。"""
    text = html.escape(text)
    text = INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = LINK.sub(lambda m: f'<a class="inline" href="{m.group(2)}" target="_blank">{m.group(1)}</a>', text)
    return text


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


class Converter:
    """Markdown を解説資料テンプレートの HTML へ変換する。

    hints.json の指示に従い、段落をコールアウト（要点 / 注意 / 補足）へ昇格させる。
    """

    def __init__(self, hints: list[dict]) -> None:
        """hints は anchor（本文中の部分一致文字列）と kind の対応表。"""
        self.hints = hints

    def hint_for(self, text: str) -> dict | None:
        """本文に anchor が含まれる最初の hint を返す。無ければ None。"""
        for h in self.hints:
            if h["anchor"] in text:
                return h
        return None

    def paragraph(self, text: str, is_lead: bool) -> str:
        """段落を <p> かコールアウト <div> として描画する。"""
        hint = self.hint_for(text)
        if hint:
            kind = hint["kind"]
            label = {"note": "要点", "caution": "注意", "info": "補足"}[kind]
            return f'<div class="{kind}"><span class="lbl">{label}</span><p>{inline(text)}</p></div>'
        cls = ' class="lead"' if is_lead else ""
        return f"<p{cls}>{inline(text)}</p>"

    def convert(self, md: str) -> tuple[str, str, str, list[dict]]:
        """Markdown 全体を (タイトル, リード文, 本文 HTML, 目次) へ変換する。

        目次は部制なら部でまとめた入れ子、そうでなければ節の平坦な並びになる。
        """
        lines = md.splitlines()
        title = ""
        intro: list[str] = []
        sections: list[dict] = []
        current: dict | None = None
        part: dict | None = None
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            if line.startswith("# ") and not title:
                title = line[2:].strip()
                i += 1
                continue

            # 2 つめ以降の h1 が「第N部」なら部の区切り。以降の節がその部に属する
            if line.startswith("# "):
                matched = PART.match(line[2:].strip())
                if matched:
                    part = {"label": f"第{matched.group(1)}部", "name": matched.group(2).strip(), "mark": True}
                    current = None
                    i += 1
                    continue

            if line.startswith("## "):
                heading = line[3:].strip()
                matched = PART.match(heading)
                if matched:
                    # h2 で書かれた部は、その節ひとつで 1 部をなす（次の節は部の外へ出る）
                    part = {"label": f"第{matched.group(1)}部", "name": matched.group(2).strip() or heading, "mark": False}
                current = {"title": heading, "html": [], "lead_done": False, "part": part}
                if part and part.pop("mark", False):
                    current["partmark"] = part
                sections.append(current)
                if matched:
                    part = None
                i += 1
                continue

            sink = current["html"] if current else intro

            if line.startswith("```"):
                lang = line[3:].strip()
                body: list[str] = []
                i += 1
                while i < n and not lines[i].startswith("```"):
                    body.append(lines[i])
                    i += 1
                i += 1
                code = html.escape("\n".join(body))
                cls = f' class="language-{lang}"' if lang else ""
                sink.append(f"<pre><code{cls}>{code}</code></pre>")
                continue

            if line.startswith("### "):
                sink.append(f"<h3>{inline(line[4:].strip())}</h3>")
                i += 1
                continue

            if line.startswith("#### "):
                sink.append(f"<h3>{inline(line[5:].strip())}</h3>")
                i += 1
                continue

            if line.startswith("|") and i + 1 < n and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
                header = split_row(line)
                i += 2
                rows = []
                while i < n and lines[i].startswith("|"):
                    rows.append(split_row(lines[i]))
                    i += 1
                sink.append(self.table(header, rows))
                continue

            m = QA.match(line.strip())
            if m:
                answer: list[str] = []
                i += 1
                while i < n and lines[i].strip() and not lines[i].startswith(("#", "**Q", "|", "```")):
                    answer.append(lines[i].strip())
                    i += 1
                body = " ".join(answer)
                sink.append(
                    f"<details><summary>{inline(m.group(1))}</summary>"
                    f'<div class="qbody"><p>{inline(body)}</p></div></details>'
                )
                continue

            if line.startswith(("- ", "* ")) or re.match(r"^\d+\. ", line):
                ordered = bool(re.match(r"^\d+\. ", line))
                items: list[str] = []
                while i < n and (lines[i].startswith(("- ", "* ", "  ", "\t")) or re.match(r"^\d+\. ", lines[i])):
                    raw = lines[i]
                    if raw.startswith(("- ", "* ")):
                        items.append(raw[2:].strip())
                    elif re.match(r"^\d+\. ", raw):
                        items.append(re.sub(r"^\d+\. ", "", raw).strip())
                    elif items:
                        items[-1] += " " + raw.strip()
                    i += 1
                sink.append(self.list_block(items, ordered))
                continue

            if line.startswith(">"):
                quote: list[str] = []
                while i < n and lines[i].startswith(">"):
                    quote.append(lines[i].lstrip("> ").strip())
                    i += 1
                text = " ".join(q for q in quote if q)
                sink.append(f'<div class="info"><span class="lbl">補足</span><p>{inline(text)}</p></div>')
                continue

            if line.strip() in ("", "---", "***"):
                i += 1
                continue

            para = [line.strip()]
            i += 1
            while i < n and lines[i].strip() and not lines[i].startswith(("#", "-", "*", ">", "|", "```", "1.")):
                para.append(lines[i].strip())
                i += 1
            text = " ".join(para)
            if current is None:
                intro.append(f"<p>{inline(text)}</p>")
                continue
            is_lead = not current["lead_done"]
            current["lead_done"] = True
            sink.append(self.paragraph(text, is_lead))

        toc: list[dict] = []
        main = []
        for k, s in enumerate(sections, 1):
            entry = {"id": f"s{k}", "number": k, "title": s["title"]}
            group = s["part"]
            if group is None:
                toc.append(entry)
            else:
                if not toc or toc[-1].get("part") is not group:
                    toc.append({"part": group, "items": []})
                # 部の見出しに名前が出るので、目次の項目名からは「第N部：」を落とす
                matched = PART.match(entry["title"])
                if matched and matched.group(2).strip():
                    entry["title"] = matched.group(2).strip()
                toc[-1]["items"].append(entry)
            mark = s.get("partmark")
            if mark:
                main.append(f'<div class="partmark"><span class="lbl">{mark["label"]}</span><h2>{inline(mark["name"])}</h2></div>')
            main.append(
                f'<section id="s{k}">\n  <span class="secnum">SECTION {k}</span>\n'
                f'  <h2>{inline(s["title"])}</h2>\n  <hr class="h2rule">\n  ' + "\n  ".join(s["html"]) + "\n</section>"
            )
        lead_html = "\n".join(intro)
        lead_text = re.sub(r"<[^>]+>", "", lead_html).strip()
        return title, lead_text, "\n\n".join(main), toc

    def table(self, header: list[str], rows: list[list[str]]) -> str:
        """表を描画する。1 列目は行見出しとして rowhead クラスを付ける。

        行が多い表だけ列ソートと折りたたみを有効にする。短い表は一覧できているので、
        操作の余地を出しても使われず、見出しに記号が並ぶ分だけ読みにくくなる。
        """
        th = "".join(f"<th>{inline(c)}</th>" for c in header)
        body = []
        for row in rows:
            cells = []
            for idx, c in enumerate(row):
                cls = ' class="rowhead"' if idx == 0 else ""
                cells.append(f"<td{cls}>{inline(c)}</td>")
            body.append("<tr>" + "".join(cells) + "</tr>")
        long_table = len(rows) > LONG_TABLE_ROWS
        wrap_attr = f' data-collapse="{LONG_TABLE_ROWS}"' if long_table else ""
        table_attr = ' class="sortable"' if long_table else ""
        return (
            f'<div class="tablewrap"{wrap_attr}>\n    <table{table_attr}>\n      <thead><tr>'
            + th
            + "</tr></thead>\n      <tbody>\n        "
            + "\n        ".join(body)
            + "\n      </tbody>\n    </table>\n  </div>"
        )

    def list_block(self, items: list[str], ordered: bool) -> str:
        """箇条書きを <ol> / <ul> として描画する。"""
        if ordered:
            lis = "".join(f"<li>{inline(t)}</li>" for t in items)
            return f"<ol>{lis}</ol>"
        lis = []
        for t in items:
            warn = ' class="warn"' if any(w in t for w in WARN_WORDS) else ""
            lis.append(f"<li{warn}>{inline(t)}</li>")
        return '<ul class="clean">' + "".join(lis) + "</ul>"


def template_parts() -> tuple[str, str]:
    raw = TEMPLATE.read_text(encoding="utf-8")
    css = raw.split("<style>", 1)[1].split("</style>", 1)[0]
    script = raw.split("<script>", 1)[1].split("</script>", 1)[0]
    return css, script


def toc_item(entry: dict) -> str:
    return f'<li><a href="#{entry["id"]}">{entry["number"]}. {html.escape(entry["title"])}</a></li>'


def render_toc(toc: list[dict]) -> str:
    """目次を描画する。部があれば details で束ね、無ければ平坦な ol にする。"""
    if not any("part" in entry for entry in toc):
        items = "\n      ".join(toc_item(entry) for entry in toc)
        return f'<ol id="toc">\n      {items}\n    </ol>'
    blocks = []
    for entry in toc:
        if "part" not in entry:
            blocks.append(f"<ol>{toc_item(entry)}</ol>")
            continue
        group = entry["part"]
        heading = f'{group["label"]}　{html.escape(group["name"])}' if group["name"] else group["label"]
        # 部が 1 節だけなら、開閉させても中身は見出しの繰り返しにしかならないので 1 行に畳む
        if len(entry["items"]) == 1 and entry["items"][0]["title"] == group["name"]:
            item = entry["items"][0]
            blocks.append(
                f'<ol><li><a href="#{item["id"]}"><span class="part-lbl">{group["label"]}</span>'
                f'{html.escape(item["title"])}</a></li></ol>'
            )
            continue
        items = "\n          ".join(toc_item(item) for item in entry["items"])
        blocks.append(
            '<details class="toc-part" open>\n'
            f'        <summary>{heading}<span class="part-progress">0/{len(entry["items"])}</span></summary>\n'
            f"        <ol>\n          {items}\n        </ol>\n      </details>"
        )
    body = "\n      ".join(blocks)
    return f'<nav id="toc">\n      {body}\n    </nav>'


def render(title: str, kicker: str, lead: str, main: str, toc: list[dict], footer: str) -> str:
    css, script = template_parts()
    toc_html = render_toc(toc)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>{css}{EXTRA_CSS}</style>
</head>
<body>

<div class="masthead">
  <div class="inner">
    <p class="kicker">{html.escape(kicker)}</p>
    <h1>{html.escape(title)}</h1>
    <p>{inline(lead)}</p>
  </div>
</div>

<div class="layout">
  <aside>
    <p class="toc-title">目次</p>
    {toc_html}
  </aside>

  <main>
{main}

    <footer>
      {footer}
    </footer>
  </main>
</div>

<script>{script}</script>
</body>
</html>
"""


def main() -> None:
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    hints_all = json.loads((HERE / "hints.json").read_text(encoding="utf-8"))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    made = 0
    for entry in spec:
        if not entry.get("html"):
            continue
        if only and only not in entry["primary"]:
            continue
        src = resolve_source(entry["primary"])
        out = OUT_ROOT / entry["html"]
        out.parent.mkdir(parents=True, exist_ok=True)
        conv = Converter(hints_all.get(entry["primary"], []))
        title, lead, body, toc = conv.convert(src.read_text(encoding="utf-8"))
        title = title or entry["source_title"]
        lead = lead or entry["lead"]
        kicker = entry["primary"].split("/", 1)[0]
        footer = (
            f'出典: <code>{html.escape(entry["primary"])}</code>'
            f'<div class="srcline">Notion ノート「{html.escape(entry["note_title"])}」の清書版。'
            f"原文を更新したら本ファイルも作り直すこと。</div>"
        )
        out.write_text(render(title, kicker, lead, body, toc, footer), encoding="utf-8")
        parts = sum(1 for item in toc if "part" in item)
        shape = f"parts={parts}" if parts else f"sections={len(toc)}"
        print(f"{out.stat().st_size:>7d} B  {entry['html']}  ({shape}, hints={len(conv.hints)})")
        made += 1
    print(f"\n{made} 本を生成した")


if __name__ == "__main__":
    main()

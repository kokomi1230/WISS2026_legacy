"""投入した本文が原文と一致しているかを行単位で突き合わせる。

ingest.build_body の出力から冒頭 callout と末尾の取り込み元を外し、
原文の各行がすべて残っているかを確認する。意図した差分（H1 削除・言語補完・
mermaid 追加・重複整理）だけが出るはずで、それ以外の欠落はバグである。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _config_dir import resolve_source  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from ingest import build_body  # noqa: E402

SPEC = Path(__file__).with_name("spec.json")


def normalize(line: str) -> str:
    """バッククォートの有無と空白の差を無視して比べる。

    裸のファイル名を `foo.md` へ囲む変換を入れたため、素の一致では偽陽性になる。
    """
    return line.replace("`", "").replace(" ", "").replace("　", "")


def strip_wrapper(body: str) -> str:
    after = body.split("</callout>", 1)[1]
    after = after.lstrip("\n").removeprefix("---").lstrip("\n")
    return after.rsplit("\n\n---\n\n## 取り込み元", 1)[0]


def main() -> None:
    entries = json.loads(SPEC.read_text(encoding="utf-8"))
    total_missing = 0
    for entry in entries:
        src_text = resolve_source(entry["primary"]).read_text(encoding="utf-8")
        body, _ = build_body(entry)
        inner = strip_wrapper(body)
        inner_lines = {normalize(line) for line in inner.splitlines()}

        edited_away = set()
        for edit in entry.get("edits", []):
            edited_away |= {normalize(line) for line in edit["old"].splitlines()}

        missing = []
        for line in src_text.splitlines():
            s = line.strip()
            if not s or normalize(line) in inner_lines:
                continue
            if normalize(line) in edited_away:
                continue
            if s.startswith("# ") and src_text.lstrip().startswith(line):
                continue  # H1 は意図的に落とす
            if s.startswith("```"):
                continue  # 言語を補ったフェンスは別途チェック
            missing.append(line)

        if missing:
            total_missing += len(missing)
            print(f"\n[欠落] {entry['primary']}  {len(missing)} 行")
            for line in missing[:5]:
                print(f"    {line[:100]}")

    print(f"\n原文行の欠落: 合計 {total_missing} 行")


if __name__ == "__main__":
    main()

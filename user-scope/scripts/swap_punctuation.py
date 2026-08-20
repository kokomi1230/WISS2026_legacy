#!/usr/bin/env python3
r"""日本語の句読点を学術スタイルと一般スタイルの間で変換する。

学術スタイル: ， ．（論文・申請書向け）
一般スタイル: 、 。（一般文書・Web コンテンツ向け）

誤変換を防ぐため、以下の範囲は変換対象から除外する:
- コードブロック（``` ... ```）およびインラインコード（`...`）
- LaTeX 数式環境（$...$、$$...$$、\\begin{equation}...\\end{equation} 等）
- URL（http://, https://, ftp://）
- HTML/Markdown タグの中身（<...>）

Usage:
  python3 swap_punctuation.py --to=academic FILE [FILE ...]
  python3 swap_punctuation.py --to=general FILE [FILE ...]
  python3 swap_punctuation.py --to=academic --check FILE      # 検出のみ
  python3 swap_punctuation.py --to=academic --stdin           # 標準入出力で処理
  python3 swap_punctuation.py --to=academic --dry-run FILE    # 差分件数のみ表示
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

ACADEMIC = {"comma": "，", "period": "．"}
GENERAL = {"comma": "、", "period": "。"}

FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HTML_TAG_RE = re.compile(r"<[^<>\n]+>")
URL_RE = re.compile(r"\b(?:https?|ftp)://[A-Za-z0-9._~:/?#@!$&'()*+,;=%\-\[\]]+")
LATEX_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)[^\$\n]+\$(?!\$)")
LATEX_DISPLAY_RE = re.compile(r"\$\$.+?\$\$", re.DOTALL)
LATEX_ENV_RE = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath|math)\*?\}" r".*?" r"\\end\{\1\*?\}",
    re.DOTALL,
)


PROTECTED_PATTERNS = (
    FENCED_CODE_RE,
    LATEX_DISPLAY_RE,
    LATEX_ENV_RE,
    INLINE_CODE_RE,
    LATEX_INLINE_RE,
    URL_RE,
    HTML_TAG_RE,
)


def _mask_protected(text: str) -> tuple[str, list[str]]:
    """保護対象の範囲をプレースホルダーに置換する。マスク済みテキストと元の断片一覧を返す。"""
    parts: list[str] = []

    def _repl(match: re.Match) -> str:
        parts.append(match.group(0))
        return f"\x00PROTECT{len(parts) - 1}\x00"

    masked = text
    for pat in PROTECTED_PATTERNS:
        masked = pat.sub(_repl, masked)
    return masked, parts


_PLACEHOLDER_RE = re.compile(r"\x00PROTECT(\d+)\x00")


def _unmask(masked: str, parts: list[str]) -> str:
    """プレースホルダーを元の断片へ戻す。入れ子が解けるまで繰り返す。

    後段のパターンが前段のプレースホルダーごと捕捉することがある（例:
    `$100 と `code` と $200` では、インラインコードを退避した後の
    プレースホルダーを LaTeX インライン数式が丸ごと取り込む）。re.sub は
    置換結果を再走査しないため、1 回で済ませると入れ子のプレースホルダーが
    そのまま出力に残り、保護したはずの断片を失う。
    """
    text = masked
    # 入れ子の深さは保護パターン数を超えない。上限は無限ループの保険。
    for _ in range(len(PROTECTED_PATTERNS) + 1):
        if not _PLACEHOLDER_RE.search(text):
            break
        text = _PLACEHOLDER_RE.sub(lambda m: parts[int(m.group(1))], text)
    return text


def swap(text: str, target: str) -> tuple[str, int, int]:
    """テキスト中の句読点を変換する。(変換後テキスト, カンマ数, 句点数) を返す。"""
    if target == "academic":
        src_comma, src_period = GENERAL["comma"], GENERAL["period"]
        dst_comma, dst_period = ACADEMIC["comma"], ACADEMIC["period"]
    elif target == "general":
        src_comma, src_period = ACADEMIC["comma"], ACADEMIC["period"]
        dst_comma, dst_period = GENERAL["comma"], GENERAL["period"]
    else:
        raise ValueError(f"不明な変換先です: {target!r}")

    masked, parts = _mask_protected(text)
    comma_count = masked.count(src_comma)
    period_count = masked.count(src_period)
    swapped = masked.replace(src_comma, dst_comma).replace(src_period, dst_period)
    return _unmask(swapped, parts), comma_count, period_count


def detect(text: str) -> dict:
    """保護対象を除く範囲で、両スタイルの句読点数をそれぞれ数える。"""
    masked, _ = _mask_protected(text)
    return {
        "general_comma": masked.count(GENERAL["comma"]),
        "general_period": masked.count(GENERAL["period"]),
        "academic_comma": masked.count(ACADEMIC["comma"]),
        "academic_period": masked.count(ACADEMIC["period"]),
    }


def _iter_paths(paths: Iterable[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for sub in sorted(path.rglob("*")):
                if sub.is_file() and sub.suffix.lower() in {".md", ".txt", ".tex", ".rst", ".org"}:
                    yield sub
        else:
            yield path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--to",
        choices=["academic", "general"],
        required=False,
        help="変換先スタイル（--check 指定時は不要）",
    )
    ap.add_argument("--check", action="store_true", help="変換せず句読点の使用状況のみ検出する")
    ap.add_argument("--dry-run", action="store_true", help="書き込まず変更件数のみ表示する")
    ap.add_argument("--stdin", action="store_true", help="標準入力を読み標準出力へ書く（files は無視）")
    ap.add_argument("files", nargs="*", help="処理対象のファイルまたはディレクトリ")
    args = ap.parse_args()

    if not args.check and not args.to:
        print("error: --check を指定しない場合は --to が必須です", file=sys.stderr)
        return 2

    if args.stdin:
        text = sys.stdin.read()
        if args.check:
            counts = detect(text)
            print(_format_counts("<stdin>", counts))
            return 0
        new_text, c, p = swap(text, args.to)
        if args.dry_run:
            print(f"<stdin>: 変換予定 カンマ={c}件, 句点={p}件", file=sys.stderr)
        sys.stdout.write(new_text)
        return 0

    if not args.files:
        print("error: ファイル/ディレクトリを指定するか --stdin を使用してください", file=sys.stderr)
        return 2

    total_changed = 0
    for path in _iter_paths(args.files):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            print(f"スキップ: {path}: {exc}", file=sys.stderr)
            continue

        if args.check:
            counts = detect(text)
            print(_format_counts(str(path), counts))
            continue

        new_text, c, p = swap(text, args.to)
        if new_text == text:
            continue
        if args.dry_run:
            print(f"{path}: 変換予定 カンマ={c}件, 句点={p}件")
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"{path}: 変換済み カンマ={c}件, 句点={p}件")
        total_changed += 1

    if not args.check and not args.dry_run:
        print(f"---\n変更ファイル数: {total_changed}", file=sys.stderr)
    return 0


def _format_counts(label: str, counts: dict) -> str:
    return (
        f"{label}: "
        f"general(、{counts['general_comma']} / 。{counts['general_period']}), "
        f"academic(，{counts['academic_comma']} / ．{counts['academic_period']})"
    )


if __name__ == "__main__":
    raise SystemExit(main())

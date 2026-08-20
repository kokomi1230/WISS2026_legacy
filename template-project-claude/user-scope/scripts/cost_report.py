#!/usr/bin/env python3
"""ローカルの Claude Code セッションログを日次の USD コスト表に集計する。

~/.claude/projects/**/*.jsonl（このマシン上の全プロジェクト。Claude Code 本体の
`/usage` コマンドと同じスコープ）を読み、モデル別に API 従量課金換算コストを
日別集計する。あくまで推定値である。Claude Max/Pro サブスクリプションはトークン
単位ではなく定額制で課金される。

料金表 最終確認: 2026-07-07 (platform.claude.com/docs/en/about-claude/pricing)

Usage:
  python3 cost_report.py                          # 直近7日間、Asia/Tokyo、全プロジェクト
  python3 cost_report.py --days 14                # 直近14日間
  python3 cost_report.py --tz UTC                  # UTC のカレンダー日で集計
  python3 cost_report.py --project-only            # カレントプロジェクトのログのみ
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# 100万トークンあたりの $: (入力, 出力, 5分キャッシュ書込, 1時間キャッシュ書込, キャッシュ読込)
# 未登録モデルのログは集計から除外されるため、新モデルが出たら必ずここに追加する。
PRICING: dict[str, tuple[float, float, float, float, float]] = {
    "claude-opus-5": (5, 25, 6.25, 10, 0.50),
    "claude-opus-4-8": (5, 25, 6.25, 10, 0.50),
    "claude-opus-4-7": (5, 25, 6.25, 10, 0.50),
    "claude-sonnet-5": (2, 10, 2.50, 4, 0.20),
    "claude-sonnet-4-6": (3, 15, 3.75, 6, 0.30),
    "claude-haiku-4-5": (1, 5, 1.25, 2, 0.10),
    "claude-fable-5": (10, 50, 12.50, 20, 1.00),
}

# 期限付きの特別価格。期限を過ぎたら自動で通常価格へ戻す。コメントの TODO だけに
# しておくと、更新を忘れたときに黙って誤った単価で集計され続ける。
# 形式: モデル接頭辞 -> (この日を過ぎたら, 通常価格)
PRICING_EXPIRY: dict[str, tuple[str, tuple[float, float, float, float, float]]] = {
    # Sonnet 5 の導入記念価格は 2026-08-31 まで。以降は通常価格。
    "claude-sonnet-5": ("2026-08-31", (3, 15, 3.75, 6, 0.30)),
}
WEB_SEARCH_COST = 0.01  # 検索1000件あたり $10
PRICING_VERIFIED = "2026-08-01"

TOP_N_MODELS = 2  # 内訳列に載せるモデル数（コストが大きい順）
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config_dir import config_dir  # noqa: E402

PROJECTS_DIR = config_dir() / "projects"


def price_for(model: str, on: date | None = None) -> tuple[float, float, float, float, float] | None:
    """モデル ID に対応する単価を返す。期限切れの特別価格は通常価格へ差し替える。

    on は集計対象の日付ではなく実行日を既定とする。過去分をさかのぼって当時の単価で
    再計算する用途は想定していない（ログに単価は残らないため厳密には復元できない）。
    """
    today = on or date.today()
    for prefix, rates in PRICING.items():
        if model.startswith(prefix):
            expiry = PRICING_EXPIRY.get(prefix)
            if expiry and today > date.fromisoformat(expiry[0]):
                return expiry[1]
            return rates
    return None


def record_cost(usage: dict, rates: tuple[float, float, float, float, float]) -> float:
    inp, out, w5m, w1h, read = rates
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)

    cache_creation = usage.get("cache_creation") or {}
    ephemeral_5m = cache_creation.get("ephemeral_5m_input_tokens", 0)
    ephemeral_1h = cache_creation.get("ephemeral_1h_input_tokens", 0)
    if not cache_creation and usage.get("cache_creation_input_tokens"):
        ephemeral_5m = usage["cache_creation_input_tokens"]

    web_searches = (usage.get("server_tool_use") or {}).get("web_search_requests", 0)

    cost = (
        input_tokens * inp + output_tokens * out + cache_read * read + ephemeral_5m * w5m + ephemeral_1h * w1h
    ) / 1_000_000
    cost += web_searches * WEB_SEARCH_COST
    return cost


def _project_dir_for_cwd() -> str:
    """CWD に対応するログディレクトリ名を組み立てる。

    as_posix() を経由するのは Windows のため。str(Path.cwd()) は区切りがバックスラッシュに
    なるので、`/` の置換が一切効かず常に不一致になる。
    """
    return Path.cwd().as_posix().replace("/", "-").replace(".", "-")


def iter_jsonl_files(project_only: bool) -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    if project_only:
        target = _project_dir_for_cwd()
        candidates = [p for p in PROJECTS_DIR.iterdir() if p.is_dir() and p.name == target]
        files: list[Path] = []
        for d in candidates:
            files.extend(d.rglob("*.jsonl"))
        return files
    return list(PROJECTS_DIR.rglob("*.jsonl"))


def iter_records(project_only: bool):
    # Claude Code は API レスポンス単位ではなく、コンテンツブロック（thinking/text/
    # tool_use）単位で JSONL の行を書く。同一レスポンスに属する行は同じ message.id と
    # 同一（確定済みの）usage を繰り返し持つ。全行をカウントするとコンテンツブロック数
    # 倍にコストが水増しされるため、message.id ごとに1回だけ課金する。
    unknown_models: set[str] = set()
    seen_message_ids: set[str] = set()
    for fp in iter_jsonl_files(project_only):
        try:
            with fp.open("r", errors="ignore") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    message = entry.get("message")
                    if not isinstance(message, dict):
                        continue
                    usage = message.get("usage")
                    model = message.get("model")
                    timestamp = entry.get("timestamp")
                    message_id = message.get("id")
                    if not usage or not model or not timestamp or not message_id:
                        continue
                    if message_id in seen_message_ids:
                        continue
                    seen_message_ids.add(message_id)
                    rates = price_for(model)
                    if rates is None:
                        unknown_models.add(model)
                        continue
                    try:
                        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    yield ts, model, record_cost(usage, rates)
        except OSError as exc:
            print(f"warning: 読み込めませんでした {fp}: {exc}", file=sys.stderr)
    if unknown_models:
        print(
            f"warning: 料金表未登録のためスキップしたモデル: {', '.join(sorted(unknown_models))}",
            file=sys.stderr,
        )


def model_label(model: str) -> str:
    for prefix in PRICING:
        if model.startswith(prefix):
            return prefix
    return model


def short_label(label: str) -> str:
    return label.removeprefix("claude-")


def bucket(records, tz: ZoneInfo, days: int) -> tuple[dict, list]:
    now = datetime.now(tz)
    window_dates = [(now - timedelta(days=i)).date() for i in range(days - 1, -1, -1)]
    totals: dict = {d: {} for d in window_dates}
    window_start = now - timedelta(days=days)

    for ts, model, cost in records:
        ts_local = ts.astimezone(tz)
        if ts_local < window_start:
            continue
        day = ts_local.date()
        if day not in totals:
            continue
        label = model_label(model)
        totals[day][label] = totals[day].get(label, 0.0) + cost

    return totals, window_dates


def display_width(s: str) -> int:
    """等幅フォントでの表示幅を返す（全角文字は2カラムとして数える）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad_cell(s: str, width: int) -> str:
    return s + " " * (width - display_width(s))


def format_date_label(day, is_today: bool) -> str:
    weekday = WEEKDAY_JA[day.weekday()] + "・今のところ" if is_today else WEEKDAY_JA[day.weekday()]
    return f"{day:%m/%d} ({weekday})"


def format_detail(day_models: dict) -> str:
    if not day_models:
        return "(利用なし)"
    ranked = sorted(day_models.items(), key=lambda kv: kv[1], reverse=True)
    parts = [f"{short_label(label)} ${cost:,.2f}" for label, cost in ranked[:TOP_N_MODELS]]
    return ", ".join(parts)


def box_table(headers: list, rows: list) -> str:
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(cell))

    def border(left: str, mid: str, right: str) -> str:
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def row_line(cells: list) -> str:
        return "│ " + " │ ".join(pad_cell(c, w) for c, w in zip(cells, widths)) + " │"

    lines = [border("┌", "┬", "┐"), row_line(headers)]
    for row in rows:
        lines.append(border("├", "┼", "┤"))
        lines.append(row_line(row))
    lines.append(border("└", "┴", "┘"))
    return "\n".join(lines)


def render(totals: dict, window_dates: list, tz: ZoneInfo) -> str:
    today = window_dates[-1]
    tz_name = "JST" if getattr(tz, "key", "") == "Asia/Tokyo" else getattr(tz, "key", str(tz))
    headers = [f"日付（{tz_name}）", "合計", "内訳（主なモデル）"]
    rows = []
    grand_total = 0.0
    for day in window_dates:
        day_models = totals[day]
        day_total = sum(day_models.values())
        grand_total += day_total
        rows.append(
            [
                format_date_label(day, is_today=(day == today)),
                f"${day_total:,.2f}",
                format_detail(day_models),
            ]
        )

    lines = [box_table(headers, rows)]
    lines.append("")
    lines.append(f"合計（{len(window_dates)}日間）: ${grand_total:,.2f}")
    lines.append("※ トークン量から算出した「API従量課金換算」の推定値。実際の請求ではない（Maxは定額制）。")
    lines.append(f"※ 料金表 最終確認: {PRICING_VERIFIED} / platform.claude.com/docs/en/about-claude/pricing")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=7, help="集計する直近日数 (既定 7)")
    ap.add_argument("--tz", default="Asia/Tokyo", help="日付境界に使うタイムゾーン (既定 Asia/Tokyo)")
    ap.add_argument(
        "--project-only",
        action="store_true",
        help="カレントプロジェクトのログのみ集計 (既定は全プロジェクト)",
    )
    args = ap.parse_args()

    if args.days < 1:
        print("error: --days は 1 以上を指定してください", file=sys.stderr)
        return 2

    try:
        tz = ZoneInfo(args.tz)
    except ZoneInfoNotFoundError:
        print(f"error: 不明なタイムゾーンです: {args.tz!r}", file=sys.stderr)
        return 2

    records = iter_records(args.project_only)
    totals, window_dates = bucket(records, tz, args.days)
    print(render(totals, window_dates, tz))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/bin/bash
# backfill_weekly.sh
# 過去の活動を週次ノートとして遡って記録する。
#
# 材料はローカルに残っているぶんだけ使える。Claude アプリのセッションは 2026-01-29 以降、
# Claude Code CLI のトランスクリプトは約 30 日で間引かれるため直近のみ、git は全履歴。
# 古い週ほど材料が薄くなるので、無理に埋めずその旨を本文に書かせる。
#
# 既に同じ週の記録があれば飛ばすため、中断しても再開できる。
#
# 使い方:
#   backfill_weekly.sh --list                  対象の週を一覧するだけ
#   backfill_weekly.sh --dry-run --weeks 1     材料を確認する（書き込まない）
#   backfill_weekly.sh --weeks 3               古い順に 3 週だけ実行する
#   backfill_weekly.sh                         全対象週を実行する（26 週で約 1 時間）

set -uo pipefail

# 自分の位置から導出する。$HOME/.claude 決め打ちだと CLAUDE_CONFIG_DIR で別の場所へ
# 配置したときに食い違う。
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SH="$SCRIPTS_DIR/notion_digest_agent.sh"
START_DATE="2026-01-29"   # Claude アプリのセッションが残っている最古の日
SLEEP_BETWEEN=10          # 週ごとの間隔（API とレート制限への配慮）

LIST_ONLY=0
DRY_RUN=""
LIMIT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --list) LIST_ONLY=1 ;;
    --dry-run) DRY_RUN="--dry-run" ;;
    --weeks) shift; LIMIT="${1:-0}" ;;
    *) echo "不明な引数: $1" >&2; exit 2 ;;
  esac
  shift 2>/dev/null || break
done

# 対象の週（月曜〜日曜）を古い順に列挙する。前週までを対象にし、今週は含めない。
WEEKS=$(python3 - "$START_DATE" <<'PY'
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

start = date.fromisoformat(sys.argv[1])
today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
# 週の起点を月曜に揃える
monday = start - timedelta(days=start.weekday())
this_monday = today - timedelta(days=today.weekday())
while monday < this_monday:
    print(f"{monday.isoformat()} {(monday + timedelta(days=6)).isoformat()}")
    monday += timedelta(days=7)
PY
)

TOTAL=$(printf '%s\n' "$WEEKS" | grep -c . || true)
echo "対象の週: ${TOTAL} 件（${START_DATE} 以降、前週まで）"

if [ "$LIST_ONLY" -eq 1 ]; then
  printf '%s\n' "$WEEKS" | nl -w3 -s'  '
  exit 0
fi

# 記録済みの日付（週次ノートは週の最終日を Date に持つ）
RECORDED=$(python3 "$SCRIPTS_DIR/activity_digest.py" --recorded 2>/dev/null)

DONE=0
SKIPPED=0
FAILED=0
while read -r since until; do
  [ -z "${until:-}" ] && continue
  if [ "$LIMIT" -gt 0 ] && [ "$DONE" -ge "$LIMIT" ]; then break; fi

  if printf '%s\n' "$RECORDED" | grep -qx "$until"; then
    echo "[$since 〜 $until] 既に記録済みのため飛ばす"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # 材料が無い週は実行そのものを省く（空のノートを作らない）
  if [ -z "$(python3 "$SCRIPTS_DIR/activity_digest.py" --since "$since" --until "$until" | tr -d '[:space:]')" ]; then
    echo "[$since 〜 $until] 活動が無いため飛ばす"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  echo "[$since 〜 $until] 実行する"
  if bash "$AGENT_SH" weekly $DRY_RUN --since "$since" --until "$until"; then
    DONE=$((DONE + 1))
  else
    FAILED=$((FAILED + 1))
    echo "[$since 〜 $until] 失敗した。中断する（再実行すれば続きから進む）" >&2
    break
  fi
  sleep "$SLEEP_BETWEEN"
done <<< "$WEEKS"

echo
echo "実行 ${DONE} 件 / 飛ばし ${SKIPPED} 件 / 失敗 ${FAILED} 件"
[ "$FAILED" -gt 0 ] && exit 1
exit 0

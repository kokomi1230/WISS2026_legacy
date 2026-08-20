#!/bin/bash
# notion_digest_agent.sh
# launchd から呼ばれ、日次（前日ぶん）または週次（直近7日）の活動を Notion の
# 研究ノート_DB へ記録層のノートとして追加する。
#
# 材料の収集は activity_digest.py が行い（コミット / Claude Code CLI / Claude アプリ）、
# 本スクリプトはその出力を判定してヘッドレス Claude Code へ渡すだけにする。
# 収集とモデルの仕事を分けておくと、収集の正しさを単体で確かめられる。
#
# 使い方:
#   notion_digest_agent.sh daily              未記録の日を古い順に埋める（既定 7 日まで）
#   notion_digest_agent.sh weekly             直近7日ぶんを記録
#   notion_digest_agent.sh daily --dry-run    Notion へ書かず、渡すプロンプトを表示する
#   notion_digest_agent.sh daily --date 2026-07-30   指定日だけを記録
#
# 実行基盤の作りは claude-paper-summary/src/scheduler/scheduled_summary.sh に倣う。

set -uo pipefail

# --- 引数 -------------------------------------------------------------------
MODE="${1:-daily}"
DRY_RUN=0
TARGET_DATE=""
PERIOD_SINCE=""
PERIOD_UNTIL=""
FORCE=0
shift 2>/dev/null || true
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --date) shift; TARGET_DATE="${1:-}" ;;
    --since) shift; PERIOD_SINCE="${1:-}" ;;
    --until) shift; PERIOD_UNTIL="${1:-}" ;;
    # 既存ノートの日付と衝突していても記録し直す（週次ノートの日次分解など）
    --force) FORCE=1 ;;
    *) ;;
  esac
  shift 2>/dev/null || break
done
case "$MODE" in
  daily|weekly) ;;
  *) echo "モードは daily か weekly を指定する（指定: ${MODE}）" >&2; exit 2 ;;
esac

# --- 設定 -------------------------------------------------------------------
# 自分の位置から導出する。$HOME/.claude 決め打ちだと CLAUDE_CONFIG_DIR で別の場所へ
# 配置したときに食い違う。BASH_SOURCE 由来なら配置先がどこでも必ず一致する。
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPTS_DIR")"
MODEL="claude-sonnet-5"    # 材料を要約して 1 行書くだけなので Sonnet で足りる
TRANSIENT_RETRY=2          # 一時的なネットワーク障害に対する追加リトライ回数
RETRY_WAIT=120             # リトライ前の待機（秒）
RUN_TIMEOUT=1800           # 1実行の最大時間（秒・30分）
BACKFILL_DAYS=7            # 未記録の日を遡って埋める上限
LOCK_STALE_SECONDS=5400    # ロックがこの秒数より古ければ残置と見なして奪う（RUN_TIMEOUT の3倍）
LOG_DIR="$HOME/Library/Logs/notion-digest"
# daily と weekly が重ならないようロックは共有する（weekly は daily の結果を読むため）
LOCK_DIR="$LOG_DIR/.lock"

# launchd は最小 PATH で起動するため、python3 / git / npx（MCP サーバ）が
# 見つかるよう明示的に PATH を構成する。
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$HOME/.npm-global/bin:$HOME/.local/bin"

# claude 本体は npm global / Homebrew / native installer のどこに入っているか分からない。
# PATH を構成した後に探す。判定は log() が使えるようになってから行う（無人実行なので、
# ログに残らないエラーは事実上気づけない）。
CLAUDE_BIN="$(command -v claude || true)"

# .env からトークンを読み込む。
# NOTION_TOKEN            … Notion MCP と notion_sync.py が共有する。
#                           起動済みシェルの失効した値を引き継がないよう .env を正とする。
# CLAUDE_CODE_OAUTH_TOKEN … Keychain の OAuth より優先され、無人実行でも 401 で落ちにくい
#                           （`claude setup-token` で発行する1年有効・サブスク枠トークン）。
set -a; [ -f "$CONFIG_DIR/.env" ] && . "$CONFIG_DIR/.env"; set +a

TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$MODE-$(date +%Y%m%d-%H%M%S).log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

if [ -z "$CLAUDE_BIN" ]; then
  log "エラー: claude が PATH に見つからない。上の PATH 構成に導入先を足すこと。"
  exit 1
fi

# 無人実行なので、気づけるのは通知だけである。失敗しても記録の成否には影響させない。
notify() {
  osascript -e "display notification \"$1\" with title \"Notion 記録\"" >/dev/null 2>&1 || true
}

# --- 多重起動防止（残置ロックで恒久的に停止しないよう期限を持たせる）----------
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || date +%s) ))
  if [ "$LOCK_AGE" -gt "$LOCK_STALE_SECONDS" ]; then
    log "残置ロックを検出した（${LOCK_AGE}s 経過）。奪って続行する"
    notify "残置ロックを解除して再開しました"
  else
    log "別の実行が進行中のためスキップする（${LOCK_AGE}s 経過, lock: ${LOCK_DIR}）"
    exit 0
  fi
fi
touch "$LOCK_DIR" 2>/dev/null
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

log "=== $MODE 記録を開始 (model=$MODEL, dry_run=$DRY_RUN) ==="

# --- ミラーの同期（既存 Keywords・前回ノート・記録済み日の把握に必要）---------
# 重複判定はミラーを見るため、判定より先に同期しておく必要がある。
sync_mirror() {
  [ "$DRY_RUN" -eq 1 ] && return 0
  python3 "$SCRIPTS_DIR/notion_sync.py" >>"$LOG_FILE" 2>&1 \
    && log "ミラーを同期した" \
    || log "ミラーの同期に失敗（継続する）"
}
sync_mirror

# --- 対象期間の決定 ---------------------------------------------------------
# daily は「前日」固定にせず、未記録かつ活動のある日を古い順に埋める。
# launchd は逃した起動を 1 回に集約するため、これが無いとスリープ中の日は永久に欠ける。
DATES=()
if [ "$MODE" = "daily" ]; then
  if [ -n "$TARGET_DATE" ]; then
    DATES=("$TARGET_DATE")
  else
    while IFS= read -r d; do [ -n "$d" ] && DATES+=("$d"); done \
      < <(python3 "$SCRIPTS_DIR/activity_digest.py" --pending "$BACKFILL_DAYS" 2>>"$LOG_FILE")
    if [ "${#DATES[@]}" -eq 0 ]; then
      log "未記録で活動のある日は無い"
      exit 0
    fi
    log "未記録の日: ${DATES[*]}"
    # 上限まで埋まっているなら、それより前にも欠けが残っている可能性が高い
    if [ "${#DATES[@]}" -ge "$BACKFILL_DAYS" ]; then
      notify "未記録が ${BACKFILL_DAYS} 日以上あります。--date で個別に補完してください"
    fi
  fi
else
  DATES=("weekly")
fi

# --- 1 期間ぶんを記録する ---------------------------------------------------
record_one() {
  local target="$1"
  local digest

  # 週次ノートは週の最終日を Date に持つ。重複判定はその日付で行う
  local recorded_key="$target"
  [ "$target" = "weekly" ] && recorded_key="$PERIOD_UNTIL"

  if [ "$FORCE" -ne 1 ] && [ -n "$recorded_key" ] \
     && python3 "$SCRIPTS_DIR/activity_digest.py" --recorded 2>/dev/null | grep -qx "$recorded_key"; then
    log "$recorded_key: 既に記録済みのため飛ばす"
    return 0
  fi

  if [ "$target" = "weekly" ]; then
    # 遡及実行では期間を明示する。指定が無ければ前日から 7 日
    if [ -n "$PERIOD_SINCE" ] && [ -n "$PERIOD_UNTIL" ]; then
      digest="$(python3 "$SCRIPTS_DIR/activity_digest.py" --since "$PERIOD_SINCE" --until "$PERIOD_UNTIL" 2>>"$LOG_FILE")"
    else
      digest="$(python3 "$SCRIPTS_DIR/activity_digest.py" --days 7 2>>"$LOG_FILE")"
    fi
  else
    digest="$(python3 "$SCRIPTS_DIR/activity_digest.py" --date "$target" 2>>"$LOG_FILE")"
  fi

  if [ -z "$(printf '%s' "$digest" | tr -d '[:space:]')" ]; then
    log "$target: 活動が無いため記録しない"
    return 0
  fi
  log "$target: 材料を収集した（$(printf '%s' "$digest" | wc -m | tr -d ' ') 文字）"

  local prompt_file="$SCRIPTS_DIR/notion_digest_${MODE}_prompt.txt"
  if [ ! -f "$prompt_file" ]; then
    log "プロンプトファイルが見つからない: $prompt_file"
    return 1
  fi
  local prompt
  prompt="$(cat "$prompt_file")

---

以下が収集済みの材料である。これ以外の情報源を新たに読みに行く必要はない。

$digest"

  if [ "$DRY_RUN" -eq 1 ]; then
    log "--- dry-run ($target): 以下のプロンプトを渡す（Notion へは書き込まない）---"
    printf '%s\n' "$prompt"
    return 0
  fi

  local attempt=0 status=1
  local attempt_out="$LOG_DIR/.attempt-$$.out"
  while [ "$attempt" -le "$TRANSIENT_RETRY" ]; do
    attempt=$((attempt + 1))
    log "$target: Claude 実行 (attempt=$attempt/$((TRANSIENT_RETRY + 1)))"
    if [ -n "$TIMEOUT_BIN" ]; then
      "$TIMEOUT_BIN" "$RUN_TIMEOUT" "$CLAUDE_BIN" --print \
        --model "$MODEL" --dangerously-skip-permissions "$prompt" >"$attempt_out" 2>&1
    else
      "$CLAUDE_BIN" --print \
        --model "$MODEL" --dangerously-skip-permissions "$prompt" >"$attempt_out" 2>&1
    fi
    status=$?
    cat "$attempt_out" >>"$LOG_FILE"

    [ "$status" -eq 0 ] && break

    if grep -qE "ConnectionRefused|FailedToOpenSocket|socket connection was closed|Connection closed mid-response|Request timed out|529 Overloaded|ENOTFOUND|nodename nor servname provided|getaddrinfo|EAI_AGAIN" "$attempt_out" \
       && [ "$attempt" -le "$TRANSIENT_RETRY" ]; then
      log "一時的な接続障害を検知（attempt=${attempt}）。${RETRY_WAIT}s 待機して再試行する"
      sleep "$RETRY_WAIT"
      continue
    fi
    break   # 認証エラー等はリトライしても無意味
  done
  rm -f "$attempt_out"

  if [ "$status" -eq 0 ]; then
    log "$target: 記録した"
    # 週次の知見候補は、人が見に行かなければ埋もれる。件数があるときだけ通知する。
    if [ "$MODE" = "weekly" ]; then
      local insights
      insights=$(grep -o 'insights=[0-9]\{1,\}' "$LOG_FILE" | tail -1 | cut -d= -f2)
      if [ -n "$insights" ] && [ "$insights" -gt 0 ] 2>/dev/null; then
        notify "今週の知見候補が ${insights} 件あります"
      fi
    fi
    # 次の日の重複判定に使うため、書いた行をミラーへ降ろす。
    # Notion の検索インデックスに遅延があるので少し待つ。
    sleep 30
    sync_mirror
  else
    log "$target: 失敗 (exit $status)"
  fi
  return $status
}

FAILED=0
for target in "${DATES[@]}"; do
  record_one "$target" || FAILED=$((FAILED + 1))
done

if [ "$FAILED" -gt 0 ]; then
  log "=== 異常終了: ${FAILED}/${#DATES[@]} 件が失敗 — 詳細は $LOG_FILE ==="
  notify "${MODE} 記録が ${FAILED} 件失敗しました"
else
  log "=== 正常終了: ${#DATES[@]} 件 ==="
fi

# 古いログを30日で間引く
find "$LOG_DIR" -name '*-*.log' -type f -mtime +30 -delete 2>/dev/null || true

[ "$FAILED" -gt 0 ] && exit 1
exit 0

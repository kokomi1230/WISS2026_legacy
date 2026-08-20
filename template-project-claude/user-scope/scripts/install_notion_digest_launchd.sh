#!/bin/bash
# install_notion_digest_launchd.sh
# 日次 / 週次の Notion 記録ジョブを launchd へ（再）インストールする。
#
# テンプレート com.lleoo.notion-{daily,weekly}-digest.plist のプレースホルダを実環境の
# 絶対パスへ置換して ~/Library/LaunchAgents/ へ配置し、bootout → bootstrap で必ず
# 再ロードする。plist やスクリプトパスを変更したら本スクリプトを実行すること
# （reload 忘れによる exit 127「No such file or directory」を防ぐ）。冪等。
#
# 使い方:
#   bash ~/.claude/scripts/install_notion_digest_launchd.sh            # 配置して再ロード
#   bash ~/.claude/scripts/install_notion_digest_launchd.sh --uninstall # 登録を解除

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# .env は設定ディレクトリ直下。$HOME/.claude 決め打ちにすると CLAUDE_CONFIG_DIR で
# 別の場所へ配置したときに、存在する .env を「無い」と誤判定して警告を出す。
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
AGENT_SH="$SCRIPT_DIR/notion_digest_agent.sh"
LOG_DIR="$HOME/Library/Logs/notion-digest"
DOMAIN="gui/$(id -u)"
LABELS=(com.lleoo.notion-daily-digest com.lleoo.notion-weekly-digest)

# --- アンインストール -------------------------------------------------------
if [ "${1:-}" = "--uninstall" ]; then
    for label in "${LABELS[@]}"; do
        launchctl bootout "$DOMAIN/$label" 2>/dev/null \
            && echo "登録を解除した: $label" \
            || echo "登録されていない: $label"
        rm -f "$HOME/Library/LaunchAgents/$label.plist"
    done
    echo "完了。ログとミラーは残している。"
    exit 0
fi

# --- 事前チェック -----------------------------------------------------------
if [ ! -f "$AGENT_SH" ]; then
    echo "エラー: notion_digest_agent.sh が見つからない: $AGENT_SH" >&2
    exit 1
fi
for label in "${LABELS[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$label.plist" ]; then
        echo "エラー: テンプレート plist が見つからない: $SCRIPT_DIR/$label.plist" >&2
        exit 1
    fi
done

# 無人実行に必要なトークン。欠けていても配置は続けるが、実行時に必ず失敗するため警告する。
if ! grep -q '^CLAUDE_CODE_OAUTH_TOKEN=' "$CONFIG_DIR/.env" 2>/dev/null; then
    echo "警告: $CONFIG_DIR/.env に CLAUDE_CODE_OAUTH_TOKEN が無い。" >&2
    echo "      無人実行は認証エラーで失敗する。'claude setup-token' で発行して追記すること。" >&2
fi
if ! grep -q '^NOTION_TOKEN=' "$CONFIG_DIR/.env" 2>/dev/null; then
    echo "警告: $CONFIG_DIR/.env に NOTION_TOKEN が無い。Notion への書き込みが失敗する。" >&2
fi

# `$VAR）` のように変数の直後へ全角文字が続くと、bash は変数名の一部として解釈する。
# set -u では未定義エラーになり、その分岐に入ったときだけ実行時に落ちる（テストで気づきにくい）。
# 波括弧 `${VAR}` で囲めば防げるので、配置前に機械的に弾く。
# BSD grep は角括弧内の \x エスケープを解釈せず誤検知するため Python で判定する。
if ! python3 - "$SCRIPT_DIR" <<'PY'
import re, sys
from pathlib import Path

pattern = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]")
# コメント行は実行されないので対象外（この検査自体の説明文が引っかかるのを避ける）
offenders = [
    f"{path.name}:{n}: {line.strip()}"
    for path in sorted(Path(sys.argv[1]).glob("*.sh"))
    for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1)
    if pattern.search(line) and not line.lstrip().startswith("#")
]
if offenders:
    print("エラー: 変数の直後に全角文字が続く箇所がある。${VAR} の形へ直すこと:", file=sys.stderr)
    print("\n".join(offenders), file=sys.stderr)
    sys.exit(1)
PY
then
    exit 1
fi

chmod +x "$AGENT_SH"
mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"

# --- 配置と再ロード ---------------------------------------------------------
# sed の区切りに | を使うためパスに | が無いことを前提とする（ホームパスでは問題なし）。
for label in "${LABELS[@]}"; do
    dest="$HOME/Library/LaunchAgents/$label.plist"
    sed -e "s|__AGENT_SH__|$AGENT_SH|g" \
        -e "s|__LOG_DIR__|$LOG_DIR|g" \
        "$SCRIPT_DIR/$label.plist" > "$dest"
    echo "plist を配置した: $dest"

    launchctl bootout "$DOMAIN/$label" 2>/dev/null
    if launchctl bootstrap "$DOMAIN" "$dest" 2>/dev/null; then
        echo "  launchctl bootstrap 成功（${DOMAIN}）"
    else
        echo "  bootstrap に失敗。旧 API（unload/load）でフォールバックする" >&2
        launchctl unload "$dest" 2>/dev/null
        launchctl load "$dest"
    fi
done

# --- 検証出力 ---------------------------------------------------------------
echo
echo "=== 登録後のジョブ ==="
for label in "${LABELS[@]}"; do
    launchctl list "$label" >/dev/null 2>&1 \
        && echo "  $label: 登録済み" \
        || echo "  $label: 未登録（要確認）"
done
echo
echo "日次 00:05（前日ぶん） / 週次 月曜 00:30（直近7日）"
echo "手動テスト: bash $AGENT_SH daily --dry-run"
echo "手動起動:   launchctl kickstart -k $DOMAIN/com.lleoo.notion-daily-digest"

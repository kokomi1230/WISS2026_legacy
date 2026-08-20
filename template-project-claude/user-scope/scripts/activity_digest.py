#!/usr/bin/env python3
"""指定期間の作業内容を 3 つのソースから集めてプロジェクト単位でまとめる。

「いつ何をやったか」を機械的に集めるだけで，要約や解釈は行わない。要約は呼び出し側
（日次 / 週次エージェント）の仕事にする。こう分けておくと，収集の正しさを本スクリプト
単体で検証でき，モデルの出力ぶれと切り離せる。

集めるもの:
  1. コミット   <リポジトリ置き場>/*/.git を横断（既定 ~/Documents/Repository、
                REPOSITORY_DIR で上書き可）
  2. CLI 会話   <設定ディレクトリ>/projects/**/*.jsonl の ai-title レコード
  3. アプリ会話 ~/Library/Application Support/Claude/local-agent-mode-sessions/**/local_*.json

生のユーザ発話は使わない。貼り付けたログが混じって 1 日 10 万文字を超え，信号にならない
ためである。Claude Code が自動生成する ai-title と，アプリ側の title / initialMessage が
同じ内容をはるかに少ない分量で表す。

該当が 1 件も無ければ何も出力しない。呼び出し側が「記録しない」を判断できるようにする。

Usage:
  python3 activity_digest.py                                  # 前日ぶん
  python3 activity_digest.py --date 2026-07-29                # 指定日
  python3 activity_digest.py --since 2026-07-25 --until 2026-07-31
  python3 activity_digest.py --days 7                         # 前日から遡って 7 日
  python3 activity_digest.py --date 2026-07-29 --format json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config_dir import config_dir, mirror_dir, repository_dir  # noqa: E402

TZ = ZoneInfo("Asia/Tokyo")

CONFIG_DIR = config_dir()
# リポジトリの置き場・ミラーの位置はマシンごとに違う。解決規則は _config_dir に集約し、
# user-scope 内のどのスクリプトでも同じ環境変数（REPOSITORY_DIR / NOTION_MIRROR_DIR）で
# 上書きできるようにする。
REPOSITORY_DIR = repository_dir()
CLI_PROJECTS_DIR = CONFIG_DIR / "projects"
# Claude アプリのセッション置き場は macOS 固有。他 OS では単に見つからず、
# CLI 側のセッションだけで記録が作られる。
APP_SESSIONS_DIR = Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"
MIRROR_DIR = mirror_dir()
REFERENCE_LIST_DIR = MIRROR_DIR / "Reference-List"

# Repository 配下ではないが作業対象になるリポジトリ。
# 設定ディレクトリはユーザースコープの skill / command / script の置き場で，
# ここでの作業はコミットとしてしか残らない
EXTRA_REPOSITORIES = (CONFIG_DIR,)

# initialMessage は依頼文の冒頭に用件が出るため，先頭だけ見れば足りる
INITIAL_MESSAGE_CHARS = 300
# ai-title が無いセッションで最初の発話を表題代わりに使うときの長さ
FALLBACK_TITLE_CHARS = 120
GIT_TIMEOUT_SECONDS = 15

# 日次 / 週次エージェント自身のヘッドレス実行を示す標識。プロンプトの先頭に置く。
# これを含むセッションを集めると，記録の仕組みが自分自身を毎日記録してしまう。
# 2 つ目は標識を導入する前に実行した分を拾うためのもので，プロンプト冒頭の定型句である
AGENT_MARKERS = ("[notion-digest-agent]", "あなたは無人実行されている")

# `docs: add ban2014controlling to references` からキーを取り出す
_BIBKEY_RE = re.compile(r"\badd\s+([A-Za-z][A-Za-z0-9_:.-]{3,})\s+to\s+references\b", re.IGNORECASE)

# ハーネスが差し込むブロック。ユーザーの発話ではないので表題の材料から除く
_INJECTED_BLOCK_RE = re.compile(
    r"<(system-reminder|command-name|command-message|command-args|local-command-stdout)>.*?" r"</\1>|<[^>]{1,40}>",
    re.DOTALL,
)

APP_NO_FOLDER = "（フォルダ未選択・Claude アプリ）"


# ---------- 収集 ----------


def _iter_repositories() -> list[Path]:
    """収集対象のリポジトリを列挙する。"""
    repos = []
    if REPOSITORY_DIR.is_dir():
        repos.extend(p for p in REPOSITORY_DIR.iterdir() if (p / ".git").exists())
    repos.extend(p for p in EXTRA_REPOSITORIES if (p / ".git").exists())
    return sorted(repos)


def collect_commits(since: date, until: date) -> dict[str, list[dict[str, Any]]]:
    """全リポジトリから期間内のコミットを集める。

    --all を付けて全ブランチを対象にする。ブランチを切って作業した日が
    記録から抜け落ちないようにするため。
    """
    # git の --until は指定日の 00:00 を指すため，翌日 00:00 を上限にして当日を含める
    after = f"{since.isoformat()} 00:00"
    before = f"{(until + timedelta(days=1)).isoformat()} 00:00"

    result: dict[str, list[dict[str, Any]]] = {}
    for repo in _iter_repositories():
        try:
            proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "log",
                    "--all",
                    "--no-merges",
                    f"--after={after}",
                    f"--before={before}",
                    "--pretty=format:%h\x1f%ad\x1f%s",
                    "--date=format-local:%Y-%m-%d %H:%M",
                ],
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT_SECONDS,
                env={"TZ": "Asia/Tokyo", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if proc.returncode != 0 or not proc.stdout.strip():
            continue

        commits = []
        for line in proc.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 3:
                commits.append({"hash": parts[0], "datetime": parts[1], "subject": parts[2]})
        if commits:
            result[repo.name] = commits
    return result


def _first_user_text(record: dict[str, Any]) -> str:
    """user レコードから本文を取り出す。差し込まれたブロックは除く。

    system-reminder や command-name はハーネスが挿入したものでユーザーの発話ではない。
    残すと用件が埋もれるため落とす。
    """
    message = record.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = " ".join(
            block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        return ""
    text = _INJECTED_BLOCK_RE.sub(" ", text)
    return " ".join(text.split())


def _modified_before(path: Path, since: date) -> bool:
    """更新時刻が対象期間より前なら中身を読む必要がない。

    セッションファイルの mtime は最終活動時刻以上になるため，下限としてのみ使えば
    取りこぼさない（逆に mtime が期間より後でも，日をまたいだセッションは対象になりうる
    ので上限には使えない）。履歴が増えても走査量が伸びにくくなる。
    """
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, TZ).date() < since
    except OSError:
        return False


def _iso_to_local_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(TZ)
    except (ValueError, AttributeError):
        return None


def _scan_cli_session(path: Path) -> dict[str, Any] | None:
    """1 セッションの jsonl から表題・cwd・稼働日を取り出す。

    ai-title はセッション後半で更新されることがあるため最後の値を採る。
    行ごとに文字列で当たりを付けてから JSON へ落とし，走査コストを抑える。

    ai-title が無いセッションもある（短時間で終わった場合など）。そのまま捨てると
    その作業が記録から丸ごと消えるため，最初のユーザー発話の冒頭で代用する。

    **稼働日はメッセージ 1 件ごとのタイムスタンプから集める。** セッションの最終時刻
    だけで日付を決めると，日をまたいだセッションが終了日にしか計上されず，開始日の
    作業が丸ごと記録から消える。長い作業ほど日をまたぎやすいので影響が大きい。
    """
    title = cwd = None
    first_prompt = ""
    is_agent = False
    active: dict[date, list[datetime]] = defaultdict(list)
    try:
        with path.open(errors="replace") as handle:
            for line in handle:
                # 記録エージェント自身のヘッドレス実行は集めない。標識は最初の発話に入る
                if any(marker in line for marker in AGENT_MARKERS):
                    is_agent = True
                    break
                if '"ai-title"' in line:
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if record.get("type") == "ai-title":
                        title = record.get("aiTitle") or title
                    continue
                if '"timestamp"' not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                cwd = record.get("cwd") or cwd
                kind = record.get("type")
                if kind == "user" and not record.get("isSidechain") and not first_prompt:
                    first_prompt = _first_user_text(record)[:FALLBACK_TITLE_CHARS]
                # 稼働日は人とモデルのやり取りだけで測る。内部レコードは除く
                if kind not in ("user", "assistant"):
                    continue
                stamp = record.get("timestamp")
                if not stamp:
                    continue
                try:
                    when = datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(TZ)
                except ValueError:
                    continue
                active[when.date()].append(when)
    except OSError:
        return None

    if is_agent or not active:
        return None
    return {
        "title": title or first_prompt or None,
        "title_is_fallback": not title,
        "cwd": cwd,
        "active": active,
    }


def _session_entries(
    session: dict[str, Any],
    since: date,
    until: date,
    project: str,
    source: str,
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """稼働日ごとに 1 エントリへ展開する。日をまたいだセッションは両日に現れる。"""
    entries = []
    for day, stamps in sorted(session["active"].items()):
        if not since <= day <= until:
            continue
        entry = {
            "project": project,
            "title": session["title"],
            "title_is_fallback": session.get("title_is_fallback", False),
            "datetime": min(stamps).strftime("%Y-%m-%d %H:%M"),
            "until": max(stamps).strftime("%H:%M"),
            "turns": len(stamps),
            "spans_days": len(session["active"]) > 1,
            "source": source,
        }
        entry.update(extra or {})
        entries.append(entry)
    return entries


def collect_cli_sessions(since: date, until: date) -> list[dict[str, Any]]:
    """Claude Code CLI のセッション表題を集める。"""
    if not CLI_PROJECTS_DIR.is_dir():
        return []

    sessions = []
    for path in CLI_PROJECTS_DIR.rglob("*.jsonl"):
        # agent-*.jsonl は subagent のトランスクリプト。親セッションの内部作業であり、
        # 独立した作業として数えると二重計上になる（表題もユーザー発話も持たない）
        if path.name.startswith("agent-"):
            continue
        if _modified_before(path, since):
            continue
        session = _scan_cli_session(path)
        if not session or not session["title"]:
            continue
        # 期間外のセッションは早めに捨てて，展開の手間を省く
        if not any(since <= day <= until for day in session["active"]):
            continue
        project = Path(session["cwd"]).name if session["cwd"] else path.parent.name
        sessions.extend(_session_entries(session, since, until, project, "cli"))
    sessions.sort(key=lambda s: s["datetime"])
    return sessions


def _app_active_days(path: Path, record: dict[str, Any]) -> dict[date, list[datetime]]:
    """アプリセッションの稼働日をメッセージ単位で求める。

    local_<uuid>.json は createdAt と lastActivityAt しか持たないため，それだけで日付を
    決めると日をまたいだセッション（189 件中 21 件）が終了日にしか計上されない。
    同じ階層の local_<uuid>/audit.jsonl に 1 メッセージごとの時刻があるので，
    そこから稼働日を集める。本文は読まず時刻だけを見るので走査は軽い。
    """
    active: dict[date, list[datetime]] = defaultdict(list)
    audit = path.parent / path.stem / "audit.jsonl"
    if audit.exists():
        try:
            with audit.open(errors="replace") as handle:
                for line in handle:
                    marker = line.find('"_audit_timestamp"')
                    if marker == -1:
                        continue
                    try:
                        stamp = json.loads(line).get("_audit_timestamp")
                    except ValueError:
                        continue
                    when = _iso_to_local_datetime(stamp)
                    if when:
                        active[when.date()].append(when)
        except OSError:
            pass
    if active:
        return active

    # audit.jsonl が無い / 読めない場合は最終活動時刻で代用する
    epoch_ms = record.get("lastActivityAt") or record.get("createdAt")
    if not epoch_ms:
        return {}
    when = datetime.fromtimestamp(epoch_ms / 1000, TZ)
    return {when.date(): [when]}


def collect_app_sessions(since: date, until: date) -> list[dict[str, Any]]:
    """Claude アプリ（local agent mode）のセッションを集める。

    CLI 側とはセッション ID が重ならないため二重計上にならない。コミットの残らない
    作業（申請書・スライド・文献調査）はここにしか現れない。
    """
    if not APP_SESSIONS_DIR.is_dir():
        return []

    sessions = []
    for path in APP_SESSIONS_DIR.rglob("local_*.json"):
        # 本体と audit.jsonl のどちらかが期間内に更新されていれば読む
        audit = path.parent / path.stem / "audit.jsonl"
        if _modified_before(path, since) and (not audit.exists() or _modified_before(audit, since)):
            continue
        try:
            record = json.loads(path.read_text(errors="replace"))
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict) or "sessionId" not in record:
            continue

        active = _app_active_days(path, record)
        if not active or not any(since <= day <= until for day in active):
            continue

        folders = [Path(p).name for p in (record.get("userSelectedFolders") or [])]
        initial = record.get("initialMessage") or ""
        if not isinstance(initial, str):
            initial = json.dumps(initial, ensure_ascii=False)
        initial = " ".join(initial.split())[:INITIAL_MESSAGE_CHARS]

        sessions.extend(
            _session_entries(
                {"title": record.get("title") or "(無題)", "active": active},
                since,
                until,
                folders[0] if folders else APP_NO_FOLDER,
                "app",
                {"folders": folders, "initial_message": initial},
            )
        )
    sessions.sort(key=lambda s: s["datetime"])
    return sessions


def resolve_references(commits: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    """コミット件名の bibkey をミラーの論文ノートへ対応付ける。

    `docs: add ban2014controlling to references` のような件名から bibkey を取り，
    Reference-List の frontmatter にある Bibtex エントリと突き合わせる。
    推測ではなく文字列の一致なので，エージェントはそのまま `関連文献` に入れてよい。
    """
    keys = {
        match.group(1).lower()
        for entries in commits.values()
        for commit in entries
        if (match := _BIBKEY_RE.search(commit["subject"]))
    }
    if not keys or not REFERENCE_LIST_DIR.is_dir():
        return []

    resolved = []
    for note in sorted(REFERENCE_LIST_DIR.glob("*.md")):
        page_id = title = bibtex = ""
        for line in note.read_text(errors="replace").splitlines():
            if line.startswith("notion_id:"):
                page_id = line.split(":", 1)[1].strip()
            elif line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("Bibtex:"):
                bibtex = line.split(":", 1)[1].strip().lower()
            elif line == "---" and page_id:
                break
        if not page_id or not bibtex:
            continue
        for key in keys:
            # Bibtex は "@article{ban2014controlling,\n ..." の形で入っている
            if f"{{{key}," in bibtex:
                resolved.append({"bibkey": key, "notion_id": page_id, "title": title})
                break
    return resolved


# ---------- 整形 ----------


def group_by_project(
    commits: dict[str, list[dict[str, Any]]],
    cli_sessions: list[dict[str, Any]],
    app_sessions: list[dict[str, Any]],
) -> dict[str, dict[str, list]]:
    """3 ソースをプロジェクト名で束ねる。"""
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: {"commits": [], "cli": [], "app": []})
    for project, entries in commits.items():
        grouped[project]["commits"] = entries
    for session in cli_sessions:
        grouped[session["project"]]["cli"].append(session)
    for session in app_sessions:
        grouped[session["project"]]["app"].append(session)
    return dict(grouped)


def _session_headline(session: dict[str, Any]) -> str:
    """セッション 1 件を 1 行にする。作業量の目安が分かるよう往復数と時間帯を添える。"""
    start = session["datetime"]
    end = session.get("until", "")
    span = f"{start}-{end}" if end and end != start[-5:] else start
    parts = [span]
    if session.get("turns"):
        parts.append(f"[{session['turns']}往復]")
    if session.get("spans_days"):
        parts.append("[日跨ぎ]")
    # 表題が無く発話の冒頭で代用したものは，要約時に文脈が薄いと分かるよう印を付ける
    if session.get("title_is_fallback"):
        parts.append("（表題なし・冒頭の依頼）")
    parts.append(session["title"])
    return " ".join(parts)


def render_markdown(
    grouped: dict[str, dict[str, list]],
    since: date,
    until: date,
    references: list[dict[str, str]] | None = None,
) -> str:
    """エージェントが読む中間形式。要約はせず，材料をそのまま並べる。"""
    period = since.isoformat() if since == until else f"{since.isoformat()} 〜 {until.isoformat()}"
    lines = [f"# 活動記録の材料: {period}", ""]

    if references:
        lines.append("## 関連する文献（コミットから確定。そのまま 関連文献 に入れてよい）")
        for ref in references:
            lines.append(f"- {ref['notion_id']}  {ref['title'][:70]}")
        lines.append("")

    # フォルダ未選択のアプリセッションは最後に回す。プロジェクトの話が先に来るほうが読みやすい
    names = sorted(k for k in grouped if k != APP_NO_FOLDER)
    if APP_NO_FOLDER in grouped:
        names.append(APP_NO_FOLDER)

    for name in names:
        entry = grouped[name]
        lines.append(f"## {name}")

        if entry["commits"]:
            lines.append(f"### コミット {len(entry['commits'])} 件")
            for commit in entry["commits"]:
                lines.append(f"- {commit['datetime']} {commit['subject']}")

        if entry["cli"]:
            lines.append(f"### Claude Code セッション {len(entry['cli'])} 件")
            for session in entry["cli"]:
                lines.append(f"- {_session_headline(session)}")

        if entry["app"]:
            lines.append(f"### Claude アプリ セッション {len(entry['app'])} 件")
            for session in entry["app"]:
                lines.append(f"- {_session_headline(session)}")
                if session.get("initial_message"):
                    lines.append(f"  - 冒頭の依頼: {session['initial_message']}")
                if len(session.get("folders") or []) > 1:
                    lines.append(f"  - 対象フォルダ: {', '.join(session['folders'])}")

        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------- 未記録日の判定 ----------


def recorded_dates() -> set[date]:
    """ミラーから、記録層のノートが既に存在する日付を集める。

    Notion 側ではなくミラーを見るのは，同じ判定を grep 一発で人も再現できるようにするため。
    呼び出し側は判定の前に同期を済ませておくこと。
    """
    notes_dir = MIRROR_DIR / "研究ノート_DB"
    if not notes_dir.is_dir():
        return set()
    found = set()
    for note in notes_dir.rglob("*.md"):
        kind = value = ""
        for line in note.read_text(errors="replace").splitlines():
            if line.startswith("Date:"):
                value = line.split(":", 1)[1].strip()
            elif line.startswith("種別:"):
                kind = line.split(":", 1)[1].strip()
            elif line == "---" and value:
                break
        if kind == "進捗" and value:
            try:
                found.add(date.fromisoformat(value[:10]))
            except ValueError:
                continue
    return found


def pending_dates(days: int) -> list[date]:
    """前日から遡って，活動があるのに記録が無い日を古い順に返す。

    スリープや一時障害で実行を逃した日を次回に埋めるために使う。
    launchd は逃した起動を 1 回に集約するため，これが無いと欠けた日は永久に戻らない。
    """
    yesterday = datetime.now(TZ).date() - timedelta(days=1)
    done = recorded_dates()
    pending = []
    for offset in range(days):
        day = yesterday - timedelta(days=offset)
        if day in done:
            continue
        if collect_commits(day, day) or collect_cli_sessions(day, day) or collect_app_sessions(day, day):
            pending.append(day)
    return sorted(pending)


# ---------- CLI ----------


def resolve_period(args: argparse.Namespace) -> tuple[date, date]:
    """引数から対象期間を決める。既定は前日 1 日ぶん。"""
    yesterday = datetime.now(TZ).date() - timedelta(days=1)
    if args.date:
        target = date.fromisoformat(args.date)
        return target, target
    if args.since or args.until:
        since = date.fromisoformat(args.since) if args.since else yesterday
        until = date.fromisoformat(args.until) if args.until else yesterday
        return since, until
    if args.days:
        return yesterday - timedelta(days=args.days - 1), yesterday
    return yesterday, yesterday


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", help="対象日 (YYYY-MM-DD)。既定は前日")
    parser.add_argument("--since", help="期間の開始日 (YYYY-MM-DD)")
    parser.add_argument("--until", help="期間の終了日 (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="前日から遡る日数")
    parser.add_argument("--format", choices=("md", "json"), default="md", help="出力形式")
    parser.add_argument(
        "--pending",
        type=int,
        metavar="N",
        help="材料を出力せず、前日から N 日遡って未記録かつ活動のある日を 1 行ずつ列挙する",
    )
    parser.add_argument("--recorded", action="store_true", help="記録済みの日付を列挙する（重複確認用）")
    args = parser.parse_args()

    if args.pending is not None:
        for day in pending_dates(args.pending):
            print(day.isoformat())
        return 0
    if args.recorded:
        for day in sorted(recorded_dates()):
            print(day.isoformat())
        return 0

    try:
        since, until = resolve_period(args)
    except ValueError as exc:
        print(f"日付の指定が不正です: {exc}", file=sys.stderr)
        return 2
    if since > until:
        print("--since が --until より後になっています", file=sys.stderr)
        return 2

    commits = collect_commits(since, until)
    grouped = group_by_project(
        commits,
        collect_cli_sessions(since, until),
        collect_app_sessions(since, until),
    )

    # 活動が無ければ何も出さない。呼び出し側が空を見て「記録しない」と判断する
    if not grouped:
        return 0

    references = resolve_references(commits)

    if args.format == "json":
        print(
            json.dumps(
                {"since": since.isoformat(), "until": until.isoformat(), "projects": grouped, "references": references},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_markdown(grouped, since, until, references), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

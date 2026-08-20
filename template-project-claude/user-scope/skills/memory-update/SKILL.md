---
name: memory-update
description: ユーザーが訂正・好み・繰り返しパターンを述べたとき、その内容を `.claude/MEMORY.md` の Preferences / Corrections / Patterns 該当セクションに追記する。トリガー: "don't"、"stop"、"〜じゃなくて〜"、"いつも〜にして"、"今後は〜"、"emダッシュ使わないで" 等の永続化を意図する発言、もしくはユーザーが明示的に "memory に追記して" / "覚えておいて" と言ったとき。CLAUDE.md 既出ルールやハーネス auto-memory に書くべき個人的学習は除外。Use when the user expresses a permanent preference, correction, or recurring pattern that should outlive the current session and be shared with teammates.
---

# プロジェクト記憶ファイル更新 (memory-update)

このスキルは `.claude/MEMORY.md` への追記判断と書込手順を Claude に与える。Miles Deutscher の "Memory.MD" 機構（`docs/CLAUDE_CODE_BEST_PRACTICES.md` Part 3 Step 3）に基づき、本プロジェクトで運用するための実装スキル。

## いつ発火させるか

ユーザーが以下のいずれかに該当する発言をしたとき、本スキルを自動適用する:

- **訂正の発言** — "don't 〜"、"stop 〜"、"〜じゃなくて〜にして"、"〜は使わないで"
- **永続的な好みの表明** — "いつも〜にして"、"今後は〜で"、"このプロジェクトでは〜"
- **繰り返しパターンの宣言** — "この作業は毎回〜"、"〜のときは〜の順でやる"
- **明示的な指示** — "memory に追記して"、"覚えておいて"、"記録して"
- **同じ訂正が 2 回目** — 同セッション内であっても、同種の指摘が繰り返されたら永続化を検討
- **Claude 自身のミス** — 同種のツールエラー・誤った前提・ビルド/テスト失敗に **2 回** 当たった、またはその再現性ある根本原因と解決策を見つけたとき（ユーザーの発言を待たず自発的に記録する）

## 基本理念

CLAUDE.md は **チーム規約**、`.claude/MEMORY.md` は **学習履歴**。新しく覚えた事項をこちらに書き溜めることで、毎セッションの再説明コストをゼロに近づける。

## 書込手順

1. **読込** — `.claude/MEMORY.md` を Read する
2. **判定** — 後述「記録対象の判定」に従い、追記すべきか、書き込むセクションはどこかを決める
3. **重複チェック** — 既存項目を `grep -F` 等で確認。同義の項目があれば追記せず既存を更新する
4. **追記** — Edit ツールで該当セクションに 1 行〜数行で追記。各エントリ冒頭は `-` のリスト記法
5. **ユーザー通知** — 追記したセクション名と要点を 1 文で報告

## 記録対象の判定

### 記録する

| 種類 | 例 | 振り分け先 |
|---|---|---|
| 永続的なスタイル好み | "見出しは ## ではなく ■ で"、"em ダッシュ禁止" | `## Preferences` |
| 再発を防ぐべき訂正 | "ファイル削除前に必ず ls で確認"、"`mkdir -p` を勝手に使わない" | `## Corrections` |
| Claude が解決した再発性ミス | "lint 前に必ず X を実行"、"削除前に必ず ls で存在確認"、"SKILL.md 編集後は drift 確認" | `## Corrections` |
| 繰り返し利用する手順・テンプレ | "新規 skill 追加時は CATALOG.md にも登録"、"PR 説明文は要約 + 動作確認の 2 章構成" | `## Patterns` |

### 記録しない（除外条件）

以下は本ファイルに書かない:

- **CLAUDE.md / 既存 skill に既出のルール** — 重複は context を肥大化させるだけ。CLAUDE.md に書くべき内容ならそちらを Edit する
- **一時的なタスク状態** — "今このバグを調査中" は `tasks/` または会話履歴で十分
- **コード固有のバグ修正** — fix の根拠はコミットメッセージ / PR description に残す。一度きりの bug fix は記録せず、**再現性・再発性のある原因のみ** Corrections へ（同種のミスを 2 回繰り返した場合がこれに当たる）
- **個人スコープの学習** — 特定マシンでの依存関係問題、個人の癖、ローカル context は **ハーネス auto-memory** (`~/.claude/projects/<encoded>/memory/`) に任せる。本ファイルは git 管理対象なのでチーム共有性のない情報は書かない
- **機微情報** — API キー、社内固有名、未公開仕様などは絶対に書かない

## ハーネス auto-memory との使い分け

| 観点 | `.claude/MEMORY.md` | ハーネス auto-memory |
|---|---|---|
| スコープ | プロジェクト（チーム共有） | 個人（マシン単位） |
| 管理 | git | ハーネスが自律管理 |
| 構造 | 単一 Markdown、3 セクション | frontmatter 付き分割ファイル (user/feedback/project/reference) |
| 書込判断 | 本スキルがユーザー承認下で実施 | ハーネスが自律的に実施 |

両者は **競合しない**。プロジェクト共有性で振り分ける。判断に迷う場合: "他の開発者がこのリポジトリで作業するときに役立つか？" が Yes なら本ファイル、No ならハーネス側。

## 出力例

ユーザー: "今後コミットメッセージは英語で書いてください"

Claude（本スキル発火）:

1. `.claude/MEMORY.md` を Read
2. `## Preferences` セクションに該当項目がないことを確認
3. Edit で以下を追記:
   ```
   - コミットメッセージは英語で記述する
   ```
4. ユーザー報告: "`.claude/MEMORY.md` の Preferences に追記しました。"

## 関連ツール

- `.claude/MEMORY.md` — 書込先ファイル本体
- `docs/CLAUDE_CODE_BEST_PRACTICES.md` — 出典（Part 3 Step 3）
- CLAUDE.md の「プロジェクト記憶」セクション — プロジェクト全体方針

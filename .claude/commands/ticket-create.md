---
description: 新規タスクチケット (tasks/T-NNN-<slug>.md) を [ ] チェックボックス形式で生成。次の T-NNN を自動採番し、汎用 5 セクション構成（目的 / 背景 / 手順 / 検証 / 完了報告）を出力する。
allowed-tools: Read, Write, AskUserQuestion, Bash(ls:*), Bash(find:*)
argument-hint: "[slug] (kebab-case、省略時は対話で入力)"
profile_relevance:
  - meta
---

# /ticket-create

`tasks/_template.md` を雛形に新規タスクチケットを生成します。次の T-NNN を自動採番し、手順 / 検証セクションは `- [ ]` で出力。`/ticket-run` で実行するときに `- [x]` へ更新します。

## 実行手順（Claude が踏むステップ）

### ステップ 1: 次の T-NNN を採番

```bash
ls tasks/ tasks/_done/ 2>/dev/null | grep -oE "^T-[0-9]+" | sort -u | tail -1
```

最大 ID を取得し、`+1` して 3 桁ゼロ詰めの新規 ID とする（例: `T-010` → `T-011`、`T-099` → `T-100`）。
ID が衝突する場合（並行作成）は再度 `ls` を実行して採番し直す。

### ステップ 2: slug の取得

引数 `$1` が与えられていればそれを slug として採用。kebab-case (`^[a-z0-9-]+$`) を満たさない場合は警告して再入力を促す。

`$1` が空なら AskUserQuestion で slug を聞く（例: `add-foo-feature` / `fix-bar-bug`）。「Other」を選んだら kebab-case を満たすよう自由入力させる。

同一 slug のファイル（`tasks/T-NNN-<slug>.md` 形式）が既に `tasks/` または `tasks/_done/` に存在する場合は警告し、別 slug を促す。

### ステップ 3: メタ情報の取得（AskUserQuestion）

以下を順に聞く（合計 3 回まで AskUserQuestion を呼ぶ）:

1. **title**（短いタイトル、日本語可）
   - Other で自由入力

2. **category**（4 択 + Other）
   - `setup` — 環境整備 / 初期化 / アーカイブ等
   - `command` — スラッシュコマンド / hook の追加・修正
   - `skill-import` — 外部 skill の取り込み
   - `integration` — MCP / プラグイン / 外部サービス連携
   - Other で `workflow` / `subagent` 等を自由入力

3. **estimated_minutes**（4 択 + Other）
   - `15` / `30` / `45` / `60`
   - Other で任意の整数

`depends_on` / `parallel_with` は frontmatter で空配列 `[]` として出力し、必要なら手動で追記する案内を完了報告に含める。

### ステップ 4: ファイル生成

新規ファイル `tasks/T-NNN-<slug>.md` に以下の雛形を Write する。`tasks/_template.md` は人間向けのリファレンスとして残置（旧 skill-import 用 section を含むためここでは参照しない）。雛形は汎用 5 section 構成（目的 / 背景 / 手順 / 検証 / 完了報告）:

```markdown
---
id: T-NNN
title: <title>
status: todo
category: <category>
depends_on: []
parallel_with: []
estimated_minutes: <minutes>
---

# T-NNN: <title>

> **運用ルール**: 各 `- [ ]` は `/ticket-run` 実行時に `- [x]` へ更新。完了したら frontmatter の `status: done` へ書き換え、本ファイルを `tasks/_done/` へ `mv` する。

## 目的
<手動で 1-2 行で追記>

## 背景
<手動で必要なら追記>

## 手順
- [ ] <作業項目 1>
- [ ] <作業項目 2>
- [ ] <作業項目 3>

## 検証
- [ ] <検証コマンドまたは確認項目 1>
- [ ] <検証コマンドまたは確認項目 2>

## 完了報告（実施後追記）
- 完了時刻:
- 実施者:
- 成果物パス:
- メモ:
```

### ステップ 5: 完了報告

以下を 4〜6 行で日本語まとめ:

- 生成したファイルパス（`tasks/T-NNN-<slug>.md`）
- frontmatter サマリ（id / category / estimated_minutes）
- 次のアクション案内:
  - 目的 / 背景 / 手順 / 検証 セクションを手動で埋める
  - 依存関係があれば `depends_on: [T-XXX]` を追記
  - 実行時は `/ticket-run T-NNN` を呼ぶと `- [ ]` を順に消化し、完了で `_done/` へ自動移動

## エラー処理

- slug が kebab-case でない → 再入力を促す
- 同一 slug が既存 → 別 slug を促す
- T-NNN 採番衝突（並行作成） → 再 `ls` で採番し直し、念のためユーザに通知
- 出力先 `tasks/` ディレクトリが無い → エラー（プロジェクトが壊れている可能性）

## 注意

- `depends_on` / `parallel_with` は対話的に集めない（多くの場合は作成後に手動編集する方が早い）
- 生成直後の本文セクションは placeholder のため、`/ticket-run` を呼ぶ前に必ず人間が中身を埋めること
- 生成時の `status` は常に `todo`。`/ticket-run` 完了時に `done` へ書き換わる

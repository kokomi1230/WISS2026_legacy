---
description: 既存タスクチケット (tasks/T-NNN-<slug>.md) を実行。手順 / 検証 セクションの各 `- [ ]` 項目を順に実施し、完了するたびに `- [x]` へ更新する。全項目が完了したら frontmatter の status を done にし、完了報告を追記してファイルを tasks/_done/ へ移動する。
allowed-tools: Read, Edit, AskUserQuestion, Bash(ls:*), Bash(find:*), Bash(grep:*), Bash(mv:*), Bash(cat:*), Bash(test:*)
argument-hint: "<T-NNN | tasks/T-NNN-<slug>.md> (例: T-011 または tasks/T-011-foo.md)"
profile_relevance:
  - meta
---

# /ticket-run

タスクチケットを 1 項目ずつ実行し、進行に合わせて `- [ ]` を `- [x]` へ更新します。最後にファイルを `tasks/_done/` へ移動して完了。

## 実行手順（Claude が踏むステップ）

### ステップ 1: 対象ファイルの解決

引数 `$1` を解釈:

- `T-NNN` 形式 → `find tasks -maxdepth 1 -name "T-NNN-*.md"` で実ファイル特定
- パス直指定（例: `tasks/T-011-foo.md`） → そのまま採用
- ファイルが見つからない / 既に `tasks/_done/` 配下 → エラーで終了
- 引数省略 → AskUserQuestion で「実行可能なチケット一覧（`ls tasks/T-*.md`）」から選ばせる

### ステップ 2: チケット読込と項目抽出

対象ファイルを Read し、以下を把握:

1. frontmatter の `id` / `title` / `status` / `category`
2. `## 手順` セクションの `- [ ]` 行（行番号と本文）
3. `## 検証` セクションの `- [ ]` 行（行番号と本文）

既に `status: done` の場合は「完了済」と通知して終了するか確認。

### ステップ 3: 手順項目を順に実行

各 `- [ ]` 行について:

1. 行の本文を解釈
   - バックティック内にコマンドが書かれていれば Bash で実行
     - 例: `` - [ ] `grep -r "foo" docs/` が空 `` → `grep -r "foo" docs/` を実行し、出力が空かを確認
   - 自然文（コマンドなし）なら Claude が該当作業を実施（ファイル編集 / 確認 / 設計判断 等）
2. 実施が完了したら **Edit で当該行の `- [ ]` を `- [x]` に書き換え**
   - `old_string` は当該行全体（前後の空白含む）を一意に特定できる長さで指定
   - `replace_all: false` を厳守（複数項目を巻き込まない）
3. 失敗した場合:
   - `- [ ]` のまま残し、AskUserQuestion で「次に進む / 中断 / 当該項目を skip」を確認
   - skip 選択時は行末に ` (skipped: <理由>)` を Edit で追記し、`- [ ]` のままにする

### ステップ 4: 検証項目を順に実行

`## 検証` セクションも手順と同じ要領で 1 行ずつ実行 → Edit で `- [x]` 更新。

### ステップ 5: 全項目完了後の仕上げ

全項目が `- [x]` になったら:

1. frontmatter の `status: todo` / `status: in-progress` を `status: done` に Edit
2. `## 完了報告（実施後追記）` セクションを Edit で以下に書き換え:
   ```
   - 完了時刻: <YYYY-MM-DD>   ※ CLAUDE.md context の currentDate を参照
   - 実施者: Claude Code session
   - 成果物パス: <あれば列挙、無ければ "—">
   - メモ: <実施で気付いた点や skip 項目があればその理由を 1-2 行>
   ```

### ステップ 6: `_done/` へ移動

```bash
mv tasks/T-NNN-<slug>.md tasks/_done/
```

実行後 `ls tasks/_done/T-NNN-*` で移動を確認。

### ステップ 7: 完了報告（コンソール出力）

5〜8 行で日本語まとめ:

- 実施したチケット ID / title
- 消化した手順 / 検証項目数（`- [x]` の数）
- skip した項目があれば理由付きで列挙
- 移動先パス
- 次のアクション候補（依存タスク `depends_on` を参照したフォローアップ）

## エラー処理 / 注意

- 検証コマンドが「期待値と異なる」（例: 空が期待値だが何かヒット）場合は AskUserQuestion で続行可否を確認。盲目的に `- [x]` 化しない
- 検証コマンドに `Bash(...)` で未許可の種別が含まれる場合は権限プロンプトに従う。事前許可は read-only 系（`ls` / `find` / `grep` / `cat` / `test` / `mv`）のみ
- Edit の `old_string` 重複に注意。`- [ ]` だけだと衝突するので前後本文を含めて指定する
- スキップ項目があるまま `_done/` へ移すと「全 [x]」前提の最終検証が崩れるため、原則 1 項目でも skip があれば `_done/` 移動を見送り「未完」のまま `tasks/` に残す（ユーザに判断を仰ぐ）

## 冪等性

同じチケットを 2 回実行しても、既に `- [x]` 済みの項目は no-op で Edit がスキップされる（`old_string` が存在しないため Edit がエラーになるので、各項目 Read 後に `- [ ]` 行のみ処理する）。

---
description: プロジェクトの CLAUDE.md / README.md / .claude/rules/ を検査する。行数・paths: の有無・リンク切れ・絵文字・テンプレート定型節の残留を機械的に判定し、要対応を提示する。write を付けると修正まで行う。
allowed-tools: Bash(python3 ~/.claude/skills/project-docs/validate_docs.py:*), Read, Edit, Write, Glob, Grep, AskUserQuestion
argument-hint: "[check|write] [path] (既定は check、path 省略でカレント)"
profile_relevance:
  - meta
---

# /project-docs

`project-docs` skill の判定基準でドキュメントを点検する。skill は会話の流れでも自動発火するが、本コマンドは**検証だけを意図して呼びたい場面**のために置く。

## 実行手順

### ステップ 1: 検査

```bash
python3 ~/.claude/skills/project-docs/validate_docs.py <path>
```

`<path>` は `$2`（省略時はカレント）。終了コードは `0` = 指摘なし / `1` = 警告のみ / `2` = 要対応。

スクリプトが見つからない場合は、ユーザースコープ資産が未配置である。テンプレートリポジトリの `setup-user-scope.sh` を実行するよう案内して終了する。

### ステップ 2: 報告

指摘を major / minor に分けて提示する。各項目に**なぜ問題か**を 1 行添える。行数超過なら「削る」ではなく「どこへ移すか」を示す。

指摘が無ければ「指摘なし」とだけ返す。褒めたり水増ししたりしない。

### ステップ 3: 修正（`$1` が `write` のときだけ）

`$1` が `check` または省略なら**ここで終了する**。読取専用で終わることが既定である。

`write` の場合:

1. 修正方針を提示して AskUserQuestion で承認を取る
2. major から順に直す。`project-docs` skill の「更新」手順に従う
3. **プロジェクト固有の記述を消さない。** 消してよいのはテンプレート由来の定型節と、コードから読み取れる内容だけ
4. 再度ステップ 1 を実行し、解消を確認する

## 注意事項

- リンク切れの修正は、**リンク先が移動中でないことを確かめてから**行う。ドキュメントの移設作業と並行して走らせると、移動途中のファイルへのリンクを不要に書き換える
- 行数が 200 行を超えていても、内容がすべてプロジェクト固有なら無理に削らない。テンプレート定型やコードから読み取れる内容が無いことを確認したうえで、その旨を報告する

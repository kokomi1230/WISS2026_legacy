---
id: T-XXX
title: <タスクタイトル>
status: todo  # todo | in-progress | done | blocked
category: <skill-import | workflow | command | subagent | integration | setup>
depends_on: []  # 依存タスク ID の配列
parallel_with: []  # 並列実行可能なタスク ID の配列（情報提供のみ）
estimated_minutes: 15
---

# T-XXX: <タスクタイトル>

> **運用ルール**: 各 `- [ ]` は `/ticket-run` 実行時に `- [x]` へ更新。完了したら frontmatter の `status: done` へ書き換え、本ファイルを `tasks/_done/` へ `mv` する。

## 目的
<1-2 行で何を達成するか>

## 入力
- 取得元 URL: `<URL>`
- ライセンス: `<SPDX or "see-upstream">`
- 想定する frontmatter type: `<category>`

## 出力
- パス: `.claude/skills/<category>/<name>/SKILL.md`

## frontmatter テンプレート

```yaml
---
name: <name>
description: <英語または日本語の 1-2 行説明。AI がトリガー判定に使う>
type: <design | development | document | meta | project-management | writing | planning | research | integration | media | workflow>
source: <owner>/<repo>@<sha>
license: <SPDX>
tags: [<tag1>, <tag2>]
profile_relevance: [<profile1>, <profile2>]
---
```

## 手順
- [ ] `WebFetch` で取得元 URL の GitHub commits API から最新 SHA 取得
  - 例: `https://api.github.com/repos/<owner>/<repo>/commits/main`
- [ ] raw URL から SKILL.md を取得
  - 例: `https://raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>/SKILL.md`
- [ ] 取得した SKILL.md を本テンプレ流儀の frontmatter に整える
- [ ] 英語のみの description は本文冒頭に日本語要約を 2-3 行追記
- [ ] 参照ファイル（reference/, scripts/ 等）は同梱せず、取得元 URL をリンクのみ記載
- [ ] 出力パスに保存

## 検証
- [ ] frontmatter に必須 7 キー（name, description, type, source, license, tags, profile_relevance）が揃っている
- [ ] description が AI トリガー用途に適した粒度（1-2 行）
- [ ] 日本語要約が冒頭にある（英語のみソースの場合）
- [ ] 参照ファイルは URL リンク化（重量バンドルを同梱していない）

## フォールバック
- WebFetch がドメイン拒否で失敗 → `.claude/skills/_pending/<name>/NOTE.md` に取得元 URL とエラーを記録、本チケット status を `blocked` に
- SHA 不明 → `source: <owner>/<repo>@main-<YYYY-MM-DD>` で代替
- ライセンス不明 → `license: see-upstream` で記録し、本チケット末尾に `## ライセンス確認待ち` セクション追記

## 完了報告（実施後追記）
- 完了時刻: <YYYY-MM-DD HH:MM>
- 実施者: <session-id or agent name>
- 成果物パス: <絶対パス>
- メモ: <ライセンス確認結果や注意点>

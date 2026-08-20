---
name: general
description: 汎用テンプレート。用途未確定時に選択し、Plan → 実装 → レビュー → コミットの基本ループを提供する 4 プロファイル構成の軸。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
enabled_mcp: []
scaffold:
  - src
  - tests
  - docs
---

# General — 汎用プロファイル（軸）

## 概要
このプロジェクトは**汎用**用途です。特定領域に偏らず、企画 → 実装 → 検証 → コミットの基本サイクルを安定して回すためのプラグインだけを有効化します。研究 / システム開発 / 執筆のいずれにも踏み出せるよう、用途が固まったら `/init-project` を再実行して特化プロファイルに切り替えてください。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — TDD・系統的デバッグ・writing-plans・ブレストなど 20+ スキルを一括提供
- `feature-dev@claude-plugins-official` — 要件 → 設計 → 実装 → テスト → PR のエンドツーエンドガイド
- `code-review@claude-plugins-official` — 差分の設計・可読性・セキュリティ・テスト網羅性レビュー
- `commit-commands@claude-plugins-official` — Git ワークフロー自動化（スマートコミット・PR・チェンジログ）
- `context7@claude-plugins-official` — リアルタイムライブラリドキュメント検索（ハルシネーション防止）

## 一括インストール
```bash
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
```

## 主要ワークフロー
### ワークフロー 1: Plan → 実装 → レビュー → コミット
1. `feature-dev` で要件を整理し、必要なら Plan Mode で計画を固める
2. `superpowers` の writing-plans / TDD / systematic-debugging を使って実装
3. ライブラリ仕様調査が必要になったら `context7` で公式ドキュメントを参照
4. `code-review` で差分を自己レビュー（設計・可読性・セキュリティ・テスト網羅性）
5. `commit-commands` でコミットメッセージ整形・PR 作成

## 主要 subagent

> 校正 subagent（`japanese-proofreader` / `english-proofreader` / `code-style-reviewer`）と執筆スタイル skill（`japanese-writing-style` / `english-writing-style` / `code-style`）、`/swap-punctuation` はユーザースコープ（`~/.claude/`）にあり、プロファイルに関わらず常時利用できる。`/init-project` の退避対象ではない。
- `planner` — 大規模・不確実な変更の前段プラン作成（書込みなし）
- `code-reviewer` — 差分レビュー
- `debugger` — バグ報告から最小再現と修正パッチ
- `japanese-proofreader` — 日本語ドキュメント・README の校正（必要時）
- `english-proofreader` — 英語ドキュメント・README の校正（必要時）

## 主要 skill / command
- `japanese-writing-style` — 日本語文書の文体・句読点ルール（README・設計書を整える時に発火）
- `english-writing-style` — 英語文書の文体ルール（OSS の README / API docs 等に発火）
- `/swap-punctuation` — 「，」「．」⇄「、」「。」の一括変換

## 行動指針
- 出力言語は日本語、コードコメントは英語
- 不明点は AskUserQuestion で確認してから着手
- 変更が大きい場合は Plan Mode でユーザーと方向性を擦り合わせる
- 完了報告前に `self-verify` 系チェックを通す

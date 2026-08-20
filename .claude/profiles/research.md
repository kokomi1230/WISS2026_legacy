---
name: research
description: 文献収集 → 構造化抽出 → 実験コード → 可視化までを一気通貫で扱う研究用途プロファイル。general 軸に Web リサーチ・ベクトル DB・ML ハブ・Python LSP を加える。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
  - firecrawl@claude-plugins-official
  - huggingface-skills@claude-plugins-official
  - pinecone@claude-plugins-official
  - exa@claude-plugins-official
  - pyright-lsp@claude-plugins-official
enabled_mcp: []
scaffold:
  - sources
  - notes
  - experiments
  - references
  - output
---

# Research — 研究プロファイル

## 概要
このプロジェクトは**研究**用途です（論文調査・データ分析・実験コード・可視化）。一次情報を Web から取得して構造化し、ベクトル DB に保存して横断検索しつつ、Python で実験コードを書くというフローを想定しています。出典明示と再現性を最優先し、捏造を避けます。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — writing-plans / TDD / systematic-debugging
- `feature-dev@claude-plugins-official` — 調査計画と実験計画の標準化
- `code-review@claude-plugins-official` — 実験コード差分レビュー
- `commit-commands@claude-plugins-official` — 進捗を細かくコミット
- `context7@claude-plugins-official` — ライブラリ仕様の最新確認

### 特化追加（research 専用 5 個）
- `firecrawl@claude-plugins-official` — Web スクレイピング・サイトクロール・自律リサーチ
- `huggingface-skills@claude-plugins-official` — モデル・データセット管理（ML 必須統合）
- `pinecone@claude-plugins-official` — ベクトル DB（論文・ノートのセマンティック検索）
- `exa@claude-plugins-official` — 学術系の精度重視 Web 検索 API
- `pyright-lsp@claude-plugins-official` — Python 型推論・参照解析（実験コードを型安全に）

## 一括インストール
```bash
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install firecrawl@claude-plugins-official
/plugin install huggingface-skills@claude-plugins-official
/plugin install pinecone@claude-plugins-official
/plugin install exa@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
```

## 主要ワークフロー
### ワークフロー 1: 文献収集 → 構造化抽出 → 実験コード → 可視化
1. `exa` / `firecrawl` で一次情報（論文・記事・サイト）を収集
2. 取得した本文を `pinecone` のベクトル DB にインデックス、横断クエリで関連箇所を抽出
3. `huggingface-skills` で必要なモデル・データセットを取得（評価ベンチ含む）
4. `feature-dev` で実験計画 → `superpowers` の TDD / writing-plans で実験コード化
5. `pyright-lsp` で型エラー・参照を確認、`code-review` で自己レビュー → `commit-commands` でコミット

## 主要 subagent

> 校正 subagent（`japanese-proofreader` / `english-proofreader` / `code-style-reviewer`）と執筆スタイル skill（`japanese-writing-style` / `english-writing-style` / `code-style`）、`/swap-punctuation` はユーザースコープ（`~/.claude/`）にあり、プロファイルに関わらず常時利用できる。`/init-project` の退避対象ではない。
- `data-scientist` — データ探索・可視化・統計分析（CSV / SQL / Jupyter）
- `planner` — 調査計画の作成（書込みなし）
- `code-reviewer` — 実験コード差分レビュー
- `japanese-proofreader` — 日本語論文・申請書の校正（提出前チェック）
- `english-proofreader` — 英語論文・grant proposal の校正（投稿前チェック）

## 主要 skill / command
- `japanese-writing-style` — 論文・申請書執筆時の文体・句読点・構造ルール（である調・「，」「．」・複文 70%）
- `english-writing-style` — 英語論文・grant の文体ルール（plain English、能動態、Strunk & White ベース）
- `/swap-punctuation` — 「，」「．」⇄「、」「。」の一括変換（本文整形用）

## 行動指針
- 出典・引用元・取得日時を必ず記録
- 不確実な情報は「推定」「未確認」と明記
- 一次情報 > 二次情報の優先順位を厳守
- `firecrawl` 取得時は URL/DOI を `references/` に保存し、要約だけにしない

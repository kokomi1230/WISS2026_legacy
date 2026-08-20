---
name: writing
description: ブログ・書籍・技術文書・マーケコンテンツの執筆プロファイル。ブランド指針確認 → 草稿 → レビュー → 公開のフローで品質と一貫性を担保する。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
  - brand-voice@knowledge-work-plugins
  - marketing@knowledge-work-plugins
  - claude-md-management@claude-plugins-official
  - mintlify@claude-plugins-official
enabled_mcp: []
scaffold:
  - content
  - drafts
  - references
  - assets
  - output
---

# Writing — 執筆プロファイル

## 概要
このプロジェクトは**執筆**用途です（ブログ・書籍・技術文書・翻訳・マーケコンテンツ）。ブランドトーンと SEO 観点を踏まえつつ、章立て → 草稿 → レビュー → 公開のサイクルを回します。技術文書では API リファレンス・SDK ドキュメントの自動生成も組み合わせます。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — writing-plans / brainstorming で章立てを設計
- `feature-dev@claude-plugins-official` — コンテンツ仕様の構造化
- `code-review@claude-plugins-official` — コードサンプル・差分レビュー（校正観点でも有用）
- `commit-commands@claude-plugins-official` — 章単位コミット・PR
- `context7@claude-plugins-official` — 技術文書で取り上げるライブラリ仕様の照合

### 特化追加（writing 専用 4 個）
- `brand-voice@knowledge-work-plugins` — ブランドトーンを全コンテンツで統一
- `marketing@knowledge-work-plugins` — SEO 監査・コンテンツ戦略・競合分析
- `claude-md-management@claude-plugins-official` — CLAUDE.md / 内部ドキュメントの品質統制
- `mintlify@claude-plugins-official` — コードから API ドキュメント自動生成

## 一括インストール
```bash
/plugin marketplace add anthropics/knowledge-work-plugins
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install brand-voice@knowledge-work-plugins
/plugin install marketing@knowledge-work-plugins
/plugin install claude-md-management@claude-plugins-official
/plugin install mintlify@claude-plugins-official
```

## 主要ワークフロー
### ワークフロー 1: ブランド指針確認 → 草稿 → レビュー → 公開
1. `brand-voice` でトーン・スタイルガイドを取り込み、文体を確定
2. `marketing` で SEO キーワード・競合・構成案を作成
3. `feature-dev` + `superpowers` の writing-plans で章立てを設計、ユーザー承認後に本文化
4. 技術文書なら `mintlify` で API リファレンスを自動生成、`context7` でライブラリ仕様を照合
5. `claude-md-management` でドキュメント整合性を再点検
6. `code-review` で校正観点レビュー → `commit-commands` で公開コミット

## 主要 subagent

> 校正 subagent（`japanese-proofreader` / `english-proofreader` / `code-style-reviewer`）と執筆スタイル skill（`japanese-writing-style` / `english-writing-style` / `code-style`）、`/swap-punctuation` はユーザースコープ（`~/.claude/`）にあり、プロファイルに関わらず常時利用できる。`/init-project` の退避対象ではない。
- `japanese-proofreader` — 日本語校正 subagent（Read 専用、`japanese-writing-style` skill のルール適用）
- `english-proofreader` — 英文校正 subagent（Read 専用、`english-writing-style` skill のルール適用）
- `code-reviewer` — コードサンプル・構造の差分レビュー
- `planner` — 章立て・連載計画の前段プラン作成

## 主要 skill / command
- `japanese-writing-style` — 日本語論文・申請書の文体・句読点・構造ルールを自動適用（本多勝一・木下是雄ベース）
- `english-writing-style` — 英語論文・grant proposal・技術文書の文体ルール（plain English、能動態優先、Strunk & White ベース）
- `/swap-punctuation` — 「，」「．」⇄「、」「。」を一括変換（コードブロック / LaTeX 数式 / URL は保護）

## 行動指針
- 出力は日本語マークダウン、技術用語は適宜英語併記
- 文書全体で文体を一貫させる（ですます調 / だである調）
- 長文は **章立てをユーザー承認後に本文化**
- コード例は最小限の動く例
- 引用・参考文献は出典 URL と取得日時を明示

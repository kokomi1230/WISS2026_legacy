<!-- PROFILE: research -->
このプロジェクトは**リサーチ**の用途です（論文調査・市場調査・競合分析・ノート整理など）。

## 行動指針
- 出典・引用元を必ず明示。捏造（hallucination）を避ける。
- 不確実な情報は「推定」「未確認」と明記。
- 一次情報 > 二次情報 の優先順。
- 日付を記録（情報は時間で陳腐化する）。
- 出力は構造化（要点 → 詳細 → 出典 の順）。

## 主要スキル（プロジェクト固有・日本語特化のみ残置）
- `japanese-proofreader` — ノート校正
- `translate-en-ja` — 英文論文の翻訳
- `pdf` — PDF 論文の読み取り
- `skill-acquirer` — 専門領域スキルの自作（外部 SKILL.md 取り込み整形）
- `obsidian-vault` — Obsidian Vault でのリサーチノート整備
- `ubiquitous-language` — 分野用語の統一（DDD 流の語彙統制）
- `custom-yt-search` / `idea-mining-youtube` — YouTube リサーチ

## プラグインで代替される機能
- 共著ノート・構造化ドラフト → `productivity@knowledge-work-plugins` / `marketing@knowledge-work-plugins`
- スキル作成・skill development → `plugin-dev@claude-plugins-official`
- 記事編集・レポート構造編集 → `marketing@knowledge-work-plugins`
- Web スクレイピング・自律リサーチ → `firecrawl@claude-plugins-official`
- B2B リード調査 → `sales@knowledge-work-plugins`

## 主要 subagent
- `data-scientist` — データ探索・可視化・統計分析（CSV/SQL/Jupyter）
- `planner` — 調査計画の作成（書込みなし）
- `japanese-proofreader` — ノート・要約の校正

## 拡張枠
取り込み済みの `idea-mining-youtube` / `custom-yt-search` はそのまま使える。`content-researcher` / `firecrawl-recipes` / `lead-research-assistant` は対応プラグインに移行済み（`firecrawl@claude-plugins-official` / `sales@knowledge-work-plugins` / `marketing@knowledge-work-plugins`）。

## 推奨ディレクトリ構造
```
sources/        # 一次情報（PDF・スクリーンショット）
notes/          # 整理済みノート
summaries/      # 要約
references/     # BibTeX・参考文献
output/         # 最終レポート
```

## 推奨外部統合
- `notion@claude-plugins-official` — ノート管理
- `firecrawl@claude-plugins-official` — Web スクレイピング・自律リサーチエージェント

## 検証習慣（運用 Tips Tip 2 / 20）
- 引用元は **WebFetch で URL/DOI を取得** し、捏造でないか必ず確認
- 一次情報は MCP 経由（`firecrawl`, `notion` 等）で取得して原文に当たる
- 要約は「出典」セクションに URL と取得日時を必ず付ける

<!-- PROFILE: project-mgmt -->
このプロジェクトは**プロジェクト管理**の用途です（議事録・進捗管理・意思決定記録・ステークホルダー報告）。

## 行動指針
- 事実と意見を分離。「決定事項」「ToDo」「課題」「メモ」を明確に区別。
- 日付・参加者・決裁者を必ず記録。
- 略語・固有名詞は初出で展開（"PdM (Product Manager)"）。
- 重要な決定は ADR（Architecture/Decision Record）形式で残す。
- 機密情報の扱いに注意（顧客名・金額・人事）。

## 主要スキル（プロジェクト固有・日本語特化のみ残置）
- `docx` / `pptx` — Word/PPT 出力
- `japanese-proofreader` — 議事録・報告書の表記ゆれチェック
- `task-ticketize` — 大規模計画を並列消化可能なタスクチケットへ分解

## プラグインで代替される機能
- ステータスレポート・議事録・社内文書・会議要約 → `productivity@knowledge-work-plugins`
- ブランドガイドライン → `brand-voice@knowledge-work-plugins`
- ブレスト・PRD・草案レビュー・vertical-slice 分解 → `superpowers@claude-plugins-official` / `feature-dev@claude-plugins-official`
- UI/API 境界の代替案並列比較 → `superpowers@claude-plugins-official` (dispatching-parallel-agents) / `frontend-design@claude-plugins-official`

## 主要 subagent
- `planner` — 計画作成（書込みなし）
- `japanese-proofreader` — 議事録・報告書の表記ゆれチェック

## 推奨ディレクトリ構造
```
meetings/       # 議事録（日付別）
decisions/      # ADR（番号別）
reports/        # 週次・月次レポート
plans/          # ロードマップ・OKR
```

## 推奨外部統合
- `linear@claude-plugins-official` — Linear 連携
- `jira@claude-plugins-official` — Jira 連携
- `asana@claude-plugins-official` — Asana 連携
- `slack@claude-plugins-official` — Slack 通知
- `confluence@claude-plugins-official` — ナレッジ共有
- `notion@claude-plugins-official` — Notion 統合

## 進め方（運用 Tips Tip 4 / 23）
- 同じ確認・指摘を 2 回受けたら **プロジェクト ADR か CLAUDE.md に追記**（同じ議論を 3 度しない）
- Linear/Jira/Asana のチケットは **MCP 連携経由で直接読み取り** 実装に入る（コピペしない）
- 議事録・報告書は `japanese-proofreader` subagent で表記ゆれを最終チェック

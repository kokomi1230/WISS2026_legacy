<!-- PROFILE: general -->
このプロジェクトは**汎用**用途です。特定のカテゴリに偏らず、必要に応じて様々な作業を行います。

## 行動指針
- 用途が固まったら `/init-project` を再実行して特化プロファイルに切り替えることを推奨。
- 出力言語は日本語をデフォルト。
- 不明点は AskUserQuestion で確認してから着手。
- 試行錯誤の場合は小さく分けて検証。

## 主要スキル
プラグイン化された機能はプラグイン側で提供されるため、ここではプロジェクト固有スキルのみ残す:
- メタ: project-init, skill-pruner, catalog-generator, plugin-installer, skill-finder, skill-acquirer, self-verify
- 執筆: japanese-proofreader, translate-en-ja
- 開発: claude-api
- ドキュメント: pdf

## プラグインで代替される機能
- 企画・PRD・ブレスト → `superpowers@claude-plugins-official` / `feature-dev@claude-plugins-official`
- TDD・デバッグ・並列ディスパッチ → `superpowers@claude-plugins-official`
- 議事録・文書処理・週次レポート → `productivity@knowledge-work-plugins`
- スキル/プラグイン開発支援 → `plugin-dev@claude-plugins-official`

## 主要 subagent
- `planner` — 大規模・不確実な変更の前段プラン作成
- `code-reviewer` — 差分レビュー
- `debugger` — バグ原因特定→修正パッチ

## 推奨ディレクトリ構造
（用途確定後に追加）

## 推奨外部統合
- `github@claude-plugins-official`（必要に応じて）
- `slack@claude-plugins-official`（必要に応じて）
- `context7@claude-plugins-official` — リアルタイム API ドキュメント検索（開発時に強く推奨）
- `superpowers@claude-plugins-official` — 汎用スキルバンドル（TDD・デバッグ・プラン→実装）
- `commit-commands@claude-plugins-official` — Git ワークフロー自動化（必要に応じて）

## 進め方（運用 Tips Tip 1 / 2 / 18）
- 用途が固まらないうちは **Plan Mode** で着手し、変更前にユーザーと方向を擦り合わせる
- 完了報告前に `self-verify` skill のチェック表を最低限通す
- セッションが長くなったら `/compact` を活用、重要な発見は `/btw` で auto memory へ

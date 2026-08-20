<!-- PROFILE: web-dev -->
このプロジェクトは**Web 開発**の用途です（フロントエンド・バックエンド・API・SPA）。

## 行動指針
- 既存コードのパターン・命名規則を踏襲。新規ファイルより既存ファイル編集を優先。
- 型安全を重視（TypeScript なら `any` を避ける、Python なら型ヒント付与）。
- セキュリティ・パフォーマンスを意識（OWASP Top 10、N+1 クエリ等）。
- テストを書く（変更箇所に対応するユニットテスト最低 1 つ）。
- コミットメッセージは Conventional Commits 形式推奨。
- フィーチャーブランチで作業、main 直接コミットしない。

## 主要スキル（プロジェクト固有・特化領域のみ残置）
- `claude-api` — Claude API 統合
- `hookify-writing-rules` — フック作成ルール
- `claude-opus-4-5-migration` — モデル移行
- `improve-codebase-architecture` — ADR を参照したアーキテクチャ深化提案
- `react-best-practices` — React 特化ガイダンス
- `git-guardrails` — 危険な git コマンドのブロック設定
- `setup-pre-commit` — Husky pre-commit hook 設定
- `migrate-to-shoehorn` — TS 特定ライブラリ移行

## プラグインで代替される機能
- フロントエンド設計・Web アーティファクト → `frontend-design@claude-plugins-official`
- Web アプリ E2E テスト → `playwright@claude-plugins-official` / `chrome-devtools@claude-plugins-official`
- MCP・プラグイン・スキル・hook・agent・command 開発 → `plugin-dev@claude-plugins-official`
- TDD・系統的デバッグ・並列ディスパッチ・ブランチ完了 → `superpowers@claude-plugins-official`
- コードレビュー → `code-review@claude-plugins-official`

## 主要 subagent
- `code-reviewer` — 差分の設計/可読性/セキュリティ/テスト網羅性レビュー
- `debugger` — バグ報告・ログから原因特定→最小再現→修正パッチ
- `planner` — 大規模・不確実な変更の前段プラン作成（書込みなし）

## 推奨ディレクトリ構造
```
src/            # ソースコード
tests/          # テスト
public/ or static/  # 静的アセット
docs/           # 開発ドキュメント
```

## 推奨外部統合
- `github@claude-plugins-official` — GitHub Issues/PR
- `sentry@claude-plugins-official` — エラー監視
- `vercel@claude-plugins-official` — デプロイ
- `pyright-lsp` / `typescript-lsp` / `rust-analyzer-lsp` — LSP
- `context7@claude-plugins-official` — リアルタイム API ドキュメント検索・ハルシネーション防止（強く推奨）
- `superpowers@claude-plugins-official` — TDD・デバッグ・プラン→実装など 20+ スキル一括
- `commit-commands@claude-plugins-official` — Git ワークフロー自動化（コミット・PR・チェンジログ）
- `supabase@claude-plugins-official` — DB・認証・ストレージ管理
- `ralph-loop@claude-plugins-official` — 自律コーディングセッション
- `mintlify@claude-plugins-official` — コードからドキュメント自動生成
- `chrome-devtools@claude-plugins-official` — フロントエンドデバッグ（フロント開発時）

## 検証習慣（運用 Tips Tip 2 / 13）
- フロントエンド変更後は `playwright@claude-plugins-official` / `chrome-devtools@claude-plugins-official` プラグインでスクリーンショットを撮り、UI 崩れを確認する
- API 変更は `curl` / `httpie` で実レスポンスを確認してから完了報告（モックで済ませない）
- 型チェック (`npx tsc --noEmit`) と関連テスト (`npm test -- --related <file>`) は完了前に必ず通す
- 詳細は `self-verify` skill 参照

## 並列ワークフロー（Tip 3 / 9）
- 独立機能を同時開発する場合は `git worktree add ../<repo>-feat-x feat-x` で worktree 分離
- 各 worktree で別 Claude セッションを立て、`code-reviewer` subagent でクロスレビュー

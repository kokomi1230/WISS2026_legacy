<!-- PROFILE: devops -->
このプロジェクトは**DevOps / SRE / インフラ**用途です（CI/CD・デプロイ・監視・インシデント対応・運用自動化）。

## 行動指針
- 本番影響を伴う変更は必ず **Plan Mode** で計画→ユーザー承認後に実行。
- 変更ごとに **ロールバック手順** を記録（runbook 更新）。
- シークレットの誤コミット禁止（pre-commit hook 推奨）。`.env` / `credentials.json` 等は `.gitignore` 必須。
- インフラ as Code（Terraform / CloudFormation / Pulumi 等）を優先。手動変更はドキュメント化。
- 監視・アラートの誤検知を残さない（ノイズはオンコール疲弊を生む）。

## 主要スキル（プロジェクト固有・特化領域のみ残置）
- `claude-api` — Claude API/SDK の本番運用（プロンプトキャッシング含む）
- `hookify-writing-rules` — フック作成ベストプラクティス
- `claude-opus-4-5-migration` — モデル移行（コスト最適化）
- `improve-codebase-architecture` — ADR を参照したリファクタ提案
- `skill-acquirer` — 外部スキル取り込み（運用フローへの組み込み）
- `git-guardrails` — 危険 git コマンドのブロック設定
- `setup-pre-commit` — Husky pre-commit hook 設定
- `dependency-auditor` 退避済み → security-guidance プラグインで代替

## プラグインで代替される機能
- フック・MCP・プラグイン・skill・agent・command 開発 → `plugin-dev@claude-plugins-official`
- コードレビュー → `code-review@claude-plugins-official`
- 系統的デバッグ・ブランチ完了処理・並列ディスパッチ・計画実行 → `superpowers@claude-plugins-official`
- セキュリティスキャン・依存性監査 → `security-guidance@claude-plugins-official`

## 主要 subagent
- `code-reviewer` — 差分の設計/可読性/セキュリティ/テスト網羅性レビュー
- `debugger` — バグ報告・ログから原因特定→最小再現→修正パッチ

## 推奨ディレクトリ構造
```
infra/          # IaC（Terraform / Pulumi / CDK）
runbooks/       # 運用手順書・インシデント対応
monitoring/     # ダッシュボード設定・アラートルール
pipelines/      # CI/CD 定義（.github/workflows, .gitlab-ci.yml 等）
scripts/        # 運用スクリプト
```

## 推奨外部統合

公式マーケット（自動登録）から:
- `deploy-on-aws@claude-plugins-official` — AWS デプロイ・アーキテクチャ推奨・コスト見積もり
- `vercel@claude-plugins-official` — Vercel デプロイ・ビルド・ログ・ドメイン管理
- `sentry@claude-plugins-official` — 本番エラー監視・スタックトレース・修正提案
- `pagerduty@claude-plugins-official` — デプロイリスクスコア（コミット前評価）
- `github@claude-plugins-official` — PR / Issue / CI 操作
- `commit-commands@claude-plugins-official` — スマートコミット・PR 作成・チェンジログ
- `security-guidance@claude-plugins-official` — OWASP Top 10 / シークレット検出
- `mintlify@claude-plugins-official` — コードからドキュメント自動生成（runbook 自動化）

LSP（プロジェクトで使う言語を選択）:
- `typescript-lsp` / `pyright-lsp` / `rust-analyzer-lsp` / `ruby-lsp`

補助:
- `slack@claude-plugins-official` — オンコール通知・インシデント連絡
- `linear@claude-plugins-official` — Issue / インシデントチケット

## 検証習慣（運用 Tips Tip 2 / 13）
- インフラ変更後は `terraform plan` / `cdk diff` を必ず確認してから apply
- デプロイ後は **メトリクス確認 + ロールバック確認**（最低 5〜10 分は監視）
- シークレット系の変更は `security-guidance` プラグインでスキャン
- 詳細は `self-verify` skill 参照

## インシデント対応フロー
1. アラート受信 → Slack で `incident-XXXX` チャンネル作成
2. 影響範囲評価（ユーザー数・サービス・データ）
3. ロールバック判断（< 5 分で復旧見込みなければロールバック優先）
4. 復旧後 24h 以内に **ポストモーテム** を `runbooks/postmortems/` へ記録

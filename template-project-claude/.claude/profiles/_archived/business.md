<!-- PROFILE: business -->
このプロジェクトは**ビジネス／ナレッジワーク**用途です（マーケティング・営業・財務・法務・社内文書・ブランド運用）。

## 行動指針
- 機密情報の取り扱いに細心の注意（顧客名・契約金額・個人情報）。
- 法務・財務関連は **初回スクリーニングのみ**。最終判断は専門家に委ねる。
- ブランドトーンを文書全体で統一する（Brand Voice プラグイン併用推奨）。
- 数値・固有名詞は出典を明記。推測値には「推定」「目安」と注記。
- 出力言語は日本語マークダウン。社外向けは敬体（ですます調）。

## 主要スキル（プロジェクト固有・日本語特化のみ残置）
- `japanese-proofreader` — 日本語校正（誤字・表記ゆれ・敬語）
- `translate-en-ja` — 英日双方向翻訳（契約書・プレスリリース・社外メール）
- `docx` / `pptx` / `xlsx` / `pdf` — 各種オフィス文書フォーマット
- `obsidian-vault` — 社内ナレッジベース整備
- `ubiquitous-language` — 社内用語の統一（営業/開発/法務間の語彙整合）
- `domain-name-brainstormer` — 新規プロダクト/ドメイン名候補生成
- `image-generator` — マーケ用ビジュアル生成（Nano Banana 2）

## プラグインで代替される機能
- ステータスレポート・社内文書・議事録・会議要約 → `productivity@knowledge-work-plugins`
- ブランドガイドライン・トーン統一 → `brand-voice@knowledge-work-plugins`
- SEO・記事編集・コンテンツ戦略 → `marketing@knowledge-work-plugins`
- 企画・PRD・草案レビュー → `feature-dev@claude-plugins-official` / `superpowers@claude-plugins-official`
- PDF/Word/Excel 一括処理・請求書処理 → `productivity@knowledge-work-plugins`

## 主要 subagent
- `japanese-proofreader` — 校正 subagent（Edit のみ書込み可）

## 推奨ディレクトリ構造
```
content/        # 公開コンテンツ・記事
reports/        # 月次・週次レポート
contracts/      # 契約書（要アクセス制御）
decks/          # プレゼン資料
brand/          # ブランドガイドライン・トーン定義
```

## 推奨外部統合（`knowledge-work-plugins` マーケット必須）

まず以下を実行してマーケットプレイスを追加:
```
/plugin marketplace add anthropics/knowledge-work-plugins
```

その後、以下を導入:
- `brand-voice@knowledge-work-plugins` — ブランドトーン統一
- `marketing@knowledge-work-plugins` — SEO 監査・コンテンツ戦略・競合分析
- `sales@knowledge-work-plugins` — 見込み客リサーチ・メールシーケンス・反論対応
- `legal@knowledge-work-plugins` — 契約レビュー・コンプライアンス（初回スクリーニング）
- `finance@knowledge-work-plugins` — 財務分析・予算計画・予測モデル
- `productivity@knowledge-work-plugins` — 会議要約・タスク管理・メール下書き

補助:
- `notion@claude-plugins-official` — ドキュメント／ナレッジ管理
- `slack@claude-plugins-official` — 社内連絡
- `linear@claude-plugins-official` — タスク管理

## 進め方（運用 Tips Tip 1 / 2 / 4）
- 長文・複数ステークホルダー宛は **章立てを先にレビュー** してもらってから本文へ
- 数字や固有名詞は **必ず出典確認**（事実検証を省かない）
- 同じ指摘が 2 度入ったら ADR / ブランド規約に追記
- 法的・財務的なクリティカルパスは **必ず人間レビューを挟む**

<!-- PROFILE: writing -->
このプロジェクトは**執筆系**の用途です（ブログ・書籍・技術文書・翻訳・校正など）。

## 行動指針
- 出力は基本的に日本語マークダウン。技術用語は適宜英語併記。
- 文体は文書全体で一貫させる（ですます調 / だである調）。ユーザーが指定した文体を維持。
- 長い文章を書く場合は章立て・見出しを先に提示してから本文に入る。
- コード例を含める場合は最小限の動く例を示す。
- 引用・参考文献は明示する。

## 主要スキル（プロジェクト固有・日本語特化のみ残置）
- `japanese-proofreader` — 日本語校正
- `translate-en-ja` — 英日双方向翻訳
- `docx` / `pdf` / `pptx` — 各種文書フォーマット出力
- `obsidian-vault` — Obsidian Vault でのノート整備（wikilink/MOC）
- `ubiquitous-language` — DDD のドメイン用語集を文書横断で統一

## プラグインで代替される機能
- 文書共著・社内コミュニケーション・週次レポート → `productivity@knowledge-work-plugins`
- ブランドトーン統一 → `brand-voice@knowledge-work-plugins`
- 記事編集・SEO・コンテンツ戦略 → `marketing@knowledge-work-plugins`
- リサーチ→ドラフト→校正の一気通貫 → `marketing@knowledge-work-plugins` + `firecrawl@claude-plugins-official`

## 主要 subagent
- `japanese-proofreader` — 日本語校正 subagent（Edit のみ書き込み可）

## 推奨ディレクトリ構造
```
content/        # 執筆本体（章別 .md ファイル）
references/     # 参考資料・引用元
drafts/         # 下書き
output/         # 最終出力（PDF/DOCX）
```

## 推奨外部統合
- `notion@claude-plugins-official` — Notion 連携

## 進め方（運用 Tips Tip 1 / 2 / 15）
- 長い文章は **章立てを先に提示しユーザー承認後に本文** へ（Plan→実装）
- 仕様が曖昧な依頼は、いきなり書き始めず **Claude からユーザーに質問** して要件を引き出す（Tip 15 "Let Claude interview you"）
- 完成後は `japanese-proofreader` subagent または skill を再実行し、差分を読み返して完了報告

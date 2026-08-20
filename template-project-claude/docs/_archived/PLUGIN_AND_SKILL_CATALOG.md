# プラグイン & スキル カタログ（統合版）

> 本ドキュメントは旧 docs/ 配下の以下 2 件を統合したもの。元ファイルの章タイトル・著者注釈は原文のまま保持し、見出しレベルのみ降格（H1 → H2 等）して章間構造を整えている。
>
> - `CLAUDE_CODE_PLUGIN_GUIDE_36.md`（9,000 件から厳選した 36 プラグイン）
> - `CLAUDE_SKILLS_72_SELECTION.md`（トップ層が使う 72 スキル）

## 目次

- [PART 1: プラグイン 36 選](#part-1-プラグイン-36-選)
- [PART 2: スキル 72 選](#part-2-スキル-72-選)

---

# PART 1: プラグイン 36 選

> **原資料**: `docs/CLAUDE_CODE_PLUGIN_GUIDE_36.md`

## Claude Code プラグイン完全ガイド ── 9,000件から厳選した36選

> 元ポスト: [@ClaudeCode_love](https://x.com/ClaudeCode_love/status/2049469282107691216) / [@zodchiii](https://x.com/zodchiii/status/2042529018260656555)

Claude Codeを使っているのに、まだ「プラグイン」を入れていない人へ。Skills、MCPまでは理解している人が増えてきた一方で、Claude Codeの進化を一気に加速させる本命が「プラグイン」です。

公式Anthropicマーケットプレイス、トップコミュニティコレクション、開発者が実際に話題にしているプラグインを全部チェックし、用途別に36個に厳選したまとめ。

---

### そもそもプラグインとは何か

プラグインとは、**スキル・コマンド・フック・MCPサーバー**がまとめられたパッケージ。1つのコマンドでインストールでき、設定ファイルを自分で書く必要はありません。Claude Codeでできることを拡張してくれるもの、と思えばOK。

---

### インストール方法（全プラグイン共通）

1. ターミナルで Claude Code を開く
2. `/plugin` と入力
3. **Discover** タブに移動
4. 名前でプラグインを探す
5. 選んでインストール範囲（ユーザー or プロジェクト）を選択

事前に [claude.com/plugins](https://claude.com/plugins) で全カタログを確認可能。

公式マーケットプレイスにないコミュニティ製プラグインは、まずマーケットプレイスを追加:

```
/plugin marketplace add owner/repo
```

すると、そのリポジトリのプラグインが Discover タブに表示されるようになります。

---

### 公式 Anthropic プラグイン(01〜08)

公式マーケットプレイスにあるもの。Anthropicが作ったか検証済み。

| # | プラグイン | 概要 |
|---|---|---|
| 01 | **Frontend Design** | AIっぽくない、ちゃんとしたUIコードを生成。リアルなデザインシステム、太字のタイポグラフィ。**40万+インストール**で最も人気のプラグイン。[link](https://claude.com/plugins/frontend-design) |
| 02 | **Superpowers** | 20以上のスキルが入ったスイスアーミーナイフ。TDD、デバッグ、プラン→コード変換、ブレスト、スキル作成。**29万+インストール**。[link](https://claude.com/plugins/superpowers) |
| 03 | **Context7** | リアルタイムのドキュメント検索。ソースリポから最新のAPIと使用例を取得。古いライブラリコードのハルシネーションを防ぐ。[link](https://claude.com/plugins/context7) |
| 04 | **Code Review** | 構造化されたコードレビュー。バグ、セキュリティ、パフォーマンス、スタイル。レビュアーエージェント内蔵。[link](https://claude.com/plugins/code-review) |
| 05 | **Security Guidance** | OWASP Top 10、認証の欠陥、インジェクション脆弱性、ハードコードされたシークレットをスキャン。[link](https://claude.com/plugins/security-guidance) |
| 06 | **Commit Commands** | Gitワークフローの自動化。スマートコミット、PR作成、チェンジログ生成。[link](https://claude.com/plugins/commit-commands) |
| 07 | **Feature Dev** | 機能実装のエンドツーエンドワークフロー。仕様→計画→実装→テスト→PR。[link](https://claude.com/plugins/feature-dev) |
| 08 | **Plugin Toolkit** | 自分でプラグインを作るための7つのエキスパートスキル。フック、MCP、コマンド、エージェント、バリデーション。[link](https://claude.com/plugins/plugin-toolkit) |

---

### コード品質 & 言語サーバー(09〜12)

VS Codeと同じコードインテリジェンスをClaudeに与えるプラグイン群。定義ジャンプ、参照検索、型エラー確認が可能に。

| # | プラグイン | 概要 |
|---|---|---|
| 09 | **TypeScript LSP** | 型チェックとナビゲーション(公式) |
| 10 | **Python LSP** | Pythonの言語サーバー(公式) |
| 11 | **Rust LSP** | rust-analyzer連携(公式) |
| 12 | **Ruby LSP** | Rubyのコードインテリジェンス(公式) |

---

### 自律コーディング(13〜15)

| # | プラグイン | 概要 |
|---|---|---|
| 13 | **Ralph Loop** | 自律コーディングセッション。Claudeがタスクを1つずつ処理してgitにコミットし、そのまま次へ。放置すれば、きれいなgit履歴とともに完成コードが完成。[link](https://claude.com/plugins/ralph-wiggum) |
| 14 | **Chrome DevTools** | 既存のChromeセッションでネットワークリクエスト、コンソールエラー、ライブページのデバッグ。フロントエンドデバッグで過小評価されているプラグイン。 |
| 15 | **Playwright** | Claudeが実際のブラウザを操作。クリック、フォーム入力、スクリーンショット、UIテスト。テストスクリプトは不要。[link](https://claude.com/plugins/playwright) |

---

### 検索 & データ(16〜20)

| # | プラグイン | 概要 |
|---|---|---|
| 16 | **Firecrawl** | 任意のURLをスクレイプ、サイトクロール、自律リサーチエージェント。WebデータをClaude Codeに入れる定番。[link](https://claude.com/plugins/firecrawl) |
| 17 | **Sourcegraph** | コードベース横断検索。参照のトレース、リファクタリング影響分析、セキュリティスキャン。[link](https://claude.com/plugins/sourcegraph) |
| 18 | **SQL Analytics** | SQLでデータ分析・ビジュアライゼーション(パートナー製) |
| 19 | **Data Engineering** | ウェアハウス探索、パイプライン作成、Airflow連携(パートナー製) |
| 20 | **Amplitude** | トラッキングプラン作成、アナリティクスコード生成。[link](https://claude.com/plugins/amplitude) |

---

### DevOps & インフラ(21〜24)

| # | プラグイン | 概要 |
|---|---|---|
| 21 | **Vercel** | デプロイ、ビルド、ログ、ドメイン管理。[link](https://claude.com/plugins/vercel) |
| 22 | **AWS Deploy** | AWSデプロイ、アーキテクチャ推奨、コスト見積もり |
| 23 | **PagerDuty Risk Score** | コミット前にデプロイリスクをスコア化。[link](https://claude.com/plugins/pagerduty) |
| 24 | **Mintlify** | コードからドキュメント自動生成。[link](https://claude.com/plugins/mintlify) |

---

### インテグレーション(25〜30)

| # | プラグイン | 概要 |
|---|---|---|
| 25 | **GitHub** | PR、Issue、コード検索、CI/CD(定番中の定番)。[link](https://claude.com/plugins/github) |
| 26 | **Slack** | ワークフロー、メッセージ下書き、チャンネル分析。[link](https://claude.com/plugins/slack) |
| 27 | **Sentry** | 本番エラーモニタリング、スタックトレース、修正提案。[link](https://claude.com/plugins/sentry) |
| 28 | **Linear** | Issue管理、スプリント管理。[link](https://claude.com/plugins/linear) |
| 29 | **Supabase** | DB管理、認証、ストレージ。[link](https://claude.com/plugins/supabase) |
| 30 | **Stripe** | 決済、サブスク、請求書、顧客データ。[link](https://claude.com/plugins/stripe) |

---

### ビジネス & ナレッジワーク(31〜36)

Anthropicの `knowledge-work-plugins` マーケットプレイスから。まず追加:

```
/plugin marketplace add anthropics/knowledge-work-plugins
```

| # | プラグイン | 概要 |
|---|---|---|
| 31 | **Brand Voice** | ブランドトーンを全コンテンツで統一 |
| 32 | **Marketing** | SEO監査、コンテンツ戦略、競合分析 |
| 33 | **Sales** | 見込み客リサーチ、メールシーケンス、反論対応 |
| 34 | **Legal** | 契約レビュー、コンプライアンス(初回スクリーニング用。法的アドバイスではない) |
| 35 | **Finance** | 財務分析、予算計画、予測モデル |
| 36 | **Productivity** | 会議要約、タスク管理、メール下書き |

---

### 用途別おすすめの組み合わせ

全部入れる必要はない。自分のやっていることに応じて **3〜5個** が最適。

- **全開発者向け**: Frontend Design + Code Review + Commit Commands + 自分の言語のLSP
- **フルスタック**: Superpowers + Context7 + GitHub + Supabase
- **フロントエンド**: Frontend Design + Chrome DevTools + Playwright + Vercel
- **DevOps**: AWS Deploy + Sentry + PagerDuty + GitHub
- **ビジネス/マーケティング**: Brand Voice + Marketing + Sales + Productivity
- **データ**: SQL Analytics + Data Engineering + Firecrawl

---

### 運用上の注意点

- 各プラグインは**コンテキストトークンを消費**する。多いほどオーバーヘッドが増える。**3〜5個が最適**。
- 使っていないプラグインは無効化:

```
/plugin disable plugin-name
```

---

### 参考リンク

- 全カタログ: [claude.com/plugins](https://claude.com/plugins)
- 公式リポジトリ: [github.com/anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- プラグインドキュメント: [code.claude.com/docs/en/discover-plugins](https://code.claude.com/docs/en/discover-plugins)

---

### まとめ（PART 1）

- **9,000以上のプラグインから36個に厳選**
- 内訳: 公式Anthropic製8個 + コード品質4個 + 自律コーディング3個 + 検索&データ5個 + DevOps 4個 + インテグレーション6個 + ビジネス6個
- 最も人気は **Frontend Design(40万+)** と **Superpowers(29万+)**
- 全部入れる必要はない。用途に応じて **3〜5個**
- 使ってないプラグインは無効化してトークン節約
- コミュニティ製は `/plugin marketplace add` で追加可能

---

**Sources:**
- [元ポスト(@ClaudeCode_love)](https://x.com/ClaudeCode_love/status/2049469282107691216)
- [元記事(@zodchiii)](https://x.com/zodchiii/status/2042529018260656555)

---

# PART 2: スキル 72 選

> **原資料**: `docs/CLAUDE_SKILLS_72_SELECTION.md`

## 【完全保存版】トップ層が使うClaude Skills 72選

> 出典: [@ClaudeCode_UT のポスト](https://x.com/ClaudeCode_UT/status/2049770357419299237)
> 元記事: [@polydao のポスト](https://x.com/polydao/status/2044317956893471081)

---

### はじめに

『海外でバズってるSkillsの記事、全部英語で読みきれない』
『Skillsを入れたいけど、結局どれを入れればいいか分からなくて放置してる』

Claude Codeを使っていて、こんな経験はありませんか？

- 海外で420万人が読んだSkills記事がバズっているのに、英語で読みきれない
- Skills関連の記事をブクマしたけど、どれを入れればいいか分からず放置している
- 周りがAIを使いこなし始めているのに、自分はまだ毎回ゼロから指示している焦り
- 毎回AIに同じ説明をやり直している。前回教えたことが消えている

AI Builder / CEO の Mr. Buzzoni 氏が書いた記事が420万ビュー、1.9万ブックマークの大バズ中。本記事ではその内容を日本のビジネス現場向けに4つのカテゴリへ再構成し、独自の組み合わせパック3つと実務スキル2つを加えた**72選**として整理しています。

---

### Skillsは「一度教えたら永久に覚える仕組み」

普段のAIチャットは、セッションが終わるとすべてリセットされます。先週教えた「報告書のフォーマット」も「プレゼンの好み」も消えている。だから毎回ゼロから同じ説明をやり直すことになります。

Skillsはこの問題を根本から解決する仕組みです。`SKILL.md` というファイルに「仕事のやり方」を定義しておくと、Claude Codeが永久にそのルール通りに動きます。手順、制約、テンプレート、具体例。全部1つのファイルに書いておくだけです。

インストールは1行のコマンドだけ。

```bash
claude install @anthropics/skills/pdf
```

これを実行するだけで、PDFの読み取りや結合、分割がいつでも使えるようになります。

---

### カテゴリ1:「考える」企画と壁打ち

「考える時間」は、ビジネスの中で最も価値が高い時間です。

- **Before**: 企画書を1人で3日かけて書く。壁打ち相手がいない
- **After**: AIと壁打ちして30分で骨子が完成。残りの時間は判断と意思決定に集中

#### 1. Brainstorming (obra/superpowers)

アイデアを投げると、AIが9ステップの構造化プロセスで設計書まで仕上げます。最も重要なルールは「設計書を承認するまで一切コードを書かない」こと。

🔗 https://github.com/obra/superpowers/tree/main/skills/brainstorming

#### 2. Grill Me (mattpocock/skills) ★個人的イチオシ

「これでいいかな」と思った計画をAIに渡すと、考慮漏れを1つずつ質問攻めにしてくれるスキル。決定ツリーの分岐を1つずつ解決していく質問インタビュー形式。

🔗 https://github.com/mattpocock/skills/tree/main/grill-me

#### 3. Write a PRD (mattpocock/skills)

打ち合わせやチャットのやり取りから、企画書を自動で作成するスキル。問題定義、解決策、必要機能、対象外項目まで構造化。

🔗 https://github.com/mattpocock/skills/tree/main/write-a-prd

#### 4. PRD to Plan (obra/superpowers)

企画書から詳細な実行計画を自動生成。タスクを2〜5分単位に分解し、ファイルパスや実行コマンドまで含む計画書を出力。

🔗 https://github.com/obra/superpowers

#### 5. PRD to Issues (mattpocock/skills)

企画書をタスクチケットに自動変換。「垂直スライス」の概念で一気通貫のタスクに分割。

🔗 https://github.com/mattpocock/skills/tree/main/prd-to-issues

#### 6. Design an Interface (mattpocock/skills)

3つ以上の根本的に異なるアプローチで同時に設計案を生成。「最初のアイデアが最良とは限らない」設計哲学。

🔗 https://github.com/mattpocock/skills/tree/main/design-an-interface

#### 7. Domain Name Brainstormer

サービス名やドメイン名のアイデアを大量生成。ブランディングの壁打ち相手として。

🔗 https://github.com/Microck/ordinary-claude-skills/tree/main/skills_all/domain-name-brainstormer

#### 8. Idea Mining / YouTube

YouTubeからコンテンツのアイデアを自動収集。競合チャンネルの人気動画やトレンドを分析。

🔗 https://github.com/AgriciDaniel/claude-youtube

---

### カテゴリ2:「作る」デザインと制作と開発

全72個の中で最もボリュームのあるカテゴリ。デザイン、Web、画像、動画からコード開発まで幅広くカバー。

- **Before**: Webサイトのデザインを外注して2週間待つ
- **After**: AIに言葉で指示して、1日で本番品質のデザインが完成

#### デザイン・ビジュアル系

##### 9. Frontend Design (Anthropic公式)

言葉で伝えるだけで、プロが作ったような画面が出力される。「AIっぽいありきたりなデザインを避ける」原則が明示。

🔗 https://github.com/anthropics/skills/tree/main/skills/frontend-design

##### 10. Canvas Design (Anthropic公式)

「デザイン哲学マニフェスト」を言語化してからPNG/PDFで表現する2段階プロセス。

🔗 https://github.com/anthropics/skills/tree/main/skills/canvas-design

##### 11. Theme Factory (Anthropic公式)

10種類のプリセットテーマまたはカスタム生成。カラーパレットとフォントペアリングを全ページに統一適用。

🔗 https://github.com/anthropics/skills/tree/main/skills/theme-factory

##### 12. Awesome-design

デザインのベストプラクティス集。プロが使う設計パターンやレイアウトの原則を参照。

🔗 https://github.com/VoltAgent/awesome-design-md

##### 13. Image Generator

画像生成プロンプトを最適化し品質を管理。2種類のバリエーション付き。

🔗 https://github.com/kingbootoshi/nano-banana-2-skill

##### 14. Local Image Gen

クラウドを使わずローカル環境で画像生成。機密性の高いプロジェクト向け。

🔗 https://github.com/jezweb/claude-skills/blob/main/plugins/design-assets/skills/ai-image-generator/SKILL.md

##### 15. Image Optimizer [除外: T-009]

画像の圧縮、フォーマット変換、リサイズを自動処理。`design-assets` プラグインの `image-processing` skill で代替可能なため、テンプレ標準同梱からは除外。

##### 16. Brand Guidelines (Anthropic公式)

ブランドカラーやフォントをアーティファクトに自動適用。自社向けに書き換え可能。

🔗 https://github.com/anthropics/skills/tree/main/skills/brand-guidelines

##### 17. Algorithmic Art (Anthropic公式)

p5.jsでインタラクティブなアート作品を生成。パラメータスライダー付きHTMLビューアー。

🔗 https://github.com/anthropics/skills/tree/main/skills/algorithmic-art

#### 開発者向けスキル

##### 18. Web Artifacts Builder (Anthropic公式)

React、TypeScript、TailwindでWebアプリをHTMLアーティファクトとして生成。shadcn/uiとの連携も。

🔗 https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder

##### 19. TDD (mattpocock/skills)

「計画→トレーサー弾→反復→リファクタリング」の4ステップ。Red-Green-Refactorループ。

🔗 https://github.com/mattpocock/skills/tree/main/tdd

##### 20. Code Review (obra/superpowers)

「レビューを受ける側」と「する側」の2つに分かれた構造化レビュー。

🔗 https://github.com/obra/superpowers

##### 21. Systematic Debugging (obra/superpowers)

4フェーズで体系的にバグ解決。「3回修正に失敗したらアーキテクチャを見直す」ルール付き。

🔗 https://github.com/obra/superpowers/tree/main/skills/systematic-debugging

##### 22. Superpowers (obra/superpowers)

20個のエンジニアリングスキル一括導入のメガコレクション。16.6万スター。

🔗 https://github.com/obra/superpowers

##### 23. Improve Codebase Architecture (mattpocock/skills)

ADR(設計判断記録)を参照し、「浅いモジュールを深いモジュールに変換する」設計哲学。

🔗 https://github.com/mattpocock/skills/tree/main/improve-codebase-architecture

##### 24. QA

テスト自動化と品質保証。テストケース設計から実行、分析まで。

🔗 https://github.com/mattpocock/skills/tree/main/qa

##### 25. Triage Issue

バグ報告の分類と優先順位付けを自動化。

🔗 https://github.com/mattpocock/skills/tree/main/triage-issue

##### 26. Auto-Commit Messages

変更内容を分析してコミットメッセージを自動生成。

🔗 https://github.com/anthropics/skills/tree/main/skills/auto-commit

##### 27. Change Log Generator

コミット履歴から変更履歴を自動生成。

🔗 https://github.com/ComposioHQ/awesome-claude-skills/tree/master/changelog-generator

##### 28. Simplification Cascade

複雑なコードを段階的に簡素化。

🔗 https://mcpmarket.com/tools/skills/simplification-cascades-1

##### 29. React Best Practices

Reactのベストプラクティスをコードに自動適用。

🔗 https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices

##### 30. File Search

コードベース内のファイル検索を最適化。

🔗 https://github.com/massgen/massgen

##### 31. Context Optimization

Claude Codeのコンテキスト管理を最適化。

🔗 https://github.com/muratcankoylan/agent-skills-for-context-engineering

##### 32. Migrate to Shoehorn

フレームワーク移行支援。

🔗 https://github.com/mattpocock/skills/tree/main/migrate-to-shoehorn

##### 33. Scaffold Exercises

コード演習問題を自動生成。

🔗 https://github.com/mattpocock/skills/tree/main/scaffold-exercises

##### 34. Request Refactor Plan

リファクタリング計画の策定(現在deprecated、diagnoseやzoom-outに置き換え)。

🔗 https://github.com/mattpocock/skills/tree/main/request-refactor-plan

##### 35. Stripe Integration

Stripe決済機能の実装支援。

🔗 https://github.com/wshobson/agents/tree/main/plugins/payment-processing/skills/stripe-integration

##### 36. Setup Pre-Commit

コミット前チェックの自動設定。

🔗 https://github.com/mattpocock/skills/tree/main/setup-pre-commit

##### 37. Git Guardrails

Gitの安全ルール設定。危険なコマンド防止やブランチ保護。

🔗 https://github.com/mattpocock/skills/tree/main/git-guardrails-claude-code

##### 38. Dependency Auditor

依存パッケージのセキュリティ監査を自動化。

🔗 https://github.com/ComposioHQ/awesome-claude-skills

##### 39. Git Work Trees

複数ブランチの並列作業環境構築を自動化。

🔗 https://skillsmp.com

##### 40. Remotion Best Practices

プログラマブルな動画制作のベストプラクティス。

🔗 https://github.com/remotion-dev/remotion

##### 41. Emotion

CSS-in-JSのスタイリングを効率化。

🔗 https://github.com/wilwaldon/Claude-Code-Video-Toolkit

---

### カテゴリ3:「調べる・書く」リサーチと文書

「調べて書く」はほぼ全てのビジネスパーソンが毎日やっていること。この時間が半分になったら、影響は計り知れません。

- **Before**: リサーチに1日、執筆に1日。合計2日
- **After**: AIがリサーチを整理して、ドラフトまで共同作成。半日で完成

#### 42. Doc Co-Authoring (Anthropic公式)

3段階プロセス: ①情報収集 ②セクションごとのドラフト ③別セッションでの読者テスト。

🔗 https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring

#### 43. Edit Article (mattpocock/skills)

記事全体を「情報の依存関係グラフ」として分析し、最も理解しやすい順序に再構成。1段落最大240文字ルール。

🔗 https://github.com/mattpocock/skills/tree/main/edit-article

#### 44. Content Researcher

テーマを渡すとリサーチ結果を構造化。情報源探索→要点抽出→テーマ別分類。

🔗 https://github.com/ComposioHQ/awesome-claude-skills/blob/master/content-research-writer/SKILL.md

#### 45. Obsidian Vault (mattpocock/skills)

Obsidian連携で知識を蓄積・検索。wikilinks記法とIndex Noteによるフラット構造。

🔗 https://github.com/mattpocock/skills/tree/main/obsidian-vault

#### 46. Claude SEO

SEO最適化の分析と改善提案。タイトル、メタディスクリプション、キーワード配置。

🔗 https://github.com/AgriciDaniel/claude-seo

#### 47. Ubiquitous Language (mattpocock/skills)

チーム内の用語を統一定義。「同じものを違う名前で呼ぶ」問題を解決。

🔗 https://github.com/mattpocock/skills/tree/main/ubiquitous-language

#### 48. API Documentation Generator

コードからAPIドキュメントを自動生成。

🔗 https://github.com/ComposioHQ/awesome-claude-skills

#### 49. Marketing Skills

マーケティング施策の設計と分析支援。

🔗 https://github.com/coreyhaines31/marketingskills

#### 50. Custom YT Search

YouTube動画の高度な検索と分析。

🔗 https://github.com/ZeroPointRepo/youtube-skills/blob/main/README.md

#### 51. Firecrawl

Webサイトからのデータ自動抽出。

🔗 https://github.com/mendableai/firecrawl

---

### カテゴリ4:「回す」業務とドキュメント

毎月、毎週繰り返す「作業」こそ、Skillsの最大の効果が出る場所。

- **Before**: 請求書50枚を手入力で15時間。確認に3時間
- **After**: フォルダに入れて15分で全件処理。計算不整合だけ手動確認

#### 52. PPTX (Anthropic公式)

PowerPointファイルを自動生成。既存PPTXの内容抽出やリメイクも可能。

🔗 https://github.com/anthropics/skills/tree/main/skills/pptx

#### 53. XLSX (Anthropic公式)

Excelデータの整理、グラフ作成、数式自動化。数式再計算で自動検証。

🔗 https://github.com/anthropics/skills/tree/main/skills/xlsx

#### 54. PDF (Anthropic公式)

PDF操作のワンストップ自動化。OCRやパスワード暗号化も対応。

🔗 https://github.com/anthropics/skills/tree/main/skills/pdf

#### 55. DOCX (Anthropic公式)

Word文書の作成と編集を自動化。新規はJSライブラリ、既存修正はXML直接編集。

🔗 https://github.com/anthropics/skills/tree/main/skills/docx

#### 56. Excel MCP Server [除外: T-009]

ExcelをMCPプロトコル経由で操作。`document-skills` プラグインの `xlsx` skill（pandas + openpyxl）で代替可能なため、テンプレ標準同梱からは除外。

#### 57. GWS

Googleスプレッドシート、ドキュメント、スライドと連携。

🔗 https://github.com/googleworkspace/cli

#### 58. NotebookLM Integration

GoogleのNotebookLMと連携してリサーチを強化。

🔗 https://github.com/PleasePrompto/notebooklm-skill

#### 59. Lead Research Assistant

見込み客の企業調査を自動化。事業内容、最新ニュース、競合状況をレポート化。

🔗 https://github.com/ComposioHQ/awesome-claude-skills/blob/master/lead-research-assistant/SKILL.md

#### 60. GitHub Triage

GitHub Issueの自動分類と優先順位付け。

🔗 https://github.com/mattpocock/skills/tree/main/github-triage

#### 61. Stochastic Multi-Agent Consensus

複数のAIモデルで合意形成プロセスを実行し最適解を導く。

🔗 https://skillsmp.com

#### 62. Model-chat / Debate

AIモデル同士を対話させて多角的に分析。

🔗 https://skillsmp.com

#### 63. Playwright CLI

Webブラウザの自動操作。テスト自動化やスクレイピング。

🔗 https://github.com/microsoft/playwright

---

### Skillsの入手先(4つの場所)

#### Anthropic公式
🔗 https://github.com/anthropics/skills (12.1万スター)

#### 個人開発者
- Matt Pocock氏: https://github.com/mattpocock/skills (1.65万スター)
- obra/superpowers: https://github.com/obra/superpowers (16.6万スター)

#### 企業参入
Microsoft、Sentry、Cloudflare、Trail of Bitsなど大手テック企業も参入。

#### マーケットプレイス
SkillsMP: https://skillsmp.com (6.6万以上のSkillsが公開中)

> ⚠️ **セキュリティ注意**: Skillsは簡単に配布できるため、非公式のものはセキュリティリスクを考慮。導入前の確認を習慣化する。

---

### 独自スキル&組み合わせパック(オリジナル5選)

#### 64. 企画壁打ちパック

アイデアを投げるだけで、壁打ち→検証→企画書まで一気に完成させるワークフロー。

```markdown
---
name: planning-sprint
description: アイデアを企画書に変換する一気通貫ワークフロー。壁打ち、検証、企画書作成の3ステップを順に実行する。企画や提案の立案時に使用。
---
# 企画壁打ちパック
アイデアを投げると、壁打ち→検証→企画書の3ステップで完成させます。

## 前提スキル
- Brainstorming (@obra/superpowers)
- Grill Me (@mattpocock/skills)
- to-prd (@mattpocock/skills)

## ワークフロー
1. Brainstormingを起動し、アイデアを構造化する。設計書が承認されるまで次に進まない
2. Grill Meで設計書を検証する。考慮漏れを1つずつ質問で潰す
3. to-prdで検証済みの設計を企画書に変換する

## ポイント
- 3つのスキルを順番に呼び出すだけ
- 途中で方向転換したらステップ1に戻る
- 企画の品質が「個人の思考力」ではなく「プロセスの力」で上がる
```

#### 65. ドキュメント一括処理パック

PDF、Word、Excelが混在するフォルダを渡すだけで、中身を自動で読み取って整理。

```markdown
---
name: document-processor
description: PDF、Word、Excelの混在ファイルを一括で読み取り・整理・統合する。書類整理やデータ抽出の場面で使用。
---
# ドキュメント一括処理パック
複数形式のファイルをフォルダに入れるだけで、中身を自動処理します。

## 前提スキル
- PDF (@anthropics/skills)
- DOCX (@anthropics/skills)
- XLSX (@anthropics/skills)

## ワークフロー
1. 処理したいファイルを1つのフォルダにまとめる
2. 「このフォルダの書類を全部読み取って整理して」と指示する
3. AIがファイル形式を自動判定し、それぞれに適した方法で処理する

## 処理方法
- PDF → テキスト抽出。画像PDFはOCR処理
- Word → 本文と書式の読み取り
- Excel → データ抽出。数式は再計算して検証
```

#### 66. リサーチ→執筆パック

テーマを投げるだけで、調査、構成、執筆、校正まで一気に完成。

```markdown
---
name: research-to-writing
description: テーマ設定から完成原稿までを一気通貫で処理する。情報収集、構造化ドラフト、構造校正の3ステップ。企画書、提案書、記事の作成に使用。
---
# リサーチ→執筆パック
テーマを投げるだけで、調査・執筆・校正まで一気に完成させます。

## 前提スキル
- Doc Co-Authoring (@anthropics/skills)
- Edit Article (@mattpocock/skills)

## ワークフロー
1. テーマと目的を伝える。AIが調べるべきことを整理する
2. Doc Co-Authoringでセクション構成を提案し、ドラフトを共同作成する。最後に読者テストで分かりにくい箇所を自動指摘
3. Edit Articleでドラフト全体の情報依存関係を分析し、最も理解しやすい順序に再構成する
```

#### 67. Meeting Automation (/mtg-notes)

会議の録画やテキストから議事録、TODO、次回アジェンダを15分で完成。

- **Before**: 議事録作成に1件30〜40分。週5件で週3時間。TODO漏れが月2回
- **After**: 1件15分で完了。週1.25時間。TODO自動抽出で漏れゼロ

tl;dvやCircleback MCPと連携可能。team.mdにメンバー情報を入れておくと話者推定やTODO担当割り当ての精度が上がる。

#### 68. Invoice Reader (/read-invoices)

請求書PDFをフォルダに入れるだけで、構造化されたCSVと計算検証レポートが15分で完成。

- **Before**: 月50枚で15〜20時間の手入力。転記ミスが月2〜5件
- **After**: 15分で全件完了。計算検証で不整合を自動検出

設計のポイント:
- 計算検証はAIではなく自動検証プログラムで厳密に実行
- テキストPDFはClaude単体、画像PDFはGeminiのOCRを使う2段構え
- 処理済みは `confirmed` と `flagged` に自動振り分け

---

### 導入はメタスキルから(3ステップ)

#### Step 1: メタスキルを入れる

「Skillsを探す・作る」能力そのものを手に入れる。

##### 69. Skill Creator (Anthropic公式)
スキルの新規作成・改善・パフォーマンス評価ループを定義。トリガー説明文の最適化機能付き。
🔗 https://github.com/anthropics/skills/tree/main/skills/skill-creator

##### 70. Write a Skill (Matt Pocock版)
スキルの構造、descriptionの書き方、ファイル分割の判断基準を整理。「descriptionはAIがスキルを選ぶ唯一の手がかり」。
🔗 https://github.com/mattpocock/skills

##### 71. Find Skills
キーワードやユースケースからマッチするスキルを発見。
🔗 https://skillsmp.com

##### 72. 自分専用カスタムスキル
最終的には自分の業務に合わせて作る。SKILL.mdは自由に編集可能。

#### Step 2: 仕事で最も時間を使う作業に合うスキルを1つ選ぶ

| タイプ | おすすめ |
|---|---|
| 企画や計画が多い人 | Brainstorming + Grill Me (または企画壁打ちパック) |
| 資料作成が多い人 | PPTX + Theme Factory |
| 文書作成が多い人 | Doc Co-Authoring (またはリサーチ→執筆パック) |
| データ処理が多い人 | XLSX |
| 書類整理が多い人 | ドキュメント一括処理パック |

#### Step 3: 使って、直して、育てる

Skillsは入れて終わりではない。SKILL.mdの中身は自由に編集できる。自分の業務に合わせてルールを追加したり、テンプレートを変えたりして育てていく。使い込むほど、あなたの仕事に最適化されていく。

---

### まとめ（PART 2）

- Skillsは「一度教えたら永久に覚える仕組み」。毎回ゼロから説明する時代は終わった
- 元記事の67個を日本のビジネス現場向けに再構成し、独自5つを加えた72選
- Anthropic公式からコミュニティまで、エコシステムは1,116スキル規模に成長中
- 注目スキル10個はSKILL.mdの中身を直接読んだファクトベースの解説
- 組み合わせパック3個 (企画壁打ち、ドキュメント一括処理、リサーチ→執筆) はオリジナル
- 独自スキル2個 (会議記録と請求書処理) を無料公開
- Skillsの本質は「作業をAIに定義として渡す」仕組み。差別化の源泉は判断と思想にある

---

### Sources

- [元X投稿(@ClaudeCode_UT)](https://x.com/ClaudeCode_UT/status/2049770357419299237)
- [参照元X投稿(@polydao)](https://x.com/polydao/status/2044317956893471081)

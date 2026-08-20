---
title: STANDALONE_SKILLS
version: 2026-05-18
sources:
  - docs/CATALOG.md
  - .claude/settings.json (enabledPlugins)
verification:
  - 2026-05-18 各リポジトリの .claude-plugin/{marketplace,plugin}.json を curl で直接取得して裏取り
  - 2026-05-18 各リポジトリの README.md の「## Installation」セクションを実検証し、author が推奨する正式 install 方法を確認
---

# Standalone Skills 推奨カタログ

72 スキルを **プラグインで導入可能なもの / standalone skill として import するもの / MCP・CLI 扱い / 除外** の 4 区分に分類した導入ガイドです。

このテンプレートはプラグイン主軸で運用するため、**同じスキルがプラグインとして配布されていれば必ずプラグイン側を優先**します。`/plugin marketplace add` + `/plugin install` の方が個別 SKILL.md の手動コピーより:

- 更新追従が楽（マーケットプレイス側が改善されれば自動取り込み）
- ライセンスや配布元の信頼性が manifest 化される
- `enabledPlugins` 配列で一元管理でき、不要時は `/plugin disable` で即停止できる

2026-05-18 時点で `.claude-plugin/marketplace.json` または `.claude-plugin/plugin.json` の有無を全リポジトリで実検証しました（curl による HTTP 200/404 確認 + manifest 本文取得）。

---

## 分類サマリ

| 区分 | 判定基準 | 件数 |
|---|---|---|
| A. **Standalone 推奨** | プラグイン版が存在しない、または ComposioHQ / skillsmp のように "open SKILL.md" としてのみ配布 | 25 |
| B. **プラグインで導入** | claude-plugins-official または個別マーケットプレイスにプラグイン版が存在 | 36 |
| C. **独自パック（除外）** | 64〜68（command 版アーカイブ済 + プラグイン代替済） | 5 |
| D. **deprecated（除外）** | 34 Request Refactor Plan（公式 deprecated） | 1 |
| E. **MCP サーバー / CLI（特殊導入）** | skill ではなく MCP / CLI として配布されている | 5 |
| **合計** | — | **72** |

---

## 区分 B. プラグインで導入できるスキル（推奨、36 件 = B-1: 13 + B-2: 10 + B-3: 8 + B-4: 5）

### B-1. 既に enabled なプラグインでカバー済み（13 件）

何もしなくても OK。スキルが必要な場面で対応するプラグインが自動発火します。

| # | スキル | 内包プラグイン | 状態 |
|---|---|---|---|
| 1 | Brainstorming | `superpowers:brainstorming` | enabled |
| 4 | PRD to Plan | `superpowers:writing-plans` | enabled |
| 9 | Frontend Design | `frontend-design` | enabled |
| 20 | Code Review | `code-review` | enabled |
| 21 | Systematic Debugging | `superpowers:systematic-debugging` | enabled |
| 22 | Superpowers バンドル本体 | `superpowers` | enabled |
| 26 | Auto-Commit Messages | `commit-commands:commit` | enabled |
| 29 | React Best Practices | `vercel:react-best-practices` | available |
| 35 | Stripe Integration | `stripe:stripe-best-practices` | enabled |
| 39 | Git Work Trees | `superpowers:using-git-worktrees` | enabled |
| 51 | Firecrawl | `firecrawl` | enabled |
| 63 | Playwright CLI | `playwright` | enabled |
| 69 | Skill Creator | `skill-creator` | enabled |

### B-2. anthropics/skills マーケットプレイス追加で 10 件カバー

`/plugin marketplace add anthropics/skills` で **`anthropic-agent-skills`** マーケットプレイスを追加すると、以下 2 プラグインで 10 スキルが一括導入できます。

```bash
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

| # | スキル | 内包プラグイン |
|---|---|---|
| 52 | PPTX | `document-skills` |
| 53 | XLSX | `document-skills` |
| 54 | PDF | `document-skills` |
| 55 | DOCX | `document-skills` |
| 10 | Canvas Design | `example-skills` |
| 11 | Theme Factory | `example-skills` |
| 16 | Brand Guidelines | `example-skills` |
| 17 | Algorithmic Art | `example-skills` |
| 18 | Web Artifacts Builder | `example-skills` |
| 42 | Doc Co-Authoring | `example-skills` |

注意:

- `example-skills` は内部に `frontend-design` と `skill-creator` も含むため、既に enabled の `frontend-design@claude-plugins-official` / `skill-creator@claude-plugins-official` と **同名スキルが重複ロード** されます。重複が問題になる場合は `example-skills` を入れずに該当 6 スキルだけを手動 import（区分 A の方式）に切り替えるか、claude-plugins-official 側の 2 プラグインを `/plugin disable` する選択肢があります。
- `example-skills` には追加で `internal-comms` / `mcp-builder` / `slack-gif-creator` / `webapp-testing` も付属します（72sen には未掲載のボーナススキル）。
- 同マーケットプレイスには `claude-api` プラグインもあり（Claude API/SDK 開発者向け）、必要なら追加可。

### B-3. mattpocock/skills（8 件、npx 推奨 / plugin 代替）

**author の公式 README は `npx skills` を primary install と明記している** ため厳密には plugin install ではないが、`.claude-plugin/plugin.json`（単一プラグイン定義、`name: mattpocock-skills`、14 スキル束）も存在するため、Claude Code プラグインとしてもインストール可能。本テンプレのプラグイン主軸方針なら後者を採用。

```bash
# 公式推奨（vercel-labs/skills の cross-platform CLI 経由）
npx skills@latest add mattpocock/skills

# 代替: Claude Code プラグイン経由（plugin.json 単独）
/plugin marketplace add mattpocock/skills
/plugin install mattpocock-skills@mattpocock-skills
```

| # | スキル | プラグイン内 path |
|---|---|---|
| 2 | Grill Me | `skills/productivity/grill-me` |
| 3 | Write a PRD | `skills/engineering/to-prd` |
| 5 | PRD to Issues | `skills/engineering/to-issues` |
| 19 | TDD | `skills/engineering/tdd` |
| 23 | Improve Codebase Architecture | `skills/engineering/improve-codebase-architecture` |
| 25 | Triage Issue | `skills/engineering/triage`（state machine 型 issue tracker workflow） |
| 60 | GitHub Triage | `skills/engineering/triage`（25 と統合済み。SKILL.md の description が GitHub Issue triage を明示） |
| 70 | Write a Skill | `skills/productivity/write-a-skill` |

注意:

- ボーナススキルとして `diagnose` / `zoom-out` / `grill-with-docs` / `prototype` / `caveman` / `handoff` / `setup-matt-pocock-skills` も同時導入。とくに **`diagnose` と `zoom-out` は 34 Request Refactor Plan（deprecated）の公式置換先**。
- npx 経由は files が `.agents/skills/` に置かれ `.claude/skills/` に symlink される（cross-platform 構造）。`/plugin install` 経由は Claude Code 管理下に入る。CATALOG.md の `kind` 体系と相性が良いのは後者。
- 72sen で「mattpocock 由来」と紹介されている残り 9 スキル（6, 24, 32, 33, 36, 37, 43, 45, 47）は **author 自身が `deprecated/` / `misc/` / `personal/` 以下に振り分けており、現行プラグインには含まれていない**。これらの正確な位置と扱いは区分 A の各表を参照。

### B-4. その他コミュニティマーケットプレイス追加（5 件）

各リポジトリを個別に marketplace add する必要があります。スキル単位で必要性を判断してください。

| # | スキル | コマンド |
|---|---|---|
| 46 | Claude SEO | `/plugin marketplace add AgriciDaniel/claude-seo` → `/plugin install claude-seo@agricidaniel-seo` |
| 13 | Image Generator (nano-banana) | `/plugin marketplace add kingbootoshi/nano-banana-2-skill` → `/plugin install nano-banana@nano-banana-2-skill-marketplace`（※ README primary は `Clone the repo` だが marketplace.json が存在するため plugin install も可能） |
| 14 | Local Image Gen | `/plugin marketplace add jezweb/claude-skills` → `/plugin install design-assets@jezweb-skills` |
| 31 | Context Optimization | `/plugin marketplace add muratcankoylan/Agent-Skills-for-Context-Engineering` → `/plugin install context-engineering@context-engineering-marketplace`（※ リポジトリ名は大文字混在。公式 README の構文に合わせる） |
| 49 | Marketing Skills | `/plugin marketplace add coreyhaines31/marketingskills` → `/plugin install marketing-skills@marketingskills`（※ author 推奨は `npx skills add coreyhaines31/marketingskills`、plugin install は Option 2 として記載） |

注意:

- `jezweb/claude-skills` は **7 プラグインを内包する大型マーケットプレイス**（cloudflare / web-design / frontend / design-assets / integrations / dev-tools / writing）。14 Local Image Gen が欲しいだけなら `design-assets` のみ install すれば十分です。
- `muratcankoylan` の `context-engineering` プラグインは 14 スキル束（context-fundamentals / context-compression / context-optimization / multi-agent-patterns / memory-systems 等）を含み、31 Context Optimization 単体を超える広範な内容です。
- `coreyhaines31` の `marketing-skills` プラグインは **40 スキル束**。`marketing@knowledge-work-plugins` プラグインと内容がかぶる可能性があるため、両方入れる前に重複検討を推奨。
- 旧 doc で B-4 にあった **8 Idea Mining / YouTube (AgriciDaniel/claude-youtube)** は `marketplace.json` が存在せず、公式 README が `git clone` + `cp` を指示しているため **区分 A-2（research）へ移動**しました。

---

## 区分 A. Standalone skill として import 推奨（25 件）

プラグイン版が存在しない（または npx / SKILL.md ベタ配布のみ）スキル。`.claude/skills/<category>/<name>/` に手動配置し、CATALOG.md に `kind: skill` で登録します。

凡例（公開元）: `[コミュニティ]` GitHub 個人/組織リポジトリ、`[マーケット]` skillsmp.com / mcpmarket.com、`[カタログ]` ComposioHQ awesome-claude-skills（marketplace ではなくキュレーション集）

### A-1. meta（2 件）

| # | スキル | 公開元 | 概要 | 推奨度 |
|---|---|---|---|---|
| 71 | [Find Skills](https://skillsmp.com) | `[マーケット]` skillsmp | スキル探索 UI。クロスプラットフォーム SKILL.md 形式 | ★★★ |
| 72 | [Awesome Claude Skills](https://github.com/ComposioHQ/awesome-claude-skills) | `[カタログ]` ComposioHQ | コミュニティ全体スキルのキュレーション集 | ★★ |

### A-2. research（8 件）

| # | スキル | 公開元 | 概要 | 推奨度 |
|---|---|---|---|---|
| 7 | [Domain Name Brainstormer](https://github.com/Microck/ordinary-claude-skills/tree/main/skills_all/domain-name-brainstormer) | `[コミュニティ]` Microck | サービス名・ドメイン名のアイデア生成 | ★ |
| 8 | [Idea Mining / YouTube](https://github.com/AgriciDaniel/claude-youtube) | `[コミュニティ]` AgriciDaniel | YouTube からコンテンツアイデアを自動収集（※ marketplace.json なし。`git clone` + `cp ~/.claude/skills/claude-youtube` の標準コピー方式） | ★ |
| 44 | [Content Researcher](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/content-research-writer/SKILL.md) | `[カタログ]` ComposioHQ | テーマからリサーチ結果を構造化整理 | ★★ |
| 50 | [Custom YT Search](https://github.com/ZeroPointRepo/youtube-skills) | `[コミュニティ]` ZeroPointRepo | npx skills CLI 経由（Claude 専用プラグインなし） | ★ |
| 58 | [NotebookLM Integration](https://github.com/PleasePrompto/notebooklm-skill) | `[コミュニティ]` PleasePrompto | Google NotebookLM 連携、ローカル clone のみ | ★ |
| 59 | [Lead Research Assistant](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/lead-research-assistant/SKILL.md) | `[カタログ]` ComposioHQ | 企業名から事業内容・競合を自動レポート化 | ★ |
| 61 | [Stochastic Multi-Agent Consensus](https://skillsmp.com) | `[マーケット]` skillsmp | 複数 AI モデルの合意形成、open SKILL.md | ★ |
| 62 | [Model-chat / Debate](https://skillsmp.com) | `[マーケット]` skillsmp | AI モデル同士の対話分析、open SKILL.md | ★ |

### A-3. dev（10 件）

mattpocock の現行リポジトリでの正確な位置を確認済み（2026-05-18 検証）。author が `deprecated/` に置いている skills は **積極的なメンテナンスを期待しないこと**、`misc/` は「保管はしているが mattpocock-skills プラグインには bundle されていない」状態、`personal/` は **author 個人用途**である点に留意。

| # | スキル | 公開元 | 概要 | 推奨度 |
|---|---|---|---|---|
| 24 | [QA](https://github.com/mattpocock/skills/tree/main/skills/deprecated/qa) | `[コミュニティ]` mattpocock | テストケース設計・実行・結果分析（※ `skills/deprecated/qa/` 配置。author 公式に deprecated） | ★★ |
| 27 | [Change Log Generator](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/changelog-generator) | `[カタログ]` ComposioHQ | コミット履歴から変更履歴自動生成 | ★★ |
| 30 | [File Search](https://github.com/massgen/massgen) | `[コミュニティ]` massgen | コードベース内ファイル検索、npx 経由 | ★ |
| 32 | [Migrate to Shoehorn](https://github.com/mattpocock/skills/tree/main/skills/misc/migrate-to-shoehorn) | `[コミュニティ]` mattpocock | フレームワーク移行支援（※ `skills/misc/` 配置。プラグインから外れているが残存） | ★ |
| 33 | [Scaffold Exercises](https://github.com/mattpocock/skills/tree/main/skills/misc/scaffold-exercises) | `[コミュニティ]` mattpocock | コード演習問題の自動生成（※ `skills/misc/` 配置） | ★ |
| 36 | [Setup Pre-Commit](https://github.com/mattpocock/skills/tree/main/skills/misc/setup-pre-commit) | `[コミュニティ]` mattpocock | コミット前チェック自動設定（※ `skills/misc/` 配置） | ★★ |
| 37 | [Git Guardrails](https://github.com/mattpocock/skills/tree/main/skills/misc/git-guardrails-claude-code) | `[コミュニティ]` mattpocock | 危険コマンド防止・ブランチ保護（※ `skills/misc/` 配置） | ★★ |
| 38 | [Dependency Auditor](https://github.com/ComposioHQ/awesome-claude-skills) | `[カタログ]` ComposioHQ | 依存パッケージのセキュリティ監査（※ `security-guidance` プラグインと一部重複） | ★★ |
| 41 | [Emotion](https://github.com/wilwaldon/Claude-Code-Video-Toolkit) | `[コミュニティ]` wilwaldon | CSS-in-JS スタイリング（※ skill というよりドキュメント集） | ★ |
| 48 | [API Documentation Generator](https://github.com/ComposioHQ/awesome-claude-skills) | `[カタログ]` ComposioHQ | コードからエンドポイント仕様書を自動生成 | ★★ |

### A-4. write（5 件）

| # | スキル | 公開元 | 概要 | 推奨度 |
|---|---|---|---|---|
| 6 | [Design an Interface](https://github.com/mattpocock/skills/tree/main/skills/deprecated/design-an-interface) | `[コミュニティ]` mattpocock | 画面・システム設計を 3 つ以上の異なるアプローチで生成（※ `skills/deprecated/` 配置。author 公式に deprecated） | ★★ |
| 12 | [Awesome-design](https://github.com/VoltAgent/awesome-design-md) | `[コミュニティ]` VoltAgent | プロ設計パターン・レイアウト原則集（※ SKILL.md ではなくデザイン参考資料集） | ★ |
| 43 | [Edit Article](https://github.com/mattpocock/skills/tree/main/skills/personal/edit-article) | `[コミュニティ]` mattpocock | 文章の情報依存関係を分析して再構成（※ `skills/personal/` 配置。author 個人用途のため流用は要内容確認） | ★★★ |
| 45 | [Obsidian Vault](https://github.com/mattpocock/skills/tree/main/skills/personal/obsidian-vault) | `[コミュニティ]` mattpocock | Obsidian 連携、wikilinks + Index Note 構造（※ `skills/personal/` 配置、Obsidian ユーザのみ） | ★ |
| 47 | [Ubiquitous Language](https://github.com/mattpocock/skills/tree/main/skills/deprecated/ubiquitous-language) | `[コミュニティ]` mattpocock | チーム用語の統一定義（※ `skills/deprecated/` 配置。author 公式に deprecated、DDD 採用時のみ） | ★ |

### A-5. project（0 件）

該当なし。当初 60 GitHub Triage を A-5 に置いていましたが、自己検証の結果 `engineering/triage` スキル（mattpocock-skills プラグインに含まれる）の SKILL.md description が「issue tracker workflow（GitHub / Linear / local files）」を明示しており、25 Triage Issue と 60 GitHub Triage の両方を統合的にカバーしていることが分かったため **B-3 に移動**しました。

---

## 区分 E. MCP サーバー / CLI として導入（3 件）

skill ではなく MCP / CLI 形式で配布されているため、`/plugin install` ではなく `claude mcp add` または CLI install で導入します。CATALOG.md には `kind: plugin` の standalone MCP として登録（`install:` に `claude mcp add ...` を記載）。

> 注: 旧 #15 Image Optimizer / #56 Excel MCP Server は T-009 で除外（design-assets の image-processing skill / document-skills の xlsx skill で機能カバー済み）。

| # | スキル | 形態 | 導入 |
|---|---|---|---|
| 28 | Simplification Cascade | `[マーケット]` mcpmarket MCP | 詳細は mcpmarket ページ参照 |
| 40 | Remotion Best Practices | `[コミュニティ]` Remotion 製品リポ | skill ではなく Remotion 本体のドキュメント。Remotion を使う際に context として参照 |
| 57 | GWS | `[コミュニティ]` googleworkspace/cli | Google Workspace CLI。subagent / shell wrapper 経由で呼ぶ |

---

## 区分 C / D. 除外スキル

### C. 独自パック（5 件）

`docs/claude-skills-72sen.md` 64〜68 はテンプレ作者の独自バンドル。CLAUDE.md に記載のとおり command 版が代替プラグインに置換されアーカイブ済（`.claude/commands/_archived/`）。standalone skill としても再導入しません。

| # | スキル | 代替先 |
|---|---|---|
| 64 | 企画壁打ちパック | `superpowers:brainstorming` + `feature-dev` |
| 65 | ドキュメント一括処理パック | `document-skills@anthropic-agent-skills`（区分 B-2） |
| 66 | リサーチ→執筆パック | `example-skills:doc-coauthoring` + Edit Article（区分 A-4） |
| 67 | Meeting Automation | `productivity` プラグイン |
| 68 | Invoice Reader | `finance` プラグイン |

### D. deprecated（1 件）

| # | スキル | 置換先 |
|---|---|---|
| 34 | Request Refactor Plan | `mattpocock-skills` プラグインの `diagnose` / `zoom-out`（区分 B-3 のボーナススキル） |

---

## 導入ワークフロー

### プラグインの場合（区分 B-2 / B-3 / B-4）

```bash
# 1. マーケットプレイスを追加
/plugin marketplace add <owner>/<repo>

# 2. 必要なプラグインを install
/plugin install <plugin-name>@<marketplace-name>

# 3. 設定確認
cat .claude/settings.json | grep enabledPlugins
```

### standalone skill の場合（区分 A）

```bash
# 1. リポジトリを /tmp にクローン
gh repo clone <owner>/<repo> /tmp/<repo-name>

# 2. SKILL.md を .claude/skills/<category>/<name>/ に配置
mkdir -p .claude/skills/research/grill-me
cp /tmp/<repo-name>/<path>/SKILL.md .claude/skills/research/grill-me/SKILL.md

# 3. CATALOG.md に kind: skill エントリを追加（手編集）

# 4. HTML 再生成
/catalog-sync
```

### MCP / CLI の場合（区分 E）

```bash
# MCP
claude mcp add <name> -- <command>

# CLI（subagent 経由のラッパー想定）
.claude/agents/<name>.md に shell ラッパーを記述
```

非公式 skill は SKILL.md 本文の目視確認後に配置を推奨（72sen でも明記）。本テンプレートは公開再配布対象としていません（私用テンプレ前提、T-010 で再配布ノート廃止）。

---

## 所感

- **区分 B の発見が決定的**: 当初は 53 件を standalone 推奨と見積もっていましたが、実検証で 23 件がプラグイン化されていることが判明し、最終 standalone 推奨は 25 件まで縮小しました。anthropics/skills と mattpocock/skills がそれぞれ正式に marketplace.json / plugin.json を持つことの確認が大きな成果。
- **anthropic-agent-skills は実質必須**: PDF / XLSX / PPTX / DOCX / Doc Co-Authoring など汎用性の高い★★★スキルが 10 件まとめて入るため、テンプレ初期化直後に `/plugin marketplace add anthropics/skills` を実行し `document-skills` と `example-skills` の 2 プラグインを install する流れを推奨。
- **mattpocock-skills は付加価値高**: 1 プラグインで 14 スキル + 34 の deprecated 置換 (`diagnose` / `zoom-out`) も同時入手できます。72sen で紹介された残り 10 スキルは現行プラグインから外れているため、それらが本当に必要なら個別 import を検討。
- **standalone 推奨 25 件のうち真に汎用なのは少数**: 71 Find Skills / 27 Change Log Generator / 38 Dependency Auditor / 43 Edit Article / 48 API Documentation Generator 程度。残りはニッチ用途。
- **マーケットプレイスが乱立気味**: jezweb / muratcankoylan / coreyhaines31 など大きめのプラグインバンドルは、入れると芋づる式に大量のスキルが入ります。コンテキストトークン消費を抑える原則（3〜5 プラグイン同時）に従い、本当に常用するものだけに絞ることを推奨。
- **重複留意**: `example-skills` ⇄ `frontend-design` / `skill-creator`、`marketing-skills` ⇄ `marketing@knowledge-work-plugins`、`context-engineering` ⇄ `superpowers:context` 等で同名・類似スキルが重複ロードされ得ます。`/plugin disable` で片方を停止する運用が前提。

### おすすめ導入順（テンプレ初期化直後）

```bash
# Step 1: Anthropic 公式（最優先）
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills

# Step 2: Matt Pocock の汎用開発スキル
/plugin marketplace add mattpocock/skills
/plugin install mattpocock-skills@mattpocock-skills

# Step 3: meta（必須）— Find Skills は standalone のみ
gh repo clone <skillsmp の Find Skills 配布元>
# .claude/skills/meta/find-skills/SKILL.md に配置

# Step 4 以降は用途プロファイル次第（個別判断）
```

---

## 関連ドキュメント

- [CATALOG.md](CATALOG.md) — プラグイン / スキル / subagent / MCP 統合カタログ（source of truth）
- [PLUGIN_INSTALL_GUIDE.md](PLUGIN_INSTALL_GUIDE.md) — プラグイン導入・無効化の運用ガイド

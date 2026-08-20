---
title: CATALOG
version: 2026-05-16
generated_html: CATALOG.html
sources:
  - .claude/settings.json (enabledPlugins)
  - .claude/profiles/*.md
kinds:
  - plugin
  - skill
  - subagent
  - command
---

# 統合カタログ（プラグイン・スキル・subagent・コマンド）

このカタログはプロジェクトに導入される **プラグイン・スキル・subagent・コマンドなどすべての拡張資産** の source of truth です。各エントリは `- kind:` フィールドで種類を判別します（既定: `plugin`）。

> **MCP サーバーについて**: 単独 MCP サーバー（GitHub レポ配布、`claude mcp add` で導入するもの）も `kind: plugin` として扱います。`install:` フィールドのコマンドが marketplace plugin (`/plugin install`) か standalone MCP (`claude mcp add`) かを示します。

**フィルタ可能な UI 版**: [CATALOG.html](CATALOG.html)

**運用上の注意**: 各プラグインはコンテキストトークンを消費します。Anthropic 公式ガイドラインは **3〜5 個同時利用が最適**としており、テンプレート既定では `enabledPlugins` は **空**（T-007 でリセット済み）。`/init-project <profile>` で 5〜11 個の curated set が自動有効化されます。個人別常用プラグインは `.claude/settings.local.json` で補完してください。本カタログの `[enabled]` 印は `.claude/settings.json` の `enabledPlugins` から自動反映されます。

このファイルは **source of truth**。編集後は `/catalog-sync` か `bash .claude/scripts/sync-catalogs.sh` で HTML を再生成してください（hooks 自動同期も走るが取りこぼしの可能性あり、本カタログ末尾「自動同期の限界」を参照）。

---

## kind 体系（4 種類の分類基準）

`kind` は **インストール手段と filesystem 配置場所の組み合わせ**を表します。MCP サーバーは plugin 内包と standalone の両方を `kind: plugin` で扱い、`install:` の中身で区別します。

| kind | 導入コマンド | 配置先 / 管理場所 | 主なソース | 例 |
|---|---|---|---|---|
| **plugin** | `/plugin install <name>@<marketplace>` または `claude mcp add <name> -- <cmd>` | marketplace 管理（外部）または `~/.claude.json` の `mcpServers` | `claude-plugins-official` 等のマーケット、または GitHub repo（単独 MCP） | `github`, `slack`, `firecrawl`, `context7`, `coplay-unity-mcp` |
| **skill** | `gh repo clone` → ファイルコピー | `.claude/skills/<category>/<name>/SKILL.md` | GitHub repo（`anthropics/skills` 等） | `pdf`, `grill-me`, `domain-name-brainstormer` |
| **subagent** | ファイルを置く | `.claude/agents/<name>.md` | 手書き or GitHub | `code-reviewer`, `debugger` |
| **command** | ファイルを置く | `.claude/commands/<name>.md` | 手書き or GitHub | `catalog-sync` |

### plugin の中の 2 つの導入経路

`kind: plugin` は **マーケットプレイス配布**と **standalone MCP サーバー** の両方を包含します:

| 導入経路 | install フィールド例 | marketplace フィールド | 該当エントリ例 |
|---|---|---|---|
| marketplace 経由 | `/plugin install github@claude-plugins-official` | `claude-plugins-official` 等 | github / slack / firecrawl / context7 / pinecone（45 件中の大半） |
| standalone MCP | `claude mcp add unityMCP -- uvx --from ...` | `external (GitHub)` | coplay-unity-mcp / ivanmurzak-unity-mcp / anklebreaker-unity-mcp |

UI 上はどちらも plugin バッジで表示され、copy ボタンが押下されたときに **install フィールドの正しいコマンド**がクリップボードへコピーされます。

### plugin に内包される MCP について

github / slack / sentry / linear / firecrawl / context7 / playwright / chrome-devtools / sourcegraph / notion / pinecone 等の多くは **内部実装が MCP プロトコル**ですが、Anthropic がこれらを Claude Code プラグインとして marketplace パッケージングしているため、ユーザの導入手順は `/plugin install` で完結します。kind は導入手順を反映するため、これらはすべて `kind: plugin` です。

### なぜ機能基準（"MCP server か否か"）ではなく配布基準にしたか

1. **install コマンドが kind から自明** — `/plugin install` か `cp` かは kind から判別、`claude mcp add` か `/plugin install` かは plugin 内の `install:` フィールドから判別
2. **filesystem の管理場所が明確** — 各 kind は固定の配置先を持つ。`.claude/skills/` を見れば skill 一覧、`.claude/agents/` を見れば subagent 一覧、`.claude/commands/` を見れば command 一覧
3. **discovery が単純** — `/catalog-sync` の自動同期は kind ごとに決められたディレクトリをスキャンするだけ
4. **plugin は composition** — 1 つのプラグインが内部に skill / agent / hook / MCP server を複数持つことがある（superpowers が好例）。これを「kind」では表現できない

---

## マーケットプレイス・取得元

導入手順は kind により 3 方式に分かれます:

- **plugin**: `/plugin marketplace add <owner>/<repo>` → `/plugin install <name>@<marketplace>`
- **skill**: `gh repo clone <owner>/<repo> /tmp/<name>` → 必要な SKILL.md を `.claude/skills/<category>/<name>/` にコピー
- **mcp**: `claude mcp add <name> -- <command>` または `~/.claude.json` の `mcpServers` キーに JSON 追加

### [1] プラグインマーケットプレイス

| マーケット | 規模 | 用途 | 追加コマンド |
|---|---|---|---|
| `claude-plugins-official` | 172 プラグイン | built-in、本テンプレ主軸 | （built-in、追加不要） |
| `anthropics/knowledge-work-plugins` | 41 プラグイン | ビジネス・ナレッジワーク | `/plugin marketplace add anthropics/knowledge-work-plugins` |
| `ChromeDevTools/chrome-devtools-mcp` | DevTools MCP | フロントエンドデバッグ | `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp` |
| `zircote/lsp-marketplace` | 28 言語 LSP | 必要言語のみ | `/plugin marketplace add zircote/lsp-marketplace` |
| `xiaolai/claude-plugin-marketplace` | キュレーション | 高品質厳選 | `/plugin marketplace add xiaolai/claude-plugin-marketplace` |
| `rohitg00/awesome-claude-code-toolkit` | 176+ プラグイン + 135 agent | 探索用 | `/plugin marketplace add rohitg00/awesome-claude-code-toolkit` |
| `jeremylongshore/claude-code-plugins-plus-skills` | 425 プラグイン+CLI | 探索用 | `/plugin marketplace add jeremylongshore/claude-code-plugins-plus-skills` |

### [2] スキル取得元（GitHub レポから個別 SKILL.md を取得）

| ソース | 取得方法 | 主なスキル |
|---|---|---|
| `anthropics/skills` | `gh repo clone anthropics/skills` | pdf, docx, xlsx, pptx, doc-coauthoring, canvas-design, theme-factory, brand-guidelines, skill-creator |
| `mattpocock/skills` | `gh repo clone mattpocock/skills` | grill-me, to-prd, to-issues, triage, tdd, improve-codebase-architecture, write-a-skill, diagnose, zoom-out, prototype, grill-with-docs, caveman, handoff, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit, git-guardrails-claude-code |
| `obra/superpowers` | `gh repo clone obra/superpowers`（同名 plugin にも同梱） | 個別 SKILL.md を取り出すとき |
| `ComposioHQ/awesome-claude-skills` | `gh repo clone ComposioHQ/awesome-claude-skills` | content-researcher 他キュレーション集 |
| `PleasePrompto/notebooklm-skill` | `gh repo clone PleasePrompto/notebooklm-skill` | notebooklm-integration |
| `Microck/ordinary-claude-skills` | `gh repo clone Microck/ordinary-claude-skills` | domain-name-brainstormer |
| `muratcankoylan/agent-skills-for-context-engineering` | `gh repo clone muratcankoylan/agent-skills-for-context-engineering` | context-optimization |

### [3] MCP サーバー登録元

| ソース | MCP / 規模 | 説明 |
|---|---|---|
| `AnkleBreaker-Studio/unity-mcp-server` | **268 tools**（**標準**） | Shader Graph・NavMesh・Animation・MPPM 等を含む最大級。`npx` + Node.js 18+、ツールは `unity_*` 命名 |
| `CoplayDev/unity-mcp` | 30+ tools（代替・軽量） | Unity Editor を AI から操作。`uvx` + `mcp-for-unity-server`、Node 不要 |
| `IvanMurzak/Unity-MCP` | 100+ tools, CLI 付き | runtime 対応、任意 C# メソッドを 1 行でツール化 |
| `CoderGamester/mcp-unity` | Node.js 実装 | （本カタログ未登録、要時参考） |

### [4] 参照系（探索・検索ディレクトリ）

- `skillsmp.com` — 6.6 万スキル検索
- `claudemarketplaces.com` — プラグイン・スキル・MCP の総合ディレクトリ
- `tonsofskills.com` — 2,778 スキル検索
- `mcpmarket.com` — MCP + スキル登録サイト
- `claudepluginhub.com` — 横断検索

---

## プラグイン一覧

### official

#### frontend-design [enabled]
> AI っぽくない、ちゃんとした UI コードを生成。リアルなデザインシステム、太字のタイポグラフィ。40 万+ インストールで最も人気。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/frontend-design
- installs: 400k+
- tags: ui, design, frontend, css
- install: /plugin install frontend-design@claude-plugins-official
- profiles: web-dev, design

#### superpowers [enabled]
> 20 以上のスキルが入ったスイスアーミーナイフ。TDD、デバッグ、プラン→コード変換、ブレスト、スキル作成。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/superpowers
- installs: 290k+
- tags: meta, workflow, tdd, debug, brainstorm
- install: /plugin install superpowers@claude-plugins-official
- profiles: web-dev, devops, general

#### context7 [enabled]
> リアルタイムのドキュメント検索。ソースリポから最新の API と使用例を引っ張ってくる。Claude が古いライブラリコードをハルシネーションするのを防ぐ。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/context7
- tags: docs, search, hallucination-prevention
- install: /plugin install context7@claude-plugins-official
- profiles: web-dev, research, data-analysis

#### code-review [enabled]
> 構造化されたコードレビュー。バグ、セキュリティ、パフォーマンス、スタイル。レビュアーエージェント内蔵。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/code-review
- tags: review, quality, security
- install: /plugin install code-review@claude-plugins-official
- profiles: web-dev, devops

#### security-guidance [enabled]
> OWASP Top 10、認証の欠陥、インジェクション脆弱性、ハードコードされたシークレットをスキャン。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/security-guidance
- tags: security, owasp, audit
- install: /plugin install security-guidance@claude-plugins-official
- profiles: web-dev, devops

#### commit-commands [enabled]
> Git ワークフローの自動化。スマートコミット、PR 作成、チェンジログ生成。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/commit-commands
- tags: git, commit, pr, changelog
- install: /plugin install commit-commands@claude-plugins-official
- profiles: web-dev, devops, general

#### feature-dev [enabled]
> 機能実装のエンドツーエンドワークフロー。仕様→計画→実装→テスト→PR。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/feature-dev
- tags: workflow, planning, implementation
- install: /plugin install feature-dev@claude-plugins-official
- profiles: web-dev, project-mgmt

#### plugin-dev [enabled]
> 自分でプラグインを作るための 7 つのエキスパートスキル。フック、MCP、コマンド、エージェント、バリデーション。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/plugin-dev
- tags: plugin-dev, hooks, mcp, meta
- install: /plugin install plugin-dev@claude-plugins-official
- profiles: web-dev, devops

#### skill-creator [enabled]
> スキル作成・既存スキルの改善・パフォーマンス評価のループ。トリガー説明文の最適化機能も。本テンプレートで追加有効化済み。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/skill-creator
- tags: skill-dev, meta, evaluation
- install: /plugin install skill-creator@claude-plugins-official
- profiles: web-dev, general

#### claude-md-management [enabled]
> CLAUDE.md ファイルの監査・改善・標準化。リポジトリ全体の CLAUDE.md 品質を均す。本テンプレートで追加有効化済み。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/claude-md-management
- tags: meta, claude-md, documentation
- install: /plugin install claude-md-management@claude-plugins-official
- profiles: web-dev, devops, general

### code-quality

#### typescript-lsp [enabled]
> TypeScript の型チェックとナビゲーション。定義ジャンプ・参照検索・型エラー確認に対応する公式 LSP。

- marketplace: claude-plugins-official
- tags: lsp, typescript, types
- install: /plugin install typescript-lsp@claude-plugins-official
- profiles: web-dev

#### pyright-lsp [enabled]
> Python の言語サーバー（pyright ベース）。型推論と参照解析が高速。

- marketplace: claude-plugins-official
- tags: lsp, python, types
- install: /plugin install pyright-lsp@claude-plugins-official
- profiles: web-dev, data-analysis, research

#### rust-analyzer-lsp
> rust-analyzer 連携。Rust のコード補完・型・参照解析。

- marketplace: claude-plugins-official
- tags: lsp, rust
- install: /plugin install rust-analyzer-lsp@claude-plugins-official
- profiles: web-dev

#### ruby-lsp [enabled]
> Ruby のコードインテリジェンス。Rails 開発でも有効。

- marketplace: claude-plugins-official
- tags: lsp, ruby, rails
- install: /plugin install ruby-lsp@claude-plugins-official
- profiles: web-dev

#### pydantic-ai [available]
> Pydantic AI エージェント開発フレームワーク。研究プロトタイピング・LLM 統合に。

- marketplace: claude-plugins-official
- tags: ai-agent, pydantic, llm, python
- install: /plugin install pydantic-ai@claude-plugins-official
- profiles: web-dev, research, data-analysis

#### serena [available]
> セマンティックなコード分析。大規模リファクタリングや研究コード理解に有用。

- marketplace: claude-plugins-official
- tags: code-analysis, semantic, refactor
- install: /plugin install serena@claude-plugins-official
- profiles: web-dev, research

### autonomous

#### ralph-loop
> 自律コーディングセッション。Claude がタスクを 1 つずつ処理して git にコミットし、そのまま次に進む。放っておけば、きれいな git 履歴とともに完成したコードが待っている。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/ralph-loop
- tags: autonomous, loop, git, hands-free
- install: /plugin install ralph-loop@claude-plugins-official
- profiles: web-dev, devops

#### chrome-devtools-mcp
> 既存の Chrome セッションを使ってネットワークリクエスト、コンソールエラー、ライブページのデバッグができる。フロントエンドデバッグで過小評価。

- marketplace: claude-plugins-official
- tags: debug, frontend, chrome, devtools
- install: /plugin install chrome-devtools-mcp@claude-plugins-official
- profiles: web-dev, design, system-dev

#### playwright [enabled]
> Claude が実際のブラウザを操作する。クリック、フォーム入力、スクリーンショット、UI テスト。テストスクリプト不要。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/playwright
- tags: e2e, browser, testing, automation
- install: /plugin install playwright@claude-plugins-official
- profiles: web-dev, design

### search-data

#### firecrawl [enabled]
> 任意の URL をスクレイプ、サイトクロール、自律リサーチエージェント。Web データを Claude Code に入れるための定番。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/firecrawl
- tags: scrape, crawl, research, web
- install: /plugin install firecrawl@claude-plugins-official
- profiles: research, business, data-analysis

#### sourcegraph
> コードベース横断検索。参照のトレース、リファクタリング影響分析、セキュリティスキャン。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/sourcegraph
- tags: search, codebase, refactor
- install: /plugin install sourcegraph@claude-plugins-official
- profiles: web-dev, devops

#### data-engineering [partner]
> ウェアハウス探索、パイプライン作成、Airflow 連携（パートナー製）。

- marketplace: claude-plugins-official
- tags: data, pipeline, airflow, partner
- install: /plugin install data-engineering@claude-plugins-official
- profiles: data-analysis, devops

#### amplitude
> トラッキングプラン作成、アナリティクスコード生成。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/amplitude
- tags: analytics, tracking, product
- install: /plugin install amplitude@claude-plugins-official
- profiles: business, data-analysis

#### exa [available]
> 精度の高い Web 検索 API。論文・記事・学術ソースのリサーチに最適（汎用検索より精度高）。

- marketplace: claude-plugins-official
- tags: search, web, research, paper
- install: /plugin install exa@claude-plugins-official
- profiles: research, data-analysis

#### huggingface-skills [available]
> Hugging Face モデル・データセット管理。ML 研究の必須統合。

- marketplace: claude-plugins-official
- tags: ml, dataset, model, ai
- install: /plugin install huggingface-skills@claude-plugins-official
- profiles: research, data-analysis

#### pinecone [available]
> Pinecone ベクトルデータベース統合。RAG・論文セマンティック検索・知識ベース構築に。

- marketplace: claude-plugins-official
- tags: vector-db, rag, semantic-search, embedding
- install: /plugin install pinecone@claude-plugins-official
- profiles: research, data-analysis

#### fiftyone [available]
> FiftyOne コンピュータビジョンデータセット管理・可視化。CV・画像研究に。

- marketplace: claude-plugins-official
- tags: cv, dataset, visualization, image
- install: /plugin install fiftyone@claude-plugins-official
- profiles: research, data-analysis

#### clickhouse [enabled]
> ClickHouse 列指向 DB 統合。ベストプラクティス参照とクエリ補助のスキルを提供。ログ集計・解析用途、大規模イベントデータの探索的分析に。

- marketplace: claude-plugins-official
- tags: db, columnar, analytics, olap
- install: /plugin install clickhouse@claude-plugins-official
- profiles: data-analysis

### devops

#### vercel
> デプロイ、ビルド、ログ、ドメイン管理。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/vercel
- tags: deploy, hosting, edge
- install: /plugin install vercel@claude-plugins-official
- profiles: web-dev, devops

#### deploy-on-aws [enabled]
> AWS デプロイ、アーキテクチャ推奨、コスト見積もり。

- marketplace: claude-plugins-official
- tags: aws, deploy, infrastructure, cost
- install: /plugin install deploy-on-aws@claude-plugins-official
- profiles: devops

#### pagerduty
> コミット前にデプロイリスクをスコア化。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/pagerduty
- tags: risk, deploy, oncall
- install: /plugin install pagerduty@claude-plugins-official
- profiles: devops

#### mintlify
> コードからドキュメント自動生成。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/mintlify
- tags: docs, generation, api
- install: /plugin install mintlify@claude-plugins-official
- profiles: web-dev, devops

### integration

#### github
> PR、Issue、コード検索、CI/CD（定番中の定番）。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/github
- tags: github, pr, issue, ci
- install: /plugin install github@claude-plugins-official
- profiles: web-dev, devops, project-mgmt

#### slack
> ワークフロー、メッセージ下書き、チャンネル分析。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/slack
- tags: slack, messaging, workflow
- install: /plugin install slack@claude-plugins-official
- profiles: project-mgmt, business

#### sentry
> 本番エラーモニタリング、スタックトレース、修正提案。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/sentry
- tags: error, monitoring, observability
- install: /plugin install sentry@claude-plugins-official
- profiles: web-dev, devops

#### linear
> Issue 管理、スプリント管理。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/linear
- tags: issue, sprint, project
- install: /plugin install linear@claude-plugins-official
- profiles: project-mgmt

#### supabase
> DB 管理、認証、ストレージ。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/supabase
- tags: db, auth, storage, postgres
- install: /plugin install supabase@claude-plugins-official
- profiles: web-dev

#### stripe
> 決済、サブスク、請求書、顧客データ。

- marketplace: claude-plugins-official
- url: https://claude.com/plugins/stripe
- tags: payment, subscription, billing
- install: /plugin install stripe@claude-plugins-official
- profiles: web-dev, business

#### notion [available]
> Notion ワークスペース連携。文献整理・研究ノート管理・チーム共有に。

- marketplace: claude-plugins-official
- tags: notes, knowledge-base, collaboration
- install: /plugin install notion@claude-plugins-official
- profiles: research, project-mgmt, business

#### coplay-unity-mcp [available]
> [代替] Unity Editor を Claude Code から操作する軽量 MCP ブリッジ。assets/scenes/scripts/build/physics/Cinemachine/UI/Roslyn 型チェック等 30+ tools。batch_execute で 10-100x 高速。uvx(Python) 起動で Node 不要。268 tools が過剰な場合の軽量構成。

- kind: plugin
- marketplace: external (GitHub)
- source: CoplayDev/unity-mcp
- url: https://github.com/CoplayDev/unity-mcp
- tags: unity, gamedev, vr, simulation, editor
- profiles: system-dev, research
- install: claude mcp add unityMCP -- uvx --from mcpforunityserver mcp-for-unity --transport stdio

#### ivanmurzak-unity-mcp [available]
> AI Skills + MCP Tools + CLI for Unity。100+ tools 3 カテゴリ（Project&Assets / Scene&Hierarchy / Scripting&Editor）。runtime 対応、任意 C# メソッドを 1 行でツール化。

- kind: plugin
- marketplace: external (GitHub)
- source: IvanMurzak/Unity-MCP
- url: https://github.com/IvanMurzak/Unity-MCP
- tags: unity, gamedev, ai-skills, cli, runtime
- profiles: system-dev, research
- install: unity-mcp-cli install-plugin ./MyUnityProject && unity-mcp-cli setup-skills claude-code ./MyUnityProject

#### anklebreaker-unity-mcp [active]
> [標準] **268 tools** の最大級 Unity MCP。Scene/GameObject/Build/Profiling/Shader Graph/Amplify/Terrain/Physics/NavMesh/Animation/MPPM multiplayer 等。本テンプレ標準（.mcp.json の unityMCP / `unity-development` skill / `unity-debugger` subagent が対応）。ツールは `unity_*` 命名。Node.js 18+ + Unity 側 `unity-mcp-plugin`（UPM Git URL）が前提。

- kind: plugin
- marketplace: external (GitHub)
- source: AnkleBreaker-Studio/unity-mcp-server
- url: https://github.com/AnkleBreaker-Studio/unity-mcp-server
- tags: unity, gamedev, shader, physics, animation, multiplayer
- profiles: system-dev, research
- install: claude mcp add unityMCP -- npx -y anklebreaker-unity-mcp@latest
- plugin-url: https://github.com/AnkleBreaker-Studio/unity-mcp-plugin.git

#### figma-mcp [available]
> 公式 Figma MCP サーバ。design→code（get_design_context / get_screenshot / get_metadata）・code→design（use_figma）・Code Connect・design tokens / variables・FigJam・Figma Slides（プレゼン作成）を双方向で扱う。本テンプレ標準（.mcp.json の figma / `figma-integration` skill が対応）。

- kind: plugin
- marketplace: external (公式)
- source: Figma
- url: https://developers.figma.com/docs/figma-mcp-server/
- tags: figma, design, ui, slides, code-connect, tokens
- profiles: design
- install: claude mcp add --transport http figma https://mcp.figma.com/mcp

### business-knowledge

#### brand-voice
> ブランドトーンを全コンテンツで統一。

- marketplace: knowledge-work-plugins
- tags: brand, voice, content
- install: /plugin install brand-voice@knowledge-work-plugins
- profiles: business, writing

#### marketing
> SEO 監査、コンテンツ戦略、競合分析。

- marketplace: knowledge-work-plugins
- tags: marketing, seo, content
- install: /plugin install marketing@knowledge-work-plugins
- profiles: business, writing, research

#### sales
> 見込み客リサーチ、メールシーケンス、反論対応。

- marketplace: knowledge-work-plugins
- tags: sales, outreach, leads
- install: /plugin install sales@knowledge-work-plugins
- profiles: business, research

#### legal
> 契約レビュー、コンプライアンス（初回スクリーニング用。法的アドバイスではない）。

- marketplace: knowledge-work-plugins
- tags: legal, contract, compliance
- install: /plugin install legal@knowledge-work-plugins
- profiles: business

#### finance
> 財務分析、予算計画、予測モデル。

- marketplace: knowledge-work-plugins
- tags: finance, budget, forecast
- install: /plugin install finance@knowledge-work-plugins
- profiles: business

#### productivity
> 会議要約、タスク管理、メール下書き。

- marketplace: knowledge-work-plugins
- tags: meeting, task, email
- install: /plugin install productivity@knowledge-work-plugins
- profiles: project-mgmt, business, general

---

## subagent 一覧

`.claude/agents/<name>.md` として配置する subagent 雛形 5 個。`Agent(subagent_type="<name>", ...)` で起動。本テンプレートが標準提供。

### subagent

---

#### figma-reviewer [active]
> Figma デザイン / スライドを読み取り専用でレビューする専門エージェント。公式 Figma MCP の get_design_context・get_screenshot・get_metadata・get_variable_defs を解析し、コンポーネント整合・design tokens 一貫性・アクセシビリティ（コントラスト / WCAG）・レスポンシブ・Figma Slides の構成を点検して severity 付き構造化フィードバックを返す。書き換え（use_figma など mutation）は行わない。Figma デザイン / スライドの査定・提出前チェック時に使う。Use when reviewing a Figma design or Figma Slides deck.

- kind: subagent
- tools: Read, Glob, mcp__figma__get_design_context, mcp__figma__get_screenshot, mcp__figma__get_metadata, mcp__figma__get_variable_defs, mcp__claude_ai_Figma__get_design_context, mcp__claude_ai_Figma__get_screenshot, mcp__claude_ai_Figma__get_metadata, mcp__claude_ai_Figma__get_variable_defs
- tags: figma, design-review, accessibility, slides
- profiles: design

<!-- AUTO-DISCOVERED 2026-06-14: unity-debugger -->
#### unity-debugger [active]
> Unity のコンパイルエラー・実行時例外・シーン / 物理セットアップ不整合を診断する読み取り専用エージェント。unityMCP（AnkleBreaker）の unity_get_compilation_errors・unity_console_log・unity_scene_hierarchy・unity_gameobject_info・unity_search_missing_references・unity_editor_state を解析し、原因と修正方針を severity 付きで構造化して返す。書き換え（Edit / Write / unity_*_create / _update / _set_*）は行わない。Unity 固有エラーのデバッグ・原因特定時に使う。Use when diagnosing Unity compilation errors, runtime exceptions, or scene/physics setup issues.

- kind: subagent
- tools: Read, Grep, Glob, mcp__unityMCP__unity_get_compilation_errors, mcp__unityMCP__unity_console_log, mcp__unityMCP__unity_editor_state, mcp__unityMCP__unity_scene_hierarchy, mcp__unityMCP__unity_gameobject_info, mcp__unityMCP__unity_search_missing_references, mcp__unityMCP__unity_script_read
- tags: unity, debugging, error-diagnosis
- profiles: system-dev, research

## コマンド一覧

`.claude/commands/<name>.md` として配置し、Claude Code 内で `/<name>` 形式で実行するスラッシュコマンド。本テンプレート提供分と今後追加予定分。

### command

#### catalog-sync
> CATALOG.md から docs/CATALOG.html を再生成する。MD 編集後や hooks 同期取りこぼし時に実行。

- kind: command
- path: .claude/commands/catalog-sync.md
- tags: catalog, sync, build
- profiles: meta, general

> **status 自動判定**: `.claude/commands/<name>.md` 実体の存在で `[active]`/`[planned]` がビルド時に自動付与される。現状 `catalog-sync` のみ `[active]`。

---

<!-- AUTO-DISCOVERED 2026-05-16: init-project -->
#### init-project [active]
> テンプレートをプロジェクト用に初期化。ステップ 0 の環境プリフライトで未導入を検出したら承認のうえ導入し、用途プロファイルを選び、CLAUDE.md を生成、推奨プラグインを一括有効化、非該当 skill / subagent / command を _archived/ へ退避。

- kind: command

<!-- AUTO-DISCOVERED 2026-05-20: ticket-create -->
#### ticket-create [active]
> 新規タスクチケット (tasks/T-NNN-<slug>.md) を [ ] チェックボックス形式で生成。次の T-NNN を自動採番し、汎用 5 セクション構成（目的 / 背景 / 手順 / 検証 / 完了報告）を出力する。

- kind: command
- profiles: meta

<!-- AUTO-DISCOVERED 2026-05-20: ticket-run -->
#### ticket-run [active]
> 既存タスクチケット (tasks/T-NNN-<slug>.md) を実行。手順 / 検証 セクションの各 `- [ ]` 項目を順に実施し、完了するたびに `- [x]` へ更新する。全項目が完了したら frontmatter の status を done にし、完了報告を追記してファイルを tasks/_done/ へ移動する。

- kind: command
- profiles: meta

#### doctor [active]
> テンプレ環境の健全性診断。settings 構文 / catalog drift / user-scope drift / 秘匿情報の直書き / スコープ衝突 / ドキュメントのリンク切れなど 19 項目を一括チェックしてレポートを出力する。判定は .claude/scripts/doctor.py にあり、/init-project のプリフライトと共有する。

- kind: command
- profiles: meta

<!-- AUTO-DISCOVERED 2026-05-20: profile-switch -->
#### profile-switch [active]
> 既に初期化済みのプロジェクトのプロファイルを別プロファイルに切り替える。/init-project の再実行と同等だが、仕様文の再入力をスキップして baseline のみで切替する軽量フロー。

- kind: command
- profiles: meta

<!-- AUTO-DISCOVERED 2026-05-20: ticket-list -->
#### ticket-list [active]
> tasks/ 配下の未完了チケットを一覧表示する。frontmatter から id / title / status / category / estimated_minutes / depends_on を抽出し、表形式で出力。完了済み (tasks/_done/) は件数のみ集計。

- kind: command
- profiles: meta

## スキル一覧

`.claude/skills/<category>/<name>/SKILL.md` として配置するスキル。copy ボタンを押すと `gh repo clone + cp` のワンライナーがクリップボードに入る（取得から配置まで一発）。

### planning

### research

---

#### domain-name-brainstormer [active]
> Generates creative domain name ideas for your project and checks availability across multiple TLDs (.com, .io, .dev, .ai, etc.). Saves hours of brainstorming and manual checking.

- kind: skill
- path: .claude/skills/research/domain-name-brainstormer
- source: github.com/Microck/ordinary-claude-skills

---

---

---

#### agent-council [active]
> Convene a panel of CLI-based AI agents (Codex, Gemini) to deliberate on a question. Each agent answers independently, then you synthesize the council's verdict as chairman. Use for architecture decisions, code review, debugging hypotheses, or any question where diverse perspectives add value.

- kind: skill
- path: .claude/skills/research/agent-council

<!-- AUTO-DISCOVERED 2026-05-19: agent-council-nudge -->
#### agent-council-nudge [active]
> Ambient awareness for Agent Council. Detects moments where convening a multi-model council would genuinely help and suggests the right command. Never interrupts. Never nags. Just a quiet tip at the right moment.

- kind: skill
- path: .claude/skills/research/agent-council/agent-council-nudge

<!-- AUTO-DISCOVERED 2026-05-19: council-list -->
#### council-list [active]
> List all past Agent Council sessions for the current project. Shows session ID, mode, agent count, and question for each.

- kind: skill
- path: .claude/skills/research/agent-council/council-list

<!-- AUTO-DISCOVERED 2026-05-19: council-nudge -->
#### council-nudge [active]
> Nudge a specific agent to reconsider its opinion based on a corrected assumption. Sends the original question + response + correction to one agent and saves the updated opinion alongside the original for comparison.

- kind: skill
- path: .claude/skills/research/agent-council/council-nudge

<!-- AUTO-DISCOVERED 2026-05-19: council-outcome -->
#### council-outcome [active]
> Record the outcome of a past Agent Council decision. Was the council right? Builds calibration data over time to learn which models are best at what.

- kind: skill
- path: .claude/skills/research/agent-council/council-outcome

<!-- AUTO-DISCOVERED 2026-05-19: council-replay -->
#### council-replay [active]
> Replay a past Agent Council session in the terminal. Shows the full deliberation: question, each agent's opinion, and the chairman's synthesis.

- kind: skill
- path: .claude/skills/research/agent-council/council-replay

<!-- AUTO-DISCOVERED 2026-05-19: council-revisit -->
#### council-revisit [active]
> Revisit a past Agent Council decision with current codebase context. Re-runs the same question through the council and shows a side-by-side comparison of what changed. Use for living decisions.

- kind: skill
- path: .claude/skills/research/agent-council/council-revisit

#### notebooklm-integration [active]
> Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Browser automation, library management, persistent auth. Drastically reduced hallucinations through document-only responses.

- kind: skill
- path: .claude/skills/research/notebooklm-integration

### document

<!-- AUTO-DISCOVERED 2026-05-19: doc-coauthoring -->
#### doc-coauthoring [active]
> Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.

- kind: skill
- path: .claude/skills/document/doc-coauthoring

<!-- AUTO-DISCOVERED 2026-05-19: docx -->
#### docx [active]
> Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a 'report', 'memo', 'letter', 'template', or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation.

- kind: skill
- license: Proprietary. LICENSE.txt has complete terms
- path: .claude/skills/document/docx

<!-- AUTO-DISCOVERED 2026-05-19: pdf -->
#### pdf [active]
> Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.

- kind: skill
- license: Proprietary. LICENSE.txt has complete terms
- path: .claude/skills/document/pdf

<!-- AUTO-DISCOVERED 2026-05-19: pptx -->
#### pptx [active]
> Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill.

- kind: skill
- license: Proprietary. LICENSE.txt has complete terms
- path: .claude/skills/document/pptx

<!-- AUTO-DISCOVERED 2026-05-19: xlsx -->
#### xlsx [active]
> Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved.

- kind: skill
- license: Proprietary. LICENSE.txt has complete terms
- path: .claude/skills/document/xlsx

### meta

---

### dev

---

#### massgen [active]
> Invoke MassGen's multi-agent system. Use when the user wants multiple AI agents on a task: writing, code, review, planning, specs, research, design, or any task where parallel iteration beats working alone.

- kind: skill
- path: .claude/skills/dev/massgen

<!-- AUTO-DISCOVERED 2026-06-14: unity-development -->
#### unity-development [active]
> Unity Editor を MCP（unityMCP / AnkleBreaker unity-mcp, 268 tools）経由で操作する際のワークフロー規約を Claude に適用させる。C# スクリプトは unity_script_create→unity_get_compilation_errors でコンパイル確認してから新型を使用、新規 scene は Camera + Directional Light を必須、関連操作は unity_execute_code でまとめる、パスは Assets/ 相対・forward slash、変更前に unity_editor_state など read 系を先に確認。Unity / VR / AR / 物理シミュレーションのシーン構築・スクリプト編集・ビルド・デバッグ時に発火する。Use when building or editing Unity scenes, scripts, prefabs, or running Unity via the MCP bridge.

- kind: skill
- path: .claude/skills/dev/unity-development
- tags: unity, gamedev, vr, simulation, mcp
- profiles: system-dev, research

### project

---

### write

### design

<!-- AUTO-DISCOVERED 2026-06-14: figma-integration -->
#### figma-integration [active]
> Figma 連携の入口ガイド。公式 Figma MCP（mcp__claude_ai_Figma__*）を使った design→code（get_design_context / get_screenshot / get_metadata）、code→design（use_figma）、Code Connect マッピング、design tokens / variables、FigJam 図、および Figma Slides（プレゼン資料）作成の使い分けと、サーバ同梱 /figma-* skill のロード順を示す。Figma URL を渡された時・UI / デザインシステム構築時・スライド作成時に発火する。Use when implementing a Figma design as code, pushing code into Figma, building a design system, or creating Figma Slides.

- kind: skill
- path: .claude/skills/design/figma-integration
- tags: figma, design, ui, slides, code-connect, tokens
- profiles: design

---

## エントリの追加方法

このカタログは `.claude/scripts/build_catalog.py` がパースして HTML を生成します。**`kind` の選び方は「kind 体系」セクション（冒頭）を参照**。1 エントリの最小フォーマット:

```markdown
#### <name> [<status>]
> 1 行説明（blockquote）

- kind: plugin | skill | subagent | command   # 既定: plugin
- description: 詳細説明                 # 任意。1 行説明と同じなら省略可
- tags: tag1, tag2, tag3
- profiles: web-dev, research, ...
- url: https://...                     # 任意
- install: <導入コマンド>               # kind に応じて /plugin install or claude mcp add or gh clone+cp
- copy: 任意の文字列                    # 上記より優先（汎用 override）
```

### kind 別の必須/推奨フィールドと自動同期挙動

| kind | 必須 | 推奨 | copy ボタン中身 | filesystem 同期 |
|---|---|---|---|---|
| `plugin` | name, description, marketplace, install | url, installs, tags, profiles | `install` フィールド | 削除なし（外部）／marketplace plugin は `enabledPlugins` から `[enabled]` 自動付与。standalone MCP（`marketplace: external (GitHub)`）も同じ kind |
| `skill` | name, description, path | source, tags, profiles, license, install | `install` (gh clone+cp) | `.claude/skills/<cat>/<name>/SKILL.md` の存在で `[active]`、無ければ削除 |
| `subagent` | name, description, tools | tags, profiles | `name` のみ | `.claude/agents/<name>.md` の存在で `[active]`、無ければ削除 |
| `command` | name, description | tags, profiles | `/<name>` | `.claude/commands/<name>.md` の存在で `[active]`、無ければ削除 |

### status の意味

- `[enabled]`: プラグイン有効化済み（`.claude/settings.json` から自動反映）
- `[available]`: インストール可能だが未有効化（plugin/skill の既定）
- `[active]`: filesystem に実体あり（subagent/skill/command）
- `[planned]`: CATALOG に記述あるが filesystem 実体なし（subagent/command）。次の `/catalog-sync` で **削除される**
- `[partner]`: パートナー製プラグイン
- `[anthropic]` / `[community]` / `[self]`: スキルの出自タグ

### 編集後

1. このファイル（`CATALOG.md`）を保存すると hook が `docs/CATALOG.html` を自動再生成
2. 自動同期が走らなかった場合は `/catalog-sync` または `bash .claude/scripts/sync-catalogs.sh`
3. CI 検証は `bash .claude/scripts/sync-catalogs.sh --check`（drift があれば exit 2）

---

## 研究活用ピックアップ

研究ワークフロー別のおすすめ組み合わせ。プラグイン名は `[enabled]` または `[available]` から、skill は `## スキル一覧` のエントリ名で記載。

| 活動 | おすすめ組み合わせ |
|---|---|
| **アイデア壁打ち** | `superpowers` (Brainstorming) + skill `grill-me` + skill `domain-name-brainstormer` |
| **論文調査・文献検索** | `firecrawl` + `exa` + `context7` + skill `content-research-writer` |
| **論文要約** | skill `pdf` + skill `doc-coauthoring` + `notion` |
| **論文執筆** | skill `doc-coauthoring` + skill `docx` + skill `to-prd` |
| **発表資料・図表作成** | skill `pptx` + skill `theme-factory` + skill `canvas-design` + `frontend-design`（Figma Slides は mcp `figma-mcp` + skill `figma-integration`） |
| **実験データ整理・分析** | skill `xlsx` + `pyright-lsp` + subagent `data-scientist` + `huggingface-skills` |
| **文献ノート管理** | `notion` + skill `notebooklm-integration` |
| **仮説生成・代替案出し** | `superpowers` + skill `agent-council` |
| **複数モデルの合意形成** | skill `agent-council`（Codex / Gemini と合議） |
| **査読対応・改稿** | `code-review` + subagent `japanese-proofreader` + skill `content-research-writer` |
| **再現性確保・コード管理** | `superpowers` + `github` + subagent `code-reviewer` |
| **RAG・ベクトル検索** | `pinecone` + `firecrawl` |
| **CV・画像研究** | `fiftyone` + `huggingface-skills` + skill `canvas-design` |
| **AI エージェント実装** | `pydantic-ai` + `serena` + subagent `planner` |
| **VR/AR・物理シミュレーション** | mcp `anklebreaker-unity-mcp`（標準, 268 tools / 代替: `coplay-unity-mcp`） + skill `unity-development` |
| **長セッション最適化** | skill `context-optimization` |
| **スキル発見・自作** | skill `find-skills` + skill `write-a-skill` + `skill-creator` |

---

## 用途別推奨組み合わせ（公式ガイド）

| 用途 | 組み合わせ |
|---|---|
| 全開発者向け | frontend-design + code-review + commit-commands + 自分の言語の LSP |
| フルスタック | superpowers + context7 + github + supabase |
| フロントエンド | frontend-design + chrome-devtools + playwright + vercel |
| UI/UX デザイン・スライド | mcp `figma-mcp` + skill `figma-integration` + subagent `figma-reviewer` + frontend-design |
| Unity / VR / 物理シミュレーション | mcp `anklebreaker-unity-mcp`（標準） + skill `unity-development` + subagent `unity-debugger` |
| DevOps | deploy-on-aws + sentry + pagerduty + github |
| ビジネス/マーケ | brand-voice + marketing + sales + productivity |
| データ | data-engineering + firecrawl + clickhouse |
| 研究 R&D | superpowers + context7 + firecrawl + 自分の言語の LSP |

---

## 自動同期の限界（手動 `/catalog-sync` が必要なケース）

`.claude/hooks/catalog-sync.sh` は Claude Code の Write/Edit/MultiEdit ツール呼び出しに反応して HTML を再生成します。以下では発火しないため、手動同期が必要です。

1. **Claude Code 以外の編集** — vim / VS Code 直編集 / `git pull` / `cp` / `mv` / `rm`
2. **外部プロセスによる変更** — CI ジョブ、ビルドスクリプト、npm script、pre-commit fix-up
3. **ディレクトリ単位の操作** — `mv .claude/skills/foo .claude/skills/bar/`（Write/Edit/MultiEdit 以外のツール）
4. **アーカイブ展開・curl/git clone** で SKILL.md を追加した場合
5. **hook スクリプト自体の実行エラー** — python3 不在、構文エラー、I/O 失敗
6. **Claude Code 起動前の変更** — オフライン編集
7. **hooks 無効化中** — `.claude/settings.local.json` で上書きしている時
8. **自己再帰スキップ中の他カタログ変更** — lock 取得済みの間に来た連続更新
9. **高速連続編集** — 最初の発火中に追加変更が入ると一部反映漏れ

→ いずれの場合も `/catalog-sync`（または `bash .claude/scripts/sync-catalogs.sh`）で完全再生成できます。

---

## 出典

- [.claude/settings.json](../.claude/settings.json) — 有効化状態の source of truth
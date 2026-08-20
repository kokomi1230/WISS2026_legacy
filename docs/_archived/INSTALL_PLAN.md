---
title: INSTALL_PLAN
version: 2026-05-18
sources:
  - docs/STANDALONE_SKILLS.md
  - .claude/settings.json (enabledPlugins)
scope: 72sen の 72 件のうち除外 11 件（C 区分 5 件 + D 区分 1 件 + Deprecated/Personal 5 件）を除いた 61 件すべて
---

# 導入プラン（プラグイン + Standalone Skill + MCP）

> **プラグインの一括導入は `bash .claude/scripts/setup-plugins.sh`（user scope・冪等）を正とする。**
> マニフェスト `.claude/plugins-user-scope.json`（`marketplaces` / `core` / `extra` / `auth_local_only`）が source of truth。
> 本ドキュメントの STEP 1〜2（`/plugin marketplace add` / `/plugin install` の手動列挙）は背景・個別追加の参照用。
> core/extra は user scope で導入し、有効化はプロジェクトの `.claude/settings.json` 差分（`/init-project <profile>`）で最適化する。
> 認証 OAuth 系（`auth_local_only`）は user scope 導入対象外で、各プロジェクトの local scope で各自インストール・認証する。
> 詳細は [docs/PLUGIN_INSTALL_SCOPE.md](PLUGIN_INSTALL_SCOPE.md)。

`docs/STANDALONE_SKILLS.md`（2026-05-18 自己検証済み）の調査結果を**実行手順に落とした actionable リスト**です。 72sen の 72 件のうち除外 11 件（区分 C 5 件 + 区分 D 1 件 + Deprecated/Personal 5 件: #6 design-an-interface, #24 qa, #43 edit-article, #45 obsidian-vault, #47 ubiquitous-language）を除いた **61 件** を、以下の優先順位で導入します。

1. **プラグイン（上位互換）** — `/plugin marketplace add` + `/plugin install` で導入できるものは必ずプラグイン側を採用
2. **Standalone skill** — プラグイン版がない、または author が明示的に standalone 配布しているもの
3. **MCP / CLI** — skill ではなく外部サーバー / CLI として配布されているもの

## 全体サマリ

| 経路 | 件数 | 状態 | 対応 STEP |
|---|---|---|---|
| B-1. 既 enabled プラグイン | 13 | 既存（何もしなくて良い） | STEP 5 で確認のみ |
| B-2. anthropics/skills 追加 | 10 | 新規 install | STEP 1, 2 |
| B-3. mattpocock-skills 追加 | 8 | 新規 install | STEP 1, 2 |
| B-4. 個別マーケットプレイス追加 | 5 | 新規 install | STEP 1, 2 |
| 区分 A. Standalone skill 取り込み | 20 | 新規 import | STEP 3 |
| 区分 E. MCP / CLI 導入 | 5 | 新規 install（個別手順） | STEP 4 |
| **合計** | **61** | 既存 13 + 新規 48 | — |

除外 11 件: 区分 C 独自パック 5 件（64〜68）+ 区分 D deprecated 1 件（34）+ Deprecated/Personal 5 件（#6, #24, #43, #45, #47）— 本文末尾参照。

注意: 本テンプレートの既定 `enabledPlugins` は **空（T-007 で 51 → 0 にリセット）**。本 PLAN を一括実行するとマーケットプレイス登録とインストールは行われますが、`enabledPlugins` への登録は `/init-project <profile>` または個別 `/plugin enable` で行ってください。一度に有効化するのは Anthropic 公式推奨「同時 3〜5 個」を目安に。

---

## STEP 0. 事前準備

```bash
# 1. 現状確認
cat .claude/settings.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'enabled plugins: {sum(d[\"enabledPlugins\"].values())}'); print('\n'.join(sorted(d['enabledPlugins'].keys())))"

# 2. バックアップ
cp .claude/settings.json .claude/settings.json.bak.$(date +%Y%m%d)
cp -r .claude/skills .claude/skills.bak.$(date +%Y%m%d)

# 3. gh / git の認証確認（STEP 3 で必要）
gh auth status
```

---

## STEP 1. マーケットプレイス追加（7 個）

Claude Code 内で 1 行ずつ実行（プロンプト入力欄に貼り付け）。

```
/plugin marketplace add anthropics/skills
/plugin marketplace add mattpocock/skills
/plugin marketplace add AgriciDaniel/claude-seo
/plugin marketplace add kingbootoshi/nano-banana-2-skill
/plugin marketplace add jezweb/claude-skills
/plugin marketplace add muratcankoylan/Agent-Skills-for-Context-Engineering
/plugin marketplace add coreyhaines31/marketingskills
```

| マーケット | 出所信頼性 |
|---|---|
| `anthropics/skills` | `[公式]` Anthropic 公式リポ |
| `mattpocock/skills` | `[コミュニティ]` Matt Pocock（1.65 万スター、aihero.dev） |
| `AgriciDaniel/claude-seo` | `[コミュニティ]` 個人 |
| `kingbootoshi/nano-banana-2-skill` | `[コミュニティ]` 個人 |
| `jezweb/claude-skills` | `[コミュニティ]` Jezweb（豪州、jezweb.net） |
| `muratcankoylan/Agent-Skills-for-Context-Engineering` | `[コミュニティ]` 個人 |
| `coreyhaines31/marketingskills` | `[コミュニティ]` Corey Haines（corey.co） |

---

## STEP 2. プラグイン install（23 件、合計 8 プラグイン）

### STEP 2-1. anthropics/skills — 10 スキル

```
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

| プラグイン | カバー（72sen #） | 内包内容 |
|---|---|---|
| `document-skills` | 52 PPTX, 53 XLSX, 54 PDF, 55 DOCX | 4 スキル |
| `example-skills` | 10 Canvas Design, 11 Theme Factory, 16 Brand Guidelines, 17 Algorithmic Art, 18 Web Artifacts Builder, 42 Doc Co-Authoring | 6 スキル + bonus（internal-comms, mcp-builder, slack-gif-creator, webapp-testing） |

注意:
- `example-skills` 内部に **frontend-design / skill-creator も含まれており、既 enabled の同名プラグインと重複ロード**になります。STEP 6 で `/plugin disable example-skills@anthropic-agent-skills` の選択肢、または `frontend-design@claude-plugins-official` / `skill-creator@claude-plugins-official` を disable する選択肢を併記。

### STEP 2-2. mattpocock-skills — 8 スキル

```
/plugin install mattpocock-skills@mattpocock-skills
```

| カバー（72sen #） | プラグイン内 path |
|---|---|
| 2 Grill Me | `skills/productivity/grill-me` |
| 3 Write a PRD | `skills/engineering/to-prd` |
| 5 PRD to Issues | `skills/engineering/to-issues` |
| 19 TDD | `skills/engineering/tdd` |
| 23 Improve Codebase Architecture | `skills/engineering/improve-codebase-architecture` |
| 25 Triage Issue | `skills/engineering/triage` |
| 60 GitHub Triage | `skills/engineering/triage`（25 と統合済） |
| 70 Write a Skill | `skills/productivity/write-a-skill` |

ボーナス: diagnose / zoom-out（**34 Request Refactor Plan の公式置換先**） / grill-with-docs / prototype / caveman / handoff / setup-matt-pocock-skills も同時導入。

注意:
- author 公式 README は `npx skills@latest add mattpocock/skills`（cross-platform CLI）を推奨。本テンプレはプラグイン主軸のため plugin install を採用（上位互換として扱う）。
- author の残り 9 スキル（6, 24, 32, 33, 36, 37, 43, 45, 47）は本プラグインに含まれず `deprecated/` / `misc/` / `personal/` 配下にある（STEP 3 で個別 import）。

### STEP 2-3. 個別マーケットプレイス — 5 スキル

```
/plugin install claude-seo@agricidaniel-seo
/plugin install nano-banana@nano-banana-2-skill-marketplace
/plugin install design-assets@jezweb-skills
/plugin install context-engineering@context-engineering-marketplace
/plugin install marketing-skills@marketingskills
```

| プラグイン | カバー（72sen #） | 備考 |
|---|---|---|
| `claude-seo` | 46 Claude SEO | 25 サブスキル + 18 サブエージェント |
| `nano-banana` | 13 Image Generator | Bun + FFmpeg + ImageMagick が前提 |
| `design-assets` | 14 Local Image Gen | jezweb-skills の中の 1 プラグイン（他 6 プラグインも同時アクセス可） |
| `context-engineering` | 31 Context Optimization | 14 スキル束（context-fundamentals 他） |
| `marketing-skills` | 49 Marketing Skills | 40 スキル束。`marketing@knowledge-work-plugins` と重複の可能性、STEP 6 で disable 候補 |

---

## STEP 3. Standalone skill import（20 件）

各セクションは Claude Code のプロンプト欄ではなく、**シェルで実行**するコマンド群です。

### STEP 3-1. meta カテゴリ（2 件）

```bash
# 72 Awesome Claude Skills (キュレーション集、reference として配置)
git clone https://github.com/ComposioHQ/awesome-claude-skills /tmp/awesome-claude-skills
mkdir -p .claude/skills/meta/awesome-claude-skills
cp /tmp/awesome-claude-skills/README.md .claude/skills/meta/awesome-claude-skills/SKILL.md
# 注: 本来 SKILL.md ではなくカタログなので、必要に応じて手動で frontmatter を追加

# 71 Find Skills (skillsmp.com の Web サービス)
# GitHub レポなし。skillsmp.com を「スキル探索の reference」として記録するメモを作成
mkdir -p .claude/skills/meta/find-skills
cat > .claude/skills/meta/find-skills/SKILL.md <<'EOF'
---
name: find-skills
description: Use when looking for additional Claude Code skills not yet installed. References skillsmp.com which catalogs 1,116+ community skills.
---
# Find Skills (External Reference)

Visit https://skillsmp.com to search for skills by keyword or use case.
This SKILL.md acts as a reminder; the actual catalog lives on the website.
EOF
```

### STEP 3-2. research カテゴリ（8 件）

```bash
# 7 Domain Name Brainstormer
git clone https://github.com/Microck/ordinary-claude-skills /tmp/ordinary-claude-skills
mkdir -p .claude/skills/research/domain-name-brainstormer
cp /tmp/ordinary-claude-skills/skills_all/domain-name-brainstormer/SKILL.md .claude/skills/research/domain-name-brainstormer/SKILL.md

# 8 Idea Mining / YouTube
git clone https://github.com/AgriciDaniel/claude-youtube /tmp/claude-youtube
mkdir -p .claude/skills/research/claude-youtube
cp -r /tmp/claude-youtube/skills/claude-youtube/. .claude/skills/research/claude-youtube/

# 44 Content Researcher
git clone https://github.com/ComposioHQ/awesome-claude-skills /tmp/awesome-claude-skills 2>/dev/null
mkdir -p .claude/skills/research/content-researcher
cp /tmp/awesome-claude-skills/content-research-writer/SKILL.md .claude/skills/research/content-researcher/SKILL.md

# 50 Custom YT Search
git clone https://github.com/ZeroPointRepo/youtube-skills /tmp/youtube-skills
mkdir -p .claude/skills/research/custom-yt-search
cp /tmp/youtube-skills/README.md .claude/skills/research/custom-yt-search/SKILL.md
# 注: ZeroPointRepo は npx skills 経由が想定形式。SKILL.md の場所を README で確認

# 58 NotebookLM Integration
git clone https://github.com/PleasePrompto/notebooklm-skill /tmp/notebooklm-skill
mkdir -p .claude/skills/research/notebooklm-integration
cp /tmp/notebooklm-skill/SKILL.md .claude/skills/research/notebooklm-integration/SKILL.md

# 59 Lead Research Assistant
mkdir -p .claude/skills/research/lead-research-assistant
cp /tmp/awesome-claude-skills/lead-research-assistant/SKILL.md .claude/skills/research/lead-research-assistant/SKILL.md

# 61 Stochastic Multi-Agent Consensus (skillsmp.com の open SKILL.md)
# skillsmp.com から直接 SKILL.md を download (URL は skillsmp.com の各 skill ページから)
mkdir -p .claude/skills/research/stochastic-multi-agent-consensus
# wget <skillsmp.com の Stochastic Multi-Agent Consensus SKILL.md URL> -O .claude/skills/research/stochastic-multi-agent-consensus/SKILL.md

# 62 Model-chat / Debate (同上)
mkdir -p .claude/skills/research/model-debate
# wget <skillsmp.com の Model-chat / Debate SKILL.md URL> -O .claude/skills/research/model-debate/SKILL.md
```

### STEP 3-3. dev カテゴリ（10 件）

```bash
# mattpocock 系の skill は事前に clone（複数で再利用）
git clone https://github.com/mattpocock/skills /tmp/mp-skills

# 27 Change Log Generator
mkdir -p .claude/skills/dev/changelog-generator
cp /tmp/awesome-claude-skills/changelog-generator/SKILL.md .claude/skills/dev/changelog-generator/SKILL.md

# 30 File Search (massgen は npx skills 想定)
git clone https://github.com/massgen/massgen /tmp/massgen
mkdir -p .claude/skills/dev/file-search
cp /tmp/massgen/README.md .claude/skills/dev/file-search/SKILL.md
# 注: 公式は `npx skills add massgen/skills`。SKILL.md 位置の特定が必要

# 32 Migrate to Shoehorn (misc)
mkdir -p .claude/skills/dev/migrate-to-shoehorn
cp -r /tmp/mp-skills/skills/misc/migrate-to-shoehorn/. .claude/skills/dev/migrate-to-shoehorn/

# 33 Scaffold Exercises (misc)
mkdir -p .claude/skills/dev/scaffold-exercises
cp -r /tmp/mp-skills/skills/misc/scaffold-exercises/. .claude/skills/dev/scaffold-exercises/

# 36 Setup Pre-Commit (misc)
mkdir -p .claude/skills/dev/setup-pre-commit
cp -r /tmp/mp-skills/skills/misc/setup-pre-commit/. .claude/skills/dev/setup-pre-commit/

# 37 Git Guardrails (misc)
mkdir -p .claude/skills/dev/git-guardrails
cp -r /tmp/mp-skills/skills/misc/git-guardrails-claude-code/. .claude/skills/dev/git-guardrails/

# 38 Dependency Auditor (ComposioHQ - 具体 path は README で確認)
mkdir -p .claude/skills/dev/dependency-auditor
# cp /tmp/awesome-claude-skills/<dependency-auditor のサブディレクトリ>/SKILL.md .claude/skills/dev/dependency-auditor/SKILL.md
# 注: security-guidance@claude-plugins-official と一部重複

# 41 Emotion (CSS-in-JS、wilwaldon のドキュメント集)
git clone https://github.com/wilwaldon/Claude-Code-Video-Toolkit /tmp/ccvt
mkdir -p .claude/skills/dev/emotion
# 注: 本来 SKILL.md 形式ではないため、関連 doc を手動で SKILL.md 化する必要

# 48 API Documentation Generator (ComposioHQ)
mkdir -p .claude/skills/dev/api-doc-gen
# cp /tmp/awesome-claude-skills/<api-doc-gen のサブディレクトリ>/SKILL.md .claude/skills/dev/api-doc-gen/SKILL.md
```

### STEP 3-4. write カテゴリ（1 件）

```bash
# 12 Awesome-design (デザイン参考資料集)
git clone https://github.com/VoltAgent/awesome-design-md /tmp/awesome-design
mkdir -p .claude/skills/write/awesome-design
cp /tmp/awesome-design/README.md .claude/skills/write/awesome-design/SKILL.md
# 注: SKILL.md ではなく design 参考集なので frontmatter を手動で追加
```

---

## STEP 4. MCP サーバー / CLI 導入（2 件）

> 注: T-009 で旧 #15 Image Optimizer MCP / 旧 #56 Excel MCP は機能重複（document-skills の xlsx skill / design-assets の image-processing skill）により除外済み。

```bash
# 28 Simplification Cascade (mcpmarket.com)
# 参考: https://mcpmarket.com/tools/skills/simplification-cascades-1

# 40 Remotion Best Practices
# Remotion の skill ではなく製品リポジトリ。Remotion を使う際に CLAUDE.md で
# 「https://github.com/remotion-dev/remotion を参照」と記載するだけで十分
```

---

## STEP 5. 導入後の検証

```bash
# 1. 新規プラグインが enabled になったか
cat .claude/settings.json | python3 -c "import json,sys; d=json.load(sys.stdin); plugins=list(d['enabledPlugins'].keys()); new=['document-skills@anthropic-agent-skills','example-skills@anthropic-agent-skills','mattpocock-skills@mattpocock-skills','claude-seo@agricidaniel-seo','nano-banana@nano-banana-2-skill-marketplace','design-assets@jezweb-skills','context-engineering@context-engineering-marketplace','marketing-skills@marketingskills']; [print(f'[{\"OK\" if p in plugins else \"MISS\"}] {p}') for p in new]"

# 2. 新規 skill が配置されたか
find .claude/skills -name "SKILL.md" -newer .claude/settings.json.bak.* | wc -l
ls .claude/skills/meta/ .claude/skills/research/ .claude/skills/dev/ .claude/skills/write/

# 3. CATALOG.md / CATALOG.html の整合性確認
bash .claude/scripts/sync-catalogs.sh --check
# drift 検出時は CATALOG.md に kind:plugin / kind:skill エントリを追加 → /catalog-sync
```

---

## STEP 6. 運用緩和（オプション）

合計 53 プラグイン enabled は Anthropic 推奨「3〜5 同時」を大幅超過。以下のいずれかで運用緩和:

### 案 A: 重複の disable

```
/plugin disable example-skills@anthropic-agent-skills
# またはより細かく
/plugin disable frontend-design@claude-plugins-official
/plugin disable skill-creator@claude-plugins-official
```

`example-skills` を残すなら claude-plugins-official 側の frontend-design / skill-creator を disable する選択肢もあり。逆に既存を残すなら example-skills を install 直後に disable。

### 案 B: 用途プロファイル別に絞り込み

`.claude/profiles/<profile>.md` を切り替えて、プロファイルに不要なプラグインを `/plugin disable`。初回 install 後に `/init-project` で再評価しても良い。

### 案 C: プロジェクト単位の `.claude/settings.local.json` で上書き

global enabled 状態を変えず、プロジェクト内だけ disable する。

---

## 既 enabled プラグイン（B-1、13 件、何もしなくて良い）

スキルが必要な場面で自動発火します。これらは確認のみ。

| # | スキル | 内包プラグイン |
|---|---|---|
| 1 | Brainstorming | `superpowers:brainstorming` |
| 4 | PRD to Plan | `superpowers:writing-plans` |
| 9 | Frontend Design | `frontend-design` |
| 20 | Code Review | `code-review` |
| 21 | Systematic Debugging | `superpowers:systematic-debugging` |
| 22 | Superpowers バンドル本体 | `superpowers` |
| 26 | Auto-Commit Messages | `commit-commands:commit` |
| 29 | React Best Practices | `vercel:react-best-practices` |
| 35 | Stripe Integration | `stripe:stripe-best-practices` |
| 39 | Git Work Trees | `superpowers:using-git-worktrees` |
| 51 | Firecrawl | `firecrawl` |
| 63 | Playwright CLI | `playwright` |
| 69 | Skill Creator | `skill-creator` |

---

## 除外対象（参考、6 件）

| # | スキル | 除外理由 |
|---|---|---|
| 22 | Superpowers バンドル本体 | 既に `superpowers@claude-plugins-official` で enabled（B-1 に再掲） |
| 34 | Request Refactor Plan | 公式 deprecated。`mattpocock-skills` プラグインの `diagnose` / `zoom-out` が置換先（STEP 2-2 のボーナス） |
| 64 | 企画壁打ちパック | `_archived/`。`superpowers:brainstorming` + `feature-dev` で代替 |
| 65 | ドキュメント一括処理パック | `_archived/`。STEP 2-1 の `document-skills` で代替 |
| 66 | リサーチ→執筆パック | `_archived/`。`example-skills:doc-coauthoring` + Edit Article（STEP 3-4）で代替 |
| 67 | Meeting Automation `/mtg-notes` | `_archived/`。`productivity@knowledge-work-plugins` で代替 |
| 68 | Invoice Reader `/read-invoices` | `_archived/`。`finance@knowledge-work-plugins` で代替 |

22 は B-1 と重複カウントのため、純粋な除外は 6 件（34, 64〜68）。

---

## 想定コスト

| 項目 | 数量 | 備考 |
|---|---|---|
| 新規 marketplace 追加 | 7 個 | 1 回限り |
| 新規 plugin install | 8 個 | `/plugin install` × 8 |
| 新規 skill import | 20 件 | `git clone` × 12（複数 skill で 1 clone 共有） + `cp` 操作 |
| 新規 MCP install | 5 件 | `claude mcp add` 等、個別検証要 |
| CATALOG.md 手編集 | 38 行追加見込 | 別タスクとして実施 |
| `/catalog-sync` 実行 | 1 回 | CATALOG.html 再生成 |

---

## 関連ドキュメント

- [STANDALONE_SKILLS.md](STANDALONE_SKILLS.md) — 一次調査結果（自己検証済み）
- [CATALOG.md](CATALOG.md) — kind 体系（plugin/skill/subagent/command）と既存エントリ
- [PLUGIN_INSTALL_GUIDE.md](PLUGIN_INSTALL_GUIDE.md) — `/plugin marketplace add` の標準手順
- [PROJECT_PROFILES.md](PROJECT_PROFILES.md) — プロファイル別の推奨 plugin セット

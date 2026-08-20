# template-project-claude

あらゆる Claude Code プロジェクトの出発点となる再利用可能テンプレート。コピーして `/init-project` を実行すると、用途に合わせて設定・アセット・ディレクトリ構造が整い、テンプレート運用資産は取り除かれる。

## 目次

- [クイックスタート](#クイックスタート)
- [`/init-project` が行うこと](#init-project-が行うこと)
- [テンプレートの構造](#テンプレートの構造)
- [別マシン / 新規導入の手順](#別マシン--新規導入の手順)
- [プラグインの 3 層モデル](#プラグインの-3-層モデル)
- [残置スキル一覧](#残置スキル一覧)
- [主要ファイル](#主要ファイル)
- [利用範囲](#利用範囲)

## クイックスタート

```bash
# 1. テンプレートをコピー（このリポジトリ自身では初期化しない）
cp -r template-project-claude my-new-project
cd my-new-project

# 2. Claude Code 起動
claude

# 3. 初期化
/init-project
```

**このリポジトリ自身で `/init-project` を実行しない。** 初期化はテンプレート運用資産を削除するため、リポジトリ直下の `.template-origin` を検出した時点で中断する。必ずコピーしてから実行する。

**新しい PC でも手順は変わらない。** `/init-project` のステップ 0 が user-scope 資産とプラグインの未導入を検出し、承認を取ってから導入して先へ進む。外部リポジトリの clone は不要で、**本リポジトリだけで完結する**。

## `/init-project` が行うこと

用途プロファイルと任意の仕様文をもとに、テンプレートをプロジェクトへ作り替える。

| フェーズ | 内容 |
|---|---|
| 環境プリフライト | user-scope 資産・プラグインの未導入を検出し、承認のうえ導入する |
| プロファイル選択 | `.claude/profiles/` の 5 種から選ぶ。仕様文を渡すと Claude が `docs/CATALOG.md` と突き合わせて推奨を上書きする |
| 設定の最適化 | `.claude/settings.json` の `enabledPlugins` / `enabledMcpjsonServers` を書き換える |
| アセットの取捨 | 非該当の skill / subagent / command を `.claude/<kind>/_archived/` へ退避する |
| CLAUDE.md 生成 | `## プロジェクト規約` より前をプロファイル本文で置き換える。以降のセクションは温存される |
| ディレクトリ整備 | プロファイルの `scaffold:` に従って `src/` `tests/` などを作る（既存は触らない） |
| README 生成 | プロジェクト名・説明・技術スタックを聞き取り、プロジェクト自身の README.md を書き出す |
| 脱テンプレート化 | テンプレート運用専用の資産を一覧提示して承認を取り、削除する |

最後の脱テンプレート化で消えるのは `user-scope/`（原本の複製）、`.claude/profiles/`、`setup-*.sh`、`apply_profile.py`、`/init-project` 自身、テンプレート解説の `docs/*.md` などである。`docs/CATALOG.md` とカタログ同期・`/doctor`・チケット系の仕組みは派生プロジェクトでも動くため残る。

削除は `git rm` を伴うので `git checkout HEAD -- <path>` で復元できる。原本は常にこのテンプレートリポジトリ側に残る。

## テンプレートの構造

- `.claude/skills/` — 同梱スキル（カテゴリ別）。実体 4 カテゴリ（dev / document / research / design）+ 空 placeholder 3 種（meta / project / write）。退避済みは `_archived/`
- `.claude/agents/` — subagent 配置先。同梱は `unity-debugger`（Unity エラー診断）と `figma-reviewer`（Figma デザイン・スライドのレビュー）。いずれも read 専用でプロファイル依存
- `.claude/profiles/` — **5 種**の用途プロファイル（general / research / system-dev / writing / design）。frontmatter に `enabled_plugins` / `enabled_mcp` / `scaffold` を持つ。旧 9 種は `_archived/`
- `.claude/commands/` — **7 個**のスラッシュコマンド（init-project / catalog-sync / ticket-create / ticket-run / ticket-list / profile-switch / doctor）
- `.claude/rules/` — ファイル種別ごとの規約。`paths:` frontmatter により該当ファイルを読んだときだけ読み込まれる（catalog / user-scope / python）
- `.claude/scripts/` — 補助スクリプト。カタログ生成・プロファイル適用・脱テンプレート化・環境導入・環境診断。shell の起動処理は `_bootstrap.sh` に集約
- `.claude/hooks/catalog-sync.sh` — PostToolUse hook。`docs/CATALOG.md` / `settings.json` を編集すると HTML を再生成する
- `user-scope/` — **全プロジェクト共通資産の原本**（skill / subagent / command / scripts / statusline.sh / `settings.user.json` / `mcp-servers.user.json`）。`setup-user-scope.sh` が `~/.claude/` へ一方向で配置する
- `docs/CATALOG.md` — プラグイン・スキル・subagent を一括管理する統合カタログ（source of truth）。`docs/CATALOG.html` は生成物
- `tasks/` — T-NNN チケット。実チケットは `.gitignore` 対象で、雛形 `_template.md` だけが追跡される

用途を問わず常時使う資産（校正 subagent・執筆スタイル skill・`code-style`・`/swap-punctuation`・`/cost-report` など）はユーザースコープ（`~/.claude/`）に置く。原本は `user-scope/` にあり、判定基準は [CLAUDE.md](CLAUDE.md) の「アセットのスコープ方針」節を参照。

## 別マシン / 新規導入の手順

本リポジトリだけで完結する。macOS / Windows(Git Bash) 共通。**推奨は `/init-project` 一本**で、ステップ 0 のプリフライトが下の 1・3 を検出して代わりに実行する。

手動で進めたい場合、またはプリフライトが解決できない項目（`claude` CLI が PATH に無い等）が出た場合は以下を個別に実行する。いずれも冪等で、`--check` を付ければ dry-run できる。

```bash
# 1. ユーザースコープ資産を配置
bash .claude/scripts/setup-user-scope.sh

# 2. 秘匿情報を埋める（NOTION_TOKEN 等。不要なら省略可）
cp user-scope/.env.example ~/.claude/.env

# 3. 全 marketplace + plugin を user scope で導入
bash .claude/scripts/setup-plugins.sh

# 4. 導入状況を確認
python3 .claude/scripts/doctor.py --preflight
```

手順 1-3 は**マシンごとに 1 回**、`/init-project` は**プロジェクトごと**に実行する。`setup-user-scope.sh --diff` は配置済み資産と原本の drift を検出する（drift ありで終了コード 2）。

**Windows 対応**: symlink 配置（`--link`）は開発者モード / 管理者権限が要るため警告して copy にフォールバックする。日次・週次の自動記録（launchd）は macOS 限定で、`/notion-digest` の手動実行は両対応。改行コードは `.gitattributes` が LF に固定するため `core.autocrlf=true` でも shell / Python が壊れない。

Windows 固有の分岐は macOS 上での分岐テストまでを確認済みで、**Windows 実機での通し確認はまだ行っていない**。初回実行時は `--check` で dry-run してから適用することを勧める。

## プラグインの 3 層モデル

**導入（install）= ユーザスコープに一元化**、**有効化（enable）= プロジェクトごとに最適化**、**秘匿情報 = local 隔離** の 3 層で管理する。コピー / 別マシンでも `setup-plugins.sh` 一発で全プラグイン（OAuth 系含む）が揃い、各プロジェクトはコアからの差分だけを宣言する。

| 層 | 保存先 | 内容 |
|---|---|---|
| 導入層（user scope） | `~/.claude/settings.json` ＋ `installed_plugins.json` | 全プラグインを user scope で install。**core**（9 個）は enabled、**extra** は install して disabled。マニフェスト `.claude/plugins-user-scope.json` が source of truth |
| 最適化層（project scope） | `.claude/settings.json` | コアからの**差分のみ**記述。生 MCP（unity / figma）は `enabledMcpjsonServers` 許可リストで opt-in。`/init-project` が profile から自動生成 |
| 秘匿情報層（local scope / .env） | `.claude/settings.local.json` ／ `.env` | API キー・トークン等のみ。`.gitignore` 対象 |

マーケットプレイスのプラグインは user scope に入れても project の `enabledPlugins:false` でそのプロジェクトだけ無効化できる（同梱 MCP も停止）。一方**生の MCP サーバ（unity / figma）は user scope だと per-project 無効化ができない**ため、project の `.mcp.json` ＋ `enabledMcpjsonServers` 許可リストで扱う。

**Notion は例外**で、OAuth 版プラグインではなく API キー方式の公式 MCP サーバを user scope の `~/.claude.json` に登録する（認証を同期スクリプトと 1 本化するため）。トークンは `${NOTION_TOKEN}` のリテラル参照とし、設定ファイルに実値を書かない。

詳細手順とコラボレーター向けオンボーディングは [docs/PLUGIN_INSTALL_SCOPE.md](docs/PLUGIN_INSTALL_SCOPE.md) を参照。

## 残置スキル一覧

プラグインで代替不可能な独自運用・source-available のドキュメント処理に限定した。退避済み 29 dir は `.claude/skills/_archived/` を参照。判定根拠は各 skill の `KEPT.md` に要約してある。

- **dev** (2): massgen — マルチエージェント特殊用途 / unity-development — Unity MCP 操作の規約
- **document** (5): doc-coauthoring / docx / pdf / pptx / xlsx — Office フォーマット、プラグイン代替なし
- **research** (3): agent-council（サブ skill 6 件込み）/ domain-name-brainstormer / notebooklm-integration
- **design** (1): figma-integration — Figma 連携・デザインシステム・Figma Slides
- **meta / project / write**: 空 placeholder（`/init-project` 時に profile 固有 skill を入れ直す枠）

## 主要ファイル

| ファイル | 用途 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | プロジェクト指示書（`/init-project` が `## プロジェクト規約` より前を上書き、以降は温存） |
| [.claude/rules/](.claude/rules/) | ファイル種別ごとの規約。`paths:` により条件付きで読み込まれる |
| [docs/CATALOG.md](docs/CATALOG.md) | 統合カタログ（プラグイン・スキル・subagent・MCP、source of truth） |
| [docs/CATALOG.html](docs/CATALOG.html) | 統合カタログ（人向け UI、`build_catalog.py` が自動生成） |
| [docs/PROJECT_PROFILES.md](docs/PROJECT_PROFILES.md) | 用途プロファイル一覧 |
| [docs/PLUGIN_INSTALL_GUIDE.md](docs/PLUGIN_INSTALL_GUIDE.md) | 外部統合プラグイン導入手順 |
| [docs/PLUGIN_INSTALL_SCOPE.md](docs/PLUGIN_INSTALL_SCOPE.md) | プラグイン導入・有効化スコープ方針（3 層モデル） |
| [.claude/plugins-user-scope.json](.claude/plugins-user-scope.json) | user scope 導入マニフェスト（`setup-plugins.sh` が参照） |
| [user-scope/](user-scope/) | 全プロジェクト共通資産の原本（`setup-user-scope.sh` が `~/.claude` へ配置） |
| [.claude/scripts/doctor.py](.claude/scripts/doctor.py) | 環境診断 19 項目。`/doctor` と `/init-project` のプリフライトが共有する |
| [.claude/scripts/detemplate.py](.claude/scripts/detemplate.py) | 脱テンプレート化。`--plan` で対象一覧、`--apply` で削除 |
| [docs/_archived/](docs/_archived/) | 役目を終えたドキュメント（削除ではなく退避。参照しない） |

解説資料・知見の原文と清書版 HTML は本リポジトリではなく `~/.notion-mirror/_md/` と `~/.notion-mirror/_html/` に集約している。`docs/` に置くのはテンプレート基盤（カタログとテンプレート解説）だけである。詳細は [CLAUDE.md](CLAUDE.md) の「解説資料の置き場所」を参照。

## 利用範囲

個人 / 社内限定利用のテンプレートとして運用しており、公開再配布は想定していない。

**注意**: `.claude/skills/document/` 配下（doc-coauthoring / docx / pdf / pptx / xlsx）は Anthropic 公式 agent-skills 由来の source-available スキル。各 skill ディレクトリ内の `LICENSE.txt` が原典の条件を保持しており、再配布禁止。

# 用途プロファイル一覧

`/init-project` で選択できる **5 種**のプロファイル。プロファイルは `.claude/profiles/<name>.md` に定義され、`CLAUDE.md` の冒頭へ差し込まれる。

一覧は実体から取得できる:

```bash
python3 .claude/scripts/apply_profile.py --list-profiles
```

## プロファイル一覧

| プロファイル | 用途 | 有効化する主なプラグイン / MCP |
|---|---|---|
| [general](../.claude/profiles/general.md) | 汎用（用途未確定時の軸） | superpowers / feature-dev / code-review / commit-commands / context7 |
| [research](../.claude/profiles/research.md) | 論文・調査・分析 | 軸 + Web リサーチ・ベクトル DB・ML ハブ・Python LSP |
| [system-dev](../.claude/profiles/system-dev.md) | システム開発・コーディング | 軸 + LSP・E2E・横断検索・セキュリティスキャン、`unityMCP` |
| [writing](../.claude/profiles/writing.md) | 執筆・ドキュメント | 軸 + ブランド指針・編集・SEO 系 |
| [design](../.claude/profiles/design.md) | UI/UX・デザインシステム・Figma Slides | 軸 + frontend-design、`figma` MCP |

各プロファイルが有効化するプラグインの正確な集合は、そのプロファイル MD の frontmatter `enabled_plugins` / `enabled_mcp` が source of truth である（`docs/CATALOG.md` の `profiles:` は skill / subagent / command の退避判定にのみ使う）。

旧 9 プロファイル（web-dev / data-analysis / project-mgmt / business / devops ほか）は `.claude/profiles/_archived/` へ退避済み。

## 同梱スキルのカテゴリ

`.claude/skills/` 配下は 4 カテゴリに実体があり、3 カテゴリは空の placeholder。件数の詳細は [CATALOG.md](CATALOG.md) と [CATALOG.html](CATALOG.html) を参照。

| カテゴリ | 概要 |
|---|---|
| dev | massgen（マルチエージェント呼出し） / unity-development（Unity MCP 操作の規約） |
| document | docx / pdf / pptx / xlsx / doc-coauthoring（Office フォーマット、source-available） |
| research | agent-council（サブ skill 6 件込み） / domain-name-brainstormer / notebooklm-integration |
| design | figma-integration（Figma 連携・デザインシステム・Figma Slides） |
| meta / project / write | 空 placeholder。`/init-project` 時に profile 固有 skill を入れ直す枠 |

プラグインで代替できるものは `.claude/skills/_archived/` へ退避済み。残置理由は各 skill の `KEPT.md` にある。

## カスタムプロファイルを追加する

```bash
cp .claude/profiles/general.md .claude/profiles/my-custom.md
```

`my-custom.md` を編集して以下を記述する:

- frontmatter の `name` / `description` / `enabled_plugins` / `enabled_mcp` / `scaffold`
  - `enabled_plugins` は `name@marketplace` 形式の YAML list
  - `enabled_mcp` は `.mcp.json` のサーバ名
  - `scaffold` はリポジトリ直下から見た作業ディレクトリの YAML list（例: `src` / `tests` / `docs`）。`/init-project` のステップ 10 が `mkdir` する。既存ディレクトリには触らないので、後から項目を足しても安全である
- 本文に行動指針（このプロファイルで Claude にどう動いてほしいか）

本文はそのまま `CLAUDE.md` の冒頭に差し込まれる。ディレクトリ構造を本文にも書くと `scaffold` と二重管理になるため、frontmatter だけに持たせる。

作成後は `/init-project my-custom` で指定できる。`--list-profiles` にも自動で載るため、コマンド側の選択肢を書き換える必要はない。

## 複合プロファイル

複数の用途を兼ねる場合は、メインのプロファイルを選んだうえで:

- 追加したいプラグインは `.claude/settings.json` の `enabledPlugins` に `true` を足す
- 退避された skill / subagent は `.claude/<kind>/_archived/` から手動で戻し、`/catalog-sync` を実行する
- `CLAUDE.md` の末尾に「リサーチ機能も併用する」等の方針を追記する

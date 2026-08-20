# 外部統合プラグイン インストールガイド

`.claude/skills/` には含まれず、`/plugin install` で各ユーザー環境に追加するプラグインの一覧と手順。

## なぜテンプレートに同梱されていないか

外部統合プラグイン（github, slack, notion, brand-voice 等）は:
- ネットワーク接続・認証（API キー / OAuth）が必要
- ユーザー個別の設定が必要
- 公式マーケットプレイス経由の自動更新が望ましい

そのため、テンプレートに同梱せず `/plugin install` で各環境に導入する設計です。


## マーケットプレイス追加

### 公式（自動登録）

`claude-plugins-official` は Claude Code に自動登録されています（追加不要）。

```
/plugin install <plugin-name>@claude-plugins-official
```

### ナレッジワーク系（**business** プロファイル必須）

31〜36（brand-voice, marketing, sales, legal, finance, productivity）を使う場合:

```
/plugin marketplace add anthropics/knowledge-work-plugins
```

### コミュニティ製

```
/plugin marketplace add owner/repo
```

---

## プロファイル別推奨インストールコマンド

> ⚠️ **3〜5 個推奨**。一度に多く入れずに、必須のものから絞ること。

### writing
```
/plugin install brand-voice@knowledge-work-plugins        # 初回は marketplace add が必要
/plugin install productivity@knowledge-work-plugins
/plugin install context7@claude-plugins-official
/plugin install notion@claude-plugins-official
```

### web-dev
```
/plugin install frontend-design@claude-plugins-official
/plugin install superpowers@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install typescript-lsp@claude-plugins-official    # 言語に合わせて選択
/plugin install pyright-lsp@claude-plugins-official
/plugin install rust-lsp@claude-plugins-official
/plugin install ruby-lsp@claude-plugins-official
/plugin install chrome-devtools@claude-plugins-official
/plugin install playwright@claude-plugins-official
/plugin install sourcegraph@claude-plugins-official
/plugin install github@claude-plugins-official
/plugin install supabase@claude-plugins-official
```

### research
```
/plugin install context7@claude-plugins-official
/plugin install firecrawl@claude-plugins-official
/plugin install sourcegraph@claude-plugins-official
/plugin install productivity@knowledge-work-plugins
```

### data-analysis
```
/plugin install data-engineering@claude-plugins-official
/plugin install amplitude@claude-plugins-official
/plugin install clickhouse@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
```

### design
```
/plugin install frontend-design@claude-plugins-official
/plugin install playwright@claude-plugins-official
/plugin install chrome-devtools@claude-plugins-official
/plugin install figma@claude-plugins-official
```

### project-mgmt
```
/plugin install productivity@knowledge-work-plugins
/plugin install linear@claude-plugins-official
/plugin install slack@claude-plugins-official
/plugin install github@claude-plugins-official
```

### general
```
/plugin install superpowers@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install github@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
```

### business（要 `marketplace add anthropics/knowledge-work-plugins`）
```
/plugin marketplace add anthropics/knowledge-work-plugins   # 初回のみ

/plugin install brand-voice@knowledge-work-plugins
/plugin install marketing@knowledge-work-plugins
/plugin install sales@knowledge-work-plugins
/plugin install legal@knowledge-work-plugins
/plugin install finance@knowledge-work-plugins
/plugin install productivity@knowledge-work-plugins
```

### devops
```
/plugin install deploy-on-aws@claude-plugins-official
/plugin install pagerduty@claude-plugins-official
/plugin install sentry@claude-plugins-official
/plugin install vercel@claude-plugins-official
/plugin install github@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
/plugin install mintlify@claude-plugins-official
```

---

## 36 選プラグイン早見表

| # | ID | カテゴリ | マーケット |
|---|---|---|---|
| 01 | frontend-design | 公式 | claude-plugins-official |
| 02 | superpowers | 公式 | claude-plugins-official |
| 03 | context7 | 公式 | claude-plugins-official |
| 04 | code-review | 公式 | claude-plugins-official |
| 05 | security-guidance | 公式 | claude-plugins-official |
| 06 | commit-commands | 公式 | claude-plugins-official |
| 07 | feature-dev | 公式 | claude-plugins-official |
| 08 | plugin-dev | 公式 | claude-plugins-official |
| 09-12 | typescript-lsp / pyright-lsp / rust-lsp / ruby-lsp | LSP | claude-plugins-official |
| 13 | ralph-loop | 自律 | claude-plugins-official |
| 14 | chrome-devtools | 自律 | claude-plugins-official |
| 15 | playwright | 自律 | claude-plugins-official |
| 16 | firecrawl | 検索 | claude-plugins-official |
| 17 | sourcegraph | 検索 | claude-plugins-official |
| 18 | clickhouse | データ | claude-plugins-official |
| 19 | data-engineering | データ | claude-plugins-official (パートナー) |
| 20 | amplitude | 解析 | claude-plugins-official |
| 21 | vercel | DevOps | claude-plugins-official |
| 22 | deploy-on-aws | DevOps | claude-plugins-official |
| 23 | pagerduty | DevOps | claude-plugins-official |
| 24 | mintlify | DevOps | claude-plugins-official |
| 25 | github | 連携 | claude-plugins-official |
| 26 | slack | 連携 | claude-plugins-official |
| 27 | sentry | 連携 | claude-plugins-official |
| 28 | linear | 連携 | claude-plugins-official |
| 29 | supabase | 連携 | claude-plugins-official |
| 30 | stripe | 連携 | claude-plugins-official |
| 31 | brand-voice | ナレッジワーク | **knowledge-work-plugins** |
| 32 | marketing | ナレッジワーク | **knowledge-work-plugins** |
| 33 | sales | ナレッジワーク | **knowledge-work-plugins** |
| 34 | legal | ナレッジワーク | **knowledge-work-plugins** |
| 35 | finance | ナレッジワーク | **knowledge-work-plugins** |
| 36 | productivity | ナレッジワーク | **knowledge-work-plugins** |

⚠️ プラグイン ID は時期によって変更される場合があります（例: 旧 `plugin-toolkit` → `plugin-dev`、旧 `ralph-wiggum` → `ralph-loop`、旧 `aws-deploy` → `deploy-on-aws`）。`/plugin` の Discover タブで検索して正確な ID を確認してください。

---

## 補助プラグイン（36 選外）

ガイド 36 選には含まれないが、テンプレ既存資産として推奨できるもの:

| ID | 用途 |
|---|---|
| gitlab | GitLab 統合（web-dev） |
| firebase | Firebase 統合（web-dev） |
| jira | Jira チケット管理（project-mgmt） |
| confluence | Confluence ページ操作（project-mgmt） |
| asana | Asana タスク管理（project-mgmt） |
| notion | Notion ページ操作（writing / project-mgmt / business） |
| figma | Figma デザイン読み取り（design） |
| gopls-lsp | Go LSP（web-dev） |

---

## インストール済みプラグインの管理

```
/plugin list                # 一覧表示
/plugin disable <name>      # 無効化（コンテキスト節約）
/plugin uninstall <name>    # アンインストール
/plugin marketplace update  # マーケットプレイス更新
```

> 💡 各プラグインは**コンテキストトークンを消費**します。多いほどオーバーヘッドが増えるため、**3〜5 個が最適**。使わないものは `/plugin disable` で無効化を。

---

## トラブルシューティング

### プラグインが認識されない
- `/plugin list` で確認
- Claude Code を再起動
- マーケットプレイスを更新: `/plugin marketplace update`

### 認証エラー
- 各プラグインの README を参照（必要なスコープ・トークン形式を確認）
- API キー・OAuth 設定が必要な場合あり
- **本プロジェクトの方針**: 認証情報は `.claude/settings.local.json` または `.env` に格納（共に `.gitignore` 対象）。`~/.claude/settings.json` への直書きや `claude mcp add --scope user` は避ける
- OAuth 系プラグイン（Notion / Slack / Linear / Stripe / GitHub 等）は Local scope で `/plugin install` し直すと個別認証フローが始まる
- MCP サーバの API キーは `.mcp.json` の `env` フィールドから `${VAR}` で参照し、実値は `.env` に置く
- 詳細は [docs/PLUGIN_INSTALL_SCOPE.md](PLUGIN_INSTALL_SCOPE.md) の「本プロジェクトの認証スコープ方針」を参照

### LSP プラグインで補完が効かない
- 対象言語のランタイムがインストール済みか確認（Python, Node.js, Rust, Ruby 等）
- プラグインの設定で言語サーバーのパスを指定する必要がある場合あり

### `knowledge-work-plugins` が見つからない
- 先に `/plugin marketplace add anthropics/knowledge-work-plugins` を実行
- マーケット追加後に `/plugin install <name>@knowledge-work-plugins` で導入

---

## 参考

- 全カタログ: [claude.com/plugins](https://claude.com/plugins)
- 公式マーケット: `/plugin` コマンドで UI 検索
- プラグイン提出フォーム: claude.ai/settings/plugins/submit

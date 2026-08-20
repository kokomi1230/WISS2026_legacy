# プラグインインストールスコープガイド

Claude Code でプラグインをインストールする際に表示されるスコープ選択（User / Project / Local）の挙動と、`.claude/settings.json` への影響をまとめたガイド。とくに **"Install for all collaborators on this repository (project scope)"** を選んだ場合に何が起きるかを中心に解説する。

---

## "Install for all collaborators on this repository (project scope)" を選んだ場合の動作

### 何が起きるか

プロジェクトのルートにある **`.claude/settings.json`** に、プラグインの有効化設定が書き込まれる。

```json
{
  "enabledPlugins": {
    "frontend-design@claude-plugins-official": true
  }
}
```

このファイルは **Git でコミット・共有される**ことが前提のファイル。リポジトリをクローンした全コラボレーターに設定が共有される。

### コラボレーター側での動作フロー

1. リポジトリをクローン（または `git pull`）して Claude Code を起動する
2. フォルダを「信頼（trust）」すると、Claude Code が `.claude/settings.json` の内容を読み取り、**プラグインのインストールを促すプロンプト**が表示される
3. 同意すれば `frontend-design@claude-plugins-official` がインストールされる
4. `/reload-plugins` を実行するとプラグインが有効化される

---

## スコープ別の保存先と共有範囲

| スコープ | 保存先 | Git 共有 | 適用対象 |
|---|---|---|---|
| User scope | `~/.claude/settings.json` | 共有なし | 自分のすべてのプロジェクト |
| **Project scope** | **`.claude/settings.json`** | **共有あり** | **このリポジトリの全コラボレーター** |
| Local scope | `.claude/settings.local.json` | 共有なし | 自分のみ・このリポジトリのみ |

ポイント:

- **User scope** はマシン単位の個人設定。所属プロジェクト横断で常に使うプラグインを入れる場所。
- **Project scope** はチーム標準を強制する場所。コミット必須のプラグインを宣言する。
- **Local scope** は同じリポジトリで個人だけが試したいプラグインを入れる場所。`.gitignore` 既定対象。

---

## 本テンプレートの方針: 導入は user scope に一元化・有効化はプロジェクト差分

本テンプレート（およびコピー先プロジェクト）では、プラグインを次の 3 層で扱う。**「まず全プラグインを user scope で導入し、そこから有効化をプロジェクトごとに最適化する」** モデル。

| 層 | 保存先 | 内容 |
|---|---|---|
| 導入層（user scope） | `~/.claude/settings.json` ＋ `~/.claude/plugins/installed_plugins.json` | 全プラグインを user scope で install。**core** は enabled、**extra** は install して disabled |
| 最適化層（project scope） | `.claude/settings.json` | core からの **差分のみ**。extra を `true`／不要な core を `false`。それ以外は user 層を継承 |
| 認証層（local scope） | `.claude/settings.local.json` | OAuth サービス連携プラグインの有効化＋認証（各自・各マシン） |

source of truth はマニフェスト `.claude/plugins-user-scope.json`（`marketplaces` / `core` / `extra` / `auth_local_only`）。

### 導入手順（新規マシン / コピー直後）

```bash
# 1. ユーザースコープ資産（skill / subagent / command / scripts / statusline）を配置
bash .claude/scripts/setup-user-scope.sh

# 2. 秘匿情報を埋める
cp user-scope/.env.example ~/.claude/.env

# 3. 全 marketplace + 全プラグインを user scope で導入（冪等。--check で dry-run）
bash .claude/scripts/setup-plugins.sh

# 4. プロジェクトの有効化差分を生成
/init-project <profile>
```

手順 1 と 3 は独立した層を扱う。**`setup-user-scope.sh` は資産（ファイル）を、`setup-plugins.sh` はプラグインの install / enable を担当する。** 前者は `enabledPlugins` / `extraKnownMarketplaces` に一切触れないため、実行順は問わないし何度実行しても互いを壊さない。

`setup-plugins.sh` は core を enabled、extra を installed-but-disabled にする。認証 OAuth 系（`auth_local_only`）は導入対象外で、各プロジェクトの local scope で各自インストール・認証する。

`setup-user-scope.sh` は原本 `user-scope/` から設定ディレクトリへの **一方向配置** で、逆方向の読み戻しはしない。`--check` で dry-run、`--diff` で drift 検出（drift ありで終了コード 2）。設定ディレクトリの解決順は `CLAUDE_CONFIG_DIR` → Windows は `%USERPROFILE%\.claude` → `$HOME/.claude`。

旧モデルでは各プロジェクトの `.claude/settings.json` に約 50 個の true/false マップを直書きし install も project scope に紐付いていたが、新モデルでは install を user scope に集約し、project 側は差分だけを残す。コピー / 別マシンでも `setup-plugins.sh` だけで全プラグインが揃う。

---

## 認証スコープ方針

**秘匿情報・OAuth 認証だけ** を user scope に置かず、**プラグインの install / enable フラグは user scope に置いてよい**（秘匿情報を含まないため）。複数アカウントの取り違えと `~/.claude/` への秘匿情報流入を防ぐためのルール。

### 4 つのルール

#### ルール 1: OAuth プラグインも user scope で install（認証はマシン共通・各自）

OAuth ベースのサービス連携プラグイン（Notion / Slack / GitHub / Linear / Stripe / Supabase / Sentry / Vercel / Amplitude / ClickHouse / PagerDuty など）も、他のプラグインと同じく **user scope で install** する（`setup-plugins.sh` が一括導入）。

- マーケットプレイスのプラグインは user scope に入れても、project `.claude/settings.json` の `enabledPlugins` で **プロジェクトごとに ON/OFF できる**（project の `false` が user の `true` を上書きし、同梱 MCP サーバも停止する。公式仕様）。
- OAuth 認証セッションはそもそも **マシン共通**（`~/.claude.json`）に保存されるため、local scope に置いても「アカウント隔離」効果は実質ない。よって local に分散させる意味は薄く、user scope に集約して project で有効化を制御する方が一貫する。
- 本テンプレートでは `notion` を core（user 既定 ON）、その他 OAuth を extra（user install・既定 OFF）に分類（マニフェスト `.claude/plugins-user-scope.json`）。利用したいプロジェクトで `enabledPlugins: {"slack@...": true}` のように有効化する。
- **秘匿情報だけは別**: API キー・トークン・サービスアカウント JSON は `~/.claude` に置かず、`.env` / `.claude/settings.local.json`（ともに `.gitignore` 対象）に隔離する（ルール 3・4）。

複数アカウントを厳密に出し分けたい特殊ケースでは、従来どおり当該プラグインを project で `false` にしたうえで local install する運用も可能。

#### ルール 2: 生 MCP サーバは `.mcp.json` で宣言し、有効化は許可リスト

unity / figma などプラグインに同梱されない **生の MCP サーバ** は、user scope（`claude mcp add --scope user`）に登録すると **全プロジェクトで常時ロードされ、プロジェクト個別の無効化ができない**（`disabledMcpjsonServers` は `.mcp.json` 定義サーバ専用で、user scope サーバには効かない。公式仕様）。重いツール群（unity は 268 tools）を無関係なプロジェクトに読ませると context を圧迫する。

そこで本テンプレートでは生 MCP を **project の `.mcp.json` に定義し、profile に応じた `enabledMcpjsonServers` 許可リストで per-project に opt-in** する（`/init-project` が `apply_profile.py` 経由で書き込む）。

- unity は anklebreaker 実装（name `unityMCP`）に統一。`system-dev` プロファイルで `enabledMcpjsonServers: ["unityMCP"]`。
- figma は http MCP（name `figma`）。`design` プロファイルで `enabledMcpjsonServers: ["figma"]`。
- profile の `enabled_mcp:` frontmatter がこの許可リストの source of truth。未承認のサーバはロードされない。

API キー方式の MCP は、認証情報を `.env`（`.gitignore` 対象）から環境変数で渡す。

`.mcp.json` の例:

```json
{
  "mcpServers": {
    "stripe": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@stripe/mcp-server"],
      "env": {
        "STRIPE_API_KEY": "${STRIPE_API_KEY}"
      }
    }
  }
}
```

`.env`（コミットしない）:

```
STRIPE_API_KEY=sk_test_...
```

コラボレーターには `.env.example`（キー名だけ・値は空）を共有し、各自で `.env` を作成してもらう。

#### ルール 3: シークレットは `settings.local.json` または `.env`

API キー・OAuth トークン・サービスアカウント JSON などのシークレットは以下のいずれかに保存:

- `.claude/settings.local.json` — Claude Code 固有の設定と同居させたい場合
- `.env` — シェル環境変数として読み込ませたい場合（`.mcp.json` などから `${VAR}` で参照）

どちらも `.gitignore` 対象（テンプレート既定で除外済み）。

#### ルール 4: `~/.claude/` への **秘匿情報** 直書き禁止（install / enable フラグは可）

- `~/.claude/settings.json` と **`~/.claude.json`** への API キー / トークン直書きは避ける。MCP サーバの `env` には `${VAR}` 参照だけを書く（原本は `user-scope/mcp-servers.user.json`）
- `claude mcp add --scope user` で認証情報付き MCP を登録するのも避ける（プロジェクト横断で漏れる）
- 実値の置き場所は `~/.claude/settings.local.json` の `env` ブロック（MCP サーバへ渡る）と `~/.claude/.env`（スクリプトが自力で読む）。どちらも `.gitignore` 対象で、`setup-user-scope.sh` は読み書きしない
- `/doctor` が `~/.claude.json` / `~/.claude/settings.json` の実トークン直書きを critical として検出する
- 一方で **プラグインの install と enable フラグ**（`enabledPlugins` の true/false、`installed_plugins.json`）は秘匿情報を含まないため **user scope に置いてよい**（むしろ本テンプレートの推奨）

理由: 個人プロジェクトと業務プロジェクトで異なるアカウントを使う場面、グローバルに秘匿情報を置くと取り違えるリスクが高い。秘匿情報だけプロジェクトに閉じれば事故を起こしにくい。

### 有効化フラグの扱い

`enabledPlugins` の有効化フラグは秘匿情報を含まないため、user scope（コア）にも project scope（差分）にも自由に置ける。本テンプレートでは **core を user scope で enabled・extra を user scope で disabled とし、各プロジェクトは差分だけ** を `.claude/settings.json` に置く（前掲「3 層モデル」）。

認証が必要なプラグイン（notion / slack / github / linear / supabase / stripe / sentry / vercel / amplitude / clickhouse / pagerduty 等）も **user scope で install** する（マニフェスト `.claude/plugins-user-scope.json` の `core` / `extra`）。`notion` は core（既定 ON）、他は extra（既定 OFF）。OAuth 認証はマシン共通かつ初回利用時に各自実施するため、有効化フラグを user scope に置いても秘匿情報は漏れない。プロジェクトで使わないものは project の `enabledPlugins:false` で無効化できる。

### コラボレーター用オンボーディング

新しいメンバーがこのリポジトリに参加した場合の認証セットアップ:

1. `git clone` してフォルダを Claude Code で開く（trust プロンプトに同意）
2. `.env.example` があれば `.env` にコピーし、自分の API キーで埋める
3. `.claude/settings.local.json.example` を `.claude/settings.local.json` にコピーして必要な local 設定を追加
4. 認証が必要な MCP は `authenticate` ツールを実行（OAuth ブラウザフロー）して各自のアカウントで紐付け
5. 追加で個人専用プラグインを入れる場合は Local scope で `/plugin install`

各自が一度だけ実施すれば、以後はマシンに残った認証情報で接続が維持される。

---

## 注意点

- `.claude/settings.json` を `.gitignore` に入れていない限り、**コミットして共有される**。チーム全体に影響するため、信頼できるプラグインのみ使用すること。
- Anthropic はプラグインに含まれる MCP サーバーやコードの安全性を保証していない。インストール前にプラグインのホームページで内容（権限・実行コマンド・MCP 接続先など）を確認することが推奨されている。
- プラグイン名は `<plugin>@<marketplace>` 形式で `enabledPlugins` キーに入る。マーケットプレイス側が削除・改名されると、コラボレーター側のインストールプロンプトが失敗する可能性がある。
- 設定変更後にプラグインが反映されない場合は `/reload-plugins` を実行する。

---

## 参考

- [公式] [Discover and install prebuilt plugins through marketplaces — Claude Code Docs](https://code.claude.com/docs/en/discover-plugins)
- [公式] [Claude Code settings — Claude Code Docs](https://code.claude.com/docs/en/settings)
- [公式] [Plugins reference — Claude Code Docs](https://code.claude.com/docs/en/plugins-reference)

---

## 関連ドキュメント

- [docs/PLUGIN_INSTALL_GUIDE.md](PLUGIN_INSTALL_GUIDE.md) — 外部統合プラグインのインストール手順

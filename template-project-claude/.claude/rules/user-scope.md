---
paths:
  - "user-scope/**"
---

# ユーザースコープ資産の編集規約

`user-scope/` は全プロジェクト共通資産の **原本** である。`~/.claude/`（Windows は `%USERPROFILE%\.claude`）は `setup-user-scope.sh` が生成する **配置先＝派生物** であり、同期は一方向で、配置先から原本へ読み戻すことはない。

```
user-scope/                     # 原本（git 追跡）
├─ skills/ agents/ commands/ scripts/ statusline.sh
├─ settings.user.json           # 非プラグイン設定のマージ元
├─ mcp-servers.user.json        # user scope MCP（notion）定義
└─ .env.example                 # 秘匿情報の雛形（実値は置かない）
        ↓ bash .claude/scripts/setup-user-scope.sh
<config-dir>/                   # 配置先（派生物）
```

- **編集は必ず `user-scope/` 側で行い、`setup-user-scope.sh` で配置し直す。** 配置先を直接編集すると次回の配置で失われる（`--diff` で drift を検出できる）
- 配置スクリプトは `enabledPlugins` / `extraKnownMarketplaces`（`setup-plugins.sh` の管理領域）と、`plugins/` `projects/` `.env` `settings.local.json` には触れない
- 設定ディレクトリの解決順は `CLAUDE_CONFIG_DIR` → Windows は `%USERPROFILE%\.claude` → `$HOME/.claude`
- `statusLine` のパスは `__STATUSLINE_SH__` プレースホルダとして原本に持ち、配置時に実環境の絶対パスへ置換される。リポジトリに特定マシンのパスを書かない

## 秘匿情報を原本に置かない

`user-scope/.env.example` は雛形であり実値を書かない。実値は配置先の `.env` に入れる。MCP サーバ定義のトークンは `${NOTION_TOKEN}` のようなリテラル参照にとどめる。

## プロジェクト固有ルールを書かない

全プロジェクトで共有される以上、特定プロジェクトの方針を埋め込むと他プロジェクトへ漏れる。例えば `code-style` skill は言語横断の命名・コメント原則のみを持ち、**コメントを日本語で書く**・**絵文字を使用しない** といった本プロジェクトの方針はリポジトリ側の `CLAUDE.md` が持つ。ユーザースコープ資産は `CLAUDE.md` を読んでプロジェクト規約を優先する作りにする。

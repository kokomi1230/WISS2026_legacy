---
description: テンプレ環境の健全性診断。settings 構文 / catalog drift / user-scope drift / 秘匿情報の直書き / スコープ衝突 / ドキュメントのリンク切れなど 19 項目を一括チェックしてレポートを出力する。
allowed-tools: Read, Glob, Bash(python3 .claude/scripts/doctor.py:*), Bash(bash .claude/scripts/sync-catalogs.sh:*), Bash(bash .claude/scripts/setup-user-scope.sh:*)
argument-hint: "(引数なし) | --json"
profile_relevance:
  - meta
---

# /doctor

テンプレ環境を一括点検して **drift / 不整合 / 設定崩れ** を検出する読み取り専用の診断コマンド。

## 実行

!`python3 .claude/scripts/doctor.py`

`--json` を付けると機械可読な形式で出力する（`$ARGUMENTS` をそのまま渡してよい）。

判定ロジックは `.claude/scripts/doctor.py` にコードとして置いてある。Markdown 側にスニペットを持たないのは、**テストできること**と **`/init-project` のプリフライトが同じ判定を再利用できること**の 2 点が理由である。

## チェック項目

| # | 項目 | 重大度 |
|---|---|---|
| 1 | `.claude/settings.json` の JSON 構文 | critical |
| 2 | `claude` CLI が PATH に在るか | major |
| 3 | user-scope 資産の配置 drift（原本 `user-scope/` との差） | major |
| 4 | プラグインが user scope に install 済みか | major |
| 5 | `node` / `npx` の有無 | minor |
| 6 | `<config-dir>/.env` の有無 | minor |
| 7 | catalog ロックの残置（`.claude/.catalog-sync-lock`） | major |
| 8 | catalog drift（`docs/CATALOG.md` → `docs/CATALOG.html`） | major |
| 9 | `.claude/settings.local.json` の JSON 構文 | major |
| 10 | `enabledPlugins` のキー形式（`name@marketplace`） | major |
| 11 | `_archived/` と active の同名重複 | major |
| 12 | `.mcp.json` が参照する `${VAR}` の未定義 | minor |
| 13 | プロファイル MD の frontmatter（`enabled_plugins` が list か） | major |
| 14 | `settings.json` の hooks が指すスクリプトの実在 | minor |
| 15 | 秘匿情報の直書き（`~/.claude/settings.json` / `~/.claude.json`） | **critical** |
| 16 | statusLine が指すスクリプトの実在 | minor |
| 17 | プロジェクト scope と user scope の同名衝突 | major |
| 18 | ドキュメント内の相対リンク切れ | major |
| 19 | 現プロファイルの baseline plan が noop か | info |

1-6 は `--preflight` でも走る部分集合で、`/init-project` のステップ 0 が使う。

終了コード: `0` = clean / `1` = warning のみ / `2` = 要対応あり。

## 出力の読み方と対処

スクリプトが各項目に `→` で修復コマンドを添えて出す。主なものは以下。

| 検出 | 対処 |
|---|---|
| catalog ロックの残置 | `/catalog-sync`（ロックが残っている間は hook が停止し、drift 判定も無効になる） |
| catalog drift | `/catalog-sync` |
| user-scope drift | `bash .claude/scripts/setup-user-scope.sh`（配置先を直接編集していた場合は、その変更を `user-scope/` へ取り込んでから配置し直す） |
| plugin 未 install | `bash .claude/scripts/setup-plugins.sh` |
| 秘匿情報の直書き | 値を `~/.claude/settings.local.json` の `env` へ移して設定側は `${VAR}` 参照にする。露出したトークンは失効させて再発行する |
| statusLine broken | `bash .claude/scripts/setup-user-scope.sh` |
| スコープ間の同名衝突 | CLAUDE.md「アセットのスコープ方針」で置き場所を決め、片方を削除する |
| リンク切れ | 参照先を実在パスへ直す。退避したドキュメントを指している場合は `docs/_archived/` を参照するか記述ごと削除する |
| archived 重複 | 片方を削除する |

## 注意

- 本コマンドは **書き換えを行わない**（read-only）。修正は別コマンド / 手動操作
- 秘匿情報チェックは `~/.claude/settings.json` と `~/.claude.json` のみを見る。`.env` / `settings.local.json` は実値の正しい置き場所なので対象外
- ユーザースコープの資産も検査対象（項目 3・15・16・17）。原本が `user-scope/` として本リポジトリの管理下にあるため。ただし判定は配置状態・衝突・秘匿情報に限り、資産の中身は見ない
- user scope 側のプラグイン導入状態は項目 4 で見るが、その有効化フラグ（`~/.claude/settings.json` の `enabledPlugins`）は `setup-plugins.sh` の管理領域なので判定しない
- リンクチェックは `_archived/` と vendored skill を除外する（原典のまま保つ方針のため）

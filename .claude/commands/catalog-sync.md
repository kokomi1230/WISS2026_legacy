---
description: プロジェクト環境（.claude/agents, .claude/skills, .claude/commands, settings.json）を読み取り、新規エントリを docs/CATALOG.md に追記、ディスクに無いエントリを削除、status を更新、docs/CATALOG.html を再生成。
allowed-tools: Bash(bash .claude/scripts/sync-catalogs.sh:*)
argument-hint: "[--check] (drift 検出のみ) / [--no-discover] (discovery スキップ)"
profile_relevance:
  - meta
  - general
---

# /catalog-sync

現在のプロジェクト環境を統合カタログに **add + delete** で反映します。

## 動作

| ステップ | 入力 | カタログへの作用 |
|---|---|---|
| 1 | `.claude/agents/<name>.md` | 未登録なら subagent エントリを **追加**、登録済みなら `[active]`。ディスクに無い既存 subagent は **削除** |
| 2 | `.claude/skills/<cat>/<name>/SKILL.md` | 未登録なら skill エントリを **追加**（frontmatter から type/description/source/tags/profile_relevance 抽出）、登録済みなら `[active]`。ディスクに無い既存 skill は **削除**。frontmatter 不完全（name/description 欠落）は skip + stderr 警告 |
| 3 | `.claude/commands/<name>.md` | 未登録なら command エントリを **追加**、登録済みなら `[active]`。ディスクに無い既存 command は **削除** |
| 4 | `.claude/settings.json` `enabledPlugins` | 既知 plugin に `[enabled]` 印（plugin は disk に物理ファイル無いため削除対象外） |
| 5 | `docs/CATALOG.md` を更新 | 上記の差分を反映 |
| 6 | `docs/CATALOG.html` を再生成 | 既存 build パイプライン |

## 削除動作

- 対象 kind: `subagent` / `skill` / `command`（disk に物理ファイルがある種類のみ）
- 対象外: `plugin`（外部システム、catalog は reference list として残す。marketplace plugin / standalone MCP の両方とも `kind: plugin`）
- 削除前に stderr に `removing N entries: ...` を出力（透明性）
- 削除対象は `#### <name>` 行とその直前の `<!-- AUTO-DISCOVERED -->` コメントを含むエントリブロック全体
- ロールバック必要時は git で対応（catalog 内に backup は持たない）

## 追加動作

- discovery で見つけた未登録エントリは、kind ごとに該当 H2 セクション（`## subagent 一覧` / `## コマンド一覧` / `## スキル一覧`）の **末尾**へ追記
- カテゴリは frontmatter から決定（skill の `type` フィールド等）。サブセクション（`### <category>`）が存在しなければ自動で作成
- 追加ブロックには `<!-- AUTO-DISCOVERED YYYY-MM-DD: <name> -->` コメントを付与し、自動由来と判別できるようにする

## いつ実行するか

- `.claude/agents/` / `.claude/skills/` / `.claude/commands/` に追加・削除を行った後
- `.claude/settings.json` の `enabledPlugins` を変えた後
- 外部編集（vim, git pull, mv 等）でソースを変更した後
- 自動 hooks の同期が失敗・スキップされた疑いがある時

## 実行

!`bash .claude/scripts/sync-catalogs.sh`

## オプション

- `--check`: drift 検出のみ（書き込みなし）。CI 用、同期=0 / drift=2
- `--no-discover`: discovery をスキップし、既存 docs/CATALOG.md → HTML のみ生成（hook 互換モード）

## 自動 hooks では同期されないケース

`.claude/hooks/catalog-sync.sh` は Claude Code の Write/Edit/MultiEdit ツール呼び出しでしか発火しません。下記は手動 `/catalog-sync` が必須:

1. Claude Code 外部からの編集（vim / VS Code 直編集 / `git pull` / `cp` / `mv` / `rm`）
2. CI / pre-commit / npm script 等の外部プロセス変更
3. ディレクトリ単位の操作（`mv` で MD を移動など）
4. アーカイブ展開・`curl`・`git clone` で MD を追加
5. hook スクリプト自体の実行エラー（python3 不在、I/O 失敗）
6. Claude Code 起動前のオフライン編集
7. `.claude/settings.local.json` で hooks 無効化中
8. 自己再帰スキップ中の連続更新（lock 取得済みの間の取りこぼし）
9. 高速連続編集による競合

---
description: Notion のページをローカルの Markdown ミラー（全プロジェクト共通、既定 ~/.notion-mirror/）へ一方向で pull する。増分同期・削除追従つき。以降の読み取りを Grep / Read で行えるようにし、トークン消費を大きく抑える。
allowed-tools: Bash(python3 ~/.claude/scripts/notion_sync.py:*)
argument-hint: "[--check] (差分件数のみ) / [--dry-run] (対象一覧のみ) / [--full] (全件再取得)"
profile_relevance:
  - research
  - writing
  - general
---

# /notion-sync

Notion の内容をローカルの Markdown ミラーへ **一方向で** 取り込みます。Notion を「人間が書く・探す・読む」側、ミラーを「エージェントが走査する」側と役割分担するための同期コマンドです。

## 前提

`.env` に `NOTION_TOKEN` が必要です。未設定の場合は API を叩かずセットアップ手順を案内して終了します（終了コード 3）。手順は `notion-knowledge-base` skill の `reference.md` を参照。

## 動作

| ステップ | 処理 |
|---|---|
| 1 | `/search` でインテグレーションに共有された全ページを列挙（メタ情報のみ、安価） |
| 2 | `_manifest.json` と `last_edited_time` を突き合わせ、更新されたページだけを抽出 |
| 3 | 対象ページのブロックを再帰取得し、frontmatter 付き Markdown へ変換して書き出し |
| 4 | manifest にあって Notion 側に無いページのローカルファイルを削除 |
| 5 | manifest を更新し、空になったディレクトリを削除 |

列挙は毎回全件、本文取得だけを増分に絞る設計です。これにより削除の検出を保ちつつ、通信量を抑えます。

## 出力先

既定は `~/.notion-mirror/`、`NOTION_MIRROR_DIR` で上書きできます。**全プロジェクトが同一のミラーを共有します**（知識コーパスはリポジトリ単位ではなく 1 つであるため）。

```
~/.notion-mirror/
  _manifest.json
  <DB 名>/<種別>/<日付>-<タイトル>-<短縮ID>.md
  pages/<タイトル>-<短縮ID>.md
```

frontmatter には Notion のプロパティ（種別・状態・タグ・relation 等）がそのまま入ります。設計の詳細は `notion-knowledge-base` skill の `reference.md` を参照。

## 実行

!`python3 ~/.claude/scripts/notion_sync.py $ARGUMENTS`

## オプション

- `--check`: 差分件数のみ表示（書き込みなし）。差分ありで終了コード 2、同期済みで 0
- `--dry-run`: 取得 / 削除の対象一覧を表示（書き込みなし）
- `--full`: manifest を無視して全ページを再取得。変換ロジックを更新した後に使う
- `--quiet`: 進捗ログを抑制

## 重要な制約

- **同期が書いた領域は手で編集しない。** 派生物であり、次の pull で上書きされます。編集は Notion 側で行ってください（`_` 始まりの `_md/` `_html/` は同期の管理外なので対象外です）
- **同期は Notion → ローカルの一方向のみ。** ローカルからの push は行いません。AI の生成物は Notion へ書き（`/notion-digest` 等）、その後に本コマンドでミラーへ反映します
- **`rm -rf ~/.notion-mirror` は使わないでください。** `_md/` に解説資料の原本が、`_html/` に清書版が入っています。同期が書いた領域を取り直したいときは `--full` を使います（manifest 記載のパスだけを取り直すため、`_` 始まりの領域は無傷です）

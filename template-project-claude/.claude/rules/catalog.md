---
paths:
  - "docs/CATALOG.md"
  - ".claude/settings.json"
---

# 統合カタログの編集規約

`docs/CATALOG.md` はプラグイン・スキル・subagent などすべての拡張資産を管理する source of truth である。`docs/CATALOG.html` はそこから生成される派生物なので、**HTML を直接編集しない**。

```
CATALOG.md  (手編集、source of truth)
+ .claude/settings.json (enabledPlugins → [enabled] 自動反映)
  └─→ docs/CATALOG.html  (人向けフィルタ可能 UI)
```

各エントリは `- kind: plugin | skill | subagent`（既定 `plugin`）で種類を判別する。フィールド仕様は `docs/CATALOG.md` 末尾「エントリの追加方法」を参照。

ユーザースコープ（`~/.claude/`）の資産はカタログに登録しない。カタログはプロジェクトスコープ資産のカタログである。

## 同期の実行

- 自動: Write / Edit / MultiEdit が `docs/CATALOG.md` / `.claude/settings.json` を触ると `.claude/hooks/catalog-sync.sh` が発火し HTML を再生成する。`.claude/.catalog-sync-lock` で自己再帰を抑止する
- 手動: `/catalog-sync`（または `bash .claude/scripts/sync-catalogs.sh`）
- 検証: `bash .claude/scripts/sync-catalogs.sh --check`（書込なし、drift ありで終了コード 2）

## 手動 `/catalog-sync` が必要になるケース

hooks は Claude Code のツール呼び出しでしか発火しないため、以下では取りこぼす。**カタログを Claude Code 以外の手段で変更したら必ず手動同期する。**

1. Claude Code 外部の編集（vim / VS Code 直編集 / `git pull` / `cp` / `mv` / `rm`）
2. CI / pre-commit / npm script など外部プロセスからの変更
3. `mv` などディレクトリ単位の操作（カタログを移動）
4. アーカイブ展開・`curl`・`git clone` で MD を追加
5. hook スクリプト実行エラー（python3 不在、I/O 失敗）
6. オフライン編集（Claude Code 起動前）
7. `.claude/settings.local.json` で hooks 無効化中
8. lock 取得中の連続更新（自己再帰スキップ時の取りこぼし）
9. 高速連続編集による競合

いずれも `/catalog-sync` で完全再生成できる。CI で `sync-catalogs.sh --check` を走らせれば drift を検出できる。

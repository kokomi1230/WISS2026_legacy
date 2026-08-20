---
description: 既に初期化済みのプロジェクトのプロファイルを別プロファイルに切り替える。/init-project の再実行と同等だが、仕様文の再入力をスキップして baseline のみで切替する軽量フロー。
allowed-tools: Read, AskUserQuestion, Bash(python3 .claude/scripts/apply_profile.py:*), Bash(bash .claude/scripts/sync-catalogs.sh:*), Bash(mkdir:*), Bash(mv:*)
argument-hint: "[target-profile: general|research|system-dev|writing]"
profile_relevance:
  - meta
---

# /profile-switch

`/init-project` で確定済みのプロファイルを **別プロファイルに切り替える** コマンド。仕様文の再入力をスキップし、CATALOG の `profiles:` タグだけで機械的に判定する軽量フロー。

## 動作

| ステップ | 内容 |
|---|---|
| 1 | 現プロファイルを CLAUDE.md 1 行目（`# <プロジェクトディレクトリ名> (<profile>)`）から検出 |
| 2 | 引数 `$1` または AskUserQuestion で切替先を選択 |
| 3 | `apply_profile.py --plan` で baseline plan を生成し、diff（enable / disable / archive / restore）を表示 |
| 4 | AskUserQuestion で承認 / 中止 |
| 5 | 承認なら `--apply` + `--write-claude-md` で適用 |
| 6 | `bash_commands` の `mv` 実行（kind 別に承認プロンプト最大 3 回） |
| 7 | `sync-catalogs.sh` で HTML 再生成 |

## いつ使うか

- 進捗の途中で用途が変わった（system-dev で始めたが論文も書くようになった → research に切替）
- writing から general に戻して身軽にしたい
- system-dev に切り替えて LSP・Playwright を有効化したい

## /init-project との違い

| 観点 | /init-project | /profile-switch |
|---|---|---|
| 仕様文の入力 | あり（spec-aware 上書き） | なし（baseline のみ） |
| CLAUDE.md 書き換え | 全置換 | プロファイル行のみ書換 |
| 想定回数 | 1 回（初期化時） | 何度でも |
| 想定所要 | 5〜10 分 | 1 分以内 |

## 実行手順

### ステップ 1: 現プロファイル検出

```bash
head -1 CLAUDE.md
```

`# <プロジェクトディレクトリ名> (<profile>)` 形式の末尾の括弧から `<profile>` を抽出する。プロジェクト名はコピー先のディレクトリ名になるため、名前ではなく括弧の中だけを見る。1 行目に `（未初期化）` を含む場合は `/init-project` を先に実行するよう案内して終了。

### ステップ 2: 切替先選択

引数 `$1` が `.claude/profiles/<name>.md` に存在し、かつ現プロファイルと異なればそれを採用。

無ければ AskUserQuestion で 4 択（現プロファイルは選択肢に含めない）:

- **general** — 汎用プロジェクト
- **research** — 論文 / 調査 / 分析
- **system-dev** — システム開発 / コーディング
- **writing** — 執筆 / ドキュメント

### ステップ 3: baseline plan 生成

```bash
python3 .claude/scripts/apply_profile.py --profile <target> --plan
```

JSON の `plugins.enable` / `plugins.disable` / `archive.{skills,agents,commands}` / `already_archived` を読み取り、Claude が以下を集計:

- **新規 enable**: 現状 disable で target で enable される plugin
- **新規 disable**: 現状 enable で target で disable される plugin
- **アーカイブ復活**: `already_archived` のうち、target で `_matches()` 復活するべきものを検出。これは plan の `archive` リストには出ないため、Claude が `already_archived` と `_matches` を別途突き合わせて算出する（簡易には「現 archive 中で `profiles:` に target を含むもの」をリストアップ）

### ステップ 4: 差分提示

以下のフォーマットで diff を user に提示:

```
現プロファイル: <current>
切替先: <target>

[プラグイン]
**目指す:** N 個を新規 enable: A, B, C, ...
**避ける:** M 個を disable: D, E, ...

[アセット]
**目指す:** 復元候補 K 個（手動 mv 必要）:
  - .claude/skills/_archived/<cat>/<name>
**避ける:** 新規 archive L 件:
  - .claude/skills/<cat>/<name>
  - .claude/agents/<name>.md
```

復元候補は **手動 mv が必要** な旨を明示する（apply_profile.py は archive 方向の mv しか生成しないため）。

### ステップ 5: 承認

AskUserQuestion で 3 択:

- **適用する** — plan を実行
- **詳細を見直したい** — plan JSON 全体を表示
- **中止** — 何もせず終了

### ステップ 6: 適用

```bash
python3 .claude/scripts/apply_profile.py --profile <target> --apply --yes
python3 .claude/scripts/apply_profile.py --profile <target> --write-claude-md
```

返却された `bash_commands` の `mkdir -p ...` / `mv ... ; ...` を kind 別に実行。

### ステップ 7: カタログ再生成

```bash
bash .claude/scripts/sync-catalogs.sh
```

### ステップ 8: 完了報告

以下を 5〜8 行でまとめ:

- 移行: `<current>` → `<target>`
- enable 増減 / disable 増減
- archive 増分件数
- 復元手動 mv が必要な件数（あれば該当 mv コマンドを提示）
- 次のアクション: `/plugin enable <name>` で即時反映、または Claude Code 再起動

## 復元手動 mv のヒント

例えば writing → research への切替で `pinecone` 関連 skill を復活させたい場合:

```bash
# archive から戻す
mv .claude/skills/_archived/research/<name> .claude/skills/research/

# カタログ再生成
bash .claude/scripts/sync-catalogs.sh
```

`apply_profile.py` は archive 方向の `mv` しか生成しないため、復活は手動で行う必要がある。今後 `/skill-restore` コマンドで自動化予定（Tier 3）。

## 注意事項

- `.claude/settings.local.json` の `enabledPlugins` は触らない
- standalone MCP (Unity MCP 等の `external (GitHub)`) は `enabledPlugins` 管理外
- 仕様文ベースの細かい調整が必要なら `/init-project <target>` を実行（spec-aware 上書きあり）
- 同一プロファイルへの切替は no-op として `apply_profile.py` 側で検出される（`noop: true`）

---
description: テンプレートをプロジェクト用に初期化。環境プリフライト（新しい PC なら導入まで実施）→ プロファイル選択 + 任意の仕様文を入力 → Claude が CATALOG 全件を読んで推奨プラグイン / アセットを選定 → 承認後に CLAUDE.md 生成・enabledPlugins 書換・非該当アセットを _archived/ へ退避・ディレクトリ整備・README 生成・テンプレート運用資産の削除。
allowed-tools: Read, Edit, Write, AskUserQuestion, Bash(python3 .claude/scripts/doctor.py:*), Bash(python3 .claude/scripts/apply_profile.py:*), Bash(python3 .claude/scripts/detemplate.py:*), Bash(bash .claude/scripts/setup-user-scope.sh:*), Bash(bash .claude/scripts/setup-plugins.sh:*), Bash(bash .claude/scripts/sync-catalogs.sh:*), Bash(mkdir:*), Bash(mv:*), Bash(cp:*)
argument-hint: "[profile] [spec-file-path] (両方とも省略可、対話的に補完。プロファイル一覧は apply_profile.py --list-profiles)"
profile_relevance:
  - meta
---

# /init-project

このテンプレートを **プロファイル + プロジェクト仕様** に合わせてチューニングします。実行内容:

0. **環境プリフライト** — 新しい PC なら user-scope 資産とプラグインを導入してから先へ進む
1. CLAUDE.md のプレースホルダ冒頭を選択プロファイル MD で置換（`## プロジェクト規約` 以降の固定セクションは温存）
2. `.claude/settings.json` の `enabledPlugins` を一括書換
3. 非該当 skill / subagent / command を `.claude/<kind>/_archived/` へ `mv`
4. `docs/CATALOG.html` を再生成
5. プロファイルの `scaffold:` に沿って作業ディレクトリを作成
6. プロジェクト自身の README.md を生成
7. テンプレート運用専用の資産を削除（脱テンプレート化）

**このコマンドはテンプレート本体では完走しない。** ステップ 12 の脱テンプレート化がリポジトリ直下の `.template-origin` を検出して中断する。必ずコピー先で実行する。

**プロファイルのみ指定**した場合は docs/CATALOG.md の `profiles:` タグから機械的に決まります。**仕様文を併せて指定**すると、Claude が docs/CATALOG.md の各プラグイン description と仕様文を突き合わせて baseline を上書きします（仕様に合うものを追加、合わないものを除外）。

`profiles:` に `meta` を含むエントリは「全プロファイル共通インフラ」として常に維持されます。

## 実行手順（Claude が踏むステップ）

### ステップ 0: 環境プリフライト

**プロジェクトの最適化を始める前に、この PC に導入が済んでいるかを判定する。** 新しい PC では資産もプラグインも無いため、最適化だけ走らせても実体の無い設定が残る。

```bash
python3 .claude/scripts/doctor.py --preflight
```

判定は 6 項目（`.claude/settings.json` 構文 / `claude` CLI / user-scope 資産の配置 / プラグインの user scope install / `node`・`npx` / `<config-dir>/.env`）。終了コードは `0` = 導入済み、`1` = 警告のみ、`2` = 要対応。

**終了コード 0**: 何も表示せずステップ 1 へ進む。

**終了コード 1（警告のみ）**: 警告を 1〜2 行で伝え、そのままステップ 1 へ進む。`.env` や `node` の不足は Notion / 生 MCP にしか影響せず、初期化自体は完走できるため止めない。

**終了コード 2（要対応）**: 不足内容をそのまま提示し、AskUserQuestion で 3 択を出す。**「導入して続行」を先頭（推奨）に置く**:

1. **導入して続行**（推奨）— 下記を順に実行し、`--preflight` を再実行して解消を確認してからステップ 1 へ
2. **導入せず続行** — この PC では未導入のまま最適化だけ行う（別マシンで後から導入する前提）
3. **中止** — 何もせず終了する

「導入して続行」を選ばれた場合の実行順:

```bash
bash .claude/scripts/setup-user-scope.sh   # user-scope 資産を <config-dir> へ配置
bash .claude/scripts/setup-plugins.sh      # marketplace + plugin を user scope へ install
python3 .claude/scripts/doctor.py --preflight   # 再判定
```

再判定でまだ要対応が残る場合は、残った項目と修復コマンドを提示して**ユーザーに判断を仰ぐ**（勝手に 3 回以上リトライしない）。`claude` CLI が PATH に無いケースはスクリプトでは解決できないため、その旨を明示する。

`<config-dir>/.env` が無い場合は、導入後に次を案内する（実値の入力はユーザーが行う。Claude がトークンを書かない）:

```bash
cp user-scope/.env.example ~/.claude/.env
```

### ステップ 1: プロファイル選択

引数 `$1` が指定されていればそれを採用。無ければ実体からプロファイル一覧を取得して選択肢を組む:

```bash
python3 .claude/scripts/apply_profile.py --list-profiles
```

返る JSON の `profiles[].name` / `.description` から AskUserQuestion の選択肢を作る。**一覧をこのファイルにハードコードしない**（プロファイルを増減したときに選択肢が実体とずれるため）。

AskUserQuestion は options が最大 4 個までなので、5 件以上ある場合は代表 4 件を出し、残りは自動付与される「Other」でプロファイル名を直接入力してもらう。どれが代表かは `general` を必ず含めたうえで、残りを名前順に選ぶ。

`$1` に `.claude/profiles/<name>.md` が存在しない値（旧プロファイル名 `web-dev` 等）が渡された場合は、`--list-profiles` の結果を示したうえで「`cp .claude/profiles/general.md .claude/profiles/<name>.md` で作成してから再実行してください」と案内して終了する。

### ステップ 2: 仕様文の取得（任意）

引数 `$2` が指定されていればそのファイルパスを読む。無ければ AskUserQuestion で 3 択:

1. **ファイル**: 仕様書 / README / 設計メモのパスを別途聞いて Read
2. **インライン**: AskUserQuestion で 1〜2 段落の自由記述（やりたいこと、技術スタック、対象ユーザー等）
3. **省略**: 仕様文なし、profile-only モード（baseline をそのまま使う）

### ステップ 3: baseline プランを生成

```bash
python3 .claude/scripts/apply_profile.py --profile <X> --plan > /tmp/init-project-baseline.json
```

### ステップ 4: Claude による spec-aware 上書き（仕様文があれば）

仕様文が無ければ baseline をそのまま使う（ステップ 5 へ）。

仕様文がある場合、Claude が以下を行う:

1. `/tmp/init-project-baseline.json` を Read
2. `docs/CATALOG.md` を Read（各エントリの `description` / `tags` / `profiles` をすべて把握）
3. 仕様文と CATALOG エントリを照らし合わせ、以下の判断を行う:
   - **追加すべき plugin**: baseline の `plugins.disable` に居るが仕様に強く合致するものを `enable` に移動（例: 仕様に「Unity VR」と書いてあれば `coplay-unity-mcp` を有効化候補にする — ただし `external (GitHub)` 系は `enabledPlugins` 管理外なので付記のみ）
   - **除外すべき plugin**: baseline の `enable` に居るが仕様と無関係なものを `disable` に移動
   - **保護すべき skill / subagent / command**: baseline の `archive` に居るが仕様に役立つものを除外（archive リストから消す）
   - **追加でアーカイブすべきもの**: baseline では残るが仕様と明らかに無関係なものを `archive` に追加
4. 修正した JSON を `/tmp/init-project-final.json` に Write（baseline と同じ schema を厳守）
5. baseline と final の diff を user に提示:
   - **目指す:** 追加した enable / 保護した asset を列挙
   - **避ける:** 追加で disable / archive にしたものを列挙
   - **判断根拠:** 仕様文のどの記述に基づいて変更したか 1〜3 行で

仕様文を読んでも変更すべき点が無いと判断した場合は「baseline をそのまま採用」と明示し、final ファイルは作らない。

### ステップ 5: 承認

AskUserQuestion で「適用する / 詳細を見直したい（プラン JSON を全部表示）/ 中止」の 3 択。

### ステップ 6: 適用

```bash
# spec ありで final があれば:
python3 .claude/scripts/apply_profile.py --profile <X> --apply --plan-file /tmp/init-project-final.json --yes

# spec なしまたは Claude が baseline 採用と判断した場合:
python3 .claude/scripts/apply_profile.py --profile <X> --apply --yes
```

settings.json が書き換わり、返却 JSON 内 `bash_commands` に kind 別の mkdir / mv コマンドが入る。`warnings` フィールドに plan-file 由来のクリーンアップログが入ることがあるので user に必要に応じて提示。`settings.marketplaces_added` に値があれば「非組込 marketplace を自動登録した」旨も完了報告に含める（コラボレーターが初回 trust 時にこの marketplace 経由で対象プラグインが自動 install される）。

### ステップ 7: アーカイブの mv 実行

返却された `bash_commands` を kind ごとに 1 回ずつ Bash 実行:

- `mkdir -p ...` （自動 allow）
- `mv ... ; mv ...` （**`mv:*` は ask 設定なので承認プロンプトが kind 別に最大 3 回出ます**。事前に「mv の承認が出ます」と告知）

### ステップ 8: CLAUDE.md 差替

```bash
python3 .claude/scripts/apply_profile.py --profile <X> --write-claude-md
```

### ステップ 9: カタログ再生成

```bash
bash .claude/scripts/sync-catalogs.sh
```

mv は hook を発火させないため明示的に呼ぶ。

### ステップ 10: ディレクトリ scaffold

```bash
python3 .claude/scripts/apply_profile.py --profile <X> --scaffold
```

プロファイル frontmatter の `scaffold:` に沿って作業ディレクトリを作る。**既存ディレクトリには触らない**ので、既にファイルを置いた状態で再実行しても安全である。返却 JSON の `created` / `skipped` を完了報告に使う。

仕様文から明らかに別の構成が要る場合（例: 「FastAPI の REST API」なら `app/api/` `app/models/`）は、追加のディレクトリを提案して承認を取ってから `mkdir -p` する。プロファイルの `scaffold:` を baseline とし、そこからの差分だけを提案する。

### ステップ 11: README.md 生成

**`project-docs` skill を使う。** 節構成・120 字ルール・`TODO:` の扱いは skill が持つので、ここには書かない（二重管理になり片方だけ古くなる）。

ステップ 2 の仕様文があればそこから読み取り、**足りない項目だけ** AskUserQuestion で聞く:

1. プロジェクト名（既定はディレクトリ名）
2. 120 字未満の 1 行説明
3. 技術スタックと、セットアップ / 起動 / テストの実コマンド

**テンプレートの README をそのまま残さない。** 上書きで置き換える。

**ステップ 12 で削除されるファイルへリンクしない。** リンクしてよいのは `CLAUDE.md` / `.claude/rules/` / `docs/CATALOG.md` / `.claude/MEMORY.md` と、このプロジェクト自身のファイルだけである。`docs/PLUGIN_INSTALL_*.md` / `docs/PROJECT_PROFILES.md` / `user-scope/` / `.claude/plugins-user-scope.json` へのリンクは削除後にリンク切れになり、`/doctor` が major で報告する。削除対象の全一覧は `python3 .claude/scripts/detemplate.py --plan` で確認できる。

書き終えたら検証する（ステップ 12 の削除前に済ませる。削除後はリンク切れが出る）:

```bash
python3 ~/.claude/skills/project-docs/validate_docs.py .
```

### ステップ 12: 脱テンプレート化

テンプレート運用専用の資産（`user-scope/` / `.claude/profiles/` / `setup-*.sh` / テンプレート解説 docs / このコマンド自身）を削除する。

```bash
python3 .claude/scripts/detemplate.py --plan
```

`.template-origin` を検出すると終了コード 2 で中断する。その場合は**テンプレート本体で実行している**ので、コピー先で実行し直すよう案内してここで終了する（`--force-here` は自分から使わない）。

`--plan` の結果を件数と分類（原本資産 / プロファイル系 / テンプレート解説 docs）で提示し、AskUserQuestion で 3 択を出す:

1. **実行する**（推奨）— 削除を適用する
2. **対象の全一覧を見る** — `targets` を全件表示してから再度この 3 択に戻る
3. **スキップ** — テンプレート運用資産を残したまま初期化を終える

「実行する」なら:

```bash
python3 .claude/scripts/detemplate.py --apply
```

削除は `git rm --cached` を伴うため `git checkout HEAD -- <path>` で復元できること、原本はテンプレートリポジトリ側に残ることを併せて伝える。

このステップで `.claude/commands/init-project.md` 自身が消えるため、**必ず最後に実行する**。

### ステップ 13: 完了報告

以下を 5〜10 行で日本語まとめ:

- **ステップ 0 で導入を実行した場合はその結果**（配置した資産の件数 / install したプラグインの件数 / 残った警告）
- 採用プロファイル / 仕様文の有無
- enable した plugin の件数と主要 3 件
- disable した plugin の件数
- archive した skill / subagent / command の件数
- 作成したディレクトリ（ステップ 10 の `created`）と README.md を生成した旨
- 脱テンプレート化で削除した件数、または実行しなかった旨
- 次のアクション候補（`/plugin enable <name>` で即時反映、`/doctor` で点検）
- **注意:** `enabledPlugins` の `true/false` 切替は次回 Claude Code 起動時から反映される。即時切替は `/plugin enable <name>` / `/plugin disable <name>` をユーザーが叩く必要がある

## アーカイブからの復元

`_archived/` 配下に移動したものは別プロファイル / 別仕様で再実行しても自動復活しません（discover が `_archived` パスを除外するため）。戻したい場合は手動で:

```bash
mv .claude/skills/_archived/<category>/<name> .claude/skills/<category>/
bash .claude/scripts/sync-catalogs.sh
```

## 冪等性

同じプロファイル + 同じ仕様文で 2 回目を実行すると settings.json と CLAUDE.md と `_archived/` はいずれも実質変化しません（Claude の判断は決定論的ではないため微差は出る可能性あり）。ステップ 10 の scaffold は既存ディレクトリを飛ばし、ステップ 12 の削除は既に消えたパスを飛ばすため、いずれも再実行で壊れません。途中で失敗した場合は安全に再実行できます。

ただし**ステップ 12 まで完走するとこのコマンド自身が削除される**ため、その後の再実行はできません。やり直したい場合は `git checkout HEAD -- .claude/commands/init-project.md` で戻してください。

## 注意事項

- `.claude/settings.local.json` で `enabledPlugins` を上書きしている場合はそちらが優先される可能性があります。本コマンドは `settings.json` のみを編集するため、local 設定との競合は手動で同期してください。
- docs/CATALOG.md に登録されていない plugin（ユーザーが手動で `enabledPlugins` に足したもの）は触りません。
- standalone MCP (`marketplace: external (GitHub)` の Unity MCP 等) は `enabledPlugins` ではなく `~/.claude.json` の `mcpServers` で管理されるため、本コマンドはスキップします（`skipped_no_marketplace` に列挙、Claude が仕様文を見て該当を見つけた場合は完了報告の中で「`claude mcp add <name> -- <cmd>` で別途導入」と案内）。
- 仕様文が長すぎる（数千行レベル）場合は Claude の context を圧迫します。要点を抜粋した上で渡してください。
- Claude の判断は**監査可能**にする責任があります。final JSON を baseline と diff で提示し、承認前に必ず根拠を述べる。盲目的に上書きしない。

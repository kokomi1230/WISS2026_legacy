# template-project-claude (research)

---
name: research
description: 文献収集 → 構造化抽出 → 実験コード → 可視化までを一気通貫で扱う研究用途プロファイル。general 軸に Web リサーチ・ベクトル DB・ML ハブ・Python LSP を加える。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
  - firecrawl@claude-plugins-official
  - huggingface-skills@claude-plugins-official
  - pinecone@claude-plugins-official
  - exa@claude-plugins-official
  - pyright-lsp@claude-plugins-official
enabled_mcp: []
scaffold:
  - sources
  - notes
  - experiments
  - references
  - output
---

# Research — 研究プロファイル

## 概要
このプロジェクトは**研究**用途です（論文調査・データ分析・実験コード・可視化）。一次情報を Web から取得して構造化し、ベクトル DB に保存して横断検索しつつ、Python で実験コードを書くというフローを想定しています。出典明示と再現性を最優先し、捏造を避けます。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — writing-plans / TDD / systematic-debugging
- `feature-dev@claude-plugins-official` — 調査計画と実験計画の標準化
- `code-review@claude-plugins-official` — 実験コード差分レビュー
- `commit-commands@claude-plugins-official` — 進捗を細かくコミット
- `context7@claude-plugins-official` — ライブラリ仕様の最新確認

### 特化追加（research 専用 5 個）
- `firecrawl@claude-plugins-official` — Web スクレイピング・サイトクロール・自律リサーチ
- `huggingface-skills@claude-plugins-official` — モデル・データセット管理（ML 必須統合）
- `pinecone@claude-plugins-official` — ベクトル DB（論文・ノートのセマンティック検索）
- `exa@claude-plugins-official` — 学術系の精度重視 Web 検索 API
- `pyright-lsp@claude-plugins-official` — Python 型推論・参照解析（実験コードを型安全に）

## 一括インストール
```bash
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install firecrawl@claude-plugins-official
/plugin install huggingface-skills@claude-plugins-official
/plugin install pinecone@claude-plugins-official
/plugin install exa@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
```

## 主要ワークフロー
### ワークフロー 1: 文献収集 → 構造化抽出 → 実験コード → 可視化
1. `exa` / `firecrawl` で一次情報（論文・記事・サイト）を収集
2. 取得した本文を `pinecone` のベクトル DB にインデックス、横断クエリで関連箇所を抽出
3. `huggingface-skills` で必要なモデル・データセットを取得（評価ベンチ含む）
4. `feature-dev` で実験計画 → `superpowers` の TDD / writing-plans で実験コード化
5. `pyright-lsp` で型エラー・参照を確認、`code-review` で自己レビュー → `commit-commands` でコミット

## 主要 subagent

> 校正 subagent（`japanese-proofreader` / `english-proofreader` / `code-style-reviewer`）と執筆スタイル skill（`japanese-writing-style` / `english-writing-style` / `code-style`）、`/swap-punctuation` はユーザースコープ（`~/.claude/`）にあり、プロファイルに関わらず常時利用できる。`/init-project` の退避対象ではない。
- `data-scientist` — データ探索・可視化・統計分析（CSV / SQL / Jupyter）
- `planner` — 調査計画の作成（書込みなし）
- `code-reviewer` — 実験コード差分レビュー
- `japanese-proofreader` — 日本語論文・申請書の校正（提出前チェック）
- `english-proofreader` — 英語論文・grant proposal の校正（投稿前チェック）

## 主要 skill / command
- `japanese-writing-style` — 論文・申請書執筆時の文体・句読点・構造ルール（である調・「，」「．」・複文 70%）
- `english-writing-style` — 英語論文・grant の文体ルール（plain English、能動態、Strunk & White ベース）
- `/swap-punctuation` — 「，」「．」⇄「、」「。」の一括変換（本文整形用）

## 行動指針
- 出典・引用元・取得日時を必ず記録
- 不確実な情報は「推定」「未確認」と明記
- 一次情報 > 二次情報の優先順位を厳守
- `firecrawl` 取得時は URL/DOI を `references/` に保存し、要約だけにしない

## プロジェクト規約

### 言語・表記ポリシー

- 応答言語は日本語
- コード内のコメント・docstring は日本語。識別子（変数名・関数名・クラス名）は各言語の慣習どおり英語のままでよい
- ドキュメント（Markdown / HTML 問わず）のユーザー可視テキストは日本語。パス・コード・識別子（API フィールド名、フォント名、CSS クラス、JS 内部文字列）は英語のまま可
- **絵文字を使用しない。** 応答・コード・ドキュメント・コミットメッセージ・PR 説明文のいずれにおいても使わない。区分やラベルは `[自作]` `[公式]` `[取り込み]` のように角括弧テキストで表す。チェックリストの可否表現は `**避ける:**` / `**目指す:**` の見出しに置き換える

言語横断の命名規則・執筆スタイル・Unity / Figma / Notion のワークフローは、ユーザースコープの skill（`code-style` / `japanese-writing-style` / `english-writing-style` / `unity-development` / `figma-integration` / `notion-knowledge-base`）が持ち、必要な場面で自動発火する。ここには**それらに書けないプロジェクト固有の上乗せ**だけを置く。上の 2 項目（日本語コメント・絵文字禁止）がそれにあたる。

ファイル種別ごとの規約は [.claude/rules/](.claude/rules/) にあり、該当ファイルを読んだときだけ読み込まれる。

### アセットのスコープ方針

自作の skill / subagent / command をどちらのスコープに置くかは、次の 1 問で判定する。

> **`/init-project` がその資産を `_archived/` へ退避できる必要があるか？**

- **必要（プロファイル依存）** → プロジェクトスコープ（`.claude/`）
- **不要（用途を問わず常時使う）** → ユーザースコープ（`~/.claude/`。原本は `user-scope/`）

用途が限定される資産をユーザースコープに置くと `/init-project` が全プロジェクトから資産を消してしまうため、この 2 つは原理的に混ぜられない。

**プロジェクトスコープは同名のユーザースコープ資産を覆い隠す。** ユーザースコープ側を修正しても、プロジェクト側に同名の複製が残っていれば古い版が実行され続ける。これは実際に起きた。ユーザースコープへ移行する前のテンプレートをコピーして作ったプロジェクトに当時の資産が残り、19 プロジェクト・147 件が古い版を掴んだままになっていた（ファイルを破壊する既知バグを含む）。

- 資産をユーザースコープへ移したら、**既存プロジェクトから同名の複製を消す**。残すと移行が効かない
- `/doctor` の「スコープ間の同名衝突」がこれを検出する。ただし検査は実行中のプロジェクトに限られるため、他プロジェクトの分は各プロジェクトで `/doctor` を実行して気づく
- プロジェクト固有に作り込んだ資産は例外。同名でも中身が別物なら残す（判断は「user-scope 版で置き換えて壊れないか」）

### 解説資料の置き場所

**解説資料・知見の原文と清書版 HTML は `~/.notion-mirror/` に集約する。プロジェクトの `docs/` には置かない。**

```
~/.notion-mirror/_md/<project>/docs/<name>.md   原文（唯一の原本）
~/.notion-mirror/_html/<DB>/<種別>/<name>.html  清書版（唯一の HTML）
```

同じ資料が複数のリポジトリに複製され、どれが最新か分からなくなったため一本化した（`BrainProducts.html` が 5 箇所、`ANALYSIS.html` と `PROTOCOL.html` が 3 箇所ずつ）。集約は `python3 ~/.claude/scripts/migrate_docs_to_mirror.py`（`--apply` で実行）が行う。

`docs/` に残すのは**テンプレート基盤**だけである。

- `docs/CATALOG.md` / `docs/CATALOG.html` — `/catalog-sync`・`/doctor`・`/init-project`・`apply_profile.py` が参照する
- テンプレート解説の `.md` — `detemplate.py` が初期化時の削除対象として管理している

ミラーのパスは**インラインコードで書き、Markdown リンクにしない**。相対リンクにすると `/doctor` のリンク検査が解決に失敗する。`rm -rf ~/.notion-mirror` は `_md/` の原本ごと消すため使わない（作り直しは `notion_sync.py --full`）。

### 秘匿情報の置き場所

API キー・OAuth トークン・サービスアカウント JSON は `.claude/settings.local.json` または `.env` にだけ書く（両方とも `.gitignore` 対象）。`~/.claude/settings.json` への直書きと、`claude mcp add --scope user` での認証情報付き MCP 登録は避ける。プラグインの install / enable フラグを user scope に置くのは秘匿情報を含まないため可。

## 運用

### 常用コマンド

| コマンド | 用途 |
|---|---|
| `/doctor` | 環境健全性診断 19 項目（settings 構文・catalog / user-scope drift・秘匿情報の直書き・スコープ衝突・リンク切れ） |
| `/catalog-sync` | `docs/CATALOG.md` から `docs/CATALOG.html` を再生成 |
| `/ticket-create <slug>` / `/ticket-run T-NNN` / `/ticket-list` | タスクチケットの作成 / 実行 / 一覧 |
| `/profile-switch <target>` | 初期化済みプロジェクトのプロファイルを切替（仕様文の再入力なし） |

### タスクチケット

`tasks/` 配下で作業単位を T-NNN チケットとして管理する。雛形は `tasks/_template.md`。

- `/ticket-create <slug>` が次の T-NNN を自動採番し、手順 / 検証の項目を `- [ ]` で生成する
- `/ticket-run T-NNN` が `- [ ]` を 1 項目ずつ消化して `- [x]` へ更新し、全項目完了で `status: done` + `tasks/_done/` へ移動する
- 途中 skip があった場合は `tasks/` に残し、後日 `/ticket-run` を再実行する（既に `[x]` の項目は no-op）

### プロジェクト記憶（.claude/MEMORY.md）

チャットをまたいで保持すべき **プロジェクト共有の好み・修正履歴・繰り返しパターン** は [.claude/MEMORY.md](.claude/MEMORY.md) に蓄積する。Claude は新規セッション開始時に本ファイルと共に読み込み、そこに書かれたルールを適用する。

**新しい好み・修正・繰り返しパターンを検出したら `.claude/MEMORY.md` に追記する。** 加えて、**Claude 自身が同じツールエラー・誤前提・失敗を 2 回繰り返した場合は、その根本原因と解決策を Corrections に記録し再発を防ぐ。** 追記判定・重複チェック・除外条件は `memory-update` skill に従う。

書き分けの判断基準:

- 他の開発者がこのリポジトリで作業するときに役立つか → Yes なら `.claude/MEMORY.md`、No ならハーネス auto-memory
- このリポジトリを離れても価値が残るか → Yes なら Notion 知識ベース、No ならリポジトリ内（`CLAUDE.md` / `.claude/MEMORY.md` / `tasks/`）

Notion に書かないもの: コード・差分・リポジトリ固有の規約（git と `CLAUDE.md` の担当）。`tasks/` の T-NNN チケットと Notion の記録を二重管理しない。

## 参考

この節には**初期化後も残るもの**だけを置く。テンプレート運用の解説は初期化時に削除されるため、ここからリンクするとリンク切れになる。

- [README.md](README.md) — プロジェクト概要と導入手順
- [.claude/rules/](.claude/rules/) — ファイル種別ごとの規約
- [docs/CATALOG.md](docs/CATALOG.md) / [docs/CATALOG.html](docs/CATALOG.html) — 統合カタログ（source of truth と人向け UI）
- [.claude/MEMORY.md](.claude/MEMORY.md) — プロジェクト共有の好み・修正履歴・繰り返しパターン
- [Remotion](https://github.com/remotion-dev/remotion) — React で動画生成。同梱していないが動画関連タスク時に参照


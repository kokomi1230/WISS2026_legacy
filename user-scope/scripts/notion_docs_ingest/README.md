# docs 取り込みパイプライン

解説資料の原文を研究ノート_DB へ**全文のまま**投入し、清書版 HTML を作る。
規約は `~/.claude/skills/notion-knowledge-base/SKILL.md` の「ドキュメント取り込みノート」を正本とする。

原文は `~/.notion-mirror/_md/<project>/docs/<name>.md` に置く。移行前のプロジェクト `docs/` も
`resolve_source()` がフォールバックで見るため、移行の途中でも両方から読める。

## 使い方

```bash
cd ~/.claude/scripts/notion_docs_ingest
env -u NOTION_TOKEN python3 build_spec.py        # ミラーから spec.json を組み直す
env -u NOTION_TOKEN python3 ingest.py --dry-run  # 投入サイズと mermaid 挿入を確認
env -u NOTION_TOKEN python3 verify_fidelity.py   # 原文行の欠落がゼロか確認
env -u NOTION_TOKEN python3 ingest.py            # Notion へ全文投入
python3 md2html.py                               # 清書版 HTML を ~/.notion-mirror/_html/ へ生成
```

`env -u NOTION_TOKEN` を付けるのは、シェルに残った失効トークンを避けるため（設定ディレクトリの `.env` を読む）。

パスはすべて環境変数で上書きできる: `DOC_SOURCE_DIR`（既定 `~/.notion-mirror/_md`）/ `REPOSITORY_DIR`（フォールバック先。既定 `~/Documents/Repository`）/ `NOTION_MIRROR_DIR`（既定 `~/.notion-mirror`）/ `CLAUDE_CONFIG_DIR`（既定 `~/.claude`）/ `EXPLAINER_TEMPLATE`（`md2html.py` が使う HTML テンプレート）。

## ファイル

| ファイル | 種別 | 役割 |
|---|---|---|
| `overrides.json` | **入力（人が書く）** | mermaid 図・重複整理の置換・HTML 出力先を原文パスごとに指定 |
| `hints.json` | **入力（人が書く）** | HTML で `.note` / `.caution` / `.info` へ昇格させる段落を指定 |
| `build_spec.py` | 実行 | ミラーの各ノートから page_id・出典パス・`概要` を集め `spec.json` を作る |
| `ingest.py` | 実行 | 原文を全文のまま組み立て `PATCH /v1/pages/{id}/markdown` へ投入 |
| `md2html.py` | 実行 | 原文を解説資料テンプレートの HTML へ起こす |
| `verify_fidelity.py` | 検証 | 原文の各行が投入本文に残っているかを行単位で突き合わせる |
| `spec.json` | 生成物 | `build_spec.py` が作る。直接編集しない |

**`overrides.json` と `hints.json` は再生成できない入力なので、ミラーへは置かない。**
ミラーは Notion と原文を写す場所であり、それらを加工する道具の置き場ではない。

## 決まりごと

- **要約しない。** 原文の見出し・段落・表・コードブロックをそのまま移す
- 削ってよいのは重複だけ。`overrides.json` の `edits` に置換として書き、参照を残す
- ASCII 図は mermaid を足しつつ原文のコードブロックも残す。ディレクトリツリー・API 一覧は図にしない
- 105KB を 1 リクエストで投入できるため分割は不要
- **裸のファイル名はバッククォートで囲む。** Notion が `foo.py` をドメインとみなし `http://foo.py` へリンク化するため（`quote_bare_filenames`）。境界判定は ASCII で行う。`\w` は和文にもマッチし「過剰なCLAUDE.md」を取りこぼす

## 実測値（2026-08-01）

| 項目 | 値 |
|---|---|
| 対象ノート | 41（定型文書の集約ノート 1 本は対象外） |
| 投入合計 | 約 700KB |
| 1 リクエストの上限 | 105KB・66,204 文字で `truncated: false` を確認 |
| 原文行の欠落 | 0 |
| 自動リンク化 | 477 → 9（残りは実在ドメイン 4・メソッド名 5） |
| mermaid | 11 図（実パーサ通過を確認） |

## 原文更新の検出

```bash
env -u NOTION_TOKEN python3 ingest.py --check
```

投入した本文の SHA-256 を `ingest_state.json` に持ち、原文から組み直した本文と突き合わせる。
原文を編集したノートだけが「投入し直しが要る」として並ぶので、そのパスを引数に渡して再投入する。

```bash
env -u NOTION_TOKEN python3 ingest.py python-bci-platform/docs/ROADMAP.md
```

引数は原文置き場からの相対パス（`<project>/docs/<name>.md`）である。移行してもこの形は変わらない。

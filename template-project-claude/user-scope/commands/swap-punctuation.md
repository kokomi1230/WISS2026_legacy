---
description: 日本語ファイル内の句読点を相互変換する。学術用「，」「．」と一般用「、」「。」をスワップ。コードブロック / LaTeX 数式 / URL は保護対象。
allowed-tools: Bash(python3 ~/.claude/scripts/swap_punctuation.py:*), Read, Glob
argument-hint: "<file-or-dir> [--to=academic|general] [--check] [--dry-run]"
profile_relevance:
  - writing
  - research
  - meta
---

# /swap-punctuation

日本語テキストファイル内の **句読点** を相互変換するコマンド。論文 / 申請書系の **学術用** 「，」「．」と、ブログ / 一般文書の **一般用** 「、」「。」を一括スワップする。

## 用途

- 一般文書として書いた草稿を論文用に整形（`--to=academic`）
- 論文から抜粋した文章をブログ用に変換（`--to=general`）
- 混在状況を確認して統一方針を決める（`--check`）

## 保護対象（変換されない領域）

スクリプトが自動で以下を除外する:

- フェンスコードブロック ```` ```...``` ````
- インラインコード `` `...` ``
- LaTeX インライン数式 `$...$`
- LaTeX ディスプレイ数式 `$$...$$`
- LaTeX 環境 `\begin{equation}...\end{equation}` 等
- URL（`http://` `https://` `ftp://`）
- HTML / Markdown タグ `<...>`

これにより、コード内のカンマ / ピリオドや、数式中の `x, y` などは元のまま保持される。

## 使用例

### 単一ファイルを学術スタイルへ
```bash
python3 ~/.claude/scripts/swap_punctuation.py --to=academic content/chapter1.md
```

### ディレクトリ配下を一括変換（再帰、対象拡張子: .md .txt .tex .rst .org）
```bash
python3 ~/.claude/scripts/swap_punctuation.py --to=academic content/
```

### 現状を検出のみ（書き込みなし）
```bash
python3 ~/.claude/scripts/swap_punctuation.py --check content/
```

出力例:
```
content/chapter1.md: general(、42 / 。15), academic(，0 / ．0)
content/chapter2.md: general(、3 / 。1), academic(，35 / ．12)
```
→ 章間で句読点が混在していることが分かる

### dry-run（書き込まずに件数表示）
```bash
python3 ~/.claude/scripts/swap_punctuation.py --to=academic --dry-run content/
```

### 標準入力経由
```bash
echo "テスト、文章。" | python3 ~/.claude/scripts/swap_punctuation.py --to=academic --stdin
```

## 実行

引数で受け取ったファイル / ディレクトリに対して、`--to` で指定したスタイルへ変換する。`--check` または `--dry-run` を付けた場合は書き込まずに統計のみ表示。

!`python3 ~/.claude/scripts/swap_punctuation.py $ARGUMENTS`

## 注意

- **元ファイルを直接書き換える**（in-place）。`git` 管理下で実行し、差分確認してから commit すること
- バイナリ / UTF-8 でないファイルは自動スキップ（stderr に警告）
- 拡張子で再帰時の対象を絞り込むため、ディレクトリ指定では `.md .txt .tex .rst .org` のみ処理。それ以外はスキップ
- 保護対象に該当しない引用符内の句読点は通常通り変換される（引用元の表記を保ちたい場合は事前に対象から外すこと）
- 句読点を「，」「．」に統一する場合、`japanese-writing-style` skill の方針に準拠する。混在検出には `japanese-proofreader` subagent も併用可能

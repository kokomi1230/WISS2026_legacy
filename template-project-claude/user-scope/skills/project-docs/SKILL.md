---
name: project-docs
description: プロジェクトの CLAUDE.md / README.md / .claude/rules/ を作成・更新・検証する。どの内容をどこに書くかの振り分け（CLAUDE.md か rules か skill か README か）、公式ガイドラインの行数目標（200 行未満）、paths: による条件ロード、standard-readme の節構成を適用し、validate_docs.py で機械的に判定する。「CLAUDE.md を作って / 直して / 点検して」「README を書いて」「プロジェクトのドキュメントを整えて」等で発火する。Use when creating, updating, auditing, or validating a project's CLAUDE.md, README.md, or .claude/rules/ files.
---

# プロジェクトドキュメント (project-docs)

このスキルは `CLAUDE.md` / `README.md` / `.claude/rules/` の作成・更新・検証を扱う。判定は目視ではなく同梱の `validate_docs.py` に寄せる。行数・`paths:` の有無・リンク切れは機械的に数えられる事実であり、目視に任せると同じファイルで判定がぶれる。

## まず振り分けを決める

**書く前に、その内容がどこに属するかを決める。** これを飛ばすと同じ内容が複数の文書に重複し、片方だけ古くなる。

| 置き場所 | 条件 | 例 |
|---|---|---|
| `CLAUDE.md` | 全セッションで真、かつ Claude が守るべき規約 | 絵文字を使わない、応答は日本語、`npm test` で検証する |
| `.claude/rules/*.md` | 特定のファイル種別を触るときだけ必要 | Python の書き方、カタログの編集手順 |
| skill | 特定の作業をするときだけ必要（意図起動型） | 執筆スタイル、Figma 連携 |
| `README.md` | 人間の読者向け。Claude への指示ではない | セットアップ、ディレクトリ構成、ライセンス |

判断に迷ったら **「そのファイルを開いていないセッションでも必要か」** を問う。必要なら `CLAUDE.md`、不要なら `.claude/rules/`。

`CLAUDE.md` に書く各行には **「これを消したら Claude は間違えるか」** を問う。No なら消す。肥大した CLAUDE.md は指示自体を無視させる。

## 手順

### 作成（新規に書く）

1. リポジトリを読み、ビルド / テスト / 実行のコマンドを**実際のファイルから**確認する（`package.json` / `pyproject.toml` / `Makefile` 等）
2. 上の表で振り分ける
3. `CLAUDE.md` を書く。詳細は [references/claude-md.md](references/claude-md.md)
4. `README.md` を書く。詳細は [references/readme.md](references/readme.md)
5. 条件付きの規約があれば `.claude/rules/<topic>.md` を作り、**必ず `paths:` を付ける**
6. 検証する（下記）

**分からないことを憶測で埋めない。** 確認できない項目は `TODO:` を残す。誤った手順を書くと、読んだ人と Claude の両方が実行して失敗する。

### 更新（既存を直す）

1. まず検証を実行し、指摘を得る
2. 指摘の多い順ではなく、**major から**直す
3. 行数超過は削るのではなく**移す**。条件付きの規約は `.claude/rules/` へ、長い解説は `docs/` へ
4. プロジェクト固有の記述は消さない。消してよいのはテンプレート由来の定型節と、コードから読み取れる内容だけ
5. 再度検証する

### 検証（書き換えない）

```bash
python3 ~/.claude/skills/project-docs/validate_docs.py [PATH]
```

終了コードは `0` = 指摘なし / `1` = 警告のみ / `2` = 要対応。`--json` で機械可読。

| 判定 | 意味 |
|---|---|
| major | 直す。リンク切れ・絵文字・250 行超・README のタイトル欠落 |
| minor | 検討する。200 行超・`paths:` 欠落・`@import` の使用・節の不足 |

## 守る基準

- **`CLAUDE.md` は 200 行未満**（上限 250）。公式ドキュメントの目標値
- **ルールは falsifiable に書く。** 「良いコードを書く」は判定できない。「`async` 関数には必ずタイムアウトを付ける」は判定できる
- **`.claude/rules/*.md` には必ず `paths:` を付ける。** 無いと起動時に無条件ロードされ、`CLAUDE.md` に書くのと変わらない
- **`@path` import を使わない。** import 先は起動時に全ロードされ、コンテキストを削減しない。整理にはなるが節約にはならない
- **絵文字を使わない。** 区分は `[自作]` `[公式]` のような角括弧テキストで表す
- **`README.md` の説明は 120 字未満**、逆ピラミッド（重要な順）で並べる

## 出典

- [公式: CLAUDE.md とメモリ](https://code.claude.com/docs/en/memory) — 200 行目標、`paths:` の条件ロード、`@path` import の挙動
- [公式: ベストプラクティス](https://code.claude.com/docs/en/best-practices) — 含める / 除外の基準
- [standard-readme](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) — README の節順序と 120 字ルール

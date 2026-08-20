---
paths:
  - "**/*.py"
---

# Python の記述規約

言語横断の命名原則とコメントの「なぜ」原則は `code-style` skill（ユーザースコープ）が持つ。ここには本リポジトリ固有の上乗せだけを書く。

- **コメント・docstring は日本語で書く。** 識別子（変数名・関数名・クラス名）は PEP 8 どおり英語の `snake_case` / `PascalCase` のままにする
- **絵文字を使わない。** 出力メッセージ・ログ・コメントのいずれでも使わない。区分を示したいときは `[skip]` `[ok]` のような角括弧テキストにする
- 冗長なデバッグログを残さない。恒久的に価値のある情報だけを出力する
- ruff / black の設定はリポジトリ直下の `pyproject.toml` にある。実行は任意だが、設定と矛盾する書き方はしない

`.claude/scripts/` 配下は Claude Code のツール呼び出しから起動される。標準出力を機械可読な JSON にするスクリプト（`apply_profile.py` / `detemplate.py` / `doctor.py`）では、人間向けメッセージを stderr へ出して stdout を汚さない。

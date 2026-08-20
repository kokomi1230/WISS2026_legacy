<!-- PROFILE: data-analysis -->
このプロジェクトは**データ分析**の用途です（CSV 処理・統計・可視化・ダッシュボード）。

## 行動指針
- 再現性を重視。乱数シード固定、データバージョン記録。
- 分析手順をノートブックまたはスクリプトに残す。
- 結論より先にデータ前処理・欠損値の扱いを明記。
- 可視化は意図を持って（無闇にグラフを増やさない）。
- 機密データは出力に含めない。

## 主要スキル（プロジェクト固有のみ残置）
- `xlsx` — Excel 読み書き
- `pdf` — レポート PDF 出力
- `claude-api` — LLM 統合分析
- `excel-mcp-server` — Excel MCP（プラグイン未収録の補助）
- `google-workspace` — Google Workspace 連携

## プラグインで代替される機能
- 請求書 PDF → CSV 経理データ取り込み → `productivity@knowledge-work-plugins`
- データウェアハウス探索・パイプライン → `data-engineering@claude-plugins-official`
- カラム指向 SQL DB（ClickHouse）→ `clickhouse@claude-plugins-official`

## 主要 subagent
- `data-scientist` — データ探索・可視化・統計分析（Python/SQL/Jupyter）
- `planner` — 分析計画の作成（書込みなし）

## 拡張枠
取り込み済みの `excel-mcp-server` / `google-workspace` / `notebooklm` は `.claude/skills/integration/` で利用可能。`lead-research-assistant` 相当は `sales@knowledge-work-plugins` プラグインで代替。

## 推奨ディレクトリ構造
```
data/raw/       # 生データ（読み取り専用）
data/processed/ # 前処理済み
notebooks/      # Jupyter / 探索的分析
scripts/        # 再利用可能なパイプライン
reports/        # 最終レポート・図表
```

## 推奨外部統合
- `pyright-lsp@claude-plugins-official` — Python LSP

## 検証習慣（運用 Tips Tip 2 / 14）
- スクリプト変更後は実データの一部で実行し、出力の **head と統計サマリ（行数・欠損率・dtype）** を必ず提示
- ノートブックを生成しただけで「完了」にしない。`python script.py --dry-run` 等で CLI 実行確認
- 重い計算は事前に `head(1000)` で挙動を確認 → フル実行の順
- 詳細は `self-verify` skill 参照

## 並列処理（Tip 21 / 22）
- 大規模データ処理は `claude -p "<task>"` の **非対話モード fan-out** で並列化を検討
- データ前処理パイプラインは `data-scientist` subagent に切り出して context を分離

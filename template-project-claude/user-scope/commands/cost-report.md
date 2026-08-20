---
description: 直近N日間の Claude Code セッションコストを日次・モデル別に集計し USD 換算で表示する（ローカルログから算出、API従量課金換算の推定値）。
allowed-tools: Bash(python3 ~/.claude/scripts/cost_report.py:*), Read
argument-hint: "[--days N] (既定7) [--tz TZ] (既定Asia/Tokyo) [--project-only]"
profile_relevance:
  - meta
---

# /cost-report

Claude Code の `~/.claude/projects/` 配下のローカルセッションログを集計し、**日次・モデル別の USD 換算コスト表**を表示するコマンド。`/cost` は現在のセッションのみ、`/usage` は%表示のみでドル額の日次内訳が出ないため、それらを補完する。

## 用途

- 直近1週間、どの日にどのモデルでどれくらい使ったかを実額（$換算）で把握する
- 特定プロジェクトだけの消費傾向を見たい場合は `--project-only` で絞り込む

## 使用例

### 既定（直近7日間、Asia/Tokyo、全プロジェクト）
```bash
python3 ~/.claude/scripts/cost_report.py
```

### 直近14日間、UTC基準
```bash
python3 ~/.claude/scripts/cost_report.py --days 14 --tz UTC
```

### カレントプロジェクトのログのみ
```bash
python3 ~/.claude/scripts/cost_report.py --project-only
```

出力例（実行時は USD 額に `$` が付いた形で表示されます。この節はコマンド定義ファイルの引数置換を避けるため `$` を伏せて記載しています）:
```
┌────────────────────────┬─────────┬─────────────────────────────────────┐
│ 日付（JST）            │ 合計    │ 内訳（主なモデル）                  │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 06/30 (火)             │ USD 13.45  │ opus-4-8 USD 12.43, sonnet-5 USD 1.02      │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 07/01 (水)             │ USD 0.00   │ (利用なし)                           │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 07/07 (火・今のところ) │ USD 24.49  │ opus-4-8 USD 14.42, sonnet-4-6 USD 6.18   │
└────────────────────────┴─────────┴─────────────────────────────────────┘

合計（7日間）: USD 57.88
※ トークン量から算出した「API従量課金換算」の推定値。実際の請求ではない（Maxは定額制）。
※ 料金表 最終確認: 2026-07-07 / platform.claude.com/docs/en/about-claude/pricing
```

## データソースと注意

- `~/.claude/projects/**/*.jsonl` を読む。既定では**このマシン上の全プロジェクト**が対象（`/usage` と同じスコープ、他デバイス・claude.aiの利用は含まない）
- 料金はスクリプト内にハードコードした公式単価表（`platform.claude.com/docs/en/about-claude/pricing`）を使用。Anthropicが価格改定した場合は手動更新が必要（スクリプル冒頭の `PRICING_VERIFIED` を参照）
- Claude Max/Pro サブスクリプション利用者にとって、この金額は**実際の請求額ではない**。あくまでAPI従量課金だった場合の相当額（参考値）
- pricing表に無い未知モデルのログは集計から除外され、stderr に警告が出る

## 実行

!`python3 ~/.claude/scripts/cost_report.py $ARGUMENTS`

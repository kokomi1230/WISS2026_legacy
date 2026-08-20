---
name: design
description: UI/UX デザイン・デザインシステム・Figma Slides 作成を中心とするデザインプロファイル。general 軸に Figma 連携（design↔code 双方向・Code Connect・design tokens）と frontend-design を加える。
enabled_plugins:
  - superpowers@claude-plugins-official
  - feature-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - commit-commands@claude-plugins-official
  - context7@claude-plugins-official
  - frontend-design@claude-plugins-official
enabled_mcp:
  - figma
scaffold:
  - design
  - src
  - tokens
  - slides
  - docs
---

# Design — デザインプロファイル

## 概要
このプロジェクトは**デザイン**用途です（UI/UX 設計・デザインシステム・プレゼン資料）。Figma を中心に据え、
design→code（デザインを実装）・code→design（コードを Figma へ）の双方向、Code Connect による component 対応、
design tokens / variables の統一、そして **Figma Slides** によるスライド作成までを扱います。general 軸に
Figma MCP 連携と `frontend-design`（AI っぽくない実装コード生成）を加えます。

## 推奨プラグイン
### 必須（軸 5 個）
- `superpowers@claude-plugins-official` — writing-plans / TDD / systematic-debugging
- `feature-dev@claude-plugins-official` — 要件 → 計画 → 実装 → レビュー
- `code-review@claude-plugins-official` — 差分レビュー
- `commit-commands@claude-plugins-official` — Git ワークフロー自動化
- `context7@claude-plugins-official` — ライブラリ仕様の最新確認

### 特化追加（design 専用）
- `frontend-design@claude-plugins-official` — リアルなデザインシステム・太字タイポの UI コード生成

### MCP（`.mcp.json` で管理 / `enabled_plugins` には含めない）
- **Figma MCP** — design↔code 双方向・Code Connect・design tokens・FigJam・Figma Slides
  ```bash
  claude mcp add --transport http figma https://mcp.figma.com/mcp
  ```
  代替（Figma Desktop の Dev Mode ローカル）: `http://127.0.0.1:3845/sse`。初回接続時に OAuth 認証（`whoami` で確認）

## 一括インストール
```bash
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
/plugin install frontend-design@claude-plugins-official
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

## 主要ワークフロー
### ワークフロー 1: design→code（Figma から実装）
1. Figma URL を受領 → `get_metadata` で構造、`get_screenshot` で見た目を把握
2. `get_design_context` で実装コンテキスト、`get_variable_defs` で design tokens を取得
3. `frontend-design` で UI コードを生成、tokens をコードのトークンへマップ
4. `feature-dev` → `code-review` → `commit-commands` で実装・レビュー・コミット

### ワークフロー 2: code→design / デザインシステム
1. `/figma-use` をロード（必須）→ `use_figma` でコンポーネント / 画面を Figma へ生成・更新
2. `search_design_system` / `get_libraries` で既存ライブラリと整合
3. Code Connect（`add_code_connect_map`）で component ↔ コードを対応付け

### ワークフロー 3: Figma Slides（プレゼン資料作成）
1. `/figma-use` をロード → `use_figma` でスライドを生成・編集
2. 構成テンプレ（タイトル / アジェンダ / 背景 / 本論 / 結果 / まとめ）、1 スライド 1 主題
3. `get_variable_defs` でブランドカラー・フォントを取得し統一、図は FigJam / `generate_diagram` を併用

## 主要 subagent
- `figma-reviewer` — Figma デザイン / スライドの整合・tokens・a11y・構成を read 専用でレビュー
- `code-reviewer` — 生成 UI コードの差分レビュー
- `planner` — 大規模デザイン変更の前段プラン作成（書込みなし）

## 主要 skill / command
- `figma-integration` — Figma 連携の入口ガイド（用途別 tool 振り分け・`/figma-*` skill ロード順・Slides 規約）
- サーバ同梱 `/figma-use` / `/figma-generate-design` / `/figma-generate-library` / `/figma-code-connect` /
  `/figma-use-figjam` / `/figma-generate-diagram`（各操作前に対応 skill をロード）

## 行動指針
- `use_figma` / `generate_diagram` は対応 skill を**先にロード**してから呼ぶ
- ハードコード値を避け design tokens（`get_variable_defs`）を優先
- アクセシビリティ（WCAG コントラスト・最小文字サイズ）を満たす
- Figma への書き込み（生成 / 上書き）は外向き操作。既存ファイルを上書きする前に対象を確認
- 秘匿情報は `.env` / `.claude/settings.local.json` へ。`.mcp.json` にはサーバ定義のみ
